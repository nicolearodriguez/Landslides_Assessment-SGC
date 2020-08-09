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
import datetime
import os

start_time = time()

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
data_path = data_path.replace("\\", "/")

# Se listan los archivos en la ruta general
list = listdir(data_path)

# Se determinan los archivos con extensión .shp
shape = []
for i in list:
    if i[-4:] == '.shp':
        shape.append(i)
shape.append('None')

# Ubicación de las estaciones de precipitación
Estaciones, ok = QInputDialog.getItem(None, "Estaciones pluviométricas", "Seleccione el archivo de las estaciones", shape, 0, False)
Ruta_Estaciones = data_path + '/' + Estaciones
Estaciones = QgsVectorLayer(Ruta_Estaciones)

# Se listan los atributos en la capa seleccionada
atributos_Estaciones = []
for field in Estaciones.fields():
    atributos_Estaciones.append(field.name())

# Nombre del campo dónde se encuentran los códigos representativos de las estaciones
Codigo_Estacion, ok = QInputDialog.getItem(None, "Códigos de las estaciones", "Campo dónde se encuentran los códigos representativos de las estaciones", atributos_Estaciones, 0, False)

# Ubicación de los sismos
Sismos, ok = QInputDialog.getItem(None, "Sismos", "Seleccione el archivo de los sismos", shape, 0, False)
Ruta_Sismos = data_path + '/' + Sismos
Sismos = QgsVectorLayer(Ruta_Sismos)

# Se listan los atributos en la capa seleccionada
atributos_Sismos = []
for field in Sismos.fields():
    atributos_Sismos.append(field.name())
    
# Nombre del campo dónde se encuentran la magnitud del sismo
Magnitud_Sismo, ok = QInputDialog.getItem(None, "Magnitud del sismo", "Nombre del campo dónde se encuentran la magnitud del sismo", atributos_Sismos, 0, False)
   
# Nombre del campo dónde se encuentran la unidad de la magitud
Unidad_Sismo, ok = QInputDialog.getItem(None, "Unidad de la magnitud del sismo", "Nombre del campo dónde se encuentran la unidad de la magitud", atributos_Sismos, 0, False)
   
#Umbral de días para los movimientos en masa
dias = QInputDialog.getInt(None, 'Umbral de días de la fecha del inventario', 'Introduzca el umbral de días para el análisis del inventario de MM: ')
dias = dias[0]

#Número de grupos en los que se quiere hacer el análisis de amenaza por detonante sismo
grupo = QInputDialog.getInt(None, 'Número de grupos', 'Introduce el número de grupos en el que se quiere hacer el análisis para el detonante sismo: ')
grupo = grupo[0]

############################## PREPARACIÓN DE MOVIMIENTOS ##############################

#Movimientos en masa
Mov_Masa = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa.shp')

#Se reproyecta la capa a coordenadas planas
alg = "native:reprojectlayer"
CRS = QgsCoordinateReferenceSystem('EPSG:3116')
Reproyectada = data_path + '/Pre_Proceso/Mov_Masa_Reproyectada.shp'
params = {'INPUT': Mov_Masa, 'TARGET_CRS': CRS, 'OUTPUT': Reproyectada}
processing.run(alg, params)

#Se lee la nueva capa de MM
Mov_Masa = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Reproyectada.shp')

# Se inicia a editar la capa
caps = Mov_Masa.dataProvider().capabilities()
# Se añade los nuevos campos para las coordenadas
Mov_Masa.dataProvider().addAttributes([QgsField("X", QVariant.Double)])
Mov_Masa.dataProvider().addAttributes([QgsField("Y", QVariant.Double)])
# Se guarda la edición
Mov_Masa.updateFields()
   
# Se determina el índice de la columna que fue agregada
col_X = Mov_Masa.fields().indexFromName("X")
col_Y = Mov_Masa.fields().indexFromName("Y")

caps = Mov_Masa.dataProvider().capabilities()

for item in Mov_Masa.getFeatures():  # Se recorren las filas de la capa
    fid = item.id()  # Se obtiene el id de la fila en cuestión
    # Se obtiene la geometría del punto
    geometry = item.geometry()
    coordinate = geometry.asPoint()
    # A partir de la geometría se determinan las coordenadas
    X = coordinate[0]
    Y = coordinate[1]
    if caps & QgsVectorDataProvider.ChangeAttributeValues:
        # La columna nueva se llenará con las coordenadas
        attrs = { col_X : X, col_Y : Y }
        # Se hace el cambio de los atributos
        Mov_Masa.dataProvider().changeAttributeValues({fid: attrs})

