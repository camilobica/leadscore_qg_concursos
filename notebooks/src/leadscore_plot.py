from cycler import cycler

import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd
import seaborn as sns

# Definição das paletas de cores
cores = plt.get_cmap('Accent').colors
ciclo_cores = cycler('color', cores)
plt.rc('axes', prop_cycle=ciclo_cores)


def plot_histograma_leadscore(df, limite_a, limite_b, limite_c, limite_d):
    """
    Plota histograma do leadscore estimado total com linhas verticais para os limites das faixas.

    Parâmetros:
    ----------
    df : pd.DataFrame
        DataFrame contendo a coluna 'leadscore_estimado_total'.
    limite_a, limite_b, limite_c, limite_d : float
        Limites das faixas A, B, C e D (em ordem decrescente).
    """
    bins_leadscore = np.histogram_bin_edges(df["leadscore_mapeado"], bins="sturges")
    bins_leadscore = np.round(bins_leadscore).astype(int)

    interval_labels = [f"{bins_leadscore[i]}–{bins_leadscore[i+1]}" for i in range(len(bins_leadscore) - 1)]
    bin_centers = (bins_leadscore[:-1] + bins_leadscore[1:]) / 2

    plt.figure(figsize=(10, 5))
    ax = sns.histplot(df["leadscore_mapeado"], bins=bins_leadscore, color=cores[1])
    plt.suptitle("Distribuição do Leadscore por Faixa", y=0.97, fontsize=14)
    plt.xlabel("")
    plt.ylabel("")
    plt.yticks([])

    ax.set_xticks(bin_centers)
    ax.set_xticklabels(interval_labels, rotation=30, ha="right")

    # Linhas verticais dos limites das faixas
    ax.axvline(limite_a, color=cores[0], linestyle="--", label="Limite A")
    ax.axvline(limite_b, color=cores[4], linestyle="--", label="Limite B")
    ax.axvline(limite_c, color=cores[2], linestyle="--", label="Limite C")
    ax.axvline(limite_d, color=cores[5], linestyle="--", label="Limite D")

    # Rótulos diretos acima das linhas de limite
    ax.text(limite_a, ax.get_ylim()[1]*1.02, "Limite A >", color=cores[0], ha="center", fontsize=10)
    ax.text(limite_b, ax.get_ylim()[1]*1.02, "Limite B >", color=cores[4], ha="center", fontsize=10)
    ax.text(limite_c, ax.get_ylim()[1]*1.02, "Limite C >", color=cores[2], ha="center", fontsize=10)
    ax.text(limite_d, ax.get_ylim()[1]*1.02, "Limite D >", color=cores[5], ha="center", fontsize=10)
    
    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    plt.subplots_adjust(top=0.85)  # empurra o conteúdo para baixo
    plt.tight_layout()
    plt.show()


def plot_comparativo_leads_alunos(df_leads, df_alunos):
    """
    Plota gráfico comparando a proporção de faixas previstas (leads) vs reais (alunos).

    Parâmetros:
    ----------
    df_leads : pd.DataFrame
        DataFrame com a coluna 'faixa_predita_por_regressao'.

    df_alunos : pd.DataFrame
        DataFrame com a coluna 'leadscore_faixa'.
    """
    contagem_prevista = df_leads["leadscore_faixa"].value_counts(normalize=True).sort_index() * 100
    contagem_real = df_alunos["leadscore_faixa"].value_counts(normalize=True).sort_index() * 100

    comparativo_perc = pd.DataFrame({
        "Leads (%)": contagem_prevista,
        "Alunos (%)": contagem_real
    }).fillna(0).round(1)

    comparativo_perc["Variação (p.p.)"] = (
        comparativo_perc["Leads (%)"] - comparativo_perc["Alunos (%)"]
    ).round(1)

    plt.figure(figsize=(8, 5))
    labels = comparativo_perc.index
    x = np.arange(len(labels))
    width = 0.35

    bars1 = plt.bar(x - width/2, comparativo_perc["Leads (%)"], width, label="Leads (%)", color=cores[2])
    bars2 = plt.bar(x + width/2, comparativo_perc["Alunos (%)"], width, label="Alunos (%)", color=cores[0])

    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            plt.text(
                bar.get_x() + bar.get_width() / 2,
                height + 1,
                f"{height:.1f}%",
                ha='center',
                va='bottom'
            )

    plt.ylabel("")
    plt.title("Leads vs Alunos por Faixa", pad=20)
    plt.xticks(x, labels)
    plt.tick_params(axis='x', length=0)
    plt.yticks([])
    plt.legend()

    for spine in ["top", "right", "left", "bottom"]:
        plt.gca().spines[spine].set_visible(False)

    plt.tight_layout()
    plt.show()



