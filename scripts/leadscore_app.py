# === Imports Padrões ===
import gspread
import joblib
import logging
import os
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st
import sys
import time

from cycler import cycler
from datetime import datetime
from dotenv import load_dotenv
from google.oauth2 import service_account
from gspread_dataframe import get_as_dataframe
from io import BytesIO
from pathlib import Path


# Garante que a pasta raiz (escola_policia) esteja no sys.path
root_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(root_dir))

# === Configuração de logging segura para nuvem (Streamlit Cloud) ===
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    stream=sys.stdout  # 🔒 Apenas console
)

logger = logging.getLogger(__name__)
logger.info("App iniciado")

# === Imports dos módulos internos ===
from notebooks.src.leadscore_plot_app import (
    plot_comparativo_leads_alunos,
    plot_histograma_leadscore,
    plot_stacked_100_percent,
    plot_entrada_leads,
    plot_utm_source_por_faixa
)
from notebooks.src.leadscore_tabelas import (
    gerar_tabela_faixas_leads_alunos,
    destacar_total_linha,
    top1_utms_por_leads_A,
    gerar_tabela_utm_personalizada,
    gerar_tabela_estatisticas_leadscore,
    detalhar_leadscore_por_variavel,
    gerar_comparativo_faixas,
    mostrar_lift_e_calculo_individual,
    exibir_tabela_faixa_origem
)

# === Configuração Inicial do Streamlit ===
st.set_page_config(page_title="Leadscore QG Concursos", layout="wide")

# === Carregar variáveis de ambiente ===
load_dotenv()

# === Ajuste base_path para apontar à raiz do projeto ===
base_path = Path(__file__).resolve().parent.parent  # scripts/ → raiz do projeto

# === URL base da API e token ===
API_PARQUET_URL = os.getenv("API_PARQUET_URL")  # ex: https://escola-policia.fly.dev
API_TOKEN = os.getenv("API_TOKEN")  # mesmo token usado no curl

def baixar_parquet(nome_arquivo):
    url = f"{API_PARQUET_URL}/dados/{nome_arquivo}"
    headers = {"Authorization": f"Bearer {API_TOKEN}"}
    response = requests.get(url, headers=headers)

    if response.status_code != 200:
        raise Exception(f"Erro ao baixar {nome_arquivo}: {response.status_code} - {response.text}")

    return pd.read_parquet(BytesIO(response.content))

# === Carregar os dados ===
df_leads = baixar_parquet("leads_leadscore.parquet")
df_alunos = baixar_parquet("alunos_leadscore.parquet")

# === Arquivos obrigatórios (modelos e atualizacao.txt) ===
required_files = [
    leads_path,
    alunos_path,
    base_path / "modelos" / "limites_faixa.pkl",
    base_path / "modelos" / "score_map.pkl",
    base_path / "modelos" / "tabelas_lift.pkl"
]

missing_files = [str(f) for f in required_files if not f.exists()]
if missing_files:
    st.error(f"❌ Arquivos ausentes:\n\n{chr(10).join(missing_files)}")
    logger.error(f"Arquivos ausentes: {missing_files}")
    st.stop()

# === Carregar Dados ===
try:
    inicio = time.time()
    logger.info("Carregando arquivos .parquet")
    df_leads = pd.read_parquet(leads_path)
    df_alunos = pd.read_parquet(alunos_path)
    df_leads['data'] = pd.to_datetime(df_leads['data'], errors='coerce')
    df_leads_antigos = df_leads[df_leads["lancamentos"] != "L34"]
    df_leads_novos = df_leads[df_leads["lancamentos"] == "L34"]
    fim = time.time()
    logger.info(f"Dados carregados com sucesso em {fim - inicio:.2f}s")
except Exception as e:
    logger.exception("Erro ao carregar arquivos de dados")
    st.error(f"Erro ao carregar os dados: {e}")
    st.stop()


# === Carregar Configurações salvas ===
try:
    logger.info("Carregando modelos")
    path_modelos = base_path / "modelos"
    limites = joblib.load(path_modelos / "limites_faixa.pkl")
    score_map = joblib.load(path_modelos / "score_map.pkl")
    tabelas_lift = joblib.load(path_modelos / "tabelas_lift.pkl")
    logger.info("Modelos carregados com sucesso")
except Exception as e:
    logger.exception("Erro ao carregar arquivos de modelo")
    st.error(f"Erro ao carregar configurações: {e}")
    st.stop()

# === Paleta de cores ===
cores = plt.get_cmap('Accent').colors
ciclo_cores = cycler('color', cores)
plt.rc('axes', prop_cycle=ciclo_cores)

# === Adicionar o horário de atualização do painel ===
try:
    logger.info("Lendo data de atualização")
    with open(base_path / "config" / "ultima_atualizacao.txt", "r") as f:
        texto = f.read().strip()
        dt = datetime.strptime(texto, "%Y-%m-%d %H:%M:%S")
        data_atualizacao_formatada = dt.strftime("%d/%m/%Y %H:%M")
