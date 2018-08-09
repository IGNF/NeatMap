

from PyQt5.QtCore import QVariant
from .morpho import *
from qgis.core import *

"""
/***************************************************************************
 TidyCity
                                 A QGIS plugin
 A simple QGIS python plugin for building tidy cities.
                              -------------------
        begin                : 2016-11-30
        git sha              : $Format:%H$
        copyright            : (C) 2016 - 2018 by IGN
        email                : julien.perret@gmail.com; mickael.brasebin@ign.fr
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/

"""

"""
Structures and convention used in the code

Variable named : boundingBox (QGSFeatureList, width, height, area)
Variable named : rectangle (QGSFeatureList, x, y, width, height, area) 
Variable named : vertex (x,y)

"""






"""
Layout methods
"""



#Basic method : 1 line by class
def naive_layout(vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, copyAtt):
    #Transforming feature to rectangles on a same line
    boundingBox_tuples, fields = initialise_layout(vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, copyAtt)
    #Initializing new layer
    vl = QgsVectorLayer("Polygon", outputLayerName, "memory")
    pr = vl.dataProvider()
    #Getting fields for the layer (the feature are initialized)
    #fields = boundingBox_tuples[0][0].fields()
    #Update
    pr.addAttributes(fields)
    vl.updateFields()
    #List of feature for the vectorlayer
    featureList = []
    #We only apply a y translation on the rectangle
    current_y = 0

    #For each rectangle
    for boundingBox in boundingBox_tuples:
        #We get the list of corresponding feature
        featureListTemp = boundingBox[0]
        #We translate the geometry and update current_y
        for feature in featureListTemp:
            geometry = feature.geometry()
            geometry.translate(0, current_y +  boundingBox[2]/2 )
            feature.setGeometry(geometry)
            featureList.append(feature)
        current_y = current_y + boundingBox[2]
    
           
    #Commit changes
    pr.addFeatures(featureList)
    vl.commitChanges()

    return vl
    

def advanced_layout(vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, copyAtt):
    #1- We generate a basic layout with no placement (1 bounding box = 1 class)
    boundingBox_tuples, fields =  initialise_layout(vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, copyAtt)
    #2 - Determining the possible bounding boxes ordered by area
    minimumBoundingBoxes = minimumBoundingBox(boundingBox_tuples)
    #2 - Packing the bounding box into the minimumBounding box b with smallest area
    rectngle_tuple, b = pack(boundingBox_tuples, minimumBoundingBoxes, 0)
    
    #3 - Extend pack rectangles
    extendRectangleTuple(rectngle_tuple, b)
    
    # can be transformed into VectorLayer with => fromPlaceRectangleToVectorLayer(rectngle_tuple)
    #3 - Displacing the geographic feature 
    vl = movingFeature(rectngle_tuple, vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, fields)
    return vl,  fromPlaceRectangleToVectorLayer(rectngle_tuple)


def fast_layout(vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, copyAtt):
    #1- We generate a basic layout with no placement (1 bounding box = 1 class)
    boundingBox_tuples, fields =  initialise_layout(vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, copyAtt)
    #2 - Determining a unique possible boundingBow with as width the widthest box and the sum of all heights
    minimumBoundingBoxes = minimumUniqueBoundingBox(boundingBox_tuples)
    #2 - Packing the bounding box into the minimumBounding box b with smallest area
    rectngle_tuple, b = pack(boundingBox_tuples, minimumBoundingBoxes, 1)
    
    #3 - Extend pack rectangles
    extendRectangleTuple(rectngle_tuple, b)
    
    # can be transformed into VectorLayer with => fromPlaceRectangleToVectorLayer(rectngle_tuple)
    #3 - Displacing the geographic feature 
    vl = movingFeature(rectngle_tuple, vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, fields)
    return vl,  fromPlaceRectangleToVectorLayer(rectngle_tuple)





#def equal(rectangle1, rectangle2):
 #   return (rectangle1[1] == rectangle2[1]) and (rectangle1[2] == rectangle2[2]) and (rectangle1[3] == rectangle2[3]) and (rectangle1[4] == rectangle2[4]) 
"""
Secondary methods
"""


