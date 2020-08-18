# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 13:19:20 2020

@author: HOGAR
"""

import math
import pandas as pd
from time import time

#Se determina el momento en que inicia la ejecución del programa
start_time = time()

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
if ok == False:
    raise Exception('Cancelar')
data_path = data_path.replace("\\", "/")

#Se define cómo se quiere hacer la discritización
Discri = ["Amenaza", "Amenaza - Tipo de movimiento"]
Discritizacion, ok = QInputDialog.getItem(None, "Discretización", "Seleccione la cómo desea hacer la discretización de los MM", Discri, 0, False)
if ok == False:
    raise Exception('Cancelar')

# Se lee el inventario de movimientos en masa con fecha y susceptibilidad
DF_Inv = pd.read_csv(data_path + '/Amenaza/DF_Mov_Masa_Sismos.csv')
DF_Inv = DF_Inv.drop(['level_0'], axis=1) #Borrar
DF_Inv = DF_Inv.dropna(axis=0, subset=['FECHA_MOV'])
DF_Inv.reset_index(level=0, inplace=True)
DF_Inv['FECHA_MOV'] = DF_Inv['FECHA_MOV'].astype(str) #Identifico el nombre de la columna que contiene las fechas

#Se crea el dataframe con el que se hace el análisis
DF_Probabilidad = pd.DataFrame(columns=['Cluster', 'Tipo_Mov', 'Amenaza', 'P[R>Rt]'])
DF_Final = pd.DataFrame()

#Se determinan el número de grupos de MM
Cluster = DF_Inv['CLUSTER_ID'].unique()
Cluster = pd.DataFrame(Cluster, columns=['Cluster'],dtype=object)

# Se recorre los valores de grupos de cluster
for grupo in range (0,len(Cluster)):
    Cluster_id = Cluster.loc[grupo,'Cluster']
    
    # Si la cantidad de datos de ese grupo es menor a dos no se puede hacer el análisis
    if len(DF_Inv[DF_Inv['CLUSTER_ID'] == Cluster_id]) < 2:
        print(f'No hay suficientes datos para completar el análisis del cluster {Cluster_id}')
        print('\n')
        continue
    
    print(f'Se hará el análisis para el cluster {Cluster_id}')
    print('\n')
    
    # Se pone como indice la columna del cluster
    DF_Inv.set_index('CLUSTER_ID',inplace=True)
    DF_Inv_Cluster = DF_Inv.loc[Cluster_id] # Se extraen los MM correspondientes a ese cluster
    DF_Inv_Cluster.reset_index(level=0, inplace=True)
    DF_Inv.reset_index(level=0, inplace=True)

    #Se extraen los tipos de movimientos en masa
    Tipo_Evento = DF_Inv_Cluster['TIPO_MOV1'].unique()
    Tipo_Evento = pd.DataFrame(Tipo_Evento, columns=['Tipo_Mov'],dtype=object)
    
    # Si la descretización es solo por amenaza la extensión del for solo será de 1
    if Discritizacion == "Amenaza": Tipo_Evento = [1]

    #Se hace el estudio según el tipo de evento
    for id_evento in range (0,len(Tipo_Evento)):
        
        # Si la descretización es por tipo de movimiento y amenaza
        if Discritizacion == "Amenaza - Tipo de movimiento":
            Tipo = Tipo_Evento.loc[id_evento,'Tipo_Mov']
            
            # Si los MM correspondientes a este tipo de movimiento son menores a dos no se puede continuar con el análisis
            if len(DF_Inv_Cluster[DF_Inv_Cluster['TIPO_MOV1'] == Tipo]) < 2:
                print(f'No hay suficientes datos para completar el análisis del tipo {Tipo}')
                print('\n')
                continue
            
            print(f'Se hará el análisis para el tipo {Tipo}')
            print('\n')
            
            # Se pone como indice la columna de tipo de movimiento
            DF_Inv_Cluster.set_index('TIPO_MOV1',inplace=True)
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
            DF_Inv_Tipo = DF_Inv_Cluster.copy(deep=True)
            Campo_Amenaza = "Susc_Desli"
            Tipo = "Todos"
            
        # Si el campo determinado para la discretización de la amenaza no está en el inventario se continua
        if (Campo_Amenaza in DF_Inv_Tipo.columns) is False:
            continue
        
        # Se definen los valores únicos de amenaza que se tengan
        Categorias_Amenaza = DF_Inv_Tipo[Campo_Amenaza].unique()
        Categorias_Amenaza = pd.DataFrame(Categorias_Amenaza,columns=['Amenaza'],dtype=object)
            
        #Se hace el estudio según la categoría de amenaza
        for id_amenaza in range (0,len(Categorias_Amenaza)): 
            Amenaza = Categorias_Amenaza.loc[id_amenaza,'Amenaza']
            
            # Según el id de la amenaza se puede determinar la categoria
            if Amenaza ==2:
                Cat_amenaza = 'Alta'
            elif Amenaza ==1:
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
            
            DF_Probabilidad.loc[id_amenaza,'Cluster'] = Cluster_id
            DF_Probabilidad.loc[id_amenaza,'Amenaza'] = Cat_amenaza
            DF_Probabilidad.loc[id_amenaza,'Tipo_Mov'] = Tipo

            # Se pone como indice la columna de categoria de amenaza
            DF_Inv_Tipo.set_index(Campo_Amenaza, inplace = True)
            # Se selecciona los MM correspondientes a la categoría de amenaza
            DF_Inv_Amenaza_Tipo = DF_Inv_Tipo.loc[Amenaza]
            DF_Inv_Amenaza_Tipo.reset_index(level=0, inplace = True)
            DF_Inv_Tipo.reset_index(level=0, inplace=True)
                
            # Se extrae los valores únicos de fechas de reporte de movimientos en masa
            DF_Fechas_Unicas_MM = pd.DataFrame(columns=['Fecha'],dtype=str)
            F = DF_Inv_Amenaza_Tipo['FECHA_MOV'].unique()
            DF_Fechas_Unicas_MM['Fecha'] = F
            DF_Fechas_Unicas_MM['Fecha'] = pd.to_datetime(DF_Fechas_Unicas_MM.Fecha, dayfirst=True)
            DF_Fechas_Unicas_MM = DF_Fechas_Unicas_MM.sort_values(by = 'Fecha')
            DF_Fechas_Unicas_MM.reset_index(level = 0, inplace = True)
            DF_Fechas_Unicas_MM.drop(['index'],axis = 'columns', inplace = True)
            
            # Se determina la fecha inicial con la que se cuenta con datos
            inicio = DF_Fechas_Unicas_MM.loc[0]['Fecha']
            inicio1 = str(inicio.strftime("%d/%m/%Y"))
            print(f'La fecha inicial es {inicio1}')
            # Se determina la fecha final en la que se cuenta con datos
            fin = DF_Fechas_Unicas_MM.loc[len(DF_Fechas_Unicas_MM)-1]['Fecha']
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
DF_Final.reset_index(level=0, inplace=True)
DF_Final = DF_Final.drop(['index'], axis=1)
print(DF_Final)
print('\n')
# Se exporta el dataframe como archivo csv
DF_Final.reset_index().to_csv(data_path + '/Resultados/DF_Amenaza_Sismo.csv',header=True,index=False)

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

Amenaza_Sismo = QgsVectorLayer(data_path + '/Amenaza/Amenaza_Sismos.shp', 'Amenaza_Sismo')
QgsProject.instance().addMapLayer(Amenaza_Sismo)

elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)