#Se agrupan los movimientos por medio de un Cluster
alg = "native:kmeansclustering"
Cluster = data_path + '/Pre_Proceso/Mov_Masa_Cluster.shp'
params = {'INPUT': Mov_Masa,'CLUSTERS': grupo,'FIELD_NAME': 'CLUSTER_ID','OUTPUT': Cluster}
processing.run(alg, params)

#Se lee la nueva capa de MM
Mov_Masa = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Cluster.shp')

############################## MUESTREO DE SUSCEPTIBILIDAD ##############################

# Susceptibilidad por deslizamientos
Susceptibilidad_Deslizamientos = QgsRasterLayer(data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif', "Susceptibilidad_Deslizamientos")

#Se crean los poligonos de Voronoi dónde se espacializará la amenaza por lluvia
alg = "qgis:voronoipolygons"
Poligonos = data_path + '/Amenaza/Amenaza_Lluvia.shp'
params = {'INPUT': Estaciones, 'BUFFER':10, 'OUTPUT': Poligonos}
processing.run(alg, params)

# Se lee la capa resultante de los poligonos de Voronoi como un archivo vectorial
Poligonos = QgsVectorLayer(data_path + '/Amenaza/Amenaza_Lluvia.shp')

# Se inicia a editar la capa
caps = Poligonos.dataProvider().capabilities()
# Se añade un campo nuevo llamado "Raster"
# se asignará el valor único de cada caracteristica
Poligonos.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
# Se guarda la edición
Poligonos.updateFields()
   
# Se determina el índice de la columna que fue agregada
col = Poligonos.fields().indexFromName("Raster")
    
# Se obtienen los valores únicos de las caracteristicas
uniquevalues = []
uniqueprovider = Poligonos.dataProvider()
fields = uniqueprovider.fields()
id = fields.indexFromName(Codigo_Estacion)
atributos = uniqueprovider.uniqueValues(id)
df = pd.DataFrame(atributos)
    
# Se crea un datframe
DF_Raster = pd.DataFrame(columns=['Codigo', 'ID'], dtype=str)
    
# Se inicia a editar
caps = Poligonos.dataProvider().capabilities()
    
for i in range(0, len(atributos)):
    Atri = df.loc[i, 0]  # Caracteristica en cuestión
    DF_Raster.loc[i, 'Codigo'] = Atri  # Se llena el dataframe con la caracteristica
    DF_Raster.loc[i, 'ID'] = i+1  # Se llena el dataframe con el id
    # Se hace la selección en la capa de la caracteristica en cuestión
    Poligonos.selectByExpression(
        f'"{Codigo_Estacion}"=\'{Atri}\'', QgsVectorLayer.SetSelection)
        
    # Se reemplazan los id del atributo seleccionada
    selected_fid = []
    selection = Poligonos.selectedFeatures()
        
    for feature in selection:  # Se recorren las filas seleccionadas
        fid = feature.id()  # Se obtiene el id de la fila seleccionada
        if caps & QgsVectorDataProvider.ChangeAttributeValues:
            # La columna nueva se llenará con el id de la caracteristica (i+1)
            attrs = {col: i+1}
            # Se hace el cambio de los atributos
            Poligonos.dataProvider().changeAttributeValues({fid: attrs})
    
# Se guarda el raster y la capa vectorial
DF_Raster.reset_index().to_csv(
    data_path + '/Pre_Proceso/DF_Raster_Poligonos_Voronoi.csv', header=True, index=False)

#A partir del índice de los poligonos se hace su rasterización
alg = "gdal:rasterize"
Shape = Poligonos  # Nombre de la capa vectorial
Raster = data_path + '/Pre_Proceso/Poligonos_Voronoi.tif'  # Ruta y nombre del archivo de salida
Field = 'Raster'  # Columna con la cuál se hará la rasterización
extents = Susceptibilidad_Deslizamientos.extent()  # Capa de la cuál se copiará la extensión del algoritmo
xmin = extents.xMinimum()  # xmin de la extensión
xmax = extents.xMaximum()  # xmax de la extensión
ymin = extents.yMinimum()  # ymin de la extensión
ymax = extents.yMaximum()  # ymax de la extensión
params = {
    'INPUT': Shape, 'FIELD': Field, 'BURN': 0, 'UNITS': 1, 'WIDTH': 12.5,
    'HEIGHT': 12.5, 'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
    'NODATA': 0, 'OPTIONS': '', 'DATA_TYPE': 5, 'INIT': None, 'INVERT': False, 'OUTPUT': Raster}
processing.run(alg, params)

#Se muestrea el id de los poligonos
alg = "qgis:rastersampling"
rasterfile = data_path + '/Pre_Proceso/Poligonos_Voronoi.tif'
Mov_Masa_Amenaza_Poligono = data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Poligono.shp'
params = {'INPUT': Mov_Masa, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Poli_Voron', 'OUTPUT': Mov_Masa_Amenaza_Poligono}
processing.run(alg, params)
 
#Se muestrea la susceptibilidad por deslizamientos
alg = "qgis:rastersampling"
rasterfile = Susceptibilidad_Deslizamientos
Mov_Masa_Amenaza_Desliz = data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Desliz.shp'
params = {'INPUT': Mov_Masa_Amenaza_Poligono, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Susc_Desli', 'OUTPUT': Mov_Masa_Amenaza_Desliz}
processing.run(alg, params)

#Se guarda el archivo como CSV
Mov_Masa_Amenaza_Desliz = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Desliz.shp')
Archivo_csv = data_path + '/Amenaza/Mov_Masa_Amenaza.csv'
QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Amenaza_Desliz, Archivo_csv, "utf-8", Mov_Masa_Amenaza_Desliz.crs(), driverName = "CSV")

# Susceptibilidad por caídas
Ruta_Caidas = data_path + '/Resultados/Susceptibilidad_Caida.tif'
if os.path.isfile(Ruta_Caidas) is True:
    Susceptibilidad_Caidas = QgsRasterLayer(Ruta_Caidas, "Susceptibilidad_Caidas")
    
    #Se muestrea la susceptibilidad por caidas 
    alg = "qgis:rastersampling"
    rasterfile = Susceptibilidad_Caidas
    Mov_Masa_Amenaza_Caida = data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Caida.shp'
    params = {'INPUT': Mov_Masa_Amenaza_Desliz, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Susc_Caida', 'OUTPUT': Mov_Masa_Amenaza_Caida}
    processing.run(alg, params)
    
    #Se guarda el archivo como CSV
    Mov_Masa_Amenaza_Caida = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Caida.shp')
    Archivo_csv = data_path + '/Amenaza/Mov_Masa_Amenaza.csv'
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Amenaza_Caida, Archivo_csv, "utf-8", Mov_Masa_Amenaza_Caida.crs(), driverName = "CSV")

#Susceptibilidad por flujos
Ruta_Flujos = data_path + '/Resultados/Susceptibilidad_Flujos.tif'
if os.path.isfile(Ruta_Flujos) is True:
    Susceptibilidad_Flujos = QgsRasterLayer(Ruta_Caidas, "Susceptibilidad_Flujos")
    
    if os.path.isfile(Ruta_Caidas) is True:
        Shape = Mov_Masa_Amenaza_Caida
    else:
        Shape = Mov_Masa_Amenaza_Desliz

    #Se muestrea la susceptibilidad por flujos 
    alg = "qgis:rastersampling"
    rasterfile = Susceptibilidad_Flujos
    Mov_Masa_Amenaza_Flujo = data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Flujo.shp'
    params = {'INPUT': Shape, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Susc_Flujo', 'OUTPUT': Mov_Masa_Amenaza_Flujo}
    processing.run(alg, params)
    
    #Se guarda el archivo como CSV
    Mov_Masa_Amenaza_Flujo = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Flujo.shp')
    Archivo_csv = data_path + '/Amenaza/Mov_Masa_Amenaza.csv'
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Amenaza_Flujo, Archivo_csv, "utf-8", Mov_Masa_Amenaza_Flujo.crs(), driverName = "CSV")

############################## ANÁLISIS DE SISMOS ##############################

#Se reproyecta la capa a coordenadas planas
alg = "native:reprojectlayer"
CRS = QgsCoordinateReferenceSystem('EPSG:3116')
Reproyectada = data_path + '/Pre_Proceso/Sismos_Reproyectada.shp'
params = {'INPUT': Sismos, 'TARGET_CRS': CRS, 'OUTPUT': Reproyectada}
processing.run(alg, params)

# Se lee el nuevo archivo de Sismos
Sismos = QgsVectorLayer(data_path + '/Pre_Proceso/Sismos_Reproyectada.shp')

# Se inicia a editar la capa
caps = Sismos.dataProvider().capabilities()
# Se añade los nuevos campos para las coordenadas
Sismos.dataProvider().addAttributes([QgsField("X", QVariant.Double)])
Sismos.dataProvider().addAttributes([QgsField("Y", QVariant.Double)])
# Se guarda la edición
Sismos.updateFields()
   
# Se determina el índice de la columna que fue agregada
col_X = Sismos.fields().indexFromName("X")
col_Y = Sismos.fields().indexFromName("Y")

caps = Sismos.dataProvider().capabilities()

for item in Mov_Masa.getFeatures():  # Se recorren las filas de la capa
    fid = item.id()  # Se obtiene el id de la fila en cuestión
    # Se obtiene la geometría del punto
    geometry = item.geometry()
    coordinate = geometry.asPoint()
    # A partir de la geometría se determinan las coordenadas
    X = coordinate[0]
    Y = coordinate[1]
    if caps & QgsVectorDataProvider.ChangeAttributeValues:
        # La columna nueva se llenará con las coordenadas
        attrs = { col_X : X, col_Y : Y }
        # Se hace el cambio de los atributos
        Sismos.dataProvider().changeAttributeValues({fid: attrs})

#Se guarda el archivo como CSV de los sismos
Archivo_csv = data_path + '/Amenaza/Sismos.csv'
QgsVectorFileWriter.writeAsVectorFormat(Sismos, Archivo_csv, "utf-8", Sismos.crs(), driverName = "CSV")

#Se lee el csv y se unifican los nombres de los atributos
FILE_NAME = data_path + '/Amenaza/Sismos.csv'
Sismos = pd.read_csv(FILE_NAME, encoding = 'latin-1')
Sismos.rename(columns={Unidad_Sismo : 'Unidad'}, inplace=True)
Sismos.rename(columns={Magnitud_Sismo : 'Magnitud'}, inplace=True)

#Las unidades se unifican pasandolas a minuscula
Sismos['Unidad'] = Sismos['Unidad'].str.lower()

#Se crean los campos de los correpondientes autores
Sismos['Scordilis'] = None
Sismos['Grunthal'] = None
Sismos['Akkar'] = None
Sismos['Ulusay'] = None
Sismos['Kadirioglu'] = None

#Mb
Sismos.loc[Sismos["Unidad"].str.startswith('mb') & (Sismos.Magnitud >= 3.5) & (Sismos.Magnitud <= 6.2), 'Scordilis'] = 0.85 * Sismos.Magnitud + 1.03
Sismos.loc[Sismos["Unidad"].str.startswith('mb') & (Sismos.Magnitud <= 6.0), 'Grunthal'] = 8.17 - (42.04 - 6.42 * Sismos.Magnitud)**(1/2)
Sismos.loc[Sismos["Unidad"].str.startswith('mb') & (Sismos.Magnitud >= 3.5) & (Sismos.Magnitud <= 6.3), 'Akkar'] = 1.104 * Sismos.Magnitud - 0.194
Sismos.loc[Sismos["Unidad"].str.startswith('mb'), 'Ulusay'] = 1.2413 * Sismos.Magnitud - 0.8994
Sismos.loc[Sismos["Unidad"].str.startswith('mb') & (Sismos.Magnitud >= 3.9) & (Sismos.Magnitud <= 6.8), 'Kadirioglu'] = 1.0319 * Sismos.Magnitud + 0.0223

#Ml
Sismos.loc[Sismos["Unidad"].str.startswith('ml') & (Sismos.Magnitud >= 3.5) & (Sismos.Magnitud <= 5), 'Grunthal'] = 0.0376 * Sismos.Magnitud**(2) + 0.646 * Sismos.Magnitud + 0.53
Sismos.loc[Sismos["Unidad"].str.startswith('ml') & (Sismos.Magnitud >= 3.9) & (Sismos.Magnitud <= 6.8), 'Akkar'] = 0.953 * Sismos.Magnitud + 0.422
Sismos.loc[Sismos["Unidad"].str.startswith('ml'), 'Ulusay'] = 0.7768 * Sismos.Magnitud + 1.5921
Sismos.loc[Sismos["Unidad"].str.startswith('ml') & (Sismos.Magnitud >= 3.3) & (Sismos.Magnitud <= 6.6), 'Kadirioglu'] = 0.8095 * Sismos.Magnitud + 1.3003

#Md
Sismos.loc[Sismos["Unidad"].str.startswith('md') & (Sismos.Magnitud >= 3.7) & (Sismos.Magnitud <= 6), 'Akkar'] = 0.764 * Sismos.Magnitud + 1.379
Sismos.loc[Sismos["Unidad"].str.startswith('md'), 'Ulusay'] = 0.9495 * Sismos.Magnitud + 0.4181
Sismos.loc[Sismos["Unidad"].str.startswith('md') & (Sismos.Magnitud >= 3.5) & (Sismos.Magnitud <= 7.4), 'Kadirioglu'] = 0.7947 * Sismos.Magnitud + 1.342

#Ms
Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 3) & (Sismos.Magnitud <= 6.1), 'Scordilis'] = 0.67 * Sismos.Magnitud + 2.07
Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 6.2) & (Sismos.Magnitud <= 8.2), 'Scordilis'] = 0.99 * Sismos.Magnitud + 0.08
Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud <= 7), 'Grunthal'] = 10.85 - (73.74 - 8.34 * Sismos.Magnitud)**(1/2)
Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 3) & (Sismos.Magnitud <= 5.5), 'Akkar'] = 0.571 * Sismos.Magnitud + 2.484
Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 5.5) & (Sismos.Magnitud <= 7.7), 'Akkar'] = 0.817 * Sismos.Magnitud + 1.176
Sismos.loc[Sismos["Unidad"].str.startswith('ms'), 'Ulusay'] = 0.6798 * Sismos.Magnitud + 2.0402
Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 3.4) & (Sismos.Magnitud <= 5.4), 'Kadirioglu'] = 0.5716 * Sismos.Magnitud + 2.498
Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 5.5), 'Kadirioglu'] = 0.8126 * Sismos.Magnitud + 1.1723