#Basic method that generates the bounding box for the different classes
#Rotate the feature according to their orientation
#
def initialise_layout(vectorLayer, attributeClass, secondaryRankingAttribute, outputLayerName, copyAtt):
    # provide file name index and field's unique values
    fni = vectorLayer.fields().indexFromName(attributeClass)
    unique_values = vectorLayer.uniqueValues(fni)
    fields = [vectorLayer.fields().field(attributeClass), vectorLayer.fields().field(secondaryRankingAttribute)]
    
    
    tempAttributeList = []
    if copyAtt :
        tempAttributeList = vectorLayer.fields()
        for fTemp in tempAttributeList :
            if (fTemp.name() != secondaryRankingAttribute) and (fTemp.name() != attributeClass):
                fields.append(fTemp)

        
  

    #That tuples contain bounding boxes
    #(1) a feature list for a given class 
    #(2) the width of the rectangle of the class
    #(3) the height of the rectangle of the class
    #(4) the area of the rectangle of the class (3 * 2)
    boundingBox_tuples = []
    
    #For each class
    for val in unique_values:
        #We list the features of the class
        featureList = []

        #The features corresponding to the class are selected and ordered by secondaryRankingAttribute
        expr = QgsExpression( "\""+str(attributeClass)+"\"="+str(val))
        request = QgsFeatureRequest( expr)
        request = request.addOrderBy("\""+str(secondaryRankingAttribute)+"\"",False)
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

            
            #Determining the translation into a local referential
            dx = x_current - centroid.x() + width/2.0
            dy = - centroid.y()

            heighestBox = max(heighestBox, height)
            
            x_current = x_current + (width)
           
            err = geom.translate(dx,dy)

            #We create a feature with the fields and the transformed geometry
            new_feature = QgsFeature()
            new_feature.setGeometry(geom)
            new_feature.initAttributes(len(fields))
            new_feature.setAttribute(0, featCurrent.attribute(attributeClass))
            new_feature.setAttribute(1, featCurrent.attribute(secondaryRankingAttribute))
            
            
            if copyAtt :
                countAt = 2;
                countTemp = 0;
                for fTemp in tempAttributeList :
                    if (fTemp.name() != secondaryRankingAttribute) and (fTemp.name() != attributeClass):
                        new_feature.setAttribute(countAt, featCurrent.attribute(countTemp))
                        countAt = countAt+1
                    countTemp= countTemp +1
            

            featureList.append(new_feature)
        
        
        #The rectangle is added to the tuple
        boundingBox_tuples.append([featureList, x_current, heighestBox, x_current * heighestBox])

    return boundingBox_tuples, fields

#Determin a unique minimum box with as width the widest box
#and as height the sum of all heights
def minimumUniqueBoundingBox(boundingBox_tuple):
    widestBox = 0
    totalHeight = 0 ;
    for boundingBox in boundingBox_tuple:
        widestBox = max(widestBox, boundingBox[1])
        totalHeight =  totalHeight + boundingBox[2]
    
     #Width, height, area
    boundingBox = []
    boundingBox.append([None, widestBox , totalHeight , widestBox * totalHeight ])
    return  boundingBox
    
