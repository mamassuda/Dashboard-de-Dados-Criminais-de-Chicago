# pages/01_📊_Explorar_Dados.py
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

@st.cache_data
def load_data():
    df = pd.read_csv("chicago_crimes.csv")
    # Converter coluna de datas
    df['Date'] = pd.to_datetime(df['Date'])
    return df

# Configuração da página
st.set_page_config(page_title="Análise Estatística - Crimes Chicago", page_icon="📊", layout="wide")

# Título e navegação
st.title("Análise Estatística")
st.markdown("Navegue e filtre o banco de dados completo de crimes de Chicago")

# Botão para voltar à página inicial
if st.button("← Voltar para Página Inicial"):
    st.switch_page("app.py")

# Carregar dados
df = load_data()

# Sidebar com os filtros disponíveis
st.sidebar.header("🔧 Filtros para Análise")

#### TIPOS DE FILTRO ####

# FILTRO TEMPORAL # 
anos = st.sidebar.multiselect(
    "Selecione os anos para análise:",
    df['Year'].unique(),
    default=df['Year'].unique()
)

# FILTRO POR TIPO DE CRIME #
crime_types = df['Primary Type'].unique()
selected_crime = st.sidebar.multiselect("Selecione o tipo de crime:", crime_types, default=crime_types)

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
if 'District' in df.columns:
    distritos = st.sidebar.multiselect(
        "Selecione os distritos:",
        df['District'].unique(),
        default=df['District'].unique()
    )

### APLICAÇÃO DOS FILTROS ###
df_filtrado = df.copy()

# Aplicar filtros sequencialmente
if anos:
    df_filtrado = df_filtrado[df_filtrado['Year'].isin(anos)]

if selected_crime:
    df_filtrado = df_filtrado[df_filtrado['Primary Type'].isin(selected_crime)]

if periodo_selecionado != "Todo o dia":
    hora_i, hora_f = periods[periodo_selecionado]
    df_filtrado = df_filtrado[
        (df_filtrado['Date'].dt.hour >= hora_i) & 
        (df_filtrado['Date'].dt.hour <= hora_f)
    ]

# Filtro de distrito 
if 'District' in df.columns and 'distritos' in locals():
    df_filtrado = df_filtrado[df_filtrado['District'].isin(distritos)]

### VALIDAÇÃO DE DADOS FILTRADOS ###
if df_filtrado.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados. Tente ajustar os critérios de filtragem.")
    
    # Mostrar dados originais se os filtros não retornarem nada
    st.info("Mostrando dados sem filtros aplicados:")
    df_filtrado = df.copy()
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
    dias_unicos = df_filtrado['Date'].dt.date.nunique()
    if dias_unicos > 0:
        crimes_por_dia = total_crimes / dias_unicos
        st.metric("Média de crimes por dia", f"{crimes_por_dia:.1f}")
    else:
        st.metric("Média de crimes por dia", "0.0")

with col3:
    if 'Arrest' in df_filtrado.columns:
        taxa_arrest = (df_filtrado['Arrest'].mean() * 100)
        st.metric("Taxa de Prisões", f"{taxa_arrest:.1f}%")
    else:
        hora_pico = df_filtrado['Date'].dt.hour.mode()
        hora_pico = hora_pico.iloc[0] if not hora_pico.empty else "N/D"
        st.metric("Horário de Pico", f"{hora_pico}h")

with col4:
    if not df_filtrado.empty:
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
    if not df_filtrado.empty:
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
    if not df_filtrado.empty:
        # Gráfico de crimes por hora
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
    
    # Paginação simples
    page_size = 100
    total_pages = max(1, len(df_filtrado) // page_size)
    
    page = st.number_input("Página", min_value=1, max_value=total_pages, value=1)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    
    st.dataframe(df_filtrado.iloc[start_idx:end_idx], use_container_width=True)
    
    st.write(f"Página {page} de {total_pages} | Registros {start_idx+1} a {min(end_idx, len(df_filtrado))}")

with tab2:
    st.subheader("Estatísticas Descritivas")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Distribuição por Tipo de Crime:**")
        crime_percentages = df_filtrado['Primary Type'].value_counts(normalize=True) * 100
        for crime_type, percentage in crime_percentages.head(10).items():
            st.write(f"• {crime_type}: **{percentage:.1f}%**")
        
        st.write("**Informações Gerais:**")
        st.write(f"• Total de tipos distintos: **{df_filtrado['Primary Type'].nunique()}**")
        st.write(f"• Período coberto: **{dias_unicos} dias**")
    
    with col2:
        st.write("**Padrões Temporais:**")
        df_filtrado['Dia_Semana'] = df_filtrado['Date'].dt.day_name()
        dias_ordenados = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
        crimes_dia = df_filtrado['Dia_Semana'].value_counts().reindex(dias_ordenados, fill_value=0)
        
        st.write("**Crimes por dia da semana:**")
        for dia, count in crimes_dia.items():
            st.write(f"• {dia}: **{count}** crimes")

with tab3:
    st.subheader("Exportar Dados Filtrados")
    
    st.info("Exporte os dados filtrados para análise externa")
    
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
        st.write(f"• Período: {df_filtrado['Date'].min().strftime('%d/%m/%Y')} a {df_filtrado['Date'].max().strftime('%d/%m/%Y')}")

# Footer
st.markdown("---")
st.markdown("*Módulo de Exploração de Dados - Chicago Crime Analytics*")