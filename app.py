# app.py - Página Inicial do Dashboard (Versão Simplificada)
import streamlit as st

# Configuração da página
st.set_page_config(
    page_title="Crime Analytics Chicago", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Título principal
st.title("🔍 Sistema de Análise de Crimes de Chicago")
st.markdown("### Selecione uma das áreas abaixo para explorar os dados de criminalidade")
st.markdown("---")

# Criar os 4 cards interativos (versão simplificada sem CSS)
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("### 📊 Análise Estatística")
    st.markdown("Navegue, filtre e explore o banco de dados completo de crimes")
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

# Verificação simples
st.sidebar.success("✅ Aplicação carregada com sucesso!")