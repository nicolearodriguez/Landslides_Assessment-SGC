import processing
import pandas as pd

#Ruta general de la ubicación de los archivos relativa a la ubicación del programa
data_path= '.../09 Ejecución/01 PyQgis'

#Ruta del DEM
DTM = QgsRasterLayer(data_path+'/01 Entradas/DTM_AP_MCB_Clip41_Aest.tif',"DTM")

########################Zonificación de Susceptibilidad por zonas de inicio tipo Caida########################
#Se reclasifica teniendo en cuenta que 0 serán las pendientes menores a 45, y serán 1 las pendientes mayores a 45.
alg="native:reclassifybytable"
Pendientes = data_path+'/01 Entradas/Pendientes.tif'
Susceptibilidad_Pendiente = data_path+'/02 PreProceso/Pendientes_Suscep.tif'
table=[0,45,0,45,100,1] #[min1,max1,valor1,min2,max2,valor2] min<valor<=max
params={'INPUT_RASTER':Pendientes,'RASTER_BAND':1,'TABLE':table,'NO_DATA':-9999,'RANGE_BOUNDARIES':0,
        'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Susceptibilidad_Pendiente}
processing.run(alg,params)

#Asiganción de valor según SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS
#Geoformas indicativas de proceso tipo caida
FILE_NAME = data_path+'/01 Entradas/GeoformasIndicativasProcesoTipoCaida.csv'
DF_GeoformasIndicativas = pd.read_csv(FILE_NAME, delimiter=";",encoding='latin-1')
#Geoformas existentes en la capa
FILE_NAME = data_path+'/02 PreProceso/DF_Raster_SubunidadesGeomorf.csv'
DF_SubunidadesGeoform = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
DF_SubunidadesGeoform.drop(['index'],axis='columns',inplace=True)

for i in range(0,len(DF_SubunidadesGeoform)): 
    #Se determina la subunidad en cuestión
    Subunidad=DF_SubunidadesGeoform.loc[i,'Caract']
    #Se determina si la subunidad se encuentra en la lista de geomorfas indicativas
    if len(DF_GeoformasIndicativas[DF_GeoformasIndicativas['ACRONIMO'].isin([Subunidad])])==0:
        print('La Subunidad Geomorfologica no se encuentra en la base de datos por lo que se le 
              asignará Susceptibilidad baja, si piensa lo contrario puede modeficar la base de geoformas 
                 indicativas de tipo caída')
        #Si la longitud de la selección es 0 se determinará que la susceptibilidad es baja
        DF_SubunidadesGeoform.loc[i,'Valor']= 0
    else:
        #Si la longitud es diferente de 0 se pondrá como indice la columna del acronimo
        DF_GeoformasIndicativas.set_index('ACRONIMO',inplace=True)
        #Se reemplazará el valor de susceptibilidad correspondiente que se encuentra en la lista de subunidades
        DF_SubunidadesGeoform.loc[i,'Valor']=DF_GeoformasIndicativas.loc[Subunidad]['VALOR']
        #Se devuelve al indice númerico para continuar con el for
        DF_GeoformasIndicativas.reset_index(level=0, inplace=True)    

print(DF_SubunidadesGeoform)
DF_SubunidadesGeoform.reset_index().to_csv(data_path+'/02 PreProceso/DF_RasterCaida_SubunidadesGeoform.csv',header=True,index=False)

#Reclasificación del raster con el valor de Susceptibilidad correspondiente a SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path+'/01 Entradas/SubunidadesGeomorf.tif'
DF_SubunidadesGeomorf = data_path+'/02 PreProceso/DF_RasterCaida_SubunidadesGeoform.csv'
Susceptibilidad_SubunidadesGeomorf = data_path+'/03 Resultados/SusceptibilidadCaida_SubunidadesGeomorf.tif'
params={'INPUT_RASTER':Factor_Condicionante,'RASTER_BAND':1,'INPUT_TABLE':DF_SubunidadesGeomorf,'MIN_FIELD':'ID',
        'MAX_FIELD':'ID','VALUE_FIELD':'Valor','NO_DATA':-9999,'RANGE_BOUNDARIES':2,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,
        'OUTPUT':Susceptibilidad_SubunidadesGeomorf}
processing.run(alg,params)

#Asignación de valor según TIPO DE ROCA
#UGS de la zona
FILE_NAME = data_path+'/02 PreProceso/DF_Raster_UGS.csv'
DF_UGS = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
DF_UGS.drop(['index'],axis='columns',inplace=True)
#Se asigna un valor de susceptibilidad dependiendo del tipo de roca
for i in range (0,len(DF_UGS)):
    General=DF_UGS.loc[i,'General']
    if General=='Rd': #Roca dura
        DF_UGS.loc[i,'Valor']= 0
    elif General=='Ri': #Roca intermedia
        DF_UGS.loc[i,'Valor']= 1
    else:  ##Roca blanda y suelos
        DF_UGS.loc[i,'Valor']= 2

print(DF_UGS)
DF_UGS.reset_index().to_csv(data_path+'/02 PreProceso/DF_Raster_UGS.csv',header=True,index=False)

#Reclasificación del raster con el valor de Susceptibilidad correspondiente al TIPO DE ROCA.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path+'/01 Entradas/UGS.tif'
DF_UGS = data_path+'/02 PreProceso/DF_Raster_UGS.csv'
Susceptibilidad_UGS = data_path+'/03 Resultados/Susceptibilidad_UGS.tif'
params={'INPUT_RASTER':Factor_Condicionante,'RASTER_BAND':1,'INPUT_TABLE':DF_UGS,'MIN_FIELD':'ID',
        'MAX_FIELD':'ID','VALUE_FIELD':'Valor','NO_DATA':-9999,'RANGE_BOUNDARIES':2,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,
        'OUTPUT':Susceptibilidad_UGS}
processing.run(alg,params)

#Suma de los valores
Susceptibilidad_Pendiente=QgsRasterLayer(data_path+'/02 PreProceso/Pendientes_Suscep.tif',"Susceptibilidad_Pendiente")
QgsProject.instance().addMapLayer(Susceptibilidad_Pendiente)
SusceptibilidadCaida_SubunidadesGeomorf=QgsRasterLayer(data_path+'/03 Resultados/SusceptibilidadCaida_SubunidadesGeomorf.tif',"SusceptibilidadCaida_SubunidadesGeomorf")
QgsProject.instance().addMapLayer(SusceptibilidadCaida_SubunidadesGeomorf)
Susceptibilidad_UGS=QgsRasterLayer(data_path+'/03 Resultados/Susceptibilidad_UGS.tif',"Susceptibilidad_UGS")
QgsProject.instance().addMapLayer(Susceptibilidad_UGS)
    
#Dirección del resultado de la suma de los valores de susceptibilidad
Output = data_path+'/03 Resultados/Susceptibilidad_Inicio_Caida.tif'
    
#Sumatoria de los raster
alg = "qgis:rastercalculator"
Expresion = '\"Susceptibilidad_Pendiente@1\" + \"SusceptibilidadCaida_SubunidadesGeomorf@1\" + \"Susceptibilidad_UGS@1\"'
extents = Susceptibilidad_UGS.extent() #Extensión de la capa
xmin = extents.xMinimum()
xmax = extents.xMaximum()
ymin = extents.yMinimum()
ymax = extents.yMaximum()
CRS= QgsCoordinateReferenceSystem('EPSG:3116')
params = {'EXPRESSION': Expresion,'LAYERS':[Susceptibilidad_UGS],'CELLSIZE':0,'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'CRS': CRS,'OUTPUT': Output}
processing.run(alg,params)
 
Susceptibilidad_Inicio_Caida=QgsRasterLayer(data_path+'/03 Resultados/Susceptibilidad_Inicio_Caida.tif', "Susceptibilidad_Inicio_Caida")
QgsProject.instance().addMapLayer(Susceptibilidad_Inicio_Caida) 
 
#Se reclasifica teniendo en cuenta que 1 será susceptibilidad baja, 2 media y 4 alta.
alg="native:reclassifybytable"
Resultados_Caida = data_path+'/03 Resultados/Susceptibilidad_Inicio_Caida.tif'
Susceptibilidad_Caida = data_path+'/03 Resultados/Susceptibilidad_Inicio_Caida_Reclass.tif'
table=[0,0,1,1,3,2,4,4,4]  #[min1,max1,valor1,min2,max2,valor2,min3,max3,valor3] min<=valor<=max
params={'INPUT_RASTER':Resultados_Caida,'RASTER_BAND':1,'TABLE':table,'NO_DATA':-9999,'RANGE_BOUNDARIES':2,
           'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Susceptibilidad_Caida}
processing.run(alg,params)

Susceptibilidad_Inicio_Caida_Reclass=QgsRasterLayer(data_path+'/03 Resultados/Susceptibilidad_Inicio_Caida_Reclass.tif', "Susceptibilidad_Inicio_Caida_Reclass")
QgsProject.instance().addMapLayer(Susceptibilidad_Inicio_Caida_Reclass)

########################Zonificación de Susceptibilidad por zonas de deposito tipo Caida########################    
    
#Se hace la corrección geometrica de las capas de movimientos.
alg = "native:fixgeometries"
Movimientos_Masa = data_path+'/01 Entradas/Mov_Masa.shp'
Movimientos_Corregido = data_path+'/02 PreProceso/Mov_Masa_Corr.shp'
params = {'INPUT':Movimientos_Masa,'OUTPUT': Movimientos_Corregido}
processing.run(alg,params)

#Se agrega una columna de Raster a la capa de movimientos en masa
Movimientos_Masa = QgsVectorLayer(data_path+'/02 PreProceso/Mov_Masa_Corr.shp','Movimientos_Masa')
caps = Movimientos_Masa.dataProvider().capabilities()
Movimientos_Masa.dataProvider().addAttributes([QgsField("Raster", QVariant.Int)])
Movimientos_Masa.updateFields()

col= Movimientos_Masa.fields().indexFromName("Raster")

#A todas se les asignará un valor de 1 en la columna raster
for feature in Movimientos_Masa.getFeatures():
    fid=feature.id()
    if caps & QgsVectorDataProvider.ChangeAttributeValues:
        attrs = { col : 1 }
        Movimientos_Masa.dataProvider().changeAttributeValues({ fid : attrs })

caps = Movimientos_Masa.dataProvider().capabilities()

#Selecciono los movimientos en masa correspondientes a caída
Movimientos_Masa.selectByExpression(f'"TIPO_MOV1"=\'Caida\'', QgsVectorLayer.SetSelection)
#Se reemplazan los id del atributo seleccionada
selected_fid = []
selection = Movimientos_Masa.selectedFeatures()
for feature in selection: #For en la selección
    fid=feature.id()
    if caps & QgsVectorDataProvider.ChangeAttributeValues:
        attrs = { col : 2 } #Se reemplaza un valor de 2 en la columna raster de los elementos seleccionados (caida)
        Movimientos_Masa.dataProvider().changeAttributeValues({ fid : attrs })
 
QgsProject.instance().addMapLayer(Movimientos_Masa)
 
alg = "gdal:rasterize"
Shape = Movimientos_Masa
Raster = data_path+'/01 Entradas/Susceptibilidad_Caida_Deposito.tif'
Field= 'Raster'
extents = Movimientos_Masa.extent()
xmin = extents.xMinimum()
xmax = extents.xMaximum()
ymin = extents.yMinimum()
ymax = extents.yMaximum()
xsize = round(DTM.rasterUnitsPerPixelX(),1)
ysize = round(DTM.rasterUnitsPerPixelY(),1)
params= {'INPUT':Shape,'FIELD': Field,'BURN':0,'UNITS':1,'WIDTH':xsize,'HEIGHT':ysize,
         'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'NODATA':0,'OPTIONS':'',
          'DATA_TYPE':5,'INIT':None,'INVERT':False,'OUTPUT': Raster}
processing.run(alg,params)

#Suma de los valores
Susceptibilidad_Caida_Deposito=QgsRasterLayer(data_path+'/01 Entradas/Susceptibilidad_Caida_Deposito.tif',"Susceptibilidad_Caida_Deposito")
QgsProject.instance().addMapLayer(Susceptibilidad_Caida_Deposito)

#Dirección del resultado de la suma de los Wf
Output = data_path+'/03 Resultados/Susceptibilidad_Caida.tif'

#Sumatoria de los raster
alg = "qgis:rastercalculator"
Expresion = '\"Susceptibilidad_Caida_Deposito@1\" + \"Susceptibilidad_Inicio_Caida_Reclass@1\"'
extents = Susceptibilidad_Inicio_Caida.extent()
xmin = extents.xMinimum()
xmax = extents.xMaximum()
ymin = extents.yMinimum()
ymax = extents.yMaximum()
CRS= QgsCoordinateReferenceSystem('EPSG:3116')
params = {'EXPRESSION': Expresion,'LAYERS':[Susceptibilidad_Inicio_Caida],'CELLSIZE':0,
          'EXTENT': "%f,%f,%f,%f"% (xmin, xmax, ymin, ymax),'CRS': CRS,'OUTPUT': Output}
processing.run(alg,params)

Susceptibilidad_Caida=QgsRasterLayer(data_path+'/03 Resultados/Susceptibilidad_Caida.tif',"Susceptibilidad_Caida")
QgsProject.instance().addMapLayer(Susceptibilidad_Caida)

#Se reclasifica teniendo en cuenta que 0 será susceptibilidad baja, 1 media y 2 alta.
alg="native:reclassifybytable"
Resultados_Caida = data_path+'/03 Resultados/Susceptibilidad_Caida.tif'
Susceptibilidad_Caida = data_path+'/03 Resultados/Susceptibilidad_Caida_Reclass.tif'
table=[1,2,0,3,4,1,5,8,2]  #[min1,max1,valor1,min2,max2,valor2,min3,max3,valor3] min<=valor<=max
params={'INPUT_RASTER':Resultados_Caida,'RASTER_BAND':1,'TABLE':table,'NO_DATA':-9999,'RANGE_BOUNDARIES':2,
           'NODATA_FOR_MISSING':False,'DATA_TYPE':5,'OUTPUT':Susceptibilidad_Caida}
processing.run(alg,params)
    
Susceptibilidad_Caida_Reclass=QgsRasterLayer(data_path+'/03 Resultados/Susceptibilidad_Caida_Reclass.tif',"Susceptibilidad_Caida_Reclass")
QgsProject.instance().addMapLayer(Susceptibilidad_Caida_Reclass)


    
    