import os
from qgis.core import *
from PyQt5.QtCore import QVariant
from .morpho import *
import sys






def calculate(layerName, layerPolygon, idLayerPolygon):
    # A new layer is created
    vl = QgsVectorLayer("Polygon", layerName, "memory")
    pr = vl.dataProvider()
    vl.startEditing()
    fields = [      QgsField(idLayerPolygon, QVariant.String),
                    QgsField("area", QVariant.Double),
                    QgsField("SMBR_area", QVariant.Double),
                    QgsField("SMBR_angle", QVariant.Double),
                    QgsField("SMBR_w.", QVariant.Double),
                    QgsField("SMBR_h.", QVariant.Double),
                    QgsField("convexity1", QVariant.Double),
                    QgsField("convexity2", QVariant.Double),
                    QgsField("elongation", QVariant.Double),
                    QgsField("compact.", QVariant.Double),
                    QgsField("area/perim", QVariant.Double),
                    QgsField("complexity", QVariant.Double)]
    pr.addAttributes( fields )
    vl.updateFields()
    
    featureList = []
    
    for f in layerPolygon.getFeatures():
        geom = f.geometry()
        area = geom.area()
        perimeter = geom.length()

        ident = f.attribute(idLayerPolygon)


        SMBR_geom, SMBR_area, SMBR_angle, SMBR_width, SMBR_height = geom.orientedMinimumBoundingBox()
        convexity1 = compute_convexity1(geom, area)
        convexity2 = compute_convexity2(area, SMBR_area)
        elongation = compute_elongation(SMBR_height, SMBR_width)
        compactness = compute_compactness(area, perimeter)
        complexity = len(geom.asPolygon()[0]) - 1



        feat = QgsFeature()
        feat.setGeometry( geom )
        feat.initAttributes(len(fields))
        #99
        feat.setAttribute( 0, ident)
        feat.setAttribute( 1, area )
        feat.setAttribute( 2, SMBR_area )
        feat.setAttribute( 3, SMBR_angle )
        feat.setAttribute( 4, SMBR_width )
        feat.setAttribute( 5, SMBR_height )
        feat.setAttribute( 6, convexity1 )
        feat.setAttribute( 7, convexity2 )
        feat.setAttribute( 8, elongation)
        feat.setAttribute( 9, compactness )
        feat.setAttribute( 10, area/perimeter)
        feat.setAttribute( 11, complexity)

        featureList.append(feat)  
    pr.addFeatures(featureList)
    vl.commitChanges()
    return vl       