import processing
import pandas as pd

data_path= 'D:/Nueva carpeta/UNIVERSIDAD/8_OCTAVO/05 TRABAJO DE GRADO I/09 Ejecución/01 PyQgis'

DTM = QgsRasterLayer(data_path+'/01 Entradas/DTM_AP_MCB_Clip41_Aest.tif',"DTM")

#Asiganción de valor según SUBUNIDADES GEOMORFOLOGICAS INDICATIVAS
#Geoformas indicativas de proceso tipo flujo
FILE_NAME = data_path+'/01 Entradas/GeoformasIndicativasProcesoTipoFlujo.csv'
DF_GeoformasIndicativas = pd.read_csv(FILE_NAME, delimiter=";",encoding='latin-1')
#Geoformas existentes en la capa
FILE_NAME = data_path+'/02 PreProceso/DF_Raster_SubunidadesGeomorf.csv'
DF_SubunidadesGeoform = pd.read_csv(FILE_NAME, delimiter=",",encoding='latin-1')
DF_SubunidadesGeoform.drop(['index'],axis='columns',inplace=True)

for i in range(0,len(DF_SubunidadesGeoform)):
    Subunidad=DF_SubunidadesGeoform.loc[i,'Caract']
    if len(DF_GeoformasIndicativas[DF_GeoformasIndicativas['ACRONIMO'].isin([Subunidad])])==0:
        print('La Subunidad Geomorfologica no se encuentra en la base de datos por lo que se le asignará Susceptibilidad baja, si piensa lo contrario puede modeficar la base de geoformas indicativas de tipo flujo')
        DF_SubunidadesGeoform.loc[i,'Valor']= 0
    else:
        DF_GeoformasIndicativas.set_index('ACRONIMO',inplace=True)
        DF_SubunidadesGeoform.loc[i,'Valor']=DF_GeoformasIndicativas.loc[Subunidad]['VALOR']
        DF_GeoformasIndicativas.reset_index(level=0, inplace=True)

print(DF_SubunidadesGeoform)
DF_SubunidadesGeoform.reset_index().to_csv(data_path+'/02 PreProceso/DF_RasterFlujo_SubunidadesGeoform.csv',header=True,index=False)

#Reclasificación del raster con el valor de Susceptibilidad correspondiente.
alg="native:reclassifybylayer"
Factor_Condicionante = data_path+'/01 Entradas/SubunidadesGeomorf.tif'
DF_SubunidadesGeomorf = data_path+'/02 PreProceso/DF_RasterFlujo_SubunidadesGeoform.csv'
Susceptibilidad_SubunidadesGeomorf = data_path+'/03 Resultados/SusceptibilidadFlujo_SubunidadesGeomorf.tif'
params={'INPUT_RASTER':Factor_Condicionante,'RASTER_BAND':1,'INPUT_TABLE':DF_SubunidadesGeomorf,'MIN_FIELD':'ID',
        'MAX_FIELD':'ID','VALUE_FIELD':'Valor','NO_DATA':-9999,'RANGE_BOUNDARIES':2,'NODATA_FOR_MISSING':False,'DATA_TYPE':5,
        'OUTPUT':Susceptibilidad_SubunidadesGeomorf}
processing.run(alg,params)

SusceptibilidadFlujo_SubunidadesGeomorf=QgsRasterLayer(data_path+'/03 Resultados/SusceptibilidadFlujo_SubunidadesGeomorf.tif',"SusceptibilidadFlujo_SubunidadesGeomorf")
QgsProject.instance().addMapLayer(SusceptibilidadCaida_SubunidadesGeomorf)

