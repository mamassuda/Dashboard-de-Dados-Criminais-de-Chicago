import streamlit as st
import pandas as pd
import numpy as np
import folium
from streamlit_folium import st_folium
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import datetime

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

# Sidebar para controles
st.sidebar.header("🎯 Controles de Análise")

# Carregar dados
@st.cache_data
def load_data():
    # AJUSTE: Coloque o caminho real do seu arquivo
    try:
        df = pd.read_csv("chicago_crimes.csv")
        return df
    except:
        st.error("Erro ao carregar dados. Verifique o caminho do arquivo.")
        return pd.DataFrame()

df = load_data()

if df.empty:
    st.stop()

# Filtros interativos na sidebar
st.sidebar.subheader("🔍 Filtros de Dados")

# Seleção de tipos de crime
crime_types = sorted(df['Primary Type'].unique())
selected_crimes = st.sidebar.multiselect(
    "Tipos de Crime",
    options=crime_types,
    default=['ASSAULT']  # Valor padrão baseado no seu código
)

# Seleção de ano
available_years = sorted(df['Year'].unique())
selected_years = st.sidebar.multiselect(
    "Anos",
    options=available_years,
    default=[2020]  # Valor padrão
)

# Seleção de meses
st.sidebar.subheader("📅 Período de Análise")
start_month, end_month = st.sidebar.slider(
    "Meses (Jan=1, Dez=12)",
    min_value=1,
    max_value=12,
    value=(1, 6)  # Janeiro a Junho como padrão
)

# Configurações de análise
st.sidebar.subheader("⚙️ Configurações de Análise")

analysis_type = st.sidebar.radio(
    "Tipo de Visualização:",
    ["Mapa de Calor", "Clusters DBSCAN", "Pontos Individuais", "Análise por Distrito"]
)

# Parâmetros DBSCAN (apenas se for usar clusters)
if analysis_type == "Clusters DBSCAN":
    eps_value = st.sidebar.slider("EPS (Distância)", 0.01, 0.5, 0.1, 0.01)
    min_samples_value = st.sidebar.slider("Mínimo de Amostras", 5, 100, 50)
    use_sampling = st.sidebar.checkbox("Usar amostragem para performance", value=True)

# Aplicar filtros
df_filtered = df[
    (df['Primary Type'].isin(selected_crimes)) &
    (df['Year'].isin(selected_years)) &
    (df['Month'].between(start_month, end_month))
].copy()

st.sidebar.info(f"📊 **Dados filtrados:** {len(df_filtered):,} registros")

# Layout principal com tabs
tab1, tab2, tab3 = st.tabs(["🗺️ Mapa Interativo", "📈 Análise por Distrito", "🔍 Análise de Clusters"])

with tab1:
    st.subheader("Mapa Interativo de Crimes")
    
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        # Criar mapa base
        chicago_center = [41.8781, -87.6298]
        m = folium.Map(location=chicago_center, zoom_start=10)
        
        # Amostrar para performance se necessário
        if len(df_filtered) > 5000:
            display_df = df_filtered.sample(n=5000, random_state=42)
            st.info(f"Mostrando 5.000 pontos de {len(df_filtered):,} totais para melhor performance")
        else:
            display_df = df_filtered
        
        # Adicionar pontos ao mapa baseado no tipo de análise
        if analysis_type == "Mapa de Calor":
            from folium.plugins import HeatMap
            heat_data = [[row['Latitude'], row['Longitude']] for idx, row in display_df.iterrows() 
                        if pd.notna(row['Latitude']) and pd.notna(row['Longitude'])]
            HeatMap(heat_data).add_to(m)
            
        elif analysis_type == "Clusters DBSCAN":
            # Aplicar DBSCAN diretamente no mapa
            coords = display_df[['Latitude', 'Longitude']].dropna()
            if len(coords) > 0:
                dbscan = DBSCAN(eps=eps_value, min_samples=min_samples_value)
                clusters = dbscan.fit_predict(coords)
                
                # Cores para clusters
                colors = ['red', 'blue', 'green', 'purple', 'orange', 'darkred', 'lightred', 'darkblue']
                
                for idx, (_, row) in enumerate(coords.iterrows()):
                    color = colors[clusters[idx] % len(colors)] if clusters[idx] != -1 else 'gray'
                    folium.CircleMarker(
                        location=[row['Latitude'], row['Longitude']],
                        radius=3,
                        color=color,
                        fill=True,
                        popup=f"Cluster: {clusters[idx]}"
                    ).add_to(m)
        
        else:  # Pontos individuais ou análise por distrito
            for idx, row in display_df.iterrows():
                if pd.notna(row['Latitude']) and pd.notna(row['Longitude']):
                    folium.CircleMarker(
                        location=[row['Latitude'], row['Longitude']],
                        radius=2,
                        color='red',
                        fill=True,
                        popup=f"Tipo: {row['Primary Type']}<br>Data: {row.get('Date', 'N/A')}"
                    ).add_to(m)
        
        # Exibir mapa
        st_folium(m, width=1200, height=600)

