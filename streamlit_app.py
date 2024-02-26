import streamlit as st
import pandas as pd
import openpyxl
import altair as alt
import numpy as np
import locale
import math
from streamlit_echarts import st_pyecharts
from pyecharts import options as opts
from pyecharts.charts import Pie
from datetime import datetime


# Configurar la página
st.set_page_config(
    page_title="Reporte GCP",
    page_icon="https://media.licdn.com/dms/image/D4D0BAQEMY2nsK6QC7Q/company-logo_200_200/0/1683580839423/fastpack_logo?e=2147483647&v=beta&t=bALnnuVtSeBck7D1OILF6f88twjf7jGUsLSO0A4atVo",
)


st.title('Análisis NV Abiertas')
#st.sidebar.title('Análisis de Producción')
# Agregar la imagen al inicio del sidebar

image = 'https://www.portalminero.com/wp/wp-content/uploads/subidos/proveedor/608_60457157.png'
st.sidebar.image(image)
st.sidebar.title('Análisis de Producción')
uploaded_file = st.sidebar.file_uploader("Carga las notas de ventas abiertas", type=['xlsx'])

uploaded_file2 = st.sidebar.file_uploader("Carga Informe de Multas", type=['xlsx'])


if uploaded_file is not None:
    if  uploaded_file2 is not None:
        df = pd.read_excel(uploaded_file, engine='openpyxl')
        dfm = pd.read_excel(uploaded_file2, engine='openpyxl')
        # Asegurarse de que 'Fecha NV' es de tipo datetime
        df['Fecha NV'] = pd.to_datetime(df['Fecha NV'])

        # Ajustar las fechas al mediodía
        df['Fecha NV'] = df['Fecha NV'].apply(lambda dt: dt.replace(hour=12))

        df['CPE'] = pd.to_datetime(df['CPE'])

        # Ajustar las fechas al mediodía
        df['CPE'] = df['CPE'].apply(lambda dt: dt.replace(hour=12))

        dfm['Fecha Guia'] = pd.to_datetime(dfm['Fecha Guia'])

        # Ajustar las fechas al mediodía
        dfm['Fecha Guia'] = dfm['Fecha Guia'].apply(lambda dt: dt.replace(hour=12))

        dfm['CPE Linea'] = pd.to_datetime(dfm['CPE Linea'])

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


        
        # Crear un filtro en el sidebar de Streamlit
        areas_negocios = st.sidebar.multiselect(
            'Unidad de Negocio',
            df['Unidad de Negocio'].unique()
        )
        # Definir el mapeo de 'Área de Negocios' a 'Unidad de Negocio'


        # Verificar si se ha seleccionado alguna área de negocio
        if not areas_negocios:
            st.write('Seleccione un Área de Negocios.')
        else:
                
            # Filtrar el DataFrame en base a las Áreas de Negocios seleccionadas
            df_filtrado = df[df['Unidad de Negocio'].isin(areas_negocios)]
            df = df_filtrado

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
                if df_items is not None:
                    df_items[['Multa Saturada', 'Multa en Curso', 'Multa Diaria', 'Multa Despachada']] = df_items.apply(calcular_multas, axis=1, result_type='expand')
                    df_items['Días de atraso']=df_items['Días de atraso'].abs()

                #st.write(df_items)

                # Filtrar el DataFrame para solo los casos donde 'Colores Semaforo' es 'Rojo'
                df_rojo = df[(df['Colores Semaforo'] == 'Rojo') & (df['Multa en Curso'] > 100000)]

                # Crear una columna con colores únicos para cada 'Nota de venta'
                df_rojo['Color'] = df_rojo['Nota de venta'].map(dict(zip(df_rojo['Nota de venta'].unique(), range(df_rojo['Nota de venta'].nunique()))))

                # Ordenar el DataFrame por 'Multa en Curso' de mayor a menor
                df_rojo = df_rojo.sort_values('Multa en Curso', ascending=False)
                df_rojo['Días de atraso'] = df_rojo['Ahead / Delay'].abs()

                df_filtrado_rojo = df_rojo[df_rojo['Multa se calcula sobre:'] == 'Valor total de orden de Compra']
                if df_items is not None:
                    df_filtrado_rojo['Suma Multas']=df_filtrado_rojo['Multa en Curso'].sum()+df_items.loc[df_items['Multa en Curso'].notnull(), 'Multa en Curso'].sum()
                else:
                    df_filtrado_rojo['Suma Multas']=df_filtrado_rojo['Multa en Curso'].sum()
                #df_items['Suma Multas']=df_items['Multa en Curso'].sum()
                # Calcular la suma de las multas en curso y las multas saturadas
                if df_items is not None:
                    suma_multas_en_curso = df_items.loc[df_items['Multa en Curso'].notnull(), 'Multa en Curso'].sum()+df_filtrado_rojo['Multa en Curso'].sum()
                    suma_multas_saturadas = df_items.loc[df_items['Multa Saturada'].notnull(), 'Multa Saturada'].sum()
                if df_items is not None:
                    # Asignar estos valores a la nueva columna 'Suma Multas'
                    df_items.loc[df_items['Multa en Curso'].notnull(), 'Suma Multas'] = suma_multas_en_curso
                    #df_items.loc[df_items['Multa Saturada'].notnull(), 'Suma Multas'] = suma_multas_saturadas


                df_combinado = pd.concat([df_filtrado_rojo, df_items])
                df_combinado = df_combinado[df_combinado['Multa en Curso'] > 0]
                
                # Asegurarse de que 'Fecha NV' es de tipo datetime
                df_combinado['Fecha NV'] = pd.to_datetime(df_combinado['Fecha NV'])

                # Ajustar las fechas al mediodía
                df_combinado['Fecha NV'] = df_combinado['Fecha NV'].apply(lambda dt: dt.replace(hour=12))

                df_combinado['CPE'] = pd.to_datetime(df_combinado['CPE'])

                # Ajustar las fechas al mediodía
                df_combinado['CPE'] = df_combinado['CPE'].apply(lambda dt: dt.replace(hour=12))

                if df_items is not None:
                    df_combinado.loc[df_combinado['Fecha Guia'].notnull(), 'CPE'] = 'Despachado'
                df_combinado['Estado'] = df_combinado.apply(lambda x: 'Despachado' if pd.notnull(x['Fecha Guia']) or x['Total por Despachar (CLP)'] < 1 else 'Pendiente', axis=1)

                df_combinado = df_combinado[df_combinado['Multa en Curso'] > 100000]
                #st.write(df_combinado)
                # Crear una columna de orden para el estado
                orden_estado = {'Pendiente': 0, 'Despachado': 1}
                df_combinado['Orden Estado'] = df_combinado['Estado'].map(orden_estado)

                # Ordenar el DataFrame
                df_combinado.sort_values(by=['Nota de venta', 'Orden Estado'], ascending=[True, False], inplace=True)
                if df_combinado['Multa en Curso'].sum()>0:
                    # Mostrar el gráfico
                    chart = alt.Chart(df_combinado).mark_bar().encode(
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
                    chart
                else:
                    st.header('Sin multas en curso.')
                    st.write(" ")
                df_naranjo=df[(df['Colores Semaforo'] == 'Naranjo') & (df['Multa Saturada'] > 100000)]
                # Crear una columna con colores únicos para cada 'Nota de venta'
                df_naranjo['Color'] = df_naranjo['Nota de venta'].map(dict(zip(df_naranjo['Nota de venta'].unique(), range(df_naranjo['Nota de venta'].nunique()))))
                df_naranjo['Días de atraso'] = df_naranjo['Ahead / Delay'].abs()
                

                # Ordenar el DataFrame por 'Multa en Curso' de mayor a menor
                df_naranjo = df_naranjo.sort_values('Multa Saturada', ascending=False)
                df_naranjo = df_naranjo[df_naranjo['Multa se calcula sobre:'] == 'Valor total de orden de Compra']
                df_naranjo['Suma Multas']=df_naranjo['Multa Saturada'].sum()
    
                df_items['Días de atraso']=df_items['Días de atraso'].abs()
                df_combinado2 = pd.concat([df_naranjo, df_items])
                df_combinado2 = df_combinado2[df_combinado2['Multa Saturada'] > 100000]
                df_combinado2['Suma Multas']=df_combinado2['Multa Saturada'].sum()
                            # Asegurarse de que 'Fecha NV' es de tipo datetime
                df_combinado2['Fecha NV'] = pd.to_datetime(df_combinado2['Fecha NV'])

                # Ajustar las fechas al mediodía
                df_combinado2['Fecha NV'] = df_combinado2['Fecha NV'].apply(lambda dt: dt.replace(hour=12))

                df_combinado2['CPE'] = pd.to_datetime(df_combinado2['CPE'])

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

                
                #st.write(df_combinado2)
                chart = alt.Chart(df_combinado2).mark_bar().encode(
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
                chart
                df_unificado=pd.concat([df_combinado, df_combinado2])
                #st.write(df_unificado)

                
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
                Suma_multas_historial = int(df_historial_multas['Historial Multas'].sum())
                suma_total_venta_historial = df_historial_multas['Total Venta (CLP)'].sum()

                # Calcula el porcentaje
                porcentaje = (Suma_multas_historial / suma_total_venta_historial) * 100

                # Crea la tarjeta de métricas
                if df_historial_multas.empty==False:
                    chart = alt.Chart(df_historial_multas).mark_bar().encode(
                        x=alt.X('Nota de venta:N', sort='-y'),
                        y=alt.Y('Historial Multas:Q', title='Valor Multa(CLP)', axis=alt.Axis(format=',d')),
                        color=alt.Color('Cliente:N', legend=alt.Legend(title='Cliente')),
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
                    height=500,width=900,     
                        title='Historial de Multas'
                    ).interactive()
                    st.metric(label="Total Historial de Multas (CLP)", value=f"{Suma_multas_historial:,}", delta=f"-{porcentaje:.2f}%")

                    chart
                else:
                    st.header("Sin Historial de Multas")
                df_multas_proyectadas=df_unificado[df_unificado['Multas Proyectadas']>0]

                # Calcula las sumas
                Suma_multas_proyectadas = int(df_multas_proyectadas['Multas Proyectadas'].sum())
                suma_total_venta_proyectadas = df_multas_proyectadas['Total Venta (CLP)'].sum()

                # Calcula el porcentaje
                porcentaje = (Suma_multas_proyectadas / suma_total_venta_proyectadas) * 100

                # Crea la tarjeta de métricas
                st.metric(label="Multas Totales Proyectadas", value=f"{Suma_multas_proyectadas:,}", delta=f"-{porcentaje:.2f}%")
                chart = alt.Chart(df_multas_proyectadas).mark_bar().encode(
                    x=alt.X('Nota de venta:N', sort='-y'),
                    y=alt.Y('Multas Proyectadas:Q', title='Valor Multa (CLP)', axis=alt.Axis(format=',d')),
                    color=alt.Color('Cliente:N', legend=alt.Legend(title='Cliente')),
                    tooltip=[
                        'Nota de venta',
                        alt.Tooltip('Multas Proyectadas', title='Valor Multa (CLP)', format=',d'),
                        alt.Tooltip('Días de atraso', title='Días de atraso', format=',d'),
                        alt.Tooltip('Administrador Contratos', title='Administrador de Contrato'),
                        alt.Tooltip('Total Venta (CLP)', title='Total Venta (CLP)', format=',d'),
                        alt.Tooltip('Total por Despachar (CLP)', title='Total Por Despachar', format=',d'),
                        alt.Tooltip('Cliente', title='Cliente'),
                        alt.Tooltip('CPE', title='CPE'),
                        alt.Tooltip('Fecha NV', title='Fecha NV'),
                        alt.Tooltip('Número de artículo', title='TAG'),
                        alt.Tooltip('Estado', title='Estatus'),
                        alt.Tooltip('Pendiente x cerrar', title='Pendiente por cerrar'),

                    ]
                ).properties(
                height=500,width=900,     
                    title='Multas Proyectadas'
                ).interactive()
                chart

            df['CPE'] = pd.to_datetime(df['CPE'])

            # Crea una nueva columna para el mes
            df['Mes'] = df['CPE'].dt.month

            # Crea una lista de opciones de meses
            meses = sorted(df['Mes'].unique())

            # Crea una selección para cada mes
            selecciones = [alt.selection_single(fields=['Mes'], name=str(mes)) for mes in meses]
            # Crear el gráfico de tipo carta Gantt


            # Crea el gráfico de barras apiladas
            df_despachar = df[df['Total por Despachar (CLP)'] > 1000]
            chart = alt.Chart(df_despachar).mark_bar().encode(
                x='CPE:T',
                y='Total por Despachar (CLP):Q',
                color='Cliente:N',
                tooltip=['Nota de venta:N', 'Cliente:N',
                        alt.Tooltip('Total por Despachar (CLP)', title='Por Despachar', format=',d'),
                        alt.Tooltip('CPE', title='Fecha de entrega')],
                order=alt.Order('Total por Despachar (CLP):Q', sort='descending')
            ).properties(
                height=500, width=900,
                title='Total por despachar según CPE'
            ).interactive()

            # Agrega las selecciones al gráfico
            for seleccion in selecciones:
                chart = chart.add_selection(
                    seleccion
                ).transform_filter(
                    seleccion
                )

            # Muestra el gráfico
            chart
            # Convierte la columna 'CPE' a datetime
            #df['CPE'] = pd.to_datetime(df['CPE'])

            # Obtiene el año y mes actual
            current_year = datetime.now().year
            current_month = datetime.now().month
            # Configura el idioma a español
            locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')

            # Obtiene el mes actual en español
            current_month_ESP = datetime.now().strftime('%B')

            # Filtra el DataFrame para que solo contenga los datos del mes actual
            df_current_month = df_despachar[(df_despachar['CPE'].dt.year == current_year) & (df_despachar['CPE'].dt.month == current_month)]
            if not df_current_month.empty:

                chart = alt.Chart(df_current_month).mark_bar().encode(
                    x=alt.X('CPE:T', axis=alt.Axis(format='%d')),
                    y='Total por Despachar (CLP):Q',
                    color='Cliente:N',
                    tooltip=['Nota de venta:N', 'Cliente:N',
                    alt.Tooltip('Total por Despachar (CLP)', title='Por Despachar', format=',d'),
                    alt.Tooltip('CPE', title='Fecha de entrega') ],
                    order=alt.Order('Total por Despachar (CLP):Q', sort='descending')
                ).properties(
                height=500,width=900, 
                    title='Total por despachar para ' +str(current_month_ESP)+' según CPE'
                )

                # Muestra el gráfico
                chart



            # Primero, calcula la suma total de "Total Venta (CLP)" para cada cliente
            df_sum = df.groupby('Cliente')['Total Venta (CLP)'].sum().reset_index()

            # Luego, crea una lista de diccionarios donde cada diccionario representa un cliente y su suma total
            data = df_sum.to_dict('records')

            # Primero, calcula la suma total de "Total Venta (CLP)" para cada cliente
            df_sum = df.groupby('Cliente')['Total Venta (CLP)'].sum().reset_index()

            # Ahora, puedes usar ECharts para crear tu gráfico
            c = (
                Pie()
                .add("", [list(z) for z in zip(df_sum['Cliente'], df_sum['Total Venta (CLP)'])])
                .set_global_opts(title_opts=opts.TitleOpts(title="Ingresos por Clientes"),
                                legend_opts=opts.LegendOpts(is_show=False)) # Oculta la leyenda de colores
                .set_series_opts(label_opts=opts.LabelOpts(formatter="{b}"), # Muestra solo el nombre de la compañía
                                tooltip_opts=opts.TooltipOpts(formatter="{b}: {c} CLP")) # Muestra el número solo al pasar el mouse por encima
            )

            st_pyecharts(c)
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
                
                # Crea un DataFrame con la cuenta de las notas de venta por área de negocios
                count_df = df_nv.groupby(['Nota de venta', 'Área de Negocios']).size().reset_index(name='Número de NV')

                # Crea el gráfico de barras con Altair
                chart = alt.Chart(count_df).mark_bar().encode(
                    x='Área de Negocios',
                    y='Número de NV',
                    color=alt.Color('Área de Negocios', scale=alt.Scale(scheme='category20')),
                    tooltip=['Nota de venta', 'Área de Negocios', 'Número de NV']).properties(
                height=500,width=900 
                
                )

                st.altair_chart(chart, use_container_width=True)
                
                

            

            else:
                st.write("Las columnas 'Nota de venta' y 'Área de Negocios' no se encontraron en el archivo cargado.")
    else:
        st.write('Cargue un informe de multas.')
else:
    st.write("Cargue las NV Abiertas")
