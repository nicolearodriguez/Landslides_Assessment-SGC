from PyQt5.QtWidgets import QInputDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject
import matplotlib.pyplot as plt
from osgeo import gdal_array
import pandas as pd
import numpy as np
import processing
import gdal
import os

# Se pide la ruta general de la ubicación de los archivos relativa a la ubicación del programa
data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
data_path = data_path[0]
data_path = data_path.replace("\\", "/")

# Se pide las dimensiones del pixel
Pixel = QInputDialog.getDouble(None, 'CELLSIZE', 'Introduce el tamaño del pixel: ')
cellsize = Pixel[0]

# Capas raster reclasificadas con su respectivo Wf
PendientesReclass = QgsRasterLayer(data_path + '/Resultados/PendientesWf.tif', "PendientesReclass")
QgsProject.instance().addMapLayer(PendientesReclass)
# CoberturaReclass=QgsRasterLayer(data_path + '/Resultados/CoberturaWf.tif', "CoberturaReclass")
# QgsProject.instance().addMapLayer(CoberturaReclass)
GeomorfoReclass = QgsRasterLayer(data_path + '/Resultados/GeomorfoWf.tif', "GeomorfoReclass")
QgsProject.instance().addMapLayer(GeomorfoReclass)
UgsReclass = QgsRasterLayer(data_path + '/Resultados/UgsWf.tif', "UgsReclass")
QgsProject.instance().addMapLayer(UgsReclass)
CoberturayUsosReclass = QgsRasterLayer(data_path + '/Resultados/CoberturayUsosWf.tif', "CoberturayUsosReclass")
QgsProject.instance().addMapLayer(CoberturayUsosReclass)
CurvaturaReclass = QgsRasterLayer(data_path + '/Resultados/CurvaturaWf.tif', "CurvaturaReclass")
QgsProject.instance().addMapLayer(CurvaturaReclass)

# Dirección del resultado de la suma de los Wf
Output = data_path + '/Resultados/LSI.tif'

