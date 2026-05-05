import heapq
from typing import Dict, List, Optional, Tuple

_DEFINICAO_ARESTAS = [
    ("Lead",          "Triagem",         5,         0.00),
    ("Triagem",       "Cadastro",        8,         0.05),
    ("Cadastro",      "Contato",         15,        0.10),
    ("Contato",       "Agendamento",     20,        0.15),
    ("Contato",       "Negociacao",      35,        0.40),
    ("Negociacao",    "Agendamento",     18,        0.25),
    ("Negociacao",    "Perdido",         60,        0.90),
    ("Agendamento",   "Confirmacao",     10,        0.05),
    ("Agendamento",   "Reagendamento",   30,        0.30),
    ("Reagendamento", "Confirmacao",     12,        0.10),
]

_DESCRICAO_NOS = {
    "Lead":          "Entrada do lead pelo funil (Instagram, Facebook, Google, TikTok)",
    "Triagem":       "Verificação de duplicidade — recursão com memoização (Sprint 3)",
    "Cadastro":      "Registro do lead no CRM após triagem aprovada",
    "Contato":       "Primeiro contato pelo operador — janela crítica de atendimento",
    "Negociacao":    "Tratativas com lead resistente — alto custo operacional e de abandono",
    "Agendamento":   "Consulta agendada — otimização via Knapsack (Sprint 3)",
    "Reagendamento": "Remarcação após cancelamento",
    "Confirmacao":   "Confirmação final — lead convertido em paciente",
    "Perdido":       "Lead perdido — abandonou o funil durante a negociação",
}

_POSICOES_NOS: Dict[str, Tuple[float, float]] = {
    "Lead":          (0.0,  0.0),
    "Triagem":       (1.5,  0.0),
    "Cadastro":      (3.0,  0.0),
    "Contato":       (4.5,  0.0),
    "Negociacao":    (6.0, -1.5),
    "Agendamento":   (6.0,  1.5),
    "Perdido":       (7.5, -1.5),
    "Reagendamento": (7.5,  1.5),
    "Confirmacao":   (7.5,  0.0),
}

def _construir_grafo_adjacencia() -> Tuple[Dict[str, List[Tuple[str, float]]], List[Dict]]:
    grafo: Dict[str, List[Tuple[str, float]]] = {no: [] for no in _POSICOES_NOS}
    metadados: List[Dict] = []

    for origem, destino, tempo, abandono in _DEFINICAO_ARESTAS:
        custo = round(tempo * (1 + abandono), 2)
        grafo[origem].append((destino, custo))
        metadados.append({
            "origem": origem,
            "destino": destino,
            "tempo_medio_min": tempo,
            "taxa_abandono": abandono,
            "custo_ajustado": custo,
        })

    return grafo, metadados

GRAFO_CRM, METADADOS_ARESTAS = _construir_grafo_adjacencia()

def dijkstra(
    grafo: Dict[str, List[Tuple[str, float]]],
    origem: str,
    destino: str,
) -> Tuple[float, List[str]]:
    dist: Dict[str, float] = {no: float("inf") for no in grafo}
    dist[origem] = 0.0

    predecessor: Dict[str, Optional[str]] = {no: None for no in grafo}
    heap: List[Tuple[float, str]] = [(0.0, origem)]
    visitados: set = set()

    while heap:
        custo_atual, no_atual = heapq.heappop(heap)

        if no_atual in visitados:
            continue
        visitados.add(no_atual)

        if no_atual == destino:
            break

        for vizinho, peso in grafo.get(no_atual, []):
            novo_custo = custo_atual + peso
            if novo_custo < dist[vizinho]:
                dist[vizinho] = novo_custo
                predecessor[vizinho] = no_atual
                heapq.heappush(heap, (novo_custo, vizinho))

    if dist[destino] == float("inf"):
        return float("inf"), []

    caminho: List[str] = []
    no = destino
    while no is not None:
        caminho.append(no)
        no = predecessor[no]
    caminho.reverse()

    return round(dist[destino], 2), caminho

def _gerar_interpretacao(
    caminho_otimo: List[str],
    custo_otimo: float,
    grafo: Dict[str, List[Tuple[str, float]]],
    origem: str,
    destino: str,
) -> Dict:
    def _dfs(no_atual: str, caminho_parcial: List[str], custo_parcial: float, todos: List):
        if no_atual == destino:
            todos.append({"caminho": list(caminho_parcial), "custo": round(custo_parcial, 2)})
            return
        for vizinho, custo in grafo.get(no_atual, []):
            if vizinho not in caminho_parcial:
                _dfs(vizinho, caminho_parcial + [vizinho], custo_parcial + custo, todos)

    todos_caminhos: List[Dict] = []
    _dfs(origem, [origem], 0.0, todos_caminhos)
    todos_caminhos.sort(key=lambda x: x["custo"])

    etapas_evitadas = []
    economia = 0.0
    if len(todos_caminhos) > 1:
        segundo = set(todos_caminhos[1]["caminho"])
        etapas_evitadas = [n for n in segundo if n not in caminho_otimo]
        economia = round(todos_caminhos[1]["custo"] - custo_otimo, 2)

    return {
        "caminho_otimo_descricao": " → ".join(caminho_otimo),
        "custo_total_ajustado": custo_otimo,
        "unidade": "minutos ajustados ao risco de abandono",
        "por_que_e_eficiente": (
            f"O caminho ótimo evita etapas de alto custo como 'Negociacao' e "
            f"'Reagendamento'. A fórmula custo = tempo × (1 + taxa_abandono) penaliza "
            f"essas etapas pelo risco de perder o lead. O caminho direto via Agendamento "
            f"converte o lead em menor tempo operacional e com menor risco acumulado, "
            f"economizando {economia} unidades de custo em relação ao segundo melhor caminho."
        ),
        "etapas_de_alto_custo_evitadas": etapas_evitadas,
        "economia_vs_segundo_melhor": economia,
        "ranking_todos_caminhos": todos_caminhos,
    }