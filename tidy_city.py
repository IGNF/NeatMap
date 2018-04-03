# -*- coding: utf-8 -*-
"""
/***************************************************************************
 TidyCity
                                 A QGIS plugin
 A simple QGIS python plugin for building tidy cities.
                              -------------------
        begin                : 2016-11-30
        git sha              : $Format:%H$
        copyright            : (C) 2016 - 2018 by IGN
        email                : julien.perret@gmail.com; mickael.brasebin@ign.fr
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
import os.path
import math
from random import randrange

from PyQt5.QtCore import QSettings, QTranslator, qVersion, QCoreApplication, QVariant, Qt, pyqtSlot
from PyQt5.QtGui import QIcon, QTransform
from PyQt5.QtWidgets import QAction, QProgressBar, QCheckBox, QFrame, QVBoxLayout
from .resources import *

from qgis.core import *
from qgis.gui import *

#Internal imports
from .indicatorCalculation import *
from .classification import *
from .square_packing import *
#GUI import
from .tidy_city_dialog import TidyCityDialog



try:
    import pip
except:
    execfile(os.path.join(self.plugin_dir, get_pip.py))
    import pip
    # just in case the included version is old
    pip.main(['install','--upgrade','pip'])

try:
    import somelibrary
except:
    pip.main(['install','-U' , 'scikit-learn'])



class TidyCity:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        print("Initialisation")
        

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

        

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginVectorMenu(
                self.tr(u'&TidyCity'),
                action)
            self.iface.removeToolBarIcon(action)
        # remove the toolbar
        del self.toolbar

    """
    Fonction run.
    """

    def run(self):
        #Run method that performs all the real work
        self.prepareGUI()
        # show the dialog
        self.dlg.show()
        
        # Run the dialog event loop
        result = self.dlg.exec_()

        return 


	
    """
    GUI Iniialization
    """
    def prepareGUI(self):   
        #Button to process calculation
        self.dlg.pushButtonCalculation.clicked.connect(self.processCalculation)
        self.dlg.pushButtonClassification.clicked.connect(self.processClassification)  
        self.dlg.pushButtonLayout.clicked.connect(self.processLayout)      
        
        #DropDown are updated when dropdown layer are activated
        self.dlg.inputPolygonLayer.activated.connect(self.updatePolygonLayer)
        self.dlg.inputPolygonLayerClass.activated.connect(self.updatePolygonLayerClass)
        self.dlg.inputPolygonLayerLayout.activated.connect(self.updateLayoutLayer)
        
        #Updating the list of available attributes
        scrollArea = self.dlg.scrollArea;
        scrollArea.setWidgetResizable(True)
        scrollArea.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
        inner = QFrame(scrollArea)
        inner.setLayout(QVBoxLayout())
        scrollArea.setWidget(inner)
        #Updating all the dropboxes
        self.updateDropBoxes()
        
        
    """
    
    Refresh/updating interface
    
    """    
        #Update the dropboxes that contains the layer list
    def updateDropBoxes(self):
        """Update the  dropdowns with layers"""
        layers = QgsProject.instance().mapLayers().values()

        self.dlg.inputPolygonLayer.clear()
        self.dlg.inputPolygonLayerClass.clear()
        self.dlg.inputPolygonLayerLayout.clear()

        
        for layer in layers:
            self.dlg.inputPolygonLayer.addItem(layer.name(),layer)
            self.dlg.inputPolygonLayerClass.addItem(layer.name(),layer)
            self.dlg.inputPolygonLayerLayout.addItem(layer.name(),layer)
        #Refresh the dropboxes that list attributes 
        self.updatePolygonLayer()
        self.updatePolygonLayerClass()
        self.updateLayoutLayer()
        
    """
    
    Section 1
    
    """          
        
        
         
    #Refresh the ID attribute list from indicator calculation step
    def refreshAttributeDropBox(self):  
        #Listing layers  
        layers = QgsProject.instance().mapLayers().values()
        self.dlg.intputIDChoice.clear()        
        
        selectedInputLayerIndex = self.dlg.inputPolygonLayer.currentIndex()
        
        if selectedInputLayerIndex > -1 :
            #Getting the selected layer 
            selectedInputLayer = self.dlg.inputPolygonLayer.itemData(selectedInputLayerIndex)
            
            count = selectedInputLayer.featureCount();

            for a in selectedInputLayer.fields():
                    self.dlg.intputIDChoice.addItem(a.displayName(),a)
 

     
    #Action when layer from indicator calculation is refreshed    
    def updatePolygonLayer(self):
         self.refreshAttributeDropBox()
   
        
    """
    
    Section 2
    
    """          
    #Action when layer from classification is refreshed
    def updatePolygonLayerClass(self):
        self.refreshDropDownLayerPanel()
        self.refreshAttributeDropBoxClassif()

    #Refresh the ID attribute list from indicator calculation step
    def refreshAttributeDropBoxClassif(self):  
        #Listing layers  
        layers = QgsProject.instance().mapLayers().values()
        self.dlg.intputIDChoiceClassif.clear()        
        
        selectedInputLayerIndex = self.dlg.inputPolygonLayerClass.currentIndex()
        
        if selectedInputLayerIndex > -1 :
            #Getting the selected layer 
            selectedInputLayer = self.dlg.inputPolygonLayerClass.itemData(selectedInputLayerIndex)
            
            count = selectedInputLayer.featureCount();

            for a in selectedInputLayer.fields():
                    self.dlg.intputIDChoiceClassif.addItem(a.displayName(),a)
                    
    
    
    

    # Refresh the panel with the checkbox list                
    def refreshDropDownLayerPanel(self):
        layout =  self.dlg.scrollArea.widget().layout()
        #Cleaning layout
        
        for i in reversed(range(layout.count())): 
            widgetToRemove = layout.itemAt( i ).widget()
            # remove it from the layout list
            layout.removeWidget( widgetToRemove )
            # remove it from the gui
            widgetToRemove.setParent( None )
        
        layers = QgsProject.instance().mapLayers().values()
        
        selectedInputLayerIndex = self.dlg.inputPolygonLayerClass.currentIndex()
        
        if selectedInputLayerIndex > -1 :
            #Getting the selected layer 
            selectedInputLayer = self.dlg.inputPolygonLayerClass.itemData(selectedInputLayerIndex)
            
            count = selectedInputLayer.featureCount();


            for a in selectedInputLayer.fields():
                if (a.isNumeric()) :
                    checkBox = QCheckBox(a.displayName())
                    layout.addWidget(checkBox)
                    checkBox.setChecked(True)


    def categorizedColor(self, vectorLayer, classAttNam):
        # provide file name index and field's unique values
        fni = vectorLayer.fields().indexFromName(classAttNam)
        unique_values = vectorLayer.uniqueValues(fni)
        
        # fill categories
        categories = []
        for unique_value in unique_values:
            # initialize the default symbol for this geometry type
            symbol =     QgsSymbol.defaultSymbol(vectorLayer.geometryType())
        
            # configure a symbol layer
            layer_style = {}
            layer_style['color'] = '%d, %d, %d' % (randrange(0, 256), randrange(0, 256), randrange(0, 256))
            layer_style['outline'] = '#000000'
            symbol_layer = QgsSimpleFillSymbolLayer.create(layer_style)
        
            # replace default symbol layer with the configured one
            if symbol_layer is not None:
                symbol.changeSymbolLayer(0, symbol_layer)
        
            # create renderer object
            category = QgsRendererCategory(unique_value, symbol, str(unique_value))
            # entry for the list of category items
            categories.append(category)
        
        # create renderer object
        renderer = QgsCategorizedSymbolRenderer(classAttNam, categories)
        
        # assign the created renderer to the layer
        if renderer is not None:
            vectorLayer.setRenderer(renderer)
        
        vectorLayer.triggerRepaint()
        
    """
    
    Section 3
    
    """    
    def updateLayoutLayer(self):
        self.updateIDClassification()
        self.updateSecondaryRanking()
    
    
    def updateIDClassification(self):
        layers = QgsProject.instance().mapLayers().values()
        self.dlg.classificationAttributeLayout.clear()        
        
        selectedInputLayerIndex = self.dlg.inputPolygonLayerLayout.currentIndex()
        
        if selectedInputLayerIndex > -1 :
            #Getting the selected layer 
            selectedInputLayer = self.dlg.inputPolygonLayerLayout.itemData(selectedInputLayerIndex)
            
            count = selectedInputLayer.featureCount();

            for a in selectedInputLayer.fields():
                if a.isNumeric():
                    self.dlg.classificationAttributeLayout.addItem(a.displayName(),a)
        
    def updateSecondaryRanking(self):    
        layers = QgsProject.instance().mapLayers().values()
        self.dlg.inputSecondaryAttributeLayout.clear()        
        
        selectedInputLayerIndex = self.dlg.inputPolygonLayerLayout.currentIndex()
        
        if selectedInputLayerIndex > -1 :
            #Getting the selected layer 
            selectedInputLayer = self.dlg.inputPolygonLayerLayout.itemData(selectedInputLayerIndex)
            
            count = selectedInputLayer.featureCount();

            for a in selectedInputLayer.fields():
                if a.isNumeric():
                    self.dlg.inputSecondaryAttributeLayout.addItem(a.displayName(),a)            

    """
    
    
    Execution phase 1 : calculation
    
    """    
    
    #Processing calculation when ok button from Indicator calculation is pressed
    def processCalculation(self):
        #Getting the polygonlayer
        selectedInputLayerIndex = self.dlg.inputPolygonLayer.currentIndex()
        selectedInputLayer = self.dlg.inputPolygonLayer.itemData(selectedInputLayerIndex)
        QgsMessageLog.logMessage("Layer selected : " + selectedInputLayer.name(), "Tidy City", Qgis.Info)
        layername = self.dlg.LineEditTemporaryLayerName.text()    
        QgsMessageLog.logMessage("Calculating indicator on layer : " + layername, "Tidy City", Qgis.Info)
        intputIDChoiceIndex = self.dlg.intputIDChoice.currentIndex()
        intputIDChoiceValue = self.dlg.intputIDChoice.itemData(intputIDChoiceIndex).displayName()
        QgsMessageLog.logMessage("ID value : " + intputIDChoiceValue, "Tidy City", Qgis.Info)     
        QgsMessageLog.logMessage("Calculating indicator on layer : " + layername, "Tidy City", Qgis.Info)            
        vlOut = calculate(layername, selectedInputLayer,intputIDChoiceValue);
        QgsMessageLog.logMessage("Adding layer to map", "Tidy City", Qgis.Info)
        QgsProject.instance().addMapLayer(vlOut)
        
         #Refresh after processing
         
         #Updating all layers as a new layer is added
        self.updateDropBoxes()
        
        #Selection of new layer in classificaion menue
        self.selectItem(self.dlg.inputPolygonLayerClass,vlOut.name())
        
        #Updateing classificaion content
        self.updatePolygonLayerClass()
        self.selectItem(self.dlg.intputIDChoiceClassif, intputIDChoiceValue)
        self.selectItem(self.dlg.inputPolygonLayer,selectedInputLayer.name())
    
    
    
    """
    
    
    Execution phase 2 : classification
    
    """    
    
    
    def processClassification(self):
        selectedInputLayerIndex = self.dlg.inputPolygonLayerClass.currentIndex()
        selectedInputLayer = self.dlg.inputPolygonLayerClass.itemData(selectedInputLayerIndex)
        QgsMessageLog.logMessage("Layer selected : " + selectedInputLayer.name(), "Tidy City", Qgis.Info)
        attributes = self.listingCheckedAttributes()
        QgsMessageLog.logMessage("Attributes selected : " + str(len(attributes)), "Tidy City", Qgis.Info)
         
        strNumberOfClasses = self.dlg.classifNumberOfClasses.text()
        numberOfClasses = int(strNumberOfClasses)
        
        QgsMessageLog.logMessage("Number of classes : " + str(numberOfClasses), "Tidy City", Qgis.Info)
        
        layername = self.dlg.classLayerName.text()    
        QgsMessageLog.logMessage("Calculating indicator on layer : " + layername, "Tidy City", Qgis.Info)
        
        intputIDChoiceIndex = self.dlg.intputIDChoiceClassif.currentIndex()
        intputIDChoiceValue = self.dlg.intputIDChoiceClassif.itemData(intputIDChoiceIndex).displayName()
        QgsMessageLog.logMessage("ID value : " + intputIDChoiceValue, "Tidy City", Qgis.Info)
        
        
        attributeClass = self.dlg.lineEditAttClass.text()
        
        QgsMessageLog.logMessage("Attribute for classification: " + attributeClass, "Tidy City", Qgis.Info)               
        
        layerClassified = kmeans(selectedInputLayer, attributes, numberOfClasses, layername, attributeClass, intputIDChoiceValue)
        QgsMessageLog.logMessage("Adding layer to map", "Tidy City", Qgis.Info)
        QgsProject.instance().addMapLayer(layerClassified)
        self.categorizedColor(layerClassified, attributeClass)
        
        #Refresh after processing
        
         #Updating all layers as a new layer is added
        self.updateDropBoxes()
        
        #Selection of new layer in classificaion menue
        self.selectItem(self.dlg.inputPolygonLayerLayout,layerClassified.name())
        
        #Updateing classificaion content
        self.updatePolygonLayerClass()
        self.updateLayoutLayer()
        self.selectItem(self.dlg.classificationAttributeLayout, attributeClass)
        self.selectItem(self.dlg.inputSecondaryAttributeLayout,"area")
        
    """

    Execution phase 3 : layout
    
    """  
    def processLayout(self):
        selectedInputLayerIndex = self.dlg.inputPolygonLayerLayout.currentIndex()
        selectedInputLayer = self.dlg.inputPolygonLayerLayout.itemData(selectedInputLayerIndex)        
        QgsMessageLog.logMessage("Layer selected : " + selectedInputLayer.name(), "Tidy City", Qgis.Info)
        
        intputClassificationAttributeIndex = self.dlg.classificationAttributeLayout.currentIndex()
        intputClassificationAttribute = self.dlg.classificationAttributeLayout.itemData(intputClassificationAttributeIndex).displayName()
        QgsMessageLog.logMessage("Classification attribute : " + intputClassificationAttribute, "Tidy City", Qgis.Info)
        
        intputClassificationSecondaryAttributeIndex = self.dlg.inputSecondaryAttributeLayout.currentIndex()
        intputClassificationSecondaryAttribute = self.dlg.inputSecondaryAttributeLayout.itemData(intputClassificationSecondaryAttributeIndex).displayName()
        QgsMessageLog.logMessage("Secondary classification attribute : " + intputClassificationSecondaryAttribute, "Tidy City", Qgis.Info)
        
        layerName = self.dlg.inputLayerNameLayout.text()
        QgsMessageLog.logMessage("Attribute for classification: " + layerName, "Tidy City", Qgis.Info)   
        
        newLayoutLayer = naive_layout(selectedInputLayer, intputClassificationAttribute , intputClassificationSecondaryAttribute, layerName)

        QgsProject.instance().addMapLayer(newLayoutLayer)
        self.categorizedColor(newLayoutLayer, intputClassificationAttribute)
    
    
        
    """
    
    
    Util functions
    
    """  

    def selectItem(self, dialog, text):
        for i in range(0,dialog.count()):
            if text in dialog.itemText(i):
                dialog.setCurrentIndex(i)
    
    def listingCheckedAttributes(self):
        attributes = []
        layout =  self.dlg.scrollArea.widget().layout()
        for i in reversed(range(layout.count())):
            if  layout.itemAt(i).widget().isChecked():
                attributes.append(layout.itemAt(i).widget().text())
            #QgsMessageLog.logMessage("--WIDGET---", "Tidy City", Qgis.Info)
            #QgsMessageLog.logMessage(""+str(type(layout.itemAt(i).widget())), "Tidy City", Qgis.Info)
        return attributes


