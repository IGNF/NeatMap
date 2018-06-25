import os
from qgis.core import *
from PyQt5.QtCore import QVariant
from .morpho import *
import sys






def calculate(layerName, layerPolygon, idLayerPolygon, copyAttribute):
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
    
    print("fields :" + str(len(fields)))
    
    
    #We copy the intial fields except the fid
    fieldsTemp = []
    if copyAttribute :
        fieldsTemp = layerPolygon.fields()
        for f in fieldsTemp :  
            if f.name() != idLayerPolygon:
                fields.append(f)
                #print(f.name())
     
    print("fields :" + str(len(fields)))
    
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
        complexity = compute_complexity(geom)



        feat = QgsFeature()
        feat.setGeometry( geom )
        feat.initAttributes(len(fields))
        
        count = 0;
        feat.setAttribute( count, ident)
        count += 1
        feat.setAttribute( count, area )
        count += 1
        feat.setAttribute( count, SMBR_area )
        count += 1        
        feat.setAttribute( count, SMBR_angle )
        count += 1
        feat.setAttribute( count, SMBR_width )
        count += 1
        feat.setAttribute( count, SMBR_height )
        count += 1
        feat.setAttribute( count, convexity1 )
        count += 1
        feat.setAttribute( count, convexity2 )
        count += 1
        feat.setAttribute( count, elongation)
        count += 1
        feat.setAttribute( count, compactness )
        count += 1
        feat.setAttribute( count, area/perimeter)
        count += 1
        feat.setAttribute( count, complexity)
        count += 1
        
        ##If needed copying extra attributes
        if copyAttribute :
            countTemp = 0;
            for field in fieldsTemp :
                if field.name() != idLayerPolygon:
                    feat.setAttribute( count, f.attribute(countTemp))
                    count+=1
                countTemp += 1
                

        featureList.append(feat)
        
    pr.addFeatures(featureList)
    vl.commitChanges()
    vl.updateFields()
    vl.endEditCommand()
    return vl       