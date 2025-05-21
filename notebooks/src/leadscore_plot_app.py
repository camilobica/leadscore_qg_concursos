from cycler import cycler
from datetime import datetime
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns
import streamlit as st

# Definição das paletas de cores
cores = plt.get_cmap('tab20b').colors
ciclo_cores = cycler('color', cores)
plt.rc('axes', prop_cycle=ciclo_cores)

# Definição do layout dos gráficos
LIGHT_DARK_COLOR = '#262730'

plt.rcParams['figure.facecolor'] = LIGHT_DARK_COLOR
plt.rcParams['axes.facecolor'] = LIGHT_DARK_COLOR

plt.rcParams['text.color'] = 'white'
plt.rcParams['axes.labelcolor'] = 'white'
plt.rcParams['xtick.color'] = 'white'
plt.rcParams['ytick.color'] = 'white'
plt.rcParams['axes.titlecolor'] = 'white'
plt.rcParams['legend.labelcolor'] = 'white'


# === ABA 1 ===
def plot_entrada_leads(df_filtrado: pd.DataFrame) -> pd.DataFrame:
    df_filtrado['data'] = pd.to_datetime(df_filtrado['data'], errors='coerce')
    df_filtrado = df_filtrado.dropna(subset=['data'])

    # Agrupar por dia
    leads_diarios = (
        df_filtrado
        .groupby(df_filtrado['data'].dt.date)
        .size()
        .rename("leads")
        .reset_index()
    )
    leads_diarios["data"] = pd.to_datetime(leads_diarios["data"])
    leads_diarios = leads_diarios.sort_values("data")

    # Detectar primeira quebra > 7 dias
    leads_diarios["dias_diff"] = leads_diarios["data"].diff().dt.days
    if (leads_diarios["dias_diff"] > 7).any():
        corte_idx = leads_diarios[leads_diarios["dias_diff"] > 7].index[0]
        leads_diarios = leads_diarios.loc[:corte_idx - 1]

    # Plot
    dias_plot = len(leads_diarios)
    largura = max(20, min(1 * dias_plot, 10)) 
    fig, ax = plt.subplots(figsize=(largura, 5))

    ax.plot(leads_diarios['data'], leads_diarios['leads'], marker='o', color='lightgreen')

    margem_texto = leads_diarios['leads'].max() * 0.03
    for x, y in zip(leads_diarios['data'], leads_diarios['leads']):
        ax.text(x, y + margem_texto, str(y), ha='center', va='bottom', fontsize=9)

    locator_interval = 1 if dias_plot <= 10 else int(dias_plot / 10)
    ax.xaxis.set_major_locator(mdates.DayLocator(interval=locator_interval))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%d/%m'))

    ax.set_title("Entrada de Leads por Dia", fontsize=14, pad=20)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_yticks([])
    ax.tick_params(axis='x', length=5)  
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.grid(False)

    st.pyplot(fig)
    leads_dates = leads_diarios["data"].dt.normalize().unique()
    df_filtrado = df_filtrado[df_filtrado["data"].dt.normalize().isin(leads_dates)]
    return df_filtrado