except Exception as e:
    logger.warning("Erro ao ler data de atualização")
    data_atualizacao_formatada = "Desconhecida"
    st.error(f"[ERRO ao ler data de atualização]: {e}")

logger.info("Interface Streamlit carregada com sucesso")


# === Interface ===
aba1, aba2 = st.tabs(["📈 Leadscore QG Concursos", "🧮 Como Calculamos o Leadscore"])

# === Aba 1: Lançamentos Anteriores ===
with aba1:
    st.title("📈 Leadscore QG Concursos")
    st.markdown(f"**Última atualização:** {data_atualizacao_formatada}")

    # Layout compacto: cada filtro ocupa 1/5 da largura
    col_lancamento, col_data, _ = st.columns([1, 1, 3])
    
    with col_lancamento:
        ordem_personalizada = ["L31", "L32", "L33", "L34"]
        lancamentos_unicos = df_leads["lancamentos"].dropna().unique()
        
        # Filtra apenas os que existem no DataFrame e estão na ordem desejada
        lancamentos_ordenados = [l for l in ordem_personalizada if l in lancamentos_unicos]
        lancamentos_todos = lancamentos_ordenados

        filtro_lancamento = st.selectbox(
            "Selecione o Lançamento para filtrar:",
            options=lancamentos_todos,
            index=lancamentos_todos.index("L34") if "L34" in lancamentos_todos else 0
        )
    
    # Filtrar dados antes de calcular datas mínimas e máximas
    df_filtrado = df_leads[df_leads["lancamentos"] == filtro_lancamento].copy()
    if filtro_lancamento != "Todos":
        df_filtrado = df_filtrado[df_filtrado["lancamentos"] == filtro_lancamento]
    
    # Para L3-25 fixar a data mínima; para os demais, pegar a mínima real
    if filtro_lancamento == "L34":
        data_min = pd.to_datetime("2025-05-17").date()
    else:
        data_min = df_filtrado['data'].min().date()
    
    # Máxima segue igual para todos
    data_max = df_filtrado['data'].max().date()
    
    with col_data:
        intervalo_datas = st.date_input(
            "Selecione o intervalo de datas:",
            value=(data_min, data_max),
            min_value=data_min,
            max_value=data_max,
            format="DD/MM/YYYY"
        )
    
    # Agora sim aplica o filtro final de datas
    if isinstance(intervalo_datas, tuple) and len(intervalo_datas) == 2:
        data_inicio, data_fim = intervalo_datas
        df_filtrado = df_filtrado[
            (df_filtrado['data'].dt.date >= data_inicio) &
            (df_filtrado['data'].dt.date <= data_fim)
        ]

    # === Aplicar filtro extra de data mínima SOMENTE para o L3-25 ===
    if filtro_lancamento == "L34":
        data_limite = pd.to_datetime("2025-05-17")
        df_filtrado = df_filtrado[df_filtrado["data"] >= data_limite]

    df_alunos_filtrado = df_alunos.copy()
    if filtro_lancamento != "Todos":
        df_alunos_filtrado = df_alunos_filtrado[df_alunos_filtrado["lancamentos"] == filtro_lancamento]

    if 'data' in df_alunos_filtrado.columns:
        df_alunos_filtrado['data'] = pd.to_datetime(df_alunos_filtrado['data'], errors='coerce')
        df_alunos_filtrado = df_alunos_filtrado[
            (df_alunos_filtrado['data'].dt.date >= df_filtrado['data'].min().date()) &
            (df_alunos_filtrado['data'].dt.date <= df_filtrado['data'].max().date())
        ]

    if df_filtrado.empty:
        st.warning("⚠️ Nenhum lead encontrado para os filtros selecionados. Tente mudar os filtros.")
        st.stop()

    campos_utm = ["utm_source", "utm_campaign", "utm_medium", "utm_content", "utm_term"]
    
    st.markdown("---")
    st.subheader("Considerações iniciais")
    st.markdown("A entrada de leads no Leadscore considera apenas aqueles que responderam à `pesquisa` e possuem `UTMs`. Da mesma forma, os alunos analisados são apenas os que também estão vinculados a esses leads de cada lançamento.")
    df_filtrado = plot_entrada_leads(df_filtrado)

    st.markdown("---")
    exibir_tabela_faixa_origem(df_filtrado, df_leads, df_alunos)

    st.markdown("---")
    st.subheader("Análise Detalhada de Conversão - UTM's")
    plot_utm_source_por_faixa(df_filtrado)

    st.markdown("---")
    st.markdown("### 🔍 Análises por UTM's")
    filtros_aplicados = {}
    
    df_base_filtrado = df_filtrado.copy()
    
    for idx, campo in enumerate(campos_utm):
        st.subheader(f"🔹 Campo: `{campo}`")
    
        # Pega apenas valores válidos
        opcoes = df_base_filtrado[campo].dropna().astype(str)
        opcoes = opcoes[~opcoes.str.strip().isin(["", "nan"])]
        opcoes = opcoes[~opcoes.str.contains(r"\{\{.*?\}\}")]
        opcoes = sorted(opcoes.unique().tolist())
    
        col_filtro, _ = st.columns([2, 5])
        with col_filtro:
            valor_utm = st.selectbox(
                label="Selecione o valor da UTM:",
                options=["Todos"] + opcoes,
                key=f"filtro_{campo}"
            )
    
        # Salvar filtro aplicado
        filtros_aplicados[campo] = valor_utm
    
        # Aplicar filtro somente se valor for específico
        if valor_utm != "Todos":
            df_base_filtrado = df_base_filtrado[df_base_filtrado[campo] == valor_utm]
    
        # Gerar tabela para o campo atual, com base no DF filtrado até aqui
        styled_tabela = gerar_tabela_utm_personalizada(df_base_filtrado, campo)
    
        if styled_tabela is None:
            st.info(f"Nenhum dado disponível para `{campo}`.")
        else:
            st.dataframe(styled_tabela, use_container_width=True)


