import sys
import os
from qgis.core import *
from PyQt5.QtCore import QVariant
from indicatorCalculation import *

input_dir = "/home/mbrasebin/Documents/Donnees/Test/StageJimmy/"
output_dir = "/home/mbrasebin/Documents/Donnees/temp/"

# supply path to qgis install location
QgsApplication.setPrefixPath("/usr", True)

# create a reference to the QgsApplication, setting the second argument to False disables the GUI
qgs = QgsApplication([], False)

# load providers
qgs.initQgis()
print(qgs.showSettings())

layer_polygons = QgsVectorLayer(os.path.join(input_dir,'extract.shp'), 'polygons', 'ogr')


layerOut = calculate("bob",layer_polygons,"fid");

error = QgsVectorFileWriter.writeAsVectorFormat(layerOut, os.path.join(output_dir,"my_shapes.shp"),"utf-8", layerOut.crs(), "GeoJSON")

if error == QgsVectorFileWriter.NoError:
    print("success!")


qgs.exitQgis()

