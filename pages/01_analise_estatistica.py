# pages/01_📊_Explorar_Dados.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from datetime import datetime

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

# FUNÇÃO ATUALIZADA
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

# Configuração da página
st.set_page_config(page_title="Análise Estatística - Crimes Chicago", page_icon="📊", layout="wide")

# Título e navegação
st.title("Análise Estatística")
st.markdown("Navegue e filtre o banco de dados completo de crimes de Chicago")

# Botão para voltar à página inicial
if st.button("← Voltar para Página Inicial"):
    st.switch_page("app.py")

# Carregar dados completos (2014-2024) para permitir a seleção
df_full = load_data((2014, 2024))

# Sidebar com os filtros disponíveis
st.sidebar.header("🔧 Filtros para Análise")

#### TIPOS DE FILTRO ####

# FILTRO TEMPORAL - Agora com todos os anos de 2014-2024
anos_disponiveis = sorted(df_full['Year'].unique())
anos_selecionados = st.sidebar.multiselect(
    "Selecione os anos para análise:",
    options=anos_disponiveis,
    default=[2024, 2023, 2022]  # Anos mais recentes como padrão
)

# FILTRO POR TIPO DE CRIME - usar df_full para ter todas as opções
crime_types_full = df_full['Primary Type'].unique()
selected_crime = st.sidebar.multiselect("Selecione o tipo de crime:", crime_types_full, default=crime_types_full)

# Filtro por período do dia
st.sidebar.subheader("Selecione o período do dia:")

# dicionário com os períodos do dia #
periods = {
    "Madrugada (00:00-05:59)": (0, 5),
    "Manhã (06:00-11:59)": (6, 11),
    "Tarde (12:00-17:59)": (12, 17),
    "Noite (18:00-23:59)": (18, 23),
    "Todo o dia (00:00-23:59)": (0, 23)
}

periodo_selecionado = st.sidebar.selectbox("Período do dia:", options=list(periods.keys()))

# Filtro adicional por distrito 
distritos = None
if 'District' in df_full.columns:
    distritos = st.sidebar.multiselect(
        "Selecione os distritos:",
        df_full['District'].unique(),
        default=df_full['District'].unique()
    )

### APLICAÇÃO DOS FILTROS ###
df_filtrado = df_full.copy()

# Aplicar filtro de anos
if anos_selecionados:
    df_filtrado = df_filtrado[df_filtrado['Year'].isin(anos_selecionados)]
    st.sidebar.info(f"📅 Analisando dados de: {sorted(anos_selecionados)}")
else:
    df_filtrado = df_filtrado[df_filtrado['Year'].isin([2024, 2023, 2022])]  # Padrão: anos mais recentes
    st.sidebar.info("📅 Usando anos mais recentes (2022-2024) como padrão")

# Aplicar filtro de tipo de crime
if selected_crime:
    df_filtrado = df_filtrado[df_filtrado['Primary Type'].isin(selected_crime)]

# Aplicar filtro de período do dia
if periodo_selecionado != "Todo o dia" and 'Date' in df_filtrado.columns:
    # Extrair hora da data para filtrar
    df_filtrado = df_filtrado.copy()  # Garantir que estamos trabalhando com uma cópia
    df_filtrado['Hora'] = df_filtrado['Date'].dt.hour
    hora_i, hora_f = periods[periodo_selecionado]
    df_filtrado = df_filtrado[
        (df_filtrado['Hora'] >= hora_i) & 
        (df_filtrado['Hora'] <= hora_f)
    ]

# Aplicar filtro de distrito 
if distritos is not None and 'District' in df_filtrado.columns:
    df_filtrado = df_filtrado[df_filtrado['District'].isin(distritos)]

### VALIDAÇÃO DE DADOS FILTRADOS ###
if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados. Tente ajustar os critérios de filtragem.")
    
    # Mostrar dados originais se os filtros não retornarem nada
    st.info("Mostrando dados sem filtros aplicados:")
    df_filtrado = df_full.copy()
else:
    st.success(f"✅ **{len(df_filtrado):,} registros** encontrados com os filtros aplicados")

### Exibição quantitativa da análise ###
st.header("📈 Visão Geral dos Dados Selecionados")

# Métricas principais
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_crimes = len(df_filtrado)
    st.metric("Total de crimes", f"{total_crimes:,}")

with col2:
    if not df_filtrado.empty and 'Date' in df_filtrado.columns:
        dias_unicos = df_filtrado['Date'].dt.date.nunique()
        if dias_unicos > 0:
            crimes_por_dia = total_crimes / dias_unicos
            st.metric("Média de crimes por dia", f"{crimes_por_dia:.1f}")
        else:
            st.metric("Média de crimes por dia", "0.0")
    else:
        st.metric("Média de crimes por dia", "N/D")

with col3:
    if not df_filtrado.empty and 'Arrest' in df_filtrado.columns:
        taxa_arrest = (df_filtrado['Arrest'].mean() * 100)
        st.metric("Taxa de Prisões", f"{taxa_arrest:.1f}%")
    else:
        if not df_filtrado.empty and 'Date' in df_filtrado.columns:
            # Extrair hora se não existir
            if 'Hora' not in df_filtrado.columns:
                df_filtrado['Hora'] = df_filtrado['Date'].dt.hour
            hora_pico = df_filtrado['Hora'].mode()
            hora_pico = hora_pico.iloc[0] if not hora_pico.empty else "N/D"
            st.metric("Horário de Pico", f"{hora_pico}h")
        else:
            st.metric("Horário de Pico", "N/D")

