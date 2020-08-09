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

import matplotlib.pyplot as plt
from numpy import linalg
from time import time
import pandas as pd
import numpy as np
import math

start_time = time()

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
data_path = data_path.replace("\\", "/")

# Defina el número de días de lluvia antecedente que desea acumular
d_ant = QInputDialog.getInt(None, 'Número de días antecedentes', 'Introduce el número de días para la lluvia antecedentes: ')
d_ant = d_ant[0]

#Desea ajustar las fechas de movimientos en masa (Si o No)
Opciones = ["Si", "No"]
Ajuste, ok = QInputDialog.getItem(None, "Seleccione si desea hacer un ajuste en las fechas del inventario", "Opciones", Opciones, 0, False)

if Ajuste == "Si":
    # Defina el número de días en el que se puede ajustar las fechas de los movimientos
    umbral_dias = QInputDialog.getInt(None, 'Umbral de días antecedentes', 'Introduce el número de días umbral para el ajuste: ')
    umbral_dias = umbral_dias[0]

    # Defina la precipitación umbral para el ajuste de las fechas de los movimientos
    umbral_lluvia = QInputDialog.getInt(None, 'Umbral de lluvia', 'Introduzca la lluvia umbral con la que se hará el ajuste: ')
    umbral_lluvia = umbral_lluvia[0]

#Defina con que norma desea hacer la regresión (L1 o L2)
Normas = ["L1", "L2"]
Norma, ok = QInputDialog.getItem(None, "Seleccione la norma con la que se hará la regresión", "Opciones", Normas, 0, False)


# Ingresar registro de precipitación diaria para la estación en análisis
DF_Precipitacion_diaria = pd.read_csv(data_path + '/01_Precipitacion_diaria.csv')
DF_Precipitacion_diaria['date'] = pd.to_datetime(DF_Precipitacion_diaria.date)
begin = min(DF_Precipitacion_diaria['date'])
end = max(DF_Precipitacion_diaria['date'])

# Se lee el inventario de movimientos en masa con fecha y susceptibilidad detonados por lluvias
DF_Inv = pd.read_csv(data_path + '/Pre_Proceso/DF_Mov_Masa_Lluvias.csv')
DF_Inv = DF_Inv.dropna(axis=0, subset=['FECHA_MOV']) 
DF_Inv = DF_Inv.drop(['level_0'], axis=1) #Borrar
DF_Inv.rename(columns={'Poligono_1':'Poligono'}, inplace=True) #Borrar

DF_Inv['FECHA_MOV'] = pd.to_datetime(DF_Inv.FECHA_MOV)
DF_Inv = DF_Inv.sort_values(by ='FECHA_MOV')
DF_Inv.reset_index(level=0, inplace=True)
DF_Inv.drop(['index'], axis=1)

DF_Inv.set_index('FECHA_MOV',inplace=True)
DF_Inv = DF_Inv.truncate(before = begin, after = end)
DF_Inv.reset_index(level=0, inplace=True)
DF_Inv.drop(['index'], axis=1)

# Se lee los poligonos correspondientes a las estaciones
DF_Poligonos = pd.read_csv(data_path + '/Pre_Proceso/DF_Raster_Poligonos_Voronoi.csv')
DF_Poligonos['Codigo'] = DF_Poligonos['Codigo'].astype(int)
DF_Poligonos['Codigo'] = DF_Poligonos['Codigo'].astype(str)
DF_Poligonos.set_index('ID', inplace = True)

#Se crea el dataframe con el que se hace el análisis
DF_Excedencia = pd.DataFrame(columns=['Poli_Thiessen', 'Estacion', 'Amenaza', 'Tipo_Mov', 'Excedencia', 'P[R>Rt]', 'N', 'Fr', 'Ptem'])
DF_Final = pd.DataFrame()

#Se extraen los valores únicos de poligonos correspondientes a las estaciones
Poligonos = DF_Inv['Poli_Voron'].unique()
#Poligonos = [5]

