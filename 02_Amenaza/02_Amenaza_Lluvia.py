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

#Se determina el momento en que inicia la ejcución del programa
start_time = time()

# Ruta general de la ubicación de los archivos
data_path, ok = QInputDialog.getText(None, 'RUTA', 'Introduzca la ruta general: ')
if ok == False:
    raise Exception('Cancelar')
data_path = data_path.replace("\\", "/")

# Se listan los archivos en la ruta general
list = listdir(data_path)

# Se determinan los archivos con extensión .csv
csv = []
for i in list:
    if i[-4:] == '.csv':
        csv.append(i)

# Ubicación de la precipitación
Precipitacion, ok = QInputDialog.getItem(None, "Precipitacion por estacion", "Seleccione el archivo de la precipitacion por estacion",
                                      csv, 0, False)
if ok == False:
    raise Exception('Cancelar')
Ruta_Precipitacion = data_path + '/' + Precipitacion

# Se define el número de días de lluvia antecedente que desea acumular
d_ant, ok = QInputDialog.getInt(None, 'Número de días antecedentes',
                            'Introduce el número de días para la lluvia antecedentes: ')
if ok == False:
    raise Exception('Cancelar')

# Desea ajustar las fechas de movimientos en masa (Si o No)
Opciones = ["Si", "No"]
Ajuste, ok = QInputDialog.getItem(None, "Ajuste en las fechas del inventario",
                                  "Seleccione si desea hacer un ajuste en las fechas del inventario", Opciones, 0, False)
if ok == False:
    raise Exception('Cancelar')

if Ajuste == "Si":
    # Se defina el número de días en el que se puede ajustar las fechas de los movimientos
    umbral_dias, ok = QInputDialog.getInt(None, 'Umbral de días antecedentes',
                                      'Introduzca el número de días umbral para el ajuste: ')
    if ok == False:
        raise Exception('Cancelar')

    # Se defina la precipitación umbral para el ajuste de las fechas de los movimientos
    umbral_lluvia, ok= QInputDialog.getInt(None, 'Umbral de lluvia',
                                        'Introduzca la lluvia umbral con la que se hará el ajuste: ')
    if ok == False:
        raise Exception('Cancelar')

# Se define con que norma desea hacer la regresión (L1 o L2)
Normas = ["L1", "L2"]
Norma, ok = QInputDialog.getItem(None, "Norma de la regresión",
                                 "Seleccione la norma con la que se hará la regresión", Normas, 0, False)
if ok == False:
    raise Exception('Cancelar')
    
# Se define cómo se quiere hacer la discritización
Discri = ["Amenaza", "Amenaza - Tipo de movimiento"]
Discritizacion, ok = QInputDialog.getItem(None, "Discretización",
                                          "Seleccione la cómo desea hacer la discretización de los MM", Discri, 0, False)
if ok == False:
    raise Exception('Cancelar')

# Ingresar registro de precipitación diaria para la estación en análisis
DF_Precipitacion_diaria = pd.read_csv(Ruta_Precipitacion)
DF_Precipitacion_diaria['date'] = pd.to_datetime(DF_Precipitacion_diaria.date)
# Se determinan la fecha inicial y final con la que se cuenta precipitación
begin = min(DF_Precipitacion_diaria['date'])
end = max(DF_Precipitacion_diaria['date'])

# Se lee el inventario de movimientos en masa con fecha y susceptibilidad detonados por lluvias
DF_Inv = pd.read_csv(data_path + '/Amenaza/DF_Mov_Masa_Lluvias.csv')
# Se convierte en formato de fecha la fecha 
DF_Inv['FECHA_MOV'] = pd.to_datetime(DF_Inv.FECHA_MOV)
DF_Inv = DF_Inv.drop(['level_0'], axis=1) #Borrar
# Se ordenan los MM según la fecha
DF_Inv = DF_Inv.sort_values(by ='FECHA_MOV')
DF_Inv.reset_index(level=0, inplace=True)
DF_Inv = DF_Inv.drop(['index'], axis=1)