#Se hace el promedio de los resultados para obtener Mw
Sismos['Magnitud_Mw'] = Sismos[['Scordilis', 'Grunthal', 'Akkar', 'Ulusay', 'Kadirioglu']].mean(axis=1)
Sismos.loc[Sismos["Unidad"].str.startswith('mw'), 'Magnitud_Mw'] = Sismos.Magnitud

#Se seleccionan los sismos con la magnitud mayor a la minima 
Sismo_Detonante = Sismos.loc[(Sismos.Magnitud_Mw >= 5)]
Sismo_Detonante.reset_index().to_csv(data_path + '/Amenaza/Sismos.csv', header = True, index = False)
print('Los sismos resultantes son: ')
print(Sismo_Detonante)

############################## DETERMINACIÓN DEL DETONANTE ##############################

#CSV de los sismos
FILE_NAME = data_path + '/Amenaza/Sismos.csv'
DF_Sismos = pd.read_csv(FILE_NAME, encoding = 'latin-1')
DF_Sismos['Fecha'] = pd.to_datetime(DF_Sismos.Fecha)

# CSV de los movimientos en masa leído como dataframe
FILE_NAME = data_path + '/Amenaza/Mov_Masa_Amenaza.csv'
DF_Mov_Masa = pd.read_csv(FILE_NAME, encoding = 'latin-1')
DF_Mov_Masa = DF_Mov_Masa.dropna(axis=0, subset=['FECHA_MOV'])
DF_Mov_Masa.reset_index(level=0, inplace=True)
DF_Mov_Masa['FECHA_MOV'] = pd.to_datetime(DF_Mov_Masa.FECHA_MOV)

