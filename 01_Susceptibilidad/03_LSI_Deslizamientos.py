"""
@author: Nicole Alejadra Rodríguez Vargas
nicole.rodriguez@correo.uis.edu.co
"""

"""
En esta programación se hace el análisis LSI a partir de los pesos de evidencia, se realiza
la curva de éxito y se comprueba si esta cumple, de ser así se clasifica la función LSI según
la categoría de susceptibilidad por deslizamientos que le corresponda.
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

# Se imprime una recomendación
QMessageBox.information(iface.mainWindow(), "!Tenga en cuenta!",
                        'Se recomienda que si ya se ha ejecutado el programa con anterioridad sean borrados los archivos '
                        'que este genera para evitar conflictos al reemplazar los archivos pre-existentes en especial los .shp')

# Dimensiones del pixel
cellsize, ok = QInputDialog.getDouble(
    None, 'Tamaño del pixel', 'Introduzca el tamaño del pixel: ')
if ok == False:
    raise Exception('Cancelar')

# Capas raster reclasificadas con su respectivo Wf

# Pendiente
Ruta_Pendiente = data_path + '/Resultados/Wf_Pendiente.tif'
Wf_Pendiente = QgsRasterLayer(Ruta_Pendiente, "Wf_Pendiente")
QgsProject.instance().addMapLayer(Wf_Pendiente)

# Subunidades geomorfologicas
Ruta_SubunidadesGeomorf = data_path + '/Resultados/Wf_SubunidadesGeomorf.tif'
Wf_SubunidadesGeomorf = QgsRasterLayer(Ruta_SubunidadesGeomorf, "Wf_SubunidadesGeomorf")
QgsProject.instance().addMapLayer(Wf_SubunidadesGeomorf)

# Unidades geologicas superficiales
Ruta_UGS = data_path + '/Resultados/Wf_UGS.tif'
Wf_UGS = QgsRasterLayer(Ruta_UGS, "Wf_UGS")
QgsProject.instance().addMapLayer(Wf_UGS)

# Cobertura y uso
Ruta_CoberturaUso = data_path + '/Resultados/Wf_CoberturaUso.tif'
Wf_CoberturaUso = QgsRasterLayer(Ruta_CoberturaUso, "Wf_CoberturaUso")
QgsProject.instance().addMapLayer(Wf_CoberturaUso)

# Curvatura plana
Ruta_CurvaturaPlano = data_path + '/Resultados/Wf_CurvaturaPlano.tif'
Wf_CurvaturaPlano = QgsRasterLayer(Ruta_CurvaturaPlano, "Wf_CurvaturaPlano")
QgsProject.instance().addMapLayer(Wf_CurvaturaPlano)

# Cambio de cobertura
Ruta_CambioCobertura = data_path + '/Resultados/Wf_CambioCobertura.tif'
if os.path.isfile(Ruta_CambioCobertura) is True:
    # Si el archivo existe se tiene en cuenta en la suma
    Wf_CambioCobertura = QgsRasterLayer(Ruta_CambioCobertura, "Wf_CambioCobertura")
    QgsProject.instance().addMapLayer(Wf_CambioCobertura)
    Expresion = '\"Wf_CoberturaUso@1\" + \"Wf_CurvaturaPlano@1\" + \"Wf_SubunidadesGeomorf@1\" + \"Wf_Pendiente@1\" + \"Wf_UGS@1\" + \"Wf_CambioCobertura@1\"'
else: 
    # Si cambio de cobertura no existe no se tiene en cuenta para la suma de pesos
    Expresion = '\"Wf_CoberturaUso@1\" + \"Wf_CurvaturaPlano@1\" + \"Wf_SubunidadesGeomorf@1\" + \"Wf_Pendiente@1\" + \"Wf_UGS@1\"'

# Dirección del resultado de la suma de los Wf
Output = data_path + '/Resultados/LSI.tif'

# Sumatoria de los raster
alg = "qgis:rastercalculator"
extents = Wf_CurvaturaPlano.extent()  # Capa de la cuál se copiará la extensión del algoritmo
xmin = extents.xMinimum()  # xmin de la extensión
xmax = extents.xMaximum()  # xmax de la extensión
ymin = extents.yMinimum()  # ymin de la extensión
ymax = extents.yMaximum()  # ymax de la extensión
params = {'EXPRESSION': Expresion, 'LAYERS': [Wf_CurvaturaPlano], 'CELLSIZE': cellsize,
          'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax), 'CRS': None, 'OUTPUT': Output}
processing.run(alg, params)

# Se agrega la capa raster LSI al lienzo
LSI = QgsRasterLayer(data_path + '/Resultados/LSI.tif', "LSI")
QgsProject.instance().addMapLayer(LSI)

# Se define el archivo raster para el procedimiento
rasterfile = data_path + '/Resultados/LSI.tif'

# Se lee el archivo correspondientes a deslizamientos
Deslizamientos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos.shp')

# Dependiendo de la geometría de los deslizamientos se hace el procedimiento
if Deslizamientos.wkbType() == QgsWkbTypes.Point:
    # Obtenermos el id de la caracteristica del punto de deslizamiento
    alg = "qgis:rastersampling"
    output = data_path+'/Pre_Proceso/ValoresLSI.shp'
    params = {'INPUT': Deslizamientos, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Id_Condici', 'OUTPUT': output}
    processing.run(alg, params)
    
    # Valores LSI en los puntos de deslizamiento
    ValoresRaster = QgsVectorLayer(data_path + '/Pre_Proceso/ValoresLSI.shp', 'ValoresLSI')
else:
    # Se hace la interesección de el factor condicionante con el área de deslizamientos
    # Obteniendo así los atributos correspondintes a deslizamientos 
    alg = "gdal:cliprasterbymasklayer"
    Factor_Condicionante = rasterfile
    Deslizamiento_Condicion = data_path + '/Pre_Proceso/DeslizamientosLSI.tif'
    params = {'INPUT': Factor_Condicionante, 'MASK': Deslizamientos, 'SOURCE_CRS': None,
    'TARGET_CRS': None, 'NODATA': None, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False,
    'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '', 'OUTPUT': Deslizamiento_Condicion}
    processing.run(alg, params)
    
    # Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo por deslizamiento)
    alg = "native:rasterlayerzonalstats"
    Estadisticas_Deslizamiento = data_path + '/Pre_Proceso/DeslizamientosLSIEstadistica.csv'
    params = {'INPUT': Deslizamiento_Condicion, 'BAND': 1, 'ZONES': Deslizamiento_Condicion, 'ZONES_BAND': 1,
              'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Deslizamiento}
    processing.run(alg, params)
    
    # Lectura de las estadísticas de la zona de deslizamientos como dataframe
    Estadisticas_Deslizamiento = data_path + '/Pre_Proceso/DeslizamientosLSIEstadistica.csv'
    DF_DeslizamientosEstadistica = pd.read_csv(Estadisticas_Deslizamiento, delimiter=",", encoding = 'latin-1')

# Se obtienen las estadísticas zonales de los resultados LSI.
alg = "native:rasterlayerzonalstats"
output = data_path + '/Pre_Proceso/LSIEstadistica.csv'
params = {'INPUT': rasterfile, 'BAND': 1, 'ZONES': rasterfile, 'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': output}
processing.run(alg, params)

# Se cargan los archivos necesario para el proceso
# Valores unicos del factor condicionante
FILE_NAME = data_path + '/Pre_Proceso/LSIEstadistica.csv'
DF_LSIEstadistica = pd.read_csv(FILE_NAME, encoding = 'latin-1')
atributos = DF_LSIEstadistica["zone"].unique()
df = pd.DataFrame(atributos)
df = df.sort_values(by = 0)

# Valores minimos y máximos LSI
LSI_Min = int((round(min(atributos), 0)) - 1)
LSI_Max = int(round(max(atributos), 0) + 1)

# Se pasan los valores del raster LSI a un arreglo matricial
rasterArray = gdal_array.LoadFile(rasterfile)
rasterList = rasterArray.tolist()

# La lista de listas de la matriz se pasan a una sola lista item por item
flat_list = []
for sublist in rasterList:
    for item in sublist:
        flat_list.append(item)

# La lista se convierte en un dataframe para eliminar los valores que no corresponden a LSI
df = pd.DataFrame(flat_list)
df = df.drop(df[df[0] < -100].index) #LSI_Min
df = df.drop(df[df[0] > 100].index) #LSI_Max
df = df.dropna(axis=0, subset=[0])

# Se crea el dataframe para realizar el proceso de la curva LSI
DF_Susceptibilidad = pd.DataFrame(columns=['LSI_Min', 'LSI_Max', 'PIXLsi', 'PIXDesliz', 'PIXLsiAcum',
                                           'PIXDeslizAcum', 'X', 'Y', 'Area', 'Categoria', 'Susceptibilidad'], dtype = float)

# Se llena la fila de índice 0 del dataframe
DF_Susceptibilidad.loc[0, 'LSI_Min'] = 0
DF_Susceptibilidad.loc[0, 'LSI_Max'] = 0
DF_Susceptibilidad.loc[0, 'PIXLsi'] = 0
DF_Susceptibilidad.loc[0, 'PIXDesliz'] = 0
DF_Susceptibilidad.loc[0, 'PIXLsiAcum'] = 0
DF_Susceptibilidad.loc[0, 'PIXDeslizAcum'] = 0
DF_Susceptibilidad.loc[0, 'X'] = 0
DF_Susceptibilidad.loc[0, 'Y'] = 0

# Se definen los percentiles en los que se harán los intervalos
n_percentil = sorted(range(101), reverse=True)

#Se calcula el percentil cada 1 %
percentiles = [np.percentile(df[0], 100) + 0.001]
for i in range(1, len(n_percentil)-1):
    Valor = np.percentile(df[0], n_percentil[i])
    percentiles.append(Valor)
percentiles.append(np.percentile(df[0], 0) - 0.001)

# Se cuenta los números de pixeles para cada rango
for i in range(1, len(percentiles)):
    Min = percentiles[i]
    Max = percentiles[i-1]
    # Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i, 'LSI_Min'] = Min
    DF_Susceptibilidad.loc[i, 'LSI_Max'] = Max
    # Número de pixeles según la clase LSI
    DF_Susceptibilidad.loc[i, 'PIXLsi'] = DF_LSIEstadistica.loc[(DF_LSIEstadistica['zone'] >= Min) & (DF_LSIEstadistica['zone'] < Max)]['count'].sum()
    # Se determina el número de pixeles de deslizamientos en la clase
    # Si los deslizamientos tienen geometría de puntos
    if Deslizamientos.wkbType()== QgsWkbTypes.Point:
        ValoresRaster.selectByExpression(f'"Id_Condici" < \'{Max}\' and "Id_Condici" >= \'{Min}\'', QgsVectorLayer.SetSelection)
        selected_fid = []
        selection = ValoresRaster.selectedFeatures()
        DF_Susceptibilidad.loc[i, 'PIXDesliz'] = len(selection)
    else:
        # Si los deslizamientos tienen geometría de poligonos
        DF_Susceptibilidad.loc[i,'PIXDesliz'] = DF_DeslizamientosEstadistica.loc[(DF_DeslizamientosEstadistica['zone'] >= Min) 
                                    & (DF_DeslizamientosEstadistica['zone'] < Max)]['count'].sum()
    
# Número total de pixeles
Sum_LSI = DF_Susceptibilidad['PIXLsi'].sum()
Sum_LSIDesliz = DF_Susceptibilidad['PIXDesliz'].sum()

# Se cálculan los pixeles acumulados y el porcentaje para la elaboración de la curva
for i in range(1, len(DF_Susceptibilidad)):
    # Se determina el número de pixeles con movimientos en masa en la clase
    DF_Susceptibilidad.loc[i, 'PIXLsiAcum'] = DF_Susceptibilidad.loc[i-1, 'PIXLsiAcum']+DF_Susceptibilidad.loc[i, 'PIXLsi']
    DF_Susceptibilidad.loc[i, 'PIXDeslizAcum'] = DF_Susceptibilidad.loc[i-1, 'PIXDeslizAcum']+DF_Susceptibilidad.loc[i, 'PIXDesliz']
    DF_Susceptibilidad.loc[i, 'X'] = (DF_Susceptibilidad.loc[i, 'PIXLsiAcum']/Sum_LSI)
    DF_Susceptibilidad.loc[i, 'Y'] = (DF_Susceptibilidad.loc[i, 'PIXDeslizAcum']/Sum_LSIDesliz)

# Se calcula el área entre los rangos por medio de la formula del trapecio
for i in range(0, len(DF_Susceptibilidad)-1):
    DF_Susceptibilidad.loc[i, 'Area'] = (DF_Susceptibilidad.loc[i+1, 'X'] - DF_Susceptibilidad.loc[i, 'X'])*(DF_Susceptibilidad.loc[i+1, 'Y'] + DF_Susceptibilidad.loc[i, 'Y'])/2

# Se suman las áreas para obtener así el área bajo la curva correspondiendte a la bondad y ajuste de la curva
Area_Total = DF_Susceptibilidad['Area'].sum()
print('El área bajo la curva es: ', Area_Total)

# Si el área bajo la curva da menor a 0.7 (70%) se generá un mensaje de advertencia,
# de lo contrario se generá un mensaje para corroborar que está correcto
if Area_Total > 0.7:
    iface.messageBar().pushMessage("Ajuste LSI", 'La función final de susceptibilidad es aceptable', Qgis.Info, 5)
else:
    iface.messageBar().pushMessage("Ajuste LSI", 'La función final de susceptibilidad NO es aceptable', Qgis.Warning, 10)

# Se identifican los valores Y para asignar el rango de susceptibilidad
# Alta
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] <= 0.75)].index, 'Categoria'] = 2
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] <= 0.75)].index, 'Susceptibilidad'] = 'Alta'
# Media
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > 0.75) & (DF_Susceptibilidad['Y'] <= 0.98)].index, 'Categoria'] = 1
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > 0.75) & (DF_Susceptibilidad['Y'] <= 0.98)].index, 'Susceptibilidad'] = 'Media'
# Baja
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > 0.98)].index, 'Categoria'] = 0
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > 0.98)].index, 'Susceptibilidad'] = 'Baja'

# Se imprime la tabla y se guarda como archivo CSV
print(DF_Susceptibilidad)
DF_Susceptibilidad.reset_index().to_csv(data_path + '/Pre_Proceso/DF_LSI.csv', header=True, index=False)

# Extracción de los valores para la curva de éxito.
x = DF_Susceptibilidad['X']
y = DF_Susceptibilidad['Y']
# Se hace las espacialización de los valores
fig, ax = plt.subplots()
ax.plot(x, y, color='black', label = "Success curve")
# Se hacen las líneas correspondientes para clasificar la susceptibilidad
y1 = 0.75
ax.axhline(y1, lw = 0.5, alpha = 0.7, linestyle = "--", label = "Y=0.75", color = 'orangered')
y2 = 0.98
ax.axhline(y2, lw = 0.5, alpha = 0.7, linestyle = "--", label = "Y=0.98", color = 'green')
plt.legend(loc = 'upper left')
# Se colorean los rangos de susceptibilidad
ax.fill_between(x, y, where= (y < y1), facecolor = 'orange', edgecolor = 'orangered', linewidth = 3, alpha = 0.5)
ax.fill_between(x, y, where= (y >= y1) & (y < y2), facecolor = 'yellow', edgecolor = 'yellow', linewidth = 3, alpha = 0.5)
ax.fill_between(x, y, where= (y >= y2), facecolor = 'green', edgecolor = 'green', linewidth = 3, alpha = 0.5)
# Se aplican los nombres de los ejes y título
ax.set_xlabel("PORCENTAJE DE LA ZONA DE ESTUDIO")
ax.set_ylabel("PORCENTAJE DE LA ZONA DE DESLIZAMIENTOS")
ax.set_title('CURVA DE ÉXITO', pad = 20, fontdict = {'fontsize': 20, 'color': '#4873ab'})
plt.show()  # Se muestra la gráfica
fig.savefig(data_path+'/Resultados/Curva_Exito.jpg')  # Se guarda la gráfica en formato .jpg

# Reclasificación del mapa raster
alg = "native:reclassifybylayer"
RasterReclass = rasterfile
Tabla = data_path + '/Pre_Proceso/DF_LSI.csv'
Salida = data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif'
params = {
    'INPUT_RASTER': RasterReclass, 'RASTER_BAND': 1, 'INPUT_TABLE': Tabla, 'MIN_FIELD': 'LSI_Min',
    'MAX_FIELD': 'LSI_Max', 'VALUE_FIELD': 'Categoria', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 1,
    'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5, 'OUTPUT': Salida}
processing.run(alg, params)

# Se agrega la capa reclasificada con los rangos de susceptibilidad
iface.addRasterLayer(data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif', "Susceptibilidad_Deslizamientos")

# Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)
