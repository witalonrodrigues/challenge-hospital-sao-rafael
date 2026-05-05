from pydantic import BaseModel
from typing import List

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
    Verifica múltiplos leads contra a mesma base em uma chamada.
    O memo compartilhado é onde a memoização gera ganho real:
    pares (lead, cadastro) já calculados não são reprocessados.
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