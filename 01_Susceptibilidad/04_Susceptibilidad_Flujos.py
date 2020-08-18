from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant
from qgis.gui import QgsMessageBar
from qgis.core import QgsProject
from os import listdir
from time import time
import pandas as pd
import numpy as np
import processing
import os

#Se determina el momento en que inicia la ejcución del programa
start_time = time()

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
if ok == False:
    raise Exception('Cancelar')
data_path = data_path.replace("\\", "/")

# Se listan los archivos en la ruta general
list = listdir(data_path)

# Se determinan los archivos con extensión .shp en la ruta
csv = []
for i in list:
    if i[-4:] == '.csv':
        csv.append(i)

# Zonas de depósito
GeoformasIndicativas, ok = QInputDialog.getItem(None, "Geoformas indicativas de procesos tipo flujo",
                                           "Seleccione el archivo de las geoformas indicativas de procesos tipo flujo", csv, 0, False)
if ok == False:
    raise Exception('Cancelar')

#Asiganción de valor según SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS
#Geoformas indicativas de proceso tipo flujo
FILE_NAME = data_path+'/01 Entradas/GeoformasIndicativasProcesoTipoFlujo.csv'
DF_GeoformasIndicativas = pd.read_csv(FILE_NAME, delimiter=";",encoding='latin-1')
DF_GeoformasIndicativas['CODIGO'] = DF_GeoformasIndicativas['ACRONIMO'].astype(str).str[0:3]

#Geoformas existentes en la capa
FILE_NAME = data_path+'/02 PreProceso/DF_Raster_SubunidadesGeomorf.csv'
DF_SubunidadesGeoform = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
DF_SubunidadesGeoform.drop(['index'],axis='columns',inplace=True)
DF_SubunidadesGeoform['Caract_3'] = DF_SubunidadesGeoform['Caract'].astype(str).str[0:3]

for i in range(0, len(DF_SubunidadesGeoform)): 
    
    # Se determina la subunidad en cuestión
    Subunidad = DF_SubunidadesGeoform.loc[i, 'Caract']
    Caract = DF_SubunidadesGeoform.loc[i, 'Caract_3']
    
    # Se determina si la subunidad se encuentra en la lista de geomorfas indicativas
    if len(DF_GeoformasIndicativas[DF_GeoformasIndicativas['CODIGO'].isin([Caract])])== 0:
        # Si la longitud de la selección es 0 se determinará se pregunta la susceptibilidad
        Susceptibilidad = ["Alta", "Media", "Baja"]
        Susceptibilidad, ok = QInputDialog.getItem(None, "No se encontro",
                                 f"Seleccione la susceptibilidad para la {Subunidad}", Susceptibilidad, 0, False)
        if Susceptibilidad == "Alta":
            Valor = 2
        elif Susceptibilidad == "Media":
            Valor = 1
        else:
            Valor = 0
            
        DF_SubunidadesGeoform.loc[i, 'Valor'] = Valor
    
    else:
        
        # Si la longitud es diferente de 0 se pondrá como indice la columna del acronimo
        DF_GeoformasIndicativas.set_index('CODIGO', inplace=True)
        # Se reemplazará el valor de susceptibilidad correspondiente que se encuentra en la lista de subunidades
        Valor = DF_GeoformasIndicativas.loc[Caract]['VALOR']
        
        if Valor == np.nan:
            Susceptibilidad = ["Alta", "Media", "Baja"]
            Susceptibilidad, ok = QInputDialog.getItem(None, "No se encontro",
                                     f"Seleccione la susceptibilidad para la {Subunidad}", Susceptibilidad, 0, False)
            if Susceptibilidad == "Alta":
                Valor = 2
            elif Susceptibilidad == "Media":
                Valor = 1
            else:
                Valor = 0
            DF_SubunidadesGeoform.loc[i, 'Valor'] = Valor
        
        else:
            
            DF_SubunidadesGeoform.loc[i,'Valor'] = Valor
        
        # Se devuelve al indice númerico para continuar con el for
        DF_GeoformasIndicativas.reset_index(level=0, inplace=True)

print(DF_SubunidadesGeoform)
DF_SubunidadesGeoform.reset_index().to_csv(data_path+'/Pre_Proceso/DF_RasterFlujo_SubunidadesGeoform.csv',header=True,index=False)

#Reclasificación del raster con el valor de Susceptibilidad correspondiente.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path + '/Pre_Proceso/SubunidadesGeomorf.tif'
DF_SubunidadesGeomorf = data_path+'/Pre_Proceso/DF_RasterFlujo_SubunidadesGeoform.csv'
Susceptibilidad_Flujo = data_path + '/Resultados/Susceptibilidad_Flujo.tif'
params={'INPUT_RASTER': Factor_Condicionante, 'RASTER_BAND': 1, 'INPUT_TABLE': DF_SubunidadesGeomorf, 'MIN_FIELD': 'ID',
        'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Valor', 'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,
        'OUTPUT': Susceptibilidad_Flujo}
processing.run(alg,params)

Susceptibilidad_Flujo = QgsRasterLayer(Susceptibilidad_Flujo,"Susceptibilidad Flujo")
QgsProject.instance().addMapLayer(Susceptibilidad_Flujo)

# Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)