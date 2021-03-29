
from PyQt5.QtWidgets import QInputDialog, QMessageBox
from qgis.PyQt.QtCore import QVariant 
from qgis.gui import QgsMessageBar
from PyQt5 import QtCore
from qgis.core import QgsProject
import matplotlib.pyplot as plt
from osgeo import gdal_array
from PyQt5 import QtGui 
from qgis.core import *
from os import listdir
from time import time
from PyQt5 import uic
import pandas as pd
import numpy as np
import processing
import datetime
import math
import gdal
import os

DialogBase, DialogType = uic.loadUiType(os.path.join(os.path.dirname(__file__), 'Landslides_Assessment_SGC.ui'))

class LandslidesAssessmentSGCDialog(DialogType, DialogBase):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setupUi(self)

        #Se identifican las acciones que se llevan a cabo una vez se presiona un botón
        self.openDirectoryButton.clicked.connect(self.openDirectoryButtonPushed)
        
        self.cargarAtributosButton.clicked.connect(self.loadAttributes) 
        self.cargarCaracteristicasButton.clicked.connect(self.loadFeatures) 
        
        self.SusceptibilidadButton.clicked.connect(self.Susceptibilidad)
        
        self.AmenazaButton.clicked.connect(self.Amenaza)
        
        # Se lee el sistema coordenado
        crs_start = QgsCoordinateReferenceSystem("EPSG:3116")
        self.mQgsProjectionSelectionWidget.setCrs(crs_start)
        
        self.bar = QgsMessageBar()
        
    def openDirectoryButtonPushed(self):
    
        # Se determina la ruta general dónde se encuentran todos los insumos
        from qgis.PyQt.QtWidgets import QFileDialog
        filepath = QFileDialog.getExistingDirectory(caption = "Select Directory", directory = '')
        ##if canceled
        if not filepath:
            return
        
        self.Ruta_General.setText(filepath)
        
        # Se cargan los archivos de la ruta general
        self.loadLayers()
        
    def loadLayers (self):
        """
        Load all layers from the project and show them in the combobox
        """
        # Se listan los archivos de la ruta general
        data_path = self.Ruta_General.text()
        list_files = listdir(data_path)
        
        for i in list_files:
            
            # Se identifican los archivos vectoriales
            if i[-4:] == '.shp':
                self.Zona_Estudio.addItem(i)
                self.Mov_Masa_Puntos.addItem(i)
                self.Mov_Masa_Poligono.addItem(i)
                self.Zona_Deposito.addItem(i)
                self.Geologia.addItem(i)
                self.Geomorfologia.addItem(i)
                self.Uso_cobertura.addItem(i)
                self.Cambio_cobertura.addItem(i)
                self.Sismos.addItem(i)
                self.Estaciones.addItem(i)
                
            # Se identifican los archivos raster
            elif i[-4:] == '.tif':
                self.Pendiente.addItem(i)
                self.Curvatura.addItem(i)
                
            # Se identifican los archivos separados por comas
            elif i[-4:] == '.csv':
                self.GeoformasIndicativas_Caida.addItem(i)
                self.GeoformasIndicativas_Flujos.addItem(i)
                self.Precipitacion.addItem(i)
                
        # Se carga la posibilidad de None a los archivos que no son estrictamente necesarios   
        self.Zona_Estudio.addItem('None')
        self.Mov_Masa_Poligono.addItem('None')
        self.Mov_Masa_Puntos.addItem('None')
        self.Zona_Deposito.addItem('None')
        self.Cambio_cobertura.addItem('None')
         
         
    def loadAttributes (self):
    
        data_path = self.Ruta_General.text()
        
        """
        Se cargan los atributos de los movimientos en masa que se tengan
        """
        
        MM_Puntos = self.Mov_Masa_Puntos.currentText()
        Ruta_Mov_Masa_Puntos = data_path + '/' + MM_Puntos
        
        MM_Poligono = self.Mov_Masa_Poligono.currentText()
        Ruta_Mov_Masa_Poligono = data_path + '/' + MM_Poligono 
        
        if os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
            Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos)
            
            for field in Mov_Masa_Puntos.fields():
                self.Fecha_MM.addItem(field.name())
                self.Tipo_MM.addItem(field.name())
                
        elif os.path.isfile(Ruta_Mov_Masa_Poligono) is True:
            Mov_Masa_Poligono = QgsVectorLayer(Ruta_Mov_Masa_Poligono)
            
            for field in Mov_Masa_Poligono.fields():
                self.Fecha_MM.addItem(field.name())
                self.Tipo_MM.addItem(field.name())
                
        else:
            return
            
        """
        Se cargan los atributos de los sismos
        """
        
        Sismos = self.Sismos.currentText()
        Ruta_Sismos = data_path + '/' + Sismos
        
        if os.path.isfile(Ruta_Sismos) is True:
            Sismos = QgsVectorLayer(Ruta_Sismos)
            
            for field in Sismos.fields():
                self.Magnitud_Sismo.addItem(field.name())
                self.Unidad_Sismo.addItem(field.name())
                self.Fecha_Sismo.addItem(field.name())
                
        else:
            return
        
        """
        Se cargan los atributos del shape de estaciones pluviométricas
        """
        
        Estaciones = self.Estaciones.currentText()
        Ruta_Estaciones = data_path + '/' + Estaciones
        
        if os.path.isfile(Ruta_Estaciones) is True:
            Estaciones = QgsVectorLayer(Ruta_Estaciones)
            
            for field in Estaciones.fields():
                self.Codigo_Estacion.addItem(field.name())
        
        """
        Se cargan los atributos del csv de la precipitación diaria
        """
        
        Precipitacion = self.Precipitacion.currentText()
        Ruta_Precipitacion = data_path + '/' + Precipitacion
        
        if os.path.isfile(Ruta_Precipitacion) is True:
            DF_Precipitacion_diaria = pd.read_csv(Ruta_Precipitacion)
            Campos = DF_Precipitacion_diaria.columns.tolist()
            self.Fecha_Precip.addItems(Campos)
            
            
    def loadFeatures(self):
    
        data_path = self.Ruta_General.text()
        
        """
        Se cargan las caracteristicas del tipo de movimiento en masa 
        según la geometría de capa que se tiene
        """
    
        MM_Puntos = self.Mov_Masa_Puntos.currentText()
        Ruta_Mov_Masa_Puntos = data_path + '/' + MM_Puntos
        
        MM_Poligono = self.Mov_Masa_Poligono.currentText()
        Ruta_Mov_Masa_Poligono = data_path + '/' + MM_Poligono 
        
        # Movimientos en masa con geometría de puntos
        if os.path.isfile(Ruta_Mov_Masa_Puntos) is True:
            Mov_Masa_Puntos = QgsVectorLayer(Ruta_Mov_Masa_Puntos)
            
            Tipo_MM = self.Tipo_MM.currentText()
            
            # Se obtienen los valores únicos de las caracteristicas
            uniquevalues = []
            uniqueprovider = Mov_Masa_Puntos.dataProvider()
            fields = uniqueprovider.fields()
            id = fields.indexFromName(Tipo_MM)
            fields_MM = list(uniqueprovider.uniqueValues(id))
            print(fields_MM)
            
            self.Deslizamiento.addItems(fields_MM)
            self.Caida.addItems(fields_MM)
            self.Reptacion.addItems(fields_MM)
        
        # Movimientos en masa con geometría de polígonos
        elif os.path.isfile(Ruta_Mov_Masa_Poligono) is True:
            Mov_Masa_Poligono = QgsVectorLayer(Ruta_Mov_Masa_Poligono)
            
            Tipo_MM = self.Tipo_MM.currentText()
            
            # Se obtienen los valores únicos de las caracteristicas
            uniquevalues = []
            uniqueprovider = Mov_Masa_Poligono.dataProvider()
            fields = uniqueprovider.fields()
            id = fields.indexFromName(Tipo_MM)
            fields_MM = uniqueprovider.uniqueValues(id)
            
            self.Deslizamiento.addItems(fields_MM)
            self.Caida.addItems(fields_MM)
            self.Reptacion.addItems(fields_MM)
                
        else:
            return
 
    
    # ##################################### ANÁLISIS DE SUSCEPTIBILIDAD ##################################### #
    
    def Susceptibilidad(self):
        
        #Se determina el momento en que inicia la ejcución del programa
        start_time = time()
        
        # Se identifica que el sistema geográfico sea valido
        if self.mQgsProjectionSelectionWidget.crs().isValid():
            
            if self.mQgsProjectionSelectionWidget.crs().isGeographic(): # if it is a geografic 
                
                # Se informa que el Sistema de Referencia debe ser plano
                QMessageBox.information(self, "!SRC plano!",
                        'Por favor seleccione un Sistema Coordenado de Referencia Plano')
                        
        EPSG_code = self.mQgsProjectionSelectionWidget.crs().authid()
        EPSG_name = self.mQgsProjectionSelectionWidget.crs().description()
        
        # Se extrae la ruta general
        data_path = self.Ruta_General.text()
        
        # Se extraen los factores condicionantes
        Factores_Condicionantes = []
        Factores_Condicionantes.append(self.Geologia.currentText())
        Factores_Condicionantes.append(self.Geomorfologia.currentText())
        Factores_Condicionantes.append(self.Uso_cobertura.currentText())
        Factores_Condicionantes.append(self.Cambio_cobertura.currentText())
        
        # Se extraen las rutas correspondientes a los movimientos en masa
        Ruta_Mov_Masa_Poligono = data_path + '/' + self.Mov_Masa_Poligono.currentText()
        Ruta_Mov_Masa_Puntos = data_path + '/' + self.Mov_Masa_Puntos.currentText()
        
        # Se extraen el campo dónde se encuentra el tipo de movimiento en masa
        Campo_Poligono = self.Tipo_MM.currentText()
        Campo_Puntos = self.Tipo_MM.currentText()
        
        # Se extrae cómo están identificados los movimientos en masa según el tipo
        Deslizamiento = self.Deslizamiento.currentText()
        Caida = self.Caida.currentText()
        Reptacion = self.Reptacion.currentText()
        
        # Se extrae la ruta de la zona de estudio
        Ruta_Zona_Estudio = data_path + '/' + self.Zona_Estudio.currentText()
        
        # Se extrae el tamaño del pixel
        cellsize = self.cellsize.value()
        
        # Se extrae el porcentaje de movimientos en masa para el análisis de la curva de éxito
        MM_Exito = self.MM_Exito.value()
        
        # Se extrae el intercepto para la clasificación de susceptibilidad por deslizamientos (Alta/Media)
        suscep_alta = self.suscep_alta.value()
        suscep_alta = suscep_alta/100
        
        # Se extrae el intercepto para la clasificación de susceptibilidad por deslizamientos (Media/Baja)
        suscep_media = self.suscep_media.value()
        suscep_media = suscep_media/100
        
        # Se extrae la ruta de la zona de depósito de caídos
        Zona_Deposito = self.Zona_Deposito.currentText()
        Ruta_Zona_Deposito = data_path + '/' + Zona_Deposito
        
        # Se extrae las geoformas indicativas de procesos tipo caídas
        GeoformasIndicativas_Caida = self.GeoformasIndicativas_Caida.currentText()
        
        # Se extrae la pendiente umbral para procesos tipo caída
        slope = self.slope.value()
        
        # Se extrae las geoformas indicativas de procesos tipo flujo
        GeoformasIndicativas_Flujos = self.GeoformasIndicativas_Flujos.currentText()

        """
        01_Susceptibilidad_Insumos
        """
        
        # Se comprueba si las carpetas de pre-proceso, resultados y amenaza existen
        # de no ser así se crean
        
        if os.path.isdir(data_path + '/Pre_Proceso') is False:
            os.mkdir(data_path + '/Pre_Proceso')

        if os.path.isdir(data_path + '/Resultados') is False:
            os.mkdir(data_path + '/Resultados')
            
        if os.path.isdir(data_path + '/Amenaza') is False:
            os.mkdir(data_path + '/Amenaza')
            
        if os.path.isdir(data_path + f'/Curva_Exito') is False:
            os.mkdir(data_path + f'/Curva_Exito')

        if os.path.isdir(data_path + '/Curva_Validacion') is False:
            os.mkdir(data_path + '/Curva_Validacion')
                
        # ##################################### Factores Condicionantes ##################################### #

        # Se define la función rasterize para la rasterización de los factores condicionantes con base en el campo representativo

        def rasterize(Factor_Condicionante):
            
            Ruta_Factor = data_path + '/' + Factor_Condicionante
            
            # Si el archivo de Factor existe se hace el procedimiento
            if os.path.isfile(Ruta_Factor) is True:
                
                Factor = QgsVectorLayer(Ruta_Factor)
                
                indice = Factor_Condicionante.index('.')
                Factor_Condicionante = Factor_Condicionante[:indice]
                
                # Se listan los atributos del arhivo vectorial
                atributos_Factor = []
                for field in Factor.fields():
                    atributos_Factor.append(field.name())
                
                # Nombre del campo dónde se encuentran los códigos representativos de las Factor
                Codigo_Factor, ok = QInputDialog.getItem(None, f"Campo representativo de las {Factor_Condicionante}", f"Seleccione el campo representativo de {Factor_Condicionante}", atributos_Factor, 0, False)
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
                Raster = QgsRasterLayer(data_path + f'/Pre_Proceso/{Factor_Condicionante}.tif', f"{Factor_Condicionante}")
                QgsProject.instance().addMapLayer(Raster)
           
            # Si la capa no existe se emite un mensaje
            else:
                self.bar.pushMessage(
                    "Factor condicionante", f'No hay archivo de {Factor_Condicionante}', Qgis.Info, 5)
                    
        # Se recorre la lista de factores condicionates continuos
        for factor in Factores_Condicionantes:
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
            self.bar.pushMessage("Movimientos en masa", 'No hay archivo de movimientos en masa', Qgis.Warning, 10)

        # Según el análisis se dividen y exportan los deslizamientos para el respectivo análisis
        if os.path.isfile(data_path + '/Pre_Proceso/Deslizamientos.shp') is True:
            
            if MM_Exito == 100:
                Deslizamientos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos.shp', 'Deslizamientos')
                Deslizamientos_Exito = data_path + '/Pre_Proceso/Deslizamientos_Exito.shp'
                CRS = Deslizamientos.crs().authid()
                QgsVectorFileWriter.writeAsVectorFormat(Deslizamientos, Deslizamientos_Exito, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")
                
            else:
                # Se seleccionan aleatoriamente los deslizamientos para el análisis de éxito y validación
                Deslizamientos = QgsVectorLayer(data_path + '/Pre_Proceso/Deslizamientos.shp')
                alg = "qgis:randomselection"
                params = {'INPUT': Deslizamientos,'METHOD': 1,'NUMBER': MM_Exito}
                processing.run(alg, params)
                
                # Se guarda la selección de deslizamientos para análisis de éxito
                Deslizamientos_Exito = data_path + '/Pre_Proceso/Deslizamientos_Exito.shp'
                CRS = Deslizamientos.crs().authid()
                QgsVectorFileWriter.writeAsVectorFormat(Deslizamientos, Deslizamientos_Exito, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected = True)
                
                # Se invierte la selección para obtener así los deslizamientos de validación
                Deslizamientos.invertSelection()
                
                # Se guarda la selección de deslizamientos para análisis de validación
                Deslizamientos_Validacion = data_path + '/Pre_Proceso/Deslizamientos_Validacion.shp'
                CRS = Deslizamientos.crs().authid()
                QgsVectorFileWriter.writeAsVectorFormat(Deslizamientos, Deslizamientos_Validacion, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile", onlySelected = True)
                
                
        # Se guarda la zona de estudio para su posterior uso
        if os.path.isfile(Ruta_Zona_Estudio) is True:
            Zona_Estudio = QgsVectorLayer(Ruta_Zona_Estudio, 'Zona_Estudio')
            Zona_Estudio_Export = data_path + '/Pre_Proceso/Zona_Estudio.shp'
            CRS = Zona_Estudio.crs().authid()
            QgsVectorFileWriter.writeAsVectorFormat(Zona_Estudio, Zona_Estudio_Export, "utf-8", QgsCoordinateReferenceSystem(CRS), "ESRI Shapefile")
            
        """
        02_Metodo_WofE - Exito / Validación
        """
        
        # ############################ SE PLANTEA LA FUNCIÓN DEL MÉTODO ESTADÍSTICO BIVARIADO ############################ #

        #Se define la función Wf para determinar los pesos finales del factor condicionate
        def Wf(factor, Deslizamientos, carpeta):
                
            # Análisis de deslizamientos si su geometria es puntos
            if Deslizamientos.wkbType()== QgsWkbTypes.Point:
                # Se muestrea el id de la caracteristica del factor condicionante en el punto de deslizamiento
                alg = "qgis:rastersampling"
                output = data_path + f'/{carpeta}/Valores{factor}.shp'
                params = {'INPUT': Deslizamientos, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Id_Condici', 'OUTPUT': output}
                processing.run(alg, params)
                ValoresRaster = QgsVectorLayer(data_path + f'/{carpeta}/Valores{factor}.shp', f'Valores{factor}')
            
            else:
                # Análisis de deslizamientos si su geometria es poligonos
                # Interesección de el factor condicionante con el área de deslizamientos
                alg = "gdal:cliprasterbymasklayer"
                Deslizamiento_Condicion = data_path + f'/{carpeta}/Deslizamientos{factor}.tif'
                params = {'INPUT': rasterfile, 'MASK': Deslizamientos, 'SOURCE_CRS': None,
                          'TARGET_CRS': None, 'NODATA': None, 'ALPHA_BAND': False,
                          'CROP_TO_CUTLINE': True, 'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None,
                          'Y_RESOLUTION': None, 'MULTITHREADING': False, 'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '',
                          'OUTPUT': Deslizamiento_Condicion}
                processing.run(alg, params)
                
                # Estadísticas zonales (número de pixeles por atributo por deslizamiento)
                alg = "native:rasterlayerzonalstats"
                Estadisticas_Deslizamiento = data_path + f'/{carpeta}/Deslizamientos{factor}Estadistica.csv'
                params = {'INPUT': Deslizamiento_Condicion, 'BAND': 1, 'ZONES': Deslizamiento_Condicion,
                          'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Deslizamiento}
                processing.run(alg, params)
                
                # Lectura de las estadísticas de la zona de deslizamientos como dataframe
                Estadisticas_Deslizamiento = data_path + f'/{carpeta}/Deslizamientos{factor}Estadistica.csv'
                DF_DeslizamientosEstadistica = pd.read_csv(Estadisticas_Deslizamiento, delimiter=",",encoding='latin-1')
            
            # Estadísticas zonales del raster del factor condicionante (número de pixeles por atributo total)
            alg = "native:rasterlayerzonalstats"
            Estadisticas_Condicionante = data_path + f'/{carpeta}/{factor}Estadistica.csv'
            params = {'INPUT': rasterfile, 'BAND': 1, 'ZONES': rasterfile,
                      'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Condicionante}
            processing.run(alg, params)
            
            # Lectura de las estadísticas de toda la zona como dataframe
            Estadisticas_Condicionante = data_path + f'/{carpeta}/{factor}Estadistica.csv'
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
                    self.bar.pushMessage("Factor condicionante", f'Revisar el factor condicionante {factor}', Qgis.Warning, 5)
                    
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
            if (factor != 'CurvaturaPlano' and factor != 'Pendiente'):
                DF_Susceptibilidad = DF_Susceptibilidad.drop(['Max'], axis=1)
                DF_Susceptibilidad = DF_Susceptibilidad.rename(columns={'Min':'ID'})

            # Se imprime y se guarda el dataframe de pesos finales para el factor condicionante
            print(f'Los valores de Wf para {factor} es: ')
            print(DF_Susceptibilidad)
            DF_Susceptibilidad.reset_index().to_csv(data_path + f'/{carpeta}/DF_Susceptibilidad_{factor}.csv', header = True, index = False)
            
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
            Susceptibilidad_Condicionante = data_path + f'/{carpeta}/DF_Susceptibilidad_{factor}.csv'
            Condicionante_Reclass = data_path + f'/{carpeta}/Wf_{factor}.tif'
            params = {'INPUT_RASTER': rasterfile, 'RASTER_BAND': 1, 'INPUT_TABLE': Susceptibilidad_Condicionante,
                      'MIN_FIELD': MIN_FIELD, 'MAX_FIELD': MAX_FIELD, 'VALUE_FIELD': 'Wf', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': RANGE_BOUNDARIES,
                      'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5, 'OUTPUT': Condicionante_Reclass}
            processing.run(alg, params)
                  
        # ############################ SE APLICA EL MÉTODO (ÉXITO/VAALIDACIÓN) ############################ #
        
        # Según el porcetaje de movimientos con el que se trabaje se hace el análisis
        if MM_Exito != 100:
            Curva = ['Exito', 'Validacion']
        else:
            Curva = ['Exito']
        
        for curva in Curva:
            
            # Se define la carpeta de exportación según la curva que se va a realizar
            carpeta = f'Curva_{curva}'
            
            # Se lee el archivo correspondientes a deslizamientos
            Deslizamientos = QgsVectorLayer(data_path + f'/Pre_Proceso/Deslizamientos_{curva}.shp')
            
            # ##### FACTORES CONDICIONANTES DISCRETOS ##### #

            # Se recorre la lista de factores condicionantes
            for factor in (Factores_Condicionantes):
            
                if factor != "None":
                
                    indice = factor.index('.')
                    factor = factor[:indice]
                
                    # Se determina la posible ruta del factor condicionante
                    rasterfile = data_path + f'/Pre_Proceso/{factor}.tif'
                    
                    # Si el archivo no existe se continua 
                    if os.path.isfile(rasterfile) is False:
                        continue
                        
                    # Se aplica la función del peso al factor condicionante
                    Wf(factor, Deslizamientos, carpeta)

            # ##### FACTORES CONDICIONANTES CONTINUOS ##### #

            # Se listan los factores condicionantes continuos
            Factor_Condicionante_tif = ['Pendiente', 'CurvaturaPlano']

            # Se recorre la lista de factores condicionantes
            for factor in (Factor_Condicionante_tif):
                # Se determina la posible ruta del factor condicionante    
                if factor == 'Pendiente':
                    Ruta_Factor = self.Pendiente.currentText()
                    
                else:
                    Ruta_Factor = self.Curvatura.currentText()
                
                rasterfile = data_path + '/' + Ruta_Factor
                
                # Si el archivo no existe se continua 
                if os.path.isfile(rasterfile) is False:
                    continue
                    
                # Se aplica la función del peso al factor condicionante
                Wf(factor, Deslizamientos, carpeta)
                
        """
        03_LSI_Deslizamientos - Exito/Validación
        """
        
        # Según el porcetaje de movimientos con el que se trabaje se hace el análisis
        if MM_Exito != 100:
            Curva = ['Exito', 'Validacion']
        else:
            Curva = ['Exito']
            
        for curva in Curva:
        
            # Se define la carpeta de exportación según la curva que se va a realizar
            carpeta = f'Curva_{curva}'

            # Capas raster reclasificadas con su respectivo Wf
            
            # Unidades geologicas superficiales
            Geologia = self.Geologia.currentText()
            indice = Geologia.index('.')
            Geologia = Geologia[:indice]
            Wf_UGS = QgsRasterLayer(data_path + f'/{carpeta}/Wf_{Geologia}.tif', "Wf_UGS")
            QgsProject.instance().addMapLayer(Wf_UGS)

            # Subunidades geomorfologicas
            Geomorfologia = self.Geomorfologia.currentText()
            indice = Geomorfologia.index('.')
            Geomorfologia = Geomorfologia[:indice]
            Wf_Geomorfologia = QgsRasterLayer(data_path + f'/{carpeta}/Wf_{Geomorfologia}.tif', "Wf_Geomorfologia")
            QgsProject.instance().addMapLayer(Wf_Geomorfologia)

            # Cobertura y uso
            Uso_cobertura = self.Uso_cobertura.currentText()
            indice = Uso_cobertura.index('.')
            Uso_cobertura = Uso_cobertura[:indice]
            Wf_Uso_cobertura = QgsRasterLayer(data_path + f'/{carpeta}/Wf_{Uso_cobertura}.tif', "Wf_Uso_cobertura")
            QgsProject.instance().addMapLayer(Wf_Uso_cobertura)

            # Curvatura plana
            Wf_CurvaturaPlano = QgsRasterLayer(data_path + f'/{carpeta}/Wf_CurvaturaPlano.tif', "Wf_CurvaturaPlano")
            QgsProject.instance().addMapLayer(Wf_CurvaturaPlano)
            
            # Pendiente
            Wf_Pendiente = QgsRasterLayer(data_path + f'/{carpeta}/Wf_Pendiente.tif', "Wf_Pendiente")
            QgsProject.instance().addMapLayer(Wf_Pendiente)

            # Cambio de cobertura
            Cambio_cobertura = self.Cambio_cobertura.currentText()
            if Cambio_cobertura != "None":
                indice = Cambio_cobertura.index('.')
                Cambio_cobertura = Cambio_cobertura[:indice]
                Wf_Cambio_cobertura = QgsRasterLayer(data_path + f'/{carpeta}/Wf_{Cambio_cobertura}.tif', "Wf_Cambio_cobertura")
                QgsProject.instance().addMapLayer(Wf_Cambio_cobertura)
                Expresion = '\"Wf_UGS@1\" + \"Wf_Geomorfologia@1\" + \"Wf_Uso_cobertura@1\" + \"Wf_CurvaturaPlano@1\" + \"Wf_Pendiente@1\" + \"Wf_Cambio_cobertura@1\"'

            else: 
                # Si cambio de cobertura no existe no se tiene en cuenta para la suma de pesos
                Expresion = '\"Wf_UGS@1\" + \"Wf_Geomorfologia@1\" + \"Wf_Uso_cobertura@1\" + \"Wf_CurvaturaPlano@1\" + \"Wf_Pendiente@1\"'

            # Dirección del resultado de la suma de los Wf
            Output = data_path + f'/{carpeta}/Suma_LSI.tif'

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

            # Se define el archivo raster para el procedimiento
            rasterfile = data_path + f'/{carpeta}/Suma_LSI.tif'

            # Se corta según la zona de estudio
            if os.path.isfile(data_path + '/Pre_Proceso/Zona_Estudio.shp') is True:
                Zona_Estudio = QgsVectorLayer(data_path + '/Pre_Proceso/Zona_Estudio.shp', 'Zona_Estudio')
                
                # Se corta la capa LSI según la zona de estudio
                alg = "gdal:cliprasterbymasklayer"
                Capa_LSI = rasterfile
                Capa_LSI_Ajustada = data_path + f'/{carpeta}/LSI.tif'
                params = {'INPUT': Capa_LSI, 'MASK': Zona_Estudio, 'SOURCE_CRS': None,
                'TARGET_CRS': None, 'NODATA': None, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None, 'Y_RESOLUTION': None,
                'MULTITHREADING': False, 'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '', 'OUTPUT': Capa_LSI_Ajustada}
                processing.run(alg, params)
                
                # Se redefine la capa raster para el procedimiento
                rasterfile = data_path + f'/{carpeta}/LSI.tif'
                
            # Se agrega la capa raster LSI al lienzo
            LSI = QgsRasterLayer(rasterfile, "LSI")
            QgsProject.instance().addMapLayer(LSI)

            # Se lee el archivo correspondientes a deslizamientos
            Deslizamientos = QgsVectorLayer(data_path + f'/Pre_Proceso/Deslizamientos_{curva}.shp')

            # Dependiendo de la geometría de los deslizamientos se hace el procedimiento

            if Deslizamientos.wkbType() == QgsWkbTypes.Point:
                # Obtenermos el id de la caracteristica del punto de deslizamiento
                alg = "qgis:rastersampling"
                output = data_path + f'/{carpeta}/ValoresLSI.shp'
                params = {'INPUT': Deslizamientos, 'RASTERCOPY': rasterfile, 'COLUMN_PREFIX': 'Id_Condici', 'OUTPUT': output}
                processing.run(alg, params)
                
                # Valores LSI en los puntos de deslizamiento
                ValoresRaster = QgsVectorLayer(data_path + f'/{carpeta}/ValoresLSI.shp', 'ValoresLSI')
                
            else:
                # Se hace la interesección de el factor condicionante con el área de deslizamientos
                # Obteniendo así los atributos correspondintes a deslizamientos 
                alg = "gdal:cliprasterbymasklayer"
                Factor_Condicionante = rasterfile
                Deslizamiento_Condicion = data_path + f'/{carpeta}/DeslizamientosLSI.tif'
                params = {'INPUT': Factor_Condicionante, 'MASK': Deslizamientos, 'SOURCE_CRS': None,
                'TARGET_CRS': None, 'NODATA': None, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True,
                'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None, 'Y_RESOLUTION': None, 'MULTITHREADING': False,
                'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '', 'OUTPUT': Deslizamiento_Condicion}
                processing.run(alg, params)
                
                # Se obtienen las estadísticas zonales de la capa en cuestión (número de pixeles por atributo por deslizamiento)
                alg = "native:rasterlayerzonalstats"
                Estadisticas_Deslizamiento = data_path + f'/{carpeta}/DeslizamientosLSIEstadistica.csv'
                params = {'INPUT': Deslizamiento_Condicion, 'BAND': 1, 'ZONES': Deslizamiento_Condicion, 'ZONES_BAND': 1,
                          'REF_LAYER': 0, 'OUTPUT_TABLE': Estadisticas_Deslizamiento}
                processing.run(alg, params)
                
                # Lectura de las estadísticas de la zona de deslizamientos como dataframe
                Estadisticas_Deslizamiento = data_path + f'/{carpeta}/DeslizamientosLSIEstadistica.csv'
                DF_DeslizamientosEstadistica = pd.read_csv(Estadisticas_Deslizamiento, delimiter=",", encoding = 'latin-1')
                
            # Se obtienen las estadísticas zonales de los resultados LSI.
            alg = "native:rasterlayerzonalstats"
            output = data_path + f'/{carpeta}/LSIEstadistica.csv'
            params = {'INPUT': rasterfile, 'BAND': 1, 'ZONES': rasterfile, 'ZONES_BAND': 1, 'REF_LAYER': 0, 'OUTPUT_TABLE': output}
            processing.run(alg, params)

            # Se cargan los archivos necesario para el proceso
            # Valores unicos del factor condicionante
            FILE_NAME = data_path + f'/{carpeta}/LSIEstadistica.csv'
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
            df = df.rename(columns={0 : 'LSI'})
            
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
            percentiles = [np.percentile(df['LSI'], 100) + 0.001]
            for i in range(1, len(n_percentil)-1):
                Valor = np.percentile(df['LSI'], n_percentil[i])
                percentiles.append(Valor)
            percentiles.append(np.percentile(df['LSI'], 0) - 0.001)

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
                self.bar.pushMessage("Ajuste LSI", f'La función final de susceptibilidad es aceptable con un area de {Area_Total}', Qgis.Info, 10)
            else:
                self.bar.pushMessage("Ajuste LSI", f'La función final de susceptibilidad NO es aceptable con un area de {Area_Total}', Qgis.Warning, 10)

            # Se identifican los valores Y para asignar el rango de susceptibilidad
            # Alta
            DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] <= suscep_alta)].index, 'Categoria'] = 2
            DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] <= suscep_alta)].index, 'Susceptibilidad'] = 'Alta'
            # Media
            DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > suscep_alta) & (DF_Susceptibilidad['Y'] <= suscep_media)].index, 'Categoria'] = 1
            DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > suscep_alta) & (DF_Susceptibilidad['Y'] <= suscep_media)].index, 'Susceptibilidad'] = 'Media'
            # Baja
            DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > suscep_media)].index, 'Categoria'] = 0
            DF_Susceptibilidad.loc[DF_Susceptibilidad.loc[(DF_Susceptibilidad['Y'] > suscep_media)].index, 'Susceptibilidad'] = 'Baja'

            # Se imprime la tabla y se guarda como archivo CSV
            print(DF_Susceptibilidad)
            DF_Susceptibilidad.reset_index().to_csv(data_path + f'/{carpeta}/DF_LSI.csv', header=True, index=False)

            # Extracción de los valores para la curva de éxito.
            x = DF_Susceptibilidad['X']
            y = DF_Susceptibilidad['Y']
            # Se hace las espacialización de los valores
            fig, ax = plt.subplots()
            ax.plot(x, y, color = 'black', label = "Success curve")
            # Se hacen las líneas correspondientes para clasificar la susceptibilidad
            y1 = suscep_alta
            ax.axhline(y1, lw = 0.5, alpha = 0.7, linestyle = "--", label = f"Y = {suscep_alta}", color = 'orangered')
            y2 = suscep_media
            ax.axhline(y2, lw = 0.5, alpha = 0.7, linestyle = "--", label = f"Y = {suscep_media}", color = 'green')
            plt.legend(loc = 'upper left')
            # Se colorean los rangos de susceptibilidad
            ax.fill_between(x, y, where= (y < y1), facecolor = 'orange', edgecolor = 'orangered', linewidth = 3, alpha = 0.5)
            ax.fill_between(x, y, where= (y >= y1) & (y < y2), facecolor = 'yellow', edgecolor = 'yellow', linewidth = 3, alpha = 0.5)
            ax.fill_between(x, y, where= (y >= y2), facecolor = 'green', edgecolor = 'green', linewidth = 3, alpha = 0.5)
            # Se aplican los nombres de los ejes y título
            ax.set_xlabel("PORCENTAJE DE LA ZONA DE ESTUDIO")
            ax.set_ylabel("PORCENTAJE DE LA ZONA DE DESLIZAMIENTOS")
            ax.set_title(f"CURVA DE {curva.upper()}, Área: {round(Area_Total,2)}", pad = 20, fontdict = {'fontsize': 20, 'color': '#4873ab'})
            plt.show()  # Se muestra la gráfica
            fig.savefig(data_path+f'/{carpeta}/{carpeta}.jpg')  # Se guarda la gráfica en formato .jpg
            
            if curva == 'Exito':
            
                # Reclasificación del mapa raster
                alg = "native:reclassifybylayer"
                RasterReclass = data_path + f'/{carpeta}/LSI.tif'
                Tabla = data_path + f'/{carpeta}/DF_LSI.csv'
                Salida = data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif'
                params = {
                    'INPUT_RASTER': RasterReclass, 'RASTER_BAND': 1, 'INPUT_TABLE': Tabla, 'MIN_FIELD': 'LSI_Min',
                    'MAX_FIELD': 'LSI_Max', 'VALUE_FIELD': 'Categoria', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 1,
                    'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5, 'OUTPUT': Salida}
                processing.run(alg, params)

                # Se agrega la capa reclasificada con los rangos de susceptibilidad
                Susceptibilidad = QgsRasterLayer(data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif', "Susceptibilidad_Deslizamientos")
                QgsProject.instance().addMapLayer(Susceptibilidad)
                
                # Se cambia la simbología de la capa de susceptibilidad
                fnc = QgsColorRampShader()
                fnc.setColorRampType(QgsColorRampShader.Interpolated)
                lst = [QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#36b449'), 'Baja'),QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#d4e301'), 'Media'),QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#dc7d0f'), 'Alta')]
                fnc.setColorRampItemList(lst)
                shader = QgsRasterShader()
                shader.setRasterShaderFunction(fnc)
                renderer = QgsSingleBandPseudoColorRenderer(Susceptibilidad.dataProvider(), 1, shader)
                Susceptibilidad.setRenderer(renderer)
                
        """
        04_Susceptibilidad_Caidas
        """
        
        # #######################Zonificación de Susceptibilidad por zonas de inicio tipo Caida####################### #

        # Se determina la ruta de la pendiente
        Pendiente = self.Pendiente.currentText()

        #Se reclasifica teniendo en cuenta que 0 serán las pendientes menores a 45, y serán 1 las pendientes mayores a 45.
        alg = "native:reclassifybytable"
        Pendientes = data_path + '/' + Pendiente
        Suscep_Caida_Pendiente = data_path+'/Pre_Proceso/Suscep_Caida_Pendiente.tif'
        table = [0, slope, 0, slope, 100, 5]  # [min1, max1, valor1, min2, max2, valor2]  min<valor<=max
        params = {'INPUT_RASTER': Pendientes,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 0,
                  'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Suscep_Caida_Pendiente}
        processing.run(alg, params)

        # Asiganción de valor según SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS

        # Geoformas indicativas de proceso tipo caida
        FILE_NAME = data_path + '/' + GeoformasIndicativas_Caida
        DF_GeoformasIndicativas = pd.read_csv(FILE_NAME, delimiter = ";", encoding = 'latin-1')
        # Se extraen solo los tres primeros caracteres del acronimo teniendo en cuenta que las coincidencias no son exactas
        DF_GeoformasIndicativas['CODIGO'] = DF_GeoformasIndicativas['ACRONIMO'].astype(str).str[0:3]

        # Geoformas existentes en la capa
        Geomorfologia = self.Geomorfologia.currentText()
        indice = Geomorfologia.index('.')
        Geomorfologia = Geomorfologia[:indice]
        FILE_NAME = data_path + f'/Pre_Proceso/DF_Raster_{Geomorfologia}.csv'
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
                
                if math.isnan(Valor) is True:
                    # Si se encuentra un valor pero este es NaN también se asigna susceptibilidad baja
                    DF_SubunidadesGeoform.loc[i, 'Valor'] = 0
                    DF_SubunidadesGeoform.loc[i, 'Base_datos'] = "No encontrado"
                    Geoformas_NaN.append(Subunidad)
                
                else:
                    # Si el valor encontrado era correcto se asigna 
                    DF_SubunidadesGeoform.loc[i,'Valor'] = Valor
                    DF_SubunidadesGeoform.loc[i, 'Base_datos'] = "Encontrado"
                
                # Se devuelve al indice númerico para continuar con el for
                DF_GeoformasIndicativas.reset_index(level = 0, inplace = True)

        # Se imprimen las subunidades no encontradas
        print('No se encontraró la categoría de susceptibilidad para las siguientes subunidades geomorfologicas')
        print(Geoformas_NaN)

        # Se eliminan las columnas no necesarias en el análisis
        DF_SubunidadesGeoform = DF_SubunidadesGeoform.drop(['General'], axis = 1)
        DF_SubunidadesGeoform = DF_SubunidadesGeoform.drop(['Caract_3'], axis = 1)
        # Se imprimen las categorías finales asignadas
        print('Subunidades geomorfologicas encontradas en el área de estudio: ')
        print(DF_SubunidadesGeoform)
        DF_SubunidadesGeoform.reset_index().to_csv(data_path + '/Pre_Proceso/DF_RasterCaida_SubunidadesGeoform.csv', header = True, index = False)

        # Se verifica si el usuario está de acuerdo con las categorías de susceptibilidad
        QMessageBox.information(self, "Categorías de susceptibilidad según las subunidades geomorfologicas",
                                f'Las siguientes subunidades geomorfologicas no fueron encontradas en la base de datos: {Geoformas_NaN}, '
                                'por lo que se le asignaron la categoría de susceptibilidad BAJA. '
                                'Si desea hacer algun ajuste vaya a la carpeta de Pre_Proceso y busque el archivo "DF_RasterCaida_SubunidadesGeoform.csv" '
                                'dónde puede cambiar en la columna "Valor" la categoría de susceptibilidad teniendo en cuenta que 0: Baja, 1: Media y 2: Alta, '
                                'haga el ajuste y guarde ANTES de dar "Aceptar", si está de acuerdo con las categorías puede continuar')

        #Reclasificación del raster con el valor de Susceptibilidad correspondiente a SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS.
        alg="native:reclassifybylayer"
        Geomorfologia = self.Geomorfologia.currentText()
        indice = Geomorfologia.index('.')
        Geomorfologia = Geomorfologia[:indice]
        Factor_Condicionante = data_path + f'/Pre_Proceso/{Geomorfologia}.tif'
        DF_SubunidadesGeomorf = data_path + '/Pre_Proceso/DF_RasterCaida_SubunidadesGeoform.csv'
        Suscep_Caida_SubunidadesGeomorf = data_path + '/Pre_Proceso/Suscep_Caida_SubunidadesGeomorf.tif'
        params={'INPUT_RASTER': Factor_Condicionante, 'RASTER_BAND': 1,'INPUT_TABLE': DF_SubunidadesGeomorf, 'MIN_FIELD': 'ID',
                'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Valor', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2, 'NODATA_FOR_MISSING': True, 'DATA_TYPE': 5,
                'OUTPUT': Suscep_Caida_SubunidadesGeomorf}
        processing.run(alg, params)

        #Asignación de valor según TIPO DE ROCA
        #UGS de la zona
        Geologia = self.Geologia.currentText()
        indice = Geologia.index('.')
        Geologia = Geologia[:indice]
        FILE_NAME = data_path + f'/Pre_Proceso/DF_Raster_{Geologia}.csv'
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
        DF_UGS.reset_index().to_csv(data_path + f'/Pre_Proceso/DF_Raster_{Geologia}.csv', header = True, index = False)

        QMessageBox.information(self, "Categorías de susceptibilidad según las UGS",
                                f'Las UGS fueron caracterizadas según el DataFrame impreso'
                                'Si desea hacer algun ajuste vaya a la carpeta de Pre_Proceso y busque el archivo "DF_Raster_UGS.csv" '
                                'dónde puede cambiar en la columna "Valor" la categoría de susceptibilidad teniendo en cuenta que 0: Baja, 2: Media y 5: Alta, '
                                'haga el ajuste y guarde ANTES de dar "Aceptar", si está de acuerdo con las categorías puede continuar')

        # Reclasificación del raster con el valor de Susceptibilidad correspondiente al TIPO DE ROCA.
        alg="native:reclassifybylayer"
        Factor_Condicionante = data_path + f'/Pre_Proceso/{Geologia}.tif'
        DF_UGS = data_path + f'/Pre_Proceso/DF_Raster_{Geologia}.csv'
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
            QMessageBox.information("!Tenga en cuenta!",
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
        Susceptibilidad = QgsRasterLayer(data_path + '/Resultados/Susceptibilidad_Caida.tif', "Susceptibilidad_Caida")
        QgsProject.instance().addMapLayer(Susceptibilidad)

        # Se cambia la simbología de la capa de susceptibilidad
        fnc = QgsColorRampShader()
        fnc.setColorRampType(QgsColorRampShader.Interpolated)
        lst = [QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#36b449'), 'Baja'),QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#d4e301'), 'Media'),QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#dc7d0f'), 'Alta')]
        fnc.setColorRampItemList(lst)
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)
        renderer = QgsSingleBandPseudoColorRenderer(Susceptibilidad.dataProvider(), 1, shader)
        Susceptibilidad.setRenderer(renderer)
        
        """
        04_Susceptibilidad_Flujos
        """
        
        #Asiganción de valor según SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS
        #Geoformas indicativas de proceso tipo flujo
        FILE_NAME = data_path + '/' + GeoformasIndicativas_Flujos
        DF_GeoformasIndicativas = pd.read_csv(FILE_NAME, delimiter=";",encoding='latin-1')
        # Se extraen solo los tres primeros caracteres del acronimo teniendo en cuenta que las coincidencias no son exactas
        DF_GeoformasIndicativas['CODIGO'] = DF_GeoformasIndicativas['ACRONIMO'].astype(str).str[0:3]

        # Geoformas existentes en la capa
        Geomorfologia = self.Geomorfologia.currentText()
        indice = Geomorfologia.index('.')
        Geomorfologia = Geomorfologia[:indice]
        FILE_NAME = data_path + f'/Pre_Proceso/DF_Raster_{Geomorfologia}.csv'
        DF_SubunidadesGeoform = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
        DF_SubunidadesGeoform.drop(['index'],axis='columns',inplace=True)
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
                
                if math.isnan(Valor) is True: 
                    # Si se encuentra un valor pero este es NaN también se asigna susceptibilidad baja
                    DF_SubunidadesGeoform.loc[i, 'Valor'] = 0
                    DF_SubunidadesGeoform.loc[i, 'Base_datos'] = "No encontrado"
                    Geoformas_NaN.append(Subunidad)
                
                else:
                    # Si el valor encontrado era correcto se asigna 
                    DF_SubunidadesGeoform.loc[i,'Valor'] = Valor
                    DF_SubunidadesGeoform.loc[i, 'Base_datos'] = "Encontrado"
                
                # Se devuelve al indice númerico para continuar con el for
                DF_GeoformasIndicativas.reset_index(level=0, inplace = True)

        # Se imprimen las subunidades no encontradas
        print('No se encontraró la categoría de susceptibilidad para las siguientes subunidades geomorfologicas')
        print(Geoformas_NaN)

        # Se eliminan las columnas no necesarias en el análisis
        DF_SubunidadesGeoform = DF_SubunidadesGeoform.drop(['General'], axis = 1)
        DF_SubunidadesGeoform = DF_SubunidadesGeoform.drop(['Caract_3'], axis = 1)
        # Se imprimen las categorías finales asignadas
        print('Subunidades geomorfologicas encontradas en el área de estudio: ')
        print(DF_SubunidadesGeoform)
        DF_SubunidadesGeoform.reset_index().to_csv(data_path+'/Pre_Proceso/DF_RasterFlujo_SubunidadesGeoform.csv', header = True, index = False)

        # Se verifica si el usuario está de acuerdo con las categorías de susceptibilidad
        QMessageBox.information(self, "Categorías de susceptibilidad según las subunidades geomorfologicas",
                                f'Las siguientes subunidades geomorfologicas no fueron encontradas en la base de datos: {Geoformas_NaN}, '
                                'por lo que se le asignaron la categoría de susceptibilidad BAJA. '
                                'Si desea hacer algun ajuste vaya a la carpeta de Pre_Proceso y busque el archivo "DF_RasterFlujo_SubunidadesGeoform.csv" '
                                'dónde puede cambiar en la columna "Valor" la categoría de susceptibilidad teniendo en cuenta que 0: Baja, 1: Media y 2: Alta, '
                                'haga el ajuste y guarde ANTES de dar "Aceptar", si está de acuerdo con las categorías puede continuar')

        # Se define el raster de las subunidades geomorfologicas
        Factor_Condicionante = data_path + '/Pre_Proceso/SubunidadesGeomorf.tif'

        # Se corta según la zona de estudio
        if os.path.isfile(data_path + '/Pre_Proceso/Zona_Estudio.shp') is True:
            Zona_Estudio = QgsVectorLayer(data_path + '/Pre_Proceso/Zona_Estudio.shp', 'Zona_Estudio')
            
            # Se corta la capa de la suma según la zona de estudio
            alg = "gdal:cliprasterbymasklayer"
            Geomorfologia = self.Geomorfologia.currentText()
            indice = Geomorfologia.index('.')
            Geomorfologia = Geomorfologia[:indice]
            Subunidades = data_path + f'/Pre_Proceso/{Geomorfologia}.tif'
            Subunidades_Ajustada = data_path + '/Pre_Proceso/SubunidadesGeomorf_Ajustada.tif'
            params = {'INPUT': Subunidades, 'MASK': Zona_Estudio, 'SOURCE_CRS': None,
            'TARGET_CRS': None, 'NODATA': None, 'ALPHA_BAND': False, 'CROP_TO_CUTLINE': True,
            'KEEP_RESOLUTION': False, 'SET_RESOLUTION': False, 'X_RESOLUTION': None, 'Y_RESOLUTION': None,
            'MULTITHREADING': False, 'OPTIONS': '', 'DATA_TYPE': 0, 'EXTRA': '', 'OUTPUT': Subunidades_Ajustada}
            processing.run(alg, params)
            
            # Se redefine la capa raster para el procedimiento
            Factor_Condicionante = data_path + '/Pre_Proceso/SubunidadesGeomorf_Ajustada.tif'

        #Reclasificación del raster con el valor de Susceptibilidad correspondiente.
        alg="native:reclassifybylayer"
        DF_SubunidadesGeomorf = data_path+'/Pre_Proceso/DF_RasterFlujo_SubunidadesGeoform.csv'
        Susceptibilidad_Flujo = data_path + '/Resultados/Susceptibilidad_Flujo.tif'
        params={'INPUT_RASTER': Factor_Condicionante, 'RASTER_BAND': 1, 'INPUT_TABLE': DF_SubunidadesGeomorf, 'MIN_FIELD': 'ID',
                'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Valor', 'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,
                'OUTPUT': Susceptibilidad_Flujo}
        processing.run(alg,params)

        # Se agrega la capa reclasificada con los rangos de susceptibilidad
        Susceptibilidad = QgsRasterLayer(data_path + '/Resultados/Susceptibilidad_Flujo.tif', "Susceptibilidad_Flujo")
        QgsProject.instance().addMapLayer(Susceptibilidad)
        
        # Se cambia la simbología de la capa de susceptibilidad
        fnc = QgsColorRampShader()
        fnc.setColorRampType(QgsColorRampShader.Interpolated)
        lst = [QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#36b449'), 'Baja'),QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#d4e301'), 'Media'),QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#dc7d0f'), 'Alta')]
        fnc.setColorRampItemList(lst)
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)
        renderer = QgsSingleBandPseudoColorRenderer(Susceptibilidad.dataProvider(), 1, shader)
        Susceptibilidad.setRenderer(renderer)
        
        """
        05_Susceptibilidad_Final
        """
        
        # Se reclasifican la susceptibilidad alta de 2 a 3 para que no hayan valores erroneos en la susceptibilidad final

        # Susceptibilidad deslizamientos
        alg = "native:reclassifybytable"
        Susceptibilidad_Deslizamientos = data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif'
        Susceptibilidad_Deslizamientos_Reclass = data_path + '/Pre_Proceso/Susceptibilidad_Deslizamientos_Reclass.tif'
        table = [0, 0, 0, 1, 1, 1, 2, 2, 3]  # [min1, max1, valor1, min2, max2, valor2, min3, max3, valor3]  min<=valor<=max
        params = {'INPUT_RASTER': Susceptibilidad_Deslizamientos,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,
                  'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Deslizamientos_Reclass}
        processing.run(alg, params)

        # Susceptibilidad caídas
        alg = "native:reclassifybytable"
        Susceptibilidad_Caida = data_path + '/Resultados/Susceptibilidad_Caida.tif'
        Susceptibilidad_Caida_Reclass = data_path + '/Pre_Proceso/Susceptibilidad_Caida_Reclass.tif'
        table = [0, 0, 0, 1, 1, 1, 2, 2, 3]  # [min1, max1, valor1, min2, max2, valor2, min3, max3, valor3]  min<=valor<=max
        params = {'INPUT_RASTER': Susceptibilidad_Caida,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 2,
                  'NODATA_FOR_MISSING': True,'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Caida_Reclass}
        processing.run(alg, params)

        # Susceptibilidad flujos
        alg = "native:reclassifybytable"
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
        alg = "native:reclassifybytable"
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
        
        # Se cambia la simbología de la capa de susceptibilidad
        fnc = QgsColorRampShader()
        fnc.setColorRampType(QgsColorRampShader.Interpolated)
        lst = [QgsColorRampShader.ColorRampItem(0, QtGui.QColor('#36b449'), 'Baja'),QgsColorRampShader.ColorRampItem(1, QtGui.QColor('#d4e301'), 'Media'),QgsColorRampShader.ColorRampItem(2, QtGui.QColor('#dc7d0f'), 'Alta')]
        fnc.setColorRampItemList(lst)
        shader = QgsRasterShader()
        shader.setRasterShaderFunction(fnc)
        renderer = QgsSingleBandPseudoColorRenderer(Susceptibilidad_Final.dataProvider(), 1, shader)
        Susceptibilidad_Final.setRenderer(renderer)

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
            
        elapsed_time = time() - start_time
        QMessageBox.information(self, "Finalizó de análisis de Susceptibilidad", "Elapsed time: %0.10f seconds." % elapsed_time)

    # ##################################### ANÁLISIS DE AMENAZA ##################################### #
    
    def Amenaza(self):
    
        #Se determina el momento en que inicia la ejcución del programa
        start_time = time()
        
        # Se verifica nuevamente el sistema coordenado de referencia
        if self.mQgsProjectionSelectionWidget.crs().isValid():
            
            if self.mQgsProjectionSelectionWidget.crs().isGeographic(): # if it is a geografic 
                
                QMessageBox.information(self, "!SRC plano!",
                        'Por favor seleccione un Sistema Coordenado de Referencia Plano')
                        
        EPSG_code = self.mQgsProjectionSelectionWidget.crs().authid()
        print(f'EPSG_code = {EPSG_code}')
        EPSG_name = self.mQgsProjectionSelectionWidget.crs().description()
        print(f'EPSG_name = {EPSG_name}')
        
        data_path = self.Ruta_General.text()
        
        SRC_Destino = EPSG_code #Revisar
        
        #Estaciones pluviométricas
        Estaciones = self.Estaciones.currentText()
        Ruta_Estaciones = data_path + '/' + Estaciones
        Estaciones = QgsVectorLayer(Ruta_Estaciones)
        
        # Código de la estación pluviométrica
        Codigo_Estacion = self.Codigo_Estacion.currentText()
        
        # Sismos
        Sismos = self.Sismos.currentText()
        Ruta_Sismos = data_path + '/' + Sismos
        Sismos = QgsVectorLayer(Ruta_Sismos)
        
        # Variables de la capa vectorial de sismos
        Magnitud_Sismo = self.Magnitud_Sismo.currentText()
        Unidad_Sismo = self.Unidad_Sismo.currentText()
        Fecha_Sismo = self.Fecha_Sismo.currentText()
        Autor = self.Autor.currentText()
        
        # Movimientos en masa
        Mov_Masa = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa.shp')
        Fecha_MM = self.Fecha_MM.currentText()
        Tipo_MM = self.Tipo_MM.currentText()
        dias = self.umbral_dias.value()
        grupo = self.grupo.value()
        
        # Precipitación diaria
        Precipitacion = self.Precipitacion.currentText()
        Ruta_Precipitacion = data_path + '/' + Precipitacion
        
        # Campo de la fecha correspondiente a las precipiaciones
        Fecha_Precip = self.Fecha_Precip.currentText()
        
        # Se extrae el número de días anteriores para la precipitación anterior
        d_ant = self.d_ant.value()
        
        # Se extrae la precipitación mínima y el número de días umbral 
        # para la corrección de las fechas de los MM
        umbral_dias = self.umbral_dias.value()
        umbral_lluvia = self.umbral_lluvia.value()
        
        # Se extrae la norma que se tendrá en cuenta para el análisis
        Norma = self.Norma.currentText()
        
        # Se define la discretización de los movimientos en masa para los análisis 
        Discritizacion = self.Discritizacion.currentText()
        
        """
        06_Amenaza_Insumos
        """

        # Susceptibilidad por deslizamientos
        Susceptibilidad_Deslizamientos = QgsRasterLayer(data_path + '/Resultados/Susceptibilidad_Deslizamientos.tif',
                                                "Susceptibilidad_Deslizamientos")
        
        # ############################# PREPARACIÓN DE MOVIMIENTOS ############################# #

        # Se reproyecta la capa a coordenadas planas
        alg = "native:reprojectlayer"
        CRS = QgsCoordinateReferenceSystem(SRC_Destino)
        Reproyectada = data_path + '/Pre_Proceso/Mov_Masa_Reproyectada.shp'
        params = {'INPUT': Mov_Masa, 'TARGET_CRS': CRS, 'OUTPUT': Reproyectada}
        processing.run(alg, params)

        # Se lee la nueva capa de MM
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

        # Se inicia a editar la capa
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

        # Se agrupan los movimientos por medio de un Cluster
        alg = "native:kmeansclustering"
        Cluster = data_path + '/Pre_Proceso/Mov_Masa_Cluster.shp'
        params = {'INPUT': Mov_Masa,'CLUSTERS': grupo,'FIELD_NAME': 'CLUSTER_ID','OUTPUT': Cluster}
        processing.run(alg, params)

        # Se lee la nueva capa de MM
        Mov_Masa = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Cluster.shp')

        # Se determina el índice de la columna del cluster
        col = Mov_Masa.fields().indexFromName("CLUSTER_ID")

        # Se selecciona los puntos del cluster correspondiente al valor de 0
        Mov_Masa.selectByExpression(f'"CLUSTER_ID"=\'0\'', QgsVectorLayer.SetSelection)
            
        # Se determinan los puntos seleccionados
        selection = Mov_Masa.selectedFeatures()

        #Se inicia a editar la capa
        caps = Mov_Masa.dataProvider().capabilities()

        for feature in selection:  # Se recorren las filas seleccionadas
            fid = feature.id()  # Se obtiene el id de la fila seleccionada
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                # Se cambia por el valor de grupo
                attrs = {col: grupo}
                # Se hace el cambio de los atributos
                Mov_Masa.dataProvider().changeAttributeValues({fid: attrs})

        # ############################# POLIGONOS DE ANÁLISIS ############################# #

        # SISMOS CON BASE EN EL NÚMERO DE GRUPOS

        #Se obtienen los centroides de los grupos de movimientos
        alg = "native:meancoordinates"
        Centroides = data_path + '/Pre_Proceso/Centroides_Cluster.shp'
        params = {'INPUT': Mov_Masa,'WEIGHT':'CLUSTER_ID','UID':'CLUSTER_ID','OUTPUT': Centroides}
        processing.run(alg, params)

        # Si se tiene suficientes grupos se crean los poligonos de Voronoi
        if grupo > 2:
            # Se crean los poligonos de análisis de sismos con base en los centroides
            alg = "qgis:voronoipolygons"
            Poligonos = data_path + '/Pre_Proceso/Poligonos_Buffer_Sismo.shp'
            params = {'INPUT': Centroides,'BUFFER':100,'OUTPUT': Poligonos}
            processing.run(alg, params)

        else:
            # Si solo se cuenta con una o dos grupos se crea un buffer del punto
            alg = "native:buffer"
            Poligonos = data_path + '/Pre_Proceso/Poligonos_Buffer_Sismo.shp'
            params = {'INPUT': Centroides, 'DISTANCE':10000, 'SEGMENTS':5,
                      'END_CAP_STYLE':0, 'JOIN_STYLE':0, 'MITER_LIMIT':2,
                      'DISSOLVE':False, 'OUTPUT':Poligonos}
            processing.run(alg, params)

        # Se cortan los poligonos de sismos según la extensión de análisis
        alg = "gdal:clipvectorbyextent"
        Salida = data_path + '/Amenaza/Amenaza_Sismos.shp'
        extents = Susceptibilidad_Deslizamientos.extent()  # Capa de referencia de la extensión
        xmin = extents.xMinimum()  # xmin de la extensión
        xmax = extents.xMaximum()  # xmax de la extensión
        ymin = extents.yMinimum()  # ymin de la extensión
        ymax = extents.yMaximum()  # ymax de la extensión
        params = {'INPUT': Poligonos,'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),
                  'OPTIONS':'','OUTPUT': Salida}
        processing.run(alg, params)

        # LLUVIA CON BASE EN EL NÚMERO DE ESTACIONES

        # Se determina cuántas estaciones hay
        flat_list = []
        for item in Estaciones.getFeatures():  # Se recorren las filas de la capa
            fid = item.id()  # Se obtiene el id de la fila en cuestión
            flat_list.append(fid)
        Num_Estaciones = len(flat_list)

        # Si se tiene suficientes estaciones se crean los poligonos de Voronoi
        if Num_Estaciones > 2:
            # Se crean los poligonos de Voronoi dónde se espacializará la amenaza por lluvia
            alg = "qgis:voronoipolygons"
            Poligonos = data_path + '/Pre_Proceso/Poligonos_Buffer_Lluvia.shp'
            params = {'INPUT': Estaciones, 'BUFFER':100, 'OUTPUT': Poligonos}
            processing.run(alg, params)

        else:
            # Si solo se cuenta con una o dos estaciones se crea un buffer del punto
            alg = "native:buffer"
            Poligonos = data_path + '/Pre_Proceso/Poligonos_Buffer_Lluvia.shp'
            params = {'INPUT': Estaciones, 'DISTANCE':10000, 'SEGMENTS':5,
                      'END_CAP_STYLE':0, 'JOIN_STYLE':0, 'MITER_LIMIT':2,
                      'DISSOLVE':False, 'OUTPUT':Poligonos}
            processing.run(alg, params)
            
            
        # Se cortan los poligonos según la extensión de análisis
        alg = "gdal:clipvectorbyextent"
        Salida = data_path + '/Amenaza/Amenaza_Lluvia.shp'
        extents = Susceptibilidad_Deslizamientos.extent()  # Capa de referencia de la extensión
        xmin = extents.xMinimum()  # xmin de la extensión
        xmax = extents.xMaximum()  # xmax de la extensión
        ymin = extents.yMinimum()  # ymin de la extensión
        ymax = extents.yMaximum()  # ymax de la extensión
        params = {'INPUT': Poligonos,'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax),'OPTIONS':'','OUTPUT': Salida}
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
        params = {'INPUT': Shape, 'FIELD': Field, 'BURN': 0, 'UNITS': 1, 'WIDTH': 12.5, 'HEIGHT': 12.5,
                  'EXTENT': "%f,%f,%f,%f" % (xmin, xmax, ymin, ymax), 'NODATA': 0, 'OPTIONS': '',
                  'DATA_TYPE': 5, 'INIT': None, 'INVERT': False, 'OUTPUT': Raster}
        processing.run(alg, params)

        # Se muestrea el id de los poligonos
        alg = "qgis:rastersampling"
        rasterfile = data_path + '/Pre_Proceso/Poligonos_Voronoi.tif'
        Mov_Masa_Amenaza_Poligono = data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Poligono.shp'
        params = {'INPUT': Mov_Masa, 'RASTERCOPY': rasterfile,
                  'COLUMN_PREFIX': 'Poli_Voron', 'OUTPUT': Mov_Masa_Amenaza_Poligono}
        processing.run(alg, params)

        # ############################# MUESTREO DE SUSCEPTIBILIDAD ############################# # 

        # Se muestrea la susceptibilidad por deslizamientos
        alg = "qgis:rastersampling"
        rasterfile = Susceptibilidad_Deslizamientos
        Mov_Masa_Amenaza_Desliz = data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Desliz.shp'
        params = {'INPUT': Mov_Masa_Amenaza_Poligono, 'RASTERCOPY': rasterfile,
                  'COLUMN_PREFIX': 'Susc_Desli', 'OUTPUT': Mov_Masa_Amenaza_Desliz}
        processing.run(alg, params)

        # Se guarda el archivo como CSV
        Mov_Masa_Amenaza_Desliz = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Desliz.shp')
        Archivo_csv = data_path + '/Amenaza/Mov_Masa_Amenaza.csv'
        QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Amenaza_Desliz,
                                               Archivo_csv, "utf-8", Mov_Masa_Amenaza_Desliz.crs(), driverName = "CSV")

        # Susceptibilidad por caídas
        Ruta_Caidas = data_path + '/Resultados/Susceptibilidad_Caida.tif'
        # Se verifica que el archivo exista
        if os.path.isfile(Ruta_Caidas) is True:
            Susceptibilidad_Caidas = QgsRasterLayer(Ruta_Caidas, "Susceptibilidad_Caidas")
            
            # Se muestrea la susceptibilidad por caidas 
            alg = "qgis:rastersampling"
            rasterfile = Susceptibilidad_Caidas
            Mov_Masa_Amenaza_Caida = data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Caida.shp'
            params = {'INPUT': Mov_Masa_Amenaza_Desliz, 'RASTERCOPY': rasterfile,
                      'COLUMN_PREFIX': 'Susc_Caida', 'OUTPUT': Mov_Masa_Amenaza_Caida}
            processing.run(alg, params)
            
            # Se guarda el archivo como CSV
            Mov_Masa_Amenaza_Caida = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Caida.shp')
            Archivo_csv = data_path + '/Amenaza/Mov_Masa_Amenaza.csv'
            QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Amenaza_Caida,
                                                    Archivo_csv, "utf-8", Mov_Masa_Amenaza_Caida.crs(), driverName = "CSV")

        # Susceptibilidad por flujos
        Ruta_Flujos = data_path + '/Resultados/Susceptibilidad_Flujos.tif'
        # Se verifica que el archivo exista
        if os.path.isfile(Ruta_Flujos) is True:
            Susceptibilidad_Flujos = QgsRasterLayer(Ruta_Caidas, "Susceptibilidad_Flujos")
            
            # Dependiendo de las capas existentes se determina el archivo vectorial anterior
            if os.path.isfile(Ruta_Caidas) is True:
                Shape = Mov_Masa_Amenaza_Caida
            else:
                Shape = Mov_Masa_Amenaza_Desliz

            # Se muestrea la susceptibilidad por flujos 
            alg = "qgis:rastersampling"
            rasterfile = Susceptibilidad_Flujos
            Mov_Masa_Amenaza_Flujo = data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Flujo.shp'
            params = {'INPUT': Shape, 'RASTERCOPY': rasterfile,
                      'COLUMN_PREFIX': 'Susc_Flujo', 'OUTPUT': Mov_Masa_Amenaza_Flujo}
            processing.run(alg, params)
            
            # Se guarda el archivo como CSV
            Mov_Masa_Amenaza_Flujo = QgsVectorLayer(data_path + '/Pre_Proceso/Mov_Masa_Amenaza_Flujo.shp')
            Archivo_csv = data_path + '/Amenaza/Mov_Masa_Amenaza.csv'
            QgsVectorFileWriter.writeAsVectorFormat(Mov_Masa_Amenaza_Flujo,
                                                    Archivo_csv, "utf-8", Mov_Masa_Amenaza_Flujo.crs(), driverName = "CSV")

        ############################## ANÁLISIS DE SISMOS ##############################

        # Se reproyecta la capa a coordenadas planas
        alg = "native:reprojectlayer"
        CRS = QgsCoordinateReferenceSystem(SRC_Destino)
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

        # Se guarda el archivo como CSV de los sismos
        Archivo_csv = data_path + '/Amenaza/Sismos.csv'
        QgsVectorFileWriter.writeAsVectorFormat(Sismos, Archivo_csv, "utf-8", Sismos.crs(), driverName = "CSV")

        # Se lee el csv y se unifican los nombres de los atributos
        FILE_NAME = data_path + '/Amenaza/Sismos.csv'
        Sismos = pd.read_csv(FILE_NAME, encoding = 'latin-1')
        Sismos.rename(columns={Unidad_Sismo : 'Unidad'}, inplace=True)
        Sismos.rename(columns={Magnitud_Sismo : 'Magnitud'}, inplace=True)

        # Las unidades se unifican pasandolas a minuscula
        Sismos['Unidad'] = Sismos['Unidad'].str.lower()

        # Se crean los campos de los correpondientes autores
        Sismos['Scordilis'] = None
        Sismos['Grunthal'] = None
        Sismos['Akkar'] = None
        Sismos['Ulusay'] = None
        Sismos['Kadirioglu'] = None
        Sismos['Promedio'] = None

        # Se hace la conversión de unidades a Mw para todos los autores

        #Mb
        Sismos.loc[Sismos["Unidad"].str.startswith('mb') & (Sismos.Magnitud >= 3.5) & (Sismos.Magnitud <= 6.2),
                   'Scordilis'] = 0.85 * Sismos.Magnitud + 1.03
        Sismos.loc[Sismos["Unidad"].str.startswith('mb') & (Sismos.Magnitud <= 6.0),
                   'Grunthal'] = 8.17 - (42.04 - 6.42 * Sismos.Magnitud)**(1/2)
        Sismos.loc[Sismos["Unidad"].str.startswith('mb') & (Sismos.Magnitud >= 3.5) & (Sismos.Magnitud <= 6.3),
                   'Akkar'] = 1.104 * Sismos.Magnitud - 0.194
        Sismos.loc[Sismos["Unidad"].str.startswith('mb'),
                   'Ulusay'] = 1.2413 * Sismos.Magnitud - 0.8994
        Sismos.loc[Sismos["Unidad"].str.startswith('mb') & (Sismos.Magnitud >= 3.9) & (Sismos.Magnitud <= 6.8),
                   'Kadirioglu'] = 1.0319 * Sismos.Magnitud + 0.0223

        #Ml
        Sismos.loc[Sismos["Unidad"].str.startswith('ml') & (Sismos.Magnitud >= 3.5) & (Sismos.Magnitud <= 5),
                   'Grunthal'] = 0.0376 * Sismos.Magnitud**(2) + 0.646 * Sismos.Magnitud + 0.53
        Sismos.loc[Sismos["Unidad"].str.startswith('ml') & (Sismos.Magnitud >= 3.9) & (Sismos.Magnitud <= 6.8),
                   'Akkar'] = 0.953 * Sismos.Magnitud + 0.422
        Sismos.loc[Sismos["Unidad"].str.startswith('ml'),
                   'Ulusay'] = 0.7768 * Sismos.Magnitud + 1.5921
        Sismos.loc[Sismos["Unidad"].str.startswith('ml') & (Sismos.Magnitud >= 3.3) & (Sismos.Magnitud <= 6.6),
                   'Kadirioglu'] = 0.8095 * Sismos.Magnitud + 1.3003

        #Md
        Sismos.loc[Sismos["Unidad"].str.startswith('md') & (Sismos.Magnitud >= 3.7) & (Sismos.Magnitud <= 6),
                   'Akkar'] = 0.764 * Sismos.Magnitud + 1.379
        Sismos.loc[Sismos["Unidad"].str.startswith('md'),
                   'Ulusay'] = 0.9495 * Sismos.Magnitud + 0.4181
        Sismos.loc[Sismos["Unidad"].str.startswith('md') & (Sismos.Magnitud >= 3.5) & (Sismos.Magnitud <= 7.4),
                   'Kadirioglu'] = 0.7947 * Sismos.Magnitud + 1.342
        Sismos.loc[Sismos["Unidad"].str.startswith('md'),
                   'Grunthal'] = 1.472 * Sismos.Magnitud - 1.49

        #Ms
        Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 3) & (Sismos.Magnitud <= 6.1),
                   'Scordilis'] = 0.67 * Sismos.Magnitud + 2.07
        Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 6.2) & (Sismos.Magnitud <= 8.2),
                   'Scordilis'] = 0.99 * Sismos.Magnitud + 0.08
        Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud <= 7),
                   'Grunthal'] = 10.85 - (73.74 - 8.34 * Sismos.Magnitud)**(1/2)
        Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 3) & (Sismos.Magnitud <= 5.5),
                   'Akkar'] = 0.571 * Sismos.Magnitud + 2.484
        Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 5.5) & (Sismos.Magnitud <= 7.7),
                   'Akkar'] = 0.817 * Sismos.Magnitud + 1.176
        Sismos.loc[Sismos["Unidad"].str.startswith('ms'),
                   'Ulusay'] = 0.6798 * Sismos.Magnitud + 2.0402
        Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 3.4) & (Sismos.Magnitud <= 5.4),
                   'Kadirioglu'] = 0.5716 * Sismos.Magnitud + 2.498
        Sismos.loc[Sismos["Unidad"].str.startswith('ms') & (Sismos.Magnitud >= 5.5),
                   'Kadirioglu'] = 0.8126 * Sismos.Magnitud + 1.1723

        # Las magnitudes que si esten con Mw se agregan a todas las columnas
        Sismos.loc[Sismos["Unidad"].str.startswith('mw'), ['Scordilis', 'Grunthal', 'Akkar', 'Ulusay', 'Kadirioglu', 'Promedio']] = Sismos.Magnitud
        # Se hace el promedio de los resultados para obtener Mw
        Sismos['Promedio'] = Sismos[['Scordilis', 'Grunthal', 'Akkar', 'Ulusay', 'Kadirioglu']].mean(axis=1)

        # Se seleccionan los sismos con la magnitud mayor a la minima 
        Sismo_Detonante = Sismos.loc[(Sismos[Autor] >= 5)]
        Sismo_Detonante.reset_index().to_csv(data_path + '/Amenaza/Sismos.csv', header = True, index = False)
        print('Los sismos resultantes son: ')
        print(Sismo_Detonante)

        ############################## DETERMINACIÓN DEL DETONANTE ##############################

        # CSV de los sismos leído como dataframe
        FILE_NAME = data_path + '/Amenaza/Sismos.csv'
        DF_Sismos = pd.read_csv(FILE_NAME, encoding = 'latin-1')
        DF_Sismos[Fecha_Sismo] = pd.to_datetime(DF_Sismos[Fecha_Sismo])

        # CSV de los movimientos en masa leído como dataframe
        FILE_NAME = data_path + '/Amenaza/Mov_Masa_Amenaza.csv'
        DF_Mov_Masa = pd.read_csv(FILE_NAME, encoding = 'latin-1')
        DF_Mov_Masa = DF_Mov_Masa.dropna(axis=0, subset=[Fecha_MM])
        DF_Mov_Masa.reset_index(level=0, inplace=True)
        DF_Mov_Masa[Fecha_MM] = pd.to_datetime(DF_Mov_Masa[Fecha_MM])

        # Se listan las fechas de MM con un respectivo umbral 
        # y atributos de interes como coordenadas e índice
        DF_Fechas_MM = pd.DataFrame()
        for i in range(0, len(DF_Mov_Masa)):
            date = DF_Mov_Masa.loc[i, Fecha_MM]
            DF_Apoyo = pd.DataFrame()
            for j in range(0, dias):
                DF_Apoyo.loc[j, 'Indice'] = i
                DF_Apoyo.loc[j, 'Fecha'] = date - datetime.timedelta(days = j)
                DF_Apoyo.loc[j, 'Reporte'] = date
                DF_Apoyo.loc[j, 'X'] = DF_Mov_Masa.loc[i, 'X']
                DF_Apoyo.loc[j, 'Y'] = DF_Mov_Masa.loc[i, 'Y']
            DF_Fechas_MM = DF_Fechas_MM.append(DF_Apoyo)

        DF_Fechas_MM.reset_index(level=0, inplace=True)

        # Extraigo los valores únicos de las fechas de movimientos en masa y sismos
        DF_Fechas_Mov = DF_Fechas_MM['Fecha'].unique()
        DF_Fechas_Sismo = DF_Sismos[Fecha_Sismo].unique()

        # Se hace la intersección de las fechas de MM y sismos, extrayendo las que coinciden
        Fechas = set(DF_Fechas_Mov).intersection(set(DF_Fechas_Sismo)) 
        Fechas = pd.DataFrame(Fechas, columns = ['date'])

        # Se crea un dataframe para el llenado de los movimientos detonados por sismos
        DF_Mov_Sismos = pd.DataFrame(columns=['Indice'])

        # Se recorren las fechas coincidentes de MM y sismo
        for j in range (0, len(Fechas)):
            # Se determina la fecha de las previamente coincidentes
            Fecha = Fechas.loc[j, 'date']
            # Se determinan los índices de los sismos con la fecha en cuestión
            Indices = DF_Sismos[DF_Sismos[Fecha_Sismo] == Fecha].index
            # Se crea un campo de apoyo para calcular las distancias respectivas
            DF_Fechas_MM['Distancia'] = None
            # Se recorren los índices de los sismos ocurridos en la fecha
            for i in range (0,len(Indices)):
                # Se extraen las coordenadas del sismos correspondientes al índice
                X_Sismo = DF_Sismos.loc[Indices[i], 'X']
                Y_Sismo = DF_Sismos.loc[Indices[i], 'Y']
                # Se cálcula la distancia entre el sismos y los MM ocurridos en la fecha
                DF_Fechas_MM.loc[DF_Fechas_MM['Fecha'] == Fecha,
                                 'Distancia'] = ((DF_Fechas_MM.X - X_Sismo)**(2) + (DF_Fechas_MM.Y - Y_Sismo)**(2))**(1/2)
                
                #Se seleccionan los MM a una distancia menor de 50 km
                DF_Escogido = DF_Fechas_MM.loc[DF_Fechas_MM['Distancia'] < 50000] #50 km - 50000 m
                DF_Fechas_MM.drop(['Distancia'], axis=1)
                
            #Se va llenando el dataframe a medida que se recorren las fechas de intersección
            DF_Mov_Sismos = DF_Mov_Sismos.append(DF_Escogido)

        # Se extraen los índices únicos de los MM resultantes detonados por sismos
        Indices_Mov = DF_Mov_Sismos['Indice'].unique()
        Indices_Mov = Indices_Mov.tolist()

        # Se crea un nuevo campo de detonante en el inventario
        DF_Mov_Masa['Detonante'] = None
        # Los MM de los índices únicos fueron detonados por un sismo
        DF_Mov_Masa.loc[Indices_Mov, 'Detonante'] = "Sismo"
        # Los MM restantes se asocian al detonante lluvia
        DF_Mov_Masa.loc[DF_Mov_Masa.Detonante != "Sismo", 'Detonante'] = "Lluvia"

        # Se renombran las columnas para los posteriores análisis
        DF_Mov_Masa.rename(columns = {Fecha_MM : 'FECHA_MOV'}, inplace = True)
        DF_Mov_Masa.rename(columns = {Tipo_MM : 'TIPO_MOV1'}, inplace = True)

        # Se parte el dataframe con base en el detonante
        DF_Mov_Masa_Sismos = DF_Mov_Masa.loc[DF_Mov_Masa['Detonante'] == 'Sismo']
        DF_Mov_Masa_Lluvias = DF_Mov_Masa.loc[DF_Mov_Masa['Detonante'] == 'Lluvia']

        # Se exporta como csv los MM
        DF_Mov_Masa.reset_index().to_csv(data_path + '/Amenaza/Mov_Masa_Amenaza.csv',
                               header = True, index = False)

        # Se exporta como csv los MM detonados por sismo
        print('Movimientos en masa detonados por sismos: ')
        print(DF_Mov_Masa_Sismos)
        DF_Mov_Masa_Sismos.reset_index().to_csv(data_path + '/Amenaza/DF_Mov_Masa_Sismos.csv',
                                      header = True, index = False)

        # Se espacializan los movimientos en masa detonados por sismos
        alg = "qgis:createpointslayerfromtable"
        Tabla = data_path + '/Amenaza/DF_Mov_Masa_Sismos.csv'
        Shape = data_path + '/Amenaza/Mov_Masa_Sismos.shp'
        params = {'INPUT': Tabla,'XFIELD':'X','YFIELD':'Y','ZFIELD':None,'MFIELD':None,'TARGET_CRS':QgsCoordinateReferenceSystem(SRC_Destino),'OUTPUT': Shape}
        processing.run(alg, params)

        # Se añade la capa al lienzo
        Mov_Masa_Sismos = QgsVectorLayer(data_path + '/Amenaza/Mov_Masa_Sismos.shp', 'Mov_Masa_Sismos')
        QgsProject.instance().addMapLayer(Mov_Masa_Sismos)

        # Se exporta como csv los MM detonados por lluvia
        print('Movimientos en masa detonados por lluvia: ')
        print(DF_Mov_Masa_Lluvias)
        DF_Mov_Masa_Lluvias.reset_index().to_csv(data_path + '/Amenaza/DF_Mov_Masa_Lluvias.csv',
                                       header = True, index = False)

        # Se espacializan los movimientos en masa detonados por lluvia
        alg = "qgis:createpointslayerfromtable"
        Tabla = data_path + '/Amenaza/DF_Mov_Masa_Lluvias.csv'
        Shape = data_path + '/Amenaza/Mov_Masa_Lluvias.shp'
        params = {'INPUT': Tabla,'XFIELD':'X','YFIELD':'Y','ZFIELD':None,'MFIELD':None,'TARGET_CRS':QgsCoordinateReferenceSystem(SRC_Destino),'OUTPUT': Shape}
        processing.run(alg, params)

        # Se añade la capa al lienzo
        Mov_Masa_Lluvias = QgsVectorLayer(data_path + '/Amenaza/Mov_Masa_Lluvias.shp', 'Mov_Masa_Lluvias')
        QgsProject.instance().addMapLayer(Mov_Masa_Lluvias)
        
        """
        07_Amenaza_Lluvia
        """
        
        if len(DF_Mov_Masa_Lluvias) != 0:
            
            # Se determinan las fechas en la que se tiene información de precipitación
            DF_Precipitacion_diaria = pd.read_csv(Ruta_Precipitacion)
            DF_Precipitacion_diaria[Fecha_Precip] = pd.to_datetime(DF_Precipitacion_diaria[Fecha_Precip])
            # Se determinan la fecha inicial y final con la que se cuenta precipitación
            begin = min(DF_Precipitacion_diaria[Fecha_Precip])
            end = max(DF_Precipitacion_diaria[Fecha_Precip])

            # Se lee el inventario de movimientos en masa con fecha y susceptibilidad detonados por lluvias
            DF_Inv = pd.read_csv(data_path + '/Amenaza/DF_Mov_Masa_Lluvias.csv')
            # Se convierte en formato de fecha la fecha 
            DF_Inv['FECHA_MOV'] = pd.to_datetime(DF_Inv.FECHA_MOV)
            DF_Inv = DF_Inv.drop(['level_0'], axis=1) #Borrar

            # Se ordenan los MM según la fecha
            DF_Inv = DF_Inv.sort_values(by = 'FECHA_MOV')
            DF_Inv.reset_index(level=0, inplace = True)
            DF_Inv = DF_Inv.drop(['index'], axis = 1)

            # Se truncan las fechas de MM según las fechas de precipitación con las que se cuente
            DF_Inv.set_index('FECHA_MOV', inplace = True)
            DF_Inv = DF_Inv.truncate(before = begin, after = end)
            DF_Inv.reset_index(level = 0, inplace = True)
            DF_Inv = DF_Inv.drop(['level_0'], axis = 1)

            # Se lee los poligonos correspondientes a las estaciones
            DF_Poligonos = pd.read_csv(data_path + '/Pre_Proceso/DF_Raster_Poligonos_Voronoi.csv')
            DF_Poligonos['Codigo'] = DF_Poligonos['Codigo'].astype(int)
            DF_Poligonos['Codigo'] = DF_Poligonos['Codigo'].astype(str)
            DF_Poligonos.set_index('ID', inplace = True)

            # ############################# CALCULO DE PROBABILIDAD ############################# #

            # Se crea el dataframe con el que se hace el análisis
            DF_Excedencia = pd.DataFrame(columns=['Poli_Thiessen', 'Estacion',
                                                  'Amenaza', 'Tipo_Mov', 'Excedencia',
                                                  'P[R>Rt]', 'N', 'Fr', 'Ptem'])

            # Se crea un datframe de apoyo para ir añadiendo los resultados por poligonos
            DF_Final = pd.DataFrame()

            # Se extraen los valores únicos de poligonos correspondientes a las estaciones
            Poligonos = DF_Inv['Poli_Voron'].unique()

            # Se recorre los valores de poligonos
            for poligono in Poligonos:
                
                # Si la cantidad de datos de ese poligono es menor a dos no se puede hacer el análisis
                if len(DF_Inv[DF_Inv['Poli_Voron'] == poligono]) < 2:
                    print(f'No hay suficientes datos para completar el análisis del poligono {poligono}')
                    continue
                
                # Se pone como indice la columna de los poligonos
                DF_Inv.set_index('Poli_Voron', inplace=True)
                DF_Inv_Poligono = DF_Inv.loc[poligono] # Se extraen los MM correspondientes a ese poligono
                DF_Inv_Poligono.reset_index(level=0, inplace=True)
                DF_Inv.reset_index(level=0, inplace=True)
                
                # Se define la estación correspondiente al poligono
                Estacion = DF_Poligonos.loc[poligono]['Codigo']
                print(poligono, Estacion)
                
                # Se extrae solo las precipitaciones de la estación de interes
                DF_Estacion = DF_Precipitacion_diaria[[Fecha_Precip, Estacion]] 
                
                # Se cálcula la precipitación antecedente según los días antecedentes
                Pant = DF_Estacion[Estacion].rolling(min_periods = d_ant+1, window = d_ant+1).sum()-DF_Estacion[Estacion]
                DF_Estacion['Pant'] = Pant
                
                # Se pasa a formato de fecha el campo de la fecha
                DF_Estacion[Fecha_Precip] = pd.to_datetime(DF_Estacion[Fecha_Precip])
                DF_Estacion[Fecha_Precip] = DF_Estacion[Fecha_Precip].dt.strftime('%d/%m/%Y')
                DF_Estacion[Fecha_Precip] = DF_Estacion[Fecha_Precip].astype(str)
                DF_Estacion['P24'] = DF_Estacion[Estacion]

                #Se extraen los tipos de movimientos en masa que hay en el poligono
                Tipo_Evento = DF_Inv_Poligono['TIPO_MOV1'].unique()
                Tipo_Evento = pd.DataFrame(Tipo_Evento, columns=['Tipo_Mov'], dtype=object)
                
                # Si la descretización es solo por amenaza la extensión del for solo será de 1
                if Discritizacion == "Amenaza": Tipo_Evento = [1]
                
                #Se hace el estudio según el tipo de evento
                for id_evento in range (0, len(Tipo_Evento)): 
                    
                    # Si la descretización es por tipo de movimiento y amenaza
                    if Discritizacion == "Amenaza - Tipo de movimiento":
                        
                        # Se identifica el tipo de movimiento en cuestión
                        Tipo = Tipo_Evento.loc[id_evento, 'Tipo_Mov']
                        
                        # Si los MM correspondientes a este tipo de movimiento son menores a dos no se puede continuar con el análisis
                        if len(DF_Inv_Poligono[DF_Inv_Poligono['TIPO_MOV1'] == Tipo]) < 2:
                            print(f'No hay suficientes datos para completar el análisis del tipo {Tipo}')
                            continue
                        
                        print('\n')
                        print(f'Se hará el análisis para el tipo {Tipo}')
                        print('\n')
                        
                        # Se pone como indice la columna de tipo de movimiento
                        DF_Inv_Poligono.set_index('TIPO_MOV1', inplace=True)
                        # Se selecciona del inventario resultante anteriormente solo los del tipo en cuestión
                        DF_Inv_Tipo = DF_Inv_Poligono.loc[Tipo]
                        DF_Inv_Tipo.reset_index(level=0, inplace=True)
                        DF_Inv_Poligono.reset_index(level=0, inplace=True)
                        
                        # Según el tipo de movimiento en masa se define la categoría de susceptibilidad para el análisis
                        if Tipo == "Deslizamiento":
                            Campo_Amenaza = "Susc_Desli"
                        elif Tipo == "Caida":
                            Campo_Amenaza = "Susc_Caida"
                        elif Tipo == "Flujo":
                            Campo_Amenaza = "Susc_Flujo"
                        else:
                            print(f"No se tiene un análisis para el tipo de movimiento en masa {Tipo}")
                            continue
                    else:
                        # Si no se hará discretización por tipo de movimiento en masa
                        # se copia el inventario anteriormente exportado solo por poligonos
                        DF_Inv_Tipo = DF_Inv_Poligono.copy(deep = True)
                        Campo_Amenaza = "Susc_Desli"
                        Tipo = "Todos"
                    
                    # Si el campo determinado para la discretización de la amenaza no está en el inventario se continua
                    if (Campo_Amenaza in DF_Inv_Tipo.columns) is False:
                        continue
                    
                    # Se definen los valores únicos de amenaza que se tengan
                    Categorias_Amenaza = DF_Inv_Tipo[Campo_Amenaza].unique()
                    Categorias_Amenaza = pd.DataFrame(Categorias_Amenaza, columns = ['Amenaza'], dtype=object)
                    
                    #Se hace el estudio según la categoría de amenaza
                    for id_amenaza in range (0, len(Categorias_Amenaza)): 
                        # Se determina el id de la amenaza
                        Amenaza = Categorias_Amenaza.loc[id_amenaza, 'Amenaza']
                        
                        # Según el id de la amenaza se puede determinar la categoria
                        if Amenaza == 2:
                            Cat_amenaza = 'Alta'
                        elif Amenaza == 1:
                            Cat_amenaza = 'Media'
                        else:
                            Cat_amenaza = 'Baja'
                        
                        print('\n')  # Se imprime un renglón en blanco
                        print(f'Se hará el análisis para amenaza {Cat_amenaza}') #Se imprime la amenaza en el que va el análisis
                        print('\n')
                        
                        # Se llena el dataframe con los valores hasta ahora determinados
                        DF_Excedencia.loc[id_amenaza, 'Poli_Thiessen'] = poligono
                        DF_Excedencia.loc[id_amenaza, 'Estacion'] = Estacion
                        DF_Excedencia.loc[id_amenaza, 'Amenaza'] = Cat_amenaza
                        DF_Excedencia.loc[id_amenaza, 'Tipo_Mov'] = Tipo
                        
                        # Si no se cuenta con mas de dos MM correspondientes a la categoría de amenaza no se puede completar el análisis
                        if len(DF_Inv_Tipo[DF_Inv_Tipo[Campo_Amenaza] == Amenaza]) < 2:
                            print(f'No hay suficientes datos para completar el análisis de amenaza {Cat_amenaza} y tipo {Tipo}')
                            # Se llena con NaN los datos faltantes
                            DF_Excedencia.loc[id_amenaza, 'Excedencia'] = np.NaN
                            DF_Excedencia.loc[id_amenaza, 'P[R>Rt]'] = np.NaN
                            DF_Excedencia.loc[id_amenaza, 'N'] = np.NaN
                            DF_Excedencia.loc[id_amenaza, 'Fr'] = np.NaN
                            DF_Excedencia.loc[id_amenaza, 'Ptem'] = np.NaN
                            continue
                        
                        # Se pone como indice la columna de categoria de amenaza
                        DF_Inv_Tipo.set_index(Campo_Amenaza, inplace = True)
                        # Se selecciona los MM correspondientes a la categoría de amenaza
                        DF_Inv_Amenaza_Tipo = DF_Inv_Tipo.loc[Amenaza]
                        DF_Inv_Amenaza_Tipo['FECHA_MOV'] = DF_Inv_Amenaza_Tipo['FECHA_MOV'].dt.strftime('%d/%m/%Y')
                        DF_Inv_Amenaza_Tipo.reset_index(level=0, inplace = True)
                        DF_Inv_Tipo.reset_index(level=0, inplace=True)
                        
                        # Se extrae los valores únicos de fechas de reporte de movimientos en masa
                        DF_Fechas_Unicas_MM = pd.DataFrame(columns=['Fecha'],dtype=str)
                        F = DF_Inv_Amenaza_Tipo['FECHA_MOV'].unique()
                        DF_Fechas_Unicas_MM['Fecha'] = F
                        DF_Fechas_Unicas_MM['Fecha'] = pd.to_datetime(DF_Fechas_Unicas_MM.Fecha)
                        DF_Fechas_Unicas_MM['Fecha'] = DF_Fechas_Unicas_MM['Fecha'].dt.strftime('%d/%m/%Y')
                        DF_Fechas_Unicas_MM['Fecha'] = DF_Fechas_Unicas_MM['Fecha'].astype(str)
                            
                        # Se crea un dataframe de apoyo para el manejo de los datos de la regresión
                        DF_DatosLluviaEventos = pd.DataFrame(columns=['Fecha_Analisis', 'Pant', 'P24'], dtype=float)
                        
                        # Se recorren las fechas únicas
                        for h in range (0, len(DF_Fechas_Unicas_MM)):
                            # Se busca y se determina el índice de la fecha en el dataframe de precipitación
                            Dia = DF_Fechas_Unicas_MM.loc[h, 'Fecha']
                            indice = DF_Estacion[DF_Estacion[Fecha_Precip] == Dia].index
                            P24 = DF_Estacion.loc[indice[0], Estacion]
                            
                            if umbral_lluvia == 0:
                                # Si no se decide hacer un ajuste se llena con la precipitación del día y la antecedente correspondiente
                                DF_DatosLluviaEventos.loc[h, 'P24'] = P24
                                DF_DatosLluviaEventos.loc[h, 'Fecha_Analisis'] = DF_Estacion.loc[indice[0], Fecha_Precip]
                                DF_DatosLluviaEventos.loc[h, 'Pant'] = DF_Estacion.loc[indice[0], 'Pant']
                                
                            else:
                                # Si se decide hacer el ajuste se verifica cumple con la lluvia minima
                                if P24 <= umbral_lluvia:
                                    for z in range(0, umbral_dias):
                                        # Si no cumple la P24 se revisan las precipitaciones de los días anteriores dentro del umbral
                                        P24 = DF_Estacion.loc[indice[0] - z, Estacion]
                                        
                                        if P24 > umbral_lluvia:
                                            # Los datos de la P24 del día más cercano que cumpla el umbral serán con los que se llenará el dataframe para el análisis
                                            DF_DatosLluviaEventos.loc[h, 'P24'] = DF_Estacion.loc[indice[0] - z, Estacion]
                                            DF_DatosLluviaEventos.loc[h, 'Pant'] = DF_Estacion.loc[indice[0] - z, 'Pant']
                                            Fecha_Inicial = DF_Estacion.loc[indice[0], Fecha_Precip]
                                            Fecha_Analisis = DF_Estacion.loc[indice[0] - z, Fecha_Precip]
                                            DF_DatosLluviaEventos.loc[h, 'Fecha_Analisis'] = Fecha_Analisis
                                            DF_DatosLluviaEventos.loc[h, 'Fecha_Inventario'] = Fecha_Inicial
                                            #Se reemplaza la fecha en el inentario de movimientos para el posterior análisis
                                            DF_Inv_Amenaza_Tipo['FECHA_MOV'] = DF_Inv_Amenaza_Tipo['FECHA_MOV'].str.replace(Fecha_Inicial, Fecha_Analisis)
                                        
                                        else:
                                            continue 
                                
                                else:
                                    # Si la P24 cumple el umbral se toman sus datos
                                    DF_DatosLluviaEventos.loc[h, 'P24'] = P24
                                    DF_DatosLluviaEventos.loc[h, 'Fecha_Analisis'] = DF_Estacion.loc[indice[0], Fecha_Precip]
                                    DF_DatosLluviaEventos.loc[h, 'Pant'] = DF_Estacion.loc[indice[0], 'Pant']
                        
                        # Se eliminan datos que posiblemente no tuvieran información
                        DF_DatosLluviaEventos = DF_DatosLluviaEventos.dropna(subset=['Pant'])
                        DF_DatosLluviaEventos = DF_DatosLluviaEventos.dropna(subset=['P24'])
                        
                        # Se exporta el dataframe con los valores de precipitación para el análisis de las categorías en cuestión
                        DF_DatosLluviaEventos.reset_index().to_csv(data_path + f'/Amenaza/Lluvia_{poligono}_{Cat_amenaza}_{Tipo}.csv',header=True,index=False)
                        
                        if len(DF_DatosLluviaEventos) < 2:
                            # Si se tiene menos de dos fechas de MM para el análisis no se puede continuar con el análisis
                            print(f'No hay suficientes datos para completar el análisis de amenaza {Cat_amenaza} y tipo {Tipo}')
                            # Se llenan los datos faltante con Nan
                            DF_Excedencia.loc[id_amenaza, 'Excedencia'] = np.NaN
                            DF_Excedencia.loc[id_amenaza, 'P[R>Rt]'] = np.NaN
                            DF_Excedencia.loc[id_amenaza, 'N'] = np.NaN
                            DF_Excedencia.loc[id_amenaza, 'Fr'] = np.NaN
                            DF_Excedencia.loc[id_amenaza, 'Ptem'] = np.NaN
                            continue
                        
                        print(DF_DatosLluviaEventos)
                        print('\n')
                        
                        # Se pasa la columna de las fechas a formato fecha y se ordena el dataframe con base en esta
                        DF_DatosLluviaEventos['Fecha_Analisis'] = pd.to_datetime(DF_DatosLluviaEventos['Fecha_Analisis'], dayfirst=True)
                        DF_DatosLluviaEventos = DF_DatosLluviaEventos.sort_values(by ='Fecha_Analisis')
                        DF_DatosLluviaEventos.reset_index(level = 0, inplace = True)
                        DF_DatosLluviaEventos.drop(['index'],axis = 'columns', inplace = True)
                        
                        # Se determina la fecha inicial con la que se cuenta con datos
                        inicio = DF_DatosLluviaEventos.loc[0]['Fecha_Analisis']
                        inicio1 = str(inicio.strftime("%d/%m/%Y"))
                        print(f'La fecha inicial es {inicio1}')
                        
                        # Se determina la fecha final en la que se cuenta con datos
                        fin = DF_DatosLluviaEventos.loc[len(DF_DatosLluviaEventos)-1]['Fecha_Analisis']
                        fin1 = str(fin.strftime("%d/%m/%Y"))
                        print(f'La fecha final es {fin1}')
                        
                        # Se cálcula el número de daños en el que se tienen datos
                        años = (fin.year-inicio.year)
                        print(f'El número de años en el que se tienen los datos es {años}')
                        
                        # Se inicia el proceso de graficar el data frame DF_DatosLluviaEventos
                        
                        # Se extraen los datos de las coordenada X en un data frame individual
                        x = DF_DatosLluviaEventos['Pant']
                        x = x.tolist() 
                        
                        # Se extraen los datos de las coordenada Y en un data frame individual
                        y = DF_DatosLluviaEventos['P24']
                        y= y.tolist()
                        
                        #Se resuleve el modelo líneal por medio de vectores y matrices
                        numdat = len(y)
                        
                        # Se crea la matriz de resultados
                        G = np.ones((numdat, 2))
                        G[:,0] = x
                        #print('G=\n', G)
                        
                        # Se obtienen los parametros de la recta según la norma L2
                        ml2 = np.linalg.inv(G.T@G)@G.T@y
                        
                        dmod = G@ml2
                        rl2 = y - dmod
                        error = 1.1
                        gml0 = dmod
                        
                        # Se buscan los resultados L1 por medio del error
                        while error>0.1:
                            R = np.diag(1/np.abs(rl2))
                            ml1 = np.linalg.inv(G.T@R@G)@G.T@R@y
                            dl1 = G@ml1
                            error = np.abs((dl1[0]-gml0[0])/(1+dl1[0]))
                            gml0 = dl1
                        
                        dl2 = G@ml2
                        dl1 = G@ml1
                        
                        # Si hay tan solo dos puntos no converge debído a que el error es 0 
                        # entonces la pendiente y el corte con Y es igual que con la norma L2
                        if len(y) == 2:
                            ml1 = ml2
                            
                        # Grafica de la dispersión de los datos y sus rectas correspondientes
                        fig, ax = plt.subplots(1, 1, figsize=(12, 7))
                        ax.plot(x, y, 'o')
                        
                        # Se agregan las línea con su respectiva ecuación de recta
                        ax.plot(x, dl1, 'g--', label = f'L1: PT = {round(ml1[0],2)} * Pant + {round(ml1[1],2)}') 
                        ax.plot(x, dl2, 'r--', label = f'L2: PT = {round(ml2[0],2)} * Pant + {round(ml2[1],2)}')   
                        
                        # Se define los nombres de los ejes coordenados y el título
                        ax.set_xlabel("P_antecedente [mm]")
                        ax.set_ylabel("P24h [mm]")
                        ax.set_title(f'Lluvia del dia vs Lluvia acumulada - {poligono}: tipo {Tipo}, amenaza {Cat_amenaza}',
                                     pad = 15, fontdict = {'fontsize': 14, 'color': '#4873ab'})
                        
                        # Se activa la leyenda y la grilla, se muestra la gráfica
                        ax.legend()
                        plt.grid(True)
                        plt.show()
                            
                        #Dependiendo de la norma de regresión elegida se define los parámetros de la recta
                        if Norma == "L1":
                            Pendiente = ml1[0]
                            print (u'Pendiente "m": ', Pendiente)
                            Intercepto = ml1[1]
                            print (u'Intercepto "b": ', Intercepto)
                            
                        else:
                            Pendiente = ml2[0]
                            print (u'Pendiente "m": ', Pendiente)
                            Intercepto = ml2[1]
                            print (u'Intercepto "b": ', Intercepto)
                        
                        
                        #Se guarda la gráfica resultante en formato jpg
                        fig.savefig(data_path + f'/Amenaza/{poligono}_{Tipo}_{Cat_amenaza}.jpg')
                        
                        #Se sobreescriben los datos de la gráfica en otro dataframe
                        DF_Estacion_Analisis = pd.DataFrame()
                        DF_Estacion_Analisis['date'] = DF_Estacion[Fecha_Precip]
                        DF_Estacion_Analisis['P24'] = DF_Estacion['P24']
                        DF_Estacion_Analisis['Pant'] = DF_Estacion['Pant']
                        
                        # Calculo y creacion de un dataframe con la precipitación umbral para cada dia del registro histórico
                        #PT= precipitacion umbral
                        #PT = m * (Pant) + b
                        PT =  DF_Estacion_Analisis['Pant'] * Pendiente + Intercepto
                        DF_Estacion_Analisis['PT'] = PT
                        
                        # Calculo del número de excedencias del umbral de lluvia en todo el registro de precipitación     
                        DF_Estacion_Analisis["EX"] = 0
                        Valor = 1
                        DF_Estacion_Analisis.loc[DF_Estacion_Analisis['P24'] > DF_Estacion_Analisis['PT'], ["EX"]] = Valor
                         
                        # Se seleccionan solo las fechas entre el rango de análisis
                        DF_Estacion_Analisis.set_index('date', inplace=True)
                        DF_Estacion_Analisis = DF_Estacion_Analisis.loc[inicio1 : fin1]
                        DF_Estacion_Analisis.reset_index(level = 0, inplace=True)
                        
                        # Se suman el número de excedencias
                        Ex = DF_Estacion_Analisis["EX"].sum()
                        DF_Excedencia.loc[id_amenaza,'Excedencia'] = Ex
                        print (f'El umbral de lluvia es excedido {Ex} veces en todo el registro de precipitación para amenaza {Cat_amenaza} y tipo {Tipo}')
                        
                        # Se aplica la probabilidad de Poisson
                        I = años/Ex
                        t = 1
                        P = 1 - math.exp(-t/I)
                        print(f'La probabilidad P[R>Rt] = {P} ')
                        DF_Excedencia.loc[id_amenaza, 'P[R>Rt]'] = P
                        
                        # Si hay menos de dos datos que excedan la precipitación no se puede continuar con el anális
                        if len(DF_Estacion_Analisis[DF_Estacion_Analisis['EX'] == Valor]) < 2:
                            continue
                        
                        # Se pone como indice la columna de excedencias 
                        DF_Estacion_Analisis.set_index('EX', inplace=True)
                        # Se seleccionan los días en los que se excedió el umbral
                        DF_Estacion_Analisis = DF_Estacion_Analisis.loc[Valor]
                        DF_Estacion_Analisis.reset_index(level=0, inplace=True)
                        
                        # El campo de fecha se pasa a formato de fecha y luego a string
                        DF_Estacion_Analisis['date'] = pd.to_datetime(DF_Estacion_Analisis['date'], dayfirst=True)
                        DF_Estacion_Analisis['date'] = DF_Estacion_Analisis['date'].dt.strftime("%d/%m/%Y")  
                        
                        # El campo de fecha se pasa a formato de fecha y luego a string en el inventario de MM
                        DF_Inv_Amenaza_Tipo['FECHA_MOV'] = pd.to_datetime(DF_Inv_Amenaza_Tipo['FECHA_MOV'], dayfirst=True)
                        DF_Inv_Amenaza_Tipo['FECHA_MOV'] = DF_Inv_Amenaza_Tipo['FECHA_MOV'].dt.strftime("%d/%m/%Y")  
                        
                        # Se crea un dataframe de apoyo
                        DF_Apoyo = pd.DataFrame(columns = ['date', 'N'])
                        
                        # Se recorren las fechas de excedencia
                        for n in range (0,len(DF_Estacion_Analisis)):
                            # Se define la fecha
                            date = DF_Estacion_Analisis.loc[n, 'date']
                            # Si no hay movimientos en masa en la fecha se continua
                            if len(DF_Inv_Amenaza_Tipo[DF_Inv_Amenaza_Tipo['FECHA_MOV'] == date]) < 1:
                                continue
                            DF_Apoyo.loc[n, 'date'] = date
                            # Se cuentan los números de MM que correspondan a la fecha de excedencia
                            DF_Apoyo.loc[n, 'N'] = len(DF_Inv_Amenaza_Tipo[DF_Inv_Amenaza_Tipo['FECHA_MOV'] == date])
                            
                        # Se suman los MM en las fechas de excedencia
                        N = DF_Apoyo['N'].sum()
                        # Se otiene la frecuencia
                        Fr = N/Ex
                        DF_Excedencia.loc[id_amenaza, 'N'] = N
                        DF_Excedencia.loc[id_amenaza, 'Fr'] = Fr
                        # Se obtiene la probabilidad temporal con el producto de la probabilidad de Poisson con la frecuencia
                        DF_Excedencia.loc[id_amenaza, 'Ptem'] = P*Fr
                    
                    # Se hace append a medida que se completa el análisis
                    DF_Final = DF_Final.append(DF_Excedencia)

            # Se ordena el dataframe con base en el id de los poligonos de Voronoi
            DF_Final = DF_Final.sort_values(by = 'Poli_Thiessen')
            DF_Final.reset_index(level=0, inplace=True)
            DF_Final = DF_Final.drop(['index'], axis=1)
            print('\n')
            print(DF_Final)
            # Se exporta el dataframe como archivo csv
            DF_Final.reset_index().to_csv(data_path + '/Resultados/DF_Excedencia.csv',header=True,index=False)

            # ############################# ESPACIALIZACIÓN DE LOS RESULTADOS ############################# #

            # Se lee los poligonos en los que se llenará la probabilidad
            Amenaza_Lluvia = QgsVectorLayer(data_path + '/Amenaza/Amenaza_Lluvia.shp')

            # Si la discreticación es por Amenaza y tipo de movimiento
            if Discritizacion == "Amenaza - Tipo de movimiento":
                # Se inicia a editar la capa
                caps = Amenaza_Lluvia.dataProvider().capabilities()
                # Se añade un campo nuevo llamado "Raster"
                # se asignará el valor único de cada caracteristica
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("D_Baja", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("D_Media", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("D_Alta", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("C_Baja", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("C_Media", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("C_Alta", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("F_Baja", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("F_Media", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("F_Alta", QVariant.Double)])
                # Se guarda la edición
                Amenaza_Lluvia.updateFields()
                   
                # Se determina el índice de las columnas que fueron agregadas
                D_Baja = Amenaza_Lluvia.fields().indexFromName("D_Baja")
                D_Media = Amenaza_Lluvia.fields().indexFromName("D_Media")
                D_Alta = Amenaza_Lluvia.fields().indexFromName("D_Alta")
                C_Baja = Amenaza_Lluvia.fields().indexFromName("C_Baja")
                C_Media = Amenaza_Lluvia.fields().indexFromName("C_Media")
                C_Alta = Amenaza_Lluvia.fields().indexFromName("C_Alta")
                F_Baja = Amenaza_Lluvia.fields().indexFromName("F_Baja")
                F_Media = Amenaza_Lluvia.fields().indexFromName("F_Media")
                F_Alta = Amenaza_Lluvia.fields().indexFromName("F_Alta")

                # Se obtienen los valores únicos de las caracteristicas
                atributos = DF_Final['Poli_Thiessen'].unique()
                   
                # Se inicia a editar
                caps = Amenaza_Lluvia.dataProvider().capabilities()
                
                # Se recorren los poligonos
                for i in range(0, len(atributos)):
                    # Se define el atributo de análisis (id del poligono)
                    Atri = int(atributos[i])
                    
                    # Se extrae la probabilidad del poligono para deslizamientos con categoría de amenaza baja
                    Indice_D_0 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
                    if len(Indice_D_0) != 0: 
                        Ptem_D_0 = float(DF_Final.loc[Indice_D_0[0], 'Ptem'])
                    else:
                        Ptem_D_0 = np.nan
                    
                    # Se extrae la probabilidad del poligono para deslizamientos con categoría de amenaza media   
                    Indice_D_1 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
                    if len(Indice_D_1) != 0: 
                        Ptem_D_1 = float(DF_Final.loc[Indice_D_1[0], 'Ptem'])
                    else:
                        Ptem_D_1 = np.nan
                    
                    # Se extrae la probabilidad del poligono para deslizamientos con categoría de amenaza alta
                    Indice_D_2 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
                    if len(Indice_D_2) != 0: 
                        Ptem_D_2 = float(DF_Final.loc[Indice_D_2[0], 'Ptem'])
                    else:
                        Ptem_D_2 = np.nan
                    
                    # Se extrae la probabilidad del poligono para caida con categoría de amenaza baja
                    Indice_C_0 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Caida')].index
                    if len(Indice_C_0) != 0: 
                        Ptem_C_0 = float(DF_Final.loc[Indice_C_0[0], 'Ptem'])
                    else:
                        Ptem_C_0 = np.nan
                    
                    # Se extrae la probabilidad del poligono para caida con categoría de amenaza media
                    Indice_C_1 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Caida')].index
                    if len(Indice_C_1) != 0: 
                        Ptem_C_1 = float(DF_Final.loc[Indice_C_1[0], 'Ptem'])
                    else:
                        Ptem_C_1 = np.nan
                    
                    # Se extrae la probabilidad del poligono para caida con categoría de amenaza alta
                    Indice_C_2 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Caida')].index
                    if len(Indice_C_2) != 0: 
                        Ptem_C_2 = float(DF_Final.loc[Indice_C_2[0], 'Ptem'])
                    else:
                        Ptem_C_2 = np.nan
                    
                    # Se extrae la probabilidad del poligono para flujo con categoría de amenaza baja
                    Indice_F_0 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Flujo')].index
                    if len(Indice_F_0) != 0: 
                        Ptem_F_0 = float(DF_Final.loc[Indice_F_0[0], 'Ptem'])
                    else:
                        Ptem_F_0 = np.nan
                    
                    # Se extrae la probabilidad del poligono para flujo con categoría de amenaza media
                    Indice_F_1 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Flujo')].index
                    if len(Indice_F_1) != 0: 
                        Ptem_F_1 = float(DF_Final.loc[Indice_F_1[0], 'Ptem'])
                    else:
                        Ptem_F_1 = np.nan
                   
                    # Se extrae la probabilidad del poligono para flujo con categoría de amenaza alta
                    Indice_F_2 = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Flujo')].index
                    if len(Indice_F_2) != 0: 
                        Ptem_F_2 = float(DF_Final.loc[Indice_F_2[0], 'Ptem'])
                    else:
                        Ptem_F_2 = np.nan

                    # Se hace la selección en la capa del poligono en cuestión
                    Amenaza_Lluvia.selectByExpression(
                        f'"Raster"=\'{Atri}\'', QgsVectorLayer.SetSelection)
                        
                    # Se define la selección
                    selected_fid = []
                    selection = Amenaza_Lluvia.selectedFeatures()
                        
                    for feature in selection:  # Se recorren las filas seleccionadas
                        fid = feature.id()  # Se obtiene el id de la fila seleccionada
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            # La columnas se llenan con las probabilidades correspondientes
                            attrs = { D_Baja : Ptem_D_0, D_Media : Ptem_D_1, D_Alta : Ptem_D_2,
                                     C_Baja : Ptem_C_0, C_Media : Ptem_C_1, C_Alta : Ptem_C_2,
                                     F_Baja : Ptem_F_0, F_Media : Ptem_F_1, F_Alta : Ptem_F_2 }
                            # Se hace el cambio de los atributos
                            Amenaza_Lluvia.dataProvider().changeAttributeValues({fid: attrs})

            else:
                # Se inicia a editar la capa
                caps = Amenaza_Lluvia.dataProvider().capabilities()
                # Se añade un campo nuevo para llenar las probabilidades
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("Baja", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("Media", QVariant.Double)])
                Amenaza_Lluvia.dataProvider().addAttributes([QgsField("Alta", QVariant.Double)])

                # Se guarda la edición
                Amenaza_Lluvia.updateFields()
                   
                # Se determina el índice de la columna que fue agregada
                Baja = Amenaza_Lluvia.fields().indexFromName("Baja")
                Media = Amenaza_Lluvia.fields().indexFromName("Media")
                Alta = Amenaza_Lluvia.fields().indexFromName("Alta")

                # Se obtienen los valores únicos de las caracteristicas
                atributos = DF_Final['Poli_Thiessen'].unique()
                   
                # Se inicia a editar
                caps = Amenaza_Lluvia.dataProvider().capabilities()
                    
                for i in range(0, len(atributos)):
                    Atri = int(atributos[i])
                    
                    # Se extrae la probabilidad del poligono para la categoría de amenaza baja
                    Indice_Baja = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Baja')].index
                    if len(Indice_Baja) != 0: 
                        Ptem_Baja = float(DF_Final.loc[Indice_Baja[0], 'Ptem'])
                    else:
                        Ptem_Baja = np.nan
                      
                    # Se extrae la probabilidad del poligono para la categoría de amenaza media
                    Indice_Media = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Media')].index
                    if len(Indice_Media) != 0: 
                        Ptem_Media = float(DF_Final.loc[Indice_Media[0], 'Ptem'])
                    else:
                        Ptem_Media = np.nan
                        
                    # Se extrae la probabilidad del poligono para la categoría de amenaza alta
                    Indice_Alta = DF_Final[(DF_Final.Poli_Thiessen == Atri) & (DF_Final.Amenaza == 'Alta')].index
                    if len(Indice_Alta) != 0: 
                        Ptem_Alta = float(DF_Final.loc[Indice_Alta[0], 'Ptem'])
                    else:
                        Ptem_Alta = np.nan

                    # Se hace la selección en la capa de la caracteristica en cuestión
                    Amenaza_Lluvia.selectByExpression(
                        f'"Raster"=\'{Atri}\'', QgsVectorLayer.SetSelection)
                        
                    # Se define la selección
                    selected_fid = []
                    selection = Amenaza_Lluvia.selectedFeatures()
                        
                    for feature in selection:  # Se recorren las filas seleccionadas
                        fid = feature.id()  # Se obtiene el id de la fila seleccionada
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            # Las columnas nuevas se llenan con la probabilidad correspondiente
                            attrs = { Baja : Ptem_Baja, Media : Ptem_Media, Alta : Ptem_Alta }
                            # Se hace el cambio de los atributos
                            Amenaza_Lluvia.dataProvider().changeAttributeValues({fid: attrs})

            # Se añade la capa al lienzo
            Amenaza_Lluvia = QgsVectorLayer(data_path + '/Amenaza/Amenaza_Lluvia.shp', 'Amenaza_Lluvia')
            QgsProject.instance().addMapLayer(Amenaza_Lluvia)
            
        """
        07_Amenaza_Sismo
        """
        
        if len(DF_Mov_Masa_Sismos) != 0:
        
            # Se lee el inventario de movimientos en masa con fecha y susceptibilidad
            DF_Inv = pd.read_csv(data_path + '/Amenaza/DF_Mov_Masa_Sismos.csv')
            DF_Inv = DF_Inv.drop(['level_0'], axis=1) #Borrar
            DF_Inv = DF_Inv.dropna(axis=0, subset=['FECHA_MOV'])
            DF_Inv.reset_index(level=0, inplace=True)
            DF_Inv['FECHA_MOV'] = DF_Inv['FECHA_MOV'].astype(str) #Identifico el nombre de la columna que contiene las fechas

            # ############################# CALCULO DE PROBABILIDAD ############################# #

            #Se crea el dataframe con el que se hace el análisis
            DF_Probabilidad = pd.DataFrame(columns=['Cluster', 'Tipo_Mov', 'Amenaza', 'P[R>Rt]'])
            DF_Final = pd.DataFrame()

            #Se determinan el número de grupos de MM
            Cluster = DF_Inv['CLUSTER_ID'].unique()
            Cluster = pd.DataFrame(Cluster, columns=['Cluster'],dtype=object)

            # Se recorre los valores de grupos de cluster
            for grupo in range (0, len(Cluster)):
                Cluster_id = Cluster.loc[grupo,'Cluster']
                
                # Si la cantidad de datos de ese grupo es menor a dos no se puede hacer el análisis
                if len(DF_Inv[DF_Inv['CLUSTER_ID'] == Cluster_id]) < 2:
                    print(f'No hay suficientes datos para completar el análisis del cluster {Cluster_id}')
                    print('\n')
                    continue
                
                print(f'Se hará el análisis para el cluster {Cluster_id}')
                print('\n')
                
                # Se pone como indice la columna del cluster
                DF_Inv.set_index('CLUSTER_ID', inplace=True)
                DF_Inv_Cluster = DF_Inv.loc[Cluster_id] # Se extraen los MM correspondientes a ese cluster
                DF_Inv_Cluster.reset_index(level=0, inplace=True)
                DF_Inv.reset_index(level=0, inplace=True)

                #Se extraen los tipos de movimientos en masa
                Tipo_Evento = DF_Inv_Cluster['TIPO_MOV1'].unique()
                Tipo_Evento = pd.DataFrame(Tipo_Evento, columns=['Tipo_Mov'],dtype=object)
                
                # Si la descretización es solo por amenaza la extensión del for solo será de 1
                if Discritizacion == "Amenaza": Tipo_Evento = [1]

                #Se hace el estudio según el tipo de evento
                for id_evento in range (0, len(Tipo_Evento)):
                    
                    # Si la descretización es por tipo de movimiento y amenaza
                    if Discritizacion == "Amenaza - Tipo de movimiento":
                        Tipo = Tipo_Evento.loc[id_evento, 'Tipo_Mov']
                        
                        # Si los MM correspondientes a este tipo de movimiento son menores a dos no se puede continuar con el análisis
                        if len(DF_Inv_Cluster[DF_Inv_Cluster['TIPO_MOV1'] == Tipo]) < 2:
                            print(f'No hay suficientes datos para completar el análisis del tipo {Tipo}')
                            print('\n')
                            continue
                        
                        print(f'Se hará el análisis para el tipo {Tipo}')
                        print('\n')
                        
                        # Se pone como indice la columna de tipo de movimiento
                        DF_Inv_Cluster.set_index('TIPO_MOV1', inplace=True)
                        # Se selecciona del inventario resultante anteriormente solo los del tipo en cuestión
                        DF_Inv_Tipo = DF_Inv_Cluster.loc[Tipo]
                        DF_Inv_Tipo.reset_index(level=0, inplace=True)
                        DF_Inv_Cluster.reset_index(level=0, inplace=True)
                        
                        # Según el tipo de movimiento en masa se define la categoría de susceptibilidad para el análisis
                        if Tipo == "Deslizamiento":
                            Campo_Amenaza = "Susc_Desli"
                        elif Tipo == "Caida":
                            Campo_Amenaza = "Susc_Caida"
                        elif Tipo == "Flujo":
                            Campo_Amenaza = "Susc_Flujo"
                        else:
                            print("No se reconoce el tipo de movimiento en masa")
                            print('\n')
                            continue
                    else:
                        # Si no se hará discretización por tipo de movimiento en masa
                        # se copia el inventario anteriormente exportado solo por poligonos
                        DF_Inv_Tipo = DF_Inv_Cluster.copy(deep = True)
                        Campo_Amenaza = "Susc_Desli"
                        Tipo = "Todos"
                        
                    # Si el campo determinado para la discretización de la amenaza no está en el inventario se continua
                    if (Campo_Amenaza in DF_Inv_Tipo.columns) is False:
                        continue
                    
                    # Se definen los valores únicos de amenaza que se tengan
                    Categorias_Amenaza = DF_Inv_Tipo[Campo_Amenaza].unique()
                    Categorias_Amenaza = pd.DataFrame(Categorias_Amenaza,columns = ['Amenaza'], dtype=object)
                        
                    #Se hace el estudio según la categoría de amenaza
                    for id_amenaza in range (0, len(Categorias_Amenaza)): 
                        Amenaza = Categorias_Amenaza.loc[id_amenaza, 'Amenaza']
                        
                        # Según el id de la amenaza se puede determinar la categoria
                        if Amenaza == 2:
                            Cat_amenaza = 'Alta'
                        elif Amenaza == 1:
                            Cat_amenaza = 'Media'
                        else:
                            Cat_amenaza = 'Baja'
                        
                        # Si no se cuenta con mas de dos MM correspondientes a la categoría de amenaza no se puede completar el análisis
                        if len(DF_Inv_Tipo[DF_Inv_Tipo[Campo_Amenaza] == Amenaza]) < 2:
                            print(f'No hay suficientes datos para completar el análisis de amenaza {Cat_amenaza} y tipo {Tipo}')
                            print('\n')
                            continue
                        
                        print(f'Se hará el análisis para amenaza {Cat_amenaza}') #Se imprime la amenaza en el que va el análisis
                        print('\n') # Se imprime un renglón en blanco
                        
                        DF_Probabilidad.loc[id_amenaza, 'Cluster'] = Cluster_id
                        DF_Probabilidad.loc[id_amenaza, 'Amenaza'] = Cat_amenaza
                        DF_Probabilidad.loc[id_amenaza, 'Tipo_Mov'] = Tipo

                        # Se pone como indice la columna de categoria de amenaza
                        DF_Inv_Tipo.set_index(Campo_Amenaza, inplace = True)
                        # Se selecciona los MM correspondientes a la categoría de amenaza
                        DF_Inv_Amenaza_Tipo = DF_Inv_Tipo.loc[Amenaza]
                        DF_Inv_Amenaza_Tipo.reset_index(level=0, inplace = True)
                        DF_Inv_Tipo.reset_index(level=0, inplace=True)
                            
                        # Se extrae los valores únicos de fechas de reporte de movimientos en masa
                        DF_Fechas_Unicas_MM = pd.DataFrame(columns=['Fecha'], dtype=str)
                        F = DF_Inv_Amenaza_Tipo['FECHA_MOV'].unique()
                        DF_Fechas_Unicas_MM['Fecha'] = F
                        DF_Fechas_Unicas_MM['Fecha'] = pd.to_datetime(DF_Fechas_Unicas_MM.Fecha, dayfirst=True)
                        DF_Fechas_Unicas_MM = DF_Fechas_Unicas_MM.sort_values(by = 'Fecha')
                        DF_Fechas_Unicas_MM.reset_index(level = 0, inplace = True)
                        DF_Fechas_Unicas_MM.drop(['index'], axis = 'columns', inplace = True)
                        
                        # Se determina la fecha inicial con la que se cuenta con datos
                        inicio = DF_Fechas_Unicas_MM.loc[0]['Fecha']
                        inicio1 = str(inicio.strftime("%d/%m/%Y"))
                        print(f'La fecha inicial es {inicio1}')
                        # Se determina la fecha final en la que se cuenta con datos
                        fin = DF_Fechas_Unicas_MM.loc[len(DF_Fechas_Unicas_MM) - 1]['Fecha']
                        fin1 = str(fin.strftime("%d/%m/%Y"))
                        print(f'La fecha final es {fin1}')
                         
                        # Se cálcula el número de daños en el que se tienen datos
                        años = (fin.year - inicio.year)
                        if años == 0:
                            años = 1
                        n = len(DF_Inv_Amenaza_Tipo)
                        print(f'En {años} años, hubo {n} movimientos en masa tipo {Tipo} con categoria {Cat_amenaza}')
                        
                        # Se aplica la probabilidad de Poisson
                        I = años/n
                        t = 1
                        P = 1 - math.exp(-t/I)
                        print(f'La probabilidad P[R>Rt] = {P} ')
                        print('\n')
                        DF_Probabilidad.loc[id_amenaza, 'P[R>Rt]'] = P
                    
                    # Se hace append a medida que se completa el análisis
                    DF_Final = DF_Final.append(DF_Probabilidad)

            # Se ordena el dataframe con base en el id de los Cluster
            DF_Final = DF_Final.sort_values(by = 'Cluster')
            DF_Final.reset_index(level = 0, inplace = True)
            DF_Final = DF_Final.drop(['index'], axis = 1)
            print(DF_Final)
            print('\n')

            # Se exporta el dataframe como archivo csv
            DF_Final.reset_index().to_csv(data_path + '/Resultados/DF_Amenaza_Sismo.csv', header = True, index = False)

            # ############################# ESPACIALIZACIÓN DE LOS RESULTADOS ############################# #

            # Se lee los poligonos en los que se llenará la probabilidad
            Amenaza_Sismo = QgsVectorLayer(data_path + '/Amenaza/Amenaza_Sismos.shp')

            # Si la discreticación es por Amenaza y tipo de movimiento
            if Discritizacion == "Amenaza - Tipo de movimiento":
                # Se inicia a editar la capa
                caps = Amenaza_Sismo.dataProvider().capabilities()
                # Se añade un campo nuevo para llenar las probabilidades
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("D_Baja", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("D_Media", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("D_Alta", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("C_Baja", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("C_Media", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("C_Alta", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("F_Baja", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("F_Media", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("F_Alta", QVariant.Double)])
                # Se guarda la edición
                Amenaza_Sismo.updateFields()
                   
                # Se determina el índice de la columna que fue agregada
                D_Baja = Amenaza_Sismo.fields().indexFromName("D_Baja")
                D_Media = Amenaza_Sismo.fields().indexFromName("D_Media")
                D_Alta = Amenaza_Sismo.fields().indexFromName("D_Alta")
                C_Baja = Amenaza_Sismo.fields().indexFromName("C_Baja")
                C_Media = Amenaza_Sismo.fields().indexFromName("C_Media")
                C_Alta = Amenaza_Sismo.fields().indexFromName("C_Alta")
                F_Baja = Amenaza_Sismo.fields().indexFromName("F_Baja")
                F_Media = Amenaza_Sismo.fields().indexFromName("F_Media")
                F_Alta = Amenaza_Sismo.fields().indexFromName("F_Alta")

                # Se obtienen los valores únicos de las caracteristicas
                atributos = DF_Final['Cluster'].unique()
                   
                # Se inicia a editar
                caps = Amenaza_Sismo.dataProvider().capabilities()
                 
                # Se recorren los poligonos
                for i in range(0, len(atributos)):
                    # Se define el atributo de análisis (id del poligono - cluster)
                    Atri = int(atributos[i])
                    
                    # Se extrae la probabilidad del poligono para deslizamientos con categoría de amenaza baja
                    Indice_D_0 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
                    if len(Indice_D_0) != 0: 
                        Ptem_D_0 = float(DF_Final.loc[Indice_D_0[0], 'P[R>Rt]'])
                    else:
                        Ptem_D_0 = np.nan
                     
                    # Se extrae la probabilidad del poligono para deslizamientos con categoría de amenaza media 
                    Indice_D_1 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
                    if len(Indice_D_1) != 0: 
                        Ptem_D_1 = float(DF_Final.loc[Indice_D_1[0], 'P[R>Rt]'])
                    else:
                        Ptem_D_1 = np.nan
                     
                    # Se extrae la probabilidad del poligono para deslizamientos con categoría de amenaza alta
                    Indice_D_2 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
                    if len(Indice_D_2) != 0: 
                        Ptem_D_2 = float(DF_Final.loc[Indice_D_2[0], 'P[R>Rt]'])
                    else:
                        Ptem_D_2 = np.nan
                    
                    # Se extrae la probabilidad del poligono para caida con categoría de amenaza baja
                    Indice_C_0 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Caida')].index
                    if len(Indice_C_0) != 0: 
                        Ptem_C_0 = float(DF_Final.loc[Indice_C_0[0], 'P[R>Rt]'])
                    else:
                        Ptem_C_0 = np.nan
                    
                    # Se extrae la probabilidad del poligono para caida con categoría de amenaza media
                    Indice_C_1 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Caida')].index
                    if len(Indice_C_1) != 0: 
                        Ptem_C_1 = float(DF_Final.loc[Indice_C_1[0], 'P[R>Rt]'])
                    else:
                        Ptem_C_1 = np.nan
                    
                    # Se extrae la probabilidad del poligono para caida con categoría de amenaza alta
                    Indice_C_2 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Caida')].index
                    if len(Indice_C_2) != 0: 
                        Ptem_C_2 = float(DF_Final.loc[Indice_C_2[0], 'P[R>Rt]'])
                    else:
                        Ptem_C_2 = np.nan
                    
                    # Se extrae la probabilidad del poligono para flujo con categoría de amenaza baja
                    Indice_F_0 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Flujo')].index
                    if len(Indice_F_0) != 0: 
                        Ptem_F_0 = float(DF_Final.loc[Indice_F_0[0], 'P[R>Rt]'])
                    else:
                        Ptem_F_0 = np.nan
                      
                    # Se extrae la probabilidad del poligono para flujo con categoría de amenaza media
                    Indice_F_1 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Flujo')].index
                    if len(Indice_F_1) != 0: 
                        Ptem_F_1 = float(DF_Final.loc[Indice_F_1[0], 'P[R>Rt]'])
                    else:
                        Ptem_F_1 = np.nan
                     
                    # Se extrae la probabilidad del poligono para flujo con categoría de amenaza alta
                    Indice_F_2 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Flujo')].index
                    if len(Indice_F_2) != 0: 
                        Ptem_F_2 = float(DF_Final.loc[Indice_F_2[0], 'P[R>Rt]'])
                    else:
                        Ptem_F_2 = np.nan

                    # Se hace la selección en la capa de la caracteristica en cuestión
                    Amenaza_Sismo.selectByExpression(
                        f'"CLUSTER_ID"=\'{Atri}\'', QgsVectorLayer.SetSelection)
                        
                    # Se define la selección
                    selected_fid = []
                    selection = Amenaza_Sismo.selectedFeatures()
                        
                    for feature in selection:  # Se recorren las filas seleccionadas
                        fid = feature.id()  # Se obtiene el id de la fila seleccionada
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            # La columnas se llenan con las probabilidades correspondientes
                            attrs = { D_Baja : Ptem_D_0, D_Media : Ptem_D_1, D_Alta : Ptem_D_2,
                                     C_Baja : Ptem_C_0, C_Media : Ptem_C_1, C_Alta : Ptem_C_2,
                                     F_Baja : Ptem_F_0, F_Media : Ptem_F_1, F_Alta : Ptem_F_2 }
                            # Se hace el cambio de los atributos
                            Amenaza_Sismo.dataProvider().changeAttributeValues({fid: attrs})

            else:
                # Se inicia a editar la capa
                caps = Amenaza_Sismo.dataProvider().capabilities()
                # Se añade un campo nuevo para llenar las probabilidades
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("Baja", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("Media", QVariant.Double)])
                Amenaza_Sismo.dataProvider().addAttributes([QgsField("Alta", QVariant.Double)])

                # Se guarda la edición
                Amenaza_Sismo.updateFields()
                   
                # Se determina el índice de la columna que fue agregada
                Baja = Amenaza_Sismo.fields().indexFromName("Baja")
                Media = Amenaza_Sismo.fields().indexFromName("Media")
                Alta = Amenaza_Sismo.fields().indexFromName("Alta")

                # Se obtienen los valores únicos de las caracteristicas
                atributos = DF_Final['Cluster'].unique()
                   
                # Se inicia a editar
                caps = Amenaza_Sismo.dataProvider().capabilities()
                    
                for i in range(0, len(atributos)):
                    Atri = int(atributos[i])
                    
                    # Se extrae la probabilidad del poligono para la categoría de amenaza baja
                    Indice_Baja = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Baja')].index
                    if len(Indice_Baja) != 0: 
                        Ptem_Baja = float(DF_Final.loc[Indice_Baja[0], 'P[R>Rt]'])
                    else:
                        Ptem_Baja = np.nan
                        
                    # Se extrae la probabilidad del poligono para la categoría de amenaza media
                    Indice_Media = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Media')].index
                    if len(Indice_Media) != 0: 
                        Ptem_Media = float(DF_Final.loc[Indice_Media[0], 'P[R>Rt]'])
                    else:
                        Ptem_Media = np.nan
                        
                    # Se extrae la probabilidad del poligono para la categoría de amenaza alta
                    Indice_Alta = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Alta')].index
                    if len(Indice_Alta) != 0: 
                        Ptem_Alta = float(DF_Final.loc[Indice_Alta[0], 'P[R>Rt]'])
                    else:
                        Ptem_Alta = np.nan

                    # Se hace la selección en la capa de la caracteristica en cuestión
                    Amenaza_Sismo.selectByExpression(
                        f'"CLUSTER_ID"=\'{Atri}\'', QgsVectorLayer.SetSelection)
                        
                    # Se reemplazan los id del atributo seleccionada
                    selected_fid = []
                    selection = Amenaza_Sismo.selectedFeatures()
                        
                    for feature in selection:  # Se recorren las filas seleccionadas
                        fid = feature.id()  # Se obtiene el id de la fila seleccionada
                        if caps & QgsVectorDataProvider.ChangeAttributeValues:
                            # Las columnas nuevas se llenan con la probabilidad correspondiente
                            attrs = { Baja : Ptem_Baja, Media : Ptem_Media, Alta : Ptem_Alta }
                            # Se hace el cambio de los atributos
                            Amenaza_Sismo.dataProvider().changeAttributeValues({fid: attrs})

            # Se añade la capa al lienzo
            Amenaza_Sismo = QgsVectorLayer(data_path + '/Amenaza/Amenaza_Sismos.shp', 'Amenaza_Sismo')
            QgsProject.instance().addMapLayer(Amenaza_Sismo)
         
        # Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
        elapsed_time = time() - start_time
        QMessageBox.information(self, "Finalizó de análisis de Amenaza", "Elapsed time: %0.10f seconds." % elapsed_time)