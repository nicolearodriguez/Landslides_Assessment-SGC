from PyQt5.QtWidgets import QInputDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject
import matplotlib.pyplot as plt
from osgeo import gdal_array
import pandas as pd
import numpy as np
import processing
import gdal
import os

#Ruta general en la que se encuentran los archivos necesarios
data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general con (/): ')
data_path = data_path[0]

Pixel = QInputDialog.getDouble(None, 'CELLSIZE', 'Introduce el tamaño del pixel: ')
cellsize = Pixel[0]

#Capas raster reclasificadas con su respectivo Wf
PendientesReclass=QgsRasterLayer(data_path+'/Resultados/PendientesWf.tif',"PendientesReclass")
QgsProject.instance().addMapLayer(PendientesReclass)
CoberturaReclass=QgsRasterLayer(data_path+'/Resultados/CoberturaWf.tif', "CoberturaReclass")
QgsProject.instance().addMapLayer(CoberturaReclass)
GeomorfoReclass=QgsRasterLayer(data_path+'/Resultados/GeomorfoWf.tif', "GeomorfoReclass")
QgsProject.instance().addMapLayer(GeomorfoReclass)
UgsReclass=QgsRasterLayer(data_path+'/Resultados/UgsWf.tif', "UgsReclass")
QgsProject.instance().addMapLayer(UgsReclass)
CoberturayUsosReclass=QgsRasterLayer(data_path+'/Resultados/CoberturayUsosWf.tif', "CoberturayUsosReclass")
QgsProject.instance().addMapLayer(CoberturayUsosReclass)
CurvaturaReclass=QgsRasterLayer(data_path+'/Resultados/CurvaturaWf.tif', "CurvaturaReclass")
QgsProject.instance().addMapLayer(CurvaturaReclass)

#Dirección del resultado de la suma de los Wf
Output = data_path+'/Resultados/LSI.tif'

#Sumatoria de los raster
alg = "qgis:rastercalculator"
Expresion = '\"CoberturaReclass@1\" + \"CoberturayUsosReclass@1\" + \"CurvaturaReclass@1\" + \"GeomorfoReclass@1\" + \"PendientesReclass@1\" + \"UgsReclass@1\"'
extents = CurvaturaReclass.extent() #Capa de la cuál se copiará la extensión del algoritmo
xmin = extents.xMinimum() #xmin de la extensión
xmax = extents.xMaximum() #xmax de la extensión
ymin = extents.yMinimum() #ymin de la extensión
ymax = extents.yMaximum() #ymax de la extensión
CRS= QgsCoordinateReferenceSystem('EPSG:3116')
params = {'EXPRESSION': Expresion,'LAYERS':[CoberturaReclass],'CELLSIZE':0,'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'CRS': CRS,'OUTPUT': Output}
processing.run(alg,params)

LSI=QgsRasterLayer(data_path+'/Resultados/LSI.tif', "lSI")
QgsProject.instance().addMapLayer(LSI)

#Se obtienen las estadísticas zonales de los resultados LSI.
alg="native:rasterlayerzonalstats"
input= data_path+'/Resultados/LSI.tif'
output= data_path+'/Pre_Proceso/LSIEstadistica.csv'
params={'INPUT':input,'BAND':1,'ZONES':input,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
processing.run(alg,params)

#Se hace la corrección geometrica de la capa de movimientos en masa.
alg = "native:fixgeometries"
infnM = data_path+'/Mov_Masa.shp'
outfnM= data_path+'/Pre_Proceso/Mov_Masa_Corr.shp'
params = {'INPUT':infnM,'OUTPUT':outfnM}
processing.run(alg,params)

#Obtenemos el shape de las áreas con deslizamientos
alg = "native:extractbyattribute"
infnD = data_path+'/Pre_Proceso/Mov_Masa_Corr.shp|layername=Mov_Masa_Corr'
outfnD = data_path+'/Pre_Proceso/Deslizamientos.shp'
params = {'INPUT': infnD,'FIELD':'TIPO_MOV1','OPERATOR':0,'VALUE':'Deslizamiento','OUTPUT': outfnD}
processing.run(alg,params)

#Se hace la interesección de la capa LSI con el área de deslizamientos
alg="gdal:cliprasterbymasklayer"
Input1 = data_path+'/Resultados/LSI.tif'
Input2 = data_path+'/Pre_Proceso/Deslizamientos.shp'
Output= data_path+'/Pre_Proceso/DeslizamientosLSI.tif'
params={'INPUT':Input1,'MASK':Input2,'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:3116'),'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:3116'),
       'NODATA':None,'ALPHA_BAND':False,'CROP_TO_CUTLINE':True,'KEEP_RESOLUTION':False,'SET_RESOLUTION':False,'X_RESOLUTION':None,'Y_RESOLUTION':None,
       'MULTITHREADING':False,'OPTIONS':'','DATA_TYPE':0,'EXTRA':'','OUTPUT':Output}
