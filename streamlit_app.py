import streamlit as st
import pandas as pd
import openpyxl
import altair as alt
import numpy as np
import locale
import math
import calendar 
import matplotlib.pyplot as plt

from streamlit_echarts import st_pyecharts
from pyecharts import options as opts
from pyecharts.charts import Pie
from datetime import datetime
from streamlit_extras.metric_cards import style_metric_cards 
from streamlit_echarts import st_echarts




# Configurar la página
import streamlit as st
import requests
from PIL import Image
import io
import base64

# Configurar la página
st.set_page_config(
    page_title="Reportabilidad GCP",
    page_icon="https://cdn-icons-png.flaticon.com/512/9428/9428279.png",
    layout="wide"
)

st.title('Análisis NV Abiertas')

# Obtener la imagen de la URL
image_url = "https://i.ibb.co/5jLPQyf/Logo-Fastpack-01-2.png"
response = requests.get(image_url)
image = Image.open(io.BytesIO(response.content))

# Convertir la imagen a bytes
buf = io.BytesIO()
image.save(buf, format='PNG')
image_bytes = buf.getvalue()

# Crear un bloque de HTML con la imagen centrada
html = f'<img src="data:image/png;base64,{base64.b64encode(image_bytes).decode()}" style="display: block; margin: auto; width: 105%;">'

# Mostrar el HTML en la barra lateral
st.sidebar.markdown(html, unsafe_allow_html=True)

# Agregar un separador después de la imagen
st.sidebar.markdown("<hr style='border:2.5px solid white'> </hr>", unsafe_allow_html=True)

st.sidebar.markdown("<h1 style='text-align: center; color: white;'>Análisis de Producción</h1>", unsafe_allow_html=True)


uploaded_file = st.sidebar.file_uploader("Carga las Notas de Venta Abierta", type=['xlsx'])

uploaded_file2 = st.sidebar.file_uploader("Carga Informe de Multa", type=['xlsx'])


# URL de la imagen
url_imagen = 'https://fen.uahurtado.cl/wp-content/uploads/2019/12/portada_articulo_5.png'