for poligono in Poligonos:
    if len(DF_Inv[DF_Inv['Poli_Voron'] == poligono]) < 2:
        print(f'No hay suficientes datos para completar el análisis del poligono {poligono}')
        continue
    DF_Inv.set_index('Poli_Voron', inplace=True)
    DF_Inv_Poligono = DF_Inv.loc[poligono]
    DF_Inv_Poligono.reset_index(level=0, inplace=True)
    DF_Inv.reset_index(level=0, inplace=True)
    
    #Se define la estación correspondiente al poligono
    Estacion = DF_Poligonos.loc[poligono]['Codigo']
    print(poligono, Estacion)
    DF_Estacion = DF_Precipitacion_diaria[['date', Estacion]]
    Pant = DF_Estacion[Estacion].rolling(min_periods = d_ant+1, window = d_ant+1).sum()-DF_Estacion[Estacion]
    DF_Estacion['Pant'] = Pant
    DF_Estacion['date'] = pd.to_datetime(DF_Estacion.date)
    DF_Estacion['date'] = DF_Estacion['date'].dt.strftime('%d/%m/%Y')
    DF_Estacion['date'] = DF_Estacion['date'].astype(str)
    DF_Estacion['P24'] = DF_Estacion[Estacion]

    #Se extraen los tipos de movimientos en masa
    Tipo_Evento = DF_Inv_Poligono['TIPO_MOV1'].unique()
    Tipo_Evento = pd.DataFrame(Tipo_Evento,columns=['Tipo_Mov'],dtype=object)
    
    #Se hace el estudio según el tipo de evento
    for id_evento in range (0,len(Tipo_Evento)): # len(Categorias_Amenaza)
        Tipo = Tipo_Evento.loc[id_evento,'Tipo_Mov']
        
        if len(DF_Inv_Poligono[DF_Inv_Poligono['TIPO_MOV1'] == Tipo]) < 2:
            print(f'No hay suficientes datos para completar el análisis del tipo {Tipo}')
            continue
        
        print('\n')
        print(f'Se hará el análisis para el tipo {Tipo}')
        print('\n')

        DF_Inv_Poligono.set_index('TIPO_MOV1',inplace=True)
        DF_Inv_Tipo = DF_Inv_Poligono.loc[Tipo]
        DF_Inv_Tipo.reset_index(level=0, inplace=True)
        DF_Inv_Poligono.reset_index(level=0, inplace=True)
        
        if Tipo == "Deslizamiento":
            Campo_Amenaza = "Susc_Desli"
        elif Tipo == "Caida":
            Campo_Amenaza = "Susc_Caida"
        elif Tipo == "Flujo":
            Campo_Amenaza = "Susc_Flujo"
        else:
            print(f"No se tiene un análisis para el tipo de movimiento en masa {Tipo}")
            continue
        
        if (Campo_Amenaza in DF_Inv_Tipo.columns) is False:
            continue
        
        Categorias_Amenaza = DF_Inv_Tipo[Campo_Amenaza].unique()
        Categorias_Amenaza = pd.DataFrame(Categorias_Amenaza,columns=['Amenaza'],dtype=object)
        
        #Se hace el estudio según la categoría de amenaza
        for id_amenaza in range (0,len(Categorias_Amenaza)): 
            #Amenaza = 1
            Amenaza = Categorias_Amenaza.loc[id_amenaza,'Amenaza']
            
            if Amenaza ==2:
                Cat_amenaza = 'Alta'
            elif Amenaza ==1:
                Cat_amenaza = 'Media'
            else:
                Cat_amenaza = 'Baja'
            
            print('\n')  # Se imprime un renglón en blanco
            print(f'Se hará el análisis para amenaza {Cat_amenaza}') #Se imprime la amenaza en el que va el análisis
            print('\n')
            DF_Excedencia.loc[id_amenaza,'Poli_Thiessen'] = poligono
            DF_Excedencia.loc[id_amenaza,'Estacion'] = Estacion
            DF_Excedencia.loc[id_amenaza,'Amenaza'] = Cat_amenaza
            DF_Excedencia.loc[id_amenaza,'Tipo_Mov'] = Tipo
            
            if len(DF_Inv_Tipo[DF_Inv_Tipo[Campo_Amenaza] == Amenaza]) < 2:
                print(f'No hay suficientes datos para completar el análisis de amenaza {Cat_amenaza} y tipo {Tipo}')
                DF_Excedencia.loc[id_amenaza,'Excedencia'] = np.NaN
                DF_Excedencia.loc[id_amenaza,'P[R>Rt]'] = np.NaN
                DF_Excedencia.loc[id_amenaza,'N'] = np.NaN
                DF_Excedencia.loc[id_amenaza,'Fr'] = np.NaN
                DF_Excedencia.loc[id_amenaza,'Ptem'] = np.NaN
                continue
            
            #Se seleccionan del dataframe únicamente los movimientos en masa correspondientes al tipo
            DF_Inv_Tipo.set_index(Campo_Amenaza, inplace = True)
            DF_Inv_Amenaza_Tipo = DF_Inv_Tipo.loc[Amenaza]
            DF_Inv_Amenaza_Tipo['FECHA_MOV'] = DF_Inv_Amenaza_Tipo['FECHA_MOV'].dt.strftime('%d/%m/%Y')
            DF_Inv_Amenaza_Tipo.reset_index(level=0, inplace = True)
            DF_Inv_Tipo.reset_index(level=0, inplace=True)
            
            # 2- Extrae los valores únicos de fechas de reporte de movimientos en masa
            DF_Fechas_Unicas_MM = pd.DataFrame(columns=['Fecha'],dtype=str)
            F = DF_Inv_Amenaza_Tipo['FECHA_MOV'].unique()
            DF_Fechas_Unicas_MM['Fecha'] = F
            DF_Fechas_Unicas_MM['Fecha'] = pd.to_datetime(DF_Fechas_Unicas_MM.Fecha)
            DF_Fechas_Unicas_MM['Fecha'] = DF_Fechas_Unicas_MM['Fecha'].dt.strftime('%d/%m/%Y')
            DF_Fechas_Unicas_MM['Fecha'] = DF_Fechas_Unicas_MM['Fecha'].astype(str)
                        
            DF_DatosLluviaEventos = pd.DataFrame(columns=['Fecha_Analisis', 'Pant', 'P24'], dtype=float)   
            for h in range (0, len(DF_Fechas_Unicas_MM)):
                Dia = DF_Fechas_Unicas_MM.loc[h, 'Fecha']
                indice = DF_Estacion[DF_Estacion['date'] == Dia].index
                P24 = DF_Estacion.loc[indice[0], Estacion]
                
                if Ajuste == "No":
                    DF_DatosLluviaEventos.loc[h, 'P24'] = P24
                    DF_DatosLluviaEventos.loc[h, 'Fecha_Analisis'] = DF_Estacion.loc[indice[0], 'date']
                    DF_DatosLluviaEventos.loc[h, 'Pant'] = DF_Estacion.loc[indice[0], 'Pant']
                    
                else:
                    if P24 <= umbral_lluvia:
                        for z in range(0, umbral_dias):
                            P24 = DF_Estacion.loc[indice[0] - z, Estacion]
                            if P24 > umbral_lluvia:
                                DF_DatosLluviaEventos.loc[h, 'P24'] = DF_Estacion.loc[indice[0] - z, Estacion]
                                DF_DatosLluviaEventos.loc[h, 'Pant'] = DF_Estacion.loc[indice[0] - z, 'Pant']
                                Fecha_Inicial = DF_Estacion.loc[indice[0], 'date']
                                Fecha_Analisis = DF_Estacion.loc[indice[0] - z, 'date']
                                DF_DatosLluviaEventos.loc[h, 'Fecha_Analisis'] = Fecha_Analisis
                                DF_DatosLluviaEventos.loc[h, 'Fecha_Inventario'] = Fecha_Inicial
                                #Se reemplaza la fecha en el inentario de movimientos para el posterior análisis
                                DF_Inv_Amenaza_Tipo['FECHA_MOV'] = DF_Inv_Amenaza_Tipo['FECHA_MOV'].str.replace(Fecha_Inicial, Fecha_Analisis)
                            else:
                                continue 
                    else:
                        DF_DatosLluviaEventos.loc[h, 'P24'] = P24
                        DF_DatosLluviaEventos.loc[h, 'Fecha_Analisis'] = DF_Estacion.loc[indice[0], 'date']
                        DF_DatosLluviaEventos.loc[h, 'Pant'] = DF_Estacion.loc[indice[0], 'Pant']
                    
            DF_DatosLluviaEventos.reset_index().to_csv(data_path + f'/Amenaza/Lluvia_{poligono}_{Cat_amenaza}_{Tipo}.csv',header=True,index=False)
            
            if len(DF_DatosLluviaEventos) < 2:
                print(f'No hay suficientes datos para completar el análisis de amenaza {Cat_amenaza} y tipo {Tipo}')
                DF_Excedencia.loc[id_amenaza, 'Excedencia'] = np.NaN
                DF_Excedencia.loc[id_amenaza, 'P[R>Rt]'] = np.NaN
                DF_Excedencia.loc[id_amenaza, 'N'] = np.NaN
                DF_Excedencia.loc[id_amenaza, 'Fr'] = np.NaN
                DF_Excedencia.loc[id_amenaza, 'Ptem'] = np.NaN
                continue
            
            print(DF_DatosLluviaEventos)
            print('\n')
            
            DF_DatosLluviaEventos['Fecha_Analisis'] = pd.to_datetime(DF_DatosLluviaEventos['Fecha_Analisis'], dayfirst=True)
            DF_DatosLluviaEventos = DF_DatosLluviaEventos.sort_values(by ='Fecha_Analisis')
            DF_DatosLluviaEventos.reset_index(level = 0, inplace = True)
            DF_DatosLluviaEventos.drop(['index'],axis = 'columns', inplace = True)
            inicio = DF_DatosLluviaEventos.loc[0]['Fecha_Analisis']
            inicio1 = str(inicio.strftime("%d/%m/%Y"))
            print(f'La fecha inicial es {inicio1}')
            fin = DF_DatosLluviaEventos.loc[len(DF_DatosLluviaEventos)-1]['Fecha_Analisis']
            fin1 = str(fin.strftime("%d/%m/%Y"))
            print(f'La fecha final es {fin1}')
            
            años = (fin.year-inicio.year)
            print(f'El número de años en el que se tienen los datos es {años}')
            
            # Se inicia el proceso de graficar el data frame DF_DatosLluviaEventos
            
            # Se extraen los datos de las coordenadas x,y en un data frame individual
            x = DF_DatosLluviaEventos['Pant']
            x = list(x)

            y = DF_DatosLluviaEventos['P24']
            y = list(y)
            
            #Se resuleve el modelo líneal por medio de vectores y matrices
            numdat = len(y)

            G = np.ones((numdat, 2)) #Numdata? 2?
            G[:,0] = x
            #print('G=\n', G)
            ml2 = linalg.inv(G.T@G)@G.T@y
            
            dmod = G@ml2
            rl2 = y - dmod
            error = 1.1
            gml0 = dmod
            while error>0.1:
                R = np.diag(1/np.abs(rl2))
                ml1 = linalg.inv(G.T@R@G)@G.T@R@y
                dl1 = G@ml1
                error = np.abs((dl1[0]-gml0[0])/(1+dl1[0]))
                gml0 = dl1
            
            dl2 = G@ml2
            dl1 = G@ml1
            
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
            
            # Grafica de la dispersión de los datos y sus rectas correspondientes
            fig, ax = plt.subplots(1, 1, figsize=(12, 7))
            ax.plot(x, y, 'o')
            ax.plot(x, dl1, 'g--', label = f'L1: PT = {round(ml1[0],2)} * Pant + {round(ml1[1],2)}') 
            ax.plot(x, dl2, 'r--', label = f'L2: PT = {round(ml2[0],2)} * Pant + {round(ml2[1],2)}')   
            ax.set_xlabel("P_antecedente [mm]")
            ax.set_ylabel("P24h [mm]")
            ax.legend()
            ax.set_title(f'Lluvia del dia vs Lluvia acumulada - {poligono}: tipo {Tipo}, amenaza {Cat_amenaza}',
                         pad = 15, fontdict = {'fontsize': 14, 'color': '#4873ab'})
            plt.grid(True)
            plt.show()
            
            #Se guarda la gráfica resultante
            fig.savefig(data_path + f'/Amenaza/{poligono}_{Tipo}_{Cat_amenaza}.jpg')
            
            #Se sobreescriben los datos de la gráfica en otro dataframe
            DF_Estacion_Analisis = pd.DataFrame()
            DF_Estacion_Analisis['date'] = DF_Estacion['date']
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
             
            DF_Estacion_Analisis.set_index('date', inplace=True)
            DF_Estacion_Analisis = DF_Estacion_Analisis.loc[inicio1 : fin1]
            DF_Estacion_Analisis.reset_index(level = 0, inplace=True)
            
            Ex = DF_Estacion_Analisis["EX"].sum()
            DF_Excedencia.loc[id_amenaza,'Excedencia'] = Ex
            print (f'El umbral de lluvia es excedido {Ex} veces en todo el registro de precipitación para amenaza {Cat_amenaza} y tipo {Tipo}')
            
            I = años/Ex
            t = 1
            P = 1 - math.exp(-t/I)
            print(f'La probabilidad P[R>Rt] = {P} ')
            DF_Excedencia.loc[id_amenaza, 'P[R>Rt]'] = P
            
            if len(DF_Estacion_Analisis[DF_Estacion_Analisis['EX'] == Valor]) < 2:
                continue
            DF_Estacion_Analisis.set_index('EX', inplace=True)
            DF_Estacion_Analisis = DF_Estacion_Analisis.loc[Valor]
            DF_Estacion_Analisis.reset_index(level=0, inplace=True)
            DF_Estacion_Analisis['date'] = pd.to_datetime(DF_Estacion_Analisis['date'], dayfirst=True)
            DF_Estacion_Analisis['date'] = DF_Estacion_Analisis['date'].dt.strftime("%d/%m/%Y")  
            
            DF_Inv_Amenaza_Tipo['FECHA_MOV'] = pd.to_datetime(DF_Inv_Amenaza_Tipo['FECHA_MOV'], dayfirst=True)
            DF_Inv_Amenaza_Tipo['FECHA_MOV'] = DF_Inv_Amenaza_Tipo['FECHA_MOV'].dt.strftime("%d/%m/%Y")  
            
            DF_Apoyo = pd.DataFrame(columns = ['date', 'N'])
            
            for n in range (0,len(DF_Estacion_Analisis)):
                date = DF_Estacion_Analisis.loc[n, 'date']
                if len(DF_Inv_Amenaza_Tipo[DF_Inv_Amenaza_Tipo['FECHA_MOV'] == date]) < 1:
                    continue
                DF_Apoyo.loc[n, 'date'] = date
                DF_Apoyo.loc[n, 'N'] = len(DF_Inv_Amenaza_Tipo[DF_Inv_Amenaza_Tipo['FECHA_MOV'] == date])
                
            N = DF_Apoyo['N'].sum()
            Fr = N/Ex
            DF_Excedencia.loc[id_amenaza, 'N'] = N
            DF_Excedencia.loc[id_amenaza, 'Fr'] = Fr
            DF_Excedencia.loc[id_amenaza, 'Ptem'] = P*Fr
        
        DF_Final = DF_Final.append(DF_Excedencia)

DF_Final = DF_Final.sort_values(by = 'Poli_Thiessen')
DF_Final.reset_index(level=0, inplace=True)
DF_Final = DF_Final.drop(['index'], axis=1)
print('\n')
print(DF_Final)
DF_Final.reset_index().to_csv(data_path + '/Resultados/DF_Excedencia.csv',header=True,index=False)

elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)