def plot_probabilidade_conversao_vs_score(df_leads):
    """
    Plota um gráfico com a distribuição da probabilidade de conversão calibrada (como histograma)
    e o score híbrido (como curva de densidade), ambos normalizados em densidade.

    Também insere linhas verticais com as médias de cada distribuição e seus respectivos valores 
    percentuais no topo das linhas. O eixo X é formatado como porcentagem (0% a 100%).

    Parâmetros:
    ----------
    df_leads : pd.DataFrame
        DataFrame contendo as colunas:
        - 'probabilidade_conversao_calibrada': resultado da calibragem de modelo de classificação.
        - 'score_hibrido': score combinado (ex: classificação + regressão).
    """
    plt.figure(figsize=(10, 5))
    sns.histplot(df_leads["probabilidade_conversao_modelo"],
                 bins=30, color=cores[4], label="Prob. Conversão",
                 kde=False, stat="density", edgecolor="black")

    sns.kdeplot(df_leads["score_hibrido"], color=cores[2], label="Score Híbrido")

    plt.title("Probabilidade de Conversão por Faixa vs Score Híbrido", pad=25)
    plt.xlabel("")
    plt.ylabel("")
    plt.yticks([])
    plt.xlim(0, 1)

    media_prob = df_leads["probabilidade_conversao_modelo"].mean()
    media_hibrido = df_leads["score_hibrido"].mean()

    plt.axvline(media_prob, color=cores[4], linestyle='--', label='Média Prob.')
    plt.axvline(media_hibrido, color=cores[0], linestyle='--', label='Média Híbrido')

    ylim_top = plt.ylim()[1]

    plt.text(media_prob, ylim_top * 1.0, f"{media_prob * 100:.0f}%", color=cores[4], ha='center', va='bottom', fontsize=10)
    plt.text(media_hibrido, ylim_top * 1.0, f"{media_hibrido * 100:.0f}%", color=cores[0], ha='center', va='bottom', fontsize=10)

    plt.legend()

    for spine in ["top", "right", "left"]:
        plt.gca().spines[spine].set_visible(False)

    plt.gca().xaxis.set_major_formatter(mtick.PercentFormatter(1.0))
    plt.tight_layout()
    plt.show()


def plot_histograma_leadscore_alunos(df, limite_a, limite_b, limite_c, limite_d):
    """
    Plota histograma do leadscore total com linhas verticais para os limites das faixas.

    Parâmetros:
    ----------
    df : pd.DataFrame
        DataFrame contendo a coluna 'leadscore_total'.
    limite_a, limite_b, limite_c, limite_d : float
        Limites das faixas A, B, C e D.
    """
    media_score = df["leadscore_total"].mean()

    bins_leadscore = np.histogram_bin_edges(df["leadscore_total"], bins="sturges")
    bins_leadscore = np.round(bins_leadscore).astype(int)

    interval_labels = [f"{bins_leadscore[i]}–{bins_leadscore[i+1]}" for i in range(len(bins_leadscore) - 1)]
    bin_centers = (bins_leadscore[:-1] + bins_leadscore[1:]) / 2

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.histplot(df["leadscore_total"], bins=bins_leadscore, color=cores[1], ax=ax)

    # Linhas verticais para os limites de faixa
    ax.axvline(limite_a, color=cores[0], linestyle="--", label="Limite A")
    ax.axvline(limite_b, color=cores[4], linestyle="--", label="Limite B")
    ax.axvline(limite_c, color=cores[2], linestyle="--", label="Limite C")
    ax.axvline(limite_d, color=cores[5], linestyle="--", label="Limite D")

    ymax = ax.get_ylim()[1]
    ax.text(limite_a, ymax * 1.02, "Limite A >", color=cores[0], ha="center", fontsize=10)
    ax.text(limite_b, ymax * 1.02, "Limite B >", color=cores[4], ha="center", fontsize=10)
    ax.text(limite_c, ymax * 1.02, "Limite C >", color=cores[2], ha="center", fontsize=10)
    ax.text(limite_d, ymax * 1.02, "Limite D >", color=cores[5], ha="center", fontsize=10)

    ax.set_xticks(bin_centers)
    ax.set_xticklabels(interval_labels, rotation=30, ha="right")

    ax.set_title("Distribuição do Leadscore Total", y=1.1)
    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_yticks([])

    for spine in ["top", "right", "left"]:
        ax.spines[spine].set_visible(False)

    ax.legend()
    plt.tight_layout()
    plt.show()
