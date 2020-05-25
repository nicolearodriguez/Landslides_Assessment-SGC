from PyQt5.QtWidgets import QInputDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject
import pandas as pd
import numpy as np
import processing
import os

#Ruta general en la que se encuentran los archivos necesarios
data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general con (/): ')
data_path = data_path[0]

#Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo total)
alg="native:rasterlayerzonalstats"
Factor_Condicionante = data_path+'/Pre_Proceso/UGS.tif'
Estadisticas_Condicionante = data_path+'/Pre_Proceso/UgsEstadistica.csv'
params={'INPUT': Factor_Condicionante,'BAND':1,'ZONES':Factor_Condicionante,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':Estadisticas_Condicionante}
processing.run(alg,params)

#Se hace la corrección geometrica de las capas de movimientos y de los factores condicionantes.
alg = "native:fixgeometries"
Movimientos_Masa = data_path+'/Mov_Masa.shp'
Movimientos_Corregido = data_path+'/Pre_Proceso/Mov_Masa_Corr.shp'
params = {'INPUT':Movimientos_Masa,'OUTPUT': Movimientos_Corregido}
processing.run(alg,params)

#Obtenemos el shape de las áreas con deslizamientos
alg = "native:extractbyattribute"
Movimientos_Corregido = data_path+'/Pre_Proceso/Mov_Masa_Corr.shp|layername=Mov_Masa_Corr'
Deslizamientos = data_path+'/Pre_Proceso/Deslizamientos.shp'
params = {'INPUT': Movimientos_Corregido,'FIELD':'TIPO_MOV1','OPERATOR':0,'VALUE':'Deslizamiento','OUTPUT': Deslizamientos}
processing.run(alg,params)

#Se hace la interesección de el factor condicionante con el área de deslizamientos
#Obteniendo así los atributos correspondintes a deslizamientos 
alg="gdal:cliprasterbymasklayer"
Factor_Condicionante = Factor_Condicionante
Deslizamientos = Deslizamientos
Deslizamiento_Condicion= data_path+'/Pre_Proceso/DeslizamientosUgs.tif'
params={'INPUT':Factor_Condicionante,'MASK': Deslizamientos,'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:3116'),
'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:3116'),'NODATA':None,'ALPHA_BAND':False,'CROP_TO_CUTLINE':True,
'KEEP_RESOLUTION':False,'SET_RESOLUTION':False,'X_RESOLUTION':None,'Y_RESOLUTION':None,'MULTITHREADING':False,
'OPTIONS':'','DATA_TYPE':0,'EXTRA':'','OUTPUT':Deslizamiento_Condicion}
processing.run(alg,params)

#Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo por deslizamiento)
alg="native:rasterlayerzonalstats"
Deslizamiento_Condicion=Deslizamiento_Condicion
Estadisticas_Deslizamiento= data_path+'/Pre_Proceso/DeslizamientosUgsEstadistica.csv'
params={'INPUT':Deslizamiento_Condicion,'BAND':1,'ZONES':Deslizamiento_Condicion,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':Estadisticas_Deslizamiento}
processing.run(alg,params)

#Creación del dataFrame que se llenará con el desarrollo del Método estádistico Weight of Evidence
DF_Susceptibilidad=pd.DataFrame(columns=['ID','Mov','CLASE','Npix1','Npix2','Npix3','Npix4','Wi+','Wi-','Wf'],dtype=float)

####Se determinan los DataFrame necesarios para el desarrollo del método estadístico###
#Valores únicos del factor condicionante correspondiente a deslizamientos
Estadisticas_Deslizamiento = data_path+'/Pre_Proceso/DeslizamientosUgsEstadistica.csv'
DF_DeslizamientosUgsEstadistica = pd.read_csv(Estadisticas_Deslizamiento, delimiter=",",encoding='latin-1')
#Valores unicos del factor condicionante
Estadisticas_Condicionante = data_path+'/Pre_Proceso/UgsEstadistica.csv'
DF_UgsEstadistica = pd.read_csv(Estadisticas_Condicionante, delimiter=",",encoding='latin-1')
uniquevalues = DF_UgsEstadistica["zone"].unique()
atributos=list(sorted(uniquevalues))

###Se llena el dataframe con los valores correspondientes###
for i in range(0,len(atributos)):
    ID=atributos[i]
    #Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i,'ID']= atributos[i]
    #Se determina el número de pixeles con movimientos en masa en la clase 'Npix1'
    DF_Susceptibilidad.loc[i,'Mov']=DF_DeslizamientosUgsEstadistica.loc[DF_DeslizamientosUgsEstadistica['zone']==ID]['count'].sum()
    #Se determina el número de pixeles en la clase 'Clase'
    DF_Susceptibilidad.loc[i,'CLASE']=DF_UgsEstadistica.loc[DF_UgsEstadistica['zone']==ID]['count'].sum()

Sum_Mov=DF_Susceptibilidad['Mov'].sum()
Sum_Clase=DF_Susceptibilidad['CLASE'].sum()

###Aplicación del método a partir de los valores anteriores-Continuación de llenado del dataframe###
for i in range(0,len(atributos)):
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
DF_Susceptibilidad.reset_index().to_csv(data_path+'/Pre_Proceso/DF_SusceptibilidadUgs.csv',header=True,index=False)

#Ahora se hace la reclasificación del raster del factor condicionante con el Wf correspondiente al atributo.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path+'/Pre_Proceso/UGS.tif'
Susceptibilidad_Condicionante = data_path+'/Pre_Proceso/DF_SusceptibilidadUgs.csv'
Condicionante_Reclass = data_path+'/Resultados/UgsWf.tif'
params={'INPUT_RASTER':Factor_Condicionante,'RASTER_BAND':1,'INPUT_TABLE':Susceptibilidad_Condicionante,'MIN_FIELD':'ID',
        'MAX_FIELD':'ID','VALUE_FIELD':'Wf','NO_DATA':-9999,'RANGE_BOUNDARIES':2,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,
        'OUTPUT':Condicionante_Reclass}
processing.run(alg,params)






    


