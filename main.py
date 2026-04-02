"""
Microserviço FastAPI com Programação Dinâmica para:
  - Verificação de duplicidade de leads (Recursão + Memoização)
  - Otimização da agenda médica (Knapsack 0/1)
"""

import logging
import sys
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel
from typing import List, Optional, Tuple

# Logging

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dp_service")


# Iniciando a Aplicação

app = FastAPI(
    title="CRM Hospital São Rafael",
    description=(
        "Microserviço em python para otimização de agendas "
        "e verificação de duplicidade de leads.\n\n"
        "**Técnicas aplicadas:** Recursão, Memoização, Knapsack 0/1"
    ),
    version="1.0.0",
)


# Tratamento de Exceções

class LeadDuplicadoError(HTTPException):
    """HTTP 409 — Lead já existe na base de dados."""

    def __init__(self, motivo: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={
                "erro": "LEAD_DUPLICADO",
                "mensagem": f"Lead já cadastrado: {motivo}.",
            },
        )


class AgendaSemEncaixeError(HTTPException):
    """HTTP 422 — Nenhuma consulta cabe no tempo disponível."""

    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "erro": "AGENDA_SEM_ENCAIXE",
                "mensagem": (
                    "Nenhuma consulta cabe no tempo disponível informado. "
                    "Revise as durações ou aumente o tempo disponível."
                ),
            },
        )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    erros = [
        {
            "campo": " → ".join(str(loc) for loc in e["loc"]),
            "erro": e["msg"],
        }
        for e in exc.errors()
    ]
    logger.warning("Erro de validação em %s | %s", request.url.path, erros)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "error", "tipo": "VALIDACAO", "erros": erros},
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(
    request: Request, exc: HTTPException
) -> JSONResponse:
    logger.error(
        "Erro HTTP %d em %s | detalhe: %s",
        exc.status_code,
        request.url.path,
        exc.detail,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", **exc.detail}
        if isinstance(exc.detail, dict)
        else {"status": "error", "mensagem": exc.detail},
    )


# Modelagem de Entidades

class Lead(BaseModel):
    nome: str
    cpf: str
    email: str
    telefone: str


class DuplicidadeRequest(BaseModel):
    novo_lead: Lead
    banco_cadastros: List[Lead]


class LoteVerificacaoRequest(BaseModel):
    """
    Verifica múltiplos novos leads contra a mesma base de cadastros.
    Este é o cenário onde a memoização gera ganho real: pares
    (novo_lead, cadastro) já comparados são reutilizados entre leads.
    """
    novos_leads: List[Lead]
    banco_cadastros: List[Lead]


class Consulta(BaseModel):
    procedimento: str
    duracao: int
    prioridade: int


class AgendaRequest(BaseModel):
    consultas: List[Consulta]
    tempo_disponivel: int



# Verificação Recursiva com Memoização

def _chave_comparacao(novo: dict, cadastro: dict) -> str:
    """Identifica unicamente o par (novo_lead, cadastro) para o cache."""
    return (
        f"{novo['cpf']}|{novo['email']}|{novo['nome']}|{novo['telefone']}"
        "::"
        f"{cadastro['cpf']}|{cadastro['email']}|{cadastro['nome']}|{cadastro['telefone']}"
    )


def _comparar_leads(novo: dict, existente: dict) -> Tuple[bool, Optional[str]]:
    """
    Regras de duplicidade (qualquer condição é suficiente):
      - CPF idêntico
      - E-mail idêntico
      - Nome + Telefone idênticos simultaneamente
    """
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
    Verifica recursivamente se novo_lead já existe em lista_cadastros.

    O memo é compartilhado entre chamadas — seu valor real aparece no
    endpoint de lote, onde múltiplos leads são verificados contra a
    mesma base e pares já comparados não são recalculados.
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


# Otimização de Agenda

