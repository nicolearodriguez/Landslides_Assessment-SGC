"""
@author: Nicole Alejadra Rodríguez Vargas
nicole.rodriguez@correo.uis.edu.co
"""

"""
En esta programación se caracteriza la susceptibilidad por movimientos en masa tipo flujo,
el procedimiento solo consta del análisis de subunidades indicativas de este proceso, a 
partir de estas se caracteriza la susceptibilidad por estos procesos.
"""

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

#Se imprime una recomendación
QMessageBox.information(iface.mainWindow(), "!Tenga en cuenta!",
                        'Es necesario que haya descargado previamente el archivo CSV '
                        'con las geoformas indicativas de procesos tipo flujos '
                        '(GeoformasIndicativasProcesoTipoFlujo.csv) y este guardada '
                        'en la ruta general dónde se encuentran los insumos.')

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

# Geoformas indicativas 
GeoformasIndicativas, ok = QInputDialog.getItem(None, "Geoformas indicativas de procesos tipo flujo",
                                           "Seleccione el archivo de las geoformas indicativas de procesos tipo flujo", csv, 0, False)
if ok == False:
    raise Exception('Cancelar')

#Asiganción de valor según SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS
#Geoformas indicativas de proceso tipo flujo
FILE_NAME = data_path + '/' + GeoformasIndicativas
DF_GeoformasIndicativas = pd.read_csv(FILE_NAME, delimiter=";",encoding='latin-1')
# Se extraen solo los tres primeros caracteres del acronimo teniendo en cuenta que las coincidencias no son exactas
DF_GeoformasIndicativas['CODIGO'] = DF_GeoformasIndicativas['ACRONIMO'].astype(str).str[0:3]

#Geoformas existentes en la capa
FILE_NAME = data_path + '/Pre_Proceso/DF_Raster_SubunidadesGeomorf.csv'
DF_SubunidadesGeoform = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
DF_SubunidadesGeoform.drop(['index'],axis='columns',inplace=True)
# Se extraen solo los tres primeros caracteres del acronimo teniendo en cuenta que las coincidencias no son exactas
DF_SubunidadesGeoform['Caract_3'] = DF_SubunidadesGeoform['Caract'].astype(str).str[0:3]

# Se listaran las geoformas no encontradas en la base de datos
Geoformas_NaN = []

# Se recorren las subunidades presentes en la capa de análisis
for i in range(0, len(DF_SubunidadesGeoform)): 
    
    # Se determina la subunidad en cuestión
    Subunidad = DF_SubunidadesGeoform.loc[i, 'Caract']
    # Se determinan las primer tres letras del acrononimo 
    # debido a que puede que no haya coincidencias exactas
    Caract = DF_SubunidadesGeoform.loc[i, 'Caract_3']
    
    # Se determina si la subunidad se encuentra en la lista de geomorfas indicativas
    if len(DF_GeoformasIndicativas[DF_GeoformasIndicativas['CODIGO'].isin([Caract])])== 0:
        # Si la longitud de la busqueda es 0 la geoforma no se encuentra y se le asigna susceptibilidad baja
        DF_SubunidadesGeoform.loc[i, 'Valor'] = 0
        Geoformas_NaN.append(Subunidad)
        DF_SubunidadesGeoform.loc[i, 'Base_datos'] = "No encontrado"
    
    else:
        # Si se encuentra puede ser que se encuentre varias veces 
        # debido a que solo se busca la coincidencia de las tres primeras letras del acronimo
        if len(DF_GeoformasIndicativas[DF_GeoformasIndicativas['CODIGO'].isin([Caract])])> 1:
            # Si la longitud es diferente de 0 se pondrá como indice la columna del acronimo
            DF_GeoformasIndicativas.set_index('CODIGO', inplace=True)
            # Se extrae el valor del índice cero
            Valor = DF_GeoformasIndicativas.loc[Caract]['VALOR'][0]
        else:
            # Si la longitud es diferente de 0 se pondrá como indice la columna del acronimo
            DF_GeoformasIndicativas.set_index('CODIGO', inplace=True)
            #Se extrae el valor único que se encuentra
            Valor = DF_GeoformasIndicativas.loc[Caract]['VALOR']
        
        # Se verifica que valor fue el que se encontró
        
        if Valor == np.nan:
            # Si se encuentra un valor pero este es NaN también se asigna susceptibilidad baja
            DF_SubunidadesGeoform.loc[i, 'Valor'] = 0
            DF_SubunidadesGeoform.loc[i, 'Base_datos'] = "No encontrado"
            Geoformas_NaN.append(Subunidad)
        
        else:
            # Si el valor encontrado era correcto se asigna 
            DF_SubunidadesGeoform.loc[i,'Valor'] = Valor
            DF_SubunidadesGeoform.loc[i, 'Base_datos'] = "Encontrado"
        
        # Se devuelve al indice númerico para continuar con el for
        DF_GeoformasIndicativas.reset_index(level=0, inplace=True)

# Se imprimen las subunidades no encontradas
print('No se encontraró la categoría de susceptibilidad para las siguientes subunidades geomorfologicas')
print(Geoformas_NaN)

# Se imprimen las categorías finales asignadas
print('Subunidades geomorfologicas encontradas en el área de estudio: ')
print(DF_SubunidadesGeoform)
DF_SubunidadesGeoform.reset_index().to_csv(data_path+'/Pre_Proceso/DF_RasterFlujo_SubunidadesGeoform.csv',header=True,index=False)

# Se verifica si el usuario está de acuerdo con las categorías de susceptibilidad
QMessageBox.information(iface.mainWindow(), "Categorías de susceptibilidad según las subunidades geomorfologicas",
                        f'Las siguientes subunidades geomorfologicas no fueron encontradas en la base de datos: {Geoformas_NaN}, '
                        'por lo que se le asignaron la categoría de susceptibilidad BAJA. '
                        'Si desea hacer algun ajuste vaya a la carpeta de Pre_Proceso y busque el archivo "DF_RasterFlujo_SubunidadesGeoform.csv" '
                        'dónde puede cambiar en la columna "Valor" la categoría de susceptibilidad teniendo en cuenta que 0: Baja, 1: Media y 2: Alta, '
                        'haga el ajuste y guarde ANTES de dar "Aceptar", si está de acuerdo con las categorías puede continuar')

#Reclasificación del raster con el valor de Susceptibilidad correspondiente.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path + '/Pre_Proceso/SubunidadesGeomorf.tif'
DF_SubunidadesGeomorf = data_path+'/Pre_Proceso/DF_RasterFlujo_SubunidadesGeoform.csv'
Susceptibilidad_Flujo = data_path + '/Resultados/Susceptibilidad_Flujo.tif'
params={'INPUT_RASTER': Factor_Condicionante, 'RASTER_BAND': 1, 'INPUT_TABLE': DF_SubunidadesGeomorf, 'MIN_FIELD': 'ID',
        'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Valor', 'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,
        'OUTPUT': Susceptibilidad_Flujo}
processing.run(alg,params)

Susceptibilidad_Flujo = QgsRasterLayer(Susceptibilidad_Flujo,"Susceptibilidad_Flujo")
QgsProject.instance().addMapLayer(Susceptibilidad_Flujo)

# Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)