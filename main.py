import base64
import logging
import sys

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse, Response, RedirectResponse
from fastapi.exceptions import RequestValidationError

# Imports
from schemas.models import DuplicidadeRequest, LoteVerificacaoRequest, AgendaRequest
from service.algoritmo_sprint_3 import verificar_duplicidade_recursiva, otimizar_agenda_medico, reconstruir_consultas_selecionadas
from service.algoritmo_sprint_4 import GRAFO_CRM, METADADOS_ARESTAS, _DESCRICAO_NOS, dijkstra, _gerar_interpretacao
from service.visualizacao import gerar_visualizacao_grafo


# LOGGING 

logging.basicConfig(
    stream=sys.stdout,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("dp_service")

# FASTAPI

app = FastAPI(
    title="CRM Hospital São Rafael",
    description=(
        "Microserviço de Programação Dinâmica aplicada ao CRM do Hospital São Rafael.\n\n"
        "**Sprint 3** — Recursão + Memoização | Knapsack 0/1\n\n"
        "**Sprint 4** — Grafos Direcionados | Dijkstra | Visualização do Fluxo CRM"
    ),
    version="2.0.0",
)

@app.get("/", include_in_schema=False)
async def root():
    # Redireciona quem acessar a raiz direto para a tela de documentação
    return RedirectResponse(url="/docs")

# Exceções

class LeadDuplicadoError(HTTPException):
    def __init__(self, motivo: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail={"erro": "LEAD_DUPLICADO", "mensagem": f"Lead já cadastrado: {motivo}."},
        )

class AgendaSemEncaixeError(HTTPException):
    def __init__(self):
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "erro": "AGENDA_SEM_ENCAIXE",
                "mensagem": "Nenhuma consulta cabe no tempo disponível. Revise as durações.",
            },
        )

class CaminhoInacessivelError(HTTPException):
    def __init__(self, origem: str, destino: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "erro": "CAMINHO_INACESSIVEL",
                "mensagem": f"Não existe caminho entre '{origem}' e '{destino}' no grafo CRM.",
            },
        )

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    erros = [
        {"campo": " → ".join(str(loc) for loc in e["loc"]), "erro": e["msg"]}
        for e in exc.errors()
    ]
    logger.warning("Erro de validação em %s | %s", request.url.path, erros)
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"status": "error", "tipo": "VALIDACAO", "erros": erros},
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    logger.error("Erro HTTP %d em %s | %s", exc.status_code, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", **exc.detail}
        if isinstance(exc.detail, dict)
        else {"status": "error", "mensagem": exc.detail},
    )

# ===========================================================================
# ENDPOINTS — SPRINT 3
# ===========================================================================

@app.get("/health", tags=["Infra"], summary="Health check")
async def health_check() -> dict:
    logger.info("Health check solicitado")
    return {"status": "ok", "servico": "CRM Hospital São Rafael"}

@app.post(
    "/api/v1/verificar-duplicidade",
    tags=["Leads — Sprint 3"],
    summary="Verifica duplicidade de um Lead (Recursão + Memoização)",
    status_code=status.HTTP_200_OK,
)
async def endpoint_verificar_duplicidade(payload: DuplicidadeRequest) -> dict:
    logger.info("Verificação iniciada | lead: '%s' | base: %d", payload.novo_lead.nome, len(payload.banco_cadastros))
    novo_lead_dict = payload.novo_lead.model_dump()
    cadastros_dict = [c.model_dump() for c in payload.banco_cadastros]
    is_duplicado, motivo, memo = verificar_duplicidade_recursiva(novo_lead_dict, cadastros_dict)
    logger.info("Verificação concluída | duplicado: %s | cache: %d", is_duplicado, len(memo))

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
    tags=["Leads — Sprint 3"],
    summary="Verifica duplicidade de múltiplos Leads com memo compartilhado",
    status_code=status.HTTP_200_OK,
)
async def endpoint_verificar_duplicidade_lote(payload: LoteVerificacaoRequest) -> dict:
    logger.info("Lote iniciado | novos: %d | base: %d", len(payload.novos_leads), len(payload.banco_cadastros))
    cadastros_dict = [c.model_dump() for c in payload.banco_cadastros]
    memo_compartilhado: dict = {}
    resultados = []

    for lead in payload.novos_leads:
        lead_dict = lead.model_dump()
        is_dup, motivo, memo_compartilhado = verificar_duplicidade_recursiva(
            lead_dict, cadastros_dict, memo=memo_compartilhado
        )
        resultados.append({"lead": lead.nome, "duplicado": is_dup, "motivo": motivo})

    duplicados = sum(1 for r in resultados if r["duplicado"])
    logger.info("Lote concluído | duplicados: %d | cache: %d", duplicados, len(memo_compartilhado))

    return {
        "status": "success",
        "total_verificados": len(resultados),
        "total_duplicados": duplicados,
        "cache_entradas": len(memo_compartilhado),
        "resultados": resultados,
    }

@app.post(
    "/api/v1/otimizar-agenda",
    tags=["Agenda — Sprint 3"],
    summary="Otimiza a agenda do médico (Knapsack 0/1 com Memoização)",
    status_code=status.HTTP_200_OK,
)
async def endpoint_otimizar_agenda(payload: AgendaRequest) -> dict:
    logger.info("Otimização iniciada | consultas: %d | tempo: %d min", len(payload.consultas), payload.tempo_disponivel)
    consultas_dict = [c.model_dump() for c in payload.consultas]
    n = len(consultas_dict)
    memo: dict = {}

    pontuacao_maxima = otimizar_agenda_medico(consultas_dict, payload.tempo_disponivel, n, memo)
    if pontuacao_maxima == 0:
        raise AgendaSemEncaixeError()

    consultas_selecionadas = reconstruir_consultas_selecionadas(consultas_dict, payload.tempo_disponivel, memo)
    tempo_utilizado = sum(c["duracao"] for c in consultas_selecionadas)
    logger.info("Agenda otimizada | selecionadas: %d | usado: %d min", len(consultas_selecionadas), tempo_utilizado)

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