def otimizar_agenda_medico(
    consultas: list,
    tempo_disponivel: int,
    n: int,
    memo: dict = None,
) -> int:
    """
    Knapsack 0/1: maximiza prioridade total dentro do tempo disponível.

    Estado: (tempo_disponivel, n) — cada estado é calculado uma única vez.
    Aqui a sobreposição de subproblemas é genuína: diferentes combinações
    de inclusão/exclusão de consultas convergem para os mesmos (t, i),
    e o memo evita o reprocessamento exponencial.
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


def reconstruir_consultas_selecionadas(
    consultas: list,
    tempo_disponivel: int,
    memo: dict,
) -> list:
    """Retrocede pelo memo preenchido para identificar quais consultas foram selecionadas."""
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


# Endpoints da API

@app.get("/health", tags=["Infra"], summary="Health check")
async def health_check() -> dict:
    logger.info("Health check solicitado")
    return {"status": "ok", "servico": "CRM Hospital São Rafael"}


@app.post(
    "/api/v1/verificar-duplicidade",
    tags=["Leads"],
    summary="Verifica duplicidade de um Lead (Recursão + Memoização)",
    status_code=status.HTTP_200_OK,
)
async def endpoint_verificar_duplicidade(payload: DuplicidadeRequest) -> dict:
    logger.info(
        "Verificação iniciada | lead: '%s' | base: %d registro(s)",
        payload.novo_lead.nome,
        len(payload.banco_cadastros),
    )

    novo_lead_dict = payload.novo_lead.model_dump()
    cadastros_dict = [c.model_dump() for c in payload.banco_cadastros]

    is_duplicado, motivo, memo = verificar_duplicidade_recursiva(
        novo_lead_dict, cadastros_dict
    )

    logger.info(
        "Verificação concluída | duplicado: %s | cache: %d entradas",
        is_duplicado, len(memo),
    )

    if is_duplicado:
        raise LeadDuplicadoError(motivo)

    return {
        "status": "success",
        "lead_duplicado": False,
        "comparacoes_cacheadas": len(memo),
        "mensagem": "Lead inédito, pronto para cadastro.",
    }


@app.post(
    "/api/v1/verificar-duplicidade/lote",
    tags=["Leads"],
    summary="Verifica duplicidade de múltiplos Leads — memoização entre leads",
    status_code=status.HTTP_200_OK,
)
async def endpoint_verificar_duplicidade_lote(payload: LoteVerificacaoRequest) -> dict:
    """
    Verifica vários novos leads contra a mesma base em uma única chamada.

    O memo é compartilhado entre todos os leads do lote: se lead_A e lead_B
    são comparados com o mesmo cadastro_X, o resultado da segunda comparação
    vem direto do cache — sem reprocessamento. Este é o cenário que demonstra
    a sobreposição de subproblemas da memoização de forma concreta.
    """
    logger.info(
        "Verificação em lote iniciada | novos: %d | base: %d registro(s)",
        len(payload.novos_leads),
        len(payload.banco_cadastros),
    )

    cadastros_dict = [c.model_dump() for c in payload.banco_cadastros]
    memo_compartilhado: dict = {}

    resultados = []
    for lead in payload.novos_leads:
        lead_dict = lead.model_dump()
        is_dup, motivo, memo_compartilhado = verificar_duplicidade_recursiva(
            lead_dict, cadastros_dict, memo=memo_compartilhado
        )
        resultados.append({
            "lead": lead.nome,
            "duplicado": is_dup,
            "motivo": motivo,
        })

    duplicados = sum(1 for r in resultados if r["duplicado"])

    logger.info(
        "Lote concluído | leads: %d | duplicados: %d | cache final: %d entradas",
        len(resultados), duplicados, len(memo_compartilhado),
    )

    return {
        "status": "success",
        "total_verificados": len(resultados),
        "total_duplicados": duplicados,
        "cache_entradas": len(memo_compartilhado),
        "resultados": resultados,
    }


@app.post(
    "/api/v1/otimizar-agenda",
    tags=["Agenda"],
    summary="Otimiza a agenda do médico (Knapsack 0/1 com Memoização)",
    status_code=status.HTTP_200_OK,
)
async def endpoint_otimizar_agenda(payload: AgendaRequest) -> dict:
    logger.info(
        "Otimização iniciada | consultas: %d | tempo: %d min",
        len(payload.consultas),
        payload.tempo_disponivel,
    )

    consultas_dict = [c.model_dump() for c in payload.consultas]
    n = len(consultas_dict)
    memo: dict = {}

    pontuacao_maxima = otimizar_agenda_medico(
        consultas_dict, payload.tempo_disponivel, n, memo
    )

    if pontuacao_maxima == 0:
        logger.warning(
            "Nenhuma consulta encaixável | tempo disponível: %d min",
            payload.tempo_disponivel,
        )
        raise AgendaSemEncaixeError()

    consultas_selecionadas = reconstruir_consultas_selecionadas(
        consultas_dict, payload.tempo_disponivel, memo
    )

    tempo_utilizado = sum(c["duracao"] for c in consultas_selecionadas)

    logger.info(
        "Agenda otimizada | selecionadas: %d | tempo usado: %d min | ocioso: %d min",
        len(consultas_selecionadas),
        tempo_utilizado,
        payload.tempo_disponivel - tempo_utilizado,
    )

    return {
        "status": "success",
        "tempo_disponivel": payload.tempo_disponivel,
        "tempo_utilizado": tempo_utilizado,
        "tempo_ocioso": payload.tempo_disponivel - tempo_utilizado,
        "pontuacao_maxima_prioridade": pontuacao_maxima,
        "total_consultas_avaliadas": n,
        "total_consultas_selecionadas": len(consultas_selecionadas),
        "subproblemas_calculados": len(memo),
        "consultas_selecionadas": consultas_selecionadas,
        "mensagem": "Agenda otimizada com sucesso usando Programação Dinâmica.",
    }