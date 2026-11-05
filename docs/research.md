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
8. **Dongare et al., “Hybrid Learning and Optimization-Based Dynamic Scheduling for DL Workloads on Heterogeneous GPU Clusters” (conferência SoCC ’25, 19–21 novembro 2025; preprint arXiv 11 dezembro 2025; artigo ACM publicado em 13 janeiro 2026)**: [preprint dos autores](https://arxiv.org/abs/2512.10271), [DOI ACM](https://doi.org/10.1145/3772052.3772257). RLTune combina priorização via RL e alocação via MILP em clusters de GPU heterogêneos. Autores reportam até 20% mais utilização, redução de até 81% no tempo em fila e até 70% em JCT sob seus testes. **Limites:** números máximos reportados não caracterizam efeitos médios gerais; GPU, mapeamento multi-nó e custo MILP estão fora do MVP e não foram reproduzidos.
9. **Wu et al., “A deep reinforcement learning model for dynamic job-shop scheduling problem with uncertain processing time” (Engineering Applications of AI, 2024)**: [artigo primário](https://doi.org/10.1016/j.engappai.2023.107790). Aborda incertezas nos tempos de operação em dynamic job-shops. **Limite:** problema e dinâmica de manufatura diferem; motiva testes de estimate shift, não adoção de arquitetura específica.

**REVIEW LIMITATIONS:** Decima foi inspecionado em manuscrito; os demais estudos foram verificados por páginas editoriais, registros científicos e/ou abstracts, não por auditoria integral dos experimentos e artefatos. Esta revisão não checou código, dados brutos, custos de hardware ou reprodutibilidade de todos os trabalhos. Traces operacionais introduzem licença, filtragem, missingness, privacidade, workloads truncados e desafios contrafactuais; replay não comprova desempenho de uma policy em workloads reais.

#### Matriz de alternativas (PROPOSAL)

| Política | Informações legais necessárias | Vantagem | Limitação / risco | Custo aproximado por decisão |
| --- | --- | --- | --- | --- |
| FCFS estrito (somente diagnóstico no A) | chegada, id, demandas e capacidade | diagnostica head-of-line blocking | ilegal como competição START-only quando head bloqueado e posterior cabe; exige protocolo B com WAIT para todos | O(1) para acessar head, **não** E2E |
| FCFS-scanning (*first eligible fit*) | chegada/ID, máscara, CPU/mem livres | baseline **competitiva em ActionA_v0 ACCEPTED**, admite primeiro elegível | não reserva início do head: **não** é EASY/conservative backfilling; pode gerar starvation | O(n) escolha; máscara/safety extra |
| Shortest Estimated Job First | duração estimada e máscara de elegibilidade | potencial menor sojourn médio | estimation bias, long-job starvation | O(n) com argmin; sorting O(n log n) |
| First-fit / best-fit CPU+mem | demandas e recursos livres, score de fragmentação predefinido | reduz fragmentação de recursos | ignora duration e classes | O(n) |
| Aging / Estimated-HRRN | estimativa, waiting age, recursos | reduz propensão a starvation | piores estimates e aumento de espera média | O(n) |
| Random-valid | máscara | controle estocástico e sanity check | fraco; não sustenta superioridade de ML | O(n) para construir lista |
| Neural não treinada | mesma observação da learned policy | ablação de representação/training | custo e viés sem aprendizado | depende do modelo / tamanho de fila |

**ACTION-SPACE RATIFICADO (F01; D-017 ACCEPTED em 2026-11-04):** **ActionA_v0** exige START quando qualquer job é factível e avanço forçado do motor quando nenhum cabe. Logo FCFS-scanning é referência clássica válida para B*, enquanto FCFS estrito que preserva head exige WAIT e é **somente diagnóstico separado**. Exemplo HOL: head exige 2 CPU, existe 1 CPU livre e job posterior requer 1 CPU; START obrigatório impede espera pelo head. **ActionB_v1 DEFERRED** permitiria, se aprovada futuramente, WAIT voluntário limitado para todos, com custo, safety, fairness e stall comuns; FCFS estrito poderia então competir **somente dentro de B**. D-017 foi ratificada na [Issue #3](https://github.com/Gyliardson/genesis/issues/3#issuecomment-6640438542); esta pesquisa não comprova implementação/teste de EXP-001. Selecionar B* somente dentro de ActionA_v0, com demais decisões metodológicas pendentes. Não confundir scanning com backfilling que faz reserva/garantia ao head.

**OVERHEAD (F07):** custos O(1)/O(n) da matriz são apenas da regra de seleção; medir custo **end-to-end** da construção de Observation, geração de máscara, normalização, policy/ranking, verificação safety/fallback e telemetria, com p50/p95, soma por episódio, número de decisões, CPU/RAM e treinamento. Máscara O(n) pode dominar uma escolha head O(1); não confundir tempo lógico com wall-clock/CPU real.

**EXCLUSIONS:** SJF-oracle com duração real oculta, SRPT e qualquer política com preempção, conhecimento de chegada futura e controladores de DAG/paralelismo inexistente. Um oracle offline, se usado, é bound diagnóstico **não elegível para competição**. Comparações devem usar mesmas ações/máscaras, fallback, capacidade, trabalhos/estimativas e gerador exógeno; configurar baseline forte em validation, não selecionar vencedora pelo test.

#### Onde aprender poderia valer a pena?

**HYPOTHESIS:** há oportunidade sob carga com contenção, demanda CPU-heavy e memory-heavy complementar, bursts, mistura long/short e estimativas ruidosas/condicionadas a classe. O benefício pode decorrer de ordenação que evite fragmentação e starvation simultaneamente, mas heurísticas ajustadas podem capturar o mesmo padrão a custo menor.

**CONTROLES NEGATIVOS condicionais (F05):** igualdade de logs de scheduling apenas quando o protocolo A sem WAIT voluntário e os desempates/eventos determinísticos produzem uma única ação legal por decisão; nos outros casos, mesmo fila unitária ou baixa carga admite WAIT voluntário sob B, e homogeneidade sem mesmas chegadas/durações não implica igualdade. Testar invariantes de factibilidade separadamente de hipótese de igual qualidade. Não forçar ganho de ML como objetivo. **Stress tests:** caudas longas, subestimação adversarial, drift de duração/arrivals, sobrecarga (reportar backlog/censura), pressão de memória com CPU livre e diferenças entre classes. A vantagem real exige efeito robusto também em seeds e distribuições não vistas.

**PROPOSAL — comparação justa (D-025 OPEN):** usar candidato R_geo = exp(média ponderada **por estrato** das log-razões de médias de sojourn por coorte completa e cenário pareado, depois média sobre K seeds independentes de treinamento e E seeds de avaliação, inclusive quando B* é estocástica, preservando B*(s,i,e) compartilhada entre k e dependências do desenho cruzado); pesos candidatos iguais entre famílias fixados antes de TEST, B* escolhida por score VAL com constraints/fallback idênticos. Usar bootstrap cruzado de unidades de cenário e seeds de treino e ICs simultâneos/margens para guardrails, nunca jobs como observações independentes. Censura, TIMEOUT, POLICY_STALL ou erro em qualquer braço requerido impede a **confirmação global H1**, sem excluir pares seletivamente; números de falhas entram no denominador. Detalhes e alternativas a ratificar em [experiments.md](experiments.md).

**PROPOSAL — comparação justa:** traces exógenos fixos por seed, fronteira de observação idêntica, B* escolhida em validação, políticas não preemptivas, múltiplas seeds de training e cenários de test, IC pareado, custos de treino e inference, média/p95 de sojourn/espera, throughput, makespan apenas em batch drenado, utilização CPU/mem, starvation, fairness por classe, pendências e censoring explícito. Jobs incompletos não podem desaparecer das médias sem relatório/penalty; rewards não podem incentivar WAIT infinito. Ver protocolo detalhado em [experiments.md](experiments.md).

**DECISION REQUIRED (síntese com RESEARCH-02/03, sem editar ADR):** D-017/ActionA_v0 já ACCEPTED; semântica detalhada D-018/D-020 e falhas D-021; informação observável e estados ocultos; política de jobs inviáveis; horizonte e censura; fairness constraint versus fitness; mínimo efeito útil delta e custos; baseline work-conserving/backfill; representação para fila variável e budget de treino. Não converter OPEN para ACCEPTED com base nesta pesquisa.

## 2. Simulação e benchmark

- **SimPy:** simulador de eventos discretos orientado a processos; candidato natural para chegadas, execução e disputa de recursos. [Documentação oficial](https://simpy.readthedocs.io/).
- **Gymnasium:** interface padronizada para ambientes de aprendizado, útil se houver RL no benchmark. [Criar ambiente customizado](https://gymnasium.farama.org/tutorials/gymnasium_basics/environment_creation/).
- **Stable-Baselines3:** candidatos a baselines de RL, somente após a validação do ambiente e da função-objetivo. [Documentação](https://stable-baselines3.readthedocs.io/).
- **Pesquisa a fazer:** representar decisões de scheduling por eventos versus passos fixos; observações e espaços de ação variáveis; desbalanceamento e starvation; custo de simulação na avaliação de populações.

## 3. Neuroevolução e aprendizagem

- **NEAT (Stanley & Miikkulainen, 2002):** evolução simultânea de topologia e pesos, possível etapa posterior. [NEAT-Python](https://neat-python.readthedocs.io/).
- **Alternativas para benchmark (a pesquisar):** busca aleatória, algoritmos genéticos de topologia fixa, CMA-ES, ES e RL model-free. Escolher segundo amostragem, escalabilidade e métricas; não por popularidade.
- **Plasticidade:** avaliar em investigação separada se adaptação *online* traz benefício em mudanças de distribuição; evitar confundir aprendizagem do indivíduo com evolução entre gerações.


### Consolidação limitada de RESEARCH-03: neuroevolução e desenho do benchmark (F06)

**EVIDENCE (fontes e comentários, não eficácia comprovada):** as análises específicas de RESEARCH-03 já estão registradas em [G-009](https://github.com/Gyliardson/genesis/issues/9#issuecomment-6330082508), [G-010](https://github.com/Gyliardson/genesis/issues/10#issuecomment-6330083086) e [G-019](https://github.com/Gyliardson/genesis/issues/19#issuecomment-6330083740). Esta síntese documenta o essencial sem duplicar contratos de interface/ADR nem assumir ownership desses trabalhos. D-007/D-008/D-010/D-023 permanecem OPEN/PROPOSED no PR #22; G-019 depende de resultados futuros de #9/#10/#12 e não pode ser marcado como concluído agora.

| Candidato / controle | Mérito hipotético e custo/risco | Condição de comparação e limite |
| --- | --- | --- |
| **Score compartilhado por job** (s_i=fθ(x_i,g)) | equivariância à permutação se g e desempate forem independentes da ordem, ~O(NP); pouco contexto entre jobs | primeira representação candidata; exige máscara de ação, noninterference, N=0/1/grande e latência |
| **Deep Sets** (Zaheer et al. 2017) | agregação simétrica para contexto de outros jobs, ~O(NP); média pode apagar cardinalidade | alternativa sob falha de interação; controlar parâmetros/budget e custo |
| **Top-K/attention/GRU** | top-K pode excluir candidatos; attention frequentemente O(N²d); GRU traz estado temporal e custo | adiar até evidência; testar viés, permutação, overhead e memória separadamente |
| **Random search** de pesos | controle mínimo de exploração; simples mas pode exigir muitas avaliações | mesma topologia/objetivo e orçamento de episódios/CPU que GA |
| **GA de topologia fixa** | população, mutação/seleção/recombinação; implementação relativamente pequena | primeira hipótese evolutiva, não escolha aceita; fixar seeds, elitismo, diversidade e budget |
| **ES antitética** | paralelizável; estimativa de gradiente amostral pode consumir muitas avaliações | avaliar sob orçamento de ambiente e wall/CPU-time equivalente |
| **CMA-ES** | adaptação de covariância em parâmetros contínuos; memória tipicamente O(P²) | overhead pode não compensar em dimensões maiores |
| **NEAT** (Stanley & Miikkulainen, 2002) | evolui topologia e pesos; exige inovação/especiação/homologia e tuning | resultado original não é scheduling; **NEAT não resolve N variável sozinho** |
| **RL/PPO** | treinamento por gradientes/trajectories com critic, normalização e masks | grupo metodológico distinto, só depois de validar observação, action space, custo e orçamento |

**Primary methodology references:** [Deep Sets — Zaheer et al. (NeurIPS 2017)](https://arxiv.org/abs/1703.06114); [NEAT — Stanley & Miikkulainen (Evolutionary Computation 2002)](https://doi.org/10.1162/106365602320169811); [CMA-ES — Hansen & Ostermeier (Evolutionary Computation 2001)](https://doi.org/10.1162/106365601750190398); [ES — Salimans et al. (2017)](https://arxiv.org/abs/1703.03864). **Limites:** demonstram métodos/representações em seus domínios, não superioridade na execução não preemptiva do GENESIS; abstracts e protocolos de RESEARCH-03 não substituem reprodução de experimentos ou análise completa de implementações. Evolução de populações **entre gerações** difere de estado recorrente por episódio, plasticidade de pesos em tempo de execução e transferência de políticas congeladas.

**PROPOSAL — benchmark científico (futuro, ainda NOT_RUN):** comparar ao menos random search e GA de topologia fixa, incluindo baselines clássicas, random-valid e rede sem treino, sobre os mesmos traces exógenos; gerar TRAIN/VAL/TEST-ID/OOD independentes, com seeds de treinamento/episódios/hardware/versões e custo por avaliação; registrar convergência *anytime* por episódios e CPU-s, mais orçamento total de tuning e inferência. Não igualar número de gerações ou episódios se o custo de avaliação não for comparável; estabelecer teto **de episódios e de CPU-time**, interrompendo pelo primeiro, mais relatório separado de custo da policy. Piloto de RESEARCH-03 (20 mil episódios, 2 CPU-h, 3 seeds; estudo posterior com 5 seeds e 300 TEST scenarios) é **ilustrativo, não aprovado e não executado**. Censura/falhas seguem EXP-001, com B* congelada em VAL. Comparar média/p95 de sojourn, espera, utilização CPU/mem, fairness/starvation, throughput/backlog, gastos de treino, decisão E2E, incerteza pareada e casos de falha.

**Ablações/controles propostos:** pesos aleatórios, contexto global removido, idade permitida removida, GA sem mutação/sem seleção versus random search, tie/ordem permutados, scores ilegais com máscara, scorer versus Deep Sets, top-K com fila acima K, RESET de memória, mudança de atributos privados que não altere observação e treino em uma vs múltiplas distribuições. Desligar safety mask apenas num teste negativo isolado, nunca como política com poder privilegiado. Repetir seeds; não promover uma única *best seed* nem ajustar comparações pelo TEST.

**DECISION REQUIRED / dependências:** D-017/ActionA_v0 ACCEPTED (2026-11-04), ActionB_v1 DEFERRED; D-018/D-020/D-021 ainda abertos, interface D-008/D-023, simulador/validação #5, métricas e fitness D-010/D-025/#8 e #12 holdout antecedem implementação #9/#10 e comparação empírica #19. As sugestões de ADR pertencem ao PR #22 sob ownership separado; este PR não altera docs/decisions.md e as Issues #1/#2 permanecem abertas até revisão e aceitação efetivas.

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
