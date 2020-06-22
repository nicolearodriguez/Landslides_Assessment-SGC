from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant
from qgis.gui import QgsMessageBar
from qgis.core import QgsProject
import pandas as pd
import numpy as np
import processing
import os

# Ruta general de la ubicación de los archivos
data_path = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
data_path = data_path[0]
data_path = data_path.replace("\\", "/")

# Se comprueba si las carpetas de pre-proceso y resultados existen
# de no ser así se crean
if os.path.isdir(data_path + '/Pre_Proceso') is False:
    os.mkdir(data_path + '/Pre_Proceso')

if os.path.isdir(data_path + '/Resultados') is False:
    os.mkdir(data_path + '/Resultados')

# Se piden las entradas necesarias para la ejecución-DEM del área de estudio
# y capas vectoriales de los factores condicionante

# Modelo digital de elevación
DEM = QInputDialog.getText(
    None, 'DEM', 'Nombre del DEM con extensión (xxx.tif): ')
DEM = DEM[0]
Ruta_DEM = data_path + '/' + DEM

# Unidades geologicas superficiales
Ruta_UGS = QInputDialog.getText(
    None, 'UGS',
    'Nombre del archivo UGS con extensión (xxx.shp): ')
Ruta_UGS = Ruta_UGS[0]
UGS = data_path + '/' + Ruta_UGS

# Nombre del campo dónde se encuentran los códigos representativos de las UGS
Codigo_UGS = QInputDialog.getText(
    None, 'UGS', 'Nombre del campo representativo de las UGS: ')
Codigo_UGS = Codigo_UGS[0]

# Subunidades geomorfologicas
Ruta_SubunidadesGeomorf = QInputDialog.getText(
    None, 'Subunidades',
    'Nombre del archivo de subunidades geomorfologicas con extensión (xxx.shp): ')
Ruta_SubunidadesGeomorf = Ruta_SubunidadesGeomorf[0]
SubunidadesGeomorf = data_path + '/' + Ruta_SubunidadesGeomorf

# Campo dónde se encuentran los códigos representativos de las subunidades
Codigo_SubunidadesGeomorf = QInputDialog.getText(
    None, 'Subunidades',
    'Nombre del campo representativo de las Subunidades: ')
Codigo_SubunidadesGeomorf = Codigo_SubunidadesGeomorf[0]

# Uso y cobertura del suelo
Ruta_CoberturaUso = QInputDialog.getText(
    None, 'Cobertura-Uso',
    'Nombre del archivo de cobertura y uso con extensión (xxx.shp): ')
Ruta_CoberturaUso = Ruta_CoberturaUso[0]
CoberturaUso = data_path + '/' + Ruta_CoberturaUso

# Nombre del campo dónde se encuentran los códigos representativos
Codigo_CoberturaUso = QInputDialog.getText(
    None, 'Cobertura-Uso',
    'Nombre del campo representativo de la Cobertura-Uso: ')
Codigo_CoberturaUso = Codigo_CoberturaUso[0]

# Cambio de cobertura del suelo
Ruta_CambioCobertura = QInputDialog.getText(
    None, 'Cambio Cobertura',
    'Nombre del archivo de cambio de cobertura con extensión (xxx.shp): ')
Ruta_CambioCobertura = Ruta_CambioCobertura[0]
CambioCobertura = data_path + '/' + Ruta_CambioCobertura

# Campo dónde se encuentran los códigos representativos del cambio de cobertura
Codigo_CambioCobertura = QInputDialog.getText(
    None, 'Cambio de Cobertura',
    'Nombre del campo representativo de Cambio de Cobertura: ')
Codigo_CambioCobertura = Codigo_CambioCobertura[0]

# Movimientos en masa tipo puntos
Mov_Masa_Puntos = QInputDialog.getText(
    None, 'Movimientos en masa',
    'Capa de movimientos en masa tipo PUNTOS con extensión (xxx.shp): ')
Mov_Masa_Puntos = Mov_Masa_Puntos[0]
Ruta_Mov_Masa_Puntos = data_path + '/' + Mov_Masa_Puntos

