# -*- coding: utf-8 -*-
"""
Created on Fri Jul 17 13:19:20 2020

@author: HOGAR
"""

import math
import pandas as pd
from time import time

start_time = time()

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
data_path = data_path.replace("\\", "/")

#Se define cómo se quiere hacer la discritización
Discri = ["Amenaza", "Amenaza - Tipo de movimiento"]
Discritizacion, ok = QInputDialog.getItem(None, "Discretización", "Seleccione la cómo desea hacer la discretización de los MM", Discri, 0, False)

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

for grupo in range (0,len(Cluster)):
    Cluster_id = Cluster.loc[grupo,'Cluster']
    
    if len(DF_Inv[DF_Inv['CLUSTER_ID'] == Cluster_id]) < 2:
        print(f'No hay suficientes datos para completar el análisis del cluster {Cluster_id}')
        print('\n')
        continue
    
    print(f'Se hará el análisis para el cluster {Cluster_id}')
    print('\n')
    
    DF_Inv.set_index('CLUSTER_ID',inplace=True)
    DF_Inv_Cluster = DF_Inv.loc[Cluster_id]
    DF_Inv_Cluster.reset_index(level=0, inplace=True)
    DF_Inv.reset_index(level=0, inplace=True)

    #Se extraen los tipos de movimientos en masa
    Tipo_Evento = DF_Inv_Cluster['TIPO_MOV1'].unique()
    Tipo_Evento = pd.DataFrame(Tipo_Evento, columns=['Tipo_Mov'],dtype=object)
    
    if Discritizacion == "Amenaza": Tipo_Evento = [1]

    #Se hace el estudio según el tipo de evento
    for id_evento in range (0,len(Tipo_Evento)):
        
        if Discritizacion == "Amenaza - Tipo de movimiento":
            Tipo = Tipo_Evento.loc[id_evento,'Tipo_Mov']
            
            if len(DF_Inv_Cluster[DF_Inv_Cluster['TIPO_MOV1'] == Tipo]) < 2:
                print(f'No hay suficientes datos para completar el análisis del tipo {Tipo}')
                print('\n')
                continue
            
            print(f'Se hará el análisis para el tipo {Tipo}')
            print('\n')
            
            DF_Inv_Cluster.set_index('TIPO_MOV1',inplace=True)
            DF_Inv_Tipo = DF_Inv_Cluster.loc[Tipo]
            DF_Inv_Tipo.reset_index(level=0, inplace=True)
            DF_Inv_Cluster.reset_index(level=0, inplace=True)
                
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
            DF_Inv_Tipo = DF_Inv_Cluster.copy(deep=True)
            Campo_Amenaza = "Susc_Desli"
            Tipo = "Todos"
             
        if (Campo_Amenaza in DF_Inv_Tipo.columns) is False:
            continue
            
        Categorias_Amenaza = DF_Inv_Tipo[Campo_Amenaza].unique()
        Categorias_Amenaza = pd.DataFrame(Categorias_Amenaza,columns=['Amenaza'],dtype=object)
            
        #Se hace el estudio según la categoría de amenaza
        for id_amenaza in range (0,len(Categorias_Amenaza)): 
            Amenaza = Categorias_Amenaza.loc[id_amenaza,'Amenaza']
            
            if Amenaza ==2:
                Cat_amenaza = 'Alta'
            elif Amenaza ==1:
                Cat_amenaza = 'Media'
            else:
                Cat_amenaza = 'Baja'
            
            if len(DF_Inv_Tipo[DF_Inv_Tipo[Campo_Amenaza] == Amenaza]) < 2:
                print(f'No hay suficientes datos para completar el análisis de amenaza {Cat_amenaza} y tipo {Tipo}')
                print('\n')
                continue
            
            print(f'Se hará el análisis para amenaza {Cat_amenaza}') #Se imprime la amenaza en el que va el análisis
            print('\n') # Se imprime un renglón en blanco
            
            DF_Probabilidad.loc[id_amenaza,'Cluster'] = Cluster_id
            DF_Probabilidad.loc[id_amenaza,'Amenaza'] = Cat_amenaza
            DF_Probabilidad.loc[id_amenaza,'Tipo_Mov'] = Tipo

            #Se seleccionan del dataframe únicamente los movimientos en masa correspondientes al tipo
            DF_Inv_Tipo.set_index(Campo_Amenaza, inplace = True)
            DF_Inv_Amenaza_Tipo = DF_Inv_Tipo.loc[Amenaza]
            DF_Inv_Amenaza_Tipo.reset_index(level=0, inplace = True)
            DF_Inv_Tipo.reset_index(level=0, inplace=True)
                
            # 2- Extrae los valores únicos de fechas de reporte de movimientos en masa
            DF_Fechas_Unicas_MM = pd.DataFrame(columns=['Fecha'],dtype=str)
            F = DF_Inv_Amenaza_Tipo['FECHA_MOV'].unique()
            DF_Fechas_Unicas_MM['Fecha'] = F
            DF_Fechas_Unicas_MM['Fecha'] = pd.to_datetime(DF_Fechas_Unicas_MM.Fecha)
            DF_Fechas_Unicas_MM['Fecha'] = DF_Fechas_Unicas_MM['Fecha'].dt.strftime('%d/%m/%Y')
            
            DF_Fechas_Unicas_MM['Fecha'] = pd.to_datetime(DF_Fechas_Unicas_MM.Fecha, dayfirst=True)
            DF_Fechas_Unicas_MM = DF_Fechas_Unicas_MM.sort_values(by = 'Fecha')
            DF_Fechas_Unicas_MM.reset_index(level = 0, inplace = True)
            DF_Fechas_Unicas_MM.drop(['index'],axis = 'columns', inplace = True)
            
            inicio = DF_Fechas_Unicas_MM.loc[0]['Fecha']
            inicio1 = str(inicio.strftime("%d/%m/%Y"))
            print(f'La fecha inicial es {inicio1}')
            fin = DF_Fechas_Unicas_MM.loc[len(DF_Fechas_Unicas_MM)-1]['Fecha']
            fin1 = str(fin.strftime("%d/%m/%Y"))
            print(f'La fecha final es {fin1}')
                
            años = (fin.year - inicio.year)
            if años == 0:
                años = 1
            n = len(DF_Inv_Amenaza_Tipo)
            print(f'En {años} años, hubo {n} movimientos en masa tipo {Tipo} con categoria {Cat_amenaza}')
                
            I = años/n
            t = 1
            P = 1 - math.exp(-t/I)
            print(f'La probabilidad P[R>Rt] = {P} ')
            print('\n')
            DF_Probabilidad.loc[id_amenaza, 'P[R>Rt]'] = P
            
        DF_Final = DF_Final.append(DF_Probabilidad)

