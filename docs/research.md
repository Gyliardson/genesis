# Pesquisa inicial e bibliografia viva

> Revisão **exploratória**, iniciada em 2026-10-21. Links são pontos de partida, não prova de que uma técnica servirá ao GENESIS. Atualizar após leitura dos artigos e reprodução dos resultados.

## 1. Escalonamento aprendido

- **Decima (Mao et al., SIGCOMM 2019)** — `Learning Scheduling Algorithms for Data Processing Clusters`: demonstra RL para políticas de escalonamento em clusters. É **antecedente importante**, então não devemos anunciar scheduling por IA como conceito inédito. [Página do MIT](https://web.mit.edu/decima/index.html) · [Registro do artigo](https://dspace.mit.edu/entities/publication/b5ecbc09-0de5-401e-b4e6-55d58e3ac242) · [Simulador de referência](https://github.com/hongzimao/decima-sim).
- **Pesquisa a fazer:** diferenças de objetivos e workloads entre Decima e GENESIS; comparações honestas com heurísticas; viabilidade de neuroevolução sob chegadas estocásticas; overhead e generalização.


### RESEARCH-01 — revisão crítica específica de scheduling (2026-10-21)

**EVIDENCE — literatura primária; não experimentos do GENESIS.** Resultados não se transferem automaticamente entre cluster Spark, GPU, M/G/1 preemptivo, job-shop industrial e o MVP de um nó, CPU/memória discretos, jobs independentes e não preemptivos. Evidência dos artigos é distinta de proposições sobre GENESIS.

1. **Mao, Alizadeh, Menache & Kandula, “Resource Management with Deep Reinforcement Learning” (HotNets 2016)**: [artigo/registro Microsoft Research](https://www.microsoft.com/en-us/research/?p=354038), [DOI](https://doi.org/10.1145/3005745.3005750). DeepRM reformula packing multirrecurso como decisão de RL e reporta resultado inicial **comparável** a heurísticas fortes. Não demonstra superioridade universal, generalização fora da distribuição ou desempenho real do GENESIS; não usar DeepRM como licença para treinar antes de validar simulador.
2. **Mao et al., “Learning Scheduling Algorithms for Data Processing Clusters” (SIGCOMM 2019)**: [paper completo MIT](https://web.mit.edu/decima/content/sigcomm-2019.pdf), [DOI](https://doi.org/10.1145/3341302.3342080), [projeto Decima](https://web.mit.edu/decima/). RL com grafos de dependência (DAGs), paralelismo ajustável, chegadas contínuas, pareamento de sequências para reduzir variância e integração Spark. Os autores mediram redução de JCT médio de pelo menos 21% versus heurísticas ajustadas num cluster de 25 nós, com ganhos de até 2x em carga elevada. O artigo também testa fidelidade do simulador contra jobs reais e faz ablações. **Limites:** DAGs, paralelismo variável, múltiplos nós e estimativas de estágios não existem no MVP; ganhos percentuais não são diretamente comparáveis. Nenhuma replicação independente desta revisão.
3. **Wierman & Nuyens, “Scheduling despite inexact job-size information” (2008)**: [registro primário Caltech](https://authors.library.caltech.edu/records/k6qfy-vsj29). Analisa bounds sobre tempo médio, cauda, slowdown e schedulers size-based com previsões imperfeitas. **Limite:** teoremas e famílias como SRPT requerem modelos de fila/preempção distintos; apenas motivam investigar estimativas versus informação perfeita.
4. **“Revisiting Size-Based Scheduling with Estimated Job Sizes” (IEEE MASCOTS 2014)**: [fonte primária](https://doi.org/10.1109/MASCOTS.2014.57). O estudo com simulações e workloads sintéticos/reais identifica assimetria: *subestimar* trabalho pode prejudicar mais amplamente que *superestimar*; skew e qualidade da estimativa condicionam resultados. **Limites:** políticas size-based de filas distintas e eventuais hipóteses preemptivas não são automaticamente baselines legais no MVP.
5. **“Uniform Bounds for Scheduling with Job Size Estimates” (ITCS 2022)**: [fonte primária Dagstuhl](https://drops.dagstuhl.de/entities/document/10.4230/LIPIcs.ITCS.2022.114). Prova bounds no modelo M/G/1 quando a estimativa pertence a uma faixa multiplicativa da duração real; usar ingenuamente certas versões preemptivas de SRPT com estimates pode ser arbitrariamente ruim. **Limite:** não é um bound matemático para CPU+memória, vários jobs concorrentes e não preempção.
6. **Mondal, Sheoran & Mitra, “Scheduling of Time-Varying Workloads Using Reinforcement Learning” (AAAI 2021; página disponibilizada em 2023)**: [fonte primária AAAI](https://aaai.org/papers/09000-scheduling-of-time-varying-workloads-using-reinforcement-learning/), [DOI](https://doi.org/10.1609/aaai.v35i10.17088). Examina padrões temporais de consumo e traces Google/Alibaba. **Limite:** reservas fixas do GENESIS não modelam picos/vales de uso intra-job, justamente a informação explorada nesse trabalho.
7. **Zhang et al., “Deep Reinforcement Learning Guided Improvement Heuristic for Job Shop Scheduling” (ICLR 2024)**: [paper primário](https://proceedings.iclr.cc/paper_files/paper/2024/hash/c75abb33341363ee874a71f81dc45a3a-Abstract-Conference.html). Relata melhoria de soluções de *job-shop* por RL + GNN; evidencia importância da formulação e controles fortes. **Limite:** planejamento industrial de operações conhecidas não coincide com admissões online de jobs independentes.
8. **Dongare et al., “Hybrid Learning and Optimization-Based Dynamic Scheduling for DL Workloads on Heterogeneous GPU Clusters” (preprint dezembro 2025, SoCC)**: [preprint dos autores](https://arxiv.org/abs/2512.10271), [DOI ACM](https://doi.org/10.1145/3772052.3772257). RLTune combina priorização via RL e alocação via MILP em clusters de GPU heterogêneos. Autores reportam até 20% mais utilização, redução de até 81% no tempo em fila e até 70% em JCT sob seus testes. **Limites:** números máximos reportados não caracterizam efeitos médios gerais; GPU, mapeamento multi-nó e custo MILP estão fora do MVP e não foram reproduzidos.
9. **Wu et al., “A deep reinforcement learning model for dynamic job-shop scheduling problem with uncertain processing time” (Engineering Applications of AI, 2024)**: [artigo primário](https://doi.org/10.1016/j.engappai.2023.107790). Aborda incertezas nos tempos de operação em dynamic job-shops. **Limite:** problema e dinâmica de manufatura diferem; motiva testes de estimate shift, não adoção de arquitetura específica.

**REVIEW LIMITATIONS:** Decima foi inspecionado em manuscrito; os demais estudos foram verificados por páginas editoriais, registros científicos e/ou abstracts, não por auditoria integral dos experimentos e artefatos. Esta revisão não checou código, dados brutos, custos de hardware ou reprodutibilidade de todos os trabalhos. Traces operacionais introduzem licença, filtragem, missingness, privacidade, workloads truncados e desafios contrafactuais; replay não comprova desempenho de uma policy em workloads reais.

#### Matriz de alternativas (PROPOSAL)

| Política | Informações legais necessárias | Vantagem | Limitação / risco | Custo aproximado por decisão |
| --- | --- | --- | --- | --- |
| FCFS estrito | chegada, id, capacidade e demandas públicas | simples, ordem transparente | head-of-line blocking | O(1) para testar head |
| FCFS scanning / backfill | mesmos dados FCFS | aproveita espaço atrás do head | pode atrasar head indefinidamente | O(n) |
| Shortest Estimated Job First | duração estimada e máscara de elegibilidade | potencial menor sojourn médio | estimation bias, long-job starvation | O(n) com argmin; sorting O(n log n) |
| First-fit / best-fit CPU+mem | demandas e recursos livres, score de fragmentação predefinido | reduz fragmentação de recursos | ignora duration e classes | O(n) |
| Aging / Estimated-HRRN | estimativa, waiting age, recursos | reduz propensão a starvation | piores estimates e aumento de espera média | O(n) |
| Random-valid | máscara | controle estocástico e sanity check | fraco; não sustenta superioridade de ML | O(n) para construir lista |
| Neural não treinada | mesma observação da learned policy | ablação de representação/training | custo e viés sem aprendizado | depende do modelo / tamanho de fila |

**EXCLUSIONS:** SJF-oracle com duração real oculta, SRPT e qualquer política com preempção, conhecimento de chegada futura e controladores de DAG/paralelismo inexistente. Um oracle offline, se usado, é bound diagnóstico **não elegível para competição**. Comparações devem usar mesmas ações/máscaras, fallback, capacidade, trabalhos/estimativas e gerador exógeno; configurar baseline forte em validation, não selecionar vencedora pelo test.

#### Onde aprender poderia valer a pena?

**HYPOTHESIS:** há oportunidade sob carga com contenção, demanda CPU-heavy e memory-heavy complementar, bursts, mistura long/short e estimativas ruidosas/condicionadas a classe. O benefício pode decorrer de ordenação que evite fragmentação e starvation simultaneamente, mas heurísticas ajustadas podem capturar o mesmo padrão a custo menor.

**CONTROLES NEGATIVOS:** workload homogêneo com uma única escolha válida, fila unitária, baixa carga sem concorrência ou jobs simultâneos indistinguíveis. Policies podem ter outcomes iguais nesses regimes; não forçar ganho de ML como objetivo. **Stress tests:** caudas longas, subestimação adversarial, drift de duração/arrivals, sobrecarga (reportar backlog/censura), pressão de memória com CPU livre e diferenças entre classes. A vantagem real exige efeito robusto também em seeds e distribuições não vistas.

**PROPOSAL — comparação justa:** traces exógenos fixos por seed, fronteira de observação idêntica, B* escolhida em validação, políticas não preemptivas, múltiplas seeds de training e cenários de test, IC pareado, custos de treino e inference, média/p95 de sojourn/espera, throughput, makespan apenas em batch drenado, utilização CPU/mem, starvation, fairness por classe, pendências e censoring explícito. Jobs incompletos não podem desaparecer das médias sem relatório/penalty; rewards não podem incentivar WAIT infinito. Ver protocolo detalhado em [experiments.md](experiments.md).

**DECISION REQUIRED (síntese com RESEARCH-02/03, sem editar ADR):** semântica do tempo/eventos e WAIT; informação observável e estados ocultos; política de jobs inviáveis; horizonte e censura; fairness constraint versus fitness; mínimo efeito útil delta e custos; baseline work-conserving/backfill; representação para fila variável e budget de treino. Não converter OPEN para ACCEPTED com base nesta pesquisa.

## 2. Simulação e benchmark

- **SimPy:** simulador de eventos discretos orientado a processos; candidato natural para chegadas, execução e disputa de recursos. [Documentação oficial](https://simpy.readthedocs.io/).
- **Gymnasium:** interface padronizada para ambientes de aprendizado, útil se houver RL no benchmark. [Criar ambiente customizado](https://gymnasium.farama.org/tutorials/gymnasium_basics/environment_creation/).
- **Stable-Baselines3:** candidatos a baselines de RL, somente após a validação do ambiente e da função-objetivo. [Documentação](https://stable-baselines3.readthedocs.io/).
- **Pesquisa a fazer:** representar decisões de scheduling por eventos versus passos fixos; observações e espaços de ação variáveis; desbalanceamento e starvation; custo de simulação na avaliação de populações.

## 3. Neuroevolução e aprendizagem

- **NEAT (Stanley & Miikkulainen, 2002):** evolução simultânea de topologia e pesos, possível etapa posterior. [NEAT-Python](https://neat-python.readthedocs.io/).
- **Alternativas para benchmark (a pesquisar):** busca aleatória, algoritmos genéticos de topologia fixa, CMA-ES, ES e RL model-free. Escolher segundo amostragem, escalabilidade e métricas; não por popularidade.
- **Plasticidade:** avaliar em investigação separada se adaptação *online* traz benefício em mudanças de distribuição; evitar confundir aprendizagem do indivíduo com evolução entre gerações.

## 4. Traços operacionais reais

- [Google Cluster Data](https://github.com/google/cluster-data): traces históricos, documentação e restrições de uso a conferir. Pode exigir agregação/amostragem e harmonização de esquemas.
- [Alibaba ClusterData](https://github.com/alibaba/clusterdata): registros públicos de cargas; estudar campos, licenças, perfis e vieses.
- **Risco:** replay de traces sem capacidades e sem contrafactuais adequados pode produzir comparações inválidas; primeiro validar em workloads sintéticos controlados.

## 5. Neurociência, vida artificial e motivação de longo prazo

- **Connectomics:** circuitos de Drosophila e *C. elegans* oferecem referência para arquitetura neural e modelos experimentais. O mapa de conexões, sozinho, não simula funcionamento cerebral nem representa transferência de consciência.
- [OpenWorm / c302](https://github.com/openworm/c302): referência para circuitos neurais simplificados.
- [Brian2](https://brian2.readthedocs.io/): candidata para neurônios pulsados e plasticidade sináptica.
- **Vida artificial:** neuroevolução de organismos, evolução aberta e emergência continuam linhas **separadas do scheduling MVP**.
- **Previsão causal:** o Demônio de Laplace inspira experimentos de estimativa de estados sob informação limitada; não há promessa de previsão perfeita de mundos reais.

## Leituras prioritárias — ordem sugerida

1. Decima: objetivo, ambiente, estrutura de ação e baselines.
2. Semântica dos eventos de SimPy e modelagem de recursos.
3. NEAT original e limitações práticas de suas implementações.
4. Construção de benchmarks reprodutíveis de schedulers.
5. Publicações sobre generalização, transfer learning e robustez de controladores.

## Protocolo para atualizar esta revisão

Para cada novo paper ou biblioteca, registrar: **pergunta**, hipótese dos autores, desenho experimental, baselines, métricas, limitações, hardware/custo, licença, replicabilidade e **decisão provisória para GENESIS**. Não transformar abstracts em conclusões.