with tab2:
    st.subheader("Análise por Distrito")
    
    if df_filtered.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        # Análise por distrito (seu código original adaptado)
        if 'District' in df_filtered.columns:
            crime_counts_by_district = df_filtered.groupby('District').size().sort_values(ascending=False)
            total_crimes = crime_counts_by_district.sum()
            crime_proportion_by_district = (crime_counts_by_district / total_crimes) * 100
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.metric("Total de Crimes", f"{total_crimes:,}")
                st.metric("Distritos com Ocorrências", len(crime_counts_by_district))
            
            with col2:
                st.metric(
                    "Período Analisado", 
                    f"{datetime.date(selected_years[0], start_month, 1).strftime('%b/%Y')} - {datetime.date(selected_years[0], end_month, 1).strftime('%b/%Y')}"
                )
            
            # Tabelas
            st.subheader("📋 Estatísticas por Distrito")
            
            col3, col4 = st.columns(2)
            
            with col3:
                st.markdown("**Contagem Absoluta (Top 20)**")
                st.dataframe(
                    crime_counts_by_district.head(20).reset_index().rename(
                        columns={'District': 'Distrito', 0: 'Nº de Crimes'}
                    ),
                    use_container_width=True
                )
            
            with col4:
                st.markdown("**Proporção (%) do Total (Top 20)**")
                proportion_df = crime_proportion_by_district.head(20).round(2).reset_index()
                proportion_df = proportion_df.rename(
                    columns={'District': 'Distrito', 0: 'Proporção (%)'}
                )
                st.dataframe(proportion_df, use_container_width=True)
            
            # Gráfico
            st.subheader("📊 Distribuição por Distrito")
            top_n_districts = min(20, len(crime_counts_by_district))
            
            fig, ax = plt.subplots(figsize=(12, 6))
            crime_counts_by_district.head(top_n_districts).plot(kind='bar', ax=ax, color='skyblue')
            ax.set_title(f'Crimes por Distrito (Top {top_n_districts})')
            ax.set_xlabel('Distrito')
            ax.set_ylabel('Número de Crimes')
            ax.tick_params(axis='x', rotation=45)
            plt.tight_layout()
            st.pyplot(fig)
            
        else:
            st.warning("Coluna 'District' não encontrada nos dados.")

with tab3:
    st.subheader("Análise de Clusters com DBSCAN")
    
    if st.button("🔍 Executar Análise de Clusters", type="primary"):
        with st.spinner("Processando clusters..."):
            # Preparar dados para DBSCAN
            coords = df_filtered[['Latitude', 'Longitude']].dropna()
            
            if coords.empty:
                st.error("Não há coordenadas válidas para análise.")
            else:
                # Amostragem para performance
                if use_sampling and len(coords) > 50000:
                    coords_sample = coords.sample(n=50000, random_state=42)
                    st.info(f"📊 Usando amostra de 50.000 pontos de {len(coords):,} totais")
                else:
                    coords_sample = coords
                
                # Normalização
                coords_normalized = (coords_sample - coords_sample.mean()) / coords_sample.std()
                
                # Executar DBSCAN
                dbscan = DBSCAN(eps=eps_value, min_samples=min_samples_value, n_jobs=-1)
                clusters = dbscan.fit_predict(coords_normalized)
                
                # Métricas
                n_clusters = len(set(clusters)) - (1 if -1 in clusters else 0)
                n_noise = list(clusters).count(-1)
                noise_percentage = (n_noise / len(clusters)) * 100
                
                # Display metrics
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Clusters Identificados", n_clusters)
                with col2:
                    st.metric("Pontos de Ruído", n_noise)
                with col3:
                    st.metric("Taxa de Ruído", f"{noise_percentage:.1f}%")
                with col4:
                    st.metric("Pontos Analisados", len(coords_sample))
                
                # Gráfico de clusters
                st.subheader("📈 Visualização dos Clusters")
                
                fig, ax = plt.subplots(figsize=(12, 8))
                scatter = ax.scatter(
                    coords_sample.iloc[:, 0], 
                    coords_sample.iloc[:, 1], 
                    c=clusters, 
                    cmap='tab10', 
                    s=10, 
                    alpha=0.6
                )
                ax.set_title(f'Clusters Espaciais - {n_clusters} clusters, {n_noise} ruídos ({noise_percentage:.1f}%)')
                ax.set_xlabel('Longitude (normalizada)')
                ax.set_ylabel('Latitude (normalizada)')
                plt.colorbar(scatter, ax=ax, label='Cluster ID')
                plt.tight_layout()
                st.pyplot(fig)

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
