# (True) => Means that all attributes will be copied
#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

PACKAGE_PARENT = '..'
SCRIPT_DIR = os.path.dirname(os.path.realpath(os.path.join(os.getcwd(), os.path.expanduser(__file__))))
sys.path.append(os.path.normpath(os.path.join(SCRIPT_DIR, PACKAGE_PARENT)))


from qgis.core import *
from PyQt5.QtCore import QVariant
from NeatMap.indicatorCalculation import *
from NeatMap.classification import *
from NeatMap.square_packing import *




def run():
	print("Initializing QGS")
	# supply path to qgis install location
	QgsApplication.setPrefixPath("/usr", True)

	# create a reference to the QgsApplication, setting the second argument to False disables the GUI
	qgs = QgsApplication([], False)

	# load providers
	qgs.initQgis()

	input_file = os.path.join(SCRIPT_DIR,'data_test/world.shp')
	output_dir =  os.path.join(SCRIPT_DIR,'data_test/')
	print(input_file)
	print(output_dir)
	

	fid_atribute = "fid"

	layerName = "layer"


	print("QGIS was init")

	layer_polygons = QgsVectorLayer(input_file, 'polygons', 'ogr')

	#Export layout
	crs=QgsCoordinateReferenceSystem("epsg:-1")

	saveOption = QgsVectorFileWriter.SaveVectorOptions()
	saveOption.driverName = "ESRI ShapeFile"
	saveOption.fileEncoding = "utf-8"
	
	transformContext = QgsProject.instance().transformContext()
	
	print("Calculate indicators")
	#Step 1 : calculating indicator
	# (layerName) => The name of the output layer
	# (layer_polygons) => The input layer
	# (fid_atribute) => The name of the fid attribute
	# (True) => Means that all attributes will be copied
	layerOut = calculate(layerName,layer_polygons,fid_atribute, True);

	print("Export indicator shapefile")
	#Export features with attributes
	error = QgsVectorFileWriter.writeAsVectorFormatV2(layerOut, os.path.join(output_dir,"indicator.shp"), transformContext, saveOption )


	#Determining the attribute to use for the classification
	attributes = ["area", "elongation" , "compact."]
	#Output classification attribute
	classAttribute = "class"

	#Step 2 : Applying the classification
	print("Classification")
	# (layerOut) : the input layer (the output from previous step)
	# (attributes) : the list of attributes on which the classificatino will be proceeded
	# (10) : the number of classes
	# (layerName) : the name of the output layer name
	# (classAttribute) : the name of the attribute in which the class will be stored)
	# f(id_atribute) => The name of the fid attribute
	# (True) => Means that all attributes will be copied
	layerClassified = kmeans(layerOut, attributes, 10, layerName, classAttribute, fid_atribute, True)

	print("Export classified layer")
	#Export features with  classificatinoadvanced_layout
	error = QgsVectorFileWriter.writeAsVectorFormatV2(layerClassified, os.path.join(output_dir,"classified.shp"), transformContext, saveOption )


	#Step 3 ! Applying a naive layout
	#Secondary attribute to sort the feature (descending)
	attSecondary = "area"

	print("Preparing layout")
	# (layerClassified) : the input layer (the output from previous step)
	# (classAttribute) : the name of the attribute in which the class will be stored)
	# (attSecondary) : the secondary ranking attribute
	# (layerName) : the name of the output layer name
	# (True) => Means that all attributes will be copied
	newLayoutLayer = naive_layout(layerClassified, classAttribute , attSecondary, layerName, True)
	print("Export layout")
	#Naive layout
	error = QgsVectorFileWriter.writeAsVectorFormatV2(newLayoutLayer, os.path.join(output_dir,"naiveLayout.shp"), transformContext, saveOption )

	print("Preparing layout2")
	#Step 3 bis : other layout method (with the bounding boxes to debug the rectangle packing)
	# (layerClassified) : the input layer (the output from previous step)
	# (classAttribute) : the name of the attribute in which the class will be stored)
	# (attSecondary) : the secondary ranking attribute
	# (layerName) : the name of the output layer name
	# (True) => Means that all attributes will be copied
	otherLayout, layoutBoundingBox = advanced_layout(layerClassified, classAttribute , attSecondary, layerName, True)

	print("Export layout")
	#Bounding boxes used for pack layout production
	error = QgsVectorFileWriter.writeAsVectorFormatV2(layoutBoundingBox, os.path.join(output_dir,"boundingBox.shp"), transformContext, saveOption )

	print("Export layout")
	#Packed layout
	error = QgsVectorFileWriter.writeAsVectorFormatV2(otherLayout, os.path.join(output_dir,"otherLayout.shp"), transformContext, saveOption )

	print("Preparing layout3")
	#Step 3 ter : other layout method, less optimal that in Step 3 bis. The widestbox is placed at first and the other one
	#Are placed on this box, according to the x axis etc (like making a wall with bricks)
	# (layerClassified) : the input layer (the output from previous step)
	# (classAttribute) : the name of the attribute in which the class will be stored)
	# (attSecondary) : the secondary ranking attribute
	# (layerName) : the name of the output layer name
	# (True) => Means that all attributes will be copied
	otherLayout2, layoutBoundingBox2 = fast_layout(layerClassified, classAttribute , attSecondary, layerName, True)

	print("Export layout")
	#Bounding boxes used for fast layout production
	error = QgsVectorFileWriter.writeAsVectorFormatV2(layoutBoundingBox2, os.path.join(output_dir,"boundingBox2.shp"), transformContext, saveOption )

	print("Export layout")
	#Packed layout
	error = QgsVectorFileWriter.writeAsVectorFormatV2(otherLayout2, os.path.join(output_dir,"otherLayout2.shp"), transformContext, saveOption )


run()
