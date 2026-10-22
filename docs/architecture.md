# Arquitetura mínima e contratos de domínio — CONTRACT-01

> **STATUS: PROPOSED / DECISION_REQUIRED (2026-10-21).** Especificação candidata e reversível, **não** ratificação de interfaces, escolha de simulador ou implementação. Vinculada a [G-003](https://github.com/Gyliardson/genesis/issues/3) e à [síntese WAVE-01](https://github.com/Gyliardson/genesis/issues/3#issuecomment-6330212075). Os findings de revisão independente do [PR #21](https://github.com/Gyliardson/genesis/pull/21) precisam ser incorporados **antes** de tornar alguma decisão material ACCEPTED. A CI desse PR falhou sem primeira causa confirmada ([G-004](https://github.com/Gyliardson/genesis/issues/4)); não confundir com falha comprovada dos testes.
>
> **Evidência:** RESEARCH-01 = documentação científica no PR #21; RESEARCH-02 = propostas e oráculos nas [Issues #5](https://github.com/Gyliardson/genesis/issues/5), [#6](https://github.com/Gyliardson/genesis/issues/6), [#8](https://github.com/Gyliardson/genesis/issues/8); RESEARCH-03 = matrizes nas [Issues #9](https://github.com/Gyliardson/genesis/issues/9), [#10](https://github.com/Gyliardson/genesis/issues/10), [#19](https://github.com/Gyliardson/genesis/issues/19). Todos os detalhes abaixo são **design proposals**, não resultados experimentais do GENESIS.

## 1. Problema e menor arquitetura verificável

Um único nó lógico; jobs online independentes, não preemptivos, sem migração, CPU e memória como unidades inteiras reservadas do START até COMPLETE. Concorrência entre jobs é permitida quando a soma das duas reservas cabe. Durações verdadeiras são geradas exogenamente e ficam ocultas das policies até a conclusão; estimates são públicas. Não modelar GPU, DAG, deadlines/prioridades, consumo intra-job ou execução real neste contrato. Todo experimento precisa ser reproduzível com eventos e traces versionados antes de qualquer aprendizado.

| Componente | Responsabilidade exclusiva | Não pode fazer |
| --- | --- | --- |
| Workload Generator | Produzir um trace exógeno imutável, independente da policy; streams RNG e hashes versionados | Consultar policy, gerar duração ao iniciar, compartilhar RNG com evolução |
| Simulation Core | Armazenar verdade e estado privado, relógio, ordenação de eventos, transições, reservas e log canônico | Delegar transições ou verdade privada à policy; inferir segurança de logits |
| Observation Projector | Construir snapshot público imutável, age e máscara candidata apenas de campos públicos | Incluir durações verdadeiras, próximo evento, IDs derivados de segredo |
| Policy | Escolher uma ação solicitada a partir de observações públicas; estado interno próprio | Mutar simulação, reservar recursos, executar comandos, ler ambiente interno |
| Safety / Feasibility | Validar payload/tipo, estado READY, máscara, CPU/mem e admissibilidade **novamente** contra estado autoritativo; registrar rejeição/fallback | Confiar na máscara ou no modelo como autoridade; executar side effects |
| Evolution Engine (futuro M2) | Gerar, avaliar e selecionar parâmetros de policies via interface versionada | Mudar regras, observar truth oculto ou executar tarefas externas |
| Evaluation Lab | Rodar políticas em traces pareados; consumir log privado pós-episódio, métricas, censura, custos e incerteza | Devolver métrica/verdade privada à policy durante a decisão |
| Deployment Adapter (futuro) | Shadow/isolation, quota, timeout, fallback, audit, rollback sob autorização | Tratar performance no simulador como aprovação para produção |

Uma única implementação mínima do simulador e um pequeno adapter de policy são suficientes no início. Nenhum plugin/SDK/serviço/framework é pressuposto. SimPy, DES próprio, GA, RL e NEAT continuam sujeitos a evidência (D-006/D-007).

## 2. Tipos e fronteiras — esquema candidato v0

Usar inteiros para CPU/memória e tempo lógico discretizado. `Tick = int >= 0`; `Duration = int > 0`; `Units = int > 0`; `JobId = opaque stable string`; `SchemaVersion = immutable string`. A escala física do tick, limite máximo, regras de quantização, overflow e parse do trace precisam constar no manifesto; proibir float/NaN/Inf em qualquer campo discreto. A policy pode ter scores reais, mas somente finitos e validados no adapter. **Uma conversão silenciosa de floats para tick é proibida.**

### Job — verdade, projeção e lifecycle

| Estrutura | Campos e tipos | Semântica / visibilidade |
| --- | --- | --- |
| `JobSpecPrivate` | `id: JobId`, `arrival_tick: Tick`, `cpu_units: Units`, `memory_units: Units`, `estimated_duration_ticks: Duration`, `actual_duration_ticks: Duration` | Trace imutável; `actual_duration_ticks` **private only**; ID não codifica segredo, prioridade ou classe oculta |
| `JobRuntimePrivate` | `status: FUTURE\|READY\|RUNNING\|COMPLETED\|REJECTED_INFEASIBLE`; `started_at?: Tick`, `completed_at?: Tick` | Pertence exclusivamente ao Core; `ADMIT` é registro instantâneo, não estado durável adicional |
| `ReadyJobPublic` | `id`, `arrival_tick`, `cpu_units`, `memory_units`, `estimated_duration_ticks`, `waiting_age_ticks: Tick` | Apenas jobs READY; `waiting_age_ticks = now - arrival_tick`; snapshot frozen; **sem** actual, remaining, completion forecast, class secret, rank ou index como features |
| `FinalJobOutcome` | `status: COMPLETED\|QUEUED_AT_H\|RUNNING_AT_H\|REJECTED_INFEASIBLE\|POLICY_STALL\|TIMEOUT\|ERROR`; timestamps opcionais, observação censurada | Apenas para Evaluation Lab após run; classificação de episódio e job não é fornecida durante escolha |

Jobs com demanda individual acima da capacidade são rejeitados **antes de admissão**, como cenário negativo explícito; o gerador produtivo deve emitir somente jobs factíveis. Rejeitados nunca entram na máscara/denominador de coorte factível, mas sua contagem é obrigatoriamente publicada. IDs únicos por trace. Estado legal: FUTURE → READY → RUNNING → COMPLETED; rejeição é desfecho de validação, não uma execução. Um job inicia **no máximo uma vez**, termina no máximo uma vez e nunca libera reserva duas vezes.

### ResourcePool

`ResourcePool = {cpu_capacity: Units, memory_capacity: Units, cpu_allocated: int, memory_allocated: int}`; `cpu_free = cpu_capacity - cpu_allocated`, igualmente para memória. Capacidades constantes num episódio. Reservar ambas as dimensões atomicamente na transição START; liberar ambas atomicamente na conclusão. Para todo instante, `0 <= allocated_r <= capacity_r` e `allocated_r = sum(r_j for RUNNING jobs)`. Nunca usar uso observado de sistema real como equivalente a reserva.

### Observation / Action / Policy

| Contrato | Shape v0 / responsabilidade |
| --- | --- |
| `ObservationV0` | `schema_version`, `now_tick: Tick`, `cpu_capacity, cpu_free, memory_capacity, memory_free: int`, `ready_jobs: tuple[ReadyJobPublic,...]`, `eligible_job_ids: tuple[JobId,...]`, `wait_allowed: bool`. Ordenação canônica por `(arrival_tick,id)`; a policy nunca usa posição/ID como score/feature, salvo desempate externo |
| `ActionV0` | **Somente** `START(job_id: JobId)` no regime candidato sem WAIT voluntário. No futuro, `WAIT` requer nova decisão explícita de protocolo/versão; `ADVANCE` e `TERMINATE` são transições internas do Core, **não** ações da Policy |
| `PolicyV0` | `reset(public_config: PublicPolicyConfig, policy_seed: int) -> None`; `decide(observation: ObservationV0) -> ActionV0`. Stateful apenas internamente; nenhuma referência a Core, RNG do gerador, split/trace ID ou objeto com ponteiro para true state. Repetir reset entre episódios |
| `PublicPolicyConfig` | Versões de schema, capacidades e escalas de features derivadas **exclusivamente de TRAIN**. Sem `H_e`, split, trace_hash, duração real, seeds exógenas nem data do próximo evento |
| `ActionMaskV0` | A lista de IDs READY que cabem nas duas capacidades atuais; `wait_allowed=false` no candidato. A máscara reduz a escolha, mas o Safety Layer valida independentemente |
| `ExperimentV0` | `experiment_id`, `schema_versions`, `simulator_commit`, `policy_artifact_version`, `scenario_id`, `split: TRAIN\|VAL\|TEST_ID\|TEST_OOD`, `trace_hash`, `generator_version`, `scenario_seed`, `policy_seed`, `training_seed?`, `arrival_cutoff_tick: Tick`, `evaluation_cutoff_tick: Tick`, `mode: DRAIN\|FIXED_H`, `run_status`, `metrics_version`, `budget`, `environment_metadata` | Manifesto privado do runner; apenas subset estritamente público do config é entregue a Policy. Registrar falhas e artefatos, não apenas runs bem-sucedidos |

`eligible_job_ids` deve ser estável sob permutação da entrada (ordem canônica). Scores neurais por job precisam ser equivariante à permutação; seleção determinística por melhor score finito e, em empates, menor chave pública `(arrival_tick,id)` fora da rede. IDs opacos nunca codificam `actual_duration`, grupo experimental ou futuro. Agregados opcionais públicos ficam **desabilitados em v0**; se adicionados, devem ser funções simétricas apenas da observação e implicam novo schema/ablação. Running jobs são inicialmente representados somente por recursos ocupados; não revelar seu remaining time nem conclusão agendada.

**Exemplo fechado:** pool CPU=2, MEM=2; J1 chega em 0, requer (2,1), estimated=4, actual=3; J2 chega em 0, requer (1,1), estimated=2, actual=1. A observação em 0 lista ambos sem `actual`; ao escolher START(J1), a máscara fica vazia (CPU livre 0). Em t=3 J1 completa e libera; J2 admite e completa em t=4. Os valores `actual` e `completed_at` aparecem somente no trace privado/post-run. Outro trace com `actual` alterado **mas mesma observação pública em 0** deve produzir a mesma decisão em 0 com o mesmo estado/seed de policy.

## 3. Protocolo de eventos e progresso

Para cada timestamp t em ordem não decrescente:

1. Core avança ao menor timestamp de evento externo futuro elegível (chegada ou conclusão), sem revelar seu valor à Policy. Nunca permite `next_tick < now_tick`.
2. Processa **todas** as conclusões em t, ordenadas por ID estável; transita RUNNING→COMPLETED e libera recursos **uma vez**. Depois processa **todas** as chegadas permitidas em t, ordenadas por ID; transita FUTURE→READY ou rejeita inviabilidade explícita.
3. Cria observation/mask imutável **somente após** concluir ambas as fases. Se existe ao menos um elegível e t ainda admite START, chama Policy. Ao receber START válido, Safety valida e Core reserva/inicia atomicamente em t; reconstrói máscara e pode decidir outra vez **no mesmo t**. Cada START remove exatamente um READY e o limite por timestamp é o número inicial de READY (mais arrivals processados), impedindo loop de tempo zero.
4. Se não há elegível, Policy não é chamada: o Core faz `FORCED_ADVANCE` até o próximo evento externo; se nenhum existir e ainda houver READY, marca `POLICY_STALL/ERROR` conforme causalidade, nunca faz spin. Se não houver trabalho pendente/futuro admitido, termina `COMPLETE`.
5. Payload desconhecido, job já iniciado, job fora da máscara, recurso insuficiente, WAIT proibido e score NaN/Inf são `INVALID_ACTION`; safety não altera nenhum recurso. **Fallback candidato:** falhar o episódio como `ERROR`, registrar motivo público sanitizado e outcomes pendentes, sem mascarar falhas com heurística silenciosa. Um fallback explícito comum a todas as policies pode ser proposto posteriormente, com versão e custo contabilizados.

Ordenação total do log: `(tick, phase[COMPLETE,ARRIVE,ADMIT/START,ADVANCE/TERMINATE], sequence, id)`; `sequence` é determinística e estável na serialização. Clock monótono, durações estritamente positivas garantem que START não gera COMPLETE imediato. `log_hash` usa serialização canônica, parâmetros/versionamento fixados, sem depender da ordem de `dict`, hash() de Python ou clock wall-time. Logs privados podem conter verdade; logs e mensagens entregues à Policy só contêm projeções públicas. Nenhum logger/feature/normalizer chamado pela Policy acessa a verdade privada.

**Simultaneidade:** conclusão em t libera recurso antes de chegada em t; ambas precedem a primeira decisão. Empates são resolvidos por IDs opacos estáveis. Incluir eventos em t=0, múltiplas chegadas/conclusões, COMPLETE e ARRIVE no mesmo t, e o caso no limite de horizonte na bateria de oráculos.

## 4. Conflito material — WAIT versus FCFS estrito

**DECISION_REQUIRED: D-017.** A máscara obrigatória `START quando existe job factível` implica política work-conserving relativamente ao conjunto factível, mas **não** permite FCFS estrito head-of-line: se o primeiro READY não couber e um posterior couber, FCFS estrito precisa ociosidade voluntária. Não rotular scanning/backfill como FCFS estrito, nem comparar protocolos diferentes como se fossem iguais.

| Alternativa | Viabiliza FCFS estrito? | Comparabilidade e riscos |
| --- | --- | --- |
| **A (candidata menor MVP):** START obrigatório quando existe elegível; avanço forçado caso contrário; baseline `FCFS-scanning` | **Não**; FCFS head-of-line só como diagnóstico separado, não baseline principal legal | Espaço pequeno, progresso limitado, menos reward hacking; risco de excluir comportamento estratégico de ociosidade; medir starvation de backfill |
| **B:** WAIT voluntário disponível **para todas** as policies com elegíveis; um WAIT consome o timestamp e avança a evento exógeno futuro; falha no último evento; teto de espera/ociosidade/fairness e mesmo fallback | Sim | Captura idle estratégico, porém aumenta ação/censura e risco de stall; requer comparações reexecutadas, métricas e controles mais fortes |
| **C:** exceção de WAIT apenas para FCFS estrito | Sim, mas só por privilégio | **Rejeitar para comparação principal:** action spaces diferentes invalidam paridade informacional/operacional |

**Oráculo discriminativo de WAIT/FCFS:** pool (2,2). R chega em 0, req=(1,1), d=5 e inicia; H chega em 1, req=(2,1), d=1; Z chega em 1, req=(1,1), d=1. Em t=1 H (head) não cabe e Z cabe. Protocolo A com scanning inicia Z@1–2, depois H@5–6. FCFS head-of-line precisaria esperar em t=1, admitir H@5–6 e Z@6–7, portanto requer B. Na ausência de qualquer evento externo futuro, WAIT voluntário B com elegíveis causa POLICY_STALL, nunca um loop. Esse é um oráculo a implementar, não uma medição executada.

**Recomendação para revisão, não aprovação:** A como primeiro protocolo de corretude + scanning-FCFS, SJF-estimado, random-valid e fit com **mesma máscara**. FCFS estrito pode ser oráculo diagnóstico **em protocolo separado e rotulado**, sem comparação inferencial com A. Se a pergunta científica exigir idle intencional, versionar B e exigir evidência: dois oráculos head-blocking e último-evento, taxa de WAIT, idle com elegíveis, pendências/drain e alterações no ranking das baselines sob o **mesmo B**. Ratificar em #3 após revisão independente do PR #21; até lá não declarar uma das alternativas ACCEPTED.

## 5. Horizonte, drain, falhas e censura

Todo cenário possui coorte definida **antes** de executar policies. Candidato: `H_a > 0` define janela de chegadas **[0, H_a)**; jobs com `arrival_tick == H_a` **não** entram na coorte. `H_e >= H_a` é limite de avaliação inclusive para **COMPLETION**; uma conclusão em `t == H_e` conta. Novas admissões START podem ocorrer após `H_a` no modo drain, mas somente enquanto `t < H_e`; não iniciar em `H_e`. Nunca incluir chegadas em/apos `H_a` ao drenar. `H_e`, `H_a` e budget são definidos por config experimental e **não** dependem do desempenho da policy.

- **DRAIN (primário proposto):** após último arrival permitido, continuar executando/reagindo a COMPLETION até concluir todos os jobs factíveis da coorte ou atingir budget pré-fixado `B_drain > 0`, com `H_e = H_a + B_drain`. Se todos completam antes, `end_tick` é a última conclusão; integral de utilização/makespan usa intervalo observado [0,end_tick], não budget não utilizado. Caso timeout, o run é **FAILURE/TIMEOUT**, mantém jobs pendentes e censura; não publicar sua média de concluídos como estimando de coorte completa.
- **FIXED_H:** parar em `H_e`, processar conclusões exatamente em H_e, sem START em H_e; registrar READY como `QUEUED_AT_H` e RUNNING como `RUNNING_AT_H` e respectivos tempos observados; nunca fabricar conclusão depois do cutoff. Métricas são de janela, não comensuráveis automaticamente com a média da coorte drenada.
- **Sem progresso:** se existe READY elegível e policy retorna WAIT proibido/ação inválida, `ERROR`; se WAIT permitido em B mas não há próximo evento que mude o estado, `POLICY_STALL`; jobs inviáveis individualmente são `REJECTED_INFEASIBLE`; jobs válidos ainda em execução no deadline são `TIMEOUT/RUNNING_AT_H` conforme modo. Essas classes nunca se tornam sucesso por filtragem.
- **Censura:** para job da coorte com chegada a e sem conclusão até `t_stop` (H_e no cutoff; instante efetivo da falha se stall/error antecipado), `observed_sojourn_lower_bound = t_stop - a`, `event_observed=false`; para READY sem START, espera observada >= t_stop - a; para RUNNING, espera conhecida é `start-a`, duração de processamento é truncada. Sojourn/espera p50/p95 de jobs completados são **condicionais e rotulados**, não estimadores imparciais da coorte. Reportar completos, running, queued, rejeitados, stall, timeout, fração não iniciada, backlog e bounds por job. Métodos de sobrevivência exigem hipótese explícita sobre censura informativa.
- **Métricas canônicas:** por job `sojourn=completion-arrival`, `wait=start-arrival`; `throughput=completed/window_length`, `utilization_r=integral(allocated_r dt)/(capacity_r*window_length)`; `makespan=last_completion-first_arrival` somente coorte completa drenada; fairness/idade máxima por coorte e overhead por decisão e por episódio; nenhuma métrica usa duração verdadeira como entrada de policy. Traces sem duração de janela positiva exigem tratamento explícito, não divisão por zero.

**Golden A:** pool (2,2), J1(a0,d3,req2/1), J2(a0,d1,req1/1). Scanning FCFS J1@0–3, J2@3–4; waits 0/3, sojourn 3/4; CPU integral 7 e MEM integral 4 em 4 ticks. **Golden B:** pool (1,1), J1@0–2, J2 chega em 2 e executa @2–3, sem WAIT adicional. **Golden C:** pool (1,1), J1@0–5, J2 READY, FIXED_H H_e=3: 0 completos, 1 RUNNING, 1 QUEUED; sojourn médio da coorte **indefinido/censurado**, utilização CPU=1.0 na janela. Referências e extensões na Issue #5.

## 6. Múltiplas policies, filas variáveis e isolamento

O adaptador recebe `ready_jobs` com N variável inclusive N=0, produz `score(job, global_public_context)` se for modelo de ranking, filtra por máscara e escolhe o melhor score **finito**; desempates pelo par público (arrival,id). MLP compartilhada por job (`O(NP)`, P≈custo dos pesos) é primeira **hipótese** em D-008, não compromisso de código. Deep Sets agrega observações simetricamente e entra como alternativa se interação contextual justificar; top-K requer provar que não introduz truncamento danoso; attention/GRU são posteriores. Normalização só sobre TRAIN; N, classes e pressão fora da distribuição precisam ser exercitados.

Todas as heurísticas, rede não treinada, aleatório-válido e policy treinada passam por **mesma** ObservationV0, máscara, safety, condições de erro e orçamento. FCFS scanning desempata por (arrival,id), SJF usa **estimated_duration**, random-valid escolhe uniformemente dentro da máscara com RNG da policy, fit usa demandas públicas. FCFS estrito incompatível em A permanece fora de B* principal. Nenhum modelo tem acesso a duração real, futuras chegadas, trace_hash, split, seed exógena, metrics evaluator ou estimadores calibrados em TEST.

Os geradores de chegada, duração, recursos, estimativas e policy RNG usam streams derivados por hash criptográfico estável de namespace/split/scenario/replicate/stream, sem `hash()` do Python; geração completa antes da execução. Validação e TEST têm seeds/famílias reservadas e manifests distintos. Mesmo workload exógeno e mesmo protocolo de segurança para todas as policies. Versões dos contratos acompanham checkpoint serializado; nenhuma desserialização executa código arbitrário.

## 7. Plano de verificação (não executado nesta missão documental)

| Classe | Casos de aceite / oráculo | Evidência exigida na implementação |
| --- | --- | --- |
| Positivos | Golden A/B/C; duas dimensões de recursos; admissões consecutivas no mesmo tick; FULL DRAIN antes do budget; COMPLETE em H_e incluído | Event trace determinístico, métricas calculadas à mão, logs/hashes |
| Negativos | ID duplicado, requisito zero/negativo/acima capacidade, estimate/actual inválidos, chegada negativa, clock regressivo, START duplo, double-release, RUNNING como READY, máscara desatualizada, WAIT proibido, unknown ID, NaN/Inf no scorer, job chegando exatamente em H_a, START em H_e, stall/timeout | Rejeição sem mutação parcial, motivo e outcomes explícitos |
| Propriedades | Conservação por recurso após **toda** transição, 0<=allocated<=capacity; relógio monotônico; início>=chegada; conclusão=início+actual; monotonicidade do conjunto COMPLETED; READY count decresce em cada START no mesmo t | Property-based/geração determinística + contraexemplos minimizados/seeds |
| Reproducibilidade | Ordem de inserção/permutação de jobs com IDs fixos; replay de seed/config/version gera eventos e hash iguais; policy RNG draws extras não alteram trace exógeno; ordem de comparação de policies não altera workloads | Hash estável, manifests e snapshots |
| Não vazamento | Mudar apenas `actual_duration`/futuros/RNG privado mantendo observação pública fixa não muda projection/mask/decisão inicial; refletir alteração em duração posterior **somente** via eventos públicos; não passar IDs como feature neural | Testes de noninterference no projector, adapter, tie-break e normalization |
| Equivariância | `scores(πX)=πscores(X)`, ação por ID invariável em permutação; N=0/1/K/K+1/N grande; candidato ilegal com escore máximo nunca é selecionado | Propriedades de scorer/mask e stress de filas |
| Avaliação | Sem job omitido em cutoff; denominator fixado na coorte; falhas não têm média completa; TRAIN/VAL/TEST isolados; intervalos sobre unidades independentes, não cada job/decisão | Fixtures de métricas e manifests por split |

Os oráculos e propriedades validam **corretude do simulador**, não utilidade do scheduler nem aprendizado. CI de main/#21 falhou antes de causa diagnóstica estabelecida: falha operacional externa deve ser reportada separada de qualquer regressão específica.

## 8. Implementação incremental dependente de gates (não executar agora)

| Sequência | Issues | Entrega mínima, condição de entrada e saída |
| --- | --- | --- |
| Gate científico | [#2](https://github.com/Gyliardson/genesis/issues/2), [#3](https://github.com/Gyliardson/genesis/issues/3), [#4](https://github.com/Gyliardson/genesis/issues/4) | Resolver WAIT/FCFS, cutoff, erro, fairness/fitness provisória e findings PR #21; localizar primeira causa CI; registrar decisão revisada sem falsificar evidência |
| 1 — Sim core | [#5](https://github.com/Gyliardson/genesis/issues/5) | Domain states/atomic reservation/event ordering, goldens A/B/C e propriedades de capacidade; SimPy vs DES ainda OPEN até benchmark isomórfico |
| 2 — Workloads | [#6](https://github.com/Gyliardson/genesis/issues/6) | Generator exógeno/streams/versioned manifest; requer #3 e interface/core #5; testes noninterference |
| 3 — Heurísticas | [#7](https://github.com/Gyliardson/genesis/issues/7) | FCFS-scanning, estimated-SJF, random-valid, fit; requer #3/#5/#6, todas mesmo protocolo, sem truth leakage |
| 4 — Evaluation | [#8](https://github.com/Gyliardson/genesis/issues/8) | Métricas e failure accounting, replay pareado, CI/profiling e confronto de simuladores; depende #5/#6/#7. **Primeiro experimento válido** = golden tests + baselines em traces idênticos e DRAIN confiável, ainda sem rede |
| 5 — Neural | [#9](https://github.com/Gyliardson/genesis/issues/9) | Policy com N variável, mask, random weights, permutation/leakage tests; depende #3/#5/#8 e interface #7 |
| 6 — Evolution | [#10](https://github.com/Gyliardson/genesis/issues/10) | GA pequeno versus random search, budgets/seeds e custo; depende #2/#8/#9, **não** treinar usando TEST |
| 7 — Export/reload | [#11](https://github.com/Gyliardson/genesis/issues/11) | Checkpoint versionado/normalização + replay e rejeição de incompatibilidades; depende #9/#10 |
| 8 — EXP-001 | [#12](https://github.com/Gyliardson/genesis/issues/12) | VAL escolhe B*, TEST reservado, variação de seeds/shift, IC pareado/limites/custos; depende #7/#8/#10/#11 e regras congeladas; [#19](https://github.com/Gyliardson/genesis/issues/19) é comparação evolutiva **posterior** |

**Próximo gate antes de ratificação:** revisão independente do PR #21 no exact-head, decisão explícita #3 para D-017 e cenários de WAIT, acordo de #2 sobre fitness/fairness e verificação de oráculos/cutoffs. Sem isso, somente propostas de documentação podem avançar. Toda arquitetura pode ser revisada conforme evidência; alteração material de action/observation/horizon exige schema version novo e repetição dos benchmarks afetados.

## 9. Limites e segurança

Nenhum simulador foi construído nem benchmark executado nesta missão. Simulador correto != policy útil; policy legal != policy generalizável; evolução entre gerações != aprendizagem/plasticidade durante a vida; controladora transferível não é controladora validada em workloads reais. Execução física é futuro com isolamento, shadow mode, quotas, fallback, audit e rollback; nenhuma policy pode emitir shell ou alterar limites. Os tradeoffs e status constam em [Decision Log](decisions.md); evidência atual é pesquisa/propostas, não desempenho empírico do GENESIS.
