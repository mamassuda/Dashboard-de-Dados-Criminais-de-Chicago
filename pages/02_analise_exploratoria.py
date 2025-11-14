# 02_analise_estatistica.py - VERSÃO CORRIGIDA
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Análise Exploratória - Crimes Chicago", 
    page_icon="📈", 
    layout="wide"
)

# Título e descrição
st.title("Análise Exploratória dos Padrões de Crimes em Chicago")
st.markdown("""
### Análise Exploratória de Série Temporal
Explore padrões temporais, sazonalidade e tendências dos crimes ao longo do tempo.
""")

# Função para criar dados de exemplo (fallback)
def create_sample_data():
    """Cria dataset de demonstração caso os arquivos principais não estejam disponíveis"""
    st.info("📝 Criando dataset de demonstração...")
    dates = pd.date_range('2014-01-01', periods=365*11, freq='D')  # 2014-2024
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

# Carregar dados - USANDO A MESMA LÓGICA DO APP PRINCIPAL
@st.cache_data
def load_data(years_range=None):
    """
    Carrega dados de Chicago crimes de forma otimizada.
    years_range: tuple (start_year, end_year) ou None para dados recentes (2022-2024)
    """
    # Se não especificar anos, carrega os mais recentes (2022-2024)
    if years_range is None:
        years_range = (2022, 2024)
    
    start_year, end_year = years_range
    
    try:
        # Tentar carregar arquivo específico do período
        filename = f'chicago_crimes_{start_year}_{end_year}.csv'
        st.info(f"📊 Carregando dados de {start_year}-{end_year}...")
        df = pd.read_csv(filename)
        
    except FileNotFoundError:
        st.warning(f"⚠️ Arquivo para {start_year}-{end_year} não encontrado. Tentando alternativas...")
        
        # Tentar carregar arquivo completo como fallback
        try:
            df = pd.read_csv('chicago_crimes.csv')
            # Filtrar pelo período solicitado
            if 'Date' in df.columns:
                df['Date'] = pd.to_datetime(df['Date'])
                df['Year'] = df['Date'].dt.year
                mask = (df['Year'] >= start_year) & (df['Year'] <= end_year)
                df = df[mask].copy()
            elif 'Data' in df.columns:
                df['Date'] = pd.to_datetime(df['Data'])
                df = df.drop('Data', axis=1)
                df['Year'] = df['Date'].dt.year
                mask = (df['Year'] >= start_year) & (df['Year'] <= end_year)
                df = df[mask].copy()
                
        except FileNotFoundError:
            st.error("❌ Nenhum arquivo de dados encontrado.")
            # Usar dados de exemplo como último recurso
            return create_sample_data()
    
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

# Carregar dados
df = load_data((2014, 2024))  # Carregar dados de 2014-2024 para análise completa

if df.empty:
    st.warning("Nenhum dado carregado. Verifique o arquivo de dados.")
    st.stop()

# Sidebar para controles
st.sidebar.header("🎯 Controles de Análise")

# Filtros interativos
crime_types = sorted(df['Primary Type'].unique())
selected_crimes = st.sidebar.multiselect(
    "Tipos de Crime:",
    options=crime_types,
    default=['THEFT', 'BATTERY', 'ASSAULT'] if 'THEFT' in crime_types else crime_types[:3]
)

available_years = sorted(df['Year'].unique())
selected_years = st.sidebar.multiselect(
    "Anos:",
    options=available_years,
    default=available_years[-3:]  # Últimos 3 anos como padrão
)

analysis_granularity = st.sidebar.radio(
    "Agregação Temporal:",
    ["Diária", "Mensal", "Anual"],
    index=1
)

# Aplicar filtros
df_filtered = df[
    (df['Primary Type'].isin(selected_crimes)) & 
    (df['Year'].isin(selected_years))
].copy()

st.sidebar.info(f"📊 Registros filtrados: {len(df_filtered):,}")