DF_Final = DF_Final.sort_values(by = 'Cluster')
DF_Final.reset_index(level=0, inplace=True)
DF_Final = DF_Final.drop(['index'], axis=1)
print(DF_Final)
print('\n')
DF_Final.reset_index().to_csv(data_path + '/Resultados/DF_Amenaza_Sismo.csv',header=True,index=False)

Amenaza_Sismo = QgsVectorLayer(data_path + '/Amenaza/Amenaza_Sismos.shp')

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
        
    for i in range(0, len(atributos)):
        Atri = int(atributos[i])

        Indice_D_0 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
        if len(Indice_D_0) != 0: 
            Ptem_D_0 = float(DF_Final.loc[Indice_D_0[0], 'P[R>Rt]'])
        else:
            Ptem_D_0 = np.nan
            
        Indice_D_1 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
        if len(Indice_D_1) != 0: 
            Ptem_D_1 = float(DF_Final.loc[Indice_D_1[0], 'P[R>Rt]'])
        else:
            Ptem_D_1 = np.nan
            
        Indice_D_2 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Deslizamiento')].index
        if len(Indice_D_2) != 0: 
            Ptem_D_2 = float(DF_Final.loc[Indice_D_2[0], 'P[R>Rt]'])
        else:
            Ptem_D_2 = np.nan
        
        Indice_C_0 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Caida')].index
        if len(Indice_C_0) != 0: 
            Ptem_C_0 = float(DF_Final.loc[Indice_C_0[0], 'P[R>Rt]'])
        else:
            Ptem_C_0 = np.nan
        
        Indice_C_1 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Caida')].index
        if len(Indice_C_1) != 0: 
            Ptem_C_1 = float(DF_Final.loc[Indice_C_1[0], 'P[R>Rt]'])
        else:
            Ptem_C_1 = np.nan
            
        Indice_C_2 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Caida')].index
        if len(Indice_C_2) != 0: 
            Ptem_C_2 = float(DF_Final.loc[Indice_C_2[0], 'P[R>Rt]'])
        else:
            Ptem_C_2 = np.nan
          
        Indice_F_0 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Baja') & (DF_Final.Tipo_Mov == 'Flujo')].index
        if len(Indice_F_0) != 0: 
            Ptem_F_0 = float(DF_Final.loc[Indice_F_0[0], 'P[R>Rt]'])
        else:
            Ptem_F_0 = np.nan
            
        Indice_F_1 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Media') & (DF_Final.Tipo_Mov == 'Flujo')].index
        if len(Indice_F_1) != 0: 
            Ptem_F_1 = float(DF_Final.loc[Indice_F_1[0], 'P[R>Rt]'])
        else:
            Ptem_F_1 = np.nan
            
        Indice_F_2 = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Alta') & (DF_Final.Tipo_Mov == 'Flujo')].index
        if len(Indice_F_2) != 0: 
            Ptem_F_2 = float(DF_Final.loc[Indice_F_2[0], 'P[R>Rt]'])
        else:
            Ptem_F_2 = np.nan

        # Se hace la selección en la capa de la caracteristica en cuestión
        Amenaza_Sismo.selectByExpression(
            f'"CLUSTER_ID"=\'{Atri}\'', QgsVectorLayer.SetSelection)
            
        # Se reemplazan los id del atributo seleccionada
        selected_fid = []
        selection = Amenaza_Sismo.selectedFeatures()
            
        for feature in selection:  # Se recorren las filas seleccionadas
            fid = feature.id()  # Se obtiene el id de la fila seleccionada
            if caps & QgsVectorDataProvider.ChangeAttributeValues:
                # La columna nueva se llenará con el id de la caracteristica (i+1)
                attrs = { D_Baja : Ptem_D_0, D_Media : Ptem_D_1, D_Alta : Ptem_D_2, C_Baja : Ptem_C_0, C_Media : Ptem_C_1, C_Alta : Ptem_C_2, F_Baja : Ptem_F_0, F_Media : Ptem_F_1, F_Alta : Ptem_F_2 }
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

        Indice_Baja = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Baja')].index
        if len(Indice_Baja) != 0: 
            Ptem_Baja = float(DF_Final.loc[Indice_Baja[0], 'P[R>Rt]'])
        else:
            Ptem_Baja = np.nan
            
        Indice_Media = DF_Final[(DF_Final.Cluster == Atri) & (DF_Final.Amenaza == 'Media')].index
        if len(Indice_Media) != 0: 
            Ptem_Media = float(DF_Final.loc[Indice_Media[0], 'P[R>Rt]'])
        else:
            Ptem_Media = np.nan
            
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
                # La columna nueva se llenará con el id de la caracteristica (i+1)
                attrs = { Baja : Ptem_Baja, Media : Ptem_Media, Alta : Ptem_Alta }
                # Se hace el cambio de los atributos
                Amenaza_Sismo.dataProvider().changeAttributeValues({fid: attrs})

elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)