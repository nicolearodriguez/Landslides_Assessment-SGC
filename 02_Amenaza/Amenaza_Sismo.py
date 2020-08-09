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

# Se lee el inventario de movimientos en masa con fecha y susceptibilidad
DF_Inv = pd.read_csv(data_path + '/Pre_Proceso/DF_Mov_Masa_Sismos.csv')
DF_Inv = DF_Inv.drop(['level_0'], axis=1) #Borrar
DF_Inv = DF_Inv.dropna(axis=0, subset=['FECHA_MOV'])
DF_Inv.reset_index(level=0, inplace=True)
DF_Inv['FECHA_MOV'] = DF_Inv['FECHA_MOV'].astype(str) #Identifico el nombre de la columna que contiene las fechas

#Se crea el dataframe con el que se hace el análisis
DF_Probabilidad = pd.DataFrame(columns=['Tipo_Mov','Amenaza','P[R>Rt]'])
DF_Final = pd.DataFrame()

#Se extraen los tipos de movimientos en masa
Tipo_Evento = DF_Inv['TIPO_MOV1'].unique()
Tipo_Evento = pd.DataFrame(Tipo_Evento, columns=['Tipo_Mov'],dtype=object)
    
#Se hace el estudio según el tipo de evento
for id_evento in range (0,len(Tipo_Evento)): # len(Categorias_Amenaza)
    Tipo = Tipo_Evento.loc[id_evento,'Tipo_Mov']
    
    if len(DF_Inv[DF_Inv['TIPO_MOV1'] == Tipo]) < 2:
        print(f'No hay suficientes datos para completar el análisis del tipo {Tipo}')
        print('\n')
        continue
    
    print(f'Se hará el análisis para el tipo {Tipo}')
    print('\n')
    
    DF_Inv.set_index('TIPO_MOV1',inplace=True)
    DF_Inv_Tipo = DF_Inv.loc[Tipo]
    DF_Inv_Tipo.reset_index(level=0, inplace=True)
    DF_Inv.reset_index(level=0, inplace=True)
        
    if Tipo == "Deslizamiento":
        Campo_Amenaza = "Sus_Desliz"
    elif Tipo == "Caida":
        Campo_Amenaza = "Sus_Caida"
    elif Tipo == "Flujo":
        Campo_Amenaza = "Sus_Flujo"
    else:
        print("No se reconoce el tipo de movimiento en masa")
        print('\n')
        continue
    
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
            
        años = (fin.year-inicio.year)
        
        n = len(DF_Inv_Amenaza_Tipo)
        print(f'En {años} años, hubo {n} movimientos en masa tipo {Tipo} con categoria {Cat_amenaza}')
            
        I = años/n
        t = 1
        P = 1 - math.exp(-t/I)
        print(f'La probabilidad P[R>Rt] = {P} ')
        print('\n')
        DF_Probabilidad.loc[id_amenaza, 'P[R>Rt]'] = P
        
    DF_Final = DF_Final.append(DF_Probabilidad)

DF_Final.reset_index(level=0, inplace=True)
DF_Final = DF_Final.drop(['index'], axis=1)
print(DF_Final)
print('\n')
DF_Final.reset_index().to_csv(data_path + '/Resultados/DF_Amenaza_Sismo.csv',header=True,index=False)

elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)