# Campo dónde se encuentra el tipo de movimiento en masa para la capa de puntos
Campo_Puntos = QInputDialog.getText(
    None, 'Tipo de movimientos en masa',
    'Nombre del campo dónde está el tipo de movimiento en masa para PUNTOS: ')
Campo_Puntos = Campo_Poligono[0]

# Movimientos en masa tipo poligonos
Mov_Masa_Poligono = QInputDialog.getText(
    None, 'Movimientos en masa',
    'Capa de movimientos en masa tipo POLIGONOS con extensión (xxx.shp): ')
Mov_Masa_Poligono = Mov_Masa_Poligono[0]
Ruta_Mov_Masa_Poligono = data_path + '/' + Mov_Masa_Poligono

# Campo dónde se encuentra el tipo de movimiento en masa para la capa de poligonos
Campo_Poligono = QInputDialog.getText(
    None, 'Tipo de movimientos en masa',
    'Campo dónde está el tipo de movimiento en masa para POLIGONOS: ')
Campo_Poligono = Campo_Poligono[0]

# Dimensiones del pixel
Pixel = QInputDialog.getDouble(
    None, 'CELLSIZE', 'Introduce el tamaño del pixel: ')
cellsize = Pixel[0]

# ########################## PENDIENTE/CURVATURA ########################## #

# Cambio de tamaño de pixel
DEM = QgsRasterLayer(Ruta_DEM)

pipe = QgsRasterPipe()
extent = DEM.extent()
width_layer = DEM.width()
height_layer = DEM.height()
X = DEM.rasterUnitsPerPixelX()
Y = DEM.rasterUnitsPerPixelY()
width = (X/cellsize)*width_layer
height = (Y/cellsize)*height_layer
renderer = DEM.renderer()
provider = DEM.dataProvider()
crs = DEM.crs().toWkt()
pipe.set(provider.clone())
pipe.set(renderer.clone())
file_writer = QgsRasterFileWriter(data_path+'/Pre_Proceso/DEM_reproyectado.tif')
file_writer.writeRaster(pipe, width, height, extent, layer.crs())

# Pendiente
DEM = QgsRasterLayer(data_path+'/Pre_Proceso/DEM_reproyectado.tif')
# Se genera el mapa de pendientes
alg = "gdal:slope"
Pendiente = data_path+'/Pre_Proceso/Pendiente.tif'
params = {
    'INPUT': DEM, 'BAND': 1, 'SCALE': 1, 'AS_PERCENT': False, 'COMPUTE_EDGES': False,
    'ZEVENBERGEN': False, 'OPTIONS': '', 'EXTRA': '', 'OUTPUT': Pendiente}
processing.run(alg, params)
iface.addRasterLayer(data_path+'/Pre_Proceso/Pendiente.tif', "Pendiente")

# Curvatura

# ##################################### UGS ##################################### #

