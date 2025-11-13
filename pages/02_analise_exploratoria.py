# pages/02_analise_exploratoria.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

# Configurações da página
st.set_page_config(
    page_title="Análise Exploratória - Crime Analytics Chicago",
    page_icon="📈",
    layout="wide"
)

# CORREÇÃO: Usar dados centralizados do app.py
if 'df' not in st.session_state:
    st.error("⚠️ Dados não carregados. Volte para a página inicial primeiro.")
    st.stop()

df = st.session_state.df

st.title("📈 Análise Exploratória de Crimes")
st.markdown("Análise aprofundada com visualizações interativas e tendências temporais.")

# Filtros na sidebar
st.sidebar.header("Filtros para Análise")

# Filtro por tipo de crime
tipos_crime = sorted(df['Primary Type'].unique())
selected_crimes = st.sidebar.multiselect(
    "Selecione os tipos de crime:",
    options=tipos_crime,
    default=tipos_crime[:3]
)

# Filtro por período
if 'Date' in df.columns:
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    
    date_range = st.sidebar.date_input(
        "Selecione o período:",
        [min_date, max_date],
        min_value=min_date,
        max_value=max_date
    )
    
    if len(date_range) == 2:
        start_date, end_date = date_range
        df_filtered = df[
            (df['Primary Type'].isin(selected_crimes)) &
            (df['Date'] >= pd.to_datetime(start_date)) &
            (df['Date'] <= pd.to_datetime(end_date))
        ]
    else:
        df_filtered = df[df['Primary Type'].isin(selected_crimes)]
else:
    df_filtered = df[df['Primary Type'].isin(selected_crimes)]

# Análise de tendência temporal
st.header("📅 Tendência Temporal de Crimes")

if 'Date' in df_filtered.columns:
    crimes_por_mes = df_filtered.groupby(pd.Grouper(key='Date', freq='M')).size().reset_index(name='Count')
    fig = px.line(crimes_por_mes, x='Date', y='Count', title='Evolução Mensal de Crimes')
    st.plotly_chart(fig, use_container_width=True)

# Heatmap de crimes por hora e dia da semana
st.header("🌓 Padrões de Criminalidade por Hora e Dia")

if 'Hour' in df_filtered.columns and 'DayOfWeek' in df_filtered.columns:
    # Criar heatmap
    heatmap_data = df_filtered.pivot_table(
        index='DayOfWeek',
        columns='Hour',
        values='Primary Type',
        aggfunc='count',
        fill_value=0
    )
    
    # Ordenar os dias da semana
    dias_ordenados = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    heatmap_data = heatmap_data.reindex(dias_ordenados, fill_value=0)
    
    fig = px.imshow(
        heatmap_data,
        title='Heatmap de Crimes: Hora vs Dia da Semana',
        labels=dict(x="Hora do Dia", y="Dia da Semana", color="Número de Crimes")
    )
    st.plotly_chart(fig, use_container_width=True)

# Distribuição geográfica
st.header("🗺️ Distribuição Geográfica")

if all(col in df_filtered.columns for col in ['Latitude', 'Longitude']):
    # Amostrar para não sobrecarregar o mapa
    df_map = df_filtered.sample(n=min(5000, len(df_filtered)))
    
    fig = px.scatter_mapbox(
        df_map,
        lat="Latitude",
        lon="Longitude",
        color="Primary Type",
        hover_name="Primary Type",
        zoom=10,
        title="Mapa de Densidade de Crimes"
    )
    fig.update_layout(mapbox_style="open-street-map")
    st.plotly_chart(fig, use_container_width=True)

# Análise de correlação
st.header("🔗 Análise de Correlação")

# Selecionar colunas numéricas
numeric_cols = df_filtered.select_dtypes(include=[np.number]).columns.tolist()

if len(numeric_cols) > 1:
    corr_matrix = df_filtered[numeric_cols].corr()
    
    fig = px.imshow(
        corr_matrix,
        title="Matriz de Correlação entre Variáveis Numéricas",
        color_continuous_scale='RdBu_r'
    )
    st.plotly_chart(fig, use_container_width=True)

# Botão para voltar à página inicial
if st.button("🏠 Voltar à Página Inicial"):
    st.switch_page("app.py")