# ===========================================================================
# ENDPOINTS — SPRINT 4
# ===========================================================================

@app.get(
    "/api/v1/crm/grafo",
    tags=["Grafo CRM — Sprint 4"],
    summary="Retorna a estrutura do grafo CRM (Tarefa 1)",
    status_code=status.HTTP_200_OK,
)
async def endpoint_grafo_estrutura() -> dict:
    """
    Expõe o grafo direcionado que modela o fluxo CRM.
    Cada aresta carrega métricas reais de negócio: tempo operacional
    médio e taxa de abandono, combinados em custo ajustado ao risco.
    """
    logger.info("Estrutura do grafo CRM solicitada")
    nos = [
        {"id": no, "descricao": _DESCRICAO_NOS.get(no, ""), "adjacentes": [v for v, _ in vizinhos]}
        for no, vizinhos in GRAFO_CRM.items()
    ]
    return {
        "status": "success",
        "total_nos": len(GRAFO_CRM),
        "total_arestas": len(METADADOS_ARESTAS),
        "formula_custo": "custo_ajustado = tempo_medio_min × (1 + taxa_abandono)",
        "nos": nos,
        "arestas": METADADOS_ARESTAS,
    }

@app.get(
    "/api/v1/crm/dijkstra",
    tags=["Grafo CRM — Sprint 4"],
    summary="Executa Dijkstra no fluxo CRM: Lead → Confirmação (Tarefas 2 e 3)",
    status_code=status.HTTP_200_OK,
)
async def endpoint_dijkstra(
    origem: str = "Lead",
    destino: str = "Confirmacao",
    incluir_visualizacao: bool = True,
) -> dict:
    """
    Encontra o caminho de menor custo operacional ajustado ao risco
    entre duas etapas do CRM usando Dijkstra implementado do zero.

    Parâmetros de query:
    - origem/destino        : nós do grafo (padrão: Lead → Confirmacao)
    - incluir_visualizacao  : retorna PNG do grafo renderizado em base64

    A resposta inclui interpretação automática (Tarefa 3): por que
    esse caminho é eficiente e ranking de todos os caminhos possíveis.
    """
    if origem not in GRAFO_CRM:
        raise HTTPException(status_code=400, detail={"erro": "NO_INVALIDO", "mensagem": f"Nó '{origem}' não existe."})
    if destino not in GRAFO_CRM:
        raise HTTPException(status_code=400, detail={"erro": "NO_INVALIDO", "mensagem": f"Nó '{destino}' não existe."})

    logger.info("Dijkstra iniciado | %s → %s", origem, destino)
    custo_total, caminho_otimo = dijkstra(GRAFO_CRM, origem, destino)

    if not caminho_otimo:
        raise CaminhoInacessivelError(origem, destino)

    custo_por_etapa = []
    for i in range(len(caminho_otimo) - 1):
        u, v = caminho_otimo[i], caminho_otimo[i + 1]
        meta = next(m for m in METADADOS_ARESTAS if m["origem"] == u and m["destino"] == v)
        custo_por_etapa.append(meta)

    interpretacao = _gerar_interpretacao(caminho_otimo, custo_total, GRAFO_CRM, origem, destino)
    logger.info("Dijkstra concluído | custo: %.2f | etapas: %d", custo_total, len(caminho_otimo))

    resposta = {
        "status": "success",
        "origem": origem,
        "destino": destino,
        "caminho_otimo": caminho_otimo,
        "custo_total_ajustado": custo_total,
        "total_etapas": len(caminho_otimo) - 1,
        "custo_por_etapa": custo_por_etapa,
        "interpretacao": interpretacao,
    }

    if incluir_visualizacao:
        logger.info("Gerando visualização do grafo...")
        resposta["grafo_png_base64"] = gerar_visualizacao_grafo(caminho_otimo)
        resposta["instrucao_visualizacao"] = (
            "Copie 'grafo_png_base64' e acesse https://base64.guru/converter/decode/image "
            "— ou use GET /api/v1/crm/grafo/imagem para ver o PNG direto no browser."
        )

    return resposta

@app.get(
    "/api/v1/crm/grafo/imagem",
    tags=["Grafo CRM — Sprint 4"],
    summary="Retorna o grafo CRM como PNG direto no browser",
    response_class=Response,
)
async def endpoint_grafo_imagem(
    origem: str = "Lead",
    destino: str = "Confirmacao",
) -> Response:
    """
    Executa Dijkstra e retorna o PNG com o caminho ótimo destacado.
    Acesse diretamente no browser: /api/v1/crm/grafo/imagem
    """
    if origem not in GRAFO_CRM or destino not in GRAFO_CRM:
        raise HTTPException(status_code=400, detail={"erro": "NO_INVALIDO", "mensagem": "Nó inválido."})

    _, caminho_otimo = dijkstra(GRAFO_CRM, origem, destino)
    if not caminho_otimo:
        raise CaminhoInacessivelError(origem, destino)

    logger.info("Imagem do grafo solicitada | %s → %s", origem, destino)
    png_bytes = base64.b64decode(gerar_visualizacao_grafo(caminho_otimo))
    return Response(content=png_bytes, media_type="image/png")

# Rodar o código: uvicorn main:app --reload