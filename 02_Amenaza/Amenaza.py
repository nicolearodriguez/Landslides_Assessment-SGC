# -*- coding: utf-8 -*-
"""
Editor de Spyder

Este es un archivo temporal.
"""

"""
PROCEDIMIENTO GENERAL
1. Ingresar registro de datos con precipitación (P) diaria de la estación objeto ('Precipitacion_diaria.csv' )
2. Ingresar el catálogo de movimientos en masa ('Inventario_MM.csv')
3. Sumar la precipitación de los dias antecedentes (Pant) que se deseen analizar para cada evento, sin incluir la P del dáa en análisis
4. Almacenar como par de datos la precipitacion del dia (P24) y la Pant asociada para cada evento
5. Graficar el conjunto de datos Pant,P24 de todos los eventos
6. Hacer una regresion lineal, PT=b-m*Pant  (PT=umbral de lluvia)
7. Acumular el Pant para cada día del registro de precipitación de la estación objeto
8. Calcular el PT para todo el registro de precipitación de la estación objeto usando el Pant del paso 7
9. Contar cuantas veces P>PT durante la ventana de observación en que ocurrieron los eventos

"""


import math
import pandas as pd
import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt
#from datetime import datetime, timedelta

# Defina el número de días de lluvia antecedente que desea acumular
d_ant=15

# Ingresar registro de precipitación diaria para la estación en análisis
DF_Precipitacion_diaria=pd.read_csv('01_Precipitacion_diaria.csv')
DF_Precipitacion_diaria['date']=DF_Precipitacion_diaria['date'].astype(str)
Pant=DF_Precipitacion_diaria['P'].rolling(min_periods=d_ant-1, window=d_ant-1).sum()-DF_Precipitacion_diaria['P']
DF_Precipitacion_diaria['Pant']=Pant

# Se lee el inventario de movimientos en masa con fecha y susceptibilidad
DF_Inv=pd.read_csv('02_Inventario_MM.csv')
DF_Inv=DF_Inv[['FECHA_MOV','TIPO_MOV1','AMENAZA']]
DF_Inv['FECHA_MOV']=DF_Inv['FECHA_MOV'].astype(str) #Identifico el nombre de la columna que contiene las fechas

#Se crea el dataframe con el que se hace el análisis
DF_Excedencia=pd.DataFrame(columns=['Amenaza','Tipo_Mov','Excedencia','P[R>Rt]','N','Fr','Ptem'])

#Se extraen los tipos de movimientos en masa
Categorias_Amenaza=DF_Inv['AMENAZA'].unique()
Categorias_Amenaza=pd.DataFrame(Categorias_Amenaza,columns=['Amenaza'],dtype=str)
print(Categorias_Amenaza)

