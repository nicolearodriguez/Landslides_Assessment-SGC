"""
@author: Nicole Alejadra Rodríguez Vargas
@mail: nicole.rodriguez@correo.uis.edu.co
"""

"""
En esta programación se desarrollan la metodología WofE en dónde se le asigna un peso final
de evidencia a cada una de las características del factor doncionante según la importancia
respecto a la ocurrencia de un deslizamiento.
"""

from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant
from qgis.gui import QgsMessageBar
from qgis.core import QgsProject
from osgeo import gdal_array
from PyQt5 import QtGui
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

# Se determinan los archivos con extensión .tif en la ruta
raster = []
for i in list:
    if i[-4:] == '.tif':
        raster.append(i)
raster.append('None')

#Se imprime una recomendación
QMessageBox.information(iface.mainWindow(), "!Tenga en cuenta!",
                        'Se recomienda que si ya se ha ejecutado el programa con anterioridad sean borrados los archivos '
                        'que este genera para evitar conflictos al reemplazar los archivos pre-existentes en especial los .shp')

# ############################ SE PLANTEA LA FUNCIÓN DEL MÉTODO ESTADÍSTICO BIVARIADO ############################ #

#Se define la función Wf para determinar los pesos finales del factor condicionate
def Wf(factor, Deslizamientos):
        
    # Análisis de deslizamientos si su geometria es puntos
    if Deslizamientos.wkbType()== QgsWkbTypes.Point:
        # Se muestrea el id de la caracteristica del factor condicionante en el punto de deslizamiento
        alg = "qgis:rastersampling"
        output = data_path + f'/Curva_Validacion/Valores{factor}.shp'
        params = {'INPUT': Deslizamientos, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Id_Condici', 'OUTPUT': output}
        processing.run(alg, params)
        ValoresRaster = QgsVectorLayer(data_path + f'/Curva_Validacion/Valores{factor}.shp', f'Valores{factor}')
    
    else:
        # Análisis de deslizamientos si su geometria es poligonos
        # Interesección de el factor condicionante con el área de deslizamientos
        alg = "gdal:cliprasterbymasklayer"
        Deslizamiento_Condicion = data_path + f'/Curva_Validacion/Deslizamientos{factor}.tif'
        params = {'INPUT': rasterfile, 'MASK': Deslizamientos, 'SOURCE_CRS': None,
                  'TARGET_CRS': None, 'NODATA': None, 'ALPHA_BAND': False,
                  'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None,
                  'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '',
                  'OUTPUT': Deslizamiento_Condicion}
        processing.run(alg, params)
        
        # Estadísticas zonales (número de pixeles por atributo por deslizamiento)
        alg = "native:rasterlayerzonalstats"
        Estadisticas_Deslizamiento = data_path + f'/Curva_Validacion/Deslizamientos{factor}Estadistica.csv'
        params = {'INPUT': Deslizamiento_Condicion, 'BAND': 1, 'ZONES': Deslizamiento_Condicion,
                  'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Deslizamiento}
        processing.run(alg, params)
        
        # Lectura de las estadísticas de la zona de deslizamientos como dataframe
        Estadisticas_Deslizamiento = data_path + f'/Curva_Validacion/Deslizamientos{factor}Estadistica.csv'
        DF_DeslizamientosEstadistica = pd.read_csv(Estadisticas_Deslizamiento, delimiter=",",encoding='latin-1')
    
    # Estadísticas zonales del raster del factor condicionante (número de pixeles por atributo total)
    alg = "native:rasterlayerzonalstats"
    Estadisticas_Condicionante = data_path + f'/Curva_Validacion/{factor}Estadistica.csv'
    params = {'INPUT': rasterfile, 'BAND': 1, 'ZONES': rasterfile,
              'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Condicionante}
    processing.run(alg, params)
    
    # Lectura de las estadísticas de toda la zona como dataframe
    Estadisticas_Condicionante = data_path + f'/Curva_Validacion/{factor}Estadistica.csv'
    DF_Estadistica = pd.read_csv(Estadisticas_Condicionante, encoding='latin-1')
    
    # Valores únicos del factor condicionante
    atributos = DF_Estadistica["zone"].unique()
    Factor_ID = pd.DataFrame(atributos)
    Factor_ID = Factor_ID.sort_values(by = 0)
    atributos = Factor_ID[0].tolist()
    Valor_Max = max(atributos)
    Valor_Min =  min(atributos)
    atributos.append(Valor_Max + 1)
    
    # Si el factor condicionante es la curvatura se maneja por percentiles
    if factor == 'CurvaturaPlano':
        # Se hace un arreglo con los pixeles del raster de curvatura
        rasterArray = gdal_array.LoadFile(rasterfile)
        rasterList = rasterArray.tolist()
        
        # La lista de listas de la matriz se pasan a una sola lista item por item
        flat_list = []
        for sublist in rasterList:
            for item in sublist:
                flat_list.append(item)
        
        # Se eliminan los valores que se usaron para completar el arreglo 
        # pero que no corresponden a valores de curvatura
        df = pd.DataFrame(flat_list)
        df = df.drop(df[df[0] < Valor_Min].index)
        df = df.drop(df[df[0] > Valor_Max].index)
        
        # Se determinan los rangos de percentiles
        n_percentil = [0, 25, 50, 75, 100]
        
        # Se cálcula el primer percentil y se le resta una milesima de forma que sea tenido en cuenta
        percentiles = [np.percentile(df[0], 0)-0.001]
        
        # Se calculan los percentiles para los porcentajes internos
        for i in range(1, len(n_percentil)-1):
            Valor = np.percentile(df[0], n_percentil[i])
            percentiles.append(Valor)
        
        # Se cálcula el último percentil y se le suma una milesima de forma que sea tenido en cuenta
        percentiles.append(np.percentile(df[0], 100)+0.001)
        
    # Creación del dataFrame para llenarlo con el método estadístico
    DF_Susceptibilidad = pd.DataFrame(columns = ['Min', 'Max', 'Mov', 'CLASE', 'Npix1', 'Npix2',
                                                 'Npix3', 'Npix4', 'Wi+', 'Wi-', 'Wf'], dtype = float)
       
    # Dependiendo del factor condicionante se definen los rangos
    # en los que se lleva a cabo el procedimiento
    if factor == 'CurvaturaPlano':
        ciclo = percentiles
    elif factor == 'Pendiente':
        ciclo = [0, 2, 4, 8, 16, 35, 55, 1000]
    else:
        ciclo = atributos
    
    # ##Se llena el dataframe con los valores correspondientes## #
    for i in range(0, len(ciclo) - 1):
        # Se le asigna su mínimo y máximo a cada rango
        Min = ciclo[i]
        Max = ciclo[i+1]
        DF_Susceptibilidad.loc[i, 'Min'] = Min
        DF_Susceptibilidad.loc[i, 'Max'] = Max
        # Se determina el número de pixeles en la clase
        DF_Susceptibilidad.loc[i, 'CLASE'] = DF_Estadistica.loc[(DF_Estadistica['zone'] >= Min) & (DF_Estadistica['zone'] < Max)]['count'].sum()
        # Se determina el número de pixeles de deslizamientos en la clase
        # Si los deslizamientos tienen geometría de puntos
        if Deslizamientos.wkbType()== QgsWkbTypes.Point:
            ValoresRaster.selectByExpression(f'"Id_Condici" < \'{Max}\' and "Id_Condici" >= \'{Min}\'', QgsVectorLayer.SetSelection)
            selected_fid = []
            selection = ValoresRaster.selectedFeatures()
            DF_Susceptibilidad.loc[i, 'Mov'] = len(selection)
        else:
            # Si los deslizamientos tienen geometría de poligonos
            DF_Susceptibilidad.loc[i,'Mov'] = DF_DeslizamientosEstadistica.loc[(DF_DeslizamientosEstadistica['zone'] >= Min) 
                                        & (DF_DeslizamientosEstadistica['zone'] < Max)]['count'].sum()
        
        # Si el número de pixeles es el mismo se hace una corrección para evitar que de infinito
        if DF_Susceptibilidad.loc[i, 'Mov'] == DF_Susceptibilidad.loc[i, 'CLASE']:
            DF_Susceptibilidad.loc[i, 'CLASE'] = DF_Susceptibilidad.loc[i, 'CLASE'] + 1
            iface.messageBar().pushMessage("Factor condicionante", f'Revisar el factor condicionante {factor}', Qgis.Warning, 5)
            
    # Se obtienen el número total de pixeles en clase y en movimiento
    Sum_Mov = DF_Susceptibilidad['Mov'].sum()
    Sum_Clase = DF_Susceptibilidad['CLASE'].sum()
    
    # ##Aplicación del método a partir de los valores anteriores## #
    for i in range(0, len(ciclo) - 1):
        # Se cálculan los Npix
        DF_Susceptibilidad.loc[i, 'Npix1'] = DF_Susceptibilidad.loc[i, 'Mov']
        DF_Susceptibilidad.loc[i, 'Npix2'] = Sum_Mov-DF_Susceptibilidad.loc[i, 'Mov']
        DF_Susceptibilidad.loc[i, 'Npix3'] = DF_Susceptibilidad.loc[i, 'CLASE'] - DF_Susceptibilidad.loc[i, 'Mov']
        DF_Susceptibilidad.loc[i, 'Npix4'] = Sum_Clase - DF_Susceptibilidad.loc[i, 'CLASE'] - (Sum_Mov - DF_Susceptibilidad.loc[i, 'Npix1'])
        
        # A partir de los Npix se cálcula el peso positivo
        DF_Susceptibilidad.loc[i, 'Wi+'] = np.log((DF_Susceptibilidad.loc[i, 'Npix1']/(DF_Susceptibilidad.loc[i, 'Npix1'] + DF_Susceptibilidad.loc[i, 'Npix2']))/(DF_Susceptibilidad.loc[i, 'Npix3']/(DF_Susceptibilidad.loc[i, 'Npix3']+DF_Susceptibilidad.loc[i, 'Npix4'])))
        
        # Si el peso positivo no da algún valor será 0.
        if DF_Susceptibilidad.loc[i, 'Wi+'] == np.inf:
            DF_Susceptibilidad.loc[i, 'Wi+'] = 0
        elif DF_Susceptibilidad.loc[i, 'Wi+'] == -np.inf:
            DF_Susceptibilidad.loc[i, 'Wi+'] = 0
        elif math.isnan(DF_Susceptibilidad.loc[i, 'Wi+']) is True:
            DF_Susceptibilidad.loc[i, 'Wi+'] = 0
        
        # A partir de los Npix se cálcula el peso negativo
        DF_Susceptibilidad.loc[i, 'Wi-'] = np.log((DF_Susceptibilidad.loc[i, 'Npix2']/(DF_Susceptibilidad.loc[i, 'Npix1']+DF_Susceptibilidad.loc[i, 'Npix2']))/(DF_Susceptibilidad.loc[i, 'Npix4']/(DF_Susceptibilidad.loc[i, 'Npix3']+DF_Susceptibilidad.loc[i, 'Npix4'])))
        
        # Si el peso negativo no da algún valor será 0.
        if DF_Susceptibilidad.loc[i, 'Wi-'] == np.inf:
            DF_Susceptibilidad.loc[i, 'Wi-'] = 0
        elif DF_Susceptibilidad.loc[i, 'Wi-'] == -np.inf:
            DF_Susceptibilidad.loc[i, 'Wi-'] = 0
        elif math.isnan(DF_Susceptibilidad.loc[i, 'Wi-']) is True:
            DF_Susceptibilidad.loc[i, 'Wi-'] = 0
        DF_Susceptibilidad.loc[i, 'Wf'] = DF_Susceptibilidad.loc[i, 'Wi+'] - DF_Susceptibilidad.loc[i, 'Wi-']
    
    # Si el factor condicionante es una variable continua realmente se trabaja con el ID del campo Min y no se tiene en cuenta el Máx
    if (factor == 'UGS' or factor == 'SubunidadesGeomorf' or factor == 'CoberturaUso' or factor == 'CambioCobertura'):
        DF_Susceptibilidad = DF_Susceptibilidad.drop(['Max'], axis=1)
        DF_Susceptibilidad = DF_Susceptibilidad.rename(columns={'Min':'ID'})
        
    # Se imprime y se guarda el dataframe de pesos finales para el factor condicionante
    print(f'Los valores de Wf para {factor} es: ')
    print(DF_Susceptibilidad)
    DF_Susceptibilidad.reset_index().to_csv(data_path + f'/Curva_Validacion/DF_Susceptibilidad_{factor}.csv', header = True, index = False)
    
    # Teniendo en cuenta el tipo de factor condicionante se definen los datos para reclasificar la capa
    if factor == 'CurvaturaPlano' or factor == 'Pendiente':
        MAX_FIELD = 'Max'
        MIN_FIELD = 'Min'
        RANGE_BOUNDARIES = 1
    else:
        MAX_FIELD = 'ID'
        MIN_FIELD = 'ID'
        RANGE_BOUNDARIES = 2
        
    # Reclasificación del raster del factor condicionante con el Wf correspondiente al atributo.
    alg = "native:reclassifybylayer"
    Susceptibilidad_Condicionante = data_path + f'/Curva_Validacion/DF_Susceptibilidad_{factor}.csv'
    Condicionante_Reclass = data_path + f'/Curva_Validacion/Wf_{factor}.tif'
    params = {'INPUT_RASTER': rasterfile, 'RASTER_BAND': 1, 'INPUT_TABLE': Susceptibilidad_Condicionante,
              'MIN_FIELD': MIN_FIELD, 'MAX_FIELD': MAX_FIELD, 'VALUE_FIELD': 'Wf', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': RANGE_BOUNDARIES,
              'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5, 'OUTPUT': Condicionante_Reclass}
    processing.run(alg, params)
    
    # Se añade la capa reclasificada con los Wf al lienzo
    iface.addRasterLayer(data_path + f'/Curva_Validacion/Wf_{factor}.tif', f"Wf_{factor}")

# ############################ SE APLICA EL MÉTODO EN LOS FACTORES CONDICIONANTES DISCRETOS ############################ #

# Se lee el archivo correspondientes a deslizamientos
Deslizamientos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos_Validacion.shp')

# Se listan los factores condicionantes discretos
Factor_Condicionante = ['UGS', 'SubunidadesGeomorf', 'CoberturaUso', 'CambioCobertura']

# Se recorre la lista de factores condicionantes
for factor in (Factor_Condicionante):
    # Se determina la posible ruta del factor condicionante
    ruta = data_path + f'/Pre_Proceso/{factor}.tif'
    
    # Si el archivo no existe se continua 
    if os.path.isfile(ruta) is False:
        continue
    # Se aplica la función del peso al factor condicionante
    
    #Lectura del raster del factor condicionante
    rasterfile = data_path + f'/Pre_Proceso/{factor}.tif'
    Wf(factor, Deslizamientos)

# ############################ SE APLICA EL MÉTODO EN LOS FACTORES CONDICIONANTES CONTINUOS ############################ #

# Se listan los factores condicionantes continuos
Factor_Condicionante = ['Pendiente', 'CurvaturaPlano']

# Se recorre la lista de factores condicionantes
for factor in (Factor_Condicionante):
    # Se determina la posible ruta del factor condicionante    
    Ruta_Factor, ok = QInputDialog.getItem(None, f"{factor}",
                                       f"Seleccione el archivo de {factor}",
                                       raster, 0, False)
    if ok == False:
        raise Exception('Cancelar')
    ruta = data_path + '/' + Ruta_Factor
    
    # Si el archivo no existe se continua 
    if os.path.isfile(ruta) is False:
        continue
    # Se aplica la función del peso al factor condicionante
    rasterfile = data_path + '/' + Ruta_Factor
    Wf(factor, Deslizamientos)

# Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)