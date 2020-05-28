from PyQt5.QtWidgets import QInputDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject
from osgeo import gdal_array
import pandas as pd
import numpy as np
import processing
import gdal
import os

#Ruta general en la que se encuentran los archivos necesarios
data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general con (/): ')
data_path = data_path[0]

infnD = data_path+'/05_SHP/GEOHIDRICO/Inventario/Inventario_Movimientos_Masa.shp'

#Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo total)
alg="native:rasterlayerzonalstats"
rasterfile = data_path+'/Pre_Proceso/Curvatura_Plana.tif'
output= data_path+'/Pre_Proceso/CurvaturaEstadistica.csv'
params={'INPUT':rasterfile,'BAND':1,'ZONES':rasterfile,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
processing.run(alg,params)

#Obtenemos el shape de los puntos con deslizamientos (IGUAL)
alg = "native:extractbyattribute"
Deslizamientos = data_path+'/Pre_Proceso/Deslizamientos.shp'
params = {'INPUT': infnD,'FIELD':'TIPO_MOV1','OPERATOR':0,'VALUE':'Deslizamiento','OUTPUT': Deslizamientos}
processing.run(alg,params)

#Obtenermos la caracteristica para cada deslizamiento
alg = "qgis:rastersampling"
input = Deslizamientos
raster = rasterfile
output = data_path+'/Pre_Proceso/ValoresCurvatura.shp'
params = {'INPUT':input,'RASTERCOPY': raster,'COLUMN_PREFIX':'Id_Condicion','OUTPUT':output}
processing.run(alg,params)

#Creación del dataFrame que se llenará con el desarrollo del Método estádistico Weight of Evidence
DF_Susceptibilidad=pd.DataFrame(columns=['Min','Max','Mov','CLASE','Npix1','Npix2','Npix3','Npix4','Wi+','Wi-','Wf'],dtype=float)

#Se determinan los DataFrame necesario para el desarrollo del método estadístico
FILE_NAME = data_path+'/Pre_Proceso/CurvaturaEstadistica.csv'
DF_CurvaturaEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
uniquevalues = DF_CurvaturaEstadistica["zone"].unique()
atributos=list(sorted(uniquevalues,reverse=True))
Curve_Min=min(atributos)
Curve_Max=max(atributos)
ValoresRaster = QgsVectorLayer(data_path+'/Pre_Proceso/ValoresCurvatura.shp','ValoresCurvatura')

rasterArray = gdal_array.LoadFile(rasterfile)
rasterList=rasterArray.tolist()

flat_list = []
for sublist in rasterList:
    for item in sublist:
        flat_list.append(item)

df=pd.DataFrame(flat_list)
df=df.drop(df[df[0]<Curve_Min].index)
df=df.drop(df[df[0]>Curve_Max].index)

#Se definen los percentiles en los que se harán los intervalos
percentiles = [0,25,50,75,100]

for i in range(1,len(percentiles)):
    Max=np.percentile(df[0],percentiles[i])
    Min=np.percentile(df[0],percentiles[i-1])
    #Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i,'Min']= Min
    DF_Susceptibilidad.loc[i,'Max']= Max
    #Se determina el número de pixeles en la clase
    DF_Susceptibilidad.loc[i,'CLASE']=DF_CurvaturaEstadistica.loc[(DF_CurvaturaEstadistica['zone'] >= Min) 
                                      & (DF_CurvaturaEstadistica['zone'] < Max)]['count'].sum()
    #Se determina el número de pixeles con movimientos en masa en la clase
    ValoresRaster.selectByExpression(f'"Id_Condici" < \'{Max}\' and "Id_Condici" > \'{Min}\'', QgsVectorLayer.SetSelection)
    selected_fid = []
    selection = ValoresRaster.selectedFeatures()
    DF_Susceptibilidad.loc[i,'Mov'] = len(selection)
    
Sum_Mov=DF_Susceptibilidad['Mov'].sum()
Sum_Clase=DF_Susceptibilidad['CLASE'].sum()

###Aplicación del método a partir de los valores anteriores-Continuación de llenado del dataframe###
for i in range(1,len(DF_Susceptibilidad)+1):
    DF_Susceptibilidad.loc[i,'Npix1']=DF_Susceptibilidad.loc[i,'Mov']
    DF_Susceptibilidad.loc[i,'Npix2']=Sum_Mov-DF_Susceptibilidad.loc[i,'Mov']
    DF_Susceptibilidad.loc[i,'Npix3']=DF_Susceptibilidad.loc[i,'CLASE']-DF_Susceptibilidad.loc[i,'Mov']
    DF_Susceptibilidad.loc[i,'Npix4']=Sum_Clase-DF_Susceptibilidad.loc[i,'CLASE']-(Sum_Mov-DF_Susceptibilidad.loc[i,'Npix1'])
    
    DF_Susceptibilidad.loc[i,'Wi+']=np.log((DF_Susceptibilidad.loc[i,'Npix1']/(DF_Susceptibilidad.loc[i,'Npix1']+DF_Susceptibilidad.loc[i,'Npix2']))/(DF_Susceptibilidad.loc[i,'Npix3']/(DF_Susceptibilidad.loc[i,'Npix3']+DF_Susceptibilidad.loc[i,'Npix4'])))
    #El peso final de las filas que no convergen serán 0.
    if DF_Susceptibilidad.loc[i,'Wi+']==np.inf:
        DF_Susceptibilidad.loc[i,'Wi+']=0
    elif DF_Susceptibilidad.loc[i,'Wi+']==-np.inf:
        DF_Susceptibilidad.loc[i,'Wi+']=0
    elif math.isnan(DF_Susceptibilidad.loc[i,'Wi+'])==True:
        DF_Susceptibilidad.loc[i,'Wi+']=0
    DF_Susceptibilidad.loc[i,'Wi-']=np.log((DF_Susceptibilidad.loc[i,'Npix2']/(DF_Susceptibilidad.loc[i,'Npix1']+DF_Susceptibilidad.loc[i,'Npix2']))/(DF_Susceptibilidad.loc[i,'Npix4']/(DF_Susceptibilidad.loc[i,'Npix3']+DF_Susceptibilidad.loc[i,'Npix4'])))
        #El peso final de las filas que no convergen serán 0.
    if DF_Susceptibilidad.loc[i,'Wi-']==np.inf:
        DF_Susceptibilidad.loc[i,'Wi-']=0
    elif DF_Susceptibilidad.loc[i,'Wi-']==-np.inf:
        DF_Susceptibilidad.loc[i,'Wi-']=0
    elif math.isnan(DF_Susceptibilidad.loc[i,'Wi-'])==True:
        DF_Susceptibilidad.loc[i,'Wi-']=0
    DF_Susceptibilidad.loc[i,'Wf']=DF_Susceptibilidad.loc[i,'Wi+']-DF_Susceptibilidad.loc[i,'Wi-']

print(DF_Susceptibilidad)
DF_Susceptibilidad.reset_index().to_csv(data_path+'/Pre_Proceso/DF_SusceptibilidadCurvatura.csv',header=True,index=False)

alg="native:reclassifybylayer"
Ipunt1= rasterfile
Input2= data_path+'/Pre_Proceso/DF_SusceptibilidadCurvatura.csv'
Output= data_path+'/Resultados/CurvaturaWf.tif'
params={'INPUT_RASTER':Ipunt1,'RASTER_BAND':1,'INPUT_TABLE':Input2,'MIN_FIELD':'Min','MAX_FIELD':'Max','VALUE_FIELD':'Wf','NO_DATA':-9999,'RANGE_BOUNDARIES':2,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Output}
processing.run(alg,params)


iface.addRasterLayer(data_path+'/Resultados/CurvaturaWf.tif',"CurvaturaWf")




    


