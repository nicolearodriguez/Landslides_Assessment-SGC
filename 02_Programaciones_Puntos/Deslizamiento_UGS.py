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
Factor_Condicionante = data_path+'/Pre_Proceso/UGS.tif'
Estadisticas_Condicionante = data_path+'/Pre_Proceso/UgsEstadistica.csv'
params={'INPUT': Factor_Condicionante,'BAND':1,'ZONES':Factor_Condicionante,'ZONES_BAND':1,'REF_LAYER':0,'OUTPUT_TABLE':Estadisticas_Condicionante}
processing.run(alg,params)

#Obtenemos el shape de los puntos con deslizamientos 
alg = "native:extractbyattribute"
Deslizamientos = data_path+'/Pre_Proceso/Deslizamientos.shp'
params = {'INPUT': infnD,'FIELD':'TIPO_MOV1','OPERATOR':0,'VALUE':'Deslizamiento','OUTPUT': Deslizamientos}
processing.run(alg,params)

#Obtenermos la caracteristica para cada deslizamiento
alg = "qgis:rastersampling"
input = Deslizamientos
raster = Factor_Condicionante
output = data_path+'/Pre_Proceso/ValoresUGS.shp'
params = {'INPUT':input,'RASTERCOPY': raster,'COLUMN_PREFIX':'Id_Condicion','OUTPUT':output}
processing.run(alg,params)

#Creación del dataFrame que se llenará con el desarrollo del Método estádistico Weight of Evidence
DF_Susceptibilidad=pd.DataFrame(columns=['ID','Mov','CLASE','Npix1','Npix2','Npix3','Npix4','Wi+','Wi-','Wf'],dtype=float)

####Se determinan los DataFrame necesarios para el desarrollo del método estadístico###
#Valores unicos del factor condicionante
Estadisticas_Condicionante = data_path+'/Pre_Proceso/UgsEstadistica.csv'
DF_UgsEstadistica = pd.read_csv(Estadisticas_Condicionante, delimiter=",",encoding='latin-1')
uniquevalues = DF_UgsEstadistica["zone"].unique()
atributos=list(sorted(uniquevalues))

ValoresRaster = QgsVectorLayer(data_path+'/Pre_Proceso/ValoresUGS.shp','ValoresUGS')

###Se llena el dataframe con los valores correspondientes###
for i in range(0,len(atributos)):
    ID=atributos[i]
    #Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i,'ID']= atributos[i]
    #Se determina el número de pixeles con movimientos en masa en la clase 'Mov'
    ValoresRaster.selectByExpression(f'"Id_Condici"=\'{ID}\'', QgsVectorLayer.SetSelection)
    selected_fid = []
    selection = ValoresRaster.selectedFeatures()
    DF_Susceptibilidad.loc[i,'Mov'] = len(selection)
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

iface.addRasterLayer(data_path+'/Resultados/UgsWf.tif',"UgsWf")



    