# Se listan las fechas de MM con un respectivo umbral
DF_Fechas_MM = pd.DataFrame()
for i in range(0, len(DF_Mov_Masa)):
    date = DF_Mov_Masa.loc[i, 'FECHA_MOV']
    DF_Apoyo = pd.DataFrame()
    for j in range(0, dias):
        DF_Apoyo.loc[j, 'Indice'] = i
        DF_Apoyo.loc[j, 'Fecha'] = date - datetime.timedelta(days = j)
        DF_Apoyo.loc[j, 'Reporte'] = date
        DF_Apoyo.loc[j, 'X'] = DF_Mov_Masa.loc[i, 'X']
        DF_Apoyo.loc[j, 'Y'] = DF_Mov_Masa.loc[i, 'Y']
    DF_Fechas_MM = DF_Fechas_MM.append(DF_Apoyo)

DF_Fechas_MM.reset_index(level=0, inplace=True)

# Extraigo los valores únicos de las fechas
DF_Fechas_Mov = DF_Fechas_MM['Fecha'].unique()
DF_Fechas_Sismo = DF_Sismos['Fecha'].unique()

#Se hace la intersección de las fechas de MM y sismos, extrayendo las que coinciden
Fechas = set(DF_Fechas_Mov).intersection(set(DF_Fechas_Sismo)) 
Fechas = pd.DataFrame(Fechas, columns = ['date'])

