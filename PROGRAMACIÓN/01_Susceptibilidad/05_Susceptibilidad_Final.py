"""
@author: Nicole Alejadra Rodríguez Vargas
@mail: nicole.rodriguez@correo.uis.edu.co
"""

"""
En esta programación se hace el análisis el análisis final de susceptibilidad
por movimientos en masa en general, dónde se combinan las susceptibilidades 
anteriores de deslizamiento, caída y flujo, y se sobreponen la reptación.
"""

from PyQt5.QtWidgets import QInputDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject
import matplotlib.pyplot as plt
from osgeo import gdal_array
from time import time
import pandas as pd
import numpy as np
import processing
import gdal
import os

# Se determina el momento en que inicia la ejcución del programa
start_time = time()

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
if ok == False:
    raise Exception('Cancelar')
data_path = data_path.replace("\\", "/")

# Se reclasifican la susceptibilidad alta de 2 a 3 para que no hayan valores erroneos en la susceptibilidad final

# Susceptibilidad deslizamientos
alg="native:reclassifybytable"
Susceptibilidad_Deslizamientos = data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif'
Susceptibilidad_Deslizamientos_Reclass = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Reclass.tif'
table = [0, 0, 0, 1, 1, 1, 2, 2, 3]  # [min1, max1, valor1, min2, max2, valor2, min3, max3, valor3]  min<=valor<=max
params = {'INPUT_RASTER': Susceptibilidad_Deslizamientos,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,
          'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Deslizamientos_Reclass}
processing.run(alg, params)

# Susceptibilidad caídas
alg="native:reclassifybytable"
Susceptibilidad_Caida = data_path + '/Resultados/Susceptibilidad_Caida.tif'
Susceptibilidad_Caida_Reclass = data_path + '/Pre_Proceso/Susceptibilidad_Caida_Reclass.tif'
table = [0, 0, 0, 1, 1, 1, 2, 2, 3]  # [min1, max1, valor1, min2, max2, valor2, min3, max3, valor3]  min<=valor<=max
params = {'INPUT_RASTER': Susceptibilidad_Caida,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,
          'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Caida_Reclass}
processing.run(alg, params)

# Susceptibilidad flujos
alg="native:reclassifybytable"
Susceptibilidad_Flujo = data_path + '/Resultados/Susceptibilidad_Flujo.tif'
Susceptibilidad_Flujo_Reclass = data_path + '/Pre_Proceso/Susceptibilidad_Flujo_Reclass.tif'
table = [0, 0, 0, 1, 1, 1, 2, 2, 3]  # [min1, max1, valor1, min2, max2, valor2, min3, max3, valor3]  min<=valor<=max
params = {'INPUT_RASTER': Susceptibilidad_Flujo,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,
          'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Flujo_Reclass}
processing.run(alg, params)

# Se suman las susceptibilidades en primer lugar de deslizamientos y caídas

# Susceptibilidad deslizamientos
Ruta_Deslizamientos = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Reclass.tif'
Susceptibilidad_Deslizamientos_Reclass = QgsRasterLayer(Ruta_Deslizamientos, "Susceptibilidad_Deslizamientos_Reclass")
QgsProject.instance().addMapLayer(Susceptibilidad_Deslizamientos_Reclass)

# Susceptibilidad caídas
Ruta_Caída = data_path + '/Pre_Proceso/Susceptibilidad_Caida_Reclass.tif'
Susceptibilidad_Caida_Reclass = QgsRasterLayer(Ruta_Caída, "Susceptibilidad_Caida_Reclass")
QgsProject.instance().addMapLayer(Susceptibilidad_Caida_Reclass)

#Dirección del resultado de la suma de los valores de susceptibilidad
Susceptibilidad_Deslizamientos_Caída = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Caidas.tif'

# Sumatoria de los raster
alg = "qgis:rastercalculator"
Expresion = '\"Susceptibilidad_Deslizamientos_Reclass@1\" + \"Susceptibilidad_Caida_Reclass@1\"'
extents = Susceptibilidad_Deslizamientos_Reclass.extent()  # Capa de la cuál se copiará la extensión del algoritmo
xmin = extents.xMinimum()  # xmin de la extensión
xmax = extents.xMaximum()  # xmax de la extensión
ymin = extents.yMinimum()  # ymin de la extensión
ymax = extents.yMaximum()  # ymax de la extensión
params = {'EXPRESSION': Expresion, 'LAYERS': [Susceptibilidad_Deslizamientos_Reclass], 'CELLSIZE': 0,
          'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax), 'CRS': None, 'OUTPUT': Susceptibilidad_Deslizamientos_Caída}
processing.run(alg, params)

# Susceptibilidad combinada de deslizamientos y caídas
alg="native:reclassifybytable"
Susceptibilidad_Deslizamientos_Caída = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Caidas.tif'
Susceptibilidad_Deslizamientos_Caída_Reclass = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Caidas_Reclass.tif'
table = [0, 0, 0, 1, 2, 1, 3, 6, 3]  # [min1, max1, valor1, min2, max2, valor2, min3, max3, valor3]  min<=valor<=max
params = {'INPUT_RASTER': Susceptibilidad_Deslizamientos_Caída,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,
          'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Deslizamientos_Caída_Reclass}
processing.run(alg, params)

# Se suman las susceptibilidades previamente combinadas y flujos

# Susceptibilidad flujos
Ruta_Flujo = data_path + '/Pre_Proceso/Susceptibilidad_Flujo_Reclass.tif'
Susceptibilidad_Flujo_Reclass = QgsRasterLayer(Ruta_Flujo, "Susceptibilidad_Flujo_Reclass")
QgsProject.instance().addMapLayer(Susceptibilidad_Flujo_Reclass)

# Susceptibilidad combinada de deslizamientos y caídas
Ruta_Deslizamientos_Caidas = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Caidas_Reclass.tif'
Susceptibilidad_Deslizamientos_Caída = QgsRasterLayer(Ruta_Deslizamientos_Caidas, "Susceptibilidad_Deslizamientos_Caída")
QgsProject.instance().addMapLayer(Susceptibilidad_Deslizamientos_Caída)

#Dirección del resultado de la suma de los valores de susceptibilidad
Susceptibilidad_Deslizamientos_Caída_Flujos = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Caidas_Flujos.tif'

# Sumatoria de los raster
alg = "qgis:rastercalculator"
Expresion = '\"Susceptibilidad_Flujo_Reclass@1\" + \"Susceptibilidad_Deslizamientos_Caída@1\"'
extents = Susceptibilidad_Flujo_Reclass.extent()  # Capa de la cuál se copiará la extensión del algoritmo
xmin = extents.xMinimum()  # xmin de la extensión
xmax = extents.xMaximum()  # xmax de la extensión
ymin = extents.yMinimum()  # ymin de la extensión
ymax = extents.yMaximum()  # ymax de la extensión
params = {'EXPRESSION': Expresion, 'LAYERS': [Susceptibilidad_Flujo_Reclass], 'CELLSIZE': 0,
          'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax), 'CRS': None, 'OUTPUT': Susceptibilidad_Deslizamientos_Caída_Flujos}
processing.run(alg, params)

# Se reclasifica la susceptibilidad final por deslizamientos, caídas y flujos
alg="native:reclassifybytable"
Susceptibilidad_Deslizamientos_Caída_Flujos = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Caidas_Flujos.tif'
Susceptibilidad_Final = data_path + '/Resultados/Susceptibilidad_Final.tif'
table = [0, 0, 0, 1, 2, 1, 3, 6, 2]  # [min1, max1, valor1, min2, max2, valor2, min3, max3, valor3]  min<=valor<=max
params = {'INPUT_RASTER': Susceptibilidad_Deslizamientos_Caída_Flujos, 'RASTER_BAND': 1, 'TABLE': table, 'NO_DATA': -9999, 
          'RANGE_BOUNDARIES': 2, 'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Final}
processing.run(alg, params)

# Se añade al lienzo la susceptibilidad final
Susceptibilidad_Final = QgsRasterLayer(Susceptibilidad_Final, "Susceptibilidad_Final")
QgsProject.instance().addMapLayer(Susceptibilidad_Final)

# Se muestran las zonas de reptación en formato polígono
Reptacion_poligonos = data_path + '/Pre_Proceso/Reptacion_poligonos.shp'
if os.path.isfile(Reptacion_poligonos) is True:
    # Se añade la capa al lienzo
    Reptacion_poligonos = QgsVectorLayer(Reptacion_poligonos, 'Reptacion_poligonos')
    QgsProject.instance().addMapLayer(Reptacion_poligonos)
    
# Se muestran las zonas de reptación en formato punto
Reptacion_puntos = data_path+'/Pre_Proceso/Reptacion_puntos.shp'
if os.path.isfile(Reptacion_puntos) is True:
    # Se añade la capa al lienzo
    Reptacion_puntos = QgsVectorLayer(Reptacion_puntos, 'Reptacion_puntos')
    QgsProject.instance().addMapLayer(Reptacion_puntos)

# Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)