# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 06:32:17 2020

@author: HOGAR
"""

import math
import pandas as pd
import numpy as np
from sklearn import linear_model
from sklearn.metrics import mean_squared_error, r2_score
import matplotlib.pyplot as plt

DF_Precipitacion_diaria=pd.read_csv('01_Precipitacion_diaria.csv')
DF_Precipitacion_diaria['date']=DF_Precipitacion_diaria['date'].astype(str)

DF_Inv=pd.read_csv('02_Inventario_MM.csv')
DF_Inv=DF_Inv[['FECHA_MOV','TIPO_MOV1','AMENAZA']]
DF_Inv['FECHA_MOV']=DF_Inv['FECHA_MOV'].astype(str)

F = DF_Inv['FECHA_MOV'].unique()
Fecha = F[1]
DF_Excedencia=pd.DataFrame(columns=['Amenaza','Tipo_Mov','Excedencia','P[R>Rt]','N','Fr','Ptem'])
indice=DF_Precipitacion_diaria[DF_Precipitacion_diaria['date'] == Fecha].index
print(indice)
print('\n')
print(indice[0])
print('\n')
X=DF_Precipitacion_diaria.loc[indice[0], 'P']
print(X)
print('\n')
#DF_Excedencia.loc[0,'Amenaza'] = DF_Precipitacion_diaria.loc[DF_Precipitacion_diaria['date'] == Fecha, 'P']
print('\n')
print(DF_Excedencia)




