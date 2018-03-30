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


input_dir = "/home/mbrasebin/Documents/Donnees/Test/StageJimmy/"
output_dir = "/home/mbrasebin/Documents/Donnees/temp/"

fid_atribute = "fid"
layerName = "bob"

# supply path to qgis install location
QgsApplication.setPrefixPath("/usr", True)

# create a reference to the QgsApplication, setting the second argument to False disables the GUI
qgs = QgsApplication([], False)

# load providers
qgs.initQgis()

layer_polygons = QgsVectorLayer(os.path.join(input_dir,'extract.shp'), 'polygons', 'ogr')

#Step 1 : calculating indicator
layerOut = calculate(layerName,layer_polygons,fid_atribute);
#Determining the attribute to use for the classification
attributes = ["area", "elongation" , "compact."]
#Applying the classification
layerClassified = kmeans(layerOut, attributes, 3, layerName, "class", fid_atribute)


error = QgsVectorFileWriter.writeAsVectorFormat(layerOut, os.path.join(output_dir,"indicator.shp"),"utf-8", layerOut.crs(), "ESRI Shapefile")


if error == QgsVectorFileWriter.NoError:
    print("success!")
else:
    print(error)



error = QgsVectorFileWriter.writeAsVectorFormat(layerClassified, os.path.join(output_dir,"classified.shp"),"utf-8", layerClassified.crs(), "ESRI Shapefile")


if error == QgsVectorFileWriter.NoError:
    print("success!")
else:
    print(error)



qgs.exitQgis()