# Si el archivo de UGS existe se hace el procedimiento
if os.path.isfile(UGS) is True:
    # Se hace la corrección geometrica del factor condicionantes.
    UGS_Corr = data_path+'/Pre_Proceso/UGS_Corr.shp'
    processing.run("native:fixgeometries", {'INPUT': UGS, 'OUTPUT': UGS_Corr})

    # La capa corregida se lee como una capa vectorial
    UGS = QgsVectorLayer(data_path+'/Pre_Proceso/UGS_Corr.shp', 'UGS')
    
    # Se inicia a editar la capa
    caps = UGS.dataProvider().capabilities()
    # Se añade un campo nuevo llamado "Raster"
    # se asignará el valor único de cada aracteristica
    UGS.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
    # Se guarda la edición
    UGS.updateFields()
   
    # Se determina el índice de la columna que fue agregada
    col = UGS.fields().indexFromName("Raster")
    
    # Se obtienen los valores únicos de las caracteristicas
    uniquevalues = []
    uniqueprovider = UGS.dataProvider()
    fields = uniqueprovider.fields()
    id = fields.indexFromName(Codigo_UGS)
    uniquevalues = uniqueprovider.uniqueValues(id)
    atributos = list(uniquevalues)
    print(atributos)
    
    # Se crea un datframe
    DF_Raster = pd.DataFrame(columns=['Caract', 'ID'], dtype=float)
    
    # Se inicia a editar
    caps = UGS.dataProvider().capabilities()
    
    for i in range(0, len(atributos)):
        Atri = atributos[i]  # Caracteristica en cuestión
        DF_Raster.loc[i, 'Caract'] = Atri  # Se llena el dataframe con la caracteristica
        DF_Raster.loc[i, 'ID'] = i+1  # Se llena el dataframe con el id
        # Para el caso de las UGS se obtienen las dos primeras letras de su acronimo
        DF_Raster.loc[i, 'General'] = Atri[0:2]
        # Se hace la selección en la capa de la caracteristica en cuestión
        UGS.selectByExpression(
            f'"{Codigo_UGS}"=\'{Atri}\'', QgsVectorLayer.SetSelection)
        
        # Se reemplazan los id del atributo seleccionada
        selected_fid = []
        selection = UGS.selectedFeatures()
        
        for feature in selection:  # Se recorren las filas seleccionadas
            fid = feature.id()  # Se obtiene el id de la fila seleccionada
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                # La columna nueva se llenará con el id de la caracteristica (i+1)
                attrs = {col: i+1}
                # Se hace el cambio de los atributos
                UGS.dataProvider().changeAttributeValues({fid: attrs})
    
    # Se guarda el raster y la capa vectorial
    print(DF_Raster)
    DF_Raster.reset_index().to_csv(
        data_path+'/Pre_Proceso/DF_Raster_UGS.csv', header=True, index=False)
    
    # Se hace la respectiva rasterización del factor condicionante
    alg = "gdal:rasterize"
    Shape = UGS  # Nombre de la capa vectorial
    Raster = data_path+'/Pre_Proceso/UGS.tif'  # Ruta y nombre del archivo de salida
    Field = 'Raster'  # Columna con la cuál se hará la rasterización
    extents = UGS.extent()  # Capa de la cuál se copiará la extensión del algoritmo
    xmin = extents.xMinimum()  # xmin de la extensión
    xmax = extents.xMaximum()  # xmax de la extensión
    ymin = extents.yMinimum()  # ymin de la extensión
    ymax = extents.yMaximum()  # ymax de la extensión
    params = {
        'INPUT': Shape, 'FIELD': Field, 'BURN': 0, 'UNITS': 1, 'WIDTH': cellsize,
        'HEIGHT': cellsize, 'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
        'NODATA': 0, 'OPTIONS': '', 'DATA_TYPE': 5, 'INIT': None, 'INVERT': False,
        'OUTPUT': Raster}
    processing.run(alg, params)
    
    # Se añade la capa raster al lienzo
    iface.addRasterLayer(data_path + '/Pre_Proceso/UGS.tif', "UGS")

else:
    iface.messageBar().pushMessage(
        "Factor condicionante", 'No hay archivo de UGS', Qgis.Info, 5)

# ##################### Subunidades Geomorfologicas ##################### #

# Si el archivo de subunidades existe se hace el procedimiento
if os.path.isfile(SubunidadesGeomorf) is True:
    # Se hace la corrección geometrica del factores condicionantes.
    SubunidadesGeomorf_Corr = data_path + '/Pre_Proceso/SubunidadesGeomorf_Corr.shp'
    processing.run(
        "native:fixgeometries", 
        {'INPUT': SubunidadesGeomorf, 'OUTPUT': SubunidadesGeomorf_Corr})
    
    # La capa corregida se lee como una capa vectorial
    SubunidadesGeomorf = QgsVectorLayer(
        data_path + '/Pre_Proceso/SubunidadesGeomorf_Corr.shp',
        'Subunidades Geomorfologicas')
    
    # Se inicia a editar la capa
    caps = SubunidadesGeomorf.dataProvider().capabilities()
    # Se añade un campo nuevo llamado "Raster"
    # se asignará el valor único ce cada aracteristica para la posterior rasterización
    SubunidadesGeomorf.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
    # Se guarda la edición
    SubunidadesGeomorf.updateFields()
    
    # Se determina el índice de la columna que fue agregada
    col = SubunidadesGeomorf.fields().indexFromName("Raster")
    
    # Valores unicos del factor condicionante
    uniquevalues = []
    uniqueprovider = SubunidadesGeomorf.dataProvider()
    fields = uniqueprovider.fields()
    id = fields.indexFromName(Codigo_SubunidadesGeomorf)
    uniquevalues = uniqueprovider.uniqueValues(id)
    atributos = list(uniquevalues)
    print(atributos)
    
    # Se crea un datframe
    DF_Raster = pd.DataFrame(columns=['Caract', 'ID'], dtype=float)
    
    # Se inicia a editar
    caps = SubunidadesGeomorf.dataProvider().capabilities()
    
    for i in range(0, len(atributos)):
        Atri = atributos[i]  # Caracteristica en cuestión
        DF_Raster.loc[i, 'Caract'] = Atri  # Se llena el dataframe con la caracteristica
        DF_Raster.loc[i, 'ID'] = i+1  # Se llena el dataframe con el id
        # Se hace la selección en la capa de la caracteristica en cuestión
        SubunidadesGeomorf.selectByExpression(
            f'"{Codigo_SubunidadesGeomorf}"=\'{Atri}\'',
            QgsVectorLayer.SetSelection)
        
        # Se reemplazan los id del atributo seleccionada
        selected_fid = []
        selection = SubunidadesGeomorf.selectedFeatures()
        
        for feature in selection:  # Se recorren las filas seleccionadas
            fid = feature.id()  # Se obtiene el id de la fila seleccionada
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                # La columna nueva se llenará con el id de la caracteristica (i+1)
                attrs = {col: i+1}
                # Se hace el cambio de los atributos
                SubunidadesGeomorf.dataProvider().changeAttributeValues({fid: attrs}) 
    
    # Se guarda el raster y la capa vectorial
    print(DF_Raster)
    DF_Raster.reset_index().to_csv(
        data_path + '/Pre_Proceso/DF_Raster_SubunidadesGeomorf.csv', 
        header=True, index=False)
    
    # Se hace la respectiva rasterización del factor condicionante
    alg = "gdal:rasterize"
    Shape = SubunidadesGeomorf  # Nombre de la capa vectorial
    # Ruta y nombre del archivo de salida
    Raster = data_path + '/Pre_Proceso/SubunidadesGeomorf.tif'
    Field = 'Raster'  # Columna con la cuál se hará la rasterización
    # Capa de la cuál se copiará la extensión del algoritmo
    extents = SubunidadesGeomorf.extent()
    xmin = extents.xMinimum()  # xmin de la extensión
    xmax = extents.xMaximum()  # xmax de la extensión
    ymin = extents.yMinimum()  # ymin de la extensión
    ymax = extents.yMaximum()  # ymax de la extensión
    params = {
        'INPUT': Shape, 'FIELD': Field, 'BURN': 0, 'UNITS': 1, 'WIDTH': cellsize,
        'HEIGHT': cellsize, 'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
        'NODATA': 0, 'OPTIONS': '', 'DATA_TYPE': 5, 'INIT': None, 'INVERT': False,
        'OUTPUT': Raster}
    processing.run(alg, params)
    
    # Se añade la capa raster al lienzo
    iface.addRasterLayer(data_path + '/Pre_Proceso/SubunidadesGeomorf.tif', "SubunidadesGeomorf")

else:
    iface.messageBar().pushMessage(
        "Factor condicionante", 'No hay archivo de Subunidades geomorfologicas', Qgis.Info, 5)

# ##################################### Cobertura y Uso ##################################### #

# Si el archivo de cobertura y uso existe se hace el procedimiento
if os.path.isfile(CoberturaUso) is True:
    # Se hace la corrección geometrica del factores condicionantes.
    CoberturaUso_Corr = data_path + '/Pre_Proceso/CoberturaUso_Corr.shp'
    processing.run("native:fixgeometries", {'INPUT': CoberturaUso, 'OUTPUT': CoberturaUso_Corr})
    
    # La capa corregida se lee como una capa vectorial
    CoberturaUso = QgsVectorLayer(
        data_path + '/Pre_Proceso/CoberturaUso_Corr.shp',
        'Cobertura y Uso')
    
    # Se inicia a editar la capa
    caps = CoberturaUso.dataProvider().capabilities()
    # Se añade un campo nuevo llamado "Raster"
    # se asignará el valor único ce cada aracteristica para la posterior rasterización
    CoberturaUso.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
    # Se guarda la edición
    CoberturaUso.updateFields()
    
    # Se determina el índice de la columna que fue agregada
    col = CoberturaUso.fields().indexFromName("Raster")
    
    # Valores unicos del factor condicionante
    uniquevalues = []
    uniqueprovider = CoberturaUso.dataProvider()
    fields = uniqueprovider.fields()
    id = fields.indexFromName(Codigo_CoberturaUso)
    uniquevalues = uniqueprovider.uniqueValues(id)
    atributos = list(uniquevalues)
    print(atributos)
    
    # Se crea un datframe con el fin de conocer el id correspondiente a cada caraceristica
    DF_Raster = pd.DataFrame(columns=['Caract', 'ID'], dtype=float)
    
    # Se inicia a editar
    caps = CoberturaUso.dataProvider().capabilities()
    
    for i in range(0, len(atributos)):
        Atri = atributos[i]  # Caracteristica en cuestión
        DF_Raster.loc[i, 'Caract'] = Atri  # Se llena el dataframe con la caracteristica
        DF_Raster.loc[i, 'ID'] = i+1  # Se llena el dataframe con el id
        # Se hace la selección en la capa de la caracteristica en cuestión
        CoberturaUso.selectByExpression(
            f'"{Codigo_CoberturaUso}"=\'{Atri}\'', QgsVectorLayer.SetSelection) 
        
        # Se reemplazan los id del atributo seleccionada
        selected_fid = []
        selection = CoberturaUso.selectedFeatures()
        
        for feature in selection:  # Se recorren las filas seleccionadas
            fid = feature.id()  # Se obtiene el id de la fila seleccionada
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                # La columna nueva se llenará con el id de la caracteristica (i+1)
                attrs = {col: i+1} 
                # Se hace el cambio de los atributos
                CoberturaUso.dataProvider().changeAttributeValues({fid: attrs}) 

    # Se guarda el raster y se añade al lienzo la capa vectorial con su nueva columna llena
    print(DF_Raster)
    DF_Raster.reset_index().to_csv(
        data_path + '/Pre_Proceso/DF_Raster_CoberturaUso.csv', header=True, index=False)
    
    # Se hace la respectiva rasterización del factor condicionante
    alg = "gdal:rasterize"
    Shape = CoberturaUso  # Nombre de la capa vectorial
    Raster = data_path + '/Pre_Proceso/CoberturaUso.tif'  # Ruta y nombre del archivo de salida
    Field = 'Raster'  # Columna con la cuál se hará la rasterización
    extents = CoberturaUso.extent()  # Capa de la cuál se copiará la extensión del algoritmo
    xmin = extents.xMinimum()  # xmin de la extensión
    xmax = extents.xMaximum()  # xmax de la extensión
    ymin = extents.yMinimum()  # ymin de la extensión
    ymax = extents.yMaximum()  # ymax de la extensión
    params = {
        'INPUT': Shape, 'FIELD': Field, 'BURN': 0, 'UNITS': 1, 'WIDTH': cellsize,
        'HEIGHT': cellsize, 'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),
        'NODATA': 0, 'OPTIONS': '', 'DATA_TYPE': 5, 'INIT': None, 'INVERT': False, 'OUTPUT': Raster}
    processing.run(alg, params)
    
    # Se añade la capa raster al lienzo
    iface.addRasterLayer(data_path + '/Pre_Proceso/CoberturaUso.tif', "CoberturaUso")

else:
    iface.messageBar().pushMessage("Factor condicionante", 'No hay archivo de Cobertura y Uso', Qgis.Info, 5)

# ##################################### Cambio de Cobertura ##################################### #

# Si el archivo cambio de cobertura existe se hace el procedimiento
if os.path.isfile(CambioCobertura) is True:
    # Se hace la corrección geometrica del factores condicionantes.
    CambioCobertura_Corr = data_path + '/Pre_Proceso/CambioCobertura_Corr.shp'
    processing.run("native:fixgeometries", {'INPUT': CambioCobertura, 'OUTPUT': CambioCobertura_Corr})
    
    # La capa corregida se lee como una capa vectorial
    CambioCobertura = QgsVectorLayer(data_path + '/Pre_Proceso/CambioCobertura_Corr.shp', 'Cambio de Cobertura')
    
    # Se inicia a editar la capa
    caps = CambioCobertura.dataProvider().capabilities()
    # Se añade un campo nuevo llamado "Raster"
    # se asignará el valor único ce cada aracteristica para la posterior rasterización
    CambioCobertura.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
    # Se guarda la edición
    CambioCobertura.updateFields()
    
    # Se determina el índice de la columna que fue agregada
    col = CambioCobertura.fields().indexFromName("Raster")
    
    # Valores unicos del factor condicionante
    uniquevalues = []
    uniqueprovider = CambioCobertura.dataProvider()
    fields = uniqueprovider.fields()
    id = fields.indexFromName(Codigo_CambioCobertura)
    uniquevalues = uniqueprovider.uniqueValues(id)
    atributos = list(uniquevalues)
    print(atributos)
    
    # Se crea un datframe con el fin de conocer el id correspondiente a cada caraceristica
    DF_Raster = pd.DataFrame(columns=['Caract', 'ID'], dtype=float)
    
    # Se inicia a editar
    caps = CambioCobertura.dataProvider().capabilities()

    for i in range(0, len(atributos)): 
        Atri = atributos[i]  # Caracteristica en cuestión
        DF_Raster.loc[i, 'Caract'] = Atri  # Se llena el dataframe con la caracteristica
        DF_Raster.loc[i, 'ID'] = i+1  # Se llena el dataframe con el id
        # Se hace la selección en la capa de la caracteristica en cuestión
        CambioCobertura.selectByExpression(
            f'"{Codigo_CambioCobertura}"=\'{Atri}\'', QgsVectorLayer.SetSelection) 
        
        # Se reemplazan los id del atributo seleccionada
        selected_fid = []
        selection = CambioCobertura.selectedFeatures()
        
        for feature in selection:  # Se recorren las filas seleccionadas
            fid = feature.id()  # Se obtiene el id de la fila seleccionada
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                # Se determina que en la columna nueva se llenará con el id de la caracteristica (i+1)
                attrs = {col: i+1}
                # Se hace el cambio de los atributos
                CambioCobertura.dataProvider().changeAttributeValues({fid: attrs}) 
  
    # Se guarda el raster y se añade al lienzo la capa vectorial con su nueva columna llena
    print(DF_Raster)
    DF_Raster.reset_index().to_csv(
        data_path + '/Pre_Proceso/DF_Raster_CambioCobertura.csv', header=True, index=False)
    
    # Se hace la respectiva rasterización del factor condicionante
    alg = "gdal:rasterize"
    Shape = CambioCobertura  # Nombre de la capa vectorial
    Raster = data_path + '/Pre_Proceso/CambioCobertura.tif'  # Ruta y nombre del archivo de salida
    Field = 'Raster'  # Columna con la cuál se hará la rasterización
    extents = CambioCobertura.extent()  # Capa de la cuál se copiará la extensión del algoritmo
    xmin = extents.xMinimum()  # xmin de la extensión
    xmax = extents.xMaximum()  # xmax de la extensión
    ymin = extents.yMinimum()  # ymin de la extensión
    ymax = extents.yMaximum()  # ymax de la extensión
    params = {
        'INPUT': Shape, 'FIELD': Field, 'BURN': 0, 'UNITS': 1, 'WIDTH': cellsize,
        'HEIGHT': cellsize, 'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
        'NODATA': 0, 'OPTIONS': '', 'DATA_TYPE': 5, 'INIT': None, 'INVERT': False, 'OUTPUT': Raster}
    processing.run(alg, params)
    
    # Se añade la capa raster al lienzo
    iface.addRasterLayer(data_path + '/Pre_Proceso/CambioCobertura.tif', "CambioCobertura")

else:
    iface.messageBar().pushMessage("Factor condicionante", 'No hay archivo de Cambio de Cobertura', Qgis.Info, 5)

# ####################### Movimientos en Masa (Deslizamientos) ####################### #    
 
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
    Mov_Masa_Corr.selectByExpression(f'"{Campo_Poligono}"=\'Deslizamiento\'', QgsVectorLayer.SetSelection)
    Desliz_Preproceso = data_path + '/Pre_Proceso/Desliz_Preproceso.shp'
    QgsVectorFileWriter.writeAsVectorFormat(
        Mov_Masa_Corr, Desliz_Preproceso, "utf-8", 
        QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
    
    # Se determina si también hay mapa de puntos
    if os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
        Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos, 'Mov_Masa_Puntos')
        
        # Se generan puntos en los poligonos en los centroides de los pixeles
        # Se basa en los pixeles del raster de UGS el cuál es un factor que siempre debe tenerse
        Raster = data_path + '/Pre_Proceso/UGS.tif'
        alg = "qgis:generatepointspixelcentroidsinsidepolygons"
        Deslizamientos_poligonos = data_path + '/Pre_Proceso/Deslizamientos_poligonos.shp'
        params = {'INPUT_RASTER': Raster, 'INPUT_VECTOR': Desliz_Preproceso, 'OUTPUT': Deslizamientos_poligonos}
        processing.run(alg, params)
        
        # Se seleccionan los deslizamientos y se guardan
        Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'Deslizamiento\'', QgsVectorLayer.SetSelection)
        CRS = Mov_Masa_Puntos.crs().authid()
        Deslizamientos_puntos = data_path+'/Pre_Proceso/Deslizamientos_puntos.shp'
        QgsVectorFileWriter.writeAsVectorFormat(
            Mov_Masa_Puntos, Deslizamientos_puntos, "utf-8", 
            QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
        
        Deslizamientos_puntos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos_puntos.shp')
        Desliz_Preproceso = data_path + '/Pre_Proceso/Desliz_Preproceso.shp'
        
        # Se seleccionan los puntos que estén dentro de los poligonos
        alg = "native:selectbylocation"
        Puntos = Deslizamientos_puntos
        Poligonos = Desliz_Preproceso
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
        
        # Se unen el mapa de puntos y los puntos generados a partir de los poligonos
        alg = "native:mergevectorlayers"
        CRS = QgsCoordinateReferenceSystem('EPSG:3116')
        Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
        params = {'LAYERS': [Deslizamientos_poligonos, Deslizamientos_puntos], 'CRS': CRS, 'OUTPUT': Deslizamientos}
        processing.run(alg, params) 
    
    else:
        # Si no hay un mapa de puntos entonces el mapa de poligonos se guarda como deslizamientos
        Desliz_Preproceso = QgsVectorLayer(data_path + '/Pre_Proceso/Desliz_Preproceso.shp')
        Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
        CRS = Desliz_Preproceso.crs().authid()
        QgsVectorFileWriter.writeAsVectorFormat(Desliz_Preproceso, Deslizamientos, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")
        

# Si no hay mapa de poligonos se guarda la selección de deslizamientos
elif os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
    Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos, 'Mov_Masa_Puntos')
    Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'Deslizamiento\'', QgsVectorLayer.SetSelection)
    CRS = Mov_Masa_Puntos.crs().authid()
    Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Deslizamientos, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)

# Si no hay mapas de ningún tipo se genera un aviso porque es necesario
else:
    iface.messageBar().pushMessage("Movimientos en masa", 'No hay archivo de movimientos en masa', Qgis.Warning, 10)
