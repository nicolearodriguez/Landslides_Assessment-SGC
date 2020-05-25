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
input= data_path+'/Pre_Proceso/Pendientes.tif'
output= data_path+'/Pre_Proceso/PendientesEstadistica.csv'
params={'INPUT':input,'BAND':1,'ZONES':input,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
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
Input1=input
Input2=outfnD
Output= data_path+'/Pre_Proceso/DeslizamientosPendientes.tif'
params={'INPUT':Input1,'MASK':Input2,'SOURCE_CRS':QgsCoordinateReferenceSystem('EPSG:3116'),'TARGET_CRS':QgsCoordinateReferenceSystem('EPSG:3116'),'NODATA':None,'ALPHA_BAND':False,'CROP_TO_CUTLINE':True,'KEEP_RESOLUTION':False,'SET_RESOLUTION':False,'X_RESOLUTION':None,'Y_RESOLUTION':None,'MULTITHREADING':False,'OPTIONS':'','DATA_TYPE':0,'EXTRA':'','OUTPUT':Output}
processing.run(alg,params)

#Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo por deslizamiento)
alg="native:rasterlayerzonalstats"
input=Output
output= data_path+'/Pre_Proceso/DeslizamientosPendientesEstadistica.csv'
params={'INPUT':input,'BAND':1,'ZONES':input,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
processing.run(alg,params)

#Creación del dataFrame que se llenará con el desarrollo del Método estádistico Weight of Evidence
DF_Susceptibilidad=pd.DataFrame(columns=['Min','Max','Mov','CLASE','Npix1','Npix2','Npix3','Npix4','Wi+','Wi-','Wf'],dtype=float)

#Se determinan los DataFrame necesario para el desarrollo del método estadístico
FILE_NAME = data_path+'/Pre_Proceso/DeslizamientosPendientesEstadistica.csv'
DF_DeslizamientosPendientesEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
FILE_NAME = data_path+'/Pre_Proceso/PendientesEstadistica.csv'
DF_PendientesEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')

#Se definen los intervalos
Intervalo=[0,2,4,8,16,35,55,90]

for i in range(1,len(Intervalo)):
    Max=Intervalo[i]
    Min=Intervalo[i-1]
    #Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i,'Min']= Intervalo[i-1]
    DF_Susceptibilidad.loc[i,'Max']= Intervalo[i]
    #Se determina el número de pixeles con movimientos en masa en la clase
    DF_Susceptibilidad.loc[i,'Mov']=DF_DeslizamientosPendientesEstadistica.loc[(DF_DeslizamientosPendientesEstadistica['zone']>Min) 
                                    & (DF_DeslizamientosPendientesEstadistica['zone']<=Max)]['count'].sum()
    #Se determina el número de pixeles en la clase
    DF_Susceptibilidad.loc[i,'CLASE']=DF_PendientesEstadistica.loc[(DF_PendientesEstadistica['zone']>Min) & (DF_PendientesEstadistica['zone']<=Max)]['count'].sum()

Sum_Mov=DF_Susceptibilidad['Mov'].sum()
Sum_Clase=DF_Susceptibilidad['CLASE'].sum()

###Aplicación del método a partir de los valores anteriores-Continuación de llenado del dataframe###
for i in range(1,len(Intervalo)):
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
DF_Susceptibilidad.reset_index().to_csv(data_path+'/02 PreProceso/DF_Susceptibilidad.csv',header=True,index=False)

alg="native:reclassifybylayer"
Ipunt1= data_path+'/Pre_Proceso/Pendientes.tif'
Input2= data_path+'/Pre_Proceso/DF_Susceptibilidad.csv'
Output= data_path+'/Resultados/PendientesWf.tif'
params={'INPUT_RASTER':Ipunt1,'RASTER_BAND':1,'INPUT_TABLE':Input2,'MIN_FIELD':'Min','MAX_FIELD':'Max','VALUE_FIELD':'Wf','NO_DATA':-9999,'RANGE_BOUNDARIES':0,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Output}
processing.run(alg,params)




    


