# CRM Hospital São Rafael

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100%2B-009688?logo=fastapi)](https://fastapi.tiangolo.com/)

Microserviço desenvolvido como entrega das **Sprints 3 e 4** para a disciplina de **Dynamic Programming**. O objetivo deste serviço é otimizar processos críticos do Hospital São Rafael utilizando algoritmos de alta performance e modelagem de dados.

**Contexto de Negócio:** O Hospital São Rafael foca em cirurgias plásticas e eletivas. Atualmente, a jornada do cliente é manual. Este microserviço automatiza a triagem de leads, a gestão de agendas médicas e otimiza o fluxo de atendimento (buscando o caminho de conversão mais eficiente), priorizando demandas cruciais como a entrega de exames em até 60 dias.

---

## Funcionalidades Principais

### Sprint 3: Programação Dinâmica

1. **Verificação de Duplicidade em Lote (`/api/v1/verificar-duplicidade/lote`)**
    
    Recebe um lote de novos leads oriundos de campanhas (Facebook, Instagram, etc.) e os cruza com a base de dados existente.
    
    - **Regras de Duplicidade:** CPF idêntico, E-mail idêntico ou Nome + Telefone idênticos.
        
    - **Técnica:** Recursão com Memoização. O endpoint permite verificar vários leads simultaneamente. O cache (memo) é compartilhado entre os leads, garantindo que o cruzamento de um novo lead contra um cadastro já analisado seja resolvido em tempo constante.
        
2. **Otimização de Agenda Médica (`/api/v1/otimizar-agenda`)**
    
    Maximiza a prioridade total de atendimentos dentro de uma janela de tempo disponível do médico. Dada uma lista de procedimentos desejados e o tempo disponível, calcula a combinação exata de consultas que maximiza a prioridade/valor para o hospital, sem estourar a carga horária.
    
    - **Técnica:** Programação Dinâmica (_Knapsack 0/1_). Resolve o problema de subproblemas sobrepostos, evitando o recálculo de intervalos de horários já analisados.
        
    - **Reconstrução de Solução:** O algoritmo retrocede pelo mapa de estados para listar exatamente quais consultas foram selecionadas para compor a agenda ideal.
        

### Sprint 4: Grafos e Caminho Mínimo

3. **Otimização de Fluxo de Atendimento (`/api/v1/crm/dijkstra`)**
    
    Modela a jornada do paciente (Lead → Confirmação) como um Grafo Direcionado. Cada transição de fase possui um custo calculado pela fórmula: `custo = tempo_operacional × (1 + taxa_abandono)`.
    
    - **Técnica:** Algoritmo de Dijkstra implementado do zero via `heapq` (Min-Heap). Encontra o caminho mais eficiente penalizando rotas com alto risco de perda do lead (abandono).
        
    - **Interpretação e Visualização:** Enumera os caminhos alternativos justificando a escolha algorítmica e fornece a renderização do grafo em imagem PNG diretamente pela API.
        

---

## Arquitetura e Tecnologias

- **Linguagem:** Python 3
    
- **Framework Web:** FastAPI
    
- **Validação de Dados:** Pydantic
    
- **Servidor ASGI:** Uvicorn
    
- **Visualização (Grafos):** Matplotlib & NetworkX
    

**Estrutura Modular do Projeto:**

A arquitetura foi refatorada seguindo boas práticas de separação de responsabilidades (SRP):

Plaintext

```
challenge-hospital-sao-rafael/
├── main.py                  # Endpoints de API e tratamentos de excessão
├── schemas/
│   └── models.py            # Classes do projeto
└── service/
    ├── algoritmo_sprint_3.py # Lógica de Recursão e DP
    ├── algoritmo_sprint_4.py # Modelagem do Grafo e Dijkstra
    └── visualizacao.py       # Renderização de imagem do grafo
```

---

## Análise de Complexidade (Algoritmos)

Abaixo detalhamos a complexidade computacional das soluções implementadas, evidenciando o ganho de performance obtido pelas técnicas da disciplina:

### 1. Otimização de Agenda (Knapsack 0/1)

- **Complexidade de Tempo:** $O(N \cdot W)$
    
    - Onde $N$ é o número total de consultas analisadas e $W$ é o tempo disponível do médico em minutos.
        
    - _Justificativa:_ Graças à memoização, cada subproblema definido pelo estado `(tempo_disponivel, n)` é calculado no máximo uma vez. Sem DP, a complexidade seria exponencial $O(2^N)$.
        
- **Complexidade de Espaço:** $O(N \cdot W)$
    
    - Devido ao tamanho máximo do dicionário de `memo` armazenando os subproblemas e o limite da pilha de chamadas recursivas.
        

### 2. Verificação de Duplicidade de Leads (Lote)

- **Complexidade de Tempo (Pior Caso):** $O(L \cdot C)$
    
    - Onde $L$ é a quantidade de leads no lote e $C$ é o tamanho da base de cadastros.
        
    - _Otimização Prática:_ Embora o limite superior no pior caso seja quadrático (se todos os leads forem únicos e diferentes da base), a **memoização** faz com que a complexidade de pares idênticos repetidos dentro do mesmo contexto caia para $O(1)$.
        
- **Complexidade de Espaço:** $O(U)$
    
    - Onde $U$ é o número de pares únicos comparados `(lead, cadastro)`, limitando o tamanho do cache.
        

### 3. Caminho Mínimo no Fluxo CRM (Dijkstra)

- **Complexidade de Tempo:** $O((V + E) \log V)$
    
    - Onde $V$ é o número de vértices (etapas do CRM) e $E$ é o número de arestas (transições).
        
    - _Justificativa:_ A extração do nó de menor custo usa uma fila de prioridade (Min-Heap via `heapq`), garantindo eficiência máxima mesmo se o grafo crescer consideravelmente.
        
- **Complexidade de Espaço:** $O(V)$
    
    - Para armazenar as distâncias, predecessores e a fila de prioridade.
        

---

## Como Executar o Projeto Localmente

Siga o passo a passo abaixo para rodar a aplicação em um ambiente virtual isolado.

### Pré-requisitos

- Python 3.10 ou superior instalado.
    

### Passo 1: Clonar e Preparar o Ambiente

Abra o terminal na pasta raiz do projeto e crie uma _Virtual Environment_ (venv):

**No Windows:**

Bash

```
python -m venv venv
venv\Scripts\activate
```

**No Linux/Mac:**

Bash

```
python3 -m venv venv
source venv/bin/activate
```

### Passo 2: Instalar Dependências

Bash

```
pip install -r requirements.txt
```

### Passo 3: Rodar o Servidor

Bash

```
uvicorn main:app --reload
```

> Nota: O servidor será iniciado em `[http://127.0.0.1:8000](http://127.0.0.1:8000)`.

---

## Testando a API

A aplicação conta com uma interface gráfica interativa (Swagger) gerada automaticamente, eliminando a necessidade de ferramentas externas como Postman.

1. Com o servidor rodando, acesse no navegador: `[http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)`
    
2. Expanda o endpoint desejado (ex: `/api/v1/crm/dijkstra`).
    
3. Clique no botão "Try it out".
    
4. Modifique os parâmetros ou JSON de entrada e clique em "Execute".
    
5. Verifique a resposta da API e acompanhe os logs detalhados exibidos diretamente no seu terminal!
    

### Exemplo 1: Otimizar Agenda (`/api/v1/otimizar-agenda`)

**JSON de Entrada:**

JSON

```
{
  "consultas": [
    {"procedimento": "Avaliação Cirurgia", "duracao": 60, "prioridade": 10},
    {"procedimento": "Entrega Exames", "duracao": 30, "prioridade": 8},
    {"procedimento": "Pós-Operatório", "duracao": 45, "prioridade": 7}
  ],
  "tempo_disponivel": 80
}
```

**Resposta esperada:** O algoritmo escolherá "Entrega Exames" + "Pós-Operatório" (Prioridade 15), pois cabem nos 80min, ao contrário da "Avaliação" (Prioridade 10).

### Exemplo 2: Verificação em Lote (`/api/v1/verificar-duplicidade/lote`)

Demonstra a eficiência da memoização. Ao enviar dois leads novos que possuem o mesmo CPF contra uma base de dados, o algoritmo processa o primeiro e recupera o resultado do segundo diretamente do cache.

**JSON de Entrada:**

JSON

```
{
  "novos_leads": [
    {"nome": "Ana Souza", "cpf": "555.444.333-22", "email": "ana@teste.com", "telefone": "11911112222"},
    {"nome": "Ana Souza Silva", "cpf": "555.444.333-22", "email": "ana.silva@teste.com", "telefone": "11911112222"}
  ],
  "banco_cadastros": [
    {"nome": "Ana Souza", "cpf": "555.444.333-22", "email": "ana@teste.com", "telefone": "11911112222"}
  ]
}
```

**O que observar:** No retorno, o campo `cache_entradas` mostrará como o sistema reaproveitou as comparações, e o log do terminal confirmará que a recursão foi poupada pela memoização.

### Exemplo 3: Grafo e Caminho Ótimo (`/api/v1/crm/dijkstra`)

Mapeia o melhor fluxo de CRM de `Lead` para `Confirmacao`. Retorna o custo de cada etapa, a interpretação da análise e um PNG codificado em base64 com a visualização do caminho.

- **Dica Extra:** Acesse diretamente no seu navegador a URL `[http://127.0.0.1:8000/api/v1/crm/grafo/imagem](http://127.0.0.1:8000/api/v1/crm/grafo/imagem)` para ver a renderização do grafo plotada em tempo real!
    

---

## Equipe / Autores

- Arthur Gomes | RM 560771
    
- Luiz Silva | RM 560110
    
- Matheus Siroma | RM 560248
    
- Pedro Estevam | RM 560642
    
- Witalon Rodrigues | RM 559023
