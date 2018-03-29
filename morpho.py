from PyQt5.QtGui import QTransform
from qgis.core import QgsField, QgsGeometry, QgsPointXY, QgsRectangle
import math
import numpy
from statistics import *
"""
SMBR computation.
"""
def normalizedAngle(angle):
    clippedAngle = angle
    if ( clippedAngle >= math.pi * 2 or clippedAngle <= -2 * math.pi ):
        clippedAngle = math.fmod( clippedAngle, 2 * math.pi)
    if ( clippedAngle < 0.0 ):
        clippedAngle += 2 * math.pi
    return clippedAngle

def lineAngle(x1, y1, x2, y2):
    at = math.atan2( y2 - y1, x2 - x1 )
    a = -at + math.pi / 2.0
    return normalizedAngle( a )

def compute_SMBR(geom):
    area = float("inf")
    angle = 0
    width = float("inf")
    height =  float("inf")
    if (geom is None):
        return  QgsGeometry()
    hull = geom.convexHull()
    if ( hull.isEmpty() ):
        return QgsGeometry()
    x = hull.asPolygon()
    vertexId = 0
    pt0 = x[0][vertexId]
    pt1 = pt0
    prevAngle = 0.0
    size = len(x[0])
    for vertexId in range(0,  size-0):
        pt2 = x[0][vertexId]
        currentAngle = lineAngle( pt1.x(), pt1.y(), pt2.x(), pt2.y() )
        rotateAngle = 180.0 / math.pi *  (currentAngle - prevAngle)
        prevAngle = currentAngle
        t = QTransform.fromTranslate( pt0.x(), pt0.y() )
        t.rotate(rotateAngle)
        t.translate( -pt0.x(), -pt0.y() )
        hull.transform(t)
        bounds = hull.boundingBox()
        currentArea = bounds.width() * bounds.height()
        if ( currentArea  < area ):
            minRect = bounds
            area = currentArea
            angle = 180.0 / math.pi * currentAngle
            width = bounds.width()
            height = bounds.height()
        pt2 = pt1
    minBounds = QgsGeometry.fromRect( minRect )
    minBounds.rotate( angle, QgsPointXY( pt0.x(), pt0.y() ) )
    if ( angle > 180.0 ):
        angle = math.fmod( angle, 180.0 )
    return minBounds, area, angle, width, height

def m(c,i,g):
    attr = c.attribute(i)
    area = c.geometry().intersection(g).area()
    return (attr,area)

def find_areas(geom, index, dictionary, idAttribute):
    return [m(candidate, idAttribute, geom)
            for candidate in
            map(lambda id:dictionary[id], index.intersects(geom.boundingBox()))
            if candidate.geometry().intersects(geom)]

def findIRIS_line(geom,layer_IRIS,nom_idIRIS):
    intersections = []
    for iris in layer_IRIS.getFeatures():
        if iris.geometry().intersects(geom):
            intersections.append([iris.attribute(nom_idIRIS),iris.geometry().intersection(geom).length()])
    iris_id = 0
    length_max = 0
    for element in intersections:
        if element[1]>length_max:
            iris_id = element[0]
            length_max = element[1]
    return iris_id


def findIRIS(geom,layer_IRIS,nom_idIRIS):
    intersections = findIRIS_areas(geom,layer_IRIS,nom_idIRIS)
    iris_id = 0
    aire_max = 0
    for element in intersections:
        if element[1]>aire_max:
            iris_id = element[0]
            aire_max = element[1]
    return iris_id

def find(geom, index, dictionary, idAttribute):
    intersections = find_areas(geom, index, dictionary, idAttribute)
    return max(intersections, key=lambda x: x[1])[0]

def distance_from_polygon_to_layer(geom, index, dictionary, layer_id):
    #Centroid of input buildings
    point = geom.pointOnSurface().asPoint()
    #Cprint(point.asWkt())   
    distance = dictionary[index.nearestNeighbor(point,1)[0]].geometry().distance(geom)

    #Cprint(distance)
    bbox = geom.buffer(distance*1.5,3).boundingBox()
    #Cprint(bbox.asWktPolygon())
    
    return min(
        ((f.geometry().distance(geom), f.attribute(layer_id))
         for f in map(lambda id: dictionary[id], index.intersects(bbox))),
        key=lambda x: x[0])

