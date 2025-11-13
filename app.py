# app.py - Página Inicial do Dashboard (Versão Otimizada)
import streamlit as st
import pandas as pd
import numpy as np

# Configuração da página
st.set_page_config(
    page_title="Crime Analytics Chicago", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Função otimizada para carregar dados
@st.cache_data
def load_data():
    try:
        st.info("📊 Carregando base de dados completa...")
        df = pd.read_csv('chicago_crimes.csv')
        st.success(f"✅ Dados carregados com sucesso! Total de registros: {len(df):,}")
        return df
    except FileNotFoundError:
        st.error("❌ Arquivo 'chicago_crimes.csv' não encontrado.")
        st.info("📝 Criando dataset de demonstração...")
        # Dataset mínimo para evitar erros
        return pd.DataFrame({
            'Data': pd.date_range('2023-01-01', periods=100),
            'Primary Type': ['ROUBO', 'FURTO', 'AGRESSAO'] * 33,
            'Community Area': ['LOOP', 'NORTH', 'SOUTH'] * 33,
            'Hora': np.random.randint(0, 24, 100),
            'Latitude': np.random.uniform(41.7, 42.0, 100),
            'Longitude': np.random.uniform(-87.9, -87.6, 100)
        })

# Título principal
st.title("🔍 Sistema de Análise de Crimes de Chicago")
st.markdown("### Selecione uma das áreas abaixo para explorar os dados de criminalidade")
st.markdown("---")

# Criar os 4 cards interativos
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 📊 Análise Estatística")
    st.markdown("Navegue, filte e explore o banco de dados completo de crimes")
    if st.button("Acessar Análise Estatística", key="btn1", use_container_width=True):
        st.switch_page("pages/01_analise_estatistica.py")

with col2:
    st.markdown("### 📈 Análise Exploratória")
    st.markdown("Visualizações avançadas, tendências e métricas detalhadas")
    if st.button("Acessar Análise Exploratória", key="btn2", use_container_width=True):
        st.switch_page("pages/02_analise_exploratoria.py")

with col3:
    st.markdown("### 🔮 Predição de Dados")
    st.markdown("Modelos de machine learning e previsões futuras")
    if st.button("Acessar Predição de Dados", key="btn3", use_container_width=True):
        st.switch_page("pages/03_predicao_crimes.py")

with col4:
    st.markdown("### 🗺️ Análise Geográfica")
    st.markdown("Mapas interativos, hotspots e análise por região")
    if st.button("Acessar Análise Geográfica", key="btn4", use_container_width=True):
        st.switch_page("pages/04_analise_espacial.py")

# Informações adicionais
st.markdown("---")
st.markdown("""
### 📋 Sobre o Sistema
Este sistema de análise permite explorar dados históricos de criminalidade de Chicago através de diferentes perspectivas.

**Fonte dos dados**: Chicago Police Department
            
**Desenvolvido por**: Matheus Henrique Massuda
""")

# Verificação de dados
st.sidebar.success("✅ Aplicação carregada com sucesso!")

# Mostrar informações dos dados
with st.sidebar.expander("ℹ️ Informações dos Dados"):
    try:
        df = load_data()
        if not df.empty:
            st.write(f"📈 Total de registros: {len(df):,}")
            
            # Verifica colunas disponíveis para mostrar informações
            if 'Data' in df.columns:
                st.write(f"📅 Período: {df['Data'].min()} a {df['Data'].max()}")
            elif 'Date' in df.columns:
                st.write(f"📅 Período: {df['Date'].min()} a {df['Date'].max()}")
                
            if 'Primary Type' in df.columns:
                st.write(f"🔒 Tipos de crime: {df['Primary Type'].nunique()}")
                
            st.write("💾 Fonte: chicago_crimes.csv")
    except Exception as e:
        st.write("⚠️ Carregando dados de demonstração")