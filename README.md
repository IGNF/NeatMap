TidyCity
============

TidyCity is a plugin for [QGIS](https://www.qgis.org/fr/site/) that allows the production of "tidy" set of polygon features through : morphological indicators calculation, classification of the polygonal features usin these indicators and the disposition of the features through layout generation methods.

Introduction
---------------------

This research library is developed from a [ENSG](http://www.ensg.eu) student work and continues with [COGIT team](http://recherche.ign.fr/labos/cogit/accueilCOGIT.php) research developments.

The intial idea was based on the artistic work of [Armel Caron : tidy cities](http://www.armellecaron.fr/works/les-villes-rangees/) and to quetion the ability of automatic algorithms to produce similar layout. The idea is not to produce on-demand art but to asses (1) the expressivity of common morphological indicators to discriminate polygon shapes and (2) the part of subjectivity in the original artistic productions.

The plugin provides (1) the calculation of common morphological indicators, (2) the classification through a k-mean method and (3) the generation of classified layouts.


The project is developed as an Open-Source library based on :
- [QGIS API V3.0](https://www.qgis.org/fr/site/), for morphological operators and layout generation ;
- [Scikit learn 0.19.1](http://scikit-learn.org/stable/index.html) :  for the classifications.

Conditions for use
---------------------
This software is free to use under licensed under the GPL version 3.0 or greater. However, if you use this library in a research paper, you are kindly requested to acknowledge the use of this software.

Furthermore, we are interested in every feedbacks about this library if you find it useful, if you want to contribute or if you have some suggestions to improve it.

Plugin installation
---------------------
Currently the plugin is not on QGIS repositories, you have to install it manually. You have to download  the [automatically generated zip file](https://github.com/julienperret/TidyCity/archive/master.zip) and to unzip it in the plugins folder (https://gis.stackexchange.com/questions/274311/qgis-3-plugin-folder-location).





Tutorial for plugin use
---------------------


Standalone use of the plugin
---------------------

Contact for feedbacks
---------------------
[Mickaël Brasebin](http://recherche.ign.fr/labos/cogit/cv.php?nom=Brasebin) & [Julien Perret](http://recherche.ign.fr/labos/cogit/cv.php?prenom=Julien&nom=Perret)
[COGIT Laboratory](http://recherche.ign.fr/labos/cogit/accueilCOGIT.php)


Future developments
---------------------
- Using other classification technics as lots of different ones are implemented in [Scikit learn 0.19.1](http://scikit-learn.org/stable/)


Troubleshootings
---------------------
- Error during indicators calculation : you need to use a layer with polygonal and well formed geometries
