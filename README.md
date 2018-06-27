TidyCity
============

TidyCity is a plugin for [QGIS](https://www.qgis.org/fr/site/) that allows the production of "tidy" set of polygon features through : morphological indicators calculation, classification of the polygonal features usin these indicators and the disposition of the features through layout generation methods.

The project is developed as an Open-Source library based on :
- [QGIS API V3.0](https://www.qgis.org/fr/site/), for morphological operators and layout generation ;
- [Scikit learn 0.19.1](http://scikit-learn.org/stable/index.html) :  for the classifications.


Introduction
---------------------

This research library is developed from a [ENSG](http://www.ensg.eu) student work and continues with [COGIT team](http://recherche.ign.fr/labos/cogit/accueilCOGIT.php) research developments.

The intial idea was based on the artistic work of [Armel Caron : tidy cities](http://www.armellecaron.fr/works/les-villes-rangees/) and to quetion the ability of automatic algorithms to produce similar layout. The idea is not to produce on-demand art but to asses the expressivity of common morphological indicators to discriminate polygon shapes and  the part of subjectivity in the original artistic productions.


General principle
---------------------

![Schema of the worflow of the TidyCityPlugin](https://raw.githubusercontent.com/julienperret/TidyCity/image_doc/doc_images/rankingPrinciple.png)


The general idea of the approach is to regroup the feature with similar charateristics into group and to correctly arrange these groupss. These charateristics are assessed through a set of morphological indicators and the groups are created with a classification method. Inside the group, an attribute is used to rank the different features (for example, the area in the image presenting the principle). Each group can be modeled as a rectangle and the aim of the layout generator is to find a proper way to dispose these rectangles.


The workflow
---------------------
![Schema of the worflow of the TidyCityPlugin](https://raw.githubusercontent.com/julienperret/TidyCity/image_doc/doc_images/generalSchema.png)



The plugin is composed of 3 steps :
- (1) the calculation of common morphological indicators on a polygon layer ;
- (2) the classification through a k-mean method ;
- (3) the generation of classified layouts.
If this three steps are consecutive, they can be ran independently if a layer with the relevant attributes is provided. For example, if you have produced your own indicators, you can directly proceed to the classification or if your features are already classified to generate a layout with them.



Plugin installation
---------------------
The only requirement is to get QGIS 3.0 or later installed. You can download it from [QGIS official website](https://www.qgis.org/fr/site/).

Currently the plugin is not on QGIS repositories, you have to install it manually. You have to download  the [automatically generated zip file](https://github.com/julienperret/TidyCity/archive/master.zip) and to unzip it in the plugins folder (https://gis.stackexchange.com/questions/274311/qgis-3-plugin-folder-location).

In QGIS, in the "Extenion" menu > "Install Extension" option, you have just to activate the "TidyCity" plugin.

NOTE : if the plugin is mising, you may have to allow experimental plugins, in the parameter menu.

GUI of the plugin
---------------------

The GUI of the plugin is basically composed of three parts that reflect the three steps of the workflow (indicator calculation, classification and layout generation). Each part has its own options and own "Ok" button that allows to run separatly the different steps.

**Note : the option "Copy attributes between two steps" is a general option. It allows to keep the attribute of the layer between two steps and works for each step.**


![GUI of the plugin](https://raw.githubusercontent.com/julienperret/TidyCity/image_doc/doc_images/generalGUI.png)
Indicators Calculation
---------------------
This steps aims at calculating morphological indicators from a polygonal layer.

It requires as input :
- **Input layer ** : The name of a polygonal layer with an ID field ;
- **Output layer name** : The name of the output layer ;
- **ID attribute** : The name of the attribute field.

By clicking on the "Ok" button of this section, a new layer with the following indicators is produced and added in QGIS :
- **area** : the area of the geometry ;
- **SMBR_area** : the area of the smallest bounding rectangle ;
- **SMBR_angle** :  the orientation of the smallest bounding rectangle ;
- **SMBR_h** :  the height of the smallest bounding rectangle ;
- **SMBR_w** :  the width of the smallest bounding rectangle ;
- **convexity1** : convexity relative to the convex hull ;
- **convexity2** : convexity relative to the smallest bounding rectangle ;
- **elongation** : elongation of the building (between 0 and 1) ;
- **compact** : compactness of the polygon ;
- **area/perim** : ratio between area and perimeter ;
- **complexity** : the number of segments of the polygon.

Classification
---------------------
This step determines different classes of features through a k-mean classification method.

It requires as input :
- **Input layer ** : The name of a polygonal layer with an ID field ;
- **ID attribute** : The name of the attribute field ;
- In the central panel, a list of numerical attributes can be selected. You can use the indicators calculated during the previsous step, your own indicators or a combination of both. During the process, the attribute values are scaled between 0 and 1;
- **Number of classes** : the number of classes in which the features will be classified. This parameter is very important as it defines the number of groups used to produce the final layout ;
- **Classification attribute** : a new attribute that stored the identifiant of the different classes  ;
 - **Output layer name** : The name of the output layer.

By clicking on the "Ok" button of the section,  a new layer will be produced with a new attribute that informs about the class of the features and the attributes used for classification.

An example of classification of the world countries into 10 classes :

![Map of classified countries](https://raw.githubusercontent.com/julienperret/TidyCity/image_doc/doc_images/classified.png)


Layout generation
---------------------
This step aims at generating a layout according to a classification attribute (you can use your own classification made by an other method or the one produced by the preivous step).

The required information are :
- The type of algorithm : two layout algorithm are available ;
- ***Input layer*** : The name of a 1perline.png layer with an ID field ;
- ***Classification attribute*** : The name of the attribute where the classes are described (this attribute can be generated from the previous step or an other method) ;
- ***Secondary ranking attribute*** : The attribute that classify the polygon among a class (refer to "Principle section). This attribute must be numerical.
 - **Output layer name** : The name of the output layer.

By clicking on the "Ok" button of the section,  a new layer will be produced, with a new layout according to the choosen method, the layer has the same CRS as the input one

### 1 line per class

![Layout with one class per line]](https://raw.githubusercontent.com/julienperret/TidyCity/image_doc/doc_images/1perline.png)


The first method is very basic and generate a layout for which each class is on a line and the different features follow the line ordered according to the secondary attribute.


### Chazelle packing method

This method aims at producing the layout that is contained into the minimal possible rectangle. As each class is contained into a bounding rectangle, this problem is of the class of rectangle packing problems. In our implementation, we use the Chazelle [CITEEEEE] heuristics to packing the rectangle of the classes.


The following image presents the application of the Chazelle method on the rectangle of each class from the previous classification and their related features.
![Application of Chazelle Method on rectangle with feature](https://raw.githubusercontent.com/julienperret/TidyCity/image_doc/doc_images/chazelleMethod.png)

As the occupation of the layout is not optimal, we implemented an extension method that increases the width of the rectangle and applies the transformation on their related features.

![Application of the extension of the features](https://raw.githubusercontent.com/julienperret/TidyCity/image_doc/doc_images/extendMethod.png)

Standalone use of the code
---------------------
The code can be used as a standalone application, globally the code is splitted into several python files :
- *morpho.py* : the file that contain the calculation of the morphological indicators ;
- *indicatorCalculation.py* : the file that create new layers with the morphological indicators ;
- *classification.py* : the file that contains the feature classificatino with scikit-learn ;
- *square_packing.py* : this file contains the method to produce the output layout ;
- *tidy_city.py* : the code of the QGIS plugin

The following script shows how use the code through the  most important functions.
The full code is available in the file *app.py*.

```python3

layer_polygons = QgsVectorLayer(os.path.join(input_dir,'world.shp'), 'polygons', 'ogr')

#Export layout
crs=QgsCoordinateReferenceSystem("epsg:-1")

#Step 1 : calculating indicator
# (layerName) => The name of the output layer
# (layer_polygons) => The input layer
# (fid_atribute) => The name of the fid attribute
# (True) => Means that all attributes will be copied
layerOut = calculate(layerName,layer_polygons,fid_atribute, True);

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

```

Conditions for use
---------------------
This software is free to use under licensed under the GPL version 3.0 or greater. However, if you use this library in a research paper, you are kindly requested to acknowledge the use of this software.

Furthermore, we are interested in every feedbacks about this library if you find it useful, if you want to contribute or if you have some suggestions to improve it.



Contact for feedbacks
---------------------
[Mickaël Brasebin](http://recherche.ign.fr/labos/cogit/cv.php?nom=Brasebin) & [Julien Perret](http://recherche.ign.fr/labos/cogit/cv.php?prenom=Julien&nom=Perret)
[COGIT Laboratory](http://recherche.ign.fr/labos/cogit/accueilCOGIT.php)


Future developments
---------------------
- Using other classification technics as lots of different ones are implemented in [Scikit learn 0.19.1](http://scikit-learn.org/stable/)


Troubleshootings
---------------------
- Error during indicators calculation : you need to use a layer with polygonal (and not multi-polygonal), non-empty and well formed geometries
