from PyQt5.QtWidgets import QInputDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject
import pandas as pd
import numpy as np
import processing
import os

#Ruta general de la ubicación de los archivos relativa a la ubicación del programa
#data_path='C:/Users/paula.montoya/UNIVERSIDAD INDUSTRIAL DE SANTANDER/Infraestructura-Economia(geom) - Documentos/General/01_CART'

data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general con (/): ')
data_path = data_path[0]

infnD = data_path+'/05_SHP/GEOHIDRICO/Inventario/Inventario_Movimientos_Masa.shp' ####

#Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo total)
alg="native:rasterlayerzonalstats"
Factor_Condicionante = data_path+'/Pre_Proceso/SubunidadesGeomorf.tif'
output= data_path+'/Pre_Proceso/GeomorfoEstadistica.csv'
params={'INPUT': Factor_Condicionante,'BAND':1,'ZONES':Factor_Condicionante,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':output}
processing.run(alg,params)

#Obtenemos el shape de los puntos con deslizamientos (IGUAL)
alg = "native:extractbyattribute"
Deslizamientos = data_path+'/Pre_Proceso/Deslizamientos.shp'
params = {'INPUT': infnD,'FIELD':'TIPO_MOV1','OPERATOR':0,'VALUE':'Deslizamiento','OUTPUT': Deslizamientos}
processing.run(alg,params)

#Obtenermos la caracteristica para cada deslizamiento
alg = "qgis:rastersampling"
input = Deslizamientos
raster = Factor_Condicionante
output = data_path+'/Pre_Proceso/ValoresGeomorfo.shp'
params = {'INPUT':input,'RASTERCOPY': raster,'COLUMN_PREFIX':'Id_Condicion','OUTPUT':output}
processing.run(alg,params)

#Creación del dataFrame que se llenará con el desarrollo del Método estádistico Weight of Evidence
DF_Susceptibilidad=pd.DataFrame(columns=['ID','Mov','CLASE','Npix1','Npix2','Npix3','Npix4','Wi+','Wi-','Wf'],dtype=float)

#Se determinan los DataFrame necesario para el desarrollo del método estadístico)
#Valores unicos del factor condicionante
FILE_NAME = data_path+'/Pre_Proceso/GeomorfoEstadistica.csv'
DF_GeomorfoEstadistica = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
uniquevalues = DF_GeomorfoEstadistica["zone"].unique()
atributos=list(sorted(uniquevalues))

ValoresRaster = QgsVectorLayer(data_path+'/Pre_Proceso/ValoresGeomorfo.shp','ValoresGeomorfo')

for i in range(0,len(atributos)):
    ID=atributos[i]
    #Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i,'ID']= atributos[i]
    #Se determina el número de pixeles con movimientos en masa en la clase
    ValoresRaster.selectByExpression(f'"Id_Condici"=\'{ID}\'', QgsVectorLayer.SetSelection)
    selected_fid = []
    selection = ValoresRaster.selectedFeatures()
    DF_Susceptibilidad.loc[i,'Mov'] = len(selection)
    #Se determina el número de pixeles en la clase
    DF_Susceptibilidad.loc[i,'CLASE']=DF_GeomorfoEstadistica.loc[DF_GeomorfoEstadistica['zone']==ID]['count'].sum()

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
DF_Susceptibilidad.reset_index().to_csv(data_path+'/Pre_Proceso/DF_SusceptibilidadGeomorfo.csv',header=True,index=False)

alg="native:reclassifybylayer"
Ipunt1= data_path+'/Pre_Proceso/SubunidadesGeomorf.tif'
Input2= data_path+'/Pre_Proceso/DF_SusceptibilidadGeomorfo.csv'
Output= data_path+'/Resultados/GeomorfoWf.tif'
params={'INPUT_RASTER':Ipunt1,'RASTER_BAND':1,'INPUT_TABLE':Input2,'MIN_FIELD':'ID','MAX_FIELD':'ID','VALUE_FIELD':'Wf','NO_DATA':-9999,'RANGE_BOUNDARIES':2,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Output}
processing.run(alg,params)

iface.addRasterLayer(data_path+'/Resultados/GeomorfoWf.tif',"GeomorfoWf")




    