def plot_utm_source_por_faixa(df_leads):
    # Verifica se a coluna esperada existe
    if "leadscore_faixa" not in df_leads.columns or "utm_source" not in df_leads.columns:
        st.warning("Colunas necessárias não estão presentes no DataFrame.")
        return

    # Filtro de faixa com opção "Todos"
    faixas_disponiveis = sorted(df_leads["leadscore_faixa"].dropna().unique())
    opcoes_faixa = ["Todos"] + faixas_disponiveis
    col_select, _ = st.columns([1, 5])
    with col_select:
        faixa_selecionada = st.selectbox("Selecione a Faixa:", opcoes_faixa, index=0)


    # Filtrar por faixa, se necessário
    if faixa_selecionada != "Todos":
        df_filtrado = df_leads[df_leads["leadscore_faixa"] == faixa_selecionada].copy()
    else:
        df_filtrado = df_leads.copy()

    # Antes de contar
    df_filtrado["utm_source"] = df_filtrado["utm_source"].fillna("não informado")

    # Exibir somente os TOP 10
    top_n = 10
    contagem_utm = df_filtrado["utm_source"].value_counts().nlargest(top_n)
    contagem_percentual = (df_filtrado["utm_source"].value_counts(normalize=True).nlargest(top_n) * 100).round(1)


    df_plot = pd.DataFrame({
        "Qtd Leads": contagem_utm,
        "% Leads": contagem_percentual.round(1)
    })

    # Plotar
    plt.figure(figsize=(18, 4)) 
    labels = df_plot.index
    x = np.arange(len(labels))
    width = 0.6

    bars = plt.bar(x, df_plot["Qtd Leads"], width, color=cores[1])

    for i, bar in enumerate(bars):
        height = bar.get_height()
        pct = df_plot["% Leads"].iloc[i]
        if height > 0:
            plt.text(bar.get_x() + bar.get_width() / 2, height + 2.7, f"{height} ({pct:.1f}%)", ha='center', va='bottom')

    titulo = f"Leads por UTM Source - Faixa {faixa_selecionada}" if faixa_selecionada != "Todos" else "Leads por UTM Source - Todas as Faixas"
    plt.title(titulo, pad=20)
    plt.xticks(x, labels)
    plt.ylabel("")
    plt.tick_params(axis='x', length=0)
    plt.yticks([])
    plt.grid(False)
    plt.tight_layout()

    for spine in ["top", "right", "left", "bottom"]:
        plt.gca().spines[spine].set_visible(False)

    st.pyplot(plt.gcf())
    plt.clf()
    

# === ABA 2 ===
def plot_histograma_leadscore(df, limite_a, limite_b, limite_c, limite_d):
    bins_leadscore = np.histogram_bin_edges(df["leadscore_mapeado"], bins="sturges")
    bins_leadscore = np.round(bins_leadscore).astype(int)

    interval_labels = [f"{bins_leadscore[i]}–{bins_leadscore[i+1]}" for i in range(len(bins_leadscore) - 1)]
    bin_centers = (bins_leadscore[:-1] + bins_leadscore[1:]) / 2

    fig, ax = plt.subplots(figsize=(12, 5))
    sns.histplot(df["leadscore_mapeado"], bins=bins_leadscore, color=cores[1], ax=ax)

    ax.axvline(limite_a, color=cores[6], linestyle="--", label="Limite A")
    ax.axvline(limite_b, color=cores[18], linestyle="--", label="Limite B")
    ax.axvline(limite_c, color=cores[10], linestyle="--", label="Limite C")
    ax.axvline(limite_d, color=cores[14], linestyle="--", label="Limite D")

    ymax = ax.get_ylim()[1]
    ax.text(limite_a, ymax * 1.02, "Limite A >", color=cores[6], ha="center", fontsize=10)
    ax.text(limite_b, ymax * 1.02, "Limite B >", color=cores[18], ha="center", fontsize=10)
    ax.text(limite_c, ymax * 1.02, "Limite C >", color=cores[10], ha="center", fontsize=10)
    ax.text(limite_d, ymax * 1.02, "Limite D >", color=cores[14], ha="center", fontsize=10)

    ax.set_xticks(bin_centers)
    ax.set_xticklabels(interval_labels, rotation=30, ha="right")

    ax.set_title("Distribuição das Faixas no Leadscore", y=1.1)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_yticks([])

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.legend()
    plt.tight_layout()

    return fig


