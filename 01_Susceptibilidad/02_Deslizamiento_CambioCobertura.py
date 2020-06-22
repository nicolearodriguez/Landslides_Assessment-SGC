from PyQt5.QtWidgets import QInputDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject
import pandas as pd
import numpy as np
import processing
import os

# Ruta general de la ubicación de los archivos relativa a la ubicación del programa
data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
data_path = data_path[0]
data_path = data_path.replace("\\", "/")

Deslizamientos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos.shp')

if Deslizamientos.wkbType()== QgsWkbTypes.Point:
    # Obtenermos el id de la caracteristica del punto de deslizamiento
    alg = "qgis:rastersampling"
    output = data_path+'/Pre_Proceso/ValoresCambioCobertura.shp'
    params = {'INPUT': Deslizamientos, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Id_Condici', 'OUTPUT': output}
    processing.run(alg, params)
    
    ValoresRaster = QgsVectorLayer(data_path + '/Pre_Proceso/ValoresCambioCobertura.shp', 'ValoresUGS')
    
else:
    #Se hace la interesección de el factor condicionante con el área de deslizamientos
    #Obteniendo así los atributos correspondintes a deslizamientos 
    alg = "gdal:cliprasterbymasklayer"
    Factor_Condicionante = rasterfile
    Deslizamiento_Condicion = data_path+'/Pre_Proceso/DeslizamientosCambioCobertura.tif'
    params = {'INPUT': Factor_Condicionante, 'MASK': Deslizamientos, 'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:3116'),
    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3116'), 'NODATA': None, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False,
    'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '', 'OUTPUT': Deslizamiento_Condicion}
    processing.run(alg, params)
    
    #Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo por deslizamiento)
    alg = "native:rasterlayerzonalstats"
    Estadisticas_Deslizamiento = data_path+'/Pre_Proceso/DeslizamientosCambioCoberturaEstadistica.csv'
    params = {'INPUT': Deslizamiento_Condicion, 'BAND': 1, 'ZONES': Deslizamiento_Condicion, 'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Deslizamiento}
    processing.run(alg, params)
    
    Estadisticas_Deslizamiento = data_path+'/Pre_Proceso/DeslizamientosCambioCoberturaEstadistica.csv'
    DF_DeslizamientosEstadistica = pd.read_csv(Estadisticas_Deslizamiento, delimiter=",",encoding='latin-1')

# Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo total)
alg = "native:rasterlayerzonalstats"
rasterfile = data_path + '/Pre_Proceso/CambioCobertura.tif'
output = data_path + '/Pre_Proceso/CambioCoberturaEstadistica.csv'
params = {'INPUT': Factor_Condicionante, 'BAND': 1, 'ZONES': Factor_Condicionante, 'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': output}
processing.run(alg, params)

# Creación del dataFrame que se llenará con el desarrollo del Método estádistico Weight of Evidence
DF_Susceptibilidad = pd.DataFrame(columns=['ID', 'Mov', 'CLASE', 'Npix1', 'Npix2', 'Npix3', 'Npix4', 'Wi+', 'Wi-', 'Wf'], dtype = float)

# Se determinan los DataFrame necesario para el desarrollo del método estadístico
FILE_NAME = data_path + '/Pre_Proceso/CambioCoberturaEstadistica.csv'
DF_CoberturaEstadistica = pd.read_csv(FILE_NAME, delimiter=", ", encoding = 'latin-1')
uniquevalues = DF_CoberturaEstadistica["zone"].unique()
atributos = list(sorted(uniquevalues))

for i in range(0, len(atributos)):
    ID = atributos[i]
    # Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i, 'ID'] = atributos[i]
    # Se determina el número de pixeles en la clase
    DF_Susceptibilidad.loc[i, 'CLASE'] = DF_CoberturaEstadistica.loc[DF_CoberturaEstadistica['zone'] == ID]['count'].sum()
    # Se determina el número de pixeles con movimientos en masa en la clase
    if Deslizamientos.wkbType()== QgsWkbTypes.Point:
        ValoresRaster.selectByExpression(f'"Id_Condici"=\'{ID}\'', QgsVectorLayer.SetSelection)
        selected_fid = []
        selection = ValoresRaster.selectedFeatures()
        DF_Susceptibilidad.loc[i, 'Mov'] = len(selection)
    else:
        DF_Susceptibilidad.loc[i,'Mov']=DF_DeslizamientosEstadistica.loc[DF_DeslizamientosEstadistica['zone']==ID]['count'].sum()

    # Si el número de pixeles es el mismo se hace una corrección para evitar que de infinito
    if DF_Susceptibilidad.loc[i, 'Mov'] == DF_Susceptibilidad.loc[i, 'CLASE']:
        DF_Susceptibilidad.loc[i, 'CLASE'] = DF_Susceptibilidad.loc[i, 'CLASE']+1
        iface.messageBar().pushMessage("Factor condicionante", 'Revisar el factor condicionante', Qgis.Warning, 5)

Sum_Mov = DF_Susceptibilidad['Mov'].sum()
Sum_Clase = DF_Susceptibilidad['CLASE'].sum()

# ##Aplicación del método a partir de los valores anteriores-Continuación de llenado del dataframe###
for i in range(0, len(atributos)):
    DF_Susceptibilidad.loc[i, 'Npix1'] = DF_Susceptibilidad.loc[i, 'Mov']
    DF_Susceptibilidad.loc[i, 'Npix2'] = Sum_Mov-DF_Susceptibilidad.loc[i, 'Mov']
    DF_Susceptibilidad.loc[i, 'Npix3'] = DF_Susceptibilidad.loc[i, 'CLASE']-DF_Susceptibilidad.loc[i, 'Mov']
    DF_Susceptibilidad.loc[i, 'Npix4'] = Sum_Clase-DF_Susceptibilidad.loc[i, 'CLASE']-(Sum_Mov-DF_Susceptibilidad.loc[i, 'Npix1'])
    
    DF_Susceptibilidad.loc[i, 'Wi+'] = np.log((DF_Susceptibilidad.loc[i, 'Npix1']/(DF_Susceptibilidad.loc[i, 'Npix1']+DF_Susceptibilidad.loc[i, 'Npix2']))/(DF_Susceptibilidad.loc[i, 'Npix3']/(DF_Susceptibilidad.loc[i, 'Npix3']+DF_Susceptibilidad.loc[i, 'Npix4'])))
    # El peso final de las filas que no convergen serán 0.
    if DF_Susceptibilidad.loc[i, 'Wi+'] == np.inf:
        DF_Susceptibilidad.loc[i, 'Wi+'] = 0
    elif DF_Susceptibilidad.loc[i, 'Wi+'] == -np.inf:
        DF_Susceptibilidad.loc[i, 'Wi+'] = 0
    elif math.isnan(DF_Susceptibilidad.loc[i, 'Wi+']) is True:
        DF_Susceptibilidad.loc[i, 'Wi+'] = 0
    DF_Susceptibilidad.loc[i, 'Wi-'] = np.log((DF_Susceptibilidad.loc[i, 'Npix2']/(DF_Susceptibilidad.loc[i, 'Npix1']+DF_Susceptibilidad.loc[i, 'Npix2']))/(DF_Susceptibilidad.loc[i, 'Npix4']/(DF_Susceptibilidad.loc[i, 'Npix3']+DF_Susceptibilidad.loc[i, 'Npix4'])))
    # El peso final de las filas que no convergen serán 0.
    if DF_Susceptibilidad.loc[i, 'Wi-'] == np.inf:
        DF_Susceptibilidad.loc[i, 'Wi-'] = 0
    elif DF_Susceptibilidad.loc[i, 'Wi-'] == -np.inf:
        DF_Susceptibilidad.loc[i, 'Wi-'] = 0
    elif math.isnan(DF_Susceptibilidad.loc[i, 'Wi-']) is True:
        DF_Susceptibilidad.loc[i, 'Wi-'] = 0
    DF_Susceptibilidad.loc[i, 'Wf'] = DF_Susceptibilidad.loc[i, 'Wi+']-DF_Susceptibilidad.loc[i, 'Wi-']

print(DF_Susceptibilidad)
DF_Susceptibilidad.reset_index().to_csv(data_path + '/Pre_Proceso/DF_SusceptibilidadCambioCobertura.csv', header=True, index=False)

alg = "native:reclassifybylayer"
Ipunt1 = rasterfile
Input2 = data_path + '/Pre_Proceso/DF_SusceptibilidadCambioCobertura.csv'
Output = data_path + '/Resultados/CambioCoberturaWf.tif'
params = {'INPUT_RASTER': Ipunt1, 'RASTER_BAND': 1, 'INPUT_TABLE': Input2, 'MIN_FIELD': 'ID', 'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Wf', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2, 'NODATA_FOR_MISSING': False, 'DATA_TYPE': 5, 'OUTPUT': Output}
processing.run(alg, params)

iface.addRasterLayer(data_path + '/Resultados/CambioCoberturaWf.tif', "CoberturaWf")




    


