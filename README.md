# CRM Hospital São Rafael

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

Microserviço desenvolvido como entrega da **Sprint 3** para a disciplina de **Dynamic Programming**. O objetivo deste serviço é resolver problemas críticos de negócio do CRM do Hospital São Rafael utilizando técnicas avançadas de algoritmos (Recursão, Memoização e Programação Dinâmica).

## Funcionalidades Principais

1. **Verificação de Duplicidade em Lote (`/api/v1/verificar-duplicidade/lote`)**
   - Recebe um lote de novos leads oriundos de campanhas (Facebook, Instagram, etc.) e os cruza com a base de dados existente.
   - **Técnica:** Recursão com Memoização. O dicionário de cache compartilhado evita o reprocessamento de cruzamentos repetidos (mesmo lead comparado contra o mesmo paciente), otimizando cenários de alta volumetria.

2. **Otimização de Agenda Médica (`/api/v1/otimizar-agenda`)**
   - Dada uma lista de procedimentos desejados e o tempo disponível do médico, calcula a combinação exata de consultas que maximiza a prioridade/valor para o hospital, sem estourar a carga horária.
   - **Técnica:** Programação Dinâmica (Problema da Mochila 0/1 / *0/1 Knapsack Problem*).

## Arquitetura e Tecnologias

- **Linguagem:** Python 3
- **Framework Web:** FastAPI (escolhido pela tipagem estrita e documentação automática)
- **Validação de Dados:** Pydantic
- **Servidor ASGI:** Uvicorn

## Análise de Complexidade (Algoritmos)

Abaixo detalhamos a complexidade computacional das soluções implementadas, evidenciando o ganho de performance obtido pelas técnicas da disciplina:

### 1. Otimização de Agenda (Knapsack 0/1)
- **Complexidade de Tempo:** $O(N \cdot W)$
  - Onde $N$ é o número total de consultas analisadas e $W$ é o tempo disponível do médico em minutos. 
  - *Justificativa:* Graças à memoização, cada subproblema definido pelo estado `(tempo_disponivel, n)` é calculado no máximo uma vez. Sem DP, a complexidade seria exponencial $O(2^N)$.
- **Complexidade de Espaço:** $O(N \cdot W)$
  - Devido ao tamanho máximo do dicionário de `memo` armazenando os subproblemas e o limite da pilha de chamadas recursivas.

### 2. Verificação de Duplicidade de Leads (Lote)
- **Complexidade de Tempo (Pior Caso):** $O(L \cdot C)$
  - Onde $L$ é a quantidade de leads no lote e $C$ é o tamanho da base de cadastros.
  - *Otimização Prática:* Embora o limite superior no pior caso seja quadrático (se todos os leads forem únicos e diferentes da base), a **memoização** faz com que a complexidade de pares idênticos repetidos dentro do mesmo contexto caia para $O(1)$.
- **Complexidade de Espaço:** $O(U)$
  - Onde $U$ é o número de pares únicos comparados `(lead, cadastro)`, limitando o tamanho do dicionário de cache.

## Como Executar o Projeto Localmente

Siga o passo a passo abaixo para rodar a aplicação em um ambiente virtual isolado.

### Pré-requisitos
- Python 3.10 ou superior instalado.

### Passo 1: Clonar e Preparar o Ambiente
Abra o terminal na pasta raiz do projeto e crie uma *Virtual Environment* (venv):

**No Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

### Passo 2: Instalar Dependências
```Bash
pip install fastapi uvicorn pydantic
```

### Passo 3: Rodar o Servidor
```Bash
uvicorn main:app --reload
```

> Nota: O servidor será iniciado em http://127.0.0.1:8000.

## Testando a API
A aplicação conta com uma interface gráfica interativa (Swagger) gerada automaticamente, eliminando a necessidade de ferramentas externas como Postman.

1. Com o servidor rodando, acesse no navegador: http://127.0.0.1:8000/docs
2. Expanda o endpoint desejado (ex: /api/v1/otimizar-agenda).
3. Clique no botão "Try it out".
4. Modifique o JSON de entrada (se desejar) e clique em "Execute".
5. Verifique a resposta da API e acompanhe os logs detalhados exibidos diretamente no seu terminal!

## Equipe / Autores
- Arthur Gomes | RM 560771
- Luiz Silva | RM 560110
- Matheus Siroma | RM 560248
- Pedro Estevam | RM 560642
- Witalon Rodrigues | RM 559023