def plot_comparativo_leads_alunos(df_leads, df_alunos):
    ordem_personalizada = ["L28", "L29", "L30", "L31", "L32", "L33", "L34"]
    lancamentos_unicos = df_leads["lancamentos"].dropna().unique()
    lancamentos_ordenados = ["Todos"] + [l for l in ordem_personalizada if l in lancamentos_unicos]

    col_filtro, _ = st.columns([1, 5])
    with col_filtro:
        lancamento_selecionado = st.selectbox("Selecione o Lançamento:", lancamentos_ordenados)

    # Aplica o filtro de lançamento
    df_leads_filt = df_leads.copy()
    df_alunos_filt = df_alunos.copy()

    if lancamento_selecionado != "Todos":
        df_leads_filt = df_leads[df_leads["lancamentos"] == lancamento_selecionado]
        df_alunos_filt = df_alunos[df_alunos["lancamentos"] == lancamento_selecionado]

    # Mostrar totais após o filtro
    st.markdown(f"🔹 **Total de Leads:** {len(df_leads_filt):,}".replace(",", "."))
    st.markdown(f"🔹 **Total de Alunos:** {len(df_alunos_filt):,}".replace(",", "."))
    
    # Proporções por faixa
    contagem_prevista = df_leads_filt["leadscore_faixa"].value_counts(normalize=True).sort_index() * 100
    contagem_real = df_alunos_filt["leadscore_faixa"].value_counts(normalize=True).sort_index() * 100

    comparativo_perc = pd.DataFrame({
        "Leads (%)": contagem_prevista,
        "Alunos (%)": contagem_real
    }).fillna(0).round(1)

    comparativo_perc["Variação (p.p.)"] = (
        comparativo_perc["Leads (%)"] - comparativo_perc["Alunos (%)"]
    ).round(1)

    # Plot
    plt.figure(figsize=(14, 4))
    labels = comparativo_perc.index
    x = np.arange(len(labels))
    width = 0.35

    bars1 = plt.bar(x - width/2, comparativo_perc["Leads (%)"], width, label="Leads (%)", color=cores[1])
    bars2 = plt.bar(x + width/2, comparativo_perc["Alunos (%)"], width, label="Alunos (%)", color=cores[4])

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                plt.text(bar.get_x() + bar.get_width() / 2, height + 1.5, f"{height:.1f}%", ha='center', va='bottom')

    plt.ylim(0, max(comparativo_perc.max()) + 5)
    plt.ylabel("")
    plt.xticks(x, labels)
    plt.tick_params(axis='x', length=0)
    plt.yticks([])
    plt.legend()

    for spine in ["top", "right", "left", "bottom"]:
        plt.gca().spines[spine].set_visible(False)

    plt.tight_layout()
    st.pyplot(plt.gcf())
    plt.clf()



def plot_stacked_100_percent(df, variavel):
    if "leadscore_faixa" not in df.columns:
        st.error("leadscore_faixa não encontrado no DataFrame!")
        return

    dist = pd.crosstab(df[variavel], df["leadscore_faixa"], normalize='index') * 100
    dist = dist.fillna(0)

    cores_local = plt.get_cmap('Accent').colors
    fig, ax = plt.subplots(figsize=(15, 5))
    bottom = pd.Series([0] * len(dist), index=dist.index)

    for i, faixa in enumerate(dist.columns):
        bars = ax.bar(dist.index, dist[faixa], label=faixa, bottom=bottom, color=cores_local[i])

        for bar in bars:
            height = bar.get_height()
            if height > 5:
                ax.text(
                    bar.get_x() + bar.get_width() / 2,
                    bar.get_y() + height / 2,
                    f'{height:.1f}%',
                    ha='center',
                    va='center',
                    color='black',
                    fontsize=9
                )
        bottom += dist[faixa]

    ax.set_ylabel("Percentual (%)")
    ax.set_ylim(0, 100)
    ax.set_title(f"Distribuição de Faixa - {variavel.capitalize()}", fontsize=14, pad=10)
    ax.set_ylabel("")
    ax.set_yticks([])
    ax.legend(title="Faixa", bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.xticks(ha='center')
    plt.grid(False)

    st.pyplot(fig)
