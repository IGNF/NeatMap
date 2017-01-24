# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TidyCity
                                 A QGIS plugin
 A simple QGIS python plugin for building tidy cities.
                              -------------------
        begin                : 2016-11-30
        git sha              : $Format:%H$
        copyright            : (C) 2016 by IGN
        email                : julien.perret@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from PyQt4.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, Qt
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QProgressBar,  QTransform
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from tidy_city_dialog import TidyCityDialog
import os.path
import math
from qgis.core import QgsVectorLayer, QgsFeature, QgsSpatialIndex, QgsVectorFileWriter, QgsMapLayerRegistry
from qgis.core import QgsFeatureRequest, QgsField, QgsGeometry,  QgsPoint
from shapely.wkb import loads
from shapely.ops import cascaded_union, unary_union

class TidyCity:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'TidyCity_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)


        # Declare instance attributes
        self.actions = []
        self.menu = self.tr(u'&TidyCity')
        # TODO: We are going to let the user set this up in a future iteration
        self.toolbar = self.iface.addToolBar(u'TidyCity')
        self.toolbar.setObjectName(u'TidyCity')

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('TidyCity', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        # Create the dialog (after translation) and keep reference
        self.dlg = TidyCityDialog()

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToVectorMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/TidyCity/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Build a tidy city'),
            callback=self.run,
            parent=self.iface.mainWindow())
        
        self.dlg.fileLineEdit.clear()
        self.dlg.fileButton.clicked.connect(self.select_output_file)
        self.save = self.dlg.saveCheckBox.isChecked()
        self.load = self.dlg.loadCheckBox.isChecked()
        self.dlg.saveCheckBox.clicked.connect(self.toggle_save)
        self.dlg.loadCheckBox.clicked.connect(self.toggle_load)

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&TidyCity'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    def select_output_file(self):
        filename = QFileDialog.getSaveFileName(self.dlg, "Select output file ","", '*.shp')
        self.dlg.fileLineEdit.setText(filename)

    def toggle_save(self):
        self.save = self.dlg.saveCheckBox.isChecked()
        self.dlg.fileLineEdit.setEnabled(self.save)
        self.dlg.fileButton.setEnabled(self.save)

    def toggle_load(self):
        self.load = self.dlg.saveCheckBox.isChecked()
        self.dlg.layerLineEdit.setEnabled(self.load)

    def compute_density(self, geom, area, index, filterLayer):
        intersectingfids = index.intersects(geom.boundingBox())
        geometries = []
        for fid in intersectingfids:
            intersecting_feat = filterLayer.getFeatures(QgsFeatureRequest(fid)).next()
            if intersecting_feat.geometry().intersects(geom):
                geometries.append(intersecting_feat.geometry().intersection(geom))
        if geometries:
            union_geoms = QgsGeometry.unaryUnion(geometries)
            total_intersecting_area = union_geoms.area()
        else:
            total_intersecting_area = 0.0
        density = total_intersecting_area/area
        return density

    def compute_convexity(self, geom, area):
        convexhull = geom.convexHull()
        convexity = area/convexhull.area()
        return convexity

    def compute_compactness(self, geom, area, perimeter):
        return 4 * math.pi * area / (perimeter * perimeter)
        
    def  lineAngle(self,   x1,  y1,  x2,  y2 ):
        at =math. atan2( y2 - y1, x2 - x1 );
        a = -at + math.pi / 2.0;
        return self.normalizedAngle( a );

    def normalizedAngle(self,  angle):
        clippedAngle = angle;
        if ( clippedAngle >= math.pi * 2 or clippedAngle <= -2 * math.pi ):
            clippedAngle = math.fmod( clippedAngle, 2 * math.pi);
        if ( clippedAngle < 0.0 ):
            clippedAngle += 2 * math.pi;
        return clippedAngle;
    
    def compute_orientedboundingBox(self,  geom):
        area = float("inf");
        angle = 0;
        width = float("inf");
        height =  float("inf");
        
        if (geom is None):
            return  QgsGeometry();
 
        hull = geom.convexHull();
        if ( hull.isEmpty() ):
            return QgsGeometry();
        x = hull.asPolygon()
        vertexId = 0;
        pt0 = x[0][vertexId]
        pt1 = pt0
        prevAngle = 0.0;
        size = len(x[0]);
        for vertexId in range(0,  size-0):
            pt2 = x[0][vertexId]
            currentAngle = self.lineAngle( pt1.x(), pt1.y(), pt2.x(), pt2.y() );
            rotateAngle = 180.0 / math.pi *  ( currentAngle - prevAngle );
            prevAngle = currentAngle;
            
            t = QTransform.fromTranslate( pt0.x(), pt0.y() );
            t.rotate( rotateAngle );
            t.translate( -pt0.x(), -pt0.y() );
            hull.transform(t)
            
            bounds = hull.boundingBox();
            currentArea = bounds.width() * bounds.height();
            if ( currentArea  < area ):
                minRect = bounds;
                area = currentArea;
                angle = 180.0 / math.pi * currentAngle;
                width = bounds.width();
                height = bounds.height();
            pt2 = pt1;
        minBounds = QgsGeometry.fromRect( minRect );
        minBounds.rotate( angle, QgsPoint( pt0.x(), pt0.y() ) );
        if ( angle > 180.0 ):
            angle =math.fmod( angle, 180.0 );
        return minBounds


    def run(self):
        """Run method that performs all the real work"""
        layers = self.iface.legendInterface().layers()
        layer_list = []
        self.dlg.inputLayerComboBox.clear()
        self.dlg.filterLayerComboBox.clear()
        for layer in layers:
            layer_list.append(layer.name())
        self.dlg.inputLayerComboBox.addItems(layer_list)
        self.dlg.filterLayerComboBox.addItems(layer_list)
        # show the dialog
        self.dlg.show()
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # get the parameters from the GUI
            filename = self.dlg.fileLineEdit.text()
            layername = self.dlg.layerLineEdit.text()
            threshold = self.dlg.thresholdDoubleSpinBox.value()

            selectedInputLayerIndex = self.dlg.inputLayerComboBox.currentIndex()
            selectedInputLayer = layers[selectedInputLayerIndex]
            selectedFilterLayerIndex = self.dlg.filterLayerComboBox.currentIndex()
            selectedFilterLayer = layers[selectedFilterLayerIndex]
            # create a spatial index
            print "Creating filter layer index..."
            index = QgsSpatialIndex(selectedFilterLayer.getFeatures())
            #for f in selectedFilterLayer.getFeatures():
            #    index.insertFeature(f)
            print "Filter layer index created!"
                        
            # create layer
            vl = QgsVectorLayer("Polygon", layername, "memory")
            pr = vl.dataProvider()

            # Enter editing mode
            vl.startEditing()
			
			# TODO: ADD THE NEW MEASURES HERE!!!
            # add fields
            fields = [
                QgsField("area", QVariant.Double),
                QgsField("density", QVariant.Double),
                QgsField("convexity", QVariant.Double),
                QgsField("compactness", QVariant.Double)]
			# add the new measures to the features
            pr.addAttributes( fields )
            vl.updateFields()
            
            progressMessageBar = self.iface.messageBar().createMessage("Computing measures...")
            progress = QProgressBar()
            progress.setMaximum(selectedInputLayer.featureCount())
            progress.setAlignment(Qt.AlignLeft|Qt.AlignVCenter)
            progressMessageBar.layout().addWidget(progress)
            self.iface.messageBar().pushWidget(progressMessageBar, self.iface.messageBar().INFO)
            
            featureList = []
            i = 0
            # add features
            for f in selectedInputLayer.getFeatures():
                geom = f.geometry()
                area = geom.area()
                perimeter = geom.length()
                density = self.compute_density(geom, area, index, selectedFilterLayer)
                convexity = self.compute_convexity(geom, area)
                compacness = self.compute_compactness(geom, area, perimeter)
                geom = self.compute_orientedboundingBox(geom);
                if density > threshold:
                    feat = QgsFeature()
                    feat.setGeometry( geom )
                    feat.initAttributes(len(fields))
                    feat.setAttribute( 0, area )
                    feat.setAttribute( 1, density )
                    feat.setAttribute( 2, convexity )
                    feat.setAttribute( 3, compacness )
                    featureList.append(feat)
                i = i + 1
                progress.setValue(i)

            self.iface.messageBar().clearWidgets()
            pr.addFeatures( featureList )

            # Commit changes
            vl.commitChanges()
            if self.save:
                error = QgsVectorFileWriter.writeAsVectorFormat(vl, filename, "UTF-8", None, "ESRI Shapefile")
            if self.load:
                QgsMapLayerRegistry.instance().addMapLayer(vl)

