"""
@author: Nicole Alejadra Rodríguez Vargas
@mail: nicole.rodriguez@correo.uis.edu.co
"""

"""
En esta programación se desarrollan los insumos para las posteriores programaciones del análisis de
susceptibilidad, en esta etapa se hace la rasterización de los factores condicionantes discretos
los cuales entran como capas vectoriales, además se extraen los deslizamientos y caídas, también
se preparan los movimientos en masa como geometría de puntos para ser empleados posteriormente en
el análisis de amenaza.
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

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
if ok == False:
    raise Exception('Cancelar')
data_path = data_path.replace("\\", "/")

# Se listan los archivos en la ruta general
list = listdir(data_path)

#Se imprime una recomendación
QMessageBox.information(iface.mainWindow(), "!Tenga en cuenta!",
                        'Se recomienda que el campo representativo para los factores condicionantes corresponda a acronimos '
                        'de forma que no haya interferencia con caracteres que Qgis no distinga tales como ñ y tildes; además, '
                        'en el caso de las subunidades geomorfologicas es necesario que estos despues coincidan con las '
                        'subunidades indicativas de procesos como flujo y caidas')
QMessageBox.information(iface.mainWindow(), "!Tenga en cuenta!",
                        'Se recomienda que si ya se ha ejecutado el programa con anterioridad sean borrados los archivos '
                        'que este genera para evitar conflictos al reemplazar los archivos pre-existentes en especial los .shp')
QMessageBox.information(iface.mainWindow(), "!Tenga en cuenta!",
                        'Es necesario que todos los tipos de deslizamiento estén unificados en un solo tipo, de igual forma con las caidas')

# Se determinan los archivos con extensión .shp en la ruta
shape = []
for i in list:
    if i[-4:] == '.shp':
        shape.append(i)
shape.append('None')

# Se determinan los archivos con extensión .tif en la ruta
raster = []
for i in list:
    if i[-4:] == '.tif':
        raster.append(i)
raster.append('None')

# Se comprueba si las carpetas de pre-proceso, resultados y amenaza existen
# de no ser así se crean
if os.path.isdir(data_path + '/Pre_Proceso') is False:
    os.mkdir(data_path + '/Pre_Proceso')

if os.path.isdir(data_path + '/Resultados') is False:
    os.mkdir(data_path + '/Resultados')
    
if os.path.isdir(data_path + '/Amenaza') is False:
    os.mkdir(data_path + '/Amenaza')

# Se piden las entradas necesarias para la ejecución: 
# Capas vectoriales de los factores condicionante

# Movimientos en masa tipo puntos
Mov_Masa_Puntos, ok = QInputDialog.getItem(None, "Movimientos en masa tipo PUNTOS",
                                           "Seleccione el archivo de movimientos en masa con geometría de puntos", shape, 0, False)
if ok == False:
    raise Exception('Cancelar')
Ruta_Mov_Masa_Puntos = data_path + '/' + Mov_Masa_Puntos

# Se determina si existe el archivo de MM 
if os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
    Mov_Masa_Puntos = QgsVectorLayer(data_path + '/' + Mov_Masa_Puntos)
    
    # Se listan los atributos del arhivo vectorial
    atributos_Mov_Masa_Puntos = []
    for field in Mov_Masa_Puntos.fields():
        atributos_Mov_Masa_Puntos.append(field.name())
        
    # Campo dónde se encuentra el tipo de movimiento en masa para la capa de puntos
    Campo_Puntos, ok = QInputDialog.getItem(None, "Tipo de movimiento en masa",
                                            "Campo del tipo de movimiento en masa con geometría de punto", atributos_Mov_Masa_Puntos, 0, False)
    if ok == False:
        raise Exception('Cancelar')
        
    # Se obtienen los valores únicos de las caracteristicas
    uniquevalues = []
    uniqueprovider = Mov_Masa_Puntos.dataProvider()
    fields = uniqueprovider.fields()
    id = fields.indexFromName(Campo_Puntos)
    atributos_MM = uniqueprovider.uniqueValues(id)
    
    # Campo dónde se encuentra la fecha del movimiento en masa para la capa de puntos
    Fecha_Puntos, ok = QInputDialog.getItem(None, "Fecha de movimiento en masa",
                                            "Campo de la fecha de movimiento en masa con geometría de punto", atributos_Mov_Masa_Puntos, 0, False)
    if ok == False:
        raise Exception('Cancelar')

# Movimientos en masa tipo poligonos
Mov_Masa_Poligono, ok = QInputDialog.getItem(None, "Movimientos en masa tipo POLIGONO",
                                             "Seleccione el archivo de movimientos con geometría de poligonos", shape, 0, False)
if ok == False:
    raise Exception('Cancelar')
Ruta_Mov_Masa_Poligono = data_path + '/' + Mov_Masa_Poligono

#Se determina si existe el archivo de MM 
if os.path.isfile(Ruta_Mov_Masa_Poligono) is True:
    Mov_Masa_Poligono = QgsVectorLayer(data_path + '/' + Mov_Masa_Poligono)
    
    # Se listan los atributos del arhivo vectorial
    atributos_Mov_Masa_Poligono = []
    for field in Mov_Masa_Poligono.fields():
        atributos_Mov_Masa_Poligono.append(field.name())
        
    # Campo dónde se encuentra el tipo de movimiento en masa para la capa de poligonos
    Campo_Poligono, ok = QInputDialog.getItem(None, "Tipo de movimiento en masa",
                                              "Campo del tipo de movimiento en masa con geometría de poligono", atributos_Mov_Masa_Poligono, 0, False)
    if ok == False:
        raise Exception('Cancelar')
        
    # Se obtienen los valores únicos de las caracteristicas
    uniquevalues = []
    uniqueprovider = Mov_Masa_Poligono.dataProvider()
    fields = uniqueprovider.fields()
    id = fields.indexFromName(Campo_Poligono)
    atributos_MM = uniqueprovider.uniqueValues(id)
    
    # Campo dónde se encuentra el tipo de movimiento en masa para la capa de poligonos
    Fecha_Poligono, ok = QInputDialog.getItem(None, "Fecha de movimiento en masa",
                                              "Campo de la fecha de movimiento en masa con geometría de poligono", atributos_Mov_Masa_Poligono, 0, False)
    if ok == False:
        raise Exception('Cancelar')

# Se verifica si existen ambos archivos de MM
if os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
    if os.path.isfile(Ruta_Mov_Masa_Poligono) is True:
        # Se revisa que los campos del tipo de MM y de la fecha de ocurrencia coincidan para ambas capas vectoriales
        if Campo_Puntos != Campo_Poligono:
            QMessageBox.critical(iface.mainWindow(), "Campo del tipo de MM",
                                 'Los campos del tipo de MM de las capas de movimientos debe ser iguales')
        if Fecha_Puntos != Fecha_Poligono:
            QMessageBox.critical(iface.mainWindow(), "Campo de la fecha de MM",
                                 'Los campos de la fecha de MM de las capas de movimientos debe ser iguales')

# MM tipo deslizamiento
Deslizamiento, ok = QInputDialog.getItem(
    None, 'MM tipo deslizamiento', 'Cómo están identificados los MM tipo deslizamiento',
    atributos_MM, 0, False)
if ok == False:
    raise Exception('Cancelar')

# MM tipo caida
Caida, ok = QInputDialog.getItem(
    None, 'MM tipo caida', 'Cómo están identificados los MM tipo caida',
    atributos_MM, 0, False)
if ok == False:
    raise Exception('Cancelar')

# MM tipo reptación
Reptacion, ok = QInputDialog.getItem(
    None, 'MM tipo reptación', 'Cómo están identificados los MM tipo reptación',
    atributos_MM, 0, False)
if ok == False:
    raise Exception('Cancelar')

# Dimensiones del pixel
cellsize, ok = QInputDialog.getDouble(
    None, 'Tamaño del pixel', 'Introduzca el tamaño del pixel: ')
if ok == False:
    raise Exception('Cancelar')

# ##################################### Factores Condicionantes ##################################### #

# Se define la función rasterize para la rasterización de los factores condicionantes con base en el campo representativo

def rasterize(Factor_Condicionante):
    # Se ingresa el archivo vectorial del factor condicionante
    Ruta_Factor, ok = QInputDialog.getItem(None, f"{Factor_Condicionante}", f"Seleccione el archivo de {Factor_Condicionante}", shape, 0, False)
    if ok == False:
        raise Exception('Cancelar')
    Ruta_Factor = data_path + '/' + Ruta_Factor
    
    # Si el archivo de Factor existe se hace el procedimiento
    if os.path.isfile(Ruta_Factor) is True:
        
        Factor = QgsVectorLayer(Ruta_Factor)
        
        # Se listan los atributos del arhivo vectorial
        atributos_Factor = []
        for field in Factor.fields():
            atributos_Factor.append(field.name())
        
        # Nombre del campo dónde se encuentran los códigos representativos de las Factor
        Codigo_Factor, ok = QInputDialog.getItem(None, f"Campo representativo de las {Factor_Condicionante}", f"Seleccione el campo representativo de las {Factor_Condicionante}", atributos_Factor, 0, False)
        if ok == False:
            raise Exception('Cancelar')
            
        # Se hace la corrección geometrica del factor condicionantes.
        alg = "native:fixgeometries"
        Factor_Corr = data_path + f'/Pre_Proceso/{Factor_Condicionante}_Corr.shp'
        params = {'INPUT': Factor, 'OUTPUT': Factor_Corr}
        processing.run(alg, params)
    
        # La capa corregida se lee como una capa vectorial
        Factor = QgsVectorLayer(data_path + f'/Pre_Proceso/{Factor_Condicionante}_Corr.shp', f'{Factor_Condicionante}')
        
        # Se inicia a editar la capa
        caps = Factor.dataProvider().capabilities()
        # Se añade un campo nuevo llamado "Raster"
        # dónde se asignará el valor único de cada aracteristica
        Factor.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
        # Se guarda la edición
        Factor.updateFields()
       
        # Se determina el índice de la columna que fue agregada
        col = Factor.fields().indexFromName("Raster")
        
        # Se obtienen los valores únicos de las caracteristicas
        uniquevalues = []
        uniqueprovider = Factor.dataProvider()
        fields = uniqueprovider.fields()
        id = fields.indexFromName(Codigo_Factor)
        atributos = uniqueprovider.uniqueValues(id)
        df = pd.DataFrame(atributos, dtype = 'str')
        print(atributos)
        
        # Se crea un datframe
        DF_Raster = pd.DataFrame(columns=['Caract', 'ID'], dtype = float)
        
        # Se inicia a editar
        caps = Factor.dataProvider().capabilities()
        
        for i in range(0, len(atributos)):
            Atri = df.loc[i, 0]  # Caracteristica en cuestión
            DF_Raster.loc[i, 'Caract'] = Atri  # Se llena el dataframe con la caracteristica
            DF_Raster.loc[i, 'ID'] = i+1  # Se llena el dataframe con el id correspondiente
            # Se obtienen las dos primeras letras de su acronimo (Se utilizará en las UGS)
            DF_Raster.loc[i, 'General'] = Atri[0:2]
            # Se hace la selección en la capa de la caracteristica en cuestión
            Factor.selectByExpression(f'"{Codigo_Factor}"=\'{Atri}\'', QgsVectorLayer.SetSelection)
            
            # Se define cuál es la selección
            selected_fid = []
            selection = Factor.selectedFeatures()
            
            for feature in selection:  # Se recorren las filas seleccionadas
                fid = feature.id()  # Se obtiene el id de la fila seleccionada
                if caps & QgsVectorDataProvider.ChangeAttributeValues:
                    # La columna nueva se llenará con el id de la caracteristica (i+1)
                    attrs = {col: i+1}
                    # Se hace el cambio de los atributos
                    Factor.dataProvider().changeAttributeValues({fid: attrs})
        
        # Se guarda el raster y la capa vectorial
        print(DF_Raster)
        DF_Raster.reset_index().to_csv(data_path + f'/Pre_Proceso/DF_Raster_{Factor_Condicionante}.csv', header=True, index=False)
        
        # Se hace la respectiva rasterización del factor condicionante
        alg = "gdal:rasterize"
        Shape = Factor  # Nombre de la capa vectorial
        Raster = data_path + f'/Pre_Proceso/{Factor_Condicionante}.tif'  # Ruta y nombre del archivo de salida
        Field = 'Raster'  # Columna con la cuál se hará la rasterización
        extents = Factor.extent()  # Capa de la cuál se copiará la extensión del algoritmo
        xmin = extents.xMinimum()  # xmin de la extensión
        xmax = extents.xMaximum()  # xmax de la extensión
        ymin = extents.yMinimum()  # ymin de la extensión
        ymax = extents.yMaximum()  # ymax de la extensión
        params = {'INPUT': Shape, 'FIELD': Field, 'BURN': 0, 'UNITS': 1, 'WIDTH': cellsize, 'HEIGHT': cellsize,
                  'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax), 'NODATA': 0, 'OPTIONS': '', 'DATA_TYPE': 5,
                  'INIT': None, 'INVERT': False, 'OUTPUT': Raster}
        processing.run(alg, params)
        
        # Se añade la capa raster al lienzo
        iface.addRasterLayer(data_path + f'/Pre_Proceso/{Factor_Condicionante}.tif', f"{Factor_Condicionante}")
   
    # Si la capa no existe se emite un mensaje
    else:
        iface.messageBar().pushMessage(
            "Factor condicionante", f'No hay archivo de {Factor_Condicionante}', Qgis.Info, 5)

# Lista de los factores condicionantes continuos
Factor_Condicionante = ['UGS', 'SubunidadesGeomorf', 'CoberturaUso', 'CambioCobertura']

# Se recorre la lista de factores condicionates continuos
for factor in Factor_Condicionante:
    # Se implementa la función rasterize para cada factor
    rasterize(factor)

# ####################### Movimientos en Masa ####################### #    
 
# Se genera el mapa de deslizamientos dependiendo de los archivos base que se tengan

# Se determina si hay mapa de poligonos de movimientos en masa
if os.path.isfile(Ruta_Mov_Masa_Poligono) is True:
    
    # Se hace la corrección geometrica de la capa.
    alg = "native:fixgeometries"
    Mov_Masa_Corr = data_path + '/Pre_Proceso/Mov_Masa_Corr.shp'
    params = {'INPUT': Ruta_Mov_Masa_Poligono, 'OUTPUT': Mov_Masa_Corr}
    processing.run(alg, params)
    
    # Se seleccionan los movimientos en masa tipo deslizamiento y se guardan
    Mov_Masa_Corr = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Corr.shp', 'Mov_Masa_Corr')
    CRS = Mov_Masa_Corr.crs().authid()
    Mov_Masa_Corr.selectByExpression(f'"{Campo_Poligono}"=\'{Deslizamiento}\'', QgsVectorLayer.SetSelection)
    Desliz_Poligonos = data_path + '/Pre_Proceso/Desliz_Poligonos.shp'
    QgsVectorFileWriter.writeAsVectorFormat(
        Mov_Masa_Corr, Desliz_Poligonos, "utf-8", 
        QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
    
    # Se seleccionan los movimientos en masa tipo caída y se guardan
    Mov_Masa_Corr.selectByExpression(f'"{Campo_Poligono}"=\'{Caida}\'', QgsVectorLayer.SetSelection)
    Caida_poligonos = data_path + '/Pre_Proceso/Caida_poligonos.shp'
    QgsVectorFileWriter.writeAsVectorFormat(
        Mov_Masa_Corr, Caida_poligonos, "utf-8", 
        QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
        
    # Se seleccionan los movimientos en masa tipo reptación y se guardan
    Mov_Masa_Corr.selectByExpression(f'"{Campo_Poligono}"=\'{Reptacion}\'', QgsVectorLayer.SetSelection)
    Reptacion_poligonos = data_path + '/Pre_Proceso/Reptacion_poligonos.shp'
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Corr, Reptacion_poligonos, "utf-8", 
        QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
        
    #Se generan puntos en los centroides de los movimientos en masa
    alg = "native:centroids"
    Mov_Masa_poligonos = data_path + '/Pre_Proceso/Mov_Masa_poligonos.shp'
    params = {'INPUT': Mov_Masa_Corr, 'ALL_PARTS': True, 'OUTPUT': Mov_Masa_poligonos}
    processing.run(alg, params)
    
    # Se determina si también hay mapa de puntos
    if os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
        Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos, 'Mov_Masa_Puntos')
        
        #Se define cómo se quiere hacer el tratamiento de los deslizamientos tipo poligonos
        items = ("Centroides de pixeles", "Centroides de poligonos")
        item, ok = QInputDialog.getItem(None, "Análisis de los poligonos", "Seleccione el método de análisis de los poligonos", items, 0, False)
        if ok == False:
            raise Exception('Cancelar')
            
        if item == 'Centroides de pixeles':
            # Se generan puntos en los poligonos en los centroides de los pixeles
            # Se basa en los pixeles del raster de Factor el cuál es un factor que siempre debe tenerse
            Raster = data_path + '/Pre_Proceso/UGS.tif'
            alg = "qgis:generatepointspixelcentroidsinsidepolygons"
            Deslizamientos_poligonos = data_path + '/Pre_Proceso/Deslizamientos_poligonos.shp'
            params = {'INPUT_RASTER': Raster, 'INPUT_VECTOR': Desliz_Poligonos, 'OUTPUT': Deslizamientos_poligonos}
            processing.run(alg, params)
            
        else:
            #Se generan puntos en los centroides de los poligonos 
            alg = "native:centroids"
            Deslizamientos_poligonos = data_path+'/Pre_Proceso/Deslizamientos_poligonos.shp'
            params = {'INPUT': Desliz_Poligonos, 'ALL_PARTS': True, 'OUTPUT': Deslizamientos_poligonos}
            processing.run(alg, params)
        
        # Se seleccionan los deslizamientos y se guardan
        Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'{Deslizamiento}\'', QgsVectorLayer.SetSelection)
        CRS = Mov_Masa_Puntos.crs().authid()
        Deslizamientos_puntos = data_path+'/Pre_Proceso/Deslizamientos_puntos.shp'
        QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Deslizamientos_puntos, "utf-8", 
            QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
        
        # Se seleccionan las reptación y se guardan
        Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'{Reptacion}\'', QgsVectorLayer.SetSelection)
        Reptacion_puntos = data_path+'/Pre_Proceso/Reptacion_puntos.shp'
        QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Reptacion_puntos, "utf-8", 
            QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
            
        # Se seleccionan las caidas y se guardan
        Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'{Caida}\'', QgsVectorLayer.SetSelection)
        Caida_puntos = data_path+'/Pre_Proceso/Caida_puntos.shp'
        QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Caida_puntos, "utf-8", 
            QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)

        # Se lee como archivo vectorial los deslizamientos como puntos
        Deslizamientos_puntos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos_puntos.shp')
        Desliz_Poligonos = data_path + '/Pre_Proceso/Desliz_Poligonos.shp'
        
        # Se seleccionan los puntos que estén dentro de los poligonos
        alg = "native:selectbylocation"
        Puntos = Deslizamientos_puntos
        Poligonos = Desliz_Poligonos
        params = {'INPUT': Puntos, 'PREDICATE': [6], 'INTERSECT': Poligonos, 'METHOD': 0}
        processing.run(alg, params)
        
        # Se eliminan los puntos de la selección de forma que no queden sobrepuestos
        caps = Deslizamientos_puntos.dataProvider().capabilities()
        selected_fid = []
        selection = Deslizamientos_puntos.selectedFeatures()
        for feature in selection: 
            fid = feature.id() 
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                Deslizamientos_puntos.dataProvider().deleteFeatures([fid])
        
        # Se unen el mapa de puntos y los puntos generados a partir de los poligonos de deslizamientos
        alg = "native:mergevectorlayers"
        Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
        params = {'LAYERS': [Deslizamientos_poligonos, Deslizamientos_puntos], 'CRS':None, 'OUTPUT': Deslizamientos}
        processing.run(alg, params) 

        # Se unen el mapa de puntos y los puntos generados a partir de los poligonos de los movimientos
        alg = "native:mergevectorlayers"
        Mov_Masa = data_path + '/Pre_Proceso/Mov_Masa.shp'
        params = {'LAYERS': [Mov_Masa_poligonos, Mov_Masa_Puntos], 'CRS':None, 'OUTPUT': Mov_Masa}
        processing.run(alg, params)

    else:
        
        # Si no hay un mapa de puntos entonces el mapa de poligonos se guarda como deslizamientos
        Desliz_Poligonos = QgsVectorLayer(data_path + '/Pre_Proceso/Desliz_Poligonos.shp')
        Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
        CRS = Desliz_Poligonos.crs().authid()
        QgsVectorFileWriter.writeAsVectorFormat(Desliz_Poligonos, Deslizamientos, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")
        
        # Si no hay un mapa de puntos entonces el mapa de poligonos se guarda como movimientos
        Mov_Masa_poligonos = QgsVectorLayer(data_path+'/Pre_Proceso/Mov_Masa_poligonos.shp')
        Mov_Masa = data_path + '/Pre_Proceso/Mov_Masa.shp'
        CRS = Desliz_Poligonos.crs().authid()
        QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_poligonos, Mov_Masa, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")
        
        
elif os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
    
    # Si no hay mapa de poligonos se guarda la selección de deslizamientos
    Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos, 'Mov_Masa_Puntos')
    Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'{Deslizamiento}\'', QgsVectorLayer.SetSelection)
    CRS = Mov_Masa_Puntos.crs().authid()
    Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Deslizamientos, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
    
    # Si no hay mapa de poligonos se guarda la selección de caidas
    Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'{Caida}\'', QgsVectorLayer.SetSelection)
    Caida_puntos = data_path+'/Pre_Proceso/Caida_puntos.shp'
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Caida_puntos, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
    
    # Si no hay mapa de poligonos se guarda la selección de reptación
    Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'{Reptacion}\'', QgsVectorLayer.SetSelection)
    Reptacion_puntos = data_path+'/Pre_Proceso/Reptacion_puntos.shp'
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Reptacion_puntos, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
    
    
    # Si no hay un mapa de poligonos entonces el mapa de puntos se guarda como movimientos
    Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos, 'Mov_Masa_Puntos')
    Mov_Masa = data_path + '/Pre_Proceso/Mov_Masa.shp'
    CRS = Mov_Masa_Puntos.crs().authid()
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Mov_Masa, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")
    
else:
    # Si no hay mapas de ningún tipo se genera un aviso porque es necesario
    iface.messageBar().pushMessage("Movimientos en masa", 'No hay archivo de movimientos en masa', Qgis.Warning, 10)

# Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)
    

