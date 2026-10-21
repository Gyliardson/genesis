# GENESIS

**Autonomous Intelligence & Neuroevolution Laboratory**

> **Estado:** concepção / preparação da pesquisa. Nenhum ganho de desempenho foi demonstrado.

GENESIS é um laboratório experimental de **neuroevolução, aprendizagem adaptativa e sistemas autônomos**, com uma primeira aplicação prática: **escalonar workloads computacionais em um ambiente controlado**.

A proposta não é criar um chatbot, automatizar um fluxo com LLMs nem substituir diretamente o escalonador do sistema operacional. É estudar se controladores que aprendem ou evoluem suas políticas de decisão conseguem alocar recursos em condições variáveis, como filas, capacidade limitada, tarefas concorrentes e falhas.

## Objetivos

1. Construir ambientes de simulação determinísticos e reprodutíveis.
2. Comparar **políticas clássicas** com **controladores neurais evoluídos**, sem presumir qual vencerá.
3. Exportar e reproduzir políticas treinadas em cenários inéditos.
4. Evoluir para workloads reais, inicialmente **isolados, de baixo risco e com fallback**.
5. Preservar trilhas futuras de neurociência computacional, vida artificial, transferência de cérebros e previsão de estados.

## Primeiro caso de uso: escalonamento adaptativo

- **Entrada:** fila de jobs, estimativas observáveis de demanda/duração, disponibilidade de CPU/memória e histórico operacional permitido.
- **Saída:** escolha de um job elegível para execução (ou aguardar, se isso for uma ação válida).
- **Restrições:** capacidade de recursos, isolamento e conjunto de ações válidas; no MVP, um único nó e execução não preemptiva.
- **Avaliação:** tempo de conclusão, espera, throughput, utilização, equidade/starvation, custo de decisão e generalização.

Uma política que só funciona nos cenários de treinamento **não será considerada validada**.

## Marcos

| Marco | Escopo | Estado |
| --- | --- | --- |
| M0 — Research Foundation | Escopo, hipóteses, contratos e CI | Planejado |
| M1 — Simulation Core | Ambiente reprodutível, workloads sintéticos, baselines e métricas | Planejado |
| M2 — Neuroevolution | Controlador neural mínimo e evolução; primeiro MVP | Planejado |
| M3 — Scientific Validation | Testes independentes, repetições e ablações | Planejado |
| M4 — Real Workloads | Workers isolados e fallback, sem acesso privilegiado | Futuro |
| M5 — Advanced Research | Plasticidade, transferência, ciência cognitiva e novos domínios | Exploratória |

## Documentação de referência

- [Visão, escopo e motivações](docs/vision.md)
- [Arquitetura provisória](docs/architecture.md)
- [Hipóteses e desenho dos experimentos](docs/experiments.md)
- [Pesquisa e referências externas](docs/research.md)
- [Registro de decisões e questões abertas](docs/decisions.md)
- [Plano de execução](docs/roadmap.md)

**Backlog oficial:** [GitHub Issues](../../issues). Tarefas não devem ser duplicadas como checklists paralelos em documentação.

## Tecnologias — candidatas, não decisões finais

- **Linguagem:** Python (decidido).
- **Simulação:** SimPy ou motor de eventos discreto próprio (em avaliação).
- **Neuroevolução:** pesos de rede de topologia fixa e algoritmo genético pequeno primeiro; NEAT e outras estratégias depois (a pesquisar).
- **Dados e experimentação:** NumPy, pytest e formatos leves; demais dependências condicionadas a benchmark.
- **Validação externa:** eventualmente ambiente Gymnasium e workloads Docker isolados, sujeitos a experimentação e revisão.

A estrutura inicial será pequena; não há motivo para introduzir uma API web, Kubernetes, GPUs ou um banco distribuído apenas para dar aparência de complexidade.

## Como colaborar com a pesquisa

1. Consulte as [hipóteses](docs/experiments.md) e [decisões abertas](docs/decisions.md).
2. Escolha uma Issue e descreva critérios de conclusão verificáveis.
3. Para qualquer alegação de melhoria, reporte cenários, seeds, baselines, métricas e limitações.
4. Registre revisões de arquitetura como propostas, nunca como fatos já comprovados.

**Aviso:** GENESIS é um estudo de sistemas adaptativos. Não alega criar consciência artificial, emular cérebros biológicos ou produzir políticas superiores antes dos experimentos.
