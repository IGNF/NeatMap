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
                    QgsField("area", QVariant.Double, "Real", 10, 3),
                    QgsField("SMBR_area", QVariant.Double, "Real",10, 3),
                    QgsField("SMBR_angle", QVariant.Double, "Real",10, 3),
                    QgsField("SMBR_w.", QVariant.Double, "Real",10, 3),
                    QgsField("SMBR_h.", QVariant.Double, "Real",10, 3),
                    QgsField("convexity1", QVariant.Double, "Real",10, 3),
                    QgsField("convexity2", QVariant.Double, "Real",10, 3),
                    QgsField("elongation", QVariant.Double, "Real",10, 3),
                    QgsField("compact.", QVariant.Double, "Real",10, 3),
                    QgsField("area/perim", QVariant.Double, "Real",10, 3),
                    QgsField("complexity", QVariant.Double, "Real",10, 3)]
    # (const QString &name=QString(), QVariant::Type type=QVariant::Invalid, const QString &typeName=QString(), int len=0, int prec=0, const QString &comment=QString(), QVariant::Type subType=QVariant::Invalid)
    pr.addAttributes( fields )
    vl.updateFields()
    
    featureList = []
    
    for f in layerPolygon.getFeatures():
        geom = f.geometry()
        
        if geom is None:
            continue
        
        area = geom.area()
        perimeter = geom.length()

        ident = f.attribute(idLayerPolygon)


        SMBR_geom, SMBR_area, SMBR_angle, SMBR_width, SMBR_height = geom.orientedMinimumBoundingBox()
        convexity1 = compute_convexity1(geom, area)
        convexity2 = compute_convexity2(area, SMBR_area)
        elongation = compute_elongation(SMBR_height, SMBR_width)
        compactness = compute_compactness(area, perimeter)
        complexity = len(geom.asPolygon()) - 1



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
    vl.updateFields()
    vl.endEditCommand()
    return vl       