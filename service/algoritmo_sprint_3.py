from typing import Optional, Tuple

def _chave_comparacao(novo: dict, cadastro: dict) -> str:
    return (
        f"{novo['cpf']}|{novo['email']}|{novo['nome']}|{novo['telefone']}"
        "::"
        f"{cadastro['cpf']}|{cadastro['email']}|{cadastro['nome']}|{cadastro['telefone']}"
    )

def _comparar_leads(novo: dict, existente: dict) -> Tuple[bool, Optional[str]]:
    """Regras: CPF idêntico | E-mail idêntico | Nome + Telefone idênticos."""
    if novo["cpf"] == existente["cpf"]:
        return True, "CPF já cadastrado"
    if novo["email"] == existente["email"]:
        return True, "E-mail já cadastrado"
    if novo["nome"] == existente["nome"] and novo["telefone"] == existente["telefone"]:
        return True, "Nome e Telefone já cadastrados"
    return False, None

def verificar_duplicidade_recursiva(
    novo_lead: dict,
    lista_cadastros: list,
    index: int = 0,
    memo: dict = None,
) -> Tuple[bool, Optional[str], dict]:
    """
    Recursão com memoização. O memo é compartilhado entre chamadas —
    o ganho real ocorre no endpoint /lote, onde múltiplos leads são
    verificados contra a mesma base e pares já comparados vêm do cache.
    """
    if memo is None:
        memo = {}
    if index >= len(lista_cadastros):
        return False, None, memo

    cadastro_atual = lista_cadastros[index]
    chave = _chave_comparacao(novo_lead, cadastro_atual)

    if chave in memo:
        cached_dup, cached_motivo = memo[chave]
        if cached_dup:
            return True, cached_motivo, memo
        return verificar_duplicidade_recursiva(novo_lead, lista_cadastros, index + 1, memo)

    is_dup, motivo = _comparar_leads(novo_lead, cadastro_atual)
    memo[chave] = (is_dup, motivo)

    if is_dup:
        return True, motivo, memo

    return verificar_duplicidade_recursiva(novo_lead, lista_cadastros, index + 1, memo)

def otimizar_agenda_medico(
    consultas: list, tempo_disponivel: int, n: int, memo: dict = None
) -> int:
    """
    Knapsack 0/1 com memoização. Estado (tempo, n) garante que cada
    subproblema é resolvido uma única vez — O(n × W) vs O(2^n) sem DP.
    """
    if memo is None:
        memo = {}
    if n == 0 or tempo_disponivel == 0:
        return 0

    chave = (tempo_disponivel, n)
    if chave in memo:
        return memo[chave]

    duracao_atual = consultas[n - 1]["duracao"]
    prioridade_atual = consultas[n - 1]["prioridade"]

    if duracao_atual > tempo_disponivel:
        resultado = otimizar_agenda_medico(consultas, tempo_disponivel, n - 1, memo)
    else:
        incluir = prioridade_atual + otimizar_agenda_medico(
            consultas, tempo_disponivel - duracao_atual, n - 1, memo
        )
        nao_incluir = otimizar_agenda_medico(consultas, tempo_disponivel, n - 1, memo)
        resultado = max(incluir, nao_incluir)

    memo[chave] = resultado
    return resultado

def reconstruir_consultas_selecionadas(consultas: list, tempo_disponivel: int, memo: dict) -> list:
    """Retrocede pelo memo para identificar quais consultas compõem a solução ótima."""
    n = len(consultas)
    tempo = tempo_disponivel
    selecionadas = []

    for i in range(n, 0, -1):
        valor_com = memo.get((tempo, i), 0)
        valor_sem = memo.get((tempo, i - 1), 0)
        consulta = consultas[i - 1]
        if valor_com != valor_sem and tempo >= consulta["duracao"]:
            selecionadas.append(consulta)
            tempo -= consulta["duracao"]

    return selecionadas