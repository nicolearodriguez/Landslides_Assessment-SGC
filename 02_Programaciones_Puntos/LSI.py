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

infnD = data_path+'/05_SHP/GEOHIDRICO/Inventario/Inventario_Movimientos_Masa.shp'  ###

#Capas raster reclasificadas con su respectivo Wf
PendientesReclass=QgsRasterLayer(data_path+'/Resultados/PendientesWf.tif',"PendientesReclass")
QgsProject.instance().addMapLayer(PendientesReclass)
#CoberturaReclass=QgsRasterLayer(data_path+'/Resultados/CoberturaWf.tif', "CoberturaReclass")
#QgsProject.instance().addMapLayer(CoberturaReclass)
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
Expresion = '\"CoberturayUsosReclass@1\" + \"CurvaturaReclass@1\" + \"GeomorfoReclass@1\" + \"PendientesReclass@1\" + \"UgsReclass@1\"'#+\"CoberturaReclass@1\"'
extents = CurvaturaReclass.extent() #Capa de la cuál se copiará la extensión del algoritmo
xmin = extents.xMinimum() #xmin de la extensión
xmax = extents.xMaximum() #xmax de la extensión
ymin = extents.yMinimum() #ymin de la extensión
ymax = extents.yMaximum() #ymax de la extensión
CRS= QgsCoordinateReferenceSystem('EPSG:3116')
params = {'EXPRESSION': Expresion,'LAYERS':[CurvaturaReclass],'CELLSIZE':cellsize,'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'CRS': CRS,'OUTPUT': Output}
processing.run(alg,params)

LSI=QgsRasterLayer(data_path+'/Resultados/LSI.tif', "LSI")
QgsProject.instance().addMapLayer(LSI)

#Se obtienen las estadísticas zonales de los resultados LSI.
alg="native:rasterlayerzonalstats"
rasterfile = data_path+'/Resultados/LSI.tif'
output= data_path+'/Pre_Proceso/LSIEstadistica.csv'
params={'INPUT':rasterfile,'BAND':1,'ZONES':rasterfile,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
processing.run(alg,params)

#Obtenemos el shape de los puntos con deslizamientos (IGUAL)
alg = "native:extractbyattribute"
Deslizamientos = data_path+'/Pre_Proceso/Deslizamientos.shp'
params = {'INPUT': infnD,'FIELD':'TIPO_MOV1','OPERATOR':0,'VALUE':'Deslizamiento','OUTPUT': Deslizamientos}
processing.run(alg,params)

#Obtenermos el LSI para cada deslizamiento
alg = "qgis:rastersampling"
input = Deslizamientos
raster = rasterfile
output = data_path+'/Pre_Proceso/ValoresLSI.shp'
params = {'INPUT':input,'RASTERCOPY': raster,'COLUMN_PREFIX':'Id_Condicion','OUTPUT':output}
processing.run(alg,params)

DF_Susceptibilidad=pd.DataFrame(columns=['LSI_De','LSI_Hasta','PIXLsi','PIXDesliz','PIXLsiAcum','PIXDeslizAcum','X','Y','Area','Categoria','Susceptibilidad'],dtype=float)

#Se determinan los CSV necesario para el proceso
#Valores unicos del factor condicionante
FILE_NAME = data_path+'/Pre_Proceso/LSIEstadistica.csv'
DF_LSIEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
uniquevalues = DF_LSIEstadistica["zone"].unique()
atributos=list(sorted(uniquevalues,reverse=True))
ValoresRaster = QgsVectorLayer(data_path+'/Pre_Proceso/ValoresLSI.shp','ValoresLSI')

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
    DF_Susceptibilidad.loc[i,'PIXLsi']=DF_LSIEstadistica.loc[(DF_LSIEstadistica['zone']>=De) & (DF_LSIEstadistica['zone']<=Hasta)]['count'].sum()
    #Se determina el número de pixeles con movimientos en masa de LSI
    ValoresRaster.selectByExpression(f'"Id_Condici" < \'{Hasta}\' and "Id_Condici" > \'{De}\'', QgsVectorLayer.SetSelection)
    selected_fid = []
    selection = ValoresRaster.selectedFeatures()
    DF_Susceptibilidad.loc[i,'PIXDesliz']= len(selection)

Sum_LSI=DF_Susceptibilidad['PIXLsi'].sum()
Sum_LSIDesliz=DF_Susceptibilidad['PIXDesliz'].sum()

DF_Susceptibilidad.loc[1,'PIXLsiAcum']=DF_Susceptibilidad.loc[1,'PIXLsi']
DF_Susceptibilidad.loc[1,'PIXDeslizAcum']=DF_Susceptibilidad.loc[1,'PIXDesliz']
DF_Susceptibilidad.loc[1,'X']=0
DF_Susceptibilidad.loc[1,'Y']=0

for i in range(2,len(DF_Susceptibilidad)+1):
    #Se determina el número de pixeles con movimientos en masa en la clase
    DF_Susceptibilidad.loc[i,'PIXLsiAcum']= DF_Susceptibilidad.loc[i-1,'PIXLsiAcum']+DF_Susceptibilidad.loc[i,'PIXLsi']
    DF_Susceptibilidad.loc[i,'PIXDeslizAcum']= DF_Susceptibilidad.loc[i-1,'PIXDeslizAcum']+DF_Susceptibilidad.loc[i,'PIXDesliz']
    DF_Susceptibilidad.loc[i,'X']= (DF_Susceptibilidad.loc[i,'PIXLsiAcum']/Sum_LSI)
    DF_Susceptibilidad.loc[i,'Y']= (DF_Susceptibilidad.loc[i,'PIXDeslizAcum']/Sum_LSIDesliz)

for i in range(1,len(DF_Susceptibilidad)):
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
RasterReclass = rasterfile
Tabla = data_path+'/Resultados/DF_LSI.csv'
Salida = data_path+'/Resultados/Susceptibilidad_Deslizamientos.tif'
params={'INPUT_RASTER':RasterReclass,'RASTER_BAND':1,'INPUT_TABLE':Tabla,'MIN_FIELD':'LSI_De','MAX_FIELD':'LSI_Hasta'
        ,'VALUE_FIELD':'Categoria','NO_DATA':-9999,'RANGE_BOUNDARIES':2,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Salida}
processing.run(alg,params)

iface.addRasterLayer(data_path+'/Resultados/Susceptibilidad_Deslizamientos.tif',"Susceptibilidad_Deslizamientos")




