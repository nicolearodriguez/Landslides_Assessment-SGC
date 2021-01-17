"""
@author: Nicole Alejadra Rodríguez Vargas
@mail: nicole.rodriguez@correo.uis.edu.co
"""

"""
En esta programación se caracteriza la susceptibilidad por movimientos en masa tipo caída,
esta caracterización se hace con base en la pendiente, las UGS y las subunidades indicativas
del proceso tipo caída, además, se tienen en cuenta los eventos ocurridos anteriormente cómo
depositos para así completar la caracterización de la susceptibilidad.
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
                        'con las geoformas indicativas de procesos tipo caída '
                        '(GeoformasIndicativasProcesoTipoCaida.csv) y este guardada '
                        'en la ruta general dónde se encuentran los insumos.')

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

# Se determinan los archivos con extensión .shp en la ruta
shape = []
for i in list:
    if i[-4:] == '.shp':
        shape.append(i)
shape.append('None')

# Zonas de depósito
Zona_Deposito, ok = QInputDialog.getItem(None, "Zonas de deposito MM caídas",
                                           "Seleccione el archivo de las zonas de depósito de los MM tipo caída", shape, 0, False)
if ok == False:
    raise Exception('Cancelar')
Ruta_Zona_Deposito = data_path + '/' + Zona_Deposito

# Se determinan los archivos con extensión .csv en la ruta
csv = []
for i in list:
    if i[-4:] == '.csv':
        csv.append(i)

# Geoformas indicativas 
GeoformasIndicativas, ok = QInputDialog.getItem(None, "Geoformas indicativas de procesos tipo caída",
                                           "Seleccione el archivo de las geoformas indicativas de procesos tipo caída", csv, 0, False)
if ok == False:
    raise Exception('Cancelar')

# Pendiente umbral
slope, ok = QInputDialog.getInt(None, 'Pendiente Umbral',
                            'Se recomienda como umbral mínimo la inclinación del terreno igual '
                            'o superior a 45°. Sin embargo, puede introducir la pendiente que considere apropiada para la zona de estudio: ')
if ok == False:
    raise Exception('Cancelar')

# #######################Zonificación de Susceptibilidad por zonas de inicio tipo Caida####################### #

# Se determina la ruta de la pendiente
Pendiente, ok = QInputDialog.getItem(None, f"Pendiente",
                                   f"Seleccione el archivo de pendiente",
                                   raster, 0, False)
if ok == False:
    raise Exception('Cancelar')

#Se reclasifica teniendo en cuenta que 0 serán las pendientes menores a 45, y serán 1 las pendientes mayores a 45.
alg="native:reclassifybytable"
Pendientes = data_path + '/' + Pendiente
Suscep_Caida_Pendiente = data_path+'/Pre_Proceso/Suscep_Caida_Pendiente.tif'
table = [0, slope, 0, slope, 100, 5]  # [min1, max1, valor1, min2, max2, valor2]  min<valor<=max
params = {'INPUT_RASTER': Pendientes,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 0,
          'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Suscep_Caida_Pendiente}
processing.run(alg, params)

# Asiganción de valor según SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS

# Geoformas indicativas de proceso tipo caida
FILE_NAME = data_path + '/' + GeoformasIndicativas
DF_GeoformasIndicativas = pd.read_csv(FILE_NAME, delimiter = ";", encoding = 'latin-1')
# Se extraen solo los tres primeros caracteres del acronimo teniendo en cuenta que las coincidencias no son exactas
DF_GeoformasIndicativas['CODIGO'] = DF_GeoformasIndicativas['ACRONIMO'].astype(str).str[0:3]

# Geoformas existentes en la capa
FILE_NAME = data_path + '/Pre_Proceso/DF_Raster_SubunidadesGeomorf.csv'
DF_SubunidadesGeoform = pd.read_csv(FILE_NAME, delimiter = ",", encoding = 'latin-1')
DF_SubunidadesGeoform.drop(['index'], axis = 'columns', inplace = True)
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

# Se eliminan las columnas no necesarias en el análisis
DF_SubunidadesGeoform = DF_SubunidadesGeoform.drop(['General'], axis=1)
DF_SubunidadesGeoform = DF_SubunidadesGeoform.drop(['Caract_3'], axis=1)
# Se imprimen las categorías finales asignadas
print('Subunidades geomorfologicas encontradas en el área de estudio: ')
print(DF_SubunidadesGeoform)
DF_SubunidadesGeoform.reset_index().to_csv(data_path + '/Pre_Proceso/DF_RasterCaida_SubunidadesGeoform.csv', header = True, index = False)

# Se verifica si el usuario está de acuerdo con las categorías de susceptibilidad
QMessageBox.information(iface.mainWindow(), "Categorías de susceptibilidad según las subunidades geomorfologicas",
                        f'Las siguientes subunidades geomorfologicas no fueron encontradas en la base de datos: {Geoformas_NaN}, '
                        'por lo que se le asignaron la categoría de susceptibilidad BAJA. '
                        'Si desea hacer algun ajuste vaya a la carpeta de Pre_Proceso y busque el archivo "DF_RasterCaida_SubunidadesGeoform.csv" '
                        'dónde puede cambiar en la columna "Valor" la categoría de susceptibilidad teniendo en cuenta que 0: Baja, 1: Media y 2: Alta, '
                        'haga el ajuste y guarde ANTES de dar "Aceptar", si está de acuerdo con las categorías puede continuar')

#Reclasificación del raster con el valor de Susceptibilidad correspondiente a SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path + '/Pre_Proceso/SubunidadesGeomorf.tif'
DF_SubunidadesGeomorf = data_path + '/Pre_Proceso/DF_RasterCaida_SubunidadesGeoform.csv'
Suscep_Caida_SubunidadesGeomorf = data_path + '/Pre_Proceso/Suscep_Caida_SubunidadesGeomorf.tif'
params={'INPUT_RASTER': Factor_Condicionante, 'RASTER_BAND': 1,'INPUT_TABLE': DF_SubunidadesGeomorf, 'MIN_FIELD': 'ID',
        'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Valor', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2, 'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5,
        'OUTPUT': Suscep_Caida_SubunidadesGeomorf}
processing.run(alg, params)

#Asignación de valor según TIPO DE ROCA
#UGS de la zona
FILE_NAME = data_path + '/Pre_Proceso/DF_Raster_UGS.csv'
DF_UGS = pd.read_csv(FILE_NAME, delimiter = ",", encoding = 'latin-1')
DF_UGS.drop(['index'], axis = 'columns', inplace = True)
#Se asigna un valor de susceptibilidad dependiendo del tipo de roca
for i in range (0,len(DF_UGS)):
    General=DF_UGS.loc[i,'General']
    if General == 'Rb': #Roca blanda
        DF_UGS.loc[i,'Valor']= 5
    elif General == 'Ri': #Roca intermedia
        DF_UGS.loc[i,'Valor']= 2
    else:  ##Roca dura y suelos
        DF_UGS.loc[i,'Valor']= 0

print('Unidades geologicas superficiales encontradas en el área de estudio: ')
print(DF_UGS)
DF_UGS.reset_index().to_csv(data_path + '/Pre_Proceso/DF_Raster_UGS.csv', header = True, index = False)

QMessageBox.information(iface.mainWindow(), "Categorías de susceptibilidad según las UGS",
                        f'Las UGS fueron caracterizadas según el DataFrame impreso'
                        'Si desea hacer algun ajuste vaya a la carpeta de Pre_Proceso y busque el archivo "DF_Raster_UGS.csv" '
                        'dónde puede cambiar en la columna "Valor" la categoría de susceptibilidad teniendo en cuenta que 0: Baja, 2: Media y 5: Alta, '
                        'haga el ajuste y guarde ANTES de dar "Aceptar", si está de acuerdo con las categorías puede continuar')

# Reclasificación del raster con el valor de Susceptibilidad correspondiente al TIPO DE ROCA.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path + '/Pre_Proceso/UGS.tif'
DF_UGS = data_path + '/Pre_Proceso/DF_Raster_UGS.csv'
Suscep_Caida_UGS = data_path + '/Pre_Proceso/Suscep_Caida_UGS.tif'
params={'INPUT_RASTER': Factor_Condicionante, 'RASTER_BAND': 1, 'INPUT_TABLE': DF_UGS,
        'MIN_FIELD': 'ID', 'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Valor', 'NO_DATA': -9999,
        'RANGE_BOUNDARIES': 2, 'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5,
        'OUTPUT': Suscep_Caida_UGS}
processing.run(alg, params)

# Suma de los valores
Suscep_Caida_Pendiente = QgsRasterLayer(data_path + '/Pre_Proceso/Suscep_Caida_Pendiente.tif', "Suscep_Caida_Pendiente")
QgsProject.instance().addMapLayer(Suscep_Caida_Pendiente)
Suscep_Caida_SubunidadesGeomorf = QgsRasterLayer(data_path + '/Pre_Proceso/Suscep_Caida_SubunidadesGeomorf.tif', "Suscep_Caida_SubunidadesGeomorf")
QgsProject.instance().addMapLayer(Suscep_Caida_SubunidadesGeomorf)
Suscep_Caida_UGS = QgsRasterLayer(data_path + '/Pre_Proceso/Suscep_Caida_UGS.tif', "Suscep_Caida_UGS")
QgsProject.instance().addMapLayer(Suscep_Caida_UGS)

# Dirección del resultado de la suma de los valores de susceptibilidad
Resultados_Caida = data_path + '/Pre_Proceso/Susceptibilidad_Caida_Pre.tif'
    
# Sumatoria de los raster
alg = "qgis:rastercalculator"
Expresion = '\"Suscep_Caida_Pendiente@1\" + \"Suscep_Caida_SubunidadesGeomorf@1\" + \"Suscep_Caida_UGS@1\"'
extents = Suscep_Caida_UGS.extent() #Extensión de la capa
xmin = extents.xMinimum()
xmax = extents.xMaximum()
ymin = extents.yMinimum()
ymax = extents.yMaximum()
params = {'EXPRESSION': Expresion, 'LAYERS': [Suscep_Caida_UGS],
         'CELLSIZE':0, 'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),
         'CRS': None,'OUTPUT': Resultados_Caida}
processing.run(alg,params)

# Se corta según la zona de estudio
if os.path.isfile(data_path + '/Pre_Proceso/Zona_Estudio.shp') is True:
    Zona_Estudio = QgsVectorLayer(data_path + '/Pre_Proceso/Zona_Estudio.shp', 'Zona_Estudio')
    
    # Se corta la capa de la suma según la zona de estudio
    alg = "gdal:cliprasterbymasklayer"
    Suma = data_path + '/Pre_Proceso/Susceptibilidad_Caida_Pre.tif'
    Suma_Ajustada = data_path + '/Pre_Proceso/Susceptibilidad_Caida_Pre_Ajustada.tif'
    params = {'INPUT': Suma, 'MASK': Zona_Estudio, 'SOURCE_CRS': None,
    'TARGET_CRS': None, 'NODATA': None, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None, 'Y_RESOLUTION': None,
    'MULTITHREADING': False, 'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '', 'OUTPUT': Suma_Ajustada}
    processing.run(alg, params)
    
    # Se redefine la capa raster para el procedimiento
    Resultados_Caida = data_path + '/Pre_Proceso/Susceptibilidad_Caida_Pre_Ajustada.tif'

#Se reclasifica teniendo en cuenta que 1 será susceptibilidad baja, 2 media y 4 alta.
alg = "native:reclassifybytable"
Susceptibilidad_Caida = data_path + '/Resultados/Susceptibilidad_Inicio_Caida.tif'
table = [0, 7, 1, 8, 10, 2, 11, 12, 4]  #[min1, max1, valor1, min2, max2, valor2, min3, max3, valor3] min <= valor <= max
params = {'INPUT_RASTER': Resultados_Caida, 'RASTER_BAND': 1, 'TABLE': table, 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2,
           'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Caida}
processing.run(alg,params)

# Se añade al lienzo
Susceptibilidad_Caida = QgsRasterLayer(Susceptibilidad_Caida, "Susceptibilidad_Caida_Inicio")
QgsProject.instance().addMapLayer(Susceptibilidad_Caida)

########################Zonificación de Susceptibilidad por zonas de deposito tipo Caida########################    

Ruta_Caida_poligonos = data_path + '/Pre_Proceso/Caida_poligonos.shp'

if os.path.isfile(Ruta_Zona_Deposito) is True:
    Zona_Deposito = QgsVectorLayer(Ruta_Zona_Deposito)

    if os.path.isfile(Ruta_Caida_poligonos) is True:
        Caida_poligonos = QgsVectorLayer(Ruta_Caida_poligonos)
        alg = "native:selectbylocation"
        params = {'INPUT': Caida_poligonos, 'PREDICATE':[1,3,5,6,7], 'INTERSECT': Zona_Deposito, 'METHOD':0}
        processing.run(alg, params)
        
        # Se eliminan los poligonos de la selección de forma que no queden sobrepuestos
        caps = Caida_poligonos.dataProvider().capabilities()
        selected_fid = []
        selection = Caida_poligonos.selectedFeatures()
        for feature in selection: 
            fid = feature.id() 
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                Caida_poligonos.dataProvider().deleteFeatures([fid])
                
        # Se unen los poligonos de deposito
        alg = "native:mergevectorlayers"
        Deposito = data_path + '/Pre_Proceso/Caida_Deposito.shp'
        params = {'LAYERS': [Zona_Deposito, Caida_poligonos], 'CRS': None, 'OUTPUT': Deposito}
        processing.run(alg, params) 
        
    else:
        Deposito = Ruta_Zona_Deposito

elif os.path.isfile(Ruta_Caida_poligonos) is True:
    Deposito = Ruta_Caida_poligonos

else: 
    QMessageBox.information(iface.mainWindow(), "!Tenga en cuenta!",
                        'La susceptibilida por caídas quedará incompleta debido a que no se cuenta con zonas de deposito')
    Deposito = 'NaN'

if os.path.isfile(Deposito) is True:
    # Se sobreescriben las áreas de depósito con un valor de 1
    alg = "gdal:rasterize_over_fixed_value"
    Raster = data_path + '/Resultados/Susceptibilidad_Inicio_Caida.tif'
    params = {'INPUT': Deposito,'INPUT_RASTER': Raster,'BURN': 4,'ADD': True,'EXTRA': ''}
    processing.run(alg, params)

    # Se añade la capa al lienzo
    Caidos_Deposito = QgsVectorLayer(Deposito, 'Caidos_Desposito')
    QgsProject.instance().addMapLayer(Caidos_Deposito)
    
#Se reclasifica teniendo en cuenta que 0 será susceptibilidad baja, 1 media y 2 alta.
alg="native:reclassifybytable"
Resultados_Caida = data_path + '/Resultados/Susceptibilidad_Inicio_Caida.tif'
Susceptibilidad_Caida = data_path + '/Resultados/Susceptibilidad_Caida.tif'
table=[1, 1, 0, 2, 2, 1, 3, 8, 2]  #[min1, max1, valor1, min2, max2, valor2, min3, max3, valor3] min <= valor <= max
params={'INPUT_RASTER': Resultados_Caida, 'RASTER_BAND': 1, 'TABLE': table, 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2,
           'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5, 'OUTPUT': Susceptibilidad_Caida}
processing.run(alg, params)

# Se agrega la capa reclasificada con los rangos de susceptibilidad
Susceptibilidad = iface.addRasterLayer(data_path + '/Resultados/Susceptibilidad_Caida.tif', "Susceptibilidad_Caida")

# Se cambia la simbología de la capa de susceptibilidad
fnc = QgsColorRampShader()
fnc.setColorRampType(QgsColorRampShader.Interpolated)
lst = [QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#36b449'), 'Baja'),QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#d4e301'), 'Media'),QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#dc7d0f'), 'Alta')]
fnc.setColorRampItemList(lst)
shader = QgsRasterShader()
shader.setRasterShaderFunction(fnc)
renderer = QgsSingleBandPseudoColorRenderer(Susceptibilidad.dataProvider(), 1, shader)
Susceptibilidad.setRenderer(renderer)

# Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)
    
    