# Se crea un dataframe para el llenado de los movimientos detonados por sismos
DF_Mov_Sismos = pd.DataFrame()
# Se recorren las fechas coincidentes de MM y sismo
for j in range (0, len(Fechas)):
    #Se determina la fecha
    Fecha = Fechas.loc[j, 'date']
    #Se determinan los índices de los sismos con la fecha en cuestión
    Indices = DF_Sismos[DF_Sismos['Fecha'] == Fecha].index
    DF_Fechas['Distancia'] = None
    #Se recorren los índices de los sismos ocurridos en la fecha
    for i in range (0,len(Indices)):
        #Se extraen las coordenadas del sismos correspondientes al índice
        X_Sismo = DF_Sismos.loc[Indices[i], 'X']
        Y_Sismo = DF_Sismos.loc[Indices[i], 'Y']
        # Se cálcula la distancia entre el sismos y los MM ocurridos en la fecha
        DF_Fechas.loc[DF_Fechas['Fecha'] == Fecha, 'Distancia'] = ((DF_Fechas.X - X_Sismo)**(2) + (DF_Fechas.Y - Y_Sismo)**(2))**(1/2)
        
        #Se seleccionan los MM a una distancia menor de 50 km
        DF_Escogido = DF_Fechas.loc[DF_Fechas['Distancia'] < 50000] #50 km - 50000 m
        DF_Fechas.drop(['Distancia'], axis=1)
        
    #Se va llenando el dataframe a medida que se recorren las fechas de intersección
    DF_Mov_Sismos = DF_Mov_Sismos.append(DF_Escogido)

