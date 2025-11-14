# app.py - Página Inicial do Dashboard (Versão Corrigida)
import streamlit as st
import pandas as pd
import numpy as np
import os
import glob

# Configuração da página
st.set_page_config(
    page_title="Crime Analytics Chicago", 
    page_icon="🔍", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Função corrigida para carregar dados da pasta data_splits
@st.cache_data
def load_data(years_range=None):
    """
    Carrega dados de Chicago crimes da pasta data_splits
    years_range: tuple (start_year, end_year) ou None para todos os dados
    """
    try:
        # Verificar se a pasta data_splits existe
        if not os.path.exists("data_splits"):
            st.error("❌ Pasta 'data_splits' não encontrada")
            st.info("📁 Estrutura esperada:")
            st.info("data_splits/chicago_crimes_2014_2015.csv")
            st.info("data_splits/chicago_crimes_2016_2017.csv")
            st.info("... etc")
            return pd.DataFrame()  # Retorna DataFrame vazio em vez de dados de exemplo

        # Encontrar todos os arquivos de crimes na pasta data_splits
        arquivos_encontrados = glob.glob("data_splits/chicago_crimes_*.csv")
        
        if not arquivos_encontrados:
            st.error("❌ Nenhum arquivo de dados encontrado na pasta 'data_splits'")
            return pd.DataFrame()  # Retorna DataFrame vazio
        
        st.info(f"📁 Encontrados {len(arquivos_encontrados)} arquivos na pasta data_splits")
        
        # Carregar e combinar todos os arquivos
        partes = []
        for arquivo in sorted(arquivos_encontrados):
            try:
                nome_arquivo = os.path.basename(arquivo)
                st.write(f"📂 Carregando: {nome_arquivo}")
                parte = pd.read_csv(arquivo)
                
                # Processar coluna de data
                if 'Date' in parte.columns:
                    parte['Date'] = pd.to_datetime(parte['Date'], errors='coerce')
                elif 'Data' in parte.columns:
                    parte['Date'] = pd.to_datetime(parte['Data'], errors='coerce')
                    parte = parte.drop('Data', axis=1)
                
                # Adicionar coluna de ano se não existir
                if 'Year' not in parte.columns and 'Date' in parte.columns:
                    parte['Year'] = parte['Date'].dt.year
                
                partes.append(parte)
                st.success(f"✅ {nome_arquivo} - {len(parte):,} registros")
                
            except Exception as e:
                st.warning(f"⚠️ Erro ao carregar {arquivo}: {e}")
                continue
        
        if not partes:
            st.error("❌ Nenhum arquivo foi carregado com sucesso")
            return pd.DataFrame()  # Retorna DataFrame vazio
        
        # Combinar todos os dados
        df_completo = pd.concat(partes, ignore_index=True)
        st.success(f"🎉 Dataset completo carregado: {len(df_completo):,} registros")
        
        # Aplicar filtro de período se especificado
        if years_range is not None:
            start_year, end_year = years_range
            if 'Year' in df_completo.columns:
                mask = (df_completo['Year'] >= start_year) & (df_completo['Year'] <= end_year)
                df_completo = df_completo[mask].copy()
                st.success(f"📅 Filtrado para {start_year}-{end_year}: {len(df_completo):,} registros")
        
        return df_completo
        
    except Exception as e:
        st.error(f"❌ Erro inesperado ao carregar dados: {e}")
        return pd.DataFrame()  # Retorna DataFrame vazio
    
# Função para verificar estrutura de arquivos (para debug)
def verificar_estrutura_arquivos():
    """Verifica se os arquivos estão no lugar certo"""
    st.sidebar.header("🔍 Verificação de Arquivos")
    
    if os.path.exists("data_splits"):
        arquivos = os.listdir("data_splits")
        csv_files = [f for f in arquivos if f.endswith('.csv')]
        st.sidebar.success(f"✅ Pasta data_splits encontrada")
        st.sidebar.write(f"Arquivos CSV: {len(csv_files)}")
        for arquivo in sorted(csv_files):
            st.sidebar.write(f"• {arquivo}")
    else:
        st.sidebar.error("❌ Pasta data_splits não encontrada")

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

# Verificação de arquivos (para debug)
verificar_estrutura_arquivos()

# Carregar dados uma vez para toda a aplicação
if 'df' not in st.session_state:
    with st.spinner("Carregando dados de 2014-2024..."):
        st.session_state.df = load_data(selected_period)

# Atualizar dados se o período mudar
if st.sidebar.button("🔄 Atualizar Dados"):
    with st.spinner("Atualizando dados..."):
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
        if 'Date' in st.session_state.df.columns and not st.session_state.df['Date'].isna().all():
            min_date = st.session_state.df['Date'].min()
            max_date = st.session_state.df['Date'].max()
            if pd.notna(min_date) and pd.notna(max_date):
                date_range = f"{min_date.strftime('%Y-%m')} a {max_date.strftime('%Y-%m')}"
                st.metric("Período", date_range)
            else:
                st.metric("Período", "Datas inválidas")
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
        
        if 'Date' in df.columns and not df['Date'].isna().all():
            min_date = df['Date'].min()
            max_date = df['Date'].max()
            if pd.notna(min_date) and pd.notna(max_date):
                st.write(f"📅 **Período**: {min_date.strftime('%d/%m/%Y')} a {max_date.strftime('%d/%m/%Y')}")
            else:
                st.write("📅 **Período**: Datas inválidas")
            
        if 'Primary Type' in df.columns:
            top_crimes = df['Primary Type'].value_counts().head(3)
            st.write("🔍 **Top 3 crimes**:")
            for crime, count in top_crimes.items():
                st.write(f"   - {crime}: {count:,}")
                
        st.write(f"💾 **Fonte**: {selected_period_label}")