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
input = data_path+'/Pre_Proceso/CoberturaUso.tif'
output = data_path+'/Pre_Proceso/CoberturayUsosEstadistica.csv'
params = {'INPUT':input,'BAND':1,'ZONES':input,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
processing.run(alg,params)

#Se hace la corrección geometrica de las capas de movimientos y de los factores condicionantes.
alg = "native:fixgeometries"
infnM = data_path+'/Mov_Masa.shp'
outfnM= data_path+'/Pre_Proceso/Mov_Masa_Corr.shp'
params = {'INPUT':infnM,'OUTPUT':outfnM}
processing.run(alg,params)

#Obtenemos el shape de las áreas con deslizamientos (IGUAL)
alg = "native:extractbyattribute"
infnD = data_path+'/Pre_Proceso/Mov_Masa_Corr.shp|layername=Mov_Masa_Corr'
outfnD = data_path+'/Pre_Proceso/Deslizamientos.shp'
params = {'INPUT': infnD,'FIELD':'TIPO_MOV1','OPERATOR':0,'VALUE':'Deslizamiento','OUTPUT': outfnD}
processing.run(alg,params)

#Se hace la interesección de el factor condicionante con el área de deslizamientos
alg="gdal:cliprasterbymasklayer"
Input1 = data_path+'/Pre_Proceso/CoberturayUsosSuelo.tif'
Input2 = data_path+'/Pre_Proceso/Deslizamientos.shp'
Output = data_path+'/Pre_Proceso/DeslizamientosCoberturayUsos.tif'
params = {'INPUT':Input1,'MASK':Input2,'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:3116'),'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:3116'),'NODATA':None,'ALPHA_BAND':False,'CROP_TO_CUTLINE':True,'KEEP_RESOLUTION':False,'SET_RESOLUTION':False,'X_RESOLUTION':None,'Y_RESOLUTION':None,'MULTITHREADING':False,'OPTIONS':'','DATA_TYPE':0,'EXTRA':'','OUTPUT':Output}
processing.run(alg,params)

#Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo por deslizamiento)
alg="native:rasterlayerzonalstats"
input = Output
output = data_path+'/Pre_Proceso/DeslizamientosCoberturayUsosEstadistica.csv'
params = {'INPUT':input,'BAND':1,'ZONES':input,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
processing.run(alg,params)

#Creación del dataFrame que se llenará con el desarrollo del Método estádistico Weight of Evidence
DF_Susceptibilidad=pd.DataFrame(columns=['ID','Mov','CLASE','Npix1','Npix2','Npix3','Npix4','Wi+','Wi-','Wf'],dtype=float)

#Se determinan los DataFrame necesario para el desarrollo del método estadístico
FILE_NAME = data_path+'/Pre_Proceso/DeslizamientosCoberturayUsosEstadistica.csv'
DF_DeslizamientosCoberturayUsosEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
#Valores unicos del factor condicionante
FILE_NAME = data_path+'/Pre_Proceso/CoberturayUsosEstadistica.csv'
DF_CoberturayUsosEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
uniquevalues = DF_CoberturaEstadistica["zone"].unique()
atributos=list(sorted(uniquevalues))

for i in range(0,len(atributos)):
    ID=atributos[i]
    #Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i,'ID']= atributos[i]
    #Se determina el número de pixeles con movimientos en masa en la clase
    DF_Susceptibilidad.loc[i,'Mov']=DF_DeslizamientosCoberturayUsosEstadistica.loc[DF_DeslizamientosCoberturayUsosEstadistica['zone']==ID]['count'].sum()
    #Se determina el número de pixeles en la clase
    DF_Susceptibilidad.loc[i,'CLASE']=DF_CoberturayUsosEstadistica.loc[DF_CoberturayUsosEstadistica['zone']==ID]['count'].sum()

Sum_Mov=DF_Susceptibilidad['Mov'].sum()
Sum_Clase=DF_Susceptibilidad['CLASE'].sum()

###Aplicación del método a partir de los valores anteriores-Continuación de llenado del dataframe###
for i in range(0,len(atributos)):
    DF_Susceptibilidad.loc[i,'Npix1']=DF_Susceptibilidad.loc[i,'Mov']
    DF_Susceptibilidad.loc[i,'Npix2']=Sum_Mov-DF_Susceptibilidad.loc[i,'Mov']
    DF_Susceptibilidad.loc[i,'Npix3']=DF_Susceptibilidad.loc[i,'CLASE']-DF_Susceptibilidad.loc[i,'Mov']
    DF_Susceptibilidad.loc[i,'Npix4']=Sum_Clase-DF_Susceptibilidad.loc[i,'CLASE']-(Sum_Mov-DF_Susceptibilidad.loc[i,'Npix1'])
    
    DF_Susceptibilidad.loc[i,'Wi+']=np.log((DF_Susceptibilidad.loc[i,'Npix1']/(DF_Susceptibilidad.loc[i,'Npix1']+DF_Susceptibilidad.loc[i,'Npix2']))/
                                    (DF_Susceptibilidad.loc[i,'Npix3']/(DF_Susceptibilidad.loc[i,'Npix3']+DF_Susceptibilidad.loc[i,'Npix4'])))
    #El peso final de las filas que no convergen serán 0.
    if DF_Susceptibilidad.loc[i,'Wi+']==np.inf:
        DF_Susceptibilidad.loc[i,'Wi+']=0
    elif DF_Susceptibilidad.loc[i,'Wi+']==-np.inf:
        DF_Susceptibilidad.loc[i,'Wi+']=0
    elif math.isnan(DF_Susceptibilidad.loc[i,'Wi+'])==True:
        DF_Susceptibilidad.loc[i,'Wi+']=0
    DF_Susceptibilidad.loc[i,'Wi-']=np.log((DF_Susceptibilidad.loc[i,'Npix2']/(DF_Susceptibilidad.loc[i,'Npix1']+DF_Susceptibilidad.loc[i,'Npix2']))/
                                    (DF_Susceptibilidad.loc[i,'Npix4']/(DF_Susceptibilidad.loc[i,'Npix3']+DF_Susceptibilidad.loc[i,'Npix4'])))
        #El peso final de las filas que no convergen serán 0.
    if DF_Susceptibilidad.loc[i,'Wi-']==np.inf:
        DF_Susceptibilidad.loc[i,'Wi-']=0
    elif DF_Susceptibilidad.loc[i,'Wi-']==-np.inf:
        DF_Susceptibilidad.loc[i,'Wi-']=0
    elif math.isnan(DF_Susceptibilidad.loc[i,'Wi-'])==True:
        DF_Susceptibilidad.loc[i,'Wi-']=0
    DF_Susceptibilidad.loc[i,'Wf']=DF_Susceptibilidad.loc[i,'Wi+']-DF_Susceptibilidad.loc[i,'Wi-']

print(DF_Susceptibilidad)
DF_Susceptibilidad.reset_index().to_csv(data_path+'/02 PreProceso/DF_SusceptibilidadCoberturayUsos.csv',header=True,index=False)

alg="native:reclassifybylayer"
Ipunt1=data_path+'/Pre_Proceso/CoberturaUso.tif'
Input2=data_path+'/Pre_Proceso/DF_SusceptibilidadCoberturayUsos.csv'
Output=data_path+'/Resultados/CoberturayUsosWf.tif'
params={'INPUT_RASTER':Ipunt1,'RASTER_BAND':1,'INPUT_TABLE':Input2,'MIN_FIELD':'ID','MAX_FIELD':'ID','VALUE_FIELD':'Wf','NO_DATA':-9999,'RANGE_BOUNDARIES':2,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Output}
processing.run(alg,params)






    