if uploaded_file is not None:
    if  uploaded_file2 is not None:
        df_original = pd.read_excel(uploaded_file, engine='openpyxl')
        dfm_original = pd.read_excel(uploaded_file2, engine='openpyxl')
        df=df_original
        dfm=dfm_original
        # Asegurarse de que 'Fecha NV' es de tipo datetime
        df['Fecha NV'] = pd.to_datetime(df['Fecha NV'], format="%d/%m/%Y")

        # Ajustar las fechas al mediodía
        df['Fecha NV'] = df['Fecha NV'].apply(lambda dt: dt.replace(hour=12))

        df['CPE'] = pd.to_datetime(df['CPE'], format="%d/%m/%Y")

        # Ajustar las fechas al mediodía
        df['CPE'] = df['CPE'].apply(lambda dt: dt.replace(hour=12))

        dfm['Fecha Guia'] = pd.to_datetime(dfm['Fecha Guia'], format="%d/%m/%Y")

        # Ajustar las fechas al mediodía
        dfm['Fecha Guia'] = dfm['Fecha Guia'].apply(lambda dt: dt.replace(hour=12))

        dfm['CPE Linea'] = pd.to_datetime(dfm['CPE Linea'],  format="%d/%m/%Y")

        # Ajustar las fechas al mediodía
        dfm['CPE Linea'] = dfm['CPE Linea'].apply(lambda dt: dt.replace(hour=12))
        # Definir el mapeo de 'Área de Negocios' a 'Unidad de Negocio'
        mapeo = {
            'Cañerías y Fittings': 'Piping',
            'Coplas': 'Piping',
            'Spools': 'Piping',
            'Revestimiento, Piezas Desgaste': 'Piping',
            'Anillo Cerámico': 'Piping',
            'Enrrollables': 'Piping',
            'FPS': 'FPS',
            'Valvulas': 'Valvulas',
            'Otras Ventas': 'Otras Ventas',
            'Asset Integrety': 'Asset Integrety'
        }

        # Crear la nueva columna 'Unidad de Negocio'
        df['Unidad de Negocio'] = df['Área de Negocios'].map(mapeo)
        unidades_negocio = df['Unidad de Negocio'].unique()


        
        # Crear un filtro en el sidebar de Streamlit
        areas_negocios = st.sidebar.multiselect(
            'Unidad de Negocio',
            df['Unidad de Negocio'].unique(),
            default=unidades_negocio
        )
        # Definimos una lista de colores
        colores = ['red', 'blue', 'green', 'purple', 'orange']

        # Inicializamos una cadena vacía para almacenar el texto
        texto = "<span style='font-size: 20px;'>Unidades de negocio seleccionadas: </span>"
        count=0
        for area, color in zip(areas_negocios, colores):
            count+=1
            # Añadimos cada unidad de negocio a la cadena de texto con su color correspondiente

            if len(areas_negocios)==count:
                texto += f"<span style='font-size: 20px; color: {color};'>{area}. </span>"
            else:
                texto += f"<span style='font-size: 20px; color: {color};'>{area}, </span>"

        # Usamos markdown con HTML para mostrar el texto
        st.markdown(texto, unsafe_allow_html=True)
        # Definir el mapeo de 'Área de Negocios' a 'Unidad de Negocio'
        # Agregar la imagen al sidebar
        st.sidebar.image(url_imagen)
        # Verificar si se ha seleccionado alguna área de negocio
        if not areas_negocios:
            st.write('Seleccione Unidades de Negocio.')
        else:
                
            # Filtrar el DataFrame en base a las Áreas de Negocios seleccionadas
            df_filtrado = df[df['Unidad de Negocio'].isin(areas_negocios)]
            df = df_filtrado
            df_original_filtrado=df_filtrado
            multas_por_dia = []
            top_nv = []
            top_diferencias = []

            for i in range(0, 10):
                df=df_original_filtrado
                dfm=dfm_original
                # Copia los dataframes
                df_i = df.copy()
                dfm_i = dfm.copy()

                # Actualiza 'Ahead / Delay'
                def update_ahead_delay(row):
                    if (row['Total por Despachar (CLP)'] > 1000) and (row['Pendiente x cerrar'] == 'NO'):
                        row['Ahead / Delay'] = row['Ahead / Delay'] -i

                    return row

                df = df.apply(update_ahead_delay, axis=1)

                # Actualiza 'Días de atraso'
                def actualizar_fecha_guia(row):
                    if pd.notnull(row['Fecha Guia']):
                        row=row
                    else:
                        row['Días de atraso'] = row['Días de atraso']-i

                    return row

                dfm = dfm.apply(actualizar_fecha_guia, axis=1)

                def asignar_color_y_multa(row):
                    
                    if pd.isnull(row['Ahead / Delay']):
                        return row['Semaforo'], np.nan, np.nan, np.nan
                    elif row['Ahead / Delay'] < 0:
                        a=0
                        if a==0:    
                            if row['% Multa po Atraso'] != 0 and row['% Multa po Atraso'] is not None:
                                if row['% de Multa se aplica a:'] == 'Semana de atraso':
                                    multa = abs(row['Ahead / Delay']/7) * row['% Multa po Atraso']
                                    if multa > row['Tope de Multa %']:
                                        return 'Naranjo', int(((row['Tope de Multa %'])/100)*row['Total Venta (CLP)']), np.nan, np.nan
                                    else:
                                        return 'Rojo', np.nan, int((math.floor(abs(row['Ahead / Delay'])/7)*(row['% Multa po Atraso'])/100)*row['Total Venta (CLP)']), int((row['% Multa po Atraso']/700)*row['Total Venta (CLP)'])
                                elif row['% de Multa se aplica a:'] == 'Día de atraso':
                                    multa = abs(row['Ahead / Delay']) * row['% Multa po Atraso']
                                    if multa > row['Tope de Multa %']:
                                        return 'Naranjo', int((((row['Tope de Multa %'])/100)*row['Total Venta (CLP)'])), np.nan, np.nan
                                    else:
                                        return 'Rojo', np.nan, int(((abs(row['Ahead / Delay'])*(row['% Multa po Atraso'])/100)*row['Total Venta (CLP)'])),int(((row['% Multa po Atraso'])/100)*row['Total Venta (CLP)'])
                            else:
                                return 'Rojo', np.nan, np.nan, np.nan
                
                    elif row['Ahead / Delay'] == 0:
                        return row['Semaforo'], np.nan, np.nan, np.nan
                    elif row['Ahead / Delay'] > 0 and row['Semaforo'] in ['Amarillo', 'Verde']:
                        return row['Semaforo'], np.nan, np.nan, np.nan
                    elif row['Ahead / Delay'] > 0 and row['Semaforo'] == 'Rojo':
                        return 'Verde', np.nan, np.nan, np.nan
                
                df[['Colores Semaforo', 'Multa Saturada', 'Multa en Curso','Multa Diaria']] = df.apply(asignar_color_y_multa, axis=1, result_type='expand')
                if 'Número de artículo' not in dfm.columns:
                    if 'Item No.' in dfm.columns:
                        dfm = dfm.rename(columns={'Item No.': 'Número de artículo'}) 
                        dfm=dfm.rename(columns={'Row Total': 'Total líneas'})
                    
                def asignar_items(df, dfm):
                    # Filtrar las filas en df donde 'Multa se calcula sobre:' es 'Valor del item atrasado'
                    df_filtrado = df[(df['Multa se calcula sobre:'] == 'Valor del item atrasado') & (df['Ahead / Delay'] < 0) & (df['% Multa po Atraso']>0)]


                    # Crear una lista vacía para almacenar los resultados
                    items = []

                    # Iterar sobre las filas en df_filtrado
                    for _, row in df_filtrado.iterrows():
                        # Buscar coincidencias en dfm
                        coincidencias = dfm[dfm['NV'] == row['Nota de venta']]

                        # Si hay coincidencias, agregar la información relevante a items
                        if not coincidencias.empty:
                            for _, item in coincidencias.iterrows():
                                items.append({
                                    'Nota de venta': item['NV'],
                                    'Número de artículo': item['Número de artículo'],
                                    'Total Venta (CLP)': item['Total líneas'],
                                    'CPE': item['CPE Linea'],
                                    'Administrador Contratos': row['Administrador Contratos'],
                                    'Cliente': row['Cliente'],
                                    'Orden de Compra Cliente': row['Orden de Compra Cliente'],
                                    'Tipo de Entrega': row['Tipo de Entrega'],
                                    'Vendedor': row['Vendedor'],
                                    'Multa se calcula sobre:': row['Multa se calcula sobre:'],
                                    '% de Multa se aplica a:': row['% de Multa se aplica a:'],
                                    '% Multa po Atraso': row['% Multa po Atraso'],
                                    'Días de atraso':item['Días de atraso'],
                                    'Tope de Multa %': row['Tope de Multa %'],
                                    'Fecha NV':row['Fecha NV'],
                                    'Fecha Guia': item['Fecha Guia'],
                                    'Total por Despachar (CLP)':row['Total por Despachar (CLP)'],
                                    'Ahead / Delay':item['Días de atraso'],
                                    'Pendiente x cerrar': row['Pendiente x cerrar']
                                })

                        # Crear un DataFrame a partir de items
                        df_items = pd.DataFrame(items)

                        return df_items

                df_items=asignar_items(df,dfm)

        
                def calcular_multas(row):
                    if pd.isnull(row['Días de atraso']):
                        return np.nan, np.nan, np.nan, 'No'
                    elif row['Días de atraso'] < 0:
                        if row['% Multa po Atraso'] != 0 and row['% Multa po Atraso'] is not None:
                            if row['% de Multa se aplica a:'] == 'Semana de atraso':
                                multa = abs(row['Días de atraso']/7) * row['% Multa po Atraso']
                                if multa > row['Tope de Multa %']:
                                    return int(((row['Tope de Multa %'])/100)*row['Total Venta (CLP)']), np.nan, np.nan, 'Sí' if pd.notnull(row['Fecha Guia']) else 'No'
                                else:
                                    if pd.notnull(row['Fecha Guia']):
                                        return int((math.floor(abs(row['Días de atraso'])/7)*(row['% Multa po Atraso'])/100)*row['Total Venta (CLP)']),np.nan, np.nan,'Sí' if pd.notnull(row['Fecha Guia']) else 'No'
                                    else:
                                        return np.nan, int((math.floor(abs(row['Días de atraso'])/7)*(row['% Multa po Atraso'])/100)*row['Total Venta (CLP)']), int((row['% Multa po Atraso']/700)*row['Total Venta (CLP)']), 'Sí' if pd.notnull(row['Fecha Guia']) else 'No'
                            elif row['% de Multa se aplica a:'] == 'Día de atraso':
                                multa = abs(row['Días de atraso']) * row['% Multa po Atraso']
                                if multa > row['Tope de Multa %']:
                                    return int((((row['Tope de Multa %'])/100)*row['Total Venta (CLP)'])), np.nan, np.nan, 'Sí' if pd.notnull(row['Fecha Guia']) else 'No'
                                else:
                                    if pd.notnull(row['Fecha Guia']):
                                        return int(((abs(row['Días de atraso'])*(row['% Multa po Atraso'])/100)*row['Total Venta (CLP)'])), np.nan, np.nan,'Sí' if pd.notnull(row['Fecha Guia']) else 'No'
                                    else:
                                        return np.nan, int(((abs(row['Días de atraso'])*(row['% Multa po Atraso'])/100)*row['Total Venta (CLP)'])),int(((row['% Multa po Atraso'])/100)*row['Total Venta (CLP)']), 'Sí' if pd.notnull(row['Fecha Guia']) else 'No'
                        else:
                            return np.nan, np.nan, np.nan, 'No'
                if df_items is not None or df['Multa en Curso'].sum()+df['Multa Saturada'].sum()!=0:
                    # Aplicar la función calcular_multas a df_items
                    if not df_items.empty:
                        df_items[['Multa Saturada', 'Multa en Curso', 'Multa Diaria', 'Multa Despachada']] = df_items.apply(calcular_multas, axis=1, result_type='expand')
                        df_items['Días de atraso']=df_items['Días de atraso']


                    # Filtrar el DataFrame para solo los casos donde 'Colores Semaforo' es 'Rojo'
                    df_rojo = df[(df['Colores Semaforo'] == 'Rojo') & (df['Multa en Curso'] > 100000)]

                    # Crear una columna con colores únicos para cada 'Nota de venta'
                    df_rojo['Color'] = df_rojo['Nota de venta'].map(dict(zip(df_rojo['Nota de venta'].unique(), range(df_rojo['Nota de venta'].nunique()))))

                    # Ordenar el DataFrame por 'Multa en Curso' de mayor a menor
                    df_rojo = df_rojo.sort_values('Multa en Curso', ascending=False)
                    df_rojo['Días de atraso'] = df_rojo['Ahead / Delay']

                    df_filtrado_rojo = df_rojo[df_rojo['Multa se calcula sobre:'] == 'Valor total de orden de Compra']
                    if df_items is not None and not df_items.empty:
                        df_filtrado_rojo['Suma Multas']=df_filtrado_rojo['Multa en Curso'].sum()+df_items.loc[df_items['Multa en Curso'].notnull(), 'Multa en Curso'].sum()
                    else:
                        df_filtrado_rojo['Suma Multas']=df_filtrado_rojo['Multa en Curso'].sum()
                    #df_items['Suma Multas']=df_items['Multa en Curso'].sum()
                    # Calcular la suma de las multas en curso y las multas saturadas
                    if df_items is not None and not df_items.empty:
                        suma_multas_en_curso = df_items.loc[df_items['Multa en Curso'].notnull(), 'Multa en Curso'].sum()+df_filtrado_rojo['Multa en Curso'].sum()
                        suma_multas_saturadas = df_items.loc[df_items['Multa Saturada'].notnull(), 'Multa Saturada'].sum()
                    if df_items is not None and not df_items.empty:
                        # Asignar estos valores a la nueva columna 'Suma Multas'
                        df_items.loc[df_items['Multa en Curso'].notnull(), 'Suma Multas'] = suma_multas_en_curso
                        #df_items.loc[df_items['Multa Saturada'].notnull(), 'Suma Multas'] = suma_multas_saturadas


                    df_combinado = pd.concat([df_filtrado_rojo, df_items])
                    df_combinado = df_combinado[df_combinado['Multa en Curso'] > 0]
                    
                    # Asegurarse de que 'Fecha NV' es de tipo datetime
                    df_combinado['Fecha NV'] = pd.to_datetime(df_combinado['Fecha NV'], format="%d/%m/%Y")

                    # Ajustar las fechas al mediodía
                    df_combinado['Fecha NV'] = df_combinado['Fecha NV'].apply(lambda dt: dt.replace(hour=12))

                    df_combinado['CPE'] = pd.to_datetime(df_combinado['CPE'], format="%d/%m/%Y")

                    # Ajustar las fechas al mediodía
                    df_combinado['CPE'] = df_combinado['CPE'].apply(lambda dt: dt.replace(hour=12))

                    if df_items is not None and not df_items.empty:
                        df_combinado.loc[df_combinado['Fecha Guia'].notnull(), 'CPE'] = 'Despachado'
                    #st.write(df_items)    
                    #st.write(df_combinado)    
                    df_combinado['Estado'] = df_combinado.apply(lambda x: 'Despachado' if pd.notnull(x['Fecha Guia']) or x['Total por Despachar (CLP)'] < 1 else 'Pendiente', axis=1)
                    df_combinado['Estado'] = df_combinado.apply(
                        lambda x: 'Despachado' if not pd.isnull(x['Fecha Guia']) or x['Total por Despachar (CLP)'] < 1 else 'Pendiente', 
                        axis=1
                    )

                    df_combinado = df_combinado[df_combinado['Multa en Curso'] > 100000]
                    # Crear una columna de orden para el estado
                    orden_estado = {'Pendiente': 0, 'Despachado': 1}
                    df_combinado['Orden Estado'] = df_combinado['Estado'].map(orden_estado)

                    # Ordenar el DataFrame
                    df_combinado.sort_values(by=['Nota de venta', 'Orden Estado'], ascending=[True, False], inplace=True)
                    if df_combinado['Multa en Curso'].sum()>0:
                        # Mostrar el gráfico
                        chart_combinado = alt.Chart(df_combinado).mark_bar().encode(
                            x=alt.X('Nota de venta:N', sort='-y'),
                            y=alt.Y('Multa en Curso:Q', title='Multa en Curso (CLP)', axis=alt.Axis(format=',d')),
                            color=alt.Color('Cliente:N', legend=alt.Legend(title='Cliente')),
                            tooltip=[
                                alt.Tooltip('Multa en Curso', title='Multa en Curso (CLP)', format=',d'),
                                alt.Tooltip('Días de atraso', title='Días de atraso', format=',d'),
                                alt.Tooltip('Multa Diaria', title='Incremento Diario', format=',d'),
                                alt.Tooltip('% de Multa se aplica a:', title='Tipo de Multa'),
                                alt.Tooltip('Total Venta (CLP)', title='Total Venta', format=',d'),
                                'Nota de venta',
                                alt.Tooltip('Administrador Contratos', title='Administrador de Contrato'),
                                alt.Tooltip('Suma Multas', title='Acumulado Multas', format=',d'),
                                alt.Tooltip('Cliente', title='Cliente'),
                                alt.Tooltip('Número de artículo', title='TAG'),
                                alt.Tooltip('CPE', title='CPE'),
                                alt.Tooltip('Fecha NV', title='Fecha NV'),
                                alt.Tooltip('Estado', title='Estatus')
                            ]
                        ).properties(
                            height=500, width=900,
                            title='Estimación de Multas en Curso por Periodo de Atraso'
                        ).interactive()

                        # Mostrar el gráfico
                        #chart_combinado
                    else:
                        if i==0:
                            #st.header('Sin multas en curso.')
                            st.write(" ")
                    df_naranjo=df[(df['Colores Semaforo'] == 'Naranjo') & (df['Multa Saturada'] > 100000)]
                    # Crear una columna con colores únicos para cada 'Nota de venta'
                    df_naranjo['Color'] = df_naranjo['Nota de venta'].map(dict(zip(df_naranjo['Nota de venta'].unique(), range(df_naranjo['Nota de venta'].nunique()))))
                    df_naranjo['Días de atraso'] = df_naranjo['Ahead / Delay']

                    # Ordenar el DataFrame por 'Multa en Curso' de mayor a menor
                    df_naranjo = df_naranjo.sort_values('Multa Saturada', ascending=False)
                    df_naranjo = df_naranjo[df_naranjo['Multa se calcula sobre:'] == 'Valor total de orden de Compra']
                    df_naranjo['Suma Multas']=df_naranjo['Multa Saturada'].sum()
        
                    df_items['Días de atraso']=df_items['Días de atraso']
                    df_combinado2 = pd.concat([df_naranjo, df_items])
                    df_combinado2 = df_combinado2[df_combinado2['Multa Saturada'] > 100000]
                    df_combinado2['Suma Multas']=df_combinado2['Multa Saturada'].sum()
                                # Asegurarse de que 'Fecha NV' es de tipo datetime
                    df_combinado2['Fecha NV'] = pd.to_datetime(df_combinado2['Fecha NV'], format="%d/%m/%Y")

                    # Ajustar las fechas al mediodía
                    df_combinado2['Fecha NV'] = df_combinado2['Fecha NV'].apply(lambda dt: dt.replace(hour=12))

                    df_combinado2['CPE'] = pd.to_datetime(df_combinado2['CPE'], format="%d/%m/%Y")

                    # Ajustar las fechas al mediodía
                    df_combinado2['CPE'] = df_combinado2['CPE'].apply(lambda dt: dt.replace(hour=12))
                    #df_combinado2.loc[df_combinado2['Fecha Guia'].notnull(), 'CPE'] = 'Despachado'
                    #df_combinado2.loc[df_combinado2['CPE'] != 'Despachado', 'CPE'] = pd.to_datetime(df_combinado2.loc[df_combinado2['CPE'] != 'Despachado', 'CPE'])
                    #df_combinado2['Estado'] = df_combinado2['Fecha Guia'].apply(lambda x: 'Despachado' if pd.notnull(x) else 'Pendiente')
                    df_combinado2['Estado'] = df_combinado2.apply(lambda x: 'Despachado' if pd.notnull(x['Fecha Guia']) or x['Total por Despachar (CLP)'] < 1 else 'Pendiente', axis=1)
                    # Crear una columna de orden para el estado
                    orden_estado = {'Pendiente': 0, 'Despachado': 1}
                    df_combinado2['Orden Estado'] = df_combinado2['Estado'].map(orden_estado)

                    # Ordenar el DataFrame
                    df_combinado2.sort_values(by=['Nota de venta', 'Orden Estado'], ascending=[True, False], inplace=True)

                    
                    chart_combinado2 = alt.Chart(df_combinado2).mark_bar().encode(
                        x=alt.X('Nota de venta:N', sort='-y'),
                        y=alt.Y('Multa Saturada:Q', title='Multa Saturada (CLP)', axis=alt.Axis(format=',d')),
                        color=alt.Color('Cliente:N', legend=alt.Legend(title='Cliente')),
                        tooltip=[
                            alt.Tooltip('Multa Saturada', title='Multa Saturada (CLP)', format=',d'),
                            alt.Tooltip('Días de atraso', title='Días de atraso', format=',d'),
                            alt.Tooltip('Administrador Contratos', title='Administrador de Contrato'),
                            alt.Tooltip('Total Venta (CLP)', title='Total Venta (CLP)', format=',d'),
                            'Nota de venta',
                            alt.Tooltip('Suma Multas', title='Acumulado Multas', format=',d'),
                            alt.Tooltip('Cliente', title='Cliente'),
                            alt.Tooltip('CPE', title='CPE'),
                            alt.Tooltip('Fecha NV', title='Fecha NV'),
                            alt.Tooltip('Número de artículo', title='TAG'),
                            alt.Tooltip('Estado', title='Estatus')
                        ]
                    ).properties(
                    height=500,width=900,     
                        title='Multas Estimadas por tope de Orden de compra'
                    ).interactive()

                    # Mostrar el gráfico
                    #chart_combinado2
                    df_unificado=pd.concat([df_combinado, df_combinado2])

                    
                    def asignar_multa_proyectada(row):
                        if row['Total por Despachar (CLP)']<1000 or row['Pendiente x cerrar']=='SI':

                            if row['Multa Saturada'] >0:
                                row['Historial Multas']=row['Multa Saturada']
                                return np.nan,row['Multa Saturada']
                            else:
                                row['Historial Multas']=row['Multa en Curso']
                                return np.nan,row['Multa en Curso']
                        else:
                            if row['Multa Saturada']>0:
                                row['Multas Proyectadas']=row['Multa Saturada']
                                return row['Multa Saturada'], np.nan
                            else:
                                row['Multas Proyectadas']=row['Multa en Curso']
                                return row['Multa en Curso'], np.nan

                            
                    df_unificado[['Multas Proyectadas','Historial Multas']]=df_unificado.apply(asignar_multa_proyectada, axis=1,result_type='expand')
                    df_historial_multas=df_unificado[df_unificado['Historial Multas']>0]

                    # Calcula las sumas
                    Suma_multas_historial = (df_historial_multas['Historial Multas'].sum())
                    suma_total_venta_historial = df_historial_multas['Total Venta (CLP)'].sum()

                    # Calcula el porcentaje
                    porcentaje_historial = round(((Suma_multas_historial / suma_total_venta_historial) * 100),2)
                    df_historial_multas_filtro=df_historial_multas[df_historial_multas['Historial Multas']<250000000]
                    # Crea la tarjeta de métricas
                    if df_historial_multas_filtro.empty==False:
                        chart_historial = alt.Chart(df_historial_multas_filtro).mark_bar().encode(
                            x=alt.X('Nota de venta:N', sort='-y'),
                            y=alt.Y('Historial Multas:Q', title='Valor Multa(CLP)', axis=alt.Axis(format=',d')),
                            color=alt.Color('Cliente:N', legend=None),
                            tooltip=[
                                'Nota de venta',
                                alt.Tooltip('Historial Multas', title='Valor Multa (CLP)', format=',d'),
                                alt.Tooltip('Días de atraso', title='Días de atraso', format=',d'),
                                alt.Tooltip('Administrador Contratos', title='Administrador de Contrato'),
                                alt.Tooltip('Total Venta (CLP)', title='Total Venta (CLP)', format=',d'),
                                alt.Tooltip('Total por Despachar (CLP)', title='Total Por Despachar', format=',d'),
                                alt.Tooltip('Cliente', title='Cliente'),
                                alt.Tooltip('CPE', title='CPE'),
                                alt.Tooltip('Fecha NV', title='Fecha NV'),
                                alt.Tooltip('Número de artículo', title='TAG'),
                                alt.Tooltip('Estado', title='Estatus'),
                                alt.Tooltip('Pendiente x cerrar', title='Pendiente por cerrar')
                                
                            ]
                        ).properties(
                        height=400,width=800,     
                            title='Historial de Multas'
                        ).interactive()
                        #st.metric(label="Total Historial de Multas (CLP)", value=f"{Suma_multas_historial:,}", delta=f"-{porcentaje:.2f}%")

                        #chart_historial
                    else:
                        if i==0:
                            st.write(" ")
                            #st.header("Sin Historial de Multas")
                    df_multas_proyectadas=df_unificado[df_unificado['Multas Proyectadas']>0]

                    # Calcula las sumas
                    Suma_multas_proyectadas = int(df_multas_proyectadas['Multas Proyectadas'].sum())
                    suma_total_venta_proyectadas = df_multas_proyectadas['Total Venta (CLP)'].sum()

                    # Calcula el porcentaje
                    porcentaje_proyectadas = round((Suma_multas_proyectadas / suma_total_venta_proyectadas) * 100,2)

                    
                    # Crea la tarjeta de métricas
                    #st.metric(label="Multas Totales Proyectadas", value=f"{Suma_multas_proyectadas:,}", delta=f"-{porcentaje:.2f}%")
                    df_multas_proyectadas_filtro=df_multas_proyectadas[df_multas_proyectadas['Multas Proyectadas']<900000000]
                    #st.write(df_multas_proyectadas_filtro)
                    chart_proyectadas = alt.Chart(df_multas_proyectadas_filtro).mark_bar().encode(
                        x=alt.X('Nota de venta:N', sort='-y'),
                        y=alt.Y('Multas Proyectadas:Q', title='Valor Multa (CLP)', axis=alt.Axis(format=',d')),
                        color=alt.Color('Cliente:N', legend=None),
                        tooltip=[
                            'Nota de venta',
                            alt.Tooltip('Multas Proyectadas', title='Valor Multa (CLP)', format=',d'),
                            alt.Tooltip('Días de atraso', title='Días de atraso', format=',d'),
                            alt.Tooltip('Administrador Contratos', title='Administrador de Contrato'),
                            alt.Tooltip('Total Venta (CLP)', title='Total Venta (CLP)', format=',d'),
                            alt.Tooltip('Total por Despachar (CLP)', title='Total Por Despachar', format=',d'),
                            alt.Tooltip('Multa Diaria', title='Incremento Diario', format=',d'),
                            alt.Tooltip('Cliente', title='Cliente'),
                            alt.Tooltip('CPE', title='CPE'),
                            alt.Tooltip('Fecha NV', title='Fecha NV'),
                            alt.Tooltip('Número de artículo', title='TAG'),
                            alt.Tooltip('Estado', title='Estatus'),
                            alt.Tooltip('Pendiente x cerrar', title='Pendiente por cerrar'),

                        ]
                    ).properties(
                    height=400,width=800,     
                        title='Multas Proyectadas'
                    ).interactive()
                    #chart_proyectadas
                    

                df['CPE'] = pd.to_datetime(df['CPE'], format="%d/%m/%Y")

                # Crea una nueva columna para el mes
                df['Mes'] = df['CPE'].dt.month

                # Crea una lista de opciones de meses
                meses = sorted(df['Mes'].unique())

                # Crea una selección para cada mes
                selecciones = [alt.selection_single(fields=['Mes'], name=str(mes)) for mes in meses]
                # Crear el gráfico de tipo carta Gantt


                # Crea el gráfico de barras apiladas
                df_despachar = df[df['Total por Despachar (CLP)'] > 1000]
                chart_despachar = alt.Chart(df_despachar).mark_bar().encode(
                    x='CPE:T',
                    y='Total por Despachar (CLP):Q',
                    color=alt.Color('Cliente:N', legend=None),
                    tooltip=['Nota de venta:N', 'Cliente:N',
                            alt.Tooltip('Total por Despachar (CLP)', title='Por Despachar', format=',d'),
                            alt.Tooltip('CPE', title='Fecha de entrega')],
                    order=alt.Order('Total por Despachar (CLP):Q', sort='descending')
                ).properties(
                    height=500, width=900,
                    title='Total por despachar según CPE'
                ).interactive()



                # Muestra el gráfico
                #chart_despachar
                # Suponiendo que 'df_despachar' es tu DataFrame y 'CPE' es la columna de fechas
                current_year = datetime.now().year
                current_month = datetime.now().month

                # Filtra el DataFrame para que solo contenga los datos del mes actual
                df_current_month = df_despachar[(df_despachar['CPE'].dt.year == current_year) & (df_despachar['CPE'].dt.month == current_month)]

                # Crea una nueva columna 'Dia' que contenga solo el número del día
                df_current_month['Dia'] = df_current_month['CPE'].dt.day

                # Encuentra el último día del mes actual
                ultimo_dia_del_mes = pd.to_datetime('today').replace(day=1) + pd.offsets.MonthEnd(1)
                ultimo_dia_del_mes = ultimo_dia_del_mes.day

                # Diccionario con los nombres de los meses en español
                meses_ESP = {1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril', 5: 'Mayo', 6: 'Junio', 
                            7: 'Julio', 8: 'Agosto', 9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'}

                # Obtiene el mes actual en español
                current_month_ESP = meses_ESP[current_month]

                # Verifica si el DataFrame no está vacío
                if not df_current_month.empty:
                    chart_total_mes = alt.Chart(df_current_month).mark_bar(size=16).encode(
                        x=alt.X('Dia:Q', title='Día del mes', axis=alt.Axis(grid=False), scale=alt.Scale(domain=(1, ultimo_dia_del_mes))),  # Ajustes aquí
                        y='Total por Despachar (CLP):Q',
                        color=alt.Color('Cliente:N',legend=None),
                        tooltip=['Nota de venta:N', 'Cliente:N',
                                alt.Tooltip('Total por Despachar (CLP)', title='Por Despachar', format=',d'),
                                alt.Tooltip('Administrador Contratos', title='Administrador de Contratos'),
                                alt.Tooltip('CPE', title='Fecha de entrega')],
                        order=alt.Order('Total por Despachar (CLP):Q', sort='descending')
                    ).properties(
                        height=500, width=900,
                        title='Total por despachar para ' + str(current_month_ESP) + ' según CPE'
                    ).interactive()
                    # Muestra el gráfico
                    #chart_total_mes

                #st.write(df_current_month)

                # Primero, calcula la suma total de "Total Venta (CLP)" para cada cliente
                df_sum = df.groupby('Cliente')['Total Venta (CLP)'].sum().reset_index()

                # Luego, crea una lista de diccionarios donde cada diccionario representa un cliente y su suma total
                data = df_sum.to_dict('records')

                # Primero, calcula la suma total de "Total Venta (CLP)" para cada cliente
                df_sum = df.groupby('Cliente')['Total Venta (CLP)'].sum().reset_index()
                # Calcula la suma total de "Total Venta (CLP)" para cada cliente
                df_sum = df.groupby('Cliente')['Total Venta (CLP)'].sum().reset_index()

                # Calcula el total de ventas de todos los clientes
                total_venta = df['Total Venta (CLP)'].sum()

                # Calcula el porcentaje del total de ventas para cada cliente
                df_sum['Total Venta %'] = round((df_sum['Total Venta (CLP)'] / total_venta) * 100,1)
                #st.write("  ")
                total_clientes = df_sum['Cliente'].nunique()
                df_sum = df_sum.sort_values('Total Venta %', ascending=True)
                #st.write(df_current_month)
                pie_ingresos = (
                    Pie()
                    .add("", [list(z) for z in zip(df_sum['Cliente'], df_sum['Total Venta %'])], radius=["40%", "75%"])
                    .set_global_opts(
                        legend_opts=opts.LegendOpts(is_show=False), # Oculta la leyenda de colores
                        graphic_opts=[
                            opts.GraphicText(
                                graphic_item=opts.GraphicItem(
                                    left="center",
                                    top="center",
                                    z=1
                                ),
                                graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                                    text=f"{total_clientes} Clientes",
                                    font="bold 17px Microsoft YaHei",
                                    graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(fill="#333")
                                )
                            )
                        ]
                    )
                    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}"), # Muestra solo el nombre de la compañía
                                    tooltip_opts=opts.TooltipOpts(formatter="{b}: {c}%")) # Muestra el número solo al pasar el mouse por encima
                )



                #st_pyecharts(pie_ingresos)

                chart = alt.Chart(df).mark_bar().encode(
                    x='Fecha NV:T',
                    x2='CPE:T',
                    y='Total Venta (CLP):Q',
                    color='Cliente:N',
                    tooltip=['Nota de venta:N', 'Cliente:N',
                    alt.Tooltip('Fecha NV', title='Fecha Inicio'),
                    alt.Tooltip('CPE', title='Fecha de entrega'), 
                    alt.Tooltip('Total por Despachar (CLP)', title='Por Despachar', format=',d')]

                ).properties(
                height=500,width=900, 
                    title='Carta Gantt Total Venta X CPE'
                ).interactive()

                # Muestra el gráfico
                #chart
                # Asegúrate de que las columnas existen en el DataFrame
                if 'Nota de venta' in df.columns and 'Área de Negocios' in df.columns:
                    df_nv = df[['Nota de venta', 'Área de Negocios']]
                    
                    # Crea un DataFrame con la suma de las notas de venta por área de negocios
                    sum_df = df_nv.groupby('Área de Negocios')['Nota de venta'].nunique().reset_index(name='Número de NV')
                    
                    # Ordena el DataFrame de forma ascendente por 'Número de NV'
                    sum_df = sum_df.sort_values('Número de NV', ascending=False).reset_index()

                    # Asegúrate de que sum_df esté ordenado como deseas que aparezca la leyenda
                    sum_df = sum_df.sort_values('Número de NV', ascending=False)

                    # Ahora, usa 'scale' con 'domain' para especificar el orden de la leyenda
                    chart_nv_area = alt.Chart(sum_df).mark_bar().encode(
                        x=alt.X('Área de Negocios:N', sort='-y', axis=None),
                        y='Número de NV:Q',
                        color=alt.Color('Área de Negocios:N', 
                                        scale=alt.Scale(domain=sum_df['Área de Negocios'].tolist()),
                                        legend=alt.Legend(title='Área de Negocios')),
                        tooltip=['Área de Negocios', 'Número de NV']
                    ).properties(
                        height=300,
                        width=900
                    )

                    #st.write(df_current_month,"mesencurso")
                    #st.altair_chart(chart_nv_area, use_container_width=True)
                    total_multas=Suma_multas_historial+Suma_multas_proyectadas
                    total_despachar=int(df_despachar['Total por Despachar (CLP)'].sum())
                    total_despachar_en_curso=int(df_current_month['Total por Despachar (CLP)'].sum())
                    notas_venta_mes = df_current_month['Nota de venta'].nunique()
                    df_atrasadas = df_current_month[df_current_month['Ahead / Delay'] < 0]
                    condicion2 = df_current_month['Pendiente x cerrar'] == 'No'
                    condicion3 = df_current_month['Total por Despachar (CLP)'] > 1000
                    df_atrasadas = df_atrasadas[(condicion2 | condicion3)]
                    # Calcula el número único de notas de venta atrasadas
                    notas_venta_atrasadas = df_atrasadas['Nota de venta'].nunique()
                    # Crea una máscara booleana para los casos en que 'Ahead / Delay' es negativo
                    mask = df_despachar['Ahead / Delay'] < 0

                    # Usa la máscara para filtrar el DataFrame y luego suma la columna 'Total por Despachar (CLP)'
                    total_despachar_atrasado = int(df_despachar.loc[mask, 'Total por Despachar (CLP)'].sum())
                    mask1=df_current_month['Ahead / Delay'] < 0
                    total_atrasado_mes = int(df_current_month.loc[mask1, 'Total por Despachar (CLP)'].sum())
                    if total_atrasado_mes>0:
                        total_atrasado_mes=-total_atrasado_mes
                    if i==1:
                        col11.metric(label="Total Multas Mañana CLP",value=f"{total_multas:,}",delta=str(-round((total_multas/(suma_total_venta_historial+suma_total_venta_proyectadas))*100,1))+" %"+" Pérdida Monto Total")
                    if i==7:
                        col12.metric(label="Total Multas Próxima Semana CLP",value=f"{total_multas:,}",delta=str(-round((total_multas/(suma_total_venta_historial+suma_total_venta_proyectadas))*100,1))+" %"+" Pérdida Monto Total")

                    if i==0:
                        st.header("KPIs")
                        col5, col11,col12=st.columns(3)
                        col5.metric(label="Total Multas CLP",value=f"{total_multas:,}",delta=str(-round((total_multas/(suma_total_venta_historial+suma_total_venta_proyectadas))*100,1))+" %"+" Pérdida Monto Total")
                        
                        #st.metric(label="Proyección Multas Mañana")
                        #st.metric(label="Proyección Multas Semanal")
                        col1, col2,col13 = st.columns(3)
                        col1.metric(label="Total CLP por Despachar",value=f"{total_despachar:,}",delta=f"{-total_despachar_atrasado:,}"+" Atrasados")
                        col2.metric(label="CLP por Despachar Mes en curso",value=f"{total_despachar_en_curso:,}",delta=str(f"{total_atrasado_mes:,}")+ " Atrasados")
                        col13.metric(label="NV a Despachar Mes en curso",value=f"{notas_venta_mes:,}",delta=str(-notas_venta_atrasadas)+" Atrasadas")


                    ##prueba fin dia
                    # Crea una lista para almacenar los totales de multas por día


                
                    # Calcula el total de multas para el día i
                    total_multas_i = int(df_unificado['Multas Proyectadas'].sum()) + int(df_unificado['Historial Multas'].sum())

                    # Añade el total al listado
                    multas_por_dia.append(total_multas_i)
                    #ACA SE PEGA CALCULO TOP 3


                    
                                    #if i>1:
                        


                #prueba fin dia 
                


                ###NUEVO INTENTO CALCULAR MULTAS
                ##Intento calcular Multas
                #Restar -1 a los dias actuales 

                df_atrasado=df

                # Primero, verifica si 'Multa Saturada' no tiene valores ni información


                multas_anterior=df_unificado
                if i==0:
                    col3, col4 = st.columns(2)
                #col6.metric(label="Multas Proyectadas Mañana",value=f"{multas_mañana:,}")
                ##Intento calcular Multas
                    st.write(" ")
                # Primero, calcula la suma total de "Total por Despachar (CLP)" para cada "Área de Negocios"
                df_sum = df.groupby('Área de Negocios')['Total por Despachar (CLP)'].sum().reset_index()

                # Calcula el total general
                total_general = df_sum['Total por Despachar (CLP)'].sum()

                # Crea una nueva columna 'Total por Despachar %' que sea el (Total por Despachar (CLP) / total_general) * 100
                df_sum['Total por Despachar %'] = (df_sum['Total por Despachar (CLP)'] / total_general) * 100
                df_sum['Total por Despachar %'] = df_sum['Total por Despachar %'].apply(lambda x: (round(x,1)))
                df_sum['MCLP'] = df_sum['Total por Despachar (CLP)'] / 1000000

                # Crea una nueva columna que combine el nombre de la 'Área de Negocios' y el 'Total por Despachar (CLP)'
                df_sum['Área y Total'] = df_sum['Área de Negocios'] + ': ' + df_sum['MCLP'].apply(lambda x: '{:,}'.format(int(x)))
                df_sum = df_sum.sort_values('Total por Despachar %', ascending=True)
                # Ahora, puedes usar ECharts para crear tu gráfico
                pie_despachar = (
                    Pie()
                    .add(
                        "",
                        [list(z) for z in zip(df_sum['Área y Total'], df_sum['Total por Despachar %'])],
                        radius=["40%", "75%"],  # Esto crea el efecto de anillo
                    )
                    .set_global_opts(
                        legend_opts=opts.LegendOpts(is_show=False),  # Esto oculta la leyenda de colores
                        graphic_opts=[
                            opts.GraphicText(
                                graphic_item=opts.GraphicItem(
                                    left="center",
                                    top="center",
                                    z=1
                                ),
                                graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                                    text=f"{int(df_sum['MCLP'].sum())} $MCLP",
                                    font="bold 17px Microsoft YaHei",
                                    graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(fill="#333")
                                )
                            )
                        ]
                    )
                    .set_series_opts(
                        label_opts=opts.LabelOpts(formatter="{b}"),  # Muestra solo el nombre de la área de negocios y el total por despachar
                        tooltip_opts=opts.TooltipOpts(formatter="{b}: {c} %"),  # Muestra el número solo al pasar el mouse por encima
                    )
                )
                # Asumiendo que df_current_month es tu DataFrame y que 'Nota de Venta', 'Total por Despachar (CLP)', 'Administrador de Contrato', 'Cliente', 'CPE' son columnas en df_current_month
                total_notas_venta = len(df_current_month['Nota de venta'].unique()) # Calcula el número de notas de venta únicas

                df_current_month['Total por Despachar (MCLP)'] = (df_current_month['Total por Despachar (CLP)'] / 1_000_000).astype(int)
                df_current_month = df_current_month.sort_values('Total por Despachar (MCLP)', ascending=True)
                pie_nv = (
                    Pie()
                    .add("", [list(z) for z in zip(df_current_month['Nota de venta'], df_current_month['Total por Despachar (MCLP)'])], radius=["40%", "75%"])
                    .set_global_opts(
                        legend_opts=opts.LegendOpts(is_show=False), # Oculta la leyenda de colores
                        graphic_opts=[
                            opts.GraphicText(
                                graphic_item=opts.GraphicItem(
                                    left="center",
                                    top="center",
                                    z=1
                                ),
                                graphic_textstyle_opts=opts.GraphicTextStyleOpts(
                                    text=f"{total_notas_venta} NV",
                                    font="bold 17px Microsoft YaHei",
                                    graphic_basicstyle_opts=opts.GraphicBasicStyleOpts(fill="#333")
                                )
                            )
                        ]
                    )
                    .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}"), # Muestra solo el nombre de la nota de venta
                                    tooltip_opts=opts.TooltipOpts(formatter="NV {b}: {c} MCLP")) # Muestra el número solo al pasar el mouse por encima
                )



                #st_pyecharts(pie_despachar)
                if i==0:



                    if df_historial_multas.empty:
                        nada=0


                        
                    #st.metric(label="Multas Totales Proyectadas", value=f"{Suma_multas_proyectadas:,}", delta=f"-{porcentaje:.2f}%")
                    if df_multas_proyectadas.empty:
                        st.write("Sin Multas Proyectadas")

                    #Mati Presentación
                    st.header ("Multas")
                    style_metric_cards()
                    col1, col2 = st.columns(2)
                    if not df_historial_multas.empty:  
                        with col1: 
                            st.metric(label="Total Historial de Multas (CLP)", value=f"{Suma_multas_historial:,}", delta=f"-{porcentaje_historial:.2f}%")                
                            st.altair_chart(chart_historial,use_container_width=True)
                            
                    if not df_multas_proyectadas.empty:  
                        with col2:
                            st.metric(label="Multas Totales Proyectadas", value=f"{Suma_multas_proyectadas:,}", delta=f"-{porcentaje_proyectadas:.2f}%")
                            st.altair_chart(chart_proyectadas,use_container_width=True)
                if i==9: 
                    # Crear un DataFrame para los datos
                    grafico_multas = pd.DataFrame({
                        'Días a futuro': range(0, 10),
                        'Total de multas $MCLP': multas_por_dia
                    })
                    

                    # Crear el gráfico de área
                    area = alt.Chart(grafico_multas).mark_area(
                        point=alt.MarkConfig(shape='circle', filled=True),
                        color='steelblue',
                        opacity=0.5
                    ).encode(
                        x=alt.X('Días a futuro:Q', scale=alt.Scale(zero=False), axis=alt.Axis(values=list(np.arange(0, 10)))),
                        y=alt.Y('Total de multas $MCLP:Q', scale=alt.Scale(zero=False))
                    )

                    text = area.mark_text(
                        align='left',
                        baseline='middle',
                        dx=10,
                        dy=-10,
                        fontSize=15,
                        color='black'
                    ).encode(
                        text=alt.Text('Total de multas $MCLP:Q', format=',.0f')
                    )

                    chart_proyeccion_multas = (area + text).properties(
                        title=alt.TitleParams(
                            text='Proyección de multas diarias',
                            anchor='start',
                            subtitleColor='gray'
                        ),
                        width=1100,
                        height=300
                    )
                    st.altair_chart(chart_proyeccion_multas,use_container_width=True)
                    st.write("**Multas Mayores**")

                    df_historial_multas_grandes=df_historial_multas[df_historial_multas['Historial Multas']>=250000000]
                    #df_historial_multas_grandes.drop(["#"])
                    #df_historial_multas_grandes.drop([" "])

                    
                    #st.write(df_historial_multas_grandes)
                    df_multas_proyectadas_grandes=df_multas_proyectadas[df_multas_proyectadas['Multas Proyectadas']>=900000000]
                    columnas = ["Nota de venta", "Administrador Contratos", "Días de atraso", "Fecha NV", "Cliente", "CPE", "Historial Multas", "Multas Proyectadas", "Tipo de Entrega","Vendedor", "Total Venta (CLP)", "Total por Despachar (CLP)", "Total Generico (CLP)", "Pendiente x cerrar", "Fecha Entrega Fastpack", "Margen Previsto", "Descripción de la Venta", "Estado Pago", "Motivo Atraso", "Área de Negocios", "Tipo Oferta", "Multa se calcula sobre:", "% de Multa se aplica a:", "% Multa po Atraso", "Tope de Multa %", "Multa Saturada", "Multa en Curso", "Multa Diaria", "Estado", "Notas del Administrador"]
                    df_pegado=pd.concat([df_multas_proyectadas_grandes,df_historial_multas_grandes])
                    df_multas_mayores = df_pegado[columnas].copy() 
                    
                    #columnas_añadir = df_multas_proyectadas_grandes[columnas]
                    #df_multas_mayores = df_multas_mayores.append(columnas_añadir, ignore_index=True)

                    st.write(df_multas_mayores)                  

                    st.header("Despachos")
                    col3,col4=st.columns(2)
                    with col3:
                        st.altair_chart(chart_despachar,use_container_width=True)

                    with col4:
                        st.altair_chart(chart_total_mes,use_container_width=True)
                    st.header("Tamaño del Negocio")
                    
                    col5,col6=st.columns(2)
                    with col5:
                        st.markdown("**Porcentaje de Ingresos por Cliente**")
                        st_pyecharts(pie_ingresos)
                        st.write("**Total por Despachar $MCLP**")
                        st_pyecharts(pie_despachar)
                    with col6:
                        st.write("**Cantidad de NV por Área de Negocios**")
                        st.altair_chart(chart_nv_area, use_container_width=True)
                        st.markdown("**Total por despachar NV "+current_month_ESP+"**")
                        st_pyecharts(pie_nv)




                    #Mati presentación
                    #st_echarts(options=option, key="1")
                    st.markdown("""
                        <style>
                        :root {
                            --primary-color: ; /* Color rosa vibrante del logo */
                            --secondary-color: #4b2c94; /* Color blanco para contraste */
                            --tertiary-color: #eb098e; /* Color azul del logo */
                            --line-color: #eb098e; /* Color de la línea */
                        }

                        div[data-testid="metric-container"]:nth-child(odd) {
                            background-color: var(--primary-color);
                            border: 1px solid var();
                            color: var(--secondary-color);
                            border-left: 5px solid var(--line-color); /* Línea a la izquierda */
                        }

                        div[data-testid="metric-container"]:nth-child(even) {
                            background-color: var(--tertiary-color);
                            border: 1px solid var(--primary-color);
                            color: var(--primary-color);
                            border-left: 5px solid var(--line-color); /* Línea a la izquierda */
                        }
                        
                        div[data-testid="metric-container"] {
                            padding: 5% 5% 5% 10%;
                            border-radius: 5px;
                            overflow-wrap: break-word;
                        }
                        
                    </style>
                    """, unsafe_allow_html=True)
                    style_metric_cards()

                    



            #else:
                #st.write("Las columnas 'Nota de venta' y 'Área de Negocios' no se encontraron en el archivo cargado.")
    else:
        st.write('Cargue un informe de multas.')
else:
    st.write("Cargue las NV Abiertas")