# Sumatoria de los raster
alg = "qgis:rastercalculator"
Expresion = '\"CoberturayUsosReclass@1\" + \"CurvaturaReclass@1\" + \"GeomorfoReclass@1\" + \"PendientesReclass@1\" + \"UgsReclass@1\"'  # +\"CoberturaReclass@1\"'
extents = CurvaturaReclass.extent()  # Capa de la cuál se copiará la extensión del algoritmo
xmin = extents.xMinimum()  # xmin de la extensión
xmax = extents.xMaximum()  # xmax de la extensión
ymin = extents.yMinimum()  # ymin de la extensión
ymax = extents.yMaximum()  # ymax de la extensión
CRS = QgsCoordinateReferenceSystem('EPSG:3116')
params = {'EXPRESSION': Expresion, 'LAYERS': [CurvaturaReclass], 'CELLSIZE': cellsize, 'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax), 'CRS': CRS, 'OUTPUT': Output}
processing.run(alg, params)

# Se agrega la capa raster LSI al lienzo
LSI = QgsRasterLayer(data_path + '/Resultados/LSI.tif', "LSI")
QgsProject.instance().addMapLayer(LSI)

rasterfile = data_path + '/Resultados/LSI.tif'

# Se lee el archivo correspondientes a deslizamientos
Deslizamientos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos.shp')

if Deslizamientos.wkbType()== QgsWkbTypes.Point:
    # Obtenermos el id de la caracteristica del punto de deslizamiento
    alg = "qgis:rastersampling"
    output = data_path+'/Pre_Proceso/ValoresLSI.shp'
    params = {'INPUT': Deslizamientos, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Id_Condici', 'OUTPUT': output}
    processing.run(alg, params)
    
    # Valores LSI en los puntos de deslizamiento
    ValoresRaster = QgsVectorLayer(data_path + '/Pre_Proceso/ValoresLSI.shp', 'ValoresLSI')
else:
    #Se hace la interesección de el factor condicionante con el área de deslizamientos
    #Obteniendo así los atributos correspondintes a deslizamientos 
    alg = "gdal:cliprasterbymasklayer"
    Factor_Condicionante = rasterfile
    Deslizamiento_Condicion = data_path+'/Pre_Proceso/DeslizamientosLSI.tif'
    params = {'INPUT': Factor_Condicionante, 'MASK': Deslizamientos, 'SOURCE_CRS': QgsCoordinateReferenceSystem('EPSG:3116'),
    'TARGET_CRS': QgsCoordinateReferenceSystem('EPSG:3116'), 'NODATA': None, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True,
    'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False,
    'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '', 'OUTPUT': Deslizamiento_Condicion}
    processing.run(alg, params)
    
    #Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo por deslizamiento)
    alg = "native:rasterlayerzonalstats"
    Estadisticas_Deslizamiento = data_path+'/Pre_Proceso/DeslizamientosLSIEstadistica.csv'
    params = {'INPUT': Deslizamiento_Condicion, 'BAND': 1, 'ZONES': Deslizamiento_Condicion, 'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Deslizamiento}
    processing.run(alg, params)
    
    Estadisticas_Deslizamiento = data_path+'/Pre_Proceso/DeslizamientosLSIEstadistica.csv'
    DF_DeslizamientosEstadistica = pd.read_csv(Estadisticas_Deslizamiento, delimiter=",",encoding='latin-1')

# Se obtienen las estadísticas zonales de los resultados LSI.
alg = "native:rasterlayerzonalstats"
output = data_path + '/Pre_Proceso/LSIEstadistica.csv'
params = {'INPUT': rasterfile, 'BAND': 1, 'ZONES': rasterfile, 'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': output}
processing.run(alg, params)

# Se cargan los archivos necesario para el proceso
# Valores unicos del factor condicionante
FILE_NAME = data_path + '/Pre_Proceso/LSIEstadistica.csv'
DF_LSIEstadistica = pd.read_csv(FILE_NAME, delimiter=", ", encoding = 'latin-1')
uniquevalues = DF_LSIEstadistica["zone"].unique()
atributos = list(sorted(uniquevalues, reverse=True))

# Valores minimos y máximos LSI
LSI_Min = int((round(min(atributos), 0)) - 1)
LSI_Max = int(round(max(atributos), 0) + 1)
Intervalo = list(sorted(range(LSI_Min, LSI_Max+1), reverse = True))

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
df = df.drop(df[df[0] < LSI_Min].index)
df = df.drop(df[df[0] > LSI_Max].index)

# Se crea el dataframe para realizar el proceso de la curva LSI
DF_Susceptibilidad = pd.DataFrame(columns=['LSI_Min', 'LSI_Max', 'PIXLsi', 'PIXDesliz', 'PIXLsiAcum', 'PIXDeslizAcum', 'X', 'Y', 'Area', 'Categoria', 'Susceptibilidad'], dtype = float)

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
percentiles = list(sorted(range(101), reverse=True))

# Se cuenta los números de pixeles para cada rango
for i in range(1, len(percentiles)):
    Min = np.percentile(df[0], percentiles[i])
    Max = np.percentile(df[0], percentiles[i-1])
    # Se le asigna su id a cada atributo
    DF_Susceptibilidad.loc[i, 'LSI_Min'] = Min
    DF_Susceptibilidad.loc[i, 'LSI_Max'] = Max
    # Número de pixeles según la clase LSI
    DF_Susceptibilidad.loc[i, 'PIXLsi'] = DF_LSIEstadistica.loc[(DF_LSIEstadistica['zone'] >= De) & (DF_LSIEstadistica['zone'] <= Hasta)]['count'].sum()
    # Se determina el número de pixeles con movimientos en masa en la clase
    if Deslizamientos.wkbType()== QgsWkbTypes.Point:
        ValoresRaster.selectByExpression(f'"Id_Condici" < \'{Max}\' and "Id_Condici" > \'{Min}\'', QgsVectorLayer.SetSelection)
        selected_fid = []
        selection = ValoresRaster.selectedFeatures()
        DF_Susceptibilidad.loc[i, 'PIXDesliz'] = len(selection)
    else:
        DF_Susceptibilidad.loc[i,'PIXDesliz'] = DF_DeslizamientosEstadistica.loc[(DF_DeslizamientosEstadistica['zone'] > Min) 
                                    & (DF_DeslizamientosEstadistica['zone'] <= Max)]['count'].sum()
    
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
    DF_Susceptibilidad.loc[i, 'Area'] = (DF_Susceptibilidad.loc[i+1, 'X']-DF_Susceptibilidad.loc[i, 'X'])*(DF_Susceptibilidad.loc[i+1, 'Y']+DF_Susceptibilidad.loc[i, 'Y'])/2

# Se suman las áreas para obtener así el área bajo la curva correspondiendte a la bondad y ajuste de la curva
Area_Total = DF_Susceptibilidad['Area'].sum()
print('El área bajo la curva es: ', Area_Total)

# Si el área bajo la curva da menor a 0.7 (70%) se generá un mensaje de advertencia, de lo contrario se generá un mensaje para corroborar que está correcto
if Area_Total > 0.7:
    iface.messageBar().pushMessage("Ajuste LSI", 'La función final de susceptibilidad es aceptable', Qgis.Info, 5)
else:
    iface.messageBar().pushMessage("Ajuste LSI", 'La función final de susceptibilidad NO es aceptable', Qgis.Warning, 5)

# Se identifican los valores Y para asignar el rango de susceptibilidad
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] <= 0.75)].index, 'Categoria'] = 2
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] <= 0.75)].index, 'Susceptibilidad'] = 'Alta'
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > 0.75) & (DF_Susceptibilidad['Y'] <= 0.98)].index, 'Categoria'] = 1
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > 0.75) & (DF_Susceptibilidad['Y'] <= 0.98)].index, 'Susceptibilidad'] = 'Media'
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > 0.98)].index, 'Categoria'] = 0
DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > 0.98)].index, 'Susceptibilidad'] = 'Baja'

# Se imprime la tabla y se guarda como archivo CSV
print(DF_Susceptibilidad)
DF_Susceptibilidad.reset_index().to_csv(data_path + '/Pre_Proceso/DF_LSI.csv', header=True, index=False)

# Extracción de los valores para la curva de éxito.
x = DF_Susceptibilidad['X']
y = DF_Susceptibilidad['Y']
# Se hace las espacialización de los puntos.
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
    'INPUT_RASTER': RasterReclass, 'RASTER_BAND': 1, 'INPUT_TABLE': Tabla, 'MIN_FIELD': 'LSI_De',
    'MAX_FIELD': 'LSI_Hasta', 'VALUE_FIELD': 'Categoria', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2,
    'NODATA_FOR_MISSING': False, 'DATA_TYPE': 5, 'OUTPUT': Salida}
processing.run(alg, params)

# Se agrega la capa reclasificada con los rangos de susceptibilidad
iface.addRasterLayer(data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif', "Susceptibilidad_Deslizamientos")