#Se hace el estudio según la categoría de amenaza  
for i in range (0,len(Categorias_Amenaza)):#len(Categorias_Amenaza)
    Amenaza=Categorias_Amenaza.loc[i,'Amenaza']
    print('\n')
    print(f'Se hará el análisis para amenaza {Amenaza}')
    print('\n')
    DF_Inv.set_index('AMENAZA',inplace=True)
    DF_Inv_Amenaza=DF_Inv.loc[Amenaza]
    DF_Inv_Amenaza.reset_index(level=0, inplace=True)
    DF_Inv.reset_index(level=0, inplace=True)
    Tipo_Evento=DF_Inv_Amenaza['TIPO_MOV1'].unique()
    Tipo_Evento=pd.DataFrame(Tipo_Evento,columns=['Tipo_Mov'],dtype=object)
    
    #Se hace el estudio según el tipo de movimiento en masa
    for j in range (0,len(Tipo_Evento)): #len(Tipo_Evento)
        Tipo=Tipo_Evento.loc[j,'Tipo_Mov']
        print('\n') #Se imprime un renglón en blanco
        print(f'Se hará el análisis para el tipo {Tipo}') #Se imprime el tipo de movimiento en el que va el análisis
        print('\n')
        DF_Excedencia.loc[j,'Amenaza']=Amenaza
        DF_Excedencia.loc[j,'Tipo_Mov']=Tipo
        if len(DF_Inv_Amenaza[DF_Inv_Amenaza['TIPO_MOV1'] == Tipo])<2:
            print(f'No hay suficientes datos para completar el análisis de amenaza {Amenaza} y tipo {Tipo}')
            DF_Excedencia.loc[j,'Excedencia']=np.NaN
            DF_Excedencia.loc[j,'P[R>Rt]']=np.NaN
            DF_Excedencia.loc[j,'N']=np.NaN
            DF_Excedencia.loc[j,'Fr']=np.NaN
            DF_Excedencia.loc[j,'Ptem']=np.NaN
            continue
        #Se seleccionan del dataframe únicamente los movimientos en masa correspondientes al tipo
        DF_Inv_Amenaza.set_index('TIPO_MOV1',inplace=True)
        DF_Inv_Amenaza_Tipo=DF_Inv_Amenaza.loc[Tipo]
        DF_Inv_Amenaza_Tipo.reset_index(level=0, inplace=True)
        DF_Inv_Amenaza.reset_index(level=0, inplace=True)
        
        # 2- Extrae los valores únicos de fechas de reporte de movimientos en masa
        DF_Fechas_Unicas_MM = pd.DataFrame(columns=['Fecha'],dtype=str)
        F = DF_Inv_Amenaza_Tipo['FECHA_MOV'].unique()
        DF_Fechas_Unicas_MM['Fecha'] = F
        #DF_Fechas_Unicas_MM.to_csv(f'04_Fechas_Unicas_MM {Amenaza} {Tipo}.csv',header=True,index=False)
        
        #Búsqueda de la fechas de MM en el registro histórico de precipitación
        # Se crea un dataframe 'DF_DatosLluviaEventos' para almacenar los datos de la lluvia en el
        # día del evento y su respectiva lluvia acumulada. (recordar que la lluvia acumulada es en
        #función de la variable 'P_ant' definida al inicio del script)

        DF_DatosLluviaEventos=pd.DataFrame(columns=['date','Pant','P24'],dtype=float)   
        for i in range (0, len(DF_Fechas_Unicas_MM)):
            Dia=DF_Fechas_Unicas_MM.loc[i,'Fecha']
            indice=DF_Precipitacion_diaria[DF_Precipitacion_diaria['date'] == Dia].index
            DF_DatosLluviaEventos.loc[i,'P24'] = DF_Precipitacion_diaria.loc[indice[0], 'P']
            DF_DatosLluviaEventos.loc[i,'date'] = DF_Precipitacion_diaria.loc[indice[0], 'date']
            DF_DatosLluviaEventos.loc[i,'Pant'] = DF_Precipitacion_diaria.loc[indice[0], 'Pant']
        
        if len(DF_DatosLluviaEventos)<2:
            print(f'No hay suficientes datos para completar el análisis de amenaza {Amenaza} y tipo {Tipo}')
            DF_Excedencia.loc[j,'Excedencia']=np.NaN
            DF_Excedencia.loc[j,'P[R>Rt]']=np.NaN
            DF_Excedencia.loc[j,'N']=np.NaN
            DF_Excedencia.loc[j,'Fr']=np.NaN
            DF_Excedencia.loc[j,'Ptem']=np.NaN
            continue
        
        # Se muestran los eventos de Movimientos en Masa (MM) con su precipitación del día en análisis
        # y la precipitación acumulada para el número de días antecedentes que se este analizando.
        # Esta informacion se lista en un dataframe 'DF_DatosLluviaEventos' y se tomaran como par de datos (x,y) 
        # para ser graficados. Adicionalmente se exporta un archivo csv que contiene la información
        # anteriormente descrita
        
        #DF_DatosLluviaEventos.reset_index().to_csv(f'05_Datos_P24vsPant {Amenaza} {Tipo}.csv',header=True,index=True)
        
        DF_DatosLluviaEventos['date'] =pd.to_datetime(DF_DatosLluviaEventos.date,dayfirst=True)
        DF_DatosLluviaEventos=DF_DatosLluviaEventos.sort_values(by='date')
        DF_DatosLluviaEventos.reset_index(level=0, inplace=True)
        DF_DatosLluviaEventos.drop(['index'],axis='columns',inplace=True)
        inicio=DF_DatosLluviaEventos.loc[0]['date']
        inicio1=str(inicio.strftime("%d/%m/%Y"))
        print(f'La fecha inicial es {inicio1}')
        fin=DF_DatosLluviaEventos.loc[len(DF_DatosLluviaEventos)-1]['date']
        fin1=str(fin.strftime("%d/%m/%Y"))
        print(f'La fecha final es {fin1}')
        
        años=(fin.year-inicio.year)
        print(f'El número de años en el que se tienen los datos es {años}')

        # Se inicia el proceso de graficar el data frame DF_DatosLluviaEventos

        # Se extraen los datos de las coordenadas x,y en un data frame individual
        x = DF_DatosLluviaEventos['Pant']
        y = DF_DatosLluviaEventos['P24']

        # Se crea el modelo de regresión lineal
        modelo = linear_model.LinearRegression()
 
        # Entreno el modelo con los datos (X,Y)
        modelo.fit(x, y)

        # Ahora puedo obtener la pendiente de la recta y su intercepto con el eje y
        print (u'Pendiente "m": ', modelo.coef_)
        print (u'Intercepto "b": ',modelo.intercept_)

        # Podemos predecir usando el modelo
        y_pred = modelo.predict(x)
 
        # Se calcula e imprime el error cuadrático medio y el estadístico r^2
        print (u'Error cuadrático medio: %.2f' % mean_squared_error(y, y_pred))
        print (u'Estadístico R_2: %.2f' % r2_score(y, y_pred))

        # Se imprime la ecuación de la recta
        print('La ecuación del modelo es igual a:')
        print('PT =',modelo.coef_, 'P15  +', modelo.intercept_)


        # Grafica de los datos correspondientes, junto con la recta de ajuste (rojo) 
        fig, ax = plt.subplots(1, 1, figsize=(12, 7))
        ax.plot(x,y,color='g',marker='o',linestyle=' ',label='Eventos de MM')
        ax.set_xlabel("P_antecedente [mm]")
        ax.set_ylabel("P24h [mm]")
        ax.set_title(f'Lluvia del dia vs Lluvia acumulada {Amenaza} {Tipo}', pad = 15, fontdict={'fontsize':14, 'color': '#4873ab'})
        plt.scatter(x, y)
        plt.plot(x, y_pred, color='red')

        # Calculo y creacion de un dataframe con la precipitación umbral para cada dia del registro histórico
        #PT= precipitacion umbral
        #PT=m*(Pant)+b
        PT=DF_Precipitacion_diaria['Pant']*modelo.coef_[0]+modelo.intercept_[0]

        DF_Precipitacion_diaria['PT']=PT
        DF_Precipitacion_diaria['date'] =pd.to_datetime(DF_Precipitacion_diaria.date,dayfirst=True)
        DF_Precipitacion_diaria['date']= DF_Precipitacion_diaria['date'].dt.strftime("%d/%m/%Y")
        #DF_Precipitacion_diaria.reset_index().to_csv(f'07_P_Umbral {Amenaza} {Tipo}.csv',header=True,index=False)
        
        # Calculo del número de excedencias del umbral de lluvia en todo el registro de precipitación     
        DF_Precipitacion_diaria["EX"]=0
        Valor=1
        DF_Precipitacion_diaria.loc[DF_Precipitacion_diaria['P']>DF_Precipitacion_diaria['PT'],["EX"]]=Valor
        
        DF_Precipitacion_diaria.set_index('date',inplace=True)
        DF_Precipitacion_diaria=DF_Precipitacion_diaria.loc[inicio1:fin1]
        DF_Precipitacion_diaria.reset_index(level=0, inplace=True)
        
        Ex=DF_Precipitacion_diaria["EX"].sum()
        DF_Excedencia.loc[j,'Excedencia']=Ex
        print (f'El umbral de lluvia es excedido {Ex} veces en todo el registro de precipitación para amenaza {Amenaza} y tipo {Tipo}')
        
        I=años/Ex
        t=1
        P=1-math.exp(-t/I)
        print(f'La probabilidad P[R>Rt]= {P} ')
        DF_Excedencia.loc[j,'P[R>Rt]']=P
        
        DF_Precipitacion_diaria.set_index('EX',inplace=True)
        DF_Precipitacion_diaria=DF_Precipitacion_diaria.loc[Valor]
        DF_Precipitacion_diaria.reset_index(level=0, inplace=True)
        DF_Precipitacion_diaria['date']=DF_Precipitacion_diaria['date'].astype(str)
        print(DF_Precipitacion_diaria)
        
        DF_Inv['FECHA_MOV'] =pd.to_datetime(DF_Inv['FECHA_MOV'],dayfirst=True)
        DF_Inv['FECHA_MOV']= DF_Inv['FECHA_MOV'].dt.strftime("%d/%m/%Y")  
        DF_Inv['FECHA_MOV']=DF_Inv['FECHA_MOV'].astype(str)
        
        DF_Apoyo=pd.DataFrame(columns=['date','N'])
        
        for n in range (0,len(DF_Precipitacion_diaria)):
            date=DF_Precipitacion_diaria.loc[n,'date']
            if len(DF_Inv[DF_Inv['FECHA_MOV'] == date])<1:
                continue
            DF_Apoyo.loc[n,'date']=date
            DF_Apoyo.loc[n,'N']=len(DF_Inv[DF_Inv['FECHA_MOV'] == date])
            
        N=DF_Apoyo['N'].sum()
        Fr=N/Ex
        DF_Excedencia.loc[j,'N']=N
        DF_Excedencia.loc[j,'Fr']=Fr
        DF_Excedencia.loc[j,'Ptem']=P*Fr

print('\n')
print(DF_Excedencia)


        
         
     
    




            
        



