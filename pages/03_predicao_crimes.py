# 03_predicao_crimes.py - VERSÃO CORRIGIDA
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from sklearn.ensemble import RandomForestRegressor
from sklearn.preprocessing import StandardScaler
import holidays
from datetime import timedelta
import warnings
import sys
import os

# Configuração da página DEVE SER SEMPRE A PRIMEIRA COISA
st.set_page_config(page_title="Predição Crimes", layout="wide")

# Importa a função load_data do app.py principal
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import load_data

warnings.filterwarnings('ignore')

def main():
    # Título e navegação
    st.title("🔮 Predição Crimes")
    if st.button("← Voltar ao Início"):
        st.switch_page("app.py")

    # Carregar dados
    with st.spinner("Carregando dados de 2014-2024..."):
        df = load_data((2014, 2024))  # Carregar dados completos para análise

    # Verificar se os dados foram carregados corretamente
    if df is None or df.empty:
        st.error("❌ Não foi possível carregar os dados. Verifique se os arquivos estão na pasta 'data_splits'.")
        return

    # Sidebar - Seleção do modelo
    st.sidebar.header("🤖 Escolha do Modelo")
    modelo_selecionado = st.sidebar.radio(
        "Selecione o modelo:",
        ["Prophet", "Random Forest"],
        help="Ambos modelos usarão dados DIÁRIOS para comparação justa"
    )

    # Filtros comuns
    crime_types = sorted(df['Primary Type'].unique())
    selected_crime = st.sidebar.selectbox(
        "Tipo de Crime", 
        crime_types,
        index=crime_types.index('THEFT') if 'THEFT' in crime_types else 0
    )

    available_years = sorted(df['Year'].unique())

    # CONFIGURAÇÕES PARA AMBOS OS MODELOS (DIÁRIOS)
    st.sidebar.header("📅 Configurações Temporais")

    # Ordenar anos disponíveis
    available_years_sorted = sorted(available_years)

    # Verificar se há anos suficientes
    if len(available_years_sorted) < 2:
        st.error("❌ Não há anos suficientes no dataset para treino e teste")
        return

    # Selecionar intervalo de treino
    train_start = st.sidebar.selectbox(
        "Início do Treino", 
        available_years_sorted[:-1],
        index=max(0, len(available_years_sorted) - 4)  # Default: 4 anos antes do último
    )

    # Filtrar anos possíveis para fim do treino
    possible_train_ends = [y for y in available_years_sorted if y > train_start]
    if not possible_train_ends:
        st.error("❌ Não há anos disponíveis após o início do treino")
        return

    train_end = st.sidebar.selectbox(
        "Fim do Treino", 
        possible_train_ends,
        index=min(2, len(possible_train_ends) - 1)  # Default: 2 anos após início
    )

    train_years = list(range(train_start, train_end + 1))

    # Ano de teste (após o treino)
    available_test_years = [y for y in available_years_sorted if y > train_end]
    if not available_test_years:
        st.error("❌ Não há anos disponíveis para teste após o período de treino")
        return

    test_year = st.sidebar.selectbox(
        "Ano para Teste", 
        available_test_years,
        index=0
    )

    # Configurações específicas por modelo
    if modelo_selecionado == "Prophet":
        seasonality_mode = st.sidebar.radio("Modo Sazonalidade", ["multiplicative", "additive"])
        include_holidays = st.sidebar.checkbox("Incluir Feriados", value=True)

    else:  # Random Forest
        st.sidebar.header("🔧 Parâmetros Random Forest")
        n_estimators = st.sidebar.slider("Número de Árvores", 50, 500, 100)
        lags_dias = st.sidebar.slider("Lags (dias históricos)", 7, 90, 14)
        include_weekends = st.sidebar.checkbox("Incluir Features de Fim de Semana", value=True)

    # VERIFICAÇÃO DE SEGURANÇA
    if not train_years or not test_year:
        st.error("❌ Selecione anos para treino e teste para continuar.")
        return

    # Verificar se há sobreposição de anos
    if test_year in train_years:
        st.error("❌ O ano de teste não pode estar nos anos de treino!")
        return

    # Verificar se há dados suficientes
    df_filtered = df[(df['Primary Type'] == selected_crime) & 
                     (df['Year'].isin(train_years + [test_year]))]

    if df_filtered.empty:
        st.error("❌ Não há dados para os anos selecionados!")
        return

    st.sidebar.success(f"✅ Dados carregados: {len(df_filtered):,} registros")
    st.sidebar.write(f"📊 Período: {df_filtered['Date'].min().strftime('%d/%m/%Y')} a {df_filtered['Date'].max().strftime('%d/%m/%Y')}")

    # FUNÇÃO CORRIGIDA: Preparar e dividir dados
    def preparar_e_dividir_dados(df_filtrado, train_years, test_year):
        """Prepara dados diários e divide corretamente"""
        # Garantir que temos dados
        if df_filtrado.empty:
            return pd.DataFrame(), pd.DataFrame(), None
        
        # Criar dados diários
        dados_diarios = df_filtrado.resample('D', on='Date').size().reset_index()
        dados_diarios.columns = ['ds', 'y']
        
        # Usar o final do último ano de treino como corte
        ultimo_ano_treino = max(train_years)
        data_corte = pd.Timestamp(f"{ultimo_ano_treino}-12-31")
        
        # Verificar se a data de corte está dentro dos dados
        if data_corte < dados_diarios['ds'].min() or data_corte > dados_diarios['ds'].max():
            st.error(f"❌ Data de corte {data_corte.strftime('%d/%m/%Y')} fora do range dos dados")
            return pd.DataFrame(), pd.DataFrame(), None
        
        dados_treino = dados_diarios[dados_diarios['ds'] <= data_corte]
        dados_teste = dados_diarios[dados_diarios['ds'] > data_corte]
        
        return dados_treino, dados_teste, data_corte

    # Botão para executar previsão
    if st.button(f"🚀 Executar {modelo_selecionado} (Dados Diários)", type="primary"):
        
        # Preparar dados
        dados_treino, dados_teste, data_corte = preparar_e_dividir_dados(df_filtered, train_years, test_year)
        
        # Verificar se as divisões não estão vazias
        if dados_treino.empty or dados_teste.empty:
            st.error("❌ Não há dados suficientes para treino e teste com o período selecionado!")
            return
        
        st.write(f"📅 Dados Diários - Treino: {len(dados_treino)} dias | Teste: {len(dados_teste)} dias")
        st.write(f"📊 Corte temporal: {data_corte.strftime('%d/%m/%Y')}")
        
        if modelo_selecionado == "Prophet":
            with st.spinner("Treinando modelo Prophet..."):
                try:
                    # Tentar importar Prophet
                    try:
                        from prophet import Prophet
                    except ImportError:
                        st.error("❌ Biblioteca Prophet não instalada. Execute: pip install prophet")
                        return
                    
                    # Configurar o modelo Prophet
                    model = Prophet(
                        seasonality_mode=seasonality_mode,
                        yearly_seasonality=True,
                        weekly_seasonality=True,
                        daily_seasonality=False
                    )
                    
                    # Adicionar feriados se selecionado
                    if include_holidays:
                        model.add_country_holidays(country_name='US')
                    
                    # Treinar o modelo
                    model.fit(dados_treino)
                    
                    # Criar dataframe futuro para previsão
                    future = model.make_future_dataframe(periods=len(dados_teste), freq='D', include_history=False)
                    forecast = model.predict(future)
                    
                    # Combinar previsões com dados reais
                    forecast_test = forecast[['ds', 'yhat', 'yhat_lower', 'yhat_upper']]
                    resultados = pd.merge(dados_teste, forecast_test, on='ds', how='left')
                    
                    # Calcular métricas
                    valid_results = resultados.dropna()
                    if valid_results.empty:
                        st.error("❌ Não foi possível calcular métricas - dados inválidos")
                        return
                    
                    mape = mean_absolute_percentage_error(valid_results['y'], valid_results['yhat']) * 100
                    mae = mean_absolute_error(valid_results['y'], valid_results['yhat'])
                    mse = mean_squared_error(valid_results['y'], valid_results['yhat'])
                    rmse = np.sqrt(mse)
                    
                    # Exibir métricas
                    st.success("✅ Previsão Prophet concluída!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("MAPE", f"{mape:.2f}%")
                    col2.metric("MAE", f"{mae:.2f}")
                    col3.metric("MSE", f"{mse:.2f}")
                    col4.metric("RMSE", f"{rmse:.2f}")
                    
                    # Gráfico comparativo
                    st.subheader("📊 Comparação: Previsão vs Real")
                    
                    fig = go.Figure()
                    
                    # Dados de treino
                    fig.add_trace(go.Scatter(
                        x=dados_treino['ds'], y=dados_treino['y'],
                        mode='lines', name='Treino',
                        line=dict(color='blue', width=1),
                        opacity=0.7
                    ))
                    
                    # Dados reais de teste
                    fig.add_trace(go.Scatter(
                        x=resultados['ds'], y=resultados['y'],
                        mode='lines', name='Real (Teste)',
                        line=dict(color='green', width=2)
                    ))
                    
                    # Previsões
                    fig.add_trace(go.Scatter(
                        x=resultados['ds'], y=resultados['yhat'],
                        mode='lines', name=f'Prophet (MAPE: {mape:.1f}%)',
                        line=dict(color='red', width=2, dash='dash')
                    ))
                    
                    # Intervalo de confiança
                    fig.add_trace(go.Scatter(
                        x=resultados['ds'], y=resultados['yhat_upper'],
                        mode='lines', name='Intervalo Superior',
                        line=dict(color='red', width=1, dash='dot'),
                        opacity=0.3,
                        showlegend=False
                    ))
                    
                    fig.add_trace(go.Scatter(
                        x=resultados['ds'], y=resultados['yhat_lower'],
                        mode='lines', name='Intervalo Inferior',
                        line=dict(color='red', width=1, dash='dot'),
                        opacity=0.3,
                        fill='tonexty',
                        showlegend=False
                    ))
                    
                    fig.update_layout(
                        title=f'Previsão Diária de {selected_crime} - Prophet ({test_year})',
                        xaxis_title='Data',
                        yaxis_title='Número de Crimes por Dia',
                        hovermode='x unified',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Componentes do Prophet
                    st.subheader("🔍 Componentes do Modelo Prophet")
                    
                    try:
                        fig_components = model.plot_components(forecast)
                        st.pyplot(fig_components)
                    except Exception as e:
                        st.info(f"Visualização de componentes não disponível: {e}")
                    
                except Exception as e:
                    st.error(f"❌ Erro no Prophet: {str(e)}")
                    
        else:  # RANDOM FOREST COM DADOS DIÁRIOS
            with st.spinner("Treinando Random Forest (dados diários)..."):
                try:
                    # 1. Combinar dados de treino e teste
                    df_rf = pd.concat([dados_treino, dados_teste]).set_index('ds')
                    df_rf = df_rf.sort_index()

                    # 2. Função para criar features DIÁRIAS
                    def criar_features_diarias_sklearn(df, lags_dias=30):
                        """Cria features temporais DIÁRIAS para scikit-learn"""
                        
                        df_features = df.copy()
                        
                        # Features básicas de tempo DIÁRIAS
                        df_features['day_of_week'] = df_features.index.dayofweek
                        df_features['day_of_month'] = df_features.index.day
                        df_features['month'] = df_features.index.month
                        df_features['year'] = df_features.index.year
                        df_features['quarter'] = df_features.index.quarter
                        df_features['week_of_year'] = df_features.index.isocalendar().week.astype(int)
                        
                        # Fim de semana
                        df_features['is_weekend'] = (df_features.index.dayofweek >= 5).astype(int)
                        
                        # Feriados
                        us_holidays = holidays.US()
                        df_features['is_holiday'] = [date in us_holidays for date in df_features.index]
                        df_features['is_holiday'] = df_features['is_holiday'].astype(int)
                        
                        # Estações do ano
                        def get_season(month):
                            if month in [12, 1, 2]: return 0  # Inverno
                            elif month in [3, 4, 5]: return 1  # Primavera
                            elif month in [6, 7, 8]: return 2  # Verão
                            else: return 3  # Outono
                        
                        df_features['season'] = df_features.index.month.map(get_season)
                        
                        # Final de ano
                        df_features['is_year_end'] = df_features.index.month.isin([11, 12]).astype(int)
                        
                        # Lags DIÁRIOS
                        for lag in range(1, lags_dias + 1):
                            df_features[f'lag_{lag}d'] = df_features['y'].shift(lag)
                        
                        # Médias móveis DIÁRIAS
                        df_features['rolling_mean_7d'] = df_features['y'].rolling(window=7, min_periods=1).mean()
                        df_features['rolling_mean_30d'] = df_features['y'].rolling(window=30, min_periods=1).mean()
                        
                        return df_features

                    # Criar features diárias
                    crimes_com_features = criar_features_diarias_sklearn(df_rf, lags_dias)
                    
                    # Remover linhas com NaN (devido aos lags)
                    crimes_com_features = crimes_com_features.dropna()
                    
                    if crimes_com_features.empty:
                        st.error("❌ Não foi possível criar features - dados insuficientes após processamento")
                        return
                    
                    st.write(f"📈 Features diárias criadas: {len(crimes_com_features.columns) - 1} variáveis")

                    # 3. Split treino/teste
                    train = crimes_com_features[crimes_com_features.index <= data_corte]
                    test = crimes_com_features[crimes_com_features.index > data_corte]

                    if train.empty or test.empty:
                        st.error("❌ Não há dados suficientes para treino e teste com o período selecionado.")
                        return

                    st.write(f"🎯 Treino: {len(train)} dias | Teste: {len(test)} dias")

                    # 4. Preparar features e target
                    feature_columns = [col for col in crimes_com_features.columns if col != 'y']
                    X_train = train[feature_columns]
                    y_train = train['y']
                    X_test = test[feature_columns]
                    y_test = test['y']

                    # 5. Normalizar features
                    scaler = StandardScaler()
                    X_train_scaled = scaler.fit_transform(X_train)
                    X_test_scaled = scaler.transform(X_test)

                    # 6. Modelo Random Forest
                    model_rf = RandomForestRegressor(
                        n_estimators=n_estimators,
                        random_state=42,
                        n_jobs=-1
                    )

                    model_rf.fit(X_train_scaled, y_train)

                    # 7. Previsões
                    y_pred = model_rf.predict(X_test_scaled)

                    # 8. Métricas
                    mape_rf = mean_absolute_percentage_error(y_test, y_pred) * 100
                    mae_rf = mean_absolute_error(y_test, y_pred)
                    mse_rf = mean_squared_error(y_test, y_pred)
                    rmse_rf = np.sqrt(mse_rf)

                    # Exibir métricas
                    st.success("✅ Previsão Random Forest (Diária) concluída!")
                    
                    col1, col2, col3, col4 = st.columns(4)
                    col1.metric("MAPE", f"{mape_rf:.2f}%")
                    col2.metric("MAE", f"{mae_rf:.2f}")
                    col3.metric("MSE", f"{mse_rf:.2f}")
                    col4.metric("RMSE", f"{rmse_rf:.2f}")

                    # 9. Gráfico comparativo DIÁRIO
                    st.subheader("📊 Comparação Diária: Previsão vs Real")
                    
                    results_df = pd.DataFrame({
                        'Real': y_test,
                        'Previsao': y_pred
                    }, index=y_test.index)

                    fig = go.Figure()
                    
                    # Treino
                    fig.add_trace(go.Scatter(
                        x=train.index, y=train['y'],
                        mode='lines', name='Treino',
                        line=dict(color='blue', width=1),
                        opacity=0.7
                    ))
                    
                    # Teste Real
                    fig.add_trace(go.Scatter(
                        x=results_df.index, y=results_df['Real'],
                        mode='lines', name='Real (Teste)',
                        line=dict(color='green', width=2)
                    ))
                    
                    # Previsão
                    fig.add_trace(go.Scatter(
                        x=results_df.index, y=results_df['Previsao'],
                        mode='lines', name=f'Random Forest (MAPE: {mape_rf:.1f}%)',
                        line=dict(color='red', width=2, dash='dash')
                    ))
                    
                    fig.update_layout(
                        title=f'Previsão Diária de {selected_crime} - Random Forest ({test_year})',
                        xaxis_title='Data',
                        yaxis_title='Número de Crimes por Dia',
                        hovermode='x unified',
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)

                    # 10. Tabela de comparação
                    st.subheader("📈 Amostra de Previsões Diárias")
                    
                    comparacao = pd.DataFrame({
                        'Data': results_df.index.strftime('%d/%m/%Y'),
                        'Real': results_df['Real'],
                        'Previsto': results_df['Previsao'],
                        'Erro_Absoluto': np.abs(results_df['Real'] - results_df['Previsao']),
                        'Erro_Percentual': (np.abs(results_df['Real'] - results_df['Previsao']) / results_df['Real']) * 100
                    }).head(15)

                    st.dataframe(comparacao.round(2), use_container_width=True)

                    # 11. Importância das Features
                    st.subheader("🔍 Top 10 Features Mais Importantes")
                    
                    feature_importance = pd.DataFrame({
                        'feature': feature_columns,
                        'importance': model_rf.feature_importances_
                    }).sort_values('importance', ascending=False).head(10)

                    fig_importance = go.Figure()
                    fig_importance.add_trace(go.Bar(
                        x=feature_importance['importance'],
                        y=feature_importance['feature'],
                        orientation='h'
                    ))
                    fig_importance.update_layout(
                        title='Top 10 Features Mais Importantes (Dados Diários)',
                        xaxis_title='Importância',
                        yaxis_title='Features',
                        height=400
                    )
                    st.plotly_chart(fig_importance, use_container_width=True)

                except Exception as e:
                    st.error(f"❌ Erro no Random Forest: {str(e)}")

    else:
        # Tela inicial - informações sobre os modelos
        st.markdown(f"""
        ### 📋 Comparação Justa: Ambos Modelos com Dados Diários
        
        Agora **Prophet** e **Random Forest** usam a mesma granularidade temporal:
        
        - ✅ **Dados diários** para ambos os modelos
        - ✅ **Mesmo período** de treino e teste  
        - ✅ **Métricas comparáveis** (MAPE, MAE, RMSE)
        - ✅ **Visualização consistente**
        
        **Configuração Temporal:**
        - Treino: {min(train_years)} a {max(train_years)}
        - Teste: {test_year}
        - Tipo de Crime: {selected_crime}
        """)
        
        if modelo_selecionado == "Prophet":
            st.markdown("""
            **Prophet (Diário):**
            - Sazonalidade automática diária/semanal/anual
            - Feriados e eventos especiais
            - Ideal para padrões complexos e tendências
            """)
        else:
            st.markdown("""
            **Random Forest (Diário):**
            - Features temporais diárias (dia da semana, feriados, etc.)
            - Lags históricos em dias
            - Médias móveis de 7 e 30 dias
            - Identifica padrões não-lineares complexos
            """)

    # Footer
    st.markdown("---")
    st.markdown("**Módulo de Predição - Chicago Crime Analytics**")

if __name__ == "__main__":
    main()