# Função para preparar dados temporais - CORRIGIDA
def prepare_temporal_data(df, granularity):
    """Prepara dados temporais com agregação correta"""
    if df.empty:
        return pd.DataFrame(columns=['ds', 'y'])
    
    # Garantir que temos a coluna Date
    if 'Date' not in df.columns:
        st.error("Coluna 'Date' não encontrada nos dados")
        return pd.DataFrame(columns=['ds', 'y'])
    
    # Criar cópia para não modificar o original
    df_temp = df.copy()
    
    if granularity == "Diária":
        # Agrupar por dia
        temporal_data = df_temp.groupby(df_temp['Date'].dt.date).size().reset_index()
        temporal_data.columns = ['ds', 'y']
        temporal_data['ds'] = pd.to_datetime(temporal_data['ds'])
        
    elif granularity == "Mensal":
        # Agrupar por mês (primeiro dia do mês)
        temporal_data = df_temp.groupby(pd.Grouper(key='Date', freq='ME')).size().reset_index()
        temporal_data.columns = ['ds', 'y']
        
    else:  # Anual
        # Agrupar por ano
        temporal_data = df_temp.groupby(df_temp['Date'].dt.year).size().reset_index()
        temporal_data.columns = ['ds', 'y']
        temporal_data['ds'] = pd.to_datetime(temporal_data['ds'].astype(str) + '-01-01')
    
    return temporal_data.sort_values('ds')

# Layout principal com tabs
tab1, tab2, tab3 = st.tabs(["📊 Série Temporal", "📈 Estatísticas", "🔍 Padrões"])

