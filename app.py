# app.py - Página Inicial do Dashboard
import streamlit as st
import pandas as pd

# Para inicar o STREAMLIT: streamlit run app.py  (usar no terminal)

# Configuração da página
st.set_page_config(
    page_title="Crime Analytics Chicago", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# CSS personalizado para os cards
st.markdown("""
<style>
    .card {
        border: 2px solid #e6e6e6;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        cursor: pointer;
        height: 200px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        transition: all 0.3s ease;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
    }
    .card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 15px rgba(0, 0, 0, 0.2);
        border-color: #4CAF50;
    }
    .card h3 {
        font-size: 48px;
        margin-bottom: 10px;
    }
    .card h4 {
        color: #2c3e50;
        margin-bottom: 10px;
    }
    .card p {
        color: #7f8c8d;
        font-size: 14px;
        line-height: 1.4;
    }
</style>
""", unsafe_allow_html=True)

# Título principal
st.title("🔍 Sistema de Análise de Crimes de Chicago")
st.markdown("### Selecione uma das áreas abaixo para explorar os dados de criminalidade")
st.markdown("---")

# Criar os 4 cards interativos
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown("""
    <div class="card">
        <h3>📊</h3>
        <h4>Análise Estatística</h4>
        <p>Navegue, filtre e explore o banco de dados completo de crimes</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Acessar →", key="btn1", use_container_width=True):
        st.switch_page("pages/01_analise_estatistica.py")

with col2:
    st.markdown("""
    <div class="card">
        <h3>📈</h3>
        <h4>Análise Exploratória</h4>
        <p>Visualizações avançadas, tendências e métricas detalhadas</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Acessar →", key="btn2", use_container_width=True):
        st.switch_page("pages/02_analise_exploratoria.py")

with col3:
    st.markdown("""
    <div class="card">
        <h3>🔮</h3>
        <h4>Predição de Dados</h4>
        <p>Modelos de machine learning e previsões futuras</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Acessar →", key="btn3", use_container_width=True):
        st.switch_page("pages/03_predicao_crimes.py")

with col4:
    st.markdown("""
    <div class="card">
        <h3>🗺️</h3>
        <h4>Análise Geográfica</h4>
        <p>Mapas interativos, hotspots e análise por região</p>
    </div>
    """, unsafe_allow_html=True)
    if st.button("Acessar →", key="btn4", use_container_width=True):
        st.switch_page("pages/04_analise_espacial.py")

# Informações adicionais
st.markdown("---")
st.markdown("""
### 📋 Sobre o Sistema
Este sistema de análise permite explorar dados históricos de criminalidade de Chicago através de diferentes perspectivas:

- **Análise Estatística**: Filtros interativos e visualização tabular
- **Análise Exploratória**: Gráficos, tendências e métricas detalhadas  
- **Predição de Dados**: Modelos preditivos e análise de padrões futuros
- **Análise Geográfica**: Mapas de calor e distribuição espacial

**Fonte dos dados**: Chicago Police Department
            
**Desenvolvido por**: Matheus Henrique Massuda
""")