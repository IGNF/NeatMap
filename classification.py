from PyQt5.QtCore import QVariant
from qgis.core import *

import matplotlib.pyplot as plt
import numpy as np

try:
    import pip
except:
    execfile(os.path.join(self.plugin_dir, get_pip.py))
    import pip
    # just in case the included version is old
    pip.main(['install','--upgrade','pip'])

try:
    from sklearn import datasets
except:
    pip.main(['install','-U' , 'scikit-learn'])
    
    
    
from sklearn import datasets
from sklearn import preprocessing
from sklearn.cluster import KMeans
from sklearn.datasets import make_blobs
from sklearn.metrics import pairwise_distances_argmin



"""
Classification code only k-means for the moment
"""


# Transforing classification to vector layer (layer : input layer, attributes : attribute used for classification, layerName ; nae of the layer, attributeClasse : attribute of the classification,  attributeID : name of attribute ID) , copyAtt indicate if other attributes are copied in output
def kmeans(layer, attributes, nbClasses, layerName, attributeClass, attributeID, copyAtt):  
    # Load in the `digits` data
    dataset = prepareDataset(layer, attributes)
    # Defining k-means
    k_means = KMeans(init='k-means++', n_clusters=nbClasses, n_init=10)
    # Applying k-means
    k_means.fit(dataset.data)
    # Determining centers
    k_means_cluster_centers = np.sort(k_means.cluster_centers_, axis=0)
    # Association between points and nearest centers
    k_means_labels = pairwise_distances_argmin(dataset.data, k_means_cluster_centers)
    # Transforming classification to VectorLayer
    return export(layer, attributes, layerName, attributeClass, k_means_labels, attributeID, copyAtt)

"""
DataManagement
"""

"""
Preparing dataset for sklearn from a layer and a set of selected numeric attributes
"""
def prepareDataset(layer, attributes):
    n_samples = layer.featureCount()
    n_features = len(attributes)
       
    valueArray = []
    attributeArray = []
     
    for a in attributes:
        attributeArray.append(a)
    columns = np.array(attributeArray)   

    for f in layer.getFeatures():
        data_temp = []
        for a in attributes:
            data_temp.append(f.attribute(a))
        valueArray.append(data_temp)

    data = np.array(valueArray)
    # print(data)
    data = preprocessing.scale(data)
    # print(data)
    dataset = datasets.base.Bunch(data=data, columns=columns)
    return dataset



"""
Exporting a vector layer from input dataset and classification
"""
# Transforing classification to vector layer (layer : input layer, attributes : attribute used for classification, layerName ; nae of the layer, attributeClasse : attribute of the classification, vectorClass : the vector with corresponding class, attributeID : name of attribute ID)
def export(layer, attributes, layerName, attributeClass, vectorClass, attributeID, copyAtt):
    vl = QgsVectorLayer("Polygon", layerName, "memory")
    pr = vl.dataProvider()
    vl.startEditing()
    
    
    fields = [QgsField(attributeClass, QVariant.Int)]
    
    
    
    
    if copyAtt :
        #If copy is activated we copy all attributes
        for fieldTemp in layer.fields():
            fields.append(fieldTemp)
    else :
        #if not we only keeps the fild id and necessary to classification
        fields.append(layer.fields().field(attributeID))
        for a in attributes:
                fields.append(QgsField(a, QVariant.Double, "Real", 10, 3))
            
        
    
    pr.addAttributes(fields)
    vl.updateFields()
    
    featureList = []
    
    count = 0;
    
    for f in layer.getFeatures():
        geom = f.geometry()
        
        feat = QgsFeature()
        feat.setGeometry(geom)
        feat.initAttributes(len(fields))

        #print(vectorClass[count])
        feat.setAttribute(0, vectorClass.item(count))
        

        countAtt = 1
        
        if copyAtt:
            countTemp = 0;
            for field in layer.fields() :
                feat.setAttribute( countAtt, f.attribute(countTemp))
                countTemp+=1
                countAtt+=1
                
        else:
            feat.setAttribute(1, f.attribute(attributeID))
            countAtt+=1
            for a in attributes:
                feat.setAttribute(countAtt, f.attribute(a))
                countAtt = countAtt + 1
        
        count = count + 1
        featureList.append(feat)
    pr.addFeatures(featureList)
    vl.commitChanges()
    return vl    

    