# === Aba 2: Como Calculamos ===
with aba2:
    st.title("🧮 Como Calculamos o Leadscore")
    st.markdown(f"**Última atualização:** {data_atualizacao_formatada}")

    st.markdown("""
    O Leadscore foi desenvolvido a partir de variáveis importantes que se correlacionam com a decisão de compra:
    
     - **Renda**
    - **Escolaridade**
    - **Idade**
    - **Filhos**
    - **Estado Civil**
    - **Escolheu Profissão**

    A partir dessas variáveis, foi criado um `score ponderado` e os leads foram classificados em faixas **A, B, C, D** de acordo com o potencial de conversão.
    """)

    st.markdown("---")
    st.markdown("### Como funcionam os limites de score")

    if "leadscore_mapeado" not in df_leads.columns:
        st.warning("Leadscore ainda não calculado. Execute o cálculo de Leadscore primeiro.")
    else:
        col1, col2 = st.columns([0.7, 1.3])

        with col1:
            st.markdown("""
            **A média foi o ponto de partida para definir as faixas:**
            """)
            media_score = limites["media_compradores"]

            st.markdown(
                f"""
                <div style='background-color: #fff3cd; color: #000; display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 16px; line-height: 1.2;'>
                    Média Geral do Score: {media_score:.2f}
                </div>
                """,
                unsafe_allow_html=True
            )
            st.write("")
            st.markdown(f"🔹 **Faixa A** (≥ 110% da média): {limites['limite_a']:.2f}")
            st.markdown(f"🔹 **Faixa B** (≥  90% da média): {limites['limite_b']:.2f}")
            st.markdown(f"🔹 **Faixa C** (≥  70% da média): {limites['limite_c']:.2f}")
            st.markdown(f"🔹 **Faixa D** (≥  50% da média): {limites['limite_d']:.2f}")

            gerar_tabela_estatisticas_leadscore(df_leads)

        with col2:
            fig = plot_histograma_leadscore(
                df_leads,
                limite_a=limites["limite_a"],
                limite_b=limites["limite_b"],
                limite_c=limites["limite_c"],
                limite_d=limites["limite_d"]
            )
            st.pyplot(fig)

    st.markdown("---")
    st.markdown("### Comparativo das Faixas entre Leads x Alunos")

    plot_comparativo_leads_alunos(df_leads, df_alunos)
    
    st.markdown("---")
    st.markdown("### Análise do Lift (peso) por Variável")
    st.markdown("""
    O `Lift` é obtido dividindo a **porcentagem de alunos** pela **porcentagem de leads** em cada categoria. Já o `Score Final` é o resultado do `Lift` multiplicado pelo número absoluto de alunos na categoria.
    """)
    st.write("")
        
    mostrar_lift_e_calculo_individual(tabelas_lift, df_leads, score_map, limites)
    
    st.markdown("---")
    st.markdown("### Distribuição Percentual das Categorias por Faixa de Leadscore")
    st.markdown("**Aqui podemos ver como as respostas dos alunos se distribuem proporcionalmente em cada faixa de score de acordo com a categoria. Isso permite visualizar, por exemplo, quais características são mais comuns entre os alunos com score mais alto (Faixa A) ou mais baixo (Faixa D).**")

    variavel_selecionada = st.selectbox(
        "Selecione a variável para análise:",
        options=["renda", "escolaridade", "idade", "filhos", "estado_civil", "escolheu_profissao"],
        key="seletor_plot"
    )
    
    plot_stacked_100_percent(df_leads, variavel_selecionada)

    gerar_comparativo_faixas(df_leads)