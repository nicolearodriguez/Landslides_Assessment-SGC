from PyQt5.QtWidgets import QInputDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject
import pandas as pd
import numpy as np
import processing
import os

#data_path = 'D:/Nueva carpeta/UNIVERSIDAD/10_TRABAJO DE GRADO/09 Ejecución/01 PyQgis/01 Entradas'
#Ruta general de la ubicación de los archivos relativa a la ubicación del programa
data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general con (/): ')
data_path = data_path[0]

os.mkdir(data_path + '/Pre_Proceso')
os.mkdir(data_path + '/Resultados')

Pixel = QInputDialog.getDouble(None, 'CELLSIZE', 'Introduce el tamaño del pixel: ')
cellsize = Pixel[0]

#Entradas necesarias para la ejecución-DEM del área de estudio y capas vectoriales de los factores condicionante
UGS = data_path+'/UGS.shp'
SubunidadesGeomorf = data_path+'/SubunidadesGeomorf.shp'
CoberturaUso = data_path+'/CoberturaUso.shp'
CambioCobertura = data_path+'/CambioCobertura.shp'

######################################UGS######################################

#Se hace la corrección geometrica del factor condicionantes.
UGS_Corr = data_path+'/Pre_Proceso/UGS_Corr.shp'
processing.run("native:fixgeometries",{'INPUT':UGS,'OUTPUT':UGS_Corr})

#La capa corregida se lee como una capa vectorial
UGS = QgsVectorLayer(data_path+'/Pre_Proceso/UGS_Corr.shp','UGS')

#Se inicia a editar la capa
caps = UGS.dataProvider().capabilities()
#Se añade un campo nuevo llamado "Raster" en el que se pondrá el valor único ce cada aracteristica para la posterior rasterización
UGS.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
#Se guarda la edición
UGS.updateFields()

#Se determina el índice de la columna que fue agregada
col= UGS.fields().indexFromName("Raster")

#Se obtienen los valores únicos de las caracteristicas correspondientes al factor condicionante
uniquevalues = [];
uniqueprovider = UGS.dataProvider()
fields = uniqueprovider.fields()
id = fields.indexFromName('UGS')
uniquevalues = uniqueprovider.uniqueValues( id )
atributos=list(uniquevalues)
print(atributos)

#Se crea un datframe con el fin de conocer el id correspondiente a cada caraceristica
DF_Raster=pd.DataFrame(columns=['Caract','ID'],dtype=float)

#Se inicia a editar
caps = UGS.dataProvider().capabilities()
#Se seleccionan los poligonos correspondiente al atributo en estudio
for i in range(0,len(atributos)):
    Atri=atributos[i] #Se caracteristica en cuestión
    DF_Raster.loc[i,'Caract']= Atri #Se llena el dataframe con la caracteristica
    DF_Raster.loc[i,'ID']= i+1  #Se llena el dataframe con el id de la caracteristica
    DF_Raster.loc[i,'General']= Atri[0:2] #Para el caso de las UGS se obtienen las dos primeras letras de su acronimo
    UGS.selectByExpression(f'"UGS"=\'{Atri}\'', QgsVectorLayer.SetSelection) #Se hace la selección en la capa de la caracteristica en cuestión

    #Se reemplazan los id del atributo seleccionada
    selected_fid = []
    selection = UGS.selectedFeatures()
    for feature in selection: #Se recorren las filas seleccionadas
        fid=feature.id() #Se obtiene el id de la fila seleccionada en cuestión
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            attrs = { col : i+1 } #Se determina que en la columna nueva se llenará con el id de la caracteristica (i+1)
            UGS.dataProvider().changeAttributeValues({ fid : attrs }) #Se hace el cambio de los atributos

#Se guarda el raster y se añade al lienzo la capa vectorial con su nueva columna llena
print(DF_Raster)
DF_Raster.reset_index().to_csv(data_path+'/Pre_Proceso/DF_Raster_UGS.csv',header=True,index=False)
QgsProject.instance().addMapLayer(UGS)

