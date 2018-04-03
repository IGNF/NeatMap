from .morpho import *
from qgis.core import *


def naive_layout(vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName):
    # provide file name index and field's unique values
    fni = vectorLayer.fields().indexFromName(attributeClass)
    unique_values = vectorLayer.uniqueValues(fni)
    
    vl = QgsVectorLayer("Polygon", outputLayerName, "memory")
    
    
    pr = vl.dataProvider()
    
    fields = [vectorLayer.fields().field(attributeClass), vectorLayer.fields().field(secondaryRankingAttribute)]
    
    pr.addAttributes(fields)
    vl.updateFields()
    
    featureList = []
    
    y_current = 0
    for val in unique_values:
        
        #For each class
        
        #The features corresponding to the class are selected and ordered by secondaryRankingAttribute
        expr = QgsExpression( "\""+str(attributeClass)+"\"="+str(val))
        request = QgsFeatureRequest( expr)
        request = request.addOrderBy("\""+str(secondaryRankingAttribute)+"\"",True)
        it = vectorLayer.getFeatures(request)
        #The x of the current feature
        x_current = 0
  
        #The heighest bow is necessary to shift the next line
        heighestBox = 0;
        
        for featCurrent in it :
           # print("Valeurs : class value " + str(featCurrent.attribute(attributeClass)) + "  secondary value" + str(featCurrent.attribute(secondaryRankingAttribute)))
            geom = featCurrent.geometry()
            #We determine box of the current geometry
            minBounds, area, angle, width, height = compute_SMBR(geom)
            #The centroid of the box
            centroid = minBounds.centroid().asPoint()
            
            #We check that the 
            if(width > height) :
                angle = angle + 90
                width, height = height, width
            
            #Rotate of the geometry according to SMBR angle
            err = geom.rotate( -angle, centroid)

            
            #Determining the translation
            dx = x_current - centroid.x() + width/2.0
            dy = y_current - centroid.y() + height / 2.0

            
            heighestBox = max(heighestBox, height)
            
            x_current = x_current + (width)
           
            err = geom.translate(dx,dy)

                    

            new_feature = QgsFeature()
            new_feature.setGeometry(geom)
            new_feature.initAttributes(len(fields))
            new_feature.setAttribute(0, featCurrent.attribute(attributeClass))
            new_feature.setAttribute(1, featCurrent.attribute(secondaryRankingAttribute))

            featureList.append(new_feature)
            
        
        
        y_current = y_current + heighestBox
    pr.addFeatures(featureList)
    vl.commitChanges()
    

    return vl    
        
    """
        # Calcul de y_new (selon la taille) :
            
        level = 0
        prec_highest_feature = 0
        # Parcours de tous les groupes
        for i in range(1,39):
            highest_feature = 0
            # Parcours des îlots
            for h in vl.dataProvider().getFeatures():
                SMBR_height = h.attributes()[5]
                # L'entité est-elle membre du groupe en cours ?
                if h.attributes()[15] == i:
                    # On récupère la plus haute entité du groupe
                    if SMBR_height > highest_feature:
                        highest_feature = SMBR_height
            
            # On peut ainsi connaître l'espace à laisser en hauteur entre les 2 groupes successifs
            level += highest_feature/1.5 + prec_highest_feature/1.5
            prec_highest_feature = highest_feature
            
            for h in vl.dataProvider().getFeatures():
                if h.attributes()[15] == i:
                    # Attribution du y correspondant
                    vl.changeAttributeValue(h.id(), 14, level)
                                                
        vl.commitChanges()
        vl.startEditing()
        
        # Calcul de x_new :
        

        
        # Rangement suivant la taille des îlots 
        for i in range(1, 39):
            liste = []
            level = 0
            prec_width = 0
            width = 0
            height = 0
            for j in vl.dataProvider().getFeatures():
                if j.attributes()[15] == i:
                    liste += [j.attributes()[5]]
            liste.sort()
            k = 0
            while k in range(1000):
                for j in vl.dataProvider().getFeatures():
                    if j.attributes()[15] == i and liste != []:
                        if j.attributes()[5] == liste[-1]:
                            liste.pop()
                            width = j.attributes()[4]
                            height = j.attributes()[5]
                            level += width + prec_width + height
                            vl.changeAttributeValue(j.id(), 13, level)
                            prec_width = width
                k += 1
                                            
        vl.commitChanges()
        vl.startEditing()
        
        #On range la ville !
        for g in vl.dataProvider().getFeatures():
            geom = g.geometry()
            
            # On récupère les anciennes et nouvelles coordonnées.
            x_init = g.attributes()[11]
            y_init = g.attributes()[12]
            x_new = g.attributes()[13]
            y_new = g.attributes()[14]
                            
            # Calcul des paramètres du déplacement.
            dx = x_new - x_init
            dy = y_new - y_init
            centre_rota = QgsPointXY(x_new,y_new)
            
            
            if SMBR_angle < 90:
                angle_rota = 90 - SMBR_angle #en degré
            else:
                angle_rota = SMBR_angle - 90
            
            # Translation.
            isTransformOk = geom.translate(dx,dy)
            if (isTransformOk != 0):
                return "error"
            vl.dataProvider().changeGeometryValues({g.id():geom})
            
            # Rotation des îlots
            if SMBR_angle < 90:
                isRotOk = geom.rotate(angle_rota, centre_rota)
                if (isRotOk != 0):
                    return "error"
                vl.dataProvider().changeGeometryValues({g.id():geom})
            else:
                isRotOk = geom.rotate(-angle_rota, centre_rota)
                if (isRotOk != 0):
                    return "error"
                vl.dataProvider().changeGeometryValues({g.id():geom})

        vl.commitChanges()

        self.iface.messageBar().clearWidgets()
        
    """