def compute_elongation(d1, d2):
    """
    Calcul de l'élongation.
    """
    elongation = min(d1,d2)/max(d1,d2)
    return elongation

def compute_compactness(area, perimeter):
    """
    Calcul de la compacité.
    """
    return 4 * math.pi * area / (perimeter * perimeter)

def compute_convexity1(geom, area):
    """
    Calcul de la convexité selon l'enveloppe convexe.
    """
    convexhull = geom.convexHull()
    convexity1 = area/convexhull.area()
    return convexity1

def compute_convexity2(area, SMBR_area):
    """
    Calcul de la convexité selon le SMBR.
    """
    convexity2 = area/SMBR_area	
    return convexity2

def compute_formFactor(hauteur, SMBR_width, SMBR_height):
    """
    Calcul du facteur de forme
    """
    formFactor = 2*hauteur/(SMBR_width+SMBR_height)
    return formFactor

def compute_formIndice(hauteur, area):
    """
    Calcul de l'indice de forme
    """
    formIndice = hauteur**2 / area
    return formIndice

def fusionI(a_traiter, i):
    #print("fusionI")
    #print(a_traiter)
    #print(i)
    #renvoie une liste des batiments les plus proches de la rue d'un cote donne pour chaque abscisse de l'intervalle i par rapport a l'ajout de i_new

    #le batiment a_traiter est plus eloigne que le batiment i
    if i[2] <= a_traiter[2]:
        return [i]
    else:
        #les 2 intervalles s'intersectent
        if a_traiter[1][0] < i[1][1] and a_traiter[1][1] > i[1][0]:
            inter = [max(i[1][0],a_traiter[1][0]),min(i[1][1],a_traiter[1][1])]
            pInf = [i[1][0],inter[0]]
            pSup = [i[1][1],inter[1]]
            if pInf[0]==pInf[1] and pSup[0]==pSup[1]:
                return [inter]
            elif pInf[0]!=pInf[1] and pSup[0]==pSup[1]:
                return [inter,pInf]
            elif pInf[0]==pInf[1] and pSup[0]!=pSup[1]:
                return [inter,pSup]
            else:
                return [inter,pInf,pSup]
        #pas d'intersection, le batiment a_traiter ne donne pas sur l'intervalle du batiment i
        else:
            return [i]

def gestion_dist_rec(i_new,intervalles):
    #ajoute un intervalle i_new a l'ensemble des intervalles d'un cote donnant le batiment le plus proche de la rue pour ces abscisses
    #print("gestion_dist_rec")
    #print(i_new)
    #print(intervalles)
    if intervalles == []:
        return [i_new]
    else:
        i = intervalles[0]
        #gestion recursive de l'eventuelle partie de i_new situee avant l'intervalle i
        if i_new[1][0] < i[1][0]:
            intervalles = [i]+gestion_dist_rec([i_new[0],[i_new[1][0],min(i[1][0],i_new[1][1])],i_new[2]],intervalles[1:])
        #gestion recursive de l'eventuelle partie de i_new situee apres l'intervalle i
        if i_new[1][1] > i[1][1]:
            intervalles = [i]+gestion_dist_rec([i_new[0],[i_new[1][0],max(i[1][0],i_new[1][1])],i_new[2]],intervalles[1:])
        #gestion de l'intervalle i
        l_rempIn = fusionI(i_new,i)
        return l_rempIn+intervalles[1:]

def gestion_distance(intervalles1):
    #ne conserve pour chaque partie de la rue que le batiment le plus proche d'un cote donne
    intervalles2=[]
    #on considere successivement les differents intervalles de inttervalles1 en faisant evoluer intervalles2
    #print("gestion_distance")
    #print(intervalles1)
    for i_new in intervalles1:
        intervalles2 = gestion_dist_rec(i_new,intervalles2)
    return intervalles2

def gestion_cotes_rec(ret, intervalle, intervalles12):
    if intervalles12 == [] or intervalle[1][1]<intervalles12[0][1][0]:
        return ret
    elif intervalle[1][0]>intervalles12[0][1][1]:
        return gestion_cotes_rec(ret, intervalle, intervalles12[1:])
    else:
        ret += [[intervalle[0],intervalles12[0][0]],[max(intervalle[1][0],intervalles12[0][1][0]),min(intervalle[1][1],intervalles12[0][1][1])],intervalle[2]+intervalles12[0][2]]
        return gestion_cotes_rec(ret, intervalle, intervalles12[1:])