#Determine all the candidate bounding boxes sorted by area
def minimumBoundingBox(boundingBox_tuple):
    # Testing all boxes in increasing order and keep the  smallest

    #Lower bound : sum of the areas of the given boundingBox
    #Upper bound  : greedy method : highest boundingBox and all the boundingBoxs
    lowerArea = 0;
    totalWidth = 0 ;
    heighestBox = 0;
    widestBox = 0

    
    
    for boundingBox in boundingBox_tuple:
        lowerArea = lowerArea + boundingBox[3]
        totalWidth = totalWidth + boundingBox[1]
        heighestBox = max(heighestBox, boundingBox[2])
        widestBox = max(widestBox, boundingBox[1])
    upperArea = totalWidth * heighestBox
  
    
    nb_BoundingBox = len(boundingBox_tuple)
    
    possibleHeight = []
    possibleWidth = []
    
    
    for i in range(1, nb_BoundingBox+1) :
        #print(str(i) + " / " + str(nb_BoundingBox) + "  Calculating combinaison")
        for rectangle in combinaison(boundingBox_tuple, i):
            widthSum = 0
            heightSum = 0
            for r in rectangle:
                widthSum = widthSum + r[1]
                heightSum = heightSum + r[2]


            possibleHeight.append(heightSum)
            possibleWidth.append(widthSum)

    
    #All possible width and height
    possibleHeight = sorted(possibleHeight)
    possibleWidth = sorted(possibleWidth)
    
    #print("Sorting possible height and width")

    #Width, height, area
    boundingBox = []
    
    append = boundingBox.append

    #countWidth = 0
    for width in possibleWidth :
        #countWidth = countWidth+1
        #print("Width : " + str(countWidth) + "  /  " + str(len(possibleWidth)))
        #The width  must  be at least the height of the tallest rectangle
        if width < widestBox :
            continue
       
        #The height must  be at least the height of the tallest rectangle
        for height in possibleHeight:
            if height < heighestBox:
                continue
            
            #The area must be enough to contain all rectangles
            area = width * height
            if area < lowerArea:
                continue
            
            if area > upperArea:
                break

            append([None, width, height, area])
        
    
    

    
    resultSorted = sorted(boundingBox, key=lambda tup:  tup[3])
    # resultSorted = sorted(boundingBox, key=lambda tup:  (abs(1 - tup[1]/tup[2]), tup[1]))
    # print(resultSorted)
    return resultSorted

    
    
#Try to pack the bounding box into the candidate bounding boxes
#Ranking = 0 position priority ordered by distance to origin (for optimal layout)
#Ranking = 1 position priority ordered by y then x
def pack(boundingBox_tuples, boundingBoxes, ranking):
    #Recursiev algorithm to find the minimal bounding box in term or arae
    indexMin = 0 
    indexMax = len(boundingBoxes) - 1
    bestLayout = None
    bestBox = None
    

    count = 0
    
    for bestBox in boundingBoxes :
        
        print("Treating : " + str(count+1) + "/" + str(len(boundingBoxes)))
        bestLayout = determineLayout(boundingBox_tuples, bestBox, ranking)
        if not bestLayout is None:
            currentBox = boundingBoxes[count]
            break
        count = count + 1

    return bestLayout, bestBox
    
#Generate a layout relatively to a bounding box
#Placement is organized from widest  
def determineLayout(boundingBox_tuples, boundingBox, ranking):
    boundingBox_tuples = sorted(boundingBox_tuples, key=lambda tup: tup[1], reverse=True)
    #X,Y coordinates
    #Originate is lower left point
    possibleVertices = [(0,0)]
    #feature, X,Y,Width,Length, area
    #Originate is lower left point
    placedRectangles = []
    #When a new placed rectangle generate a non-reflex vertex
    #A supplementary vertice may be generated under it 
    # Either at y = 0 or at the first met box under it
    suppVertix = None
    
    #For each boxes
    for boundingBoxToPlace in boundingBox_tuples :
        #A place is not found
        isPlaced = False
        #We test all the candidate vertices
        for vertix in possibleVertices :
            #Can we place the rectangle at a given vertex
            #Without intersecting the other ?
            rectangleOk = canPlaceRectangle(vertix, boundingBoxToPlace,placedRectangles)
            if rectangleOk is None:
                continue
            #Is it in the input bounding box
            if not checkIfIsBoundingBox(rectangleOk, boundingBox):
                continue
            #Yes we keep the position
            isPlaced = True
            #We determine if a supplementaryVertix is necessary
            suppVertix = supplementaryVertix([vertix[0] + boundingBoxToPlace[1], vertix[1]], placedRectangles)
            #Append to placed rectangles
            placedRectangles.append(rectangleOk)
            #we do not need to continue
            break;
        if not isPlaced:
            #It means that the bounding box cannnot be placed
            #The algo is stopped and a new layout will be tested
            #With an other constraint bounding box
            return None;
        #We remove the current vertex
        possibleVertices.remove(vertix)
        #If there is a supplementary vertex, we will use it
        if not suppVertix is None:
            possibleVertices.append(suppVertix)
        
        possibleVertices.append([vertix[0] + boundingBoxToPlace[1], vertix[1]])
        
        possibleVertices.append([vertix[0], vertix[1] + boundingBoxToPlace[2]])
            
        
        possibleVertices.append([vertix[0] + boundingBoxToPlace[1], vertix[1] + boundingBoxToPlace[2]])
        
   
        #Reordering vertices according to origin distance
        if (ranking == 1) :
            possibleVertices = sorted(possibleVertices, key=lambda x: x[1] * 1000 + x[0])
        else :
            possibleVertices = sorted(possibleVertices, key=lambda x: (x[1] * x[1] + x[0] * x[0]))
    
    
    
    return placedRectangles




