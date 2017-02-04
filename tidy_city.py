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
from PyQt4.QtGui import QAction, QIcon, QFileDialog, QProgressBar, QTransform
# Initialize Qt resources from file resources.py
#import resources
# Import the code for the dialog
from tidy_city_dialog import TidyCityDialog
import os.path
import math
from qgis.core import QgsVectorLayer, QgsFeature, QgsSpatialIndex, QgsVectorFileWriter, QgsMapLayerRegistry
from qgis.core import QgsFeatureRequest, QgsField, QgsGeometry, QgsPoint, QgsRectangle
from shapely.wkb import loads
from shapely.ops import cascaded_union, unary_union

class TidyCity:
    """QGIS Plugin Implementation."""

    """
    Initialisation du plugin.
    """

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
	
	
    """
    Méthode de calcul du SMBR.
    """

    def normalizedAngle(self,  angle):
        clippedAngle = angle
        if ( clippedAngle >= math.pi * 2 or clippedAngle <= -2 * math.pi ):
            clippedAngle = math.fmod( clippedAngle, 2 * math.pi)
        if ( clippedAngle < 0.0 ):
            clippedAngle += 2 * math.pi
        return clippedAngle

    def lineAngle(self, x1, y1, x2, y2):
        at = math.atan2( y2 - y1, x2 - x1 )
        a = -at + math.pi / 2.0
        return self.normalizedAngle( a )

    def compute_SMBR(self, geom):
        area = float("inf")
        angle = 0
        width = float("inf")
        height =  float("inf")
        
        if (geom is None):
            return  QgsGeometry()
 
        hull = geom.convexHull()
        if ( hull.isEmpty() ):
            return QgsGeometry()
        x = hull.asPolygon()
        vertexId = 0
        pt0 = x[0][vertexId]
        pt1 = pt0
        prevAngle = 0.0
        size = len(x[0])
        for vertexId in range(0,  size-0):
            pt2 = x[0][vertexId]
            currentAngle = self.lineAngle( pt1.x(), pt1.y(), pt2.x(), pt2.y() )
            rotateAngle = 180.0 / math.pi *  (currentAngle - prevAngle)
            prevAngle = currentAngle
            
            t = QTransform.fromTranslate( pt0.x(), pt0.y() )
            t.rotate(rotateAngle)
            t.translate( -pt0.x(), -pt0.y() )
            hull.transform(t)
            
            bounds = hull.boundingBox()
            currentArea = bounds.width() * bounds.height()
            if ( currentArea  < area ):
                minRect = bounds
                area = currentArea
                angle = 180.0 / math.pi * currentAngle
                width = bounds.width()
                height = bounds.height()
            pt2 = pt1
        minBounds = QgsGeometry.fromRect( minRect )
        minBounds.rotate( angle, QgsPoint( pt0.x(), pt0.y() ) )
        if ( angle > 180.0 ):
            angle = math.fmod( angle, 180.0 )
        return minBounds, area, angle, width, height

            
    """
    Méthodes de calcul des indicateurs.
    """

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

    def compute_elongation(self, SMBR_height, SMBR_width):
        """
        Calcul de l'élongation.
        """
        elongation = SMBR_height/SMBR_width
        return elongation

    def compute_compactness(self, area, perimeter):
        """
        Calcul de la compacité.
        """
        return 4 * math.pi * area / (perimeter * perimeter)
    
    def compute_convexity1(self, geom, area):
        """
        Calcul de la convexité selon l'enveloppe convexe.
        """
        convexhull = geom.convexHull()
        convexity1 = area/convexhull.area()
        return convexity1
        
    def compute_convexity2(self, area, SMBR_area):
        """
        Calcul de la convexité selon le SMBR.
        """
        convexity2 = area/SMBR_area	
        return convexity2
        
    def compute_sidesnumber(self,geom):
        """
        Calcul du nombre de côtés simplifié. 
        Méthode non aboutie.
        """
        simple_geom = geom.simplify(10.0)
        verysimple_geom = simple_geom.simplify(10.0)
        nb_sides = 0
        ver = verysimple_geom.vertexAt(0)
        while(ver != QgsPoint(0,0)):
            nb_sides += 1
            ver = verysimple_geom.vertexAt(nb_sides)
        return verysimple_geom, nb_sides
        

    """
    Fonction run.
    """

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
            print("Creating filter layer index...")
            index = QgsSpatialIndex(selectedFilterLayer.getFeatures())
                        
            # create layer
            vl = QgsVectorLayer("Polygon", layername, "memory")
            pr = vl.dataProvider()

            # Enter editing mode
            vl.startEditing()

            # add fields
            fields = [
                QgsField("area", QVariant.Double),
                QgsField("density", QVariant.Double),
                QgsField("SMBR_area", QVariant.Double),
                QgsField("SMBR_angle", QVariant.Double),
                QgsField("SMBR_width", QVariant.Double),
                QgsField("SMBR_height", QVariant.Double),
                QgsField("convexity1", QVariant.Double),    
                QgsField("convexity2", QVariant.Double),
                QgsField("elongation", QVariant.Double),
                QgsField("compactness", QVariant.Double),
                QgsField("sides_nb", QVariant.Int),
                QgsField("x_init",QVariant.Double),
                QgsField("y_init",QVariant.Double),
                QgsField("x_new",QVariant.Double),
                QgsField("y_new",QVariant.Double),
                QgsField("group",QVariant.Int)]
            
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
                
                #calcul des indicateurs
                param_SMBR = self.compute_SMBR(geom)
                SMBR_geom = param_SMBR[0]
                SMBR_area = param_SMBR[1]
                SMBR_angle = param_SMBR[2]
                SMBR_width = param_SMBR[3]
                SMBR_height = param_SMBR[4]
                convexity1 = self.compute_convexity1(geom, area)
                convexity2 = self.compute_convexity2(area, SMBR_area)
                elongation = self.compute_elongation(SMBR_height, SMBR_width)
                compactness = self.compute_compactness(area, perimeter)
                sides = self.compute_sidesnumber(geom)
                simple_geom = sides[0]
                sides_nb = sides[1]

                #on détermine le groupe en fonction des indicateurs
                
                if area > 600000:
                    group = 1 #4
                
                elif elongation > 5:
                    group = 38 #119 OK
                    
                elif convexity2 > 0.98:
                    group = 3 #103 OK
                    
                elif convexity1 < 0.80:
                    group = 2 #105 OK
                     
                elif elongation > 0.75 and elongation < 1.25 and compactness < 0.6:
                    group = 4 #120 OK
                elif elongation > 0.75 and elongation < 1.25 and compactness > 0.6 and compactness < 0.7 and convexity2 < 0.6:
                    group = 5 #90 OK
                elif elongation > 0.75 and elongation < 1.25 and compactness > 0.6 and compactness < 0.7 and convexity2 > 0.6:
                    group = 6 #108 OK
                elif elongation > 0.75 and elongation < 1.25 and compactness > 0.7 and compactness < 0.8 and convexity2 < 0.7:
                    group = 7 #104 OK
                elif elongation > 0.75 and elongation < 1.25 and compactness > 0.7 and compactness < 0.8 and convexity2 > 0.7 and convexity2 < 0.8:
                    group = 8 #155 OK
                elif elongation > 0.75 and elongation < 1.25 and compactness > 0.7 and compactness < 0.8 and convexity2 > 0.8 and convexity2 < 0.88:
                    group = 9 #97 OK
                elif elongation > 0.75 and elongation < 1.25 and compactness > 0.7 and compactness < 0.8 and convexity2 > 0.88:
                    group = 10 #93 OK 
                elif elongation > 0.75 and elongation < 1.25 and compactness > 0.8:
                    group = 11 #141 OK
                    
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness < 0.6 and convexity2 < 0.6:
                    group = 12 #115 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness < 0.6 and convexity2 > 0.6:
                    group = 13 #94 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.6 and compactness < 0.7 and convexity2 < 0.6:
                    group = 14 #142 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.6 and compactness < 0.7 and convexity2 > 0.6 and convexity2 < 0.7:
                    group = 15 #144 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.6 and compactness < 0.7 and convexity2 > 0.7:
                    group = 16 #97 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.7 and compactness < 0.75 and convexity2 < 0.75:
                    group = 17 #115 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.7 and compactness < 0.75 and convexity2 > 0.75 and convexity2 < 0.85:
                    group = 18 #111 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.7 and compactness < 0.75 and convexity2 > 0.75:
                    group = 19 #90 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.75 and convexity2 < 0.8:
                    group = 20 #93 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.75 and convexity2 > 0.8 and convexity2 < 0.9:
                    group = 21 #151 OK
                elif ((elongation > 1.25 and elongation < 1.75) or (elongation < 1/1.25 and elongation > 1/1.75)) and compactness > 0.75 and convexity2 > 0.8:
                    group = 22 #108 OK
                    
                elif ((elongation > 1.75 and elongation < 2.25) or (elongation < 1/1.75 and elongation > 1/2.25)) and compactness < 0.6 and convexity2 < 0.6:
                    group = 23 #166 OK
                elif ((elongation > 1.75 and elongation < 2.25) or (elongation < 1/1.75 and elongation > 1/2.25)) and compactness < 0.6 and convexity2 > 0.6:
                    group = 24 #128 OK
                elif ((elongation > 1.75 and elongation < 2.25) or (elongation < 1/1.75 and elongation > 1/2.25)) and compactness > 0.6 and compactness < 0.7 and convexity2 < 0.65:
                    group = 25 #116 OK
                elif ((elongation > 1.75 and elongation < 2.25) or (elongation < 1/1.75 and elongation > 1/2.25)) and compactness > 0.6 and compactness < 0.7 and convexity2 > 0.65 and convexity2 < 0.8:
                    group = 26 #159 OK
                elif ((elongation > 1.75 and elongation < 2.25) or (elongation < 1/1.75 and elongation > 1/2.25)) and compactness > 0.6 and compactness < 0.7 and convexity2 > 0.8:
                    group = 27 #147 OK
                elif ((elongation > 1.75 and elongation < 2.25) or (elongation < 1/1.75 and elongation > 1/2.25)) and compactness > 0.7 and convexity2 < 0.88:
                    group = 28 #105 OK
                elif ((elongation > 1.75 and elongation < 2.25) or (elongation < 1/1.75 and elongation > 1/2.25)) and compactness > 0.7 and convexity2 > 0.88:
                    group = 29 #99 OK
                    
                elif ((elongation > 2.25 and elongation < 2.75) or (elongation < 1/2.25 and elongation > 1/2.75)) and compactness < 0.6 and convexity2 < 0.6:
                    group = 30 #129 OK
                elif ((elongation > 2.25 and elongation < 2.75) or (elongation < 1/2.25 and elongation > 1/2.75)) and compactness < 0.6 and convexity2 > 0.6:
                    group = 31 #146 OK
                elif ((elongation > 2.25 and elongation < 2.75) or (elongation < 1/2.25 and elongation > 1/2.75)) and compactness > 0.6 and convexity2 < 0.85:
                    group = 32 #99 OK
                elif ((elongation > 2.25 and elongation < 2.75) or (elongation < 1/2.25 and elongation > 1/2.75)) and compactness > 0.6 and convexity2 > 0.85:
                    group = 33 #136 OK
                
                elif ((elongation > 2.75 and elongation < 3.25) or (elongation < 1/2.75 and elongation > 1/3.25)) and compactness < 0.55:
                    group = 34 #134 OK
                elif ((elongation > 2.75 and elongation < 3.25) or (elongation < 1/2.75 and elongation > 1/3.25)) and compactness > 0.55:
                    group = 35 #132 OK
                    
                elif (elongation > 3.25 and elongation <3.75) or (elongation < 1/3.25 and elongation > 1/3.75):
                    group = 36 #169 OK
                    
                elif elongation > 3.75 or elongation < 1/3.75:
                    group = 37 #176 OK

                    
                # Calcul des coordonnées du centroide de chaque îlot.
                centroid = geom.centroid().asPoint()
                x_init = centroid[0]
                y_init = centroid[1]
                                
                if density > threshold:
                    feat = QgsFeature()
                    feat.setGeometry( geom )
                    feat.initAttributes(len(fields))
                    feat.setAttribute( 0, area )
                    feat.setAttribute( 1, density )
                    feat.setAttribute( 2, SMBR_area )
                    feat.setAttribute( 3, SMBR_angle )
                    feat.setAttribute( 4, SMBR_width )
                    feat.setAttribute( 5, SMBR_height )
                    feat.setAttribute( 6, convexity1 )
                    feat.setAttribute( 7, convexity2 )
                    feat.setAttribute( 8, elongation)
                    feat.setAttribute( 9, compactness )
                    feat.setAttribute( 10, sides_nb )
                    feat.setAttribute(11, x_init)
                    feat.setAttribute(12, y_init)
                    feat.setAttribute(15, group)
                    featureList.append(feat)
                i = i + 1
                progress.setValue(i)
                
          
            pr.addFeatures( featureList )
            
            vl.commitChanges()
            vl.startEditing()
            
            # Calcul de y_new (selon la taille) :
                
            level = 0
            prec_highest_feature = 0
            # Parcours de tous les groupes
            for i in range(1,39):
                highest_feature = 0
                # Parcours des îlots
                for h in vl.dataProvider().getFeatures():
                    SMBR_height = h.attributes()[5]
                    # L'entité est-elle membre du groupe en cours ?
                    if h.attributes()[15] == i:
                        # On récupère la plus haute entité du groupe
                        if SMBR_height > highest_feature:
                            highest_feature = SMBR_height
                
                # On peut ainsi connaître l'espace à laisser en hauteur entre les 2 groupes successifs
                level += highest_feature/1.5 + prec_highest_feature/1.5
                prec_highest_feature = highest_feature
                
                for h in vl.dataProvider().getFeatures():
                    if h.attributes()[15] == i:
                        # Attribution du y correspondant
                        vl.changeAttributeValue(h.id(), 14, level)
                                                    
            vl.commitChanges()
            vl.startEditing()
            
            # Calcul de x_new :
            
            # Rangement suivant l'ordre d'arrivée des îlots 
            """
            for i in range(1,39):
                prec_width = 0
                level = 0
                prec_width = 0
                width = 0
                height = 0
                for j in vl.dataProvider().getFeatures():
                    # L'entité est-elle membre du groupe en cours ?
                    if j.attributes()[15] == i:
                        width = j.attributes()[4]
                        height = j.attributes()[5]
                        level += width + prec_width + height
                        vl.changeAttributeValue(j.id(), 13, level)
                        prec_width = width
                
            vl.commitChanges()
            vl.startEditing()
            """
            
            # Rangement suivant la taille des îlots 
            for i in range(1, 39):
                liste = []
                level = 0
                prec_width = 0
                width = 0
                height = 0
                for j in vl.dataProvider().getFeatures():
                    if j.attributes()[15] == i:
                        liste += [j.attributes()[5]]
                liste.sort()
                k = 0
                while k in range(1000):
                    for j in vl.dataProvider().getFeatures():
                        if j.attributes()[15] == i and liste != []:
                            if j.attributes()[5] == liste[-1]:
                                liste.pop()
                                width = j.attributes()[4]
                                height = j.attributes()[5]
                                level += width + prec_width + height
                                vl.changeAttributeValue(j.id(), 13, level)
                                prec_width = width
                    k += 1
                                                
            vl.commitChanges()
            vl.startEditing()
            
            #On range la ville !
            for g in vl.dataProvider().getFeatures():
                geom = g.geometry()
                
                # On récupère les anciennes et nouvelles coordonnées.
                x_init = g.attributes()[11]
                y_init = g.attributes()[12]
                x_new = g.attributes()[13]
                y_new = g.attributes()[14]
                                
                # Calcul des paramètres du déplacement.
                dx = x_new - x_init
                dy = y_new - y_init
                centre_rota = QgsPoint(x_new,y_new)
                if SMBR_angle < 90:
                    angle_rota = 90 - SMBR_angle #en degré
                else:
                    angle_rota = SMBR_angle - 90
                
                # Translation.
                isTransformOk = geom.translate(dx,dy)
                if (isTransformOk != 0):
                    return "error"
                vl.dataProvider().changeGeometryValues({g.id():geom})
                
                # Rotation des îlots
                if SMBR_angle < 90:
                    isRotOk = geom.rotate(angle_rota, centre_rota)
                    if (isRotOk != 0):
                        return "error"
                    vl.dataProvider().changeGeometryValues({g.id():geom})
                else:
                    isRotOk = geom.rotate(-angle_rota, centre_rota)
                    if (isRotOk != 0):
                        return "error"
                    vl.dataProvider().changeGeometryValues({g.id():geom})

            vl.commitChanges()

            self.iface.messageBar().clearWidgets()
            if self.save:
                error = QgsVectorFileWriter.writeAsVectorFormat(vl, filename, "UTF-8", None, "ESRI Shapefile")
            if self.load:
                QgsMapLayerRegistry.instance().addMapLayer(vl)