#Se hace la respectiva rasterización del factor condicionante
alg="gdal:rasterize"
Shape = UGS #Nombre de la capa vectorial
Raster = data_path+'/Pre_Proceso/UGS.tif' #Ruta y nombre del archivo de salida
Field= 'Raster' #Columna con la cuál se hará la rasterización
extents = UGS.extent() #Capa de la cuál se copiará la extensión del algoritmo
xmin = extents.xMinimum() #xmin de la extensión
xmax = extents.xMaximum() #xmax de la extensión
ymin = extents.yMinimum() #ymin de la extensión
ymax = extents.yMaximum() #ymax de la extensión
params= {'INPUT':Shape,'FIELD': Field,'BURN':0,'UNITS':1,'WIDTH':cellsize,'HEIGHT':cellsize,'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'NODATA':0,'OPTIONS':'','DATA_TYPE':5,'INIT':None,'INVERT':False,'OUTPUT': Raster}
processing.run(alg,params)

#Se añade la capa raster al lienzo
iface.addRasterLayer(data_path+'/Pre_Proceso/UGS.tif',"UGS")

######################################Subunidades Geomorfologicas######################################

#Se hace la corrección geometrica del factores condicionantes.
SubunidadesGeomorf_Corr = data_path+'/Pre_Proceso/SubunidadesGeomorf_Corr.shp'
processing.run("native:fixgeometries",{'INPUT':SubunidadesGeomorf,'OUTPUT':SubunidadesGeomorf_Corr})

SubunidadesGeomorf = QgsVectorLayer(data_path+'/Pre_Proceso/SubunidadesGeomorf_Corr.shp','Subunidades Geomorfologicas')

caps = SubunidadesGeomorf.dataProvider().capabilities()
SubunidadesGeomorf.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
SubunidadesGeomorf.updateFields()

col= SubunidadesGeomorf.fields().indexFromName("Raster")

#Valores unicos del factor condicionante
uniquevalues = [];
uniqueprovider = SubunidadesGeomorf.dataProvider()
fields = uniqueprovider.fields()
id = fields.indexFromName('Codigo')
uniquevalues = uniqueprovider.uniqueValues( id )
atributos=list(uniquevalues)
print(atributos)

DF_Raster=pd.DataFrame(columns=['Caract','ID'],dtype=float)

caps = SubunidadesGeomorf.dataProvider().capabilities()
#Se seleccionan los poligonos correspondiente al atributo en estudio
for i in range(0,len(atributos)):
    Atri=atributos[i]
    DF_Raster.loc[i,'Caract']= Atri
    DF_Raster.loc[i,'ID']= i+1
    SubunidadesGeomorf.selectByExpression(f'"Codigo"=\'{Atri}\'', QgsVectorLayer.SetSelection)
    
    #Se reemplazan los id del atributo seleccionada
    selected_fid = []
    selection = SubunidadesGeomorf.selectedFeatures()
    for feature in selection:
        fid=feature.id()
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            attrs = { col : i+1 }
            SubunidadesGeomorf.dataProvider().changeAttributeValues({ fid : attrs })

print(DF_Raster)
DF_Raster.reset_index().to_csv(data_path+'/Pre_Proceso/DF_Raster_SubunidadesGeomorf.csv',header=True,index=False)
QgsProject.instance().addMapLayer(SubunidadesGeomorf)

alg="gdal:rasterize"
Shape = SubunidadesGeomorf
Raster = data_path+'/Pre_Proceso/SubunidadesGeomorf.tif'
Field= 'Raster'
extents = SubunidadesGeomorf.extent()
xmin = extents.xMinimum()
xmax = extents.xMaximum()
ymin = extents.yMinimum()
ymax = extents.yMaximum()
params= {'INPUT':Shape,'FIELD': Field,'BURN':0,'UNITS':1,'WIDTH':cellsize,'HEIGHT':cellsize,'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'NODATA':0,'OPTIONS':'','DATA_TYPE':5,'INIT':None,'INVERT':False,'OUTPUT': Raster}
processing.run(alg,params)

iface.addRasterLayer(data_path+'/Pre_Proceso/SubunidadesGeomorf.tif',"SubunidadesGeomorf")

######################################Cobertura y Uso######################################

#Se hace la corrección geometrica del factores condicionantes.
CoberturaUso_Corr = data_path+'/Pre_Proceso/CoberturaUso_Corr.shp'
processing.run("native:fixgeometries",{'INPUT':CoberturaUso,'OUTPUT':CoberturaUso_Corr})

CoberturaUso = QgsVectorLayer(data_path+'/Pre_Proceso/CoberturaUso_Corr.shp','Cobertura y Uso')

caps = CoberturaUso.dataProvider().capabilities()
CoberturaUso.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
CoberturaUso.updateFields()

col= CoberturaUso.fields().indexFromName("Raster")

#Valores unicos del factor condicionante
uniquevalues = [];
uniqueprovider = CoberturaUso.dataProvider()
fields = uniqueprovider.fields()
id = fields.indexFromName('COD')
uniquevalues = uniqueprovider.uniqueValues( id )
atributos=list(uniquevalues)
print(atributos)

DF_Raster=pd.DataFrame(columns=['Caract','ID'],dtype=float)

caps = CoberturaUso.dataProvider().capabilities()
#Se seleccionan los poligonos correspondiente al atributo en estudio
for i in range(0,len(atributos)):
    Atri=atributos[i]
    DF_Raster.loc[i,'Caract']= Atri
    DF_Raster.loc[i,'ID']= i+1
    CoberturaUso.selectByExpression(f'"COD"=\'{Atri}\'', QgsVectorLayer.SetSelection)
    
    #Se reemplazan los id del atributo seleccionada
    selected_fid = []
    selection = CoberturaUso.selectedFeatures()
    for feature in selection:
        fid=feature.id()
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            attrs = { col : i+1 }
            CoberturaUso.dataProvider().changeAttributeValues({ fid : attrs })

print(DF_Raster)
DF_Raster.reset_index().to_csv(data_path+'/Pre_Proceso/DF_Raster_CoberturaUso.csv',header=True,index=False)
QgsProject.instance().addMapLayer(CoberturaUso)

alg="gdal:rasterize"
Shape = CoberturaUso
Raster = data_path+'/Pre_Proceso/CoberturaUso.tif'
Field= 'Raster'
extents = CoberturaUso.extent()
xmin = extents.xMinimum()
xmax = extents.xMaximum()
ymin = extents.yMinimum()
ymax = extents.yMaximum()
params= {'INPUT':Shape,'FIELD': Field,'BURN':0,'UNITS':1,'WIDTH':cellsize,'HEIGHT':cellsize,'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'NODATA':0,'OPTIONS':'','DATA_TYPE':5,'INIT':None,'INVERT':False,'OUTPUT': Raster}
processing.run(alg,params)

iface.addRasterLayer(data_path+'/Pre_Proceso/CoberturaUso.tif',"CoberturaUso")

######################################Cambio de Cobertura######################################

#Se hace la corrección geometrica del factores condicionantes.
CambioCobertura_Corr = data_path+'/Pre_Proceso/CambioCobertura_Corr.shp'
processing.run("native:fixgeometries",{'INPUT':CambioCobertura,'OUTPUT':CambioCobertura_Corr})

CambioCobertura = QgsVectorLayer(data_path+'/Pre_Proceso/CambioCobertura_Corr.shp','Cambio de Cobertura')

caps = CambioCobertura.dataProvider().capabilities()
CambioCobertura.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
CambioCobertura.updateFields()

col= CambioCobertura.fields().indexFromName("Raster")

#Valores unicos del factor condicionante
uniquevalues = [];
uniqueprovider = CambioCobertura.dataProvider()
fields = uniqueprovider.fields()
id = fields.indexFromName('CLAS')
uniquevalues = uniqueprovider.uniqueValues( id )
atributos=list(uniquevalues)
print(atributos)

DF_Raster=pd.DataFrame(columns=['Caract','ID'],dtype=float)

caps = CambioCobertura.dataProvider().capabilities()
#Se seleccionan los poligonos correspondiente al atributo en estudio
for i in range(0,len(atributos)):
    Atri=atributos[i]
    DF_Raster.loc[i,'Caract']= Atri
    DF_Raster.loc[i,'ID']= i+1
    CambioCobertura.selectByExpression(f'"CLAS"=\'{Atri}\'', QgsVectorLayer.SetSelection)
    
    #Se reemplazan los id del atributo seleccionada
    selected_fid = []
    selection = CambioCobertura.selectedFeatures()
    for feature in selection:
        fid=feature.id()
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            attrs = { col : i+1 }
            CambioCobertura.dataProvider().changeAttributeValues({ fid : attrs })

print(DF_Raster)
DF_Raster.reset_index().to_csv(data_path+'/Pre_Proceso/DF_Raster_CambioCobertura.csv',header=True,index=False)
QgsProject.instance().addMapLayer(CambioCobertura)

alg="gdal:rasterize"
Shape = CambioCobertura
Raster = data_path+'/Pre_Proceso/CambioCobertura.tif'
Field= 'Raster'
extents = CambioCobertura.extent()
xmin = extents.xMinimum()
xmax = extents.xMaximum()
ymin = extents.yMinimum()
ymax = extents.yMaximum()
params= {'INPUT':Shape,'FIELD': Field,'BURN':0,'UNITS':1,'WIDTH':cellsize,'HEIGHT':cellsize,'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'NODATA':0,'OPTIONS':'','DATA_TYPE':5,'INIT':None,'INVERT':False,'OUTPUT': Raster}
processing.run(alg,params)

iface.addRasterLayer(data_path+'/Pre_Proceso/CambioCobertura.tif',"CambioCobertura")






