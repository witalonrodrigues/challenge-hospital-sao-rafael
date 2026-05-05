import base64
import io
from typing import List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import networkx as nx 

# Importando os dados do grafo da Sprint 4
from service.algoritmo_sprint_4 import _DEFINICAO_ARESTAS, _POSICOES_NOS

_CORES = {
    "fundo":         "#0f0f23",
    "no_origem":     "#e74c3c",
    "no_destino":    "#2ecc71",
    "no_caminho":    "#3498db",
    "no_neutro":     "#4a4a6a",
    "no_perda":      "#8e44ad",
    "aresta_otima":  "#f1c40f",
    "aresta_neutra": "#2c2c4a",
    "texto":         "#ecf0f1",
    "peso_otimo":    "#f39c12",
    "peso_neutro":   "#7f8c8d",
}

def gerar_visualizacao_grafo(caminho_otimo: List[str]) -> str:
    """
    Gera PNG do grafo CRM com o caminho ótimo destacado.
    Retorna a imagem codificada em base64.
    """
    G = nx.DiGraph()
    for origem, destino, tempo, abandono in _DEFINICAO_ARESTAS:
        custo = round(tempo * (1 + abandono), 2)
        G.add_edge(origem, destino, weight=custo)

    pos = _POSICOES_NOS
    arestas_caminho = set(zip(caminho_otimo, caminho_otimo[1:]))

    cores_nos = []
    for no in G.nodes():
        if no == "Lead":
            cores_nos.append(_CORES["no_origem"])
        elif no == "Confirmacao":
            cores_nos.append(_CORES["no_destino"])
        elif no == "Perdido":
            cores_nos.append(_CORES["no_perda"])
        elif no in caminho_otimo:
            cores_nos.append(_CORES["no_caminho"])
        else:
            cores_nos.append(_CORES["no_neutro"])

    arestas_otimas = [(u, v) for u, v in G.edges() if (u, v) in arestas_caminho]
    arestas_neutras = [(u, v) for u, v in G.edges() if (u, v) not in arestas_caminho]

    fig, ax = plt.subplots(figsize=(16, 9))
    fig.patch.set_facecolor(_CORES["fundo"])
    ax.set_facecolor(_CORES["fundo"])
    ax.axis("off")

    nx.draw_networkx_nodes(G, pos, ax=ax, node_color=cores_nos, node_size=2800, alpha=0.95)
    nx.draw_networkx_labels(G, pos, ax=ax, font_color=_CORES["texto"], font_size=8, font_weight="bold")

    nx.draw_networkx_edges(
        G, pos, edgelist=arestas_otimas, ax=ax,
        edge_color=_CORES["aresta_otima"], width=3.5,
        arrows=True, arrowsize=25,
        connectionstyle="arc3,rad=0.08",
        min_source_margin=30, min_target_margin=30,
    )
    nx.draw_networkx_edges(
        G, pos, edgelist=arestas_neutras, ax=ax,
        edge_color=_CORES["aresta_neutra"], width=1.2, style="dashed",
        arrows=True, arrowsize=15,
        connectionstyle="arc3,rad=0.08",
        min_source_margin=30, min_target_margin=30,
    )

    pesos_otimos = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True) if (u, v) in arestas_caminho}
    pesos_neutros = {(u, v): f"{d['weight']}" for u, v, d in G.edges(data=True) if (u, v) not in arestas_caminho}

    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=pesos_otimos, ax=ax,
        font_color=_CORES["peso_otimo"], font_size=8, font_weight="bold", label_pos=0.35,
        bbox={"boxstyle": "round,pad=0.2", "facecolor": _CORES["fundo"], "alpha": 0.7, "edgecolor": "none"},
    )
    nx.draw_networkx_edge_labels(
        G, pos, edge_labels=pesos_neutros, ax=ax,
        font_color=_CORES["peso_neutro"], font_size=7, label_pos=0.35,
        bbox={"boxstyle": "round,pad=0.2", "facecolor": _CORES["fundo"], "alpha": 0.6, "edgecolor": "none"},
    )

    custo_total = sum(G[u][v]["weight"] for u, v in arestas_caminho if G.has_edge(u, v))
    ax.set_title(
        f"Fluxo CRM — Hospital São Rafael\n"
        f"Caminho ótimo (Dijkstra): {' → '.join(caminho_otimo)}   |   Custo: {round(custo_total, 2)} min ajustados",
        color=_CORES["texto"], fontsize=11, pad=15, fontweight="bold",
    )

    legenda = [
        mpatches.Patch(color=_CORES["no_origem"],    label="Lead (origem)"),
        mpatches.Patch(color=_CORES["no_destino"],   label="Confirmação (destino)"),
        mpatches.Patch(color=_CORES["no_caminho"],   label="Etapa no caminho ótimo"),
        mpatches.Patch(color=_CORES["no_neutro"],    label="Etapa alternativa"),
        mpatches.Patch(color=_CORES["no_perda"],     label="Perdido (abandono)"),
        mpatches.Patch(color=_CORES["aresta_otima"], label="Caminho ótimo (Dijkstra)"),
    ]
    ax.legend(
        handles=legenda, loc="lower left",
        facecolor="#1a1a3e", edgecolor="#3a3a5e",
        labelcolor=_CORES["texto"], fontsize=8,
    )
    ax.annotate(
        "Peso = tempo_medio_min × (1 + taxa_abandono)",
        xy=(0.5, 0.02), xycoords="axes fraction",
        ha="center", fontsize=8, color=_CORES["peso_neutro"],
    )

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=130, bbox_inches="tight", facecolor=_CORES["fundo"])
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")