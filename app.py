#!/usr/bin/env python3

import sys
import os

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))

from qgis.core import *
from PyQt5.QtCore import QVariant
from TidyCity.indicatorCalculation import *
from TidyCity.classification import *
from TidyCity.square_packing import *



input_dir = "/home/mbrasebin/Documents/Donnees/Test/TidyCity/world/"
output_dir = "/home/mbrasebin/Documents/Donnees/temp/"

fid_atribute = "fid"

layerName = "bob"

# supply path to qgis install location
QgsApplication.setPrefixPath("/usr", True)

# create a reference to the QgsApplication, setting the second argument to False disables the GUI
qgs = QgsApplication([], False)

# load providers
qgs.initQgis()

layer_polygons = QgsVectorLayer(os.path.join(input_dir,'world.shp'), 'polygons', 'ogr')

#Step 1 : calculating indicator
layerOut = calculate(layerName,layer_polygons,fid_atribute);
#Determining the attribute to use for the classification
attributes = ["area", "elongation" , "compact."]
#Output classification attribute
classAttribute = "class"
#Step 2 : Applying the classification
layerClassified = kmeans(layerOut, attributes, 10, layerName, classAttribute, fid_atribute)
#Step 3 ! Applying a naive layout
#Secondary attribute to sort the feature (descending)
attSecondary = "area"
newLayoutLayer = naive_layout(layerClassified, classAttribute , attSecondary, layerName)

#Step 3 bis : other layout method (with the bounding boxes to debug the rectangle packing)
otherLayout, layoutBoundingBox = advanced_layout(layerClassified, classAttribute , attSecondary, layerName)

#Export

#Export features with attributes
error = QgsVectorFileWriter.writeAsVectorFormat(layerOut, os.path.join(output_dir,"indicator.shp"),"utf-8", layerOut.crs(), "ESRI Shapefile")

#Export features with  classificatino
error = QgsVectorFileWriter.writeAsVectorFormat(layerClassified, os.path.join(output_dir,"classified.shp"),"utf-8", layerClassified.crs(), "ESRI Shapefile")

#Export layout
crs=QgsCoordinateReferenceSystem("epsg:-1")
#Naive layout
error = QgsVectorFileWriter.writeAsVectorFormat(newLayoutLayer, os.path.join(output_dir,"naiveLayout.shp"),"utf-8", crs, "ESRI Shapefile")
#Packed layout
error = QgsVectorFileWriter.writeAsVectorFormat(otherLayout, os.path.join(output_dir,"otherLayout.shp"),"utf-8", crs, "ESRI Shapefile")
#Bounding boxes used for pack layout production
error = QgsVectorFileWriter.writeAsVectorFormat(layoutBoundingBox, os.path.join(output_dir,"boundingBox.shp"),"utf-8", crs, "ESRI Shapefile")

qgs.exitQgis()

