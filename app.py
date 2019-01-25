# (True) => Means that all attributes will be copied#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from pathlib import Path

# Chercher les chemins de QGIS sur Linux, Windows ou MacOS
qgsRoot = None
if sys.platform == 'linux':
    for d in ['/usr', '/usr/local', '/opt/qgis']:
        if Path(d + '/lib/qgis').exists():
            qgsRoot = Path(d)
            sys.path.append(str(qgsRoot/'share/qgis/python'))
            print('libqgis : '+d + '/lib/qgis')
elif sys.platform == 'win32':
    for d in Path('C:/Program Files').iterdir():
        if 'QGIS 3' in str(d) or 'OSGeo4W64' in str(d):
            qgsRoot = d
    if not qgsRoot :
        for d in Path('C:/').iterdir():
            if 'OSGeo4W64' in str(d):
                qgsRoot = d
    if qgsRoot:
        sys.path.append(str(qgsRoot/'apps/qgis/python'))
elif sys.platform == 'darwin':
    if Path('/Applications/QGIS.app').exists():
        qgsRoot = Path('/Applications/QGIS.app')
        sys.path.append(str(qgsRoot/'Contents/Resources/python/'))

if not qgsRoot:
    print('Unable to locate QGIS 3. Exiting now...')
    sys.exit()
print(sys.path)
from qgis.core import *

from PyQt5.QtCore import QVariant
from NeatMap.indicatorCalculation import *
from NeatMap.classification import *
from NeatMap.square_packing import *



input_file = os.path.join(SCRIPT_DIR,'data_test/world.shp')
output_dir =  os.path.join(SCRIPT_DIR,'data_test/')
print(input_file)
print(output_dir)

fid_atribute = "fid"

layerName = "layer"

# supply path to qgis install location
QgsApplication.setPrefixPath("/usr", True)

# create a reference to the QgsApplication, setting the second argument to False disables the GUI
qgs = QgsApplication([],GUIenabled=False)

# load providers
qgs.initQgis()

layer_polygons = QgsVectorLayer(input_file, 'polygons', 'ogr')

#Export layout
crs=QgsCoordinateReferenceSystem("epsg:-1")

#Step 1 : calculating indicator
# (layerName) => The name of the output layer
# (layer_polygons) => The input layer
# (fid_atribute) => The name of the fid attribute
# (True) => Means that all attributes will be copied
layerOut = calculate(layerName,layer_polygons,fid_atribute, True);

#Export features with attributes
error = QgsVectorFileWriter.writeAsVectorFormat(layerOut, os.path.join(output_dir,"indicator.shp"),"utf-8", layerOut.crs(), "ESRI Shapefile")


#Determining the attribute to use for the classification
attributes = ["area", "elongation" , "compact."]
#Output classification attribute
classAttribute = "class"

#Step 2 : Applying the classification
# (layerOut) : the input layer (the output from previous step)
# (attributes) : the list of attributes on which the classificatino will be proceeded
# (10) : the number of classes
# (layerName) : the name of the output layer name
# (classAttribute) : the name of the attribute in which the class will be stored)
# f(id_atribute) => The name of the fid attribute
# (True) => Means that all attributes will be copied
layerClassified = kmeans(layerOut, attributes, 10, layerName, classAttribute, fid_atribute, True)

#Export features with  classificatinoadvanced_layout
error = QgsVectorFileWriter.writeAsVectorFormat(layerClassified, os.path.join(output_dir,"classified.shp"),"utf-8", layerClassified.crs(), "ESRI Shapefile")


#Step 3 ! Applying a naive layout
#Secondary attribute to sort the feature (descending)
attSecondary = "area"

# (layerClassified) : the input layer (the output from previous step)
# (classAttribute) : the name of the attribute in which the class will be stored)
# (attSecondary) : the secondary ranking attribute
# (layerName) : the name of the output layer name
# (True) => Means that all attributes will be copied
newLayoutLayer = naive_layout(layerClassified, classAttribute , attSecondary, layerName, True)

#Naive layout
error = QgsVectorFileWriter.writeAsVectorFormat(newLayoutLayer, os.path.join(output_dir,"naiveLayout.shp"),"utf-8", crs, "ESRI Shapefile")


#Step 3 bis : other layout method (with the bounding boxes to debug the rectangle packing)
# (layerClassified) : the input layer (the output from previous step)
# (classAttribute) : the name of the attribute in which the class will be stored)
# (attSecondary) : the secondary ranking attribute
# (layerName) : the name of the output layer name
# (True) => Means that all attributes will be copied
otherLayout, layoutBoundingBox = advanced_layout(layerClassified, classAttribute , attSecondary, layerName, True)

#Bounding boxes used for pack layout production
error = QgsVectorFileWriter.writeAsVectorFormat(layoutBoundingBox, os.path.join(output_dir,"boundingBox.shp"),"utf-8", crs, "ESRI Shapefile")


#Packed layout
error = QgsVectorFileWriter.writeAsVectorFormat(otherLayout, os.path.join(output_dir,"otherLayout.shp"),"utf-8", crs, "ESRI Shapefile")

#Step 3 ter : other layout method, less optimal that in Step 3 bis. The widestbox is placed at first and the other one
#Are placed on this box, according to the x axis etc (like making a wall with bricks)
# (layerClassified) : the input layer (the output from previous step)
# (classAttribute) : the name of the attribute in which the class will be stored)
# (attSecondary) : the secondary ranking attribute
# (layerName) : the name of the output layer name
# (True) => Means that all attributes will be copied
otherLayout2, layoutBoundingBox2 = fast_layout(layerClassified, classAttribute , attSecondary, layerName, True)

#Bounding boxes used for fast layout production
error = QgsVectorFileWriter.writeAsVectorFormat(layoutBoundingBox2, os.path.join(output_dir,"boundingBox2.shp"),"utf-8", crs, "ESRI Shapefile")


#Packed layout
error = QgsVectorFileWriter.writeAsVectorFormat(otherLayout2, os.path.join(output_dir,"otherLayout2.shp"),"utf-8", crs, "ESRI Shapefile")

qgs.exitQgis()