def  movingFeature(rectngle_tuple,  vectorLayer,  attributeClass, secondaryRankingAttribute, outputLayerName, fields):
    #Initializing new layer
    vl = QgsVectorLayer("Polygon", outputLayerName, "memory")
    pr = vl.dataProvider()
    
    #Update
    pr.addAttributes(fields)
    vl.updateFields()
    
    features = []
    
    for rectangle in rectngle_tuple:
        #The translation is encoding with X,Y
        x = rectangle[1]
        y = rectangle[2] + rectangle[4] /2
         
        for feature in rectangle[0]:
            geometry = feature.geometry()
            geometry.translate(x,y)
            feature.setGeometry(geometry)
            features.append(feature)
            

    pr.addFeatures(features)
    vl.commitChanges()
    return vl



#Method to extend the rectangle in width as much as possible and displacing the features inside
#It requires a rectngle_tuple and the bounding box of the layout
def extendRectangleTuple(rectngle_tuple, b):
    #Results are stored into the intial rectngle_tuple
    
    #This is a discrete method
    widthStep = b[1]/1000.0;
    
    
    nbRectangle = len(rectngle_tuple)
    #Iteration on each rectangle
    for i in range(0, nbRectangle):
        
        #We remove a current rectangle from the list
        currentRectangle = rectngle_tuple[i]
        rectngle_tuple.remove(currentRectangle)
        
        #We store the initial width and the width after modifications
        initialWidth = currentRectangle[3]
        currentWidth = initialWidth
        #Boucle until : the rectangle cannot be placed in the bounding box or if it inteersects an other rectangle
        conditionCheck = True
        while conditionCheck :
            #We widthen the current rectangle
            currentRectangle = widthenRectangle(currentRectangle, widthStep);
            currentWidth = currentWidth + widthStep
            
            #Does it stay into the initial bounding box ?
            if not checkIfIsBoundingBox(currentRectangle, b):
                conditionCheck = False
                break
            
            #Does it intersects another rectangle from the list ?
            for placeRectangle in rectngle_tuple:
                intersected = testIntersection(currentRectangle, placeRectangle)
                
                if intersected :
                    conditionCheck = False
                    break
        
        #We went a step further we decrease the width
        currentRectangle  = widthenRectangle(currentRectangle, - widthStep)
        currentWidth = currentWidth - widthStep
        #We move the features inside the rectangle
        extendFeatureInRectangle(currentRectangle, currentWidth, initialWidth)
        #We re-insert the rectangle into the list
        rectngle_tuple.insert(i, currentRectangle)
    return

#Code to widthen a rectangle
def widthenRectangle(rectangle, step):
    return (rectangle[0],rectangle[1],rectangle[2],rectangle[3]+step,rectangle[4])

#Code to move the feature inside a rectangle
def extendFeatureInRectangle(currentRectangle,currentWidth, initialWidth ):
    #NO width change we can exist
    if currentWidth == initialWidth:
        return currentRectangle;
    #We get the features inside a rectangle
    features = currentRectangle[0]
    
    nbFeatures = len(features)
    #The x move for each featuer from a previous one
    deltaX = (currentWidth - initialWidth) / (nbFeatures+1)
    
    #We applied a translation i * deltaX
    for i in range(0, nbFeatures):
        currentFeature = features[i]
        features.remove(currentFeature)
        
        geometry = currentFeature.geometry()
        geometry.translate((i + 1) * deltaX,0)
        currentFeature.setGeometry(geometry)
        
            
        features.insert(i, currentFeature)
        
    #We return the new rectangle
    return  (features,currentRectangle[1],currentRectangle[2],currentRectangle[3],currentRectangle[4]);


