from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant
from qgis.gui import QgsMessageBar
from qgis.core import QgsProject
from osgeo import gdal_array
from os import listdir
import pandas as pd
import numpy as np
import processing
import os

# Ruta general de la ubicación de los archivos relativa a la ubicación del programa
data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
data_path = data_path[0]
data_path = data_path.replace("\\", "/")

def Wf(factor, Deslizamientos):
    
    #Lectura del raster del factor condicionante
    rasterfile = data_path + f'/Pre_Proceso/{factor}.tif'
    
    #Análisis de deslizamientos si su geometria es puntos
    if Deslizamientos.wkbType()== QgsWkbTypes.Point:
        # Obtenermos el id de la caracteristica del punto de deslizamiento
        alg = "qgis:rastersampling"
        output = data_path + f'/Pre_Proceso/Valores{factor}.shp'
        params = {'INPUT': Deslizamientos, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Id_Condici', 'OUTPUT': output}
        processing.run(alg, params)
        ValoresRaster = QgsVectorLayer(data_path + f'/Pre_Proceso/Valores{factor}.shp', f'Valores{factor}')
    
    #Análisis de deslizamientos si su geometria es poligonos
    else:
        #Interesección de el factor condicionante con el área de deslizamientos
        alg = "gdal:cliprasterbymasklayer"
        Deslizamiento_Condicion = data_path + f'/Pre_Proceso/Deslizamientos{factor}.tif'
        params = {'INPUT': rasterfile, 'MASK': Deslizamientos, 'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:3116'),
        'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3116'), 'NODATA': None, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True,
        'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False,
        'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '', 'OUTPUT': Deslizamiento_Condicion}
        processing.run(alg, params)
        
        #Estadísticas zonales (número de pixeles por atributo por deslizamiento)
        alg = "native:rasterlayerzonalstats"
        Estadisticas_Deslizamiento = data_path + f'/Pre_Proceso/Deslizamientos{factor}Estadistica.csv'
        params = {'INPUT': Deslizamiento_Condicion, 'BAND': 1, 'ZONES': Deslizamiento_Condicion, 'ZONES_BAND': 1,
                  'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Deslizamiento}
        processing.run(alg, params)
        
        #Lectura de las estadísticas de la zona de deslizamientos como dataframe
        Estadisticas_Deslizamiento = data_path + f'/Pre_Proceso/Deslizamientos{factor}Estadistica.csv'
        DF_DeslizamientosEstadistica = pd.read_csv(Estadisticas_Deslizamiento, delimiter=",",encoding='latin-1')
    
    # Estadísticas zonales del raster del factor condicionante (número de pixeles por atributo total)
    alg = "native:rasterlayerzonalstats"
    Estadisticas_Condicionante = data_path + f'/Pre_Proceso/{factor}Estadistica.csv'
    params = {'INPUT': rasterfile, 'BAND': 1, 'ZONES': rasterfile,
              'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Condicionante}
    processing.run(alg, params)
    
    # Lectura de las estadísticas de toda la zona como dataframe
    Estadisticas_Condicionante = data_path + f'/Pre_Proceso/{factor}Estadistica.csv'
    DF_Estadistica = pd.read_csv(Estadisticas_Condicionante, encoding='latin-1')
    # Valores únicos del factor condicionante
    atributos = DF_Estadistica["zone"].unique()
    Factor_ID = pd.DataFrame(atributos)
    Factor_ID = Factor_ID.sort_values(by = 0)
    atributos = Factor_ID[0].tolist()
    Valor_Max = max(atributos)
    Valor_Min =  min(atributos)
    atributos.append(Valor_Max + 1)
    
    if factor == 'CurvaturaPlano':
        rasterArray = gdal_array.LoadFile(rasterfile)
        rasterList = rasterArray.tolist()
        
        flat_list = []
        for sublist in rasterList:
            for item in sublist:
                flat_list.append(item)
                
        df = pd.DataFrame(flat_list)
        df = df.drop(df[df[0] < Valor_Min].index)
        df = df.drop(df[df[0] > Valor_Max].index)
        
        n_percentil = [0, 25, 50, 75, 100]
        
        percentiles = [np.percentile(df[0], 0)-0.001]
        for i in range(1, len(n_percentil)-1):
            Valor = np.percentile(df[0], n_percentil[i])
            percentiles.append(Valor)
        percentiles.append(np.percentile(df[0], 100)+0.001)
        
    # Creación del dataFrame
    DF_Susceptibilidad = pd.DataFrame(columns = ['Min', 'Max', 'Mov', 'CLASE', 'Npix1', 'Npix2', 'Npix3', 'Npix4', 'Wi+', 'Wi-', 'Wf'], dtype = float)
        
    if factor == 'CurvaturaPlano':
        ciclo = percentiles
    elif factor == 'Pendiente':
        ciclo = [0, 2, 4, 8, 16, 35, 55, 90]
    else:
        ciclo = atributos
    
    # ##Se llena el dataframe con los valores correspondientes###
    for i in range(0, len(ciclo) - 1):
        # Se le asigna su id a cada atributo
        Min = ciclo[i]
        Max = ciclo[i+1]
        DF_Susceptibilidad.loc[i, 'Min'] = Min
        DF_Susceptibilidad.loc[i, 'Max'] = Max
        # Se determina el número de pixeles en la clase
        DF_Susceptibilidad.loc[i, 'CLASE'] = DF_Estadistica.loc[(DF_Estadistica['zone'] >= Min) & (DF_Estadistica['zone'] < Max)]['count'].sum()
        # Se determina el número de pixeles con movimientos en masa en la clase
        if Deslizamientos.wkbType()== QgsWkbTypes.Point:
            ValoresRaster.selectByExpression(f'"Id_Condici" < \'{Max}\' and "Id_Condici" >= \'{Min}\'', QgsVectorLayer.SetSelection)
            selected_fid = []
            selection = ValoresRaster.selectedFeatures()
            DF_Susceptibilidad.loc[i, 'Mov'] = len(selection)
        else:
            DF_Susceptibilidad.loc[i,'Mov'] = DF_DeslizamientosEstadistica.loc[(DF_DeslizamientosEstadistica['zone'] >= Min) 
                                        & (DF_DeslizamientosEstadistica['zone'] < Max)]['count'].sum()
        
        # Si el número de pixeles es el mismo se hace una corrección para evitar que de infinito
        if DF_Susceptibilidad.loc[i, 'Mov'] == DF_Susceptibilidad.loc[i, 'CLASE']:
            DF_Susceptibilidad.loc[i, 'CLASE'] = DF_Susceptibilidad.loc[i, 'CLASE'] + 1
            iface.messageBar().pushMessage("Factor condicionante", f'Revisar el factor condicionante {factor}', Qgis.Warning, 5)
            
    Sum_Mov = DF_Susceptibilidad['Mov'].sum()
    Sum_Clase = DF_Susceptibilidad['CLASE'].sum()
    
    # ##Aplicación del método a partir de los valores anteriores###
    for i in range(0, len(ciclo) - 1):
        DF_Susceptibilidad.loc[i, 'Npix1'] = DF_Susceptibilidad.loc[i, 'Mov']
        DF_Susceptibilidad.loc[i, 'Npix2'] = Sum_Mov-DF_Susceptibilidad.loc[i, 'Mov']
        DF_Susceptibilidad.loc[i, 'Npix3'] = DF_Susceptibilidad.loc[i, 'CLASE'] - DF_Susceptibilidad.loc[i, 'Mov']
        DF_Susceptibilidad.loc[i, 'Npix4'] = Sum_Clase - DF_Susceptibilidad.loc[i, 'CLASE'] - (Sum_Mov - DF_Susceptibilidad.loc[i, 'Npix1'])
        
        DF_Susceptibilidad.loc[i, 'Wi+'] = np.log((DF_Susceptibilidad.loc[i, 'Npix1']/(DF_Susceptibilidad.loc[i, 'Npix1'] + DF_Susceptibilidad.loc[i, 'Npix2']))/(DF_Susceptibilidad.loc[i, 'Npix3']/(DF_Susceptibilidad.loc[i, 'Npix3']+DF_Susceptibilidad.loc[i, 'Npix4'])))
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
        DF_Susceptibilidad.loc[i, 'Wf'] = DF_Susceptibilidad.loc[i, 'Wi+'] - DF_Susceptibilidad.loc[i, 'Wi-']
    
    if (factor == 'UGS' or factor == 'SubunidadesGeomorf' or factor == 'CoberturaUso' or factor == 'CambioCobertura'):
        DF_Susceptibilidad = DF_Susceptibilidad.drop(['Max'], axis=1)
        DF_Susceptibilidad = DF_Susceptibilidad.rename(columns={'Min':'ID'})
        
    print(f'Los valores de Wf para {factor} es: ')
    print(DF_Susceptibilidad)
    DF_Susceptibilidad.reset_index().to_csv(data_path + f'/Pre_Proceso/DF_Susceptibilidad_{factor}.csv', header = True, index = False)
    
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
    Susceptibilidad_Condicionante = data_path + f'/Pre_Proceso/DF_Susceptibilidad_{factor}.csv'
    Condicionante_Reclass = data_path + f'/Resultados/Wf_{factor}.tif'
    params = {'INPUT_RASTER': rasterfile, 'RASTER_BAND': 1, 'INPUT_TABLE': Susceptibilidad_Condicionante,
              'MIN_FIELD': MIN_FIELD, 'MAX_FIELD': MAX_FIELD, 'VALUE_FIELD': 'Wf', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': RANGE_BOUNDARIES,
              'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5, 'OUTPUT': Condicionante_Reclass}
    processing.run(alg, params)
    
    iface.addRasterLayer(data_path + f'/Resultados/Wf_{factor}.tif', f"Wf_{factor}")

# Se lee el archivo correspondientes a deslizamientos
Deslizamientos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos.shp')

Factor_Condicionante = ['UGS', 'SubunidadesGeomorf', 'CoberturaUso', 'CambioCobertura', 'Pendiente', 'CurvaturaPlano']

for factor in (Factor_Condicionante):
    ruta = data_path + f'/Pre_Proceso/{factor}.tif'
    
    if os.path.isfile(ruta) is False:
        continue
    
    Wf(factor, Deslizamientos)