# Se extraen los índices únicos de los MM resultantes
Indices_Mov = DF_Mov_Sismos['Indice'].unique()
Indices_Mov = Indices_Mov.tolist()

# Se crea un nuevo campo de detonante en el inventario
DF_Mov_Masa['Detonante'] = None
# Los MM de los índices únicos fueron detonados por un sismo
DF_Mov_Masa.loc[Indices_Mov, 'Detonante'] = "Sismo"
# Los MM restantes se asocian al detonante lluvia
DF_Mov_Masa.loc[DF_Mov_Masa.Detonante != "Sismo", 'Detonante'] = "Lluvia"

# Se determina el campo detonante cómo indice
DF_Mov_Masa.set_index('Detonante', inplace=True)
# Se parte el dataframe con base en el detonante
DF_Mov_Masa_Sismos = DF_Mov_Masa.loc['Sismo']
DF_Mov_Masa_Lluvias = DF_Mov_Masa.loc['Lluvia']
DF_Mov_Masa.reset_index(level=0, inplace=True)

# Se exporta como csv los MM
DF_Mov_Masa.reset_index(level=0, inplace=True)
DF_Mov_Masa.reset_index().to_csv(data_path + '/Amenaza/Mov_Masa_Amenaza.csv', header = True, index = False)

# Se exporta como csv los MM detonados por sismo
DF_Mov_Masa_Sismos.reset_index(level=0, inplace=True)
print(DF_Mov_Masa_Sismos)
DF_Mov_Masa_Sismos.reset_index().to_csv(data_path + '/Pre_Proceso/DF_Mov_Masa_Sismos.csv', header = True, index = False)

# Se exporta como csv los MM detonados por lluvia
DF_Mov_Masa_Lluvias.reset_index(level=0, inplace=True)
print(DF_Mov_Masa_Lluvias)
DF_Mov_Masa_Lluvias.reset_index().to_csv(data_path + '/Pre_Proceso/DF_Mov_Masa_Lluvias.csv', header = True, index = False)

#Se imprime el tiempo en el que se llevo a cambo la programación
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)




