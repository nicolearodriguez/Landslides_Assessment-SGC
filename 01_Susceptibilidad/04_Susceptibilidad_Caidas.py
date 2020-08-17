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

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
if ok == False:
    raise Exception('Cancelar')
data_path = data_path.replace("\\", "/")

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

# #######################Zonificación de Susceptibilidad por zonas de inicio tipo Caida####################### #

#Se reclasifica teniendo en cuenta que 0 serán las pendientes menores a 45, y serán 1 las pendientes mayores a 45.
alg="native:reclassifybytable"
Pendientes = data_path + '/Pre_Proceso/Pendiente.tif'
Susceptibilidad_Pendiente = data_path+'/Pre_Proceso/Pendientes_Suscep.tif'
table = [0, 45, 0, 45, 100, 5]  # [min1, max1, valor1, min2, max2, valor2]  min<valor<=max
params = {'INPUT_RASTER': Pendientes,'RASTER_BAND': 1,'TABLE': table,'NO_DATA': -9999,'RANGE_BOUNDARIES': 0,
          'NODATA_FOR_MISSING': False,'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Pendiente}
processing.run(alg, params)

# Asiganción de valor según SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS

# Geoformas indicativas de proceso tipo caida
FILE_NAME = data_path + '/GeoformasIndicativasProcesoTipoCaida.csv'
DF_GeoformasIndicativas = pd.read_csv(FILE_NAME, delimiter = ";", encoding = 'latin-1')
DF_GeoformasIndicativas['CODIGO'] = DF_GeoformasIndicativas['ACRONIMO'].astype(str).str[0:3]

# Geoformas existentes en la capa
FILE_NAME = data_path + '/Pre_Proceso/DF_Raster_SubunidadesGeomorf.csv'
DF_SubunidadesGeoform = pd.read_csv(FILE_NAME, delimiter = ",", encoding = 'latin-1')
DF_SubunidadesGeoform.drop(['index'], axis = 'columns', inplace = True)
DF_SubunidadesGeoform['Caract_3'] = DF_SubunidadesGeoform['Caract'].astype(str).str[0:3]

for i in range(0, len(DF_SubunidadesGeoform)): 
    
    # Se determina la subunidad en cuestión
    Subunidad = DF_SubunidadesGeoform.loc[i, 'Caract']
    Caract = DF_SubunidadesGeoform.loc[i, 'Caract_3']
    
    # Se determina si la subunidad se encuentra en la lista de geomorfas indicativas
    if len(DF_GeoformasIndicativas[DF_GeoformasIndicativas['CODIGO'].isin([Caract])])== 0:
        # Si la longitud de la selección es 0 se determinará se pregunta la susceptibilidad
        Susceptibilidad = ["Alta", "Media", "Baja"]
        Susceptibilidad, ok = QInputDialog.getItem(None, "No se encontro",
                                 f"Seleccione la susceptibilidad para la {Subunidad}", Susceptibilidad, 0, False)
        if Susceptibilidad == "Alta":
            Valor = 2
        elif Susceptibilidad == "Media":
            Valor = 1
        else:
            Valor = 0
            
        DF_SubunidadesGeoform.loc[i, 'Valor'] = Valor
    
    else:
        
        # Si la longitud es diferente de 0 se pondrá como indice la columna del acronimo
        DF_GeoformasIndicativas.set_index('CODIGO', inplace=True)
        # Se reemplazará el valor de susceptibilidad correspondiente que se encuentra en la lista de subunidades
        Valor = DF_GeoformasIndicativas.loc[Caract]['VALOR']
        
        if Valor = np.nan:
            Susceptibilidad = ["Alta", "Media", "Baja"]
            Susceptibilidad, ok = QInputDialog.getItem(None, "No se encontro",
                                     f"Seleccione la susceptibilidad para la {Subunidad}", Susceptibilidad, 0, False)
            if Susceptibilidad == "Alta":
                Valor = 2
            elif Susceptibilidad == "Media":
                Valor = 1
            else:
                Valor = 0
            DF_SubunidadesGeoform.loc[i, 'Valor'] = Valor
        
        else:
            
            DF_SubunidadesGeoform.loc[i,'Valor'] = Valor
        
        # Se devuelve al indice númerico para continuar con el for
        DF_GeoformasIndicativas.reset_index(level=0, inplace=True)

print(DF_SubunidadesGeoform)
DF_SubunidadesGeoform.reset_index().to_csv(data_path + '/Pre_Proceso/DF_RasterCaida_SubunidadesGeoform.csv', header = True, index = False)

#Reclasificación del raster con el valor de Susceptibilidad correspondiente a SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path + '/Pre_Proceso/SubunidadesGeomorf.tif'
DF_SubunidadesGeomorf = data_path + '/Pre_Proceso/DF_RasterCaida_SubunidadesGeoform.csv'
Susceptibilidad_SubunidadesGeomorf = data_path + '/Resultados/SusceptibilidadCaida_SubunidadesGeomorf.tif'
params={'INPUT_RASTER': Factor_Condicionante, 'RASTER_BAND': 1,'INPUT_TABLE': DF_SubunidadesGeomorf, 'MIN_FIELD': 'ID',
        'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Valor', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2, 'NODATA_FOR_MISSING': False, 'DATA_TYPE': 5,
        'OUTPUT': Susceptibilidad_SubunidadesGeomorf}
processing.run(alg, params)

#Asignación de valor según TIPO DE ROCA
#UGS de la zona
FILE_NAME = data_path+'/Pre_Proceso/DF_Raster_UGS.csv'
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

print(DF_UGS)
DF_UGS.reset_index().to_csv(data_path + '/Pre_Proceso/DF_Raster_UGS.csv', header = True, index = False)

#Reclasificación del raster con el valor de Susceptibilidad correspondiente al TIPO DE ROCA.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path+'/Pre_Proceso/UGS.tif'
DF_UGS = data_path + '/Pre_Proceso/DF_Raster_UGS.csv'
Susceptibilidad_UGS = data_path+'/Resultados/Susceptibilidad_UGS.tif'
params={'INPUT_RASTER': Factor_Condicionante, 'RASTER_BAND': 1, 'INPUT_TABLE': DF_UGS, 'MIN_FIELD': 'ID',
        'MAX_FIELD': 'ID', 'VALUE_FIELD': 'Valor', 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2, 'NODATA_FOR_MISSING': False, 'DATA_TYPE': 5,
        'OUTPUT': Susceptibilidad_UGS}
processing.run(alg, params)

#Suma de los valores
Susceptibilidad_Pendiente = QgsRasterLayer(data_path + '/Pre_Proceso/Pendientes_Suscep.tif', "Susceptibilidad_Pendiente")
QgsProject.instance().addMapLayer(Susceptibilidad_Pendiente)
SusceptibilidadCaida_SubunidadesGeomorf = QgsRasterLayer(data_path + '/Resultados/SusceptibilidadCaida_SubunidadesGeomorf.tif', "SusceptibilidadCaida_SubunidadesGeomorf")
QgsProject.instance().addMapLayer(SusceptibilidadCaida_SubunidadesGeomorf)
Susceptibilidad_UGS = QgsRasterLayer(data_path + '/Resultados/Susceptibilidad_UGS.tif', "Susceptibilidad_UGS")
QgsProject.instance().addMapLayer(Susceptibilidad_UGS)
    
#Dirección del resultado de la suma de los valores de susceptibilidad
Output = data_path + '/Resultados/Susceptibilidad_Inicio_Caida.tif'
    
#Sumatoria de los raster
alg = "qgis:rastercalculator"
Expresion = '\"Susceptibilidad_Pendiente@1\" + \"SusceptibilidadCaida_SubunidadesGeomorf@1\" + \"Susceptibilidad_UGS@1\"'
extents = Susceptibilidad_UGS.extent() #Extensión de la capa
xmin = extents.xMinimum()
xmax = extents.xMaximum()
ymin = extents.yMinimum()
ymax = extents.yMaximum()
CRS = QgsCoordinateReferenceSystem('EPSG:3116')
params = {'EXPRESSION': Expresion, 'LAYERS': [Susceptibilidad_UGS], 'CELLSIZE':0, 'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'CRS': CRS,'OUTPUT': Output}
processing.run(alg,params)

#Se reclasifica teniendo en cuenta que 1 será susceptibilidad baja, 2 media y 4 alta.
alg = "native:reclassifybytable"
Resultados_Caida = data_path + '/Resultados/Susceptibilidad_Inicio_Caida.tif'
Susceptibilidad_Caida = data_path + '/Resultados/Susceptibilidad_Caida_Pre.tif'
table = [0, 7, 1, 8, 10, 2, 11, 12, 4]  #[min1, max1, valor1, min2, max2, valor2, min3, max3, valor3] min <= valor <= max
params = {'INPUT_RASTER': Resultados_Caida, 'RASTER_BAND': 1, 'TABLE': table, 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2,
           'NODATA_FOR_MISSING': False, 'DATA_TYPE': 5,'OUTPUT': Susceptibilidad_Caida}
processing.run(alg,params)

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
        CRS = QgsCoordinateReferenceSystem('EPSG:3116')
        Deposito = data_path + '/Pre_Proceso/Caida_Deposito.shp'
        params = {'LAYERS': [Zona_Deposito, Caida_poligonos], 'CRS': CRS, 'OUTPUT': Deposito}
        processing.run(alg, params) 
        
    else:
        Deposito = Ruta_Zona_Deposito

elif os.path.isfile(Ruta_Caida_poligonos) is True:
    Deposito = Ruta_Caida_poligonos

else: 
    QMessageBox.information(iface.mainWindow(), "!Tenga en cuenta!",
                        'La susceptibilida por caídas quedará incompleta debido a que no se cuenta con zonas de deposito')

if os.path.isfile(Deposito) is True:
    # Se sobreescriben las áreas de depósito con un valor de 1
    alg = "gdal:rasterize_over_fixed_value"
    Raster = data_path + '/Resultados/Susceptibilidad_Caida_Pre.tif'
    params = {'INPUT': Deposito,'INPUT_RASTER': Raster,'BURN': 4,'ADD':True,'EXTRA':''}
    processing.run(alg, params)
    
#Se reclasifica teniendo en cuenta que 0 será susceptibilidad baja, 1 media y 2 alta.
alg="native:reclassifybytable"
Resultados_Caida = data_path + '/Resultados/Susceptibilidad_Caida_Pre.tif'
Susceptibilidad_Caida = data_path + '/03 Resultados/Susceptibilidad_Caida.tif'
table=[1, 1, 0, 2, 2, 1, 3, 8, 2]  #[min1, max1, valor1, min2, max2, valor2, min3, max3, valor3] min <= valor <= max
params={'INPUT_RASTER': Resultados_Caida, 'RASTER_BAND': 1, 'TABLE': table, 'NO_DATA': -9999, 'RANGE_BOUNDARIES': 2,
           'NODATA_FOR_MISSING': False, 'DATA_TYPE': 5, 'OUTPUT': Susceptibilidad_Caida}
processing.run(alg, params)
    
Susceptibilidad_Caida = QgsRasterLayer(Susceptibilidad_Caida, "Susceptibilidad_Caida")
QgsProject.instance().addMapLayer(Susceptibilidad_Caida)


    
    