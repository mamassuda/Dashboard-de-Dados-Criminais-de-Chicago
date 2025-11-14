# app.py - Página Inicial do Dashboard (Versão Otimizada com Divisão por Anos)
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

# Função para criar dados de exemplo (fallback)
def create_sample_data():
    """Cria dataset de demonstração caso os arquivos principais não estejam disponíveis"""
    st.info("📝 Criando dataset de demonstração...")
    dates = pd.date_range('2020-01-01', periods=365*3, freq='D')
    crimes = ['THEFT', 'BATTERY', 'CRIMINAL DAMAGE', 'NARCOTICS', 'ASSAULT', 'BURGLARY', 'ROBBERY']
    districts = ['001', '002', '003', '004', '005', '006', '007', '008', '009', '010']
    
    data = []
    for date in dates:
        daily_crimes = np.random.randint(50, 200)
        for _ in range(daily_crimes):
            data.append({
                'Date': date,
                'Primary Type': np.random.choice(crimes),
                'District': np.random.choice(districts),
                'Latitude': np.random.uniform(41.7, 42.0),
                'Longitude': np.random.uniform(-87.9, -87.6),
                'Arrest': np.random.choice([True, False]),
                'Year': date.year
            })
    
    return pd.DataFrame(data)

# Função otimizada para carregar dados com divisão por anos
@st.cache_data
def load_data(years_range=None):
    """
    Carrega dados de Chicago crimes de forma otimizada.
    years_range: tuple (start_year, end_year) ou None para dados recentes
    """
    # Se não especificar anos, carrega os mais recentes (2022-2024)
    if years_range is None:
        years_range = (2022, 2024)
    
    start_year, end_year = years_range
    
    try:
        # CORREÇÃO: Usar o caminho correto da pasta data_splits
        filename = f'data_splits/chicago_crimes_{start_year}_{end_year}.csv'
        st.info(f"📊 Carregando dados de {start_year}-{end_year}...")
        df = pd.read_csv(filename)
        
        # Garantir que a coluna de data está no formato correto
        if 'Date' in df.columns:
            df['Date'] = pd.to_datetime(df['Date'])
        elif 'Data' in df.columns:
            df['Date'] = pd.to_datetime(df['Data'])
            df = df.drop('Data', axis=1)
        
        # Adicionar coluna de ano se não existir
        if 'Year' not in df.columns:
            df['Year'] = df['Date'].dt.year
            
        st.success(f"✅ Dados de {start_year}-{end_year} carregados! Total: {len(df):,} registros")
        return df
        
    except FileNotFoundError:
        st.error(f"❌ Arquivo para {start_year}-{end_year} não encontrado.")
        # Usar dados de exemplo como último recurso
        return create_sample_data()

# Título principal
st.title("🔍 Sistema de Análise de Crimes de Chicago")
st.markdown("### Selecione uma das áreas abaixo para explorar os dados de criminalidade")
st.markdown("---")

# Sidebar com seletor de período
st.sidebar.header("📅 Configuração de Período")

# Opções de períodos (baseado na divisão 2 em 2 anos)
period_options = {
    "Dados Completos (2014-2024)": None,
    "Período Recente (2022-2024)": (2022, 2024),
    "2020-2021": (2020, 2021),
    "2018-2019": (2018, 2019), 
    "2016-2017": (2016, 2017),
    "2014-2015": (2014, 2015)
}

selected_period_label = st.sidebar.selectbox(
    "Selecione o período para análise:",
    list(period_options.keys())
)

# Obter o range de anos selecionado
selected_period = period_options[selected_period_label]

# Carregar dados uma vez para toda a aplicação
if 'df' not in st.session_state:
    st.session_state.df = load_data(selected_period)

# Atualizar dados se o período mudar
if st.sidebar.button("🔄 Atualizar Dados"):
    st.session_state.df = load_data(selected_period)
    st.rerun()

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

# Informações dos dados carregados
st.markdown("---")
st.markdown("### 📋 Informações do Dataset Carregado")

if not st.session_state.df.empty:
    col_info1, col_info2, col_info3, col_info4 = st.columns(4)
    
    with col_info1:
        st.metric("Total de Registros", f"{len(st.session_state.df):,}")
    
    with col_info2:
        if 'Date' in st.session_state.df.columns:
            date_range = f"{st.session_state.df['Date'].min().strftime('%Y-%m')} a {st.session_state.df['Date'].max().strftime('%Y-%m')}"
            st.metric("Período", date_range)
        else:
            st.metric("Período", "Não disponível")
    
    with col_info3:
        if 'Primary Type' in st.session_state.df.columns:
            crime_types = st.session_state.df['Primary Type'].nunique()
            st.metric("Tipos de Crime", crime_types)
        else:
            st.metric("Tipos de Crime", "N/A")
    
    with col_info4:
        if 'District' in st.session_state.df.columns:
            districts = st.session_state.df['District'].nunique()
            st.metric("Distritos", districts)
        else:
            st.metric("Distritos", "N/A")

# Informações adicionais
st.markdown("---")
st.markdown("""
### 📋 Sobre o Sistema
Este sistema de análise permite explorar dados históricos de criminalidade de Chicago através de diferentes perspectivas.

**Fonte dos dados**: Chicago Police Department
            
**Desenvolvido por**: Matheus Henrique Massuda

**Estratégia de dados**: Divisão por períodos de 2 anos para otimização de performance
""")

# Verificação de dados
st.sidebar.success("✅ Aplicação carregada com sucesso!")

# Mostrar informações dos dados no sidebar
with st.sidebar.expander("ℹ️ Detalhes dos Dados Carregados"):
    df = st.session_state.df
    if not df.empty:
        st.write(f"📈 **Total de registros**: {len(df):,}")
        
        if 'Date' in df.columns:
            st.write(f"📅 **Período**: {df['Date'].min().strftime('%d/%m/%Y')} a {df['Date'].max().strftime('%d/%m/%Y')}")
            
        if 'Primary Type' in df.columns:
            top_crimes = df['Primary Type'].value_counts().head(3)
            st.write("🔍 **Top 3 crimes**:")
            for crime, count in top_crimes.items():
                st.write(f"   - {crime}: {count:,}")
                
        st.write(f"💾 **Fonte**: {selected_period_label}")