# Se truncan las fechas de MM según las fechas de precipitación 
DF_Inv.set_index('FECHA_MOV',inplace=True)
DF_Inv = DF_Inv.truncate(before = begin, after = end)
DF_Inv.reset_index(level=0, inplace=True)
DF_Inv = DF_Inv.drop(['level_0'], axis=1)

# Se lee los poligonos correspondientes a las estaciones
DF_Poligonos = pd.read_csv(data_path + '/Pre_Proceso/DF_Raster_Poligonos_Voronoi.csv')
DF_Poligonos['Codigo'] = DF_Poligonos['Codigo'].astype(int)
DF_Poligonos['Codigo'] = DF_Poligonos['Codigo'].astype(str)
DF_Poligonos.set_index('ID', inplace = True)

#Se crea el dataframe con el que se hace el análisis
DF_Excedencia = pd.DataFrame(columns=['Poli_Thiessen', 'Estacion',
                                      'Amenaza', 'Tipo_Mov', 'Excedencia',
                                      'P[R>Rt]', 'N', 'Fr', 'Ptem'])
DF_Final = pd.DataFrame()

#Se extraen los valores únicos de poligonos correspondientes a las estaciones
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
    
    #Se define la estación correspondiente al poligono
    Estacion = DF_Poligonos.loc[poligono]['Codigo']
    print(poligono, Estacion)
    # Se extrae solo las precipitaciones de la estación de interes
    DF_Estacion = DF_Precipitacion_diaria[['date', Estacion]] 
    # Se cálcula la precipitación antecedente según los días antecedentes
    Pant = DF_Estacion[Estacion].rolling(min_periods = d_ant+1, window = d_ant+1).sum()-DF_Estacion[Estacion]
    DF_Estacion['Pant'] = Pant
    # Se pasa a formato de fecha el campo de la fecha
    DF_Estacion['date'] = pd.to_datetime(DF_Estacion.date)
    DF_Estacion['date'] = DF_Estacion['date'].dt.strftime('%d/%m/%Y')
    DF_Estacion['date'] = DF_Estacion['date'].astype(str)
    DF_Estacion['P24'] = DF_Estacion[Estacion]

    #Se extraen los tipos de movimientos en masa
    Tipo_Evento = DF_Inv_Poligono['TIPO_MOV1'].unique()
    Tipo_Evento = pd.DataFrame(Tipo_Evento,columns=['Tipo_Mov'],dtype=object)
    
    # Si la descretización es solo por amenaza la extensión del for solo será de 1
    if Discritizacion == "Amenaza": Tipo_Evento = [1]
    
    #Se hace el estudio según el tipo de evento
    for id_evento in range (0,len(Tipo_Evento)): 
        
        # Si la descretización es por tipo de movimiento y amenaza
        if Discritizacion == "Amenaza - Tipo de movimiento":
            
            # Se identifica el tipo de movimiento en cuestión
            Tipo = Tipo_Evento.loc[id_evento,'Tipo_Mov']
            
            # Si los MM correspondientes a este tipo de movimiento son menores a dos no se puede continuar con el análisis
            if len(DF_Inv_Poligono[DF_Inv_Poligono['TIPO_MOV1'] == Tipo]) < 2:
                print(f'No hay suficientes datos para completar el análisis del tipo {Tipo}')
                continue
            
            print('\n')
            print(f'Se hará el análisis para el tipo {Tipo}')
            print('\n')
            
            # Se pone como indice la columna de tipo de movimiento
            DF_Inv_Poligono.set_index('TIPO_MOV1',inplace=True)
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
            DF_Inv_Tipo = DF_Inv_Poligono.copy(deep=True)
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
            #Amenaza = 1
            Amenaza = Categorias_Amenaza.loc[id_amenaza,'Amenaza']
            
            # Según el id de la amenaza se puede determinar la categoria
            if Amenaza ==2:
                Cat_amenaza = 'Alta'
            elif Amenaza ==1:
                Cat_amenaza = 'Media'
            else:
                Cat_amenaza = 'Baja'
            
            print('\n')  # Se imprime un renglón en blanco
            print(f'Se hará el análisis para amenaza {Cat_amenaza}') #Se imprime la amenaza en el que va el análisis
            print('\n')
            
            # Se llena el dataframe con los valores hasta ahora determinados
            DF_Excedencia.loc[id_amenaza,'Poli_Thiessen'] = poligono
            DF_Excedencia.loc[id_amenaza,'Estacion'] = Estacion
            DF_Excedencia.loc[id_amenaza,'Amenaza'] = Cat_amenaza
            DF_Excedencia.loc[id_amenaza,'Tipo_Mov'] = Tipo
            
            # Si no se cuenta con mas de dos MM correspondientes a la categoría de amenaza no se puede completar el análisis
            if len(DF_Inv_Tipo[DF_Inv_Tipo[Campo_Amenaza] == Amenaza]) < 2:
                print(f'No hay suficientes datos para completar el análisis de amenaza {Cat_amenaza} y tipo {Tipo}')
                # Se llena con NaN los datos faltantes
                DF_Excedencia.loc[id_amenaza,'Excedencia'] = np.NaN
                DF_Excedencia.loc[id_amenaza,'P[R>Rt]'] = np.NaN
                DF_Excedencia.loc[id_amenaza,'N'] = np.NaN
                DF_Excedencia.loc[id_amenaza,'Fr'] = np.NaN
                DF_Excedencia.loc[id_amenaza,'Ptem'] = np.NaN
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
                indice = DF_Estacion[DF_Estacion['date'] == Dia].index
                P24 = DF_Estacion.loc[indice[0], Estacion]
                
                if Ajuste == "No":
                    # Si no se decide hacer un ajuste se llena con la precipitación del día y la antecedente correspondiente
                    DF_DatosLluviaEventos.loc[h, 'P24'] = P24
                    DF_DatosLluviaEventos.loc[h, 'Fecha_Analisis'] = DF_Estacion.loc[indice[0], 'date']
                    DF_DatosLluviaEventos.loc[h, 'Pant'] = DF_Estacion.loc[indice[0], 'Pant']
                    
                else:
                    # Si se decide hacer el ajuste se verifica cumple con el umbral
                    if P24 <= umbral_lluvia:
                        for z in range(0, umbral_dias):
                            # Si no cumple la P24 se revisan las precipitaciones de los días anteriores dentro del umbral
                            P24 = DF_Estacion.loc[indice[0] - z, Estacion]
                            if P24 > umbral_lluvia:
                                # Los datos de la P24 del día más cercano que cumpla el umbral serán con los que se llenará el dataframe para el análisis
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
                        # Si la P24 cumple el umbral se toman sus datos
                        DF_DatosLluviaEventos.loc[h, 'P24'] = P24
                        DF_DatosLluviaEventos.loc[h, 'Fecha_Analisis'] = DF_Estacion.loc[indice[0], 'date']
                        DF_DatosLluviaEventos.loc[h, 'Pant'] = DF_Estacion.loc[indice[0], 'Pant']
            
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
            # Se agregan las línea con su respectiva ecuación de recta
            ax.plot(x, dl1, 'g--', label = f'L1: PT = {round(ml1[0],2)} * Pant + {round(ml1[1],2)}') 
            ax.plot(x, dl2, 'r--', label = f'L2: PT = {round(ml2[0],2)} * Pant + {round(ml2[1],2)}')   
            # Se define los nombres de los ejes coordenados y el título
            ax.set_xlabel("P_antecedente [mm]")
            ax.set_ylabel("P24h [mm]")
            ax.set_title(f'Lluvia del dia vs Lluvia acumulada - {poligono}: tipo {Tipo}, amenaza {Cat_amenaza}',
                         pad = 15, fontdict = {'fontsize': 14, 'color': '#4873ab'})
            ax.legend()
            plt.grid(True)
            plt.show()
            
            #Se guarda la gráfica resultante en formato jpg
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
    Amenaza_Sismo.updateFields()
       
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

# Se imprime el tiempo en el que se llevo a cambo la ejecución del algoritmo
elapsed_time = time() - start_time
print("Elapsed time: %0.10f seconds." % elapsed_time)