with col4:
    if not df_filtrado.empty and 'Primary Type' in df_filtrado.columns:
        principal_crime = df_filtrado['Primary Type'].value_counts().idxmax()
        st.metric("Tipo de crime mais comum", principal_crime)
    else:
        st.metric("Tipo de crime mais comum", "N/D")

### VISUALIZAÇÕES GRÁFICAS ###
st.header("📊 Análises Visuais Rápidas")

# Criar colunas para os gráficos
col1, col2 = st.columns(2)

with col1:
    st.subheader("Distribuição por Tipo de Crime")
    if not df_filtrado.empty and 'Primary Type' in df_filtrado.columns:
        # Gráfico de pizza para tipos de crime
        crime_counts = df_filtrado['Primary Type'].value_counts().head(10)
        fig_pizza = px.pie(
            values=crime_counts.values,
            names=crime_counts.index,
            title="Top 10 Tipos de Crime"
        )
        st.plotly_chart(fig_pizza, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir no gráfico.")

with col2:
    st.subheader("Crimes por Hora do Dia")
    if not df_filtrado.empty and 'Date' in df_filtrado.columns:
        # Garantir que temos a coluna Hora
        if 'Hora' not in df_filtrado.columns:
            df_filtrado['Hora'] = df_filtrado['Date'].dt.hour
        
        crimes_por_hora = df_filtrado['Hora'].value_counts().sort_index()
        
        fig_hora = px.bar(
            x=crimes_por_hora.index,
            y=crimes_por_hora.values,
            title="Distribuição de Crimes por Hora",
            labels={'x': 'Hora do Dia', 'y': 'Número de Crimes'}
        )
        st.plotly_chart(fig_hora, use_container_width=True)
    else:
        st.info("Nenhum dado para exibir no gráfico.")

### ANÁLISE DETALHADA ###
st.header("🔍 Análise Detalhada dos Dados")

# Criar abas para diferentes análises
tab1, tab2, tab3 = st.tabs(["📋 Dados Filtrados", "📊 Estatísticas", "📥 Exportar Dados"])

with tab1:
    st.subheader("Visualização dos Dados Filtrados")
    st.write(f"Mostrando {len(df_filtrado)} registros:")
    
    if not df_filtrado.empty:
        # Paginação simples
        page_size = 100
        total_pages = max(1, (len(df_filtrado) + page_size - 1) // page_size)
        
        page = st.number_input("Página", min_value=1, max_value=total_pages, value=1)
        start_idx = (page - 1) * page_size
        end_idx = min(start_idx + page_size, len(df_filtrado))
        
        st.dataframe(df_filtrado.iloc[start_idx:end_idx], use_container_width=True)
        
        st.write(f"Página {page} de {total_pages} | Registros {start_idx+1} a {end_idx}")
    else:
        st.info("Nenhum dado para exibir.")

with tab2:
    st.subheader("Estatísticas Descritivas")
    
    if not df_filtrado.empty:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Distribuição por Tipo de Crime:**")
            crime_percentages = df_filtrado['Primary Type'].value_counts(normalize=True) * 100
            for crime_type, percentage in crime_percentages.head(10).items():
                st.write(f"• {crime_type}: **{percentage:.1f}%**")
            
            st.write("**Informações Gerais:**")
            st.write(f"• Total de tipos distintos: **{df_filtrado['Primary Type'].nunique()}**")
            if 'Date' in df_filtrado.columns:
                dias_unicos = df_filtrado['Date'].dt.date.nunique()
                st.write(f"• Período coberto: **{dias_unicos} dias**")
        
        with col2:
            st.write("**Padrões Temporais:**")
            if 'Date' in df_filtrado.columns:
                df_filtrado['Dia_Semana'] = df_filtrado['Date'].dt.day_name()
                dias_ordenados = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                crimes_dia = df_filtrado['Dia_Semana'].value_counts().reindex(dias_ordenados, fill_value=0)
                
                st.write("**Crimes por dia da semana:**")
                for dia, count in crimes_dia.items():
                    st.write(f"• {dia}: **{count}** crimes")
    else:
        st.info("Nenhum dado para análise estatística.")

with tab3:
    st.subheader("Exportar Dados Filtrados")
    
    st.info("Exporte os dados filtrados para análise externa")
    
    if not df_filtrado.empty:
        # Opções de exportação
        col1, col2 = st.columns(2)
        
        with col1:
            # Download CSV
            csv = df_filtrado.to_csv(index=False)
            st.download_button(
                label="📥 Download como CSV",
                data=csv,
                file_name=f"chicago_crimes_filtrados_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with col2:
            # Estatísticas do dataset
            st.write("**Resumo do Dataset:**")
            st.write(f"• Registros: {len(df_filtrado):,}")
            st.write(f"• Colunas: {len(df_filtrado.columns)}")
            if 'Date' in df_filtrado.columns:
                st.write(f"• Período: {df_filtrado['Date'].min().strftime('%d/%m/%Y')} a {df_filtrado['Date'].max().strftime('%d/%m/%Y')}")
    else:
        st.warning("Nenhum dado disponível para exportação.")

# Footer
st.markdown("---")
st.markdown("*Módulo de Exploração de Dados - Chicago Crime Analytics*")