processing.run(alg,params)

#Se obtienen las estadísticas zonales de los resultados LSI en zona de deslizamientos.
alg="native:rasterlayerzonalstats"
input= data_path+'/Pre_Proceso/DeslizamientosLSI.tif'
output= data_path+'/Pre_Proceso/DeslizamientosLSIEstadistica.csv'
params={'INPUT':input,'BAND':1,'ZONES':input,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
processing.run(alg,params)

DF_Susceptibilidad=pd.DataFrame(columns=['LSI_De','LSI_Hasta','PIXLsi','PIXDesliz','PIXLsiAcum','PIXDeslizAcum','X','Y','Area','Categoria','Susceptibilidad'],dtype=float)

#Se determinan los CSV necesario para el proceso
FILE_NAME = data_path+'/Pre_Proceso/DeslizamientosLSIEstadistica.csv'
DF_DeslizamientosLSIEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
#Valores unicos del factor condicionante
FILE_NAME = data_path+'/Pre_Proceso/LSIEstadistica.csv'
DF_LSIEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
uniquevalues = DF_LSIEstadistica["zone"].unique()
atributos=list(sorted(uniquevalues,reverse=True))

LSI_Min=int((round(min(atributos),0))-1)
LSI_Max=int(round(max(atributos),0)+1)
Intervalo=list(sorted(range(LSI_Min,LSI_Max+1),reverse=True))

rasterArray = gdal_array.LoadFile(rasterfile)
rasterList=rasterArray.tolist()

flat_list = []
for sublist in rasterList:
    for item in sublist:
        flat_list.append(item)

df=pd.DataFrame(flat_list)
df=df.drop(df[df[0]<LSI_Min].index)
df=df.drop(df[df[0]>LSI_Max].index)

#Se definen los percentiles en los que se harán los intervalos
percentiles = list(sorted(range(101),reverse=True))

for i in range(1,len(percentiles)):
    De=np.percentile(df[0],percentiles[i])
    Hasta=np.percentile(df[0],percentiles[i-1])
    #Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i,'LSI_De']= De
    DF_Susceptibilidad.loc[i,'LSI_Hasta']= Hasta
    #Número de pixeles según la clase LSI
    DF_Susceptibilidad.loc[i,'PIXLsi']=DF_LSIEstadistica.loc[(DF_LSIEstadistica['zone']>De) & (DF_LSIEstadistica['zone']<=Hasta)]['count'].sum()
    #Se determina el número de pixeles con movimientos en masa de LSI
    DF_Susceptibilidad.loc[i,'PIXDesliz']=DF_DeslizamientosLSIEstadistica.loc[(DF_DeslizamientosLSIEstadistica['zone']>De) & (DF_DeslizamientosLSIEstadistica['zone']<=Hasta)]['count'].sum()

Sum_LSI=DF_Susceptibilidad['PIXLsi'].sum()
Sum_LSIDesliz=DF_Susceptibilidad['PIXDesliz'].sum()

DF_Susceptibilidad.loc[0,'PIXLsiAcum']=DF_Susceptibilidad.loc[0,'PIXLsi']
DF_Susceptibilidad.loc[0,'PIXDeslizAcum']=DF_Susceptibilidad.loc[0,'PIXDesliz']
DF_Susceptibilidad.loc[0,'X']=0
DF_Susceptibilidad.loc[0,'Y']=0

for i in range(2,len(DF_Susceptibilidad)+1):
    #Se determina el número de pixeles con movimientos en masa en la clase
    DF_Susceptibilidad.loc[i,'PIXLsiAcum']= DF_Susceptibilidad.loc[i-1,'PIXLsiAcum']+DF_Susceptibilidad.loc[i,'PIXLsi']
    DF_Susceptibilidad.loc[i,'PIXDeslizAcum']= DF_Susceptibilidad.loc[i-1,'PIXDeslizAcum']+DF_Susceptibilidad.loc[i,'PIXDesliz']
    DF_Susceptibilidad.loc[i,'X']= (DF_Susceptibilidad.loc[i,'PIXLsiAcum']/Sum_LSI)
    DF_Susceptibilidad.loc[i,'Y']= (DF_Susceptibilidad.loc[i,'PIXDeslizAcum']/Sum_LSIDesliz)

for i in range(1,len(DF_Susceptibilidad)+1):
    DF_Susceptibilidad.loc[i,'Area']= (DF_Susceptibilidad.loc[i+1,'X']-DF_Susceptibilidad.loc[i,'X'])*(DF_Susceptibilidad.loc[i+1,'Y']+DF_Susceptibilidad.loc[i,'Y'])/2

Area_Total=DF_Susceptibilidad['Area'].sum()
print('El área bajo la curva es: ',Area_Total)

DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y']<=0.75)].index,'Categoria']=2
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y']<=0.75)].index,'Susceptibilidad']='Alta'
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y']>0.75) & (DF_Susceptibilidad['Y']<=0.98)].index,'Categoria']=1
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y']>0.75) & (DF_Susceptibilidad['Y']<=0.98)].index,'Susceptibilidad']='Media'
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y']>0.98)].index,'Categoria']=0
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y']>0.98)].index,'Susceptibilidad']='Baja'

print(DF_Susceptibilidad)
DF_Susceptibilidad.reset_index().to_csv(data_path+'/Pre_Proceso/DF_LSI.csv',header=True,index=False)

#Extracción de la curva de éxito.
x=DF_Susceptibilidad['X']
y=DF_Susceptibilidad['Y']
#Se hace las espacialización de los puntos.
fig, ax = plt.subplots(1, 1, figsize=(12, 12))
ax.plot(x,y,color='g',marker='o',linestyle='-')
ax.set_xlabel("Porcentaje del mapa de susceptibilidad")
ax.set_ylabel("Porcentaje de los deslizamientos en el área de estudio")
ax.set_title('CURVA DE ÉXITO', pad = 20, fontdict={'fontsize':20, 'color': '#4873ab'})
plt.show()
fig.savefig(data_path+'/Resultados/Curva_Exito.jpg')

#Reclasificación del mapa raster
alg="native:reclassifybylayer"
RasterReclass = data_path+'/Resultados/LSI.tif'
Tabla = data_path+'/Pre_Proceso/DF_LSI.csv'
Salida = data_path+'/Resultados/SusceptibilidadReclass.tif'
params={'INPUT_RASTER':RasterReclass,'RASTER_BAND':1,'INPUT_TABLE':Tabla,'MIN_FIELD':'LSI_De','MAX_FIELD':'LSI_Hasta'
        ,'VALUE_FIELD':'Categoria','NO_DATA':-9999,'RANGE_BOUNDARIES':0,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Salida}
processing.run(alg,params)

iface.addRasterLayer(data_path+'/Resultados/SusceptibilidadReclass.tif',"Raster")