def gestion_cotes(intervalles11, intervalles12):
    res = []
    for i in intervalles11:
        res += [gestion_cotes_rec([],i,intervalles12)]
    return res

def compute_landsberg(rue, sIndex_bati, features_bati, nom_hauteur):
    #calcule l'indicateur de landsberg pour la rue
    #selection des batiments proches de la rue de chaque cote
    b_rue = rue.geometry().singleSidedBuffer(500,7,QgsGeometry.SideLeft)
    b_rue2 = rue.geometry().singleSidedBuffer(500,7,QgsGeometry.SideRight)
    buffers_rue = [b_rue,b_rue2]
    gdbuff_rue = b_rue.combine(b_rue2)
    batis_id = sIndex_bati.intersects(gdbuff_rue.boundingBox())
    #print(batis_id)
    batis_id_2c = [[],[]]
    for bati_id in batis_id:
        if features_bati[bati_id].geometry().intersects(b_rue):
            batis_id_2c[0] += [bati_id]
        elif features_bati[bati_id].geometry().intersects(b_rue2):
            batis_id_2c[1] += [bati_id]
    #calcul de la projection de chaque batiment sur la rue pour chaque cote
    for i in [0,1]:
        buff_rue = buffers_rue[i]
        voisinage = batis_id_2c[i]
        intervalles = []
        for voisin_id in voisinage:
            voisin = features_bati[voisin_id]
            init = False
            intervalles = []
            for point in voisin.geometry().asPolygon()[0]:
                x = rue.geometry().lineLocatePoint(QgsGeometry.fromPointXY(point))
                if not init:
                    mini = x
                    maxi = x
                    init = True
                else:
                    mini = min(x,mini)
                    maxi = max(x,maxi)
            disR = voisin.geometry().distance(rue.geometry())
            intervalles += [[voisin_id,[mini,maxi],disR]]
        if i == 0:
            intervalles01 = intervalles
        else:
            intervalles11 = intervalles

        """
        batis_id = sIndex_bati.intersects(buff_rue.boundingBox())
        for bati_id in batis_id:
            if features_bati[bati_id].geometry().intersects(buff_rue):
                voisinage += [bati_id]
        intervalles = []
        for voisin_id in voisinage:
            voisin = features_bati[voisin_id]
            init = False
            for point in voisin.geometry().asPolygon()[0]:
                x = rue.geometry().lineLocatePoint(QgsGeometry.fromPoint(point))
                if not init:
                    mini = x
                    maxi = x
                else:
                    mini = min(x,mini)
                    maxi = max(x,maxi)
            disR = voisin.geometry().distance(rue.geometry())
            intervalles += [[voisin_id,[mini,maxi],disR]]
        if i == 0:
            intervalles01 = intervalles
        else:
            intervalles11 = intervalles
        """
    #selection des batiments sur chaque intervalle ou 2 se font face
    intervalles02 = gestion_distance(intervalles01)
    intervalles12 = gestion_distance(intervalles11)
    intervalles2 = gestion_cotes(intervalles11,intervalles12)

    #calcul de l'indicateur sur chaque intervalle ou 2 batiments se font face
    landsberg = 0
    som_int = 0
    for i in intervalles2 :
        hauteur1 = features_bati[i[0][0]].attribute(nom_hauteur)
        hauteur2 = features_bati[i[0][1]].attribute(nom_hauteur)
        hauteur_moy = (hauteur1 + hauteur2)/2.
        som_int += i[1][1]-i[1][0]
        landsberg += (i[1][1]-i[1][0])*hauteur_moy/i[2]
    if som_int > 0:
        landsberg = landsberg / som_int
    """
    for i in intervalles2 :
        hauteur = features_bati[i[0]].attribute(nom_hauteur)
        landsberg += (intervalles2[1][1]-intervalles2[1][0])*hauteur/i[2]
    landsberg = landsberg / som_int
    """
    return landsberg

def standard_deviation(l):
    if len(l) > 1: return stdev(l)
    return 0

def deciles(l): return numpy.percentile(l, numpy.arange(0, 100, 10))

def deciles_as_str(l): return numpy.array2string(deciles(l), precision=2, separator=',',suppress_small=True)
