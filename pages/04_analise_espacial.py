import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import datetime
import warnings
warnings.filterwarnings('ignore')

# Configuração da página
st.set_page_config(
    page_title="Análise Espacial - Crimes Chicago", 
    page_icon="🗺️", 
    layout="wide"
)

# Título e descrição
st.title("🗺️ Análise Espacial de Crimes")
st.markdown("""
### Mapeamento Interativo e Análise Espacial
Explore a distribuição geográfica dos crimes, identifique hotspots e padrões espaciais.
""")

# Função para criar dados de exemplo (fallback)
def create_sample_data():
    """Cria dataset de demonstração caso os arquivos principais não estejam disponíveis"""
    st.info("📝 Criando dataset de demonstração...")
    dates = pd.date_range('2014-01-01', periods=365*3, freq='D')
    crimes = ['THEFT', 'BATTERY', 'CRIMINAL DAMAGE', 'NARCOTICS', 'ASSAULT', 'BURGLARY', 'ROBBERY']
    
    data = []
    for date in dates:
        daily_crimes = np.random.randint(50, 200)
        for _ in range(daily_crimes):
            lat = np.random.uniform(41.7, 42.0)
            lng = np.random.uniform(-87.9, -87.6)
            data.append({
                'Date': date,
                'Primary Type': np.random.choice(crimes),
                'District': np.random.choice(['001', '002', '003', '004', '005', '006', '007', '008', '009', '010', '011', '012', '014', '015', '016', '017', '018', '019', '020', '022', '024', '025']),
                'Latitude': lat,
                'Longitude': lng,
                'Arrest': np.random.choice([True, False]),
                'Year': date.year,
                'Month': date.month
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
    
    # Adicionar coluna de mês se não existir
    if 'Month' not in df.columns:
        df['Month'] = df['Date'].dt.month
        
    st.success(f"✅ Dados de {start_year}-{end_year} carregados! Total: {len(df):,} registros")
    return df

# Carregar dados
df = load_data((2014, 2024))  # Carregar dados completos para análise

if df.empty:
    st.error("❌ Não foi possível carregar os dados. Verifique os arquivos de dados.")
    st.stop()

# Sidebar para controles
st.sidebar.header("🎯 Controles de Análise")

# Filtros interativos na sidebar
st.sidebar.subheader("🔍 Filtros de Dados")

# Seleção de tipos de crime
crime_types = sorted(df['Primary Type'].unique())
selected_crimes = st.sidebar.multiselect(
    "Tipos de Crime:",
    options=crime_types,
    default=['THEFT', 'BATTERY', 'ASSAULT']  # Valores padrão mais comuns
)

# Seleção de ano
available_years = sorted(df['Year'].unique())
selected_years = st.sidebar.multiselect(
    "Anos:",
    options=available_years,
    default=available_years[-3:]  # Últimos 3 anos como padrão
)

# Seleção de meses
st.sidebar.subheader("📅 Período de Análise")
start_month, end_month = st.sidebar.slider(
    "Meses (Jan=1, Dez=12):",
    min_value=1,
    max_value=12,
    value=(1, 12)  # Todo o ano como padrão
)

# Configurações de análise
st.sidebar.subheader("⚙️ Configurações de Análise")

analysis_type = st.sidebar.radio(
    "Tipo de Visualização:",
    ["Mapa de Calor", "Clusters DBSCAN", "Pontos Individuais", "Análise por Distrito"]
)

# Parâmetros DBSCAN (apenas se for usar clusters)
if analysis_type == "Clusters DBSCAN":
    eps_value = st.sidebar.slider("EPS (Distância):", 0.001, 0.1, 0.01, 0.001)
    min_samples_value = st.sidebar.slider("Mínimo de Amostras:", 5, 100, 10)
    use_sampling = st.sidebar.checkbox("Usar amostragem para performance", value=True)

# Aplicar filtros
df_filtered = df[
    (df['Primary Type'].isin(selected_crimes)) &
    (df['Year'].isin(selected_years)) &
    (df['Month'].between(start_month, end_month))
].copy()

# Remover linhas com coordenadas inválidas
df_filtered = df_filtered.dropna(subset=['Latitude', 'Longitude'])

# Filtrar coordenadas dentro de Chicago
chicago_bounds = {
    'lat_min': 41.6, 'lat_max': 42.1,
    'lng_min': -88.0, 'lng_max': -87.5
}

df_filtered = df_filtered[
    (df_filtered['Latitude'].between(chicago_bounds['lat_min'], chicago_bounds['lat_max'])) &
    (df_filtered['Longitude'].between(chicago_bounds['lng_min'], chicago_bounds['lng_max']))
]

st.sidebar.info(f"📊 **Dados filtrados:** {len(df_filtered):,} registros")

if df_filtered.empty:
    st.warning("⚠️ Nenhum dado encontrado com os filtros selecionados após limpeza de coordenadas.")
    st.stop()

# Layout principal com tabs
tab1, tab2, tab3 = st.tabs(["🗺️ Mapa Interativo", "📈 Análise por Distrito", "🔍 Análise de Clusters"])

with tab1:
    st.subheader("Mapa Interativo de Crimes")
    
    # Criar mapa base
    chicago_center = [41.8781, -87.6298]
    m = folium.Map(location=chicago_center, zoom_start=10)
    
    # Amostrar para performance se necessário
    if len(df_filtered) > 10000:
        display_df = df_filtered.sample(n=10000, random_state=42)
        st.info(f"📊 Mostrando 10.000 pontos de {len(df_filtered):,} totais para melhor performance")
    else:
        display_df = df_filtered
    
    # Adicionar pontos ao mapa baseado no tipo de análise
    if analysis_type == "Mapa de Calor":
        try:
            from folium.plugins import HeatMap
            heat_data = [[row['Latitude'], row['Longitude']] for idx, row in display_df.iterrows()]
            if heat_data:
                HeatMap(heat_data, radius=10, blur=15, max_zoom=13).add_to(m)
                st.success("✅ Mapa de calor gerado com sucesso!")
            else:
                st.warning("⚠️ Nenhum dado válido para gerar mapa de calor")
        except Exception as e:
            st.error(f"❌ Erro ao gerar mapa de calor: {e}")
            
    elif analysis_type == "Clusters DBSCAN":
        try:
            # Aplicar DBSCAN diretamente no mapa
            coords = display_df[['Latitude', 'Longitude']].values
            
            if len(coords) > 0:
                # Normalizar coordenadas para DBSCAN
                coords_normalized = (coords - coords.mean(axis=0)) / coords.std(axis=0)
                dbscan = DBSCAN(eps=eps_value, min_samples=min_samples_value)
                clusters = dbscan.fit_predict(coords_normalized)
                
                # Cores para clusters
                colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'darkblue', 'lightblue', 'darkgreen']
                
                for idx, (lat, lng) in enumerate(coords):
                    cluster_id = clusters[idx]
                    if cluster_id != -1:  # Ignorar ruído
                        color = colors[cluster_id % len(colors)]
                        folium.CircleMarker(
                            location=[lat, lng],
                            radius=3,
                            color=color,
                            fill=True,
                            fill_opacity=0.7,
                            popup=f"Cluster: {cluster_id}"
                        ).add_to(m)
                st.success(f"✅ {len(set(clusters)) - 1} clusters identificados")
        except Exception as e:
            st.error(f"❌ Erro no DBSCAN: {e}")
    
    else:  # Pontos individuais ou análise por distrito
        # Usar cores diferentes para tipos de crime
        crime_color_map = {
            'THEFT': 'blue',
            'BATTERY': 'red', 
            'ASSAULT': 'orange',
            'BURGLARY': 'green',
            'ROBBERY': 'purple',
            'NARCOTICS': 'darkred',
            'CRIMINAL DAMAGE': 'gray'
        }
        
        for idx, row in display_df.iterrows():
            crime_type = row['Primary Type']
            color = crime_color_map.get(crime_type, 'red')
            
            folium.CircleMarker(
                location=[row['Latitude'], row['Longitude']],
                radius=2,
                color=color,
                fill=True,
                fill_opacity=0.7,
                popup=f"""
                <b>Tipo:</b> {crime_type}<br>
                <b>Data:</b> {row['Date'].strftime('%d/%m/%Y') if pd.notna(row['Date']) else 'N/A'}<br>
                <b>Distrito:</b> {row.get('District', 'N/A')}<br>
                <b>Arrest:</b> {row.get('Arrest', 'N/A')}
                """
            ).add_to(m)
    
    # Exibir mapa
    st.subheader("📍 Mapa Interativo")
    map_data = st_folium(m, width=1200, height=600, returned_objects=[])
    
    # Estatísticas rápidas
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total de Crimes no Mapa", len(display_df))
    with col2:
        st.metric("Tipos de Crime", len(display_df['Primary Type'].unique()))
    with col3:
        if 'District' in display_df.columns:
            st.metric("Distritos", len(display_df['District'].unique()))

with tab2:
    st.subheader("Análise por Distrito")
    
    if 'District' not in df_filtered.columns:
        st.warning("⚠️ Coluna 'District' não encontrada nos dados.")
    else:
        # Análise por distrito
        crime_counts_by_district = df_filtered['District'].value_counts().sort_values(ascending=False)
        total_crimes = crime_counts_by_district.sum()
        crime_proportion_by_district = (crime_counts_by_district / total_crimes) * 100
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.metric("Total de Crimes", f"{total_crimes:,}")
            st.metric("Distritos com Ocorrências", len(crime_counts_by_district))
        
        with col2:
            if selected_years:
                year_str = ", ".join(map(str, selected_years))
                st.metric("Anos Analisados", year_str)
            st.metric("Meses", f"{start_month} a {end_month}")
        
        # Tabelas
        st.subheader("📋 Estatísticas por Distrito")
        
        col3, col4 = st.columns(2)
        
        with col3:
            st.markdown("**Contagem Absoluta (Top 15)**")
            top_districts = crime_counts_by_district.head(15).reset_index()
            top_districts.columns = ['Distrito', 'Nº de Crimes']
            st.dataframe(top_districts, use_container_width=True)
        
        with col4:
            st.markdown("**Proporção (%) do Total (Top 15)**")
            proportion_df = crime_proportion_by_district.head(15).round(2).reset_index()
            proportion_df.columns = ['Distrito', 'Proporção (%)']
            st.dataframe(proportion_df, use_container_width=True)
        
        # Gráfico
        st.subheader("📊 Distribuição por Distrito")
        top_n_districts = min(15, len(crime_counts_by_district))
        
        fig, ax = plt.subplots(figsize=(12, 6))
        crime_counts_by_district.head(top_n_districts).plot(kind='bar', ax=ax, color='skyblue')
        ax.set_title(f'Crimes por Distrito (Top {top_n_districts})')
        ax.set_xlabel('Distrito')
        ax.set_ylabel('Número de Crimes')
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

with tab3:
    st.subheader("Análise de Clusters com DBSCAN")
    
    if st.button("🔍 Executar Análise de Clusters", type="primary"):
        with st.spinner("Processando clusters..."):
            try:
                # Preparar dados para DBSCAN
                coords = df_filtered[['Latitude', 'Longitude']].values
                
                if len(coords) == 0:
                    st.error("❌ Não há coordenadas válidas para análise.")
                    st.stop()
                
                # Amostragem para performance
                if use_sampling and len(coords) > 50000:
                    sample_indices = np.random.choice(len(coords), 50000, replace=False)
                    coords_sample = coords[sample_indices]
                    st.info(f"📊 Usando amostra de 50.000 pontos de {len(coords):,} totais")
                else:
                    coords_sample = coords
                
                # Normalização para DBSCAN
                coords_mean = coords_sample.mean(axis=0)
                coords_std = coords_sample.std(axis=0)
                coords_normalized = (coords_sample - coords_mean) / coords_std
                
                # Executar DBSCAN
                dbscan = DBSCAN(eps=eps_value, min_samples=min_samples_value)
                clusters = dbscan.fit_predict(coords_normalized)
                
                # Métricas
                unique_clusters = set(clusters)
                n_clusters = len(unique_clusters) - (1 if -1 in unique_clusters else 0)
                n_noise = list(clusters).count(-1)
                noise_percentage = (n_noise / len(clusters)) * 100
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Clusters Identificados", n_clusters)
                with col2:
                    st.metric("Pontos de Ruído", f"{n_noise:,}")
                with col3:
                    st.metric("Taxa de Ruído", f"{noise_percentage:.1f}%")
                with col4:
                    st.metric("Pontos Analisados", f"{len(coords_sample):,}")
                
                # Gráfico de clusters
                st.subheader("📈 Visualização dos Clusters")
                
                fig, ax = plt.subplots(figsize=(12, 8))
                scatter = ax.scatter(
                    coords_sample[:, 1],  # Longitude no eixo X
                    coords_sample[:, 0],  # Latitude no eixo Y
                    c=clusters, 
                    cmap='tab10', 
                    s=10, 
                    alpha=0.6
                )
                ax.set_title(f'Clusters Espaciais - {n_clusters} clusters, {n_noise} ruídos ({noise_percentage:.1f}%)')
                ax.set_xlabel('Longitude')
                ax.set_ylabel('Latitude')
                plt.colorbar(scatter, ax=ax, label='Cluster ID')
                plt.tight_layout()
                st.pyplot(fig)
                
                # Análise dos clusters
                if n_clusters > 0:
                    st.subheader("🔍 Análise Detalhada dos Clusters")
                    
                    # Adicionar labels de cluster aos dados
                    cluster_df = pd.DataFrame({
                        'Latitude': coords_sample[:, 0],
                        'Longitude': coords_sample[:, 1],
                        'Cluster': clusters
                    })
                    
                    # Estatísticas por cluster
                    cluster_stats = cluster_df[cluster_df['Cluster'] != -1].groupby('Cluster').agg({
                        'Latitude': ['count', 'mean'],
                        'Longitude': 'mean'
                    }).round(4)
                    
                    cluster_stats.columns = ['N_Pontos', 'Latitude_Media', 'Longitude_Media']
                    cluster_stats = cluster_stats.sort_values('N_Pontos', ascending=False)
                    
                    st.markdown("**Estatísticas por Cluster:**")
                    st.dataframe(cluster_stats, use_container_width=True)
                
            except Exception as e:
                st.error(f"❌ Erro na análise de clusters: {e}")

# Rodapé informativo
st.markdown("---")
st.markdown("""
**💡 Dicas de Uso:**

- **Mapa de Calor**: Ideal para identificar hotspots de criminalidade
- **Clusters DBSCAN**: Mostra agrupamentos naturais de ocorrências  
- **Pontos Individuais**: Permite análise detalhada de cada crime
- **Análise por Distrito**: Compara a distribuição entre regiões administrativas

**📊 Filtros Disponíveis:** Tipo de crime, ano, meses, parâmetros de clusterização
""")

# Footer
st.markdown("---")
st.markdown("**Módulo de Análise Espacial - Chicago Crime Analytics**")