with tab1:
    st.subheader("Análise da Série Temporal")
    
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        temporal_data = prepare_temporal_data(df_filtered, analysis_granularity)
        
        if temporal_data.empty:
            st.warning("Não foi possível gerar dados temporais com os filtros selecionados.")
        else:
            col1, col2 = st.columns([2, 1])
            
            with col1:
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=temporal_data['ds'],
                    y=temporal_data['y'],
                    mode='lines+markers',
                    name='Crimes',
                    line=dict(color='#1f77b4', width=2)
                ))
                fig.update_layout(
                    title=f'Série Temporal - {", ".join(selected_crimes)}',
                    xaxis_title='Data',
                    yaxis_title=f'Número de Crimes ({analysis_granularity.lower()})',
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                st.subheader("📈 Métricas")
                total_crimes = temporal_data['y'].sum()
                avg_crimes = temporal_data['y'].mean()
                max_crimes = temporal_data['y'].max()
                
                st.metric("Total de Crimes", f"{total_crimes:,}")
                st.metric(f"Média {analysis_granularity}", f"{avg_crimes:.1f}")
                st.metric("Máximo", f"{max_crimes:,}")

with tab2:
    st.subheader("Estatísticas Descritivas")
    
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        daily_data = prepare_temporal_data(df_filtered, "Diária")
        
        if daily_data.empty:
            st.warning("Não foi possível gerar dados diários com os filtros selecionados.")
        else:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📋 Estatísticas Básicas")
                stats = {
                    'Métrica': ['Total', 'Média', 'Mediana', 'Desvio Padrão', 'Máximo', 'Mínimo'],
                    'Valor': [
                        f"{daily_data['y'].sum():,}",
                        f"{daily_data['y'].mean():.2f}",
                        f"{daily_data['y'].median():.2f}",
                        f"{daily_data['y'].std():.2f}",
                        f"{daily_data['y'].max():,}",
                        f"{daily_data['y'].min():,}"
                    ]
                }
                stats_df = pd.DataFrame(stats)
                st.dataframe(stats_df, use_container_width=True, hide_index=True)
            
            with col2:
                st.subheader("📊 Distribuição")
                fig_hist = px.histogram(
                    daily_data, 
                    x='y', 
                    nbins=20,
                    title='Distribuição de Crimes por Dia',
                    labels={'y': 'Número de Crimes'},
                    color_discrete_sequence=['#1f77b4']
                )
                st.plotly_chart(fig_hist, use_container_width=True)

with tab3:
    st.subheader("Análise de Padrões")
    
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        # Preparar dados diários para análise de padrões
        daily_data = prepare_temporal_data(df_filtered, "Diária")
        
        if daily_data.empty:
            st.warning("Não foi possível gerar dados diários para análise de padrões.")
        else:
            # Adicionar colunas para análise
            daily_data['dia_semana'] = daily_data['ds'].dt.day_name()
            daily_data['mes'] = daily_data['ds'].dt.month
            
            col1, col2 = st.columns(2)
            
            with col1:
                # Média por dia da semana
                dias_ordenados = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                media_semanal = daily_data.groupby('dia_semana')['y'].mean().reindex(dias_ordenados)
                
                # Traduzir para português
                dias_portugues = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
                media_semanal.index = dias_portugues
                
                fig_semanal = px.bar(
                    x=media_semanal.index,
                    y=media_semanal.values,
                    title='Média de Crimes por Dia da Semana',
                    labels={'x': 'Dia da Semana', 'y': 'Média de Crimes'}
                )
                st.plotly_chart(fig_semanal, use_container_width=True)
            
            with col2:
                # Média por mês
                media_mensal = daily_data.groupby('mes')['y'].mean()
                nomes_meses = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 
                              'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dec']
                
                fig_mensal = px.line(
                    x=nomes_meses,
                    y=media_mensal.values,
                    title='Média de Crimes por Mês',
                    labels={'x': 'Mês', 'y': 'Média de Crimes'},
                    markers=True
                )
                st.plotly_chart(fig_mensal, use_container_width=True)
            
            # SEÇÃO CORRIGIDA - Análise de Outliers
            st.subheader("🚨 Análise de Valores Atípicos")
            
            Q1 = daily_data['y'].quantile(0.25)
            Q3 = daily_data['y'].quantile(0.75)
            IQR = Q3 - Q1
            limite_superior = Q3 + 1.5 * IQR
            
            outliers = daily_data[daily_data['y'] > limite_superior]
            
            col3, col4 = st.columns(2)
            
            with col3:
                st.metric("Dias Atípicos", len(outliers))
                st.metric("Limite Superior para Outliers", f"{limite_superior:.1f}")
            
            with col4:
                if len(outliers) > 0:
                    st.markdown("**Top 5 Dias com Mais Crimes:**")
                    top_dias = outliers.nlargest(5, 'y')[['ds', 'y']].copy()
                    top_dias['ds'] = top_dias['ds'].dt.strftime('%d/%m/%Y')
                    top_dias = top_dias.rename(columns={'ds': 'Data', 'y': 'Crimes'})
                    st.dataframe(top_dias.reset_index(drop=True), use_container_width=True)
                else:
                    st.info("Nenhum outlier detectado nos dados filtrados")
            
            # Distribuição de frequência
            st.subheader("📊 Distribuição de Frequência")
            
            fig_dist = px.histogram(
                daily_data,
                x='y',
                nbins=30,
                title='Distribuição de Crimes por Dia',
                labels={'y': 'Número de Crimes', 'count': 'Frequência'},
                color_discrete_sequence=['#1f77b4']
            )
            fig_dist.update_layout(yaxis_title='Frequência')
            
            st.plotly_chart(fig_dist, use_container_width=True)

# Recomendações para Modelagem
st.markdown("---")
st.subheader("🚀 Recomendações para Modelagem Preditiva")

col1, col2, col3 = st.columns(3)

with col1:
    st.info("""
    **📅 Sazonalidade**
    - Padrão semanal bem definido
    - Considerar feriados
    - Sazonalidade mensal
    """)

with col2:
    st.info("""
    **⚙️ Configurações**
    - seasonality_mode='multiplicative'
    - weekly_seasonality=True
    - yearly_seasonality=True
    """)

with col3:
    st.info("""
    **📊 Validação**
    - Holdout temporal
    - Métricas: MAE, RMSE, MAPE
    - Cross-validation
    """)

# Rodapé
st.markdown("---")
st.markdown("**Desenvolvido para Análise de Crimes de Chicago**")