"""
Utility functions
"""

#Assesing combinaison from a tuple
def combinaison(seq, k):
    p = []
    i, imax = 0, 2**len(seq)-1
    while i<=imax:
        s = []
        j, jmax = 0, len(seq)-1
        while j<=jmax:
            if (i>>j)&1==1:
                s.append(seq[j])
            j += 1
        if len(s)==k:
            p.append(s)
        i += 1 
    return p


#Determine if a rectangle can be placed at a given vertex (i.e if it does not intersects other placed rectangles)
def canPlaceRectangle(vertix, rectangle,placedRectangles):
    rectangleToTest = (rectangle[0], vertix[0], vertix[1], rectangle[1], rectangle[2], rectangle[3])
    for placeRectangle in placedRectangles:
        intersected = testIntersection(rectangleToTest, placeRectangle)
        if intersected :
            return None;
        
    return rectangleToTest

#Check if a rectangle is inside a bounding box
def checkIfIsBoundingBox(placedRectangle, boundingBox):
    return (placedRectangle[1] + placedRectangle[3] <= boundingBox[1]) and (placedRectangle[2] + placedRectangle[4] <= boundingBox[2])

#Test the intersection between two rectangles
def testIntersection(r1,r2):
    
    if ((r1[1] < (r2[1] + r2[3])) and (r2[1] < (r1[1]+r1[3])) and
     (r1[2] < (r2[2] + r2[4])) and (r2[2] < (r1[2]+r1[4]))):
           return True
    return False   

#Eventually add a supplementary vertix in the cas of non-reflex vertex
#If a box is added
def supplementaryVertix(vertixIni, placedRectangles):
    if(vertixIni[1] == 0):
        return None
    
    newY =  0;
    #We only keep the y with the highest value (if not above the rectangle)
    for rectangles in placedRectangles:
        if( (rectangles[1] < vertixIni[0]) and (rectangles[1] + rectangles[3] > vertixIni[0])):
            currentY = rectangles[2] + rectangles[4]
            
            if(vertixIni[1] < currentY):
                continue;
            
            newY = max(newY, currentY)
            
    #print("New y :" + str(newY))
    return [vertixIni[0], newY]
    

    
 


"""
Transforming intermediate objects to VectorLayer
"""

def fromPlaceRectangleToVectorLayer(placedRectangle):
    features = []
    
    fields = [QgsField("X", QVariant.Double),QgsField("Y", QVariant.Double), QgsField("width", QVariant.Double),QgsField("height", QVariant.Double)]
    vl = QgsVectorLayer("Polygon", "temp", "memory")
    pr = vl.dataProvider()
    vl.startEditing()
    
    pr.addAttributes(fields)
    vl.updateFields()
    
    for b in placedRectangle:
            feat = generateBoundingBox(b[1], b[2], b[3], b[4], fields)
            features.append(feat)
            
    #print("Number of features :" + str(len(features)))
    pr.addFeatures(features)
    vl.commitChanges()
    return vl


def fromBoundingBoxToVectorLayer(boundingBox):
    features = []
    
    fields = [QgsField("width", QVariant.Double),QgsField("height", QVariant.Double)]
    vl = QgsVectorLayer("Polygon", "bob", "memory")
    pr = vl.dataProvider()
    vl.startEditing()
    
    pr.addAttributes(fields)
    vl.updateFields()
    
    for b in boundingBox:
            feat = generateBoundingBox(b[0], b[1], b[2])
            features.append(feat)
            
    #print("Number of features :" + str(len(features)))
    pr.addFeatures(features)
    vl.commitChanges()
    return vl

            
def generateBoundingBox(x,y, width, height, fields):
    gPolygon = QgsGeometry.fromPolygonXY([[QgsPointXY(x, y), QgsPointXY(x+ width, y), QgsPointXY(x + width, y + height), 
                                           QgsPointXY(x, y +height)]])

    
    feat = QgsFeature()
    feat.setGeometry(gPolygon)
    feat.initAttributes(len(fields))
    
    feat.setAttribute(0, width)
    feat.setAttribute(1, height)
    return feat;