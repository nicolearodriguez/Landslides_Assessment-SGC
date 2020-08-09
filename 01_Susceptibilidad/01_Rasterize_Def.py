from PyQt5.QtWidgets import QInputDialog
from PyQt5.QtWidgets import QMessageBox
from qgis.PyQt.QtCore import QVariant
from qgis.gui import QgsMessageBar
from qgis.core import QgsProject
from os import listdir
import pandas as pd
import numpy as np
import processing
import os

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
data_path = data_path.replace("\\", "/")

list = listdir(data_path)

shape = []
for i in list:
    if i[-4:] == '.shp':
        shape.append(i)
shape.append('None')

raster = []
for i in list:
    if i[-4:] == '.tif':
        raster.append(i)
raster.append('None')

# Se comprueba si las carpetas de pre-proceso y resultados existen
# de no ser así se crean
if os.path.isdir(data_path + '/Pre_Proceso') is False:
    os.mkdir(data_path + '/Pre_Proceso')

if os.path.isdir(data_path + '/Resultados') is False:
    os.mkdir(data_path + '/Resultados')
    
if os.path.isdir(data_path + '/Amenaza') is False:
    os.mkdir(data_path + '/Amenaza')

# Se piden las entradas necesarias para la ejecución-DEM del área de estudio
# y capas vectoriales de los factores condicionante

# Modelo digital de elevación
DEM, ok = QInputDialog.getItem(None, "Seleccione el archivo DEM", "Opciones", raster, 0, False)
Ruta_DEM = data_path + '/' + DEM

# Movimientos en masa tipo puntos
Mov_Masa_Puntos, ok = QInputDialog.getItem(None, "Movimientos en masa tipo PUNTOS", "Seleccione el archivo de movimientos en masa tipo puntos", shape, 0, False)
Ruta_Mov_Masa_Puntos = data_path + '/' + Mov_Masa_Puntos

if os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
    Mov_Masa_Puntos = QgsVectorLayer(data_path + '/' + Mov_Masa_Puntos)
    
    atributos_Mov_Masa_Puntos = []
    for field in Mov_Masa_Puntos.fields():
        atributos_Mov_Masa_Puntos.append(field.name())
        
    # Campo dónde se encuentra el tipo de movimiento en masa para la capa de puntos
    Campo_Puntos, ok = QInputDialog.getItem(None, "Tipo de movimiento en masa", "Campo del tipo de movimiento en masa tipo punto", atributos_Mov_Masa_Puntos, 0, False)

# Movimientos en masa tipo poligonos
Mov_Masa_Poligono, ok = QInputDialog.getItem(None, "Movimientos en masa tipo POLIGONO", "Seleccione el archivo de movimientos en masa tipo poligonos", shape, 0, False)
Ruta_Mov_Masa_Poligono = data_path + '/' + Mov_Masa_Poligono

if os.path.isfile(Ruta_Mov_Masa_Poligono) is True:
    Mov_Masa_Poligono = QgsVectorLayer(data_path + '/' + Mov_Masa_Poligono)
    
    atributos_Mov_Masa_Poligono = []
    for field in Mov_Masa_Poligono.fields():
        atributos_Mov_Masa_Poligono.append(field.name())
        
    # Campo dónde se encuentra el tipo de movimiento en masa para la capa de poligonos
    Campo_Poligono, ok = QInputDialog.getItem(None, "Tipo de movimiento en masa", "Campo del tipo de movimiento en masa tipo poligono", atributos_Mov_Masa_Poligono, 0, False)

if os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
    if os.path.isfile(Ruta_Mov_Masa_Poligono) is True:
        if Campo_Puntos != Campo_Poligono:
            QMessageBox.critical(iface.mainWindow(), "Movimientos", 'Los campos del tipo de MM de las capas de movimientos debe ser iguales')

# Dimensiones del pixel
cellsize, ok = QInputDialog.getDouble(
    None, 'CELLSIZE', 'Introduce el tamaño del pixel: ')

# ########################## PENDIENTE/CURVATURA ########################## #

## Cambio de tamaño de pixel
#DEM = QgsRasterLayer(Ruta_DEM)
#
#pipe = QgsRasterPipe()
#extent = DEM.extent()
#width_layer = DEM.width()
#height_layer = DEM.height()
#X = DEM.rasterUnitsPerPixelX()
#Y = DEM.rasterUnitsPerPixelY()
#width = (X/cellsize)*width_layer
#height = (Y/cellsize)*height_layer
#renderer = DEM.renderer()
#provider = DEM.dataProvider()
#crs = DEM.crs().toWkt()
#pipe.set(provider.clone())
#pipe.set(renderer.clone())
#file_writer = QgsRasterFileWriter(data_path+'/Pre_Proceso/DEM_reproyectado.tif')
#file_writer.writeRaster(pipe, width, height, extent, layer.crs())
#
## Pendiente
#DEM = QgsRasterLayer(data_path+'/Pre_Proceso/DEM_reproyectado.tif')
## Se genera el mapa de pendientes
#alg = "gdal:slope"
#Pendiente = data_path+'/Pre_Proceso/Pendiente.tif'
#params = {
#    'INPUT': DEM, 'BAND': 1, 'SCALE': 1, 'AS_PERCENT': False, 'COMPUTE_EDGES': False,
#    'ZEVENBERGEN': False, 'OPTIONS': '', 'EXTRA': '', 'OUTPUT': Pendiente}
#processing.run(alg, params)
#iface.addRasterLayer(data_path+'/Pre_Proceso/Pendiente.tif', "Pendiente")
#
## Curvatura

# ##################################### Factores Condicionantes ##################################### #

def rasterize(Factor_Condicionante):
    # Unidades geologicas superficiales
    Ruta_Factor, ok = QInputDialog.getItem(None, f"{Factor_Condicionante}", "Seleccione el archivo de {Factor_Condicionante}", shape, 0, False)
    Ruta_Factor = data_path + '/' + Ruta_Factor
    Factor = QgsVectorLayer(Ruta_Factor)
        
    # Si el archivo de Factor existe se hace el procedimiento
    if os.path.isfile(Ruta_Factor) is True:
        
        atributos_Factor = []
        for field in Factor.fields():
            atributos_Factor.append(field.name())
        
        # Nombre del campo dónde se encuentran los códigos representativos de las Factor
        Codigo_Factor, ok = QInputDialog.getItem(None, f"Campo representativo de las {Factor_Condicionante}", "Seleccione el campo representativo de las {Factor_Condicionante}", atributos_Factor, 0, False)
        
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
        # se asignará el valor único de cada aracteristica
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
        df = pd.DataFrame(atributos)
        print(atributos)
        
        # Se crea un datframe
        DF_Raster = pd.DataFrame(columns=['Caract', 'ID'], dtype=float)
        
        # Se inicia a editar
        caps = Factor.dataProvider().capabilities()
        
        for i in range(0, len(atributos)):
            Atri = df.loc[i, 0]  # Caracteristica en cuestión
            DF_Raster.loc[i, 'Caract'] = Atri  # Se llena el dataframe con la caracteristica
            DF_Raster.loc[i, 'ID'] = i+1  # Se llena el dataframe con el id
            # Para el caso de las Factor se obtienen las dos primeras letras de su acronimo
            DF_Raster.loc[i, 'General'] = Atri[0:2]
            # Se hace la selección en la capa de la caracteristica en cuestión
            Factor.selectByExpression(f'"{Codigo_Factor}"=\'{Atri}\'', QgsVectorLayer.SetSelection)
            
            # Se reemplazan los id del atributo seleccionada
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
    
    else:
        iface.messageBar().pushMessage(
            "Factor condicionante", f'No hay archivo de {Factor_Condicionante}', Qgis.Info, 5)

Factor_Condicionante = ['UGS', 'SubunidadesGeomorf', 'CoberturaUso', 'CambioCobertura']

