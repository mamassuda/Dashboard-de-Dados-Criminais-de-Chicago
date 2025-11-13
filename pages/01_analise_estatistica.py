# pages/01_analise_estatistica.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# Configuração da página
st.set_page_config(
    page_title="Análise Estatística - Crime Analytics Chicago",
    page_icon="📊",
    layout="wide"
)

# CORREÇÃO: Usar dados centralizados do app.py
if 'df' not in st.session_state:
    st.error("⚠️ Dados não carregados. Volte para a página inicial primeiro.")
    st.stop()

df = st.session_state.df

st.title("📊 Análise Estatística de Crimes")
st.markdown("Explore insights estatísticos sobre os dados de criminalidade de Chicago.")

# Sidebar com filtros
st.sidebar.header("Filtros")

# Filtro por tipo de crime
tipos_crime = sorted(df['Primary Type'].unique())
selected_crimes = st.sidebar.multiselect(
    "Tipos de Crime",
    options=tipos_crime,
    default=tipos_crime[:5]
)

# Filtro por data
if 'Date' in df.columns:
    min_date = df['Date'].min()
    max_date = df['Date'].max()
    
    date_range = st.sidebar.date_input(
        "Período",
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

# Métricas principais
st.header("📈 Métricas Principais")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total de Crimes", len(df_filtered))

with col2:
    st.metric("Tipos de Crime", df_filtered['Primary Type'].nunique())

with col3:
    arrest_rate = (df_filtered['Arrest'].sum() / len(df_filtered)) * 100
    st.metric("Taxa de Prisão", f"{arrest_rate:.1f}%")

with col4:
    domestic_rate = (df_filtered['Domestic'].sum() / len(df_filtered)) * 100
    st.metric("Taxa de Crimes Domésticos", f"{domestic_rate:.1f}%")

# Visualizações
st.header("📊 Visualizações")

col1, col2 = st.columns(2)

with col1:
    # Crimes por tipo
    crimes_por_tipo = df_filtered['Primary Type'].value_counts().head(10)
    fig = px.bar(
        crimes_por_tipo,
        title="Top 10 Crimes por Frequência",
        labels={'value': 'Quantidade', 'index': 'Tipo de Crime'}
    )
    st.plotly_chart(fig, use_container_width=True)

with col2:
    # Distribuição por hora do dia
    if 'Hour' in df_filtered.columns:
        crimes_por_hora = df_filtered['Hour'].value_counts().sort_index()
        fig = px.line(
            crimes_por_hora,
            title="Crimes por Hora do Dia",
            labels={'value': 'Quantidade', 'index': 'Hora'}
        )
        st.plotly_chart(fig, use_container_width=True)

# Tabela de dados
st.header("📋 Dados Detalhados")
st.dataframe(df_filtered.head(1000), use_container_width=True)

# Botão para voltar à página inicial
if st.button("🏠 Voltar à Página Inicial"):
    st.switch_page("app.py")
