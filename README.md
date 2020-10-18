# Landslides_Assessment-SGC by the SGC methodology

Las programaciones se correran en el orden númerico cómo estás lo traen, empezando por el análisis de susceptibilidad y continuando con el análisis de las probabilidades de amenaza, se deben tener en cuenta las siguientes recomendaciones:

1. La programación se debe correr en Qgis, más específicamente en Pyqgis, que es la interfaz de Python en Qgis.
2. Se descargan las programaciones y se abren en Pyqgis.
3. Todos los insumos deben estar en una sola carpeta, por lo que la programación pedirá la ruta general lo cuál hace referencia a copiar y pegar la ruta de la carpeta en la caja flotante.
4.Para el análisis de los movimientos en masa, se puede tener geometría de puntos o polígonos, dónde los tipos de movimientos deben estar agrupados, es decir, todos los movimientos en masa tipo deslizamientos deben estar agrupados en un solo grupo general de deslizamientos. Además, si se tiene movimientos en masa en geometría de puntos Y polígonos es necesario que los atributos de ambas capas coincidad, al igual que como están identificados los tipos de movimientos en masa.
5. Para el análisis de los factores condicionantes discretos, los archivos vectoriales deberán tener un atributo característico el cuál se recomienda sea el acrónimo de la característica o código, el cuál no tenga ñ o tíldes que Qgis no identifica.
6. La programación creará las carpetas internas de Pre_Proceso, Resultados y Amenaza en dónde se guardaran los archivos según corresponda.
7. Si la programación ya se ha corrido con anterioridad, se recomienda borrar los archivos que fueron creados, en especial los archivos shape ya que el programa los identifica como en uso y no permite hacerles cambios.
8. Para el análisis LSI la programación mostrará la gráfica e informará si es aceptada o no la hipotesis.
9. Para el análisis de caídas, si desde un principio se trabajó con movimientos en masa con geometría de polígono, ya se extrayeron los polígonos de deposito, en está fase se pueden introducir más polígonos correspondientes a depositos, o si se trabajo con movimientos en masa de geometría punto, entonces se deberan introducir los polígonos para continuar con el análisis.
10. Para el análisis de caídas y flujos es necesario que se hayan descargado en la carpeta general las geomorfas indicativas de estos procesos, pues en este punto la programación pedirá saber cuál archivo .csv corresponde a estos.
11. Para el análisis de subunidades geomorfologicas, en los análisis para caídas y flujos, se puede hacer la corrección de su aporte de susceptibilidad cómo lo indica la programación si no se está de acuerdo con lo asignado.
12. Para el análisis de amenaza, deben estar espacializadas las ubicacones de las estaciones pluviométricas y de los sismos, para poder así relacionarlos con los movimientos en masa.
13. Las estaciones pluviométricas deben identificarse con el código de estación, el mismo código con el que debe estar identificada la precipitación diaria.
14. Los simos deben tener por lo menos su campo de magnitud, unidades de magnitud y la fecha de ocurrencia.
15. Para el análisis de amenaza es fundamental les fechas reales, por lo que si no se tiene seguridad es mejor dejar el Movimiento en Masa sin fecha y la programación lo elimina.
16. Si se cuenta con suficientes movimientos en masa se puede hacer la discretización para el análisis de amenaza a partir del movimiento en masa y su respectiva categoría de susceptibilidad. Si no hay suficientes movimientos en masa se recomienda solo hacer la discretización según la categoría de susceptibilidad general.
17. Para el análisis de amenaza son necesarias varias variables cómo días umbrales, lluvia mínima, entre otros, los cuáles se asignan según el criterío experto y el conocimiento del área de estudio.