for factor in Factor_Condicionante:
    rasterize(factor)

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
        
        if item == 'Centroides de pixeles':
            # Se generan puntos en los poligonos en los centroides de los pixeles
            # Se basa en los pixeles del raster de Factor el cuál es un factor que siempre debe tenerse
            Raster = data_path + '/Pre_Proceso/UGS.tif'
            alg = "qgis:generatepointspixelcentroidsinsidepolygons"
            Deslizamientos_poligonos = data_path + '/Pre_Proceso/Deslizamientos_poligonos.shp'
            params = {'INPUT_RASTER': Raster, 'INPUT_VECTOR': Desliz_Preproceso, 'OUTPUT': Deslizamientos_poligonos}
            processing.run(alg, params)
            
        else:
            #Se generan puntos en los poligonos en los centroides de los pixeles
            #Se basa en los pixeles del raster de Factor el cuál es un factor que siempre debe tenerse
            alg = "native:centroids"
            Deslizamientos_poligonos = data_path+'/Pre_Proceso/Deslizamientos_poligonos.shp'
            params = {'INPUT': Desliz_Preproceso, 'ALL_PARTS': True, 'OUTPUT': Deslizamientos_poligonos}
            processing.run(alg, params)
        
        # Se seleccionan los deslizamientos y se guardan
        Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'Deslizamiento\'', QgsVectorLayer.SetSelection)
        CRS = Mov_Masa_Puntos.crs().authid()
        Deslizamientos_puntos = data_path+'/Pre_Proceso/Deslizamientos_puntos.shp'
        QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Deslizamientos_puntos, "utf-8", 
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
        
        # Se unen el mapa de puntos y los puntos generados a partir de los poligonos de deslizamientos
        alg = "native:mergevectorlayers"
        CRS = QgsCoordinateReferenceSystem('EPSG:3116')
        Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
        params = {'LAYERS': [Deslizamientos_poligonos, Deslizamientos_puntos], 'CRS': CRS, 'OUTPUT': Deslizamientos}
        processing.run(alg, params) 
        
        # Se unen el mapa de puntos y los puntos generados a partir de los poligonos de los movimientos
        alg = "native:mergevectorlayers"
        CRS = QgsCoordinateReferenceSystem('EPSG:3116')
        Mov_Masa = data_path + '/Pre_Proceso/Mov_Masa.shp'
        params = {'LAYERS': [Mov_Masa_poligonos, Mov_Masa_Puntos], 'CRS': CRS, 'OUTPUT': Mov_Masa}
        processing.run(alg, params)
    
    else:
        # Si no hay un mapa de puntos entonces el mapa de poligonos se guarda como deslizamientos
        Desliz_Preproceso = QgsVectorLayer(data_path + '/Pre_Proceso/Desliz_Preproceso.shp')
        Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
        CRS = Desliz_Preproceso.crs().authid()
        QgsVectorFileWriter.writeAsVectorFormat(Desliz_Preproceso, Deslizamientos, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")
        
        # Si no hay un mapa de puntos entonces el mapa de poligonos se guarda como movimientos
        Mov_Masa_poligonos = QgsVectorLayer(data_path+'/Pre_Proceso/Mov_Masa_poligonos.shp')
        Mov_Masa = data_path + '/Pre_Proceso/Mov_Masa.shp'
        CRS = Desliz_Preproceso.crs().authid()
        QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_poligonos, Mov_Masa, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")

elif os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
    
    # Si no hay mapa de poligonos se guarda la selección de deslizamientos
    Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos, 'Mov_Masa_Puntos')
    Mov_Masa_Puntos.selectByExpression(f'"{Campo_Puntos}"=\'Deslizamiento\'', QgsVectorLayer.SetSelection)
    CRS = Mov_Masa_Puntos.crs().authid()
    Deslizamientos = data_path + '/Pre_Proceso/Deslizamientos.shp'
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Deslizamientos, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected=True)
    
    # Si no hay un mapa de poligonos entonces el mapa de puntos se guarda como movimientos
    Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos, 'Mov_Masa_Puntos')
    Mov_Masa = data_path + '/Pre_Proceso/Mov_Masa.shp'
    CRS = Mov_Masa_Puntos.crs().authid()
    QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Puntos, Mov_Masa, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")


# Si no hay mapas de ningún tipo se genera un aviso porque es necesario
else:
    iface.messageBar().pushMessage("Movimientos en masa", 'No hay archivo de movimientos en masa', Qgis.Warning, 10)

    

