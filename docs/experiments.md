# Caderno de experimentos — plano inicial

> **Nenhum resultado experimental existe ainda.** Todo número de exemplo abaixo é proposta de protocolo, não métrica observada.

## EXP-001 — Neuroevolução para admissão/seleção de jobs

### Pergunta

Uma política neural evoluída consegue igualar ou superar métodos clássicos de scheduling em cargas heterogêneas **não vistas**, sem usar regras por cenário?

### Hipóteses refutáveis — hierarquia única

A **única H0/H1 confirmatória** de EXP-001 é definida operacionalmente na subseção "Estimando, hipótese nula e refutação" abaixo. A ideia anterior de "vantagens em subconjuntos específicos" passa a **H2 exploratória** (heterogeneidade de efeito por famílias de workloads); "diversidade de ambientes no treinamento melhora generalização" passa a **H3 exploratória/posterior**. Nenhuma descoberta *post hoc* de subgrupo rejeita H0. Para qualquer teste confirmatório adicional de H2/H3, pré-registrar estratos, direções e ajuste de multiplicidade antes de abrir TEST. A pergunta "igualar" é descritiva/não inferioridade e não se confunde com demonstrar superioridade prática.

### Ambiente mínimo proposto

- Um nó com `cpu_units`, `memory_units` e jobs independentes não preemptivos.
- Chegadas dinâmicas; durações reais geradas pelo simulador, estimativas ruidosas disponíveis às policies.
- Ações em **ActionA_v0 ACCEPTED**: START obrigatório quando há elegível; avanço forçado pelo ambiente quando nenhum cabe. WAIT voluntário é apenas hipótese futura **ActionB_v1 DEFERRED**, fora da comparação confirmatória.
- Eventos relevantes: chegada de job, conclusão, desbloqueio de recursos e decisão.

### Baselines obrigatórias

- FCFS-scanning (*first eligible fit*) sob **ActionA_v0 / D-017 ACCEPTED (2026-11-04)**, sem WAIT voluntário; FCFS estrito head-of-line é somente diagnóstico externo, nunca candidato a B* neste protocolo.
- SJF baseado **na duração estimada observável**, nunca no valor verdadeiro oculto.
- Heurística de encaixe de recursos (best-fit ou similar), se compatível com a semântica do ambiente.
- Política aleatória **sobre ações válidas**.
- Controle neural não treinado, para separar contribuição da arquitetura versus treinamento.

### Métodos em comparação (planejados)

1. MLP com pesos evoluídos por mutação/seleção.
2. Futuro: NEAT ou algoritmo alternativo após microbenchmark.
3. Futuro: RL com Gymnasium/SB3, caso o espaço de ações seja representável sem distorção grave.

### Métricas

- Job completion/sojourn time: média, mediana e p95.
- Waiting time e p95 de espera; starvation e fração não atendida.
- Throughput; makespan em janelas fechadas quando apropriado.
- Utilização média e por recurso; idle com fila elegível.
- Custo do controlador por decisão e custo de treinamento.
- Distribuição de resultados por cenário/seed, com intervalos de incerteza.

**Fitness de treinamento:** requer pesquisa e decisão explícita; não usar número de jobs concluídos isoladamente nem alegar otimização multiobjetivo se só houver um escalar arbitrário.

### Desenho experimental

- Cenários gerados por seeds fixas e versionadas.
- Partições independentes: treino, validação e teste, inclusive distribuição deslocada.
- Comparar políticas **no mesmo conjunto de cenários por seed** (common random numbers) para reduzir variância.
- Rodar diversas seeds de treinamento e testes independentes, não escolher e divulgar só a melhor execução.
- Estabelecer orçamento comparável entre métodos e separar seleção de hiperparâmetros de avaliação final.
- Publicar configuração, commit, versões, duração, dados e limitações; preservar resultados negativos.

### Critério de conclusão EXP-001

- Um único comando reproduz benchmarks das baselines e de um controlador evoluído carregado de checkpoint.
- Tabelas por cenário e resultados agregados; gráficos opcionais.
- Comparação com holdout e conclusão modesta, inclusive quando o método evolutivo perde.


### EXP-001 — protocolo pré-registrável proposto por RESEARCH-01

**EVIDENCE:** nenhum experimento foi executado nem existem resultados GENESIS. As definições abaixo são **PROPOSAL** até a síntese e aceitação das decisões OPEN.

#### Estimando, hipótese nula e refutação (F02/F03/F05; proposta alinhada a D-025 OPEN)

Para cada job da coorte completa: sojourn T_j = f_j - a_j, espera W_j = s_j - a_j; **N_{s,i} >= 1 denota a coorte-alvo factível congelada ex ante** no cenário (s,i): jobs com `0 <= arrival < H_a` e requisitos compatíveis com recursos. Contar separadamente `REJECTED_INFEASIBLE`, especificações inválidas e todas as células planejadas; um trace TEST que viole o protocolo de geração invalida o teste, sem excluir/redefinir jobs ou cenários depois de observar resultados. N_{s,i} não significa jobs concluídos nem todas as chegadas indiscriminadamente. Pré-registrar S famílias/estratos-alvo, seus manifestos TEST de cenários exógenos independentes i=1..n_s e pesos w_s = 1/S (**candidato explícito**: igual peso por família, independentemente de n_s/N_i; alternativa requer decisão ANTES de TEST). O cenário é a unidade amostral de workloads; treino da policy A gera K **seeds de treinamento independentes**, todas avaliadas em todos os mesmos cenários, sem escolher o melhor indivíduo/seed pelo TEST. Baselines determinísticas compartilham cada trace; baselines estocásticas têm replicações/seeds independentes pré-registradas e agregação congelada em VAL.

**Estimando candidato R_geo, não pooled ratio (D-025 OPEN; definição PROPOSTA sujeita a #2/#8):** planejar K seeds independentes de treinamento e E seeds de avaliação/policy RNG por cenário. E=1 somente se ambos os braços forem determinísticos dado o trace; usar E>1 quando A ou B* for estocástica. Definir m_A(s,i,k,e) = (1/N_{s,i}) Σ_{j∈coorte(s,i)} T_A,j e m_B*(s,i,e) = (1/N_{s,i}) Σ_{j∈coorte(s,i)} T_B*,j, exigindo a coorte inteira encerrada em ambos os braços. Definir l(s,i,k,e) = log[m_A(s,i,k,e)/m_B*(s,i,e)] e theta = Σ_s w_s (1/n_s) Σ_i (1/K) Σ_k (1/E) Σ_e l(s,i,k,e), com **R_geo = exp(theta)**. O mesmo denominador B*(s,i,e) é compartilhado entre todos os k; manter a dependência no IC. A realização estocástica de B* não pode ser substituída por um denominador pontual arbitrário. As médias por coorte entram apenas antes do log; não fazer pooling de jobs, média aritmética das razões ou razão de médias agregadas. O estimando é a expectativa geométrica das **razões pareadas dos tempos médios por cenário**, com pesos fixos e média sobre variação de treinamento; sojourn e horas simuladas positivos são pré-requisitos. Tamanho de cada estrato, w_s, K e elegibilidade da coorte deverão ser congelados no pré-registro.

**Seleção de B* em VAL, nunca em TEST:** construir a lista de baselines clássicas **legais sob o MESMO protocolo de ações**; ajustar hiperparâmetros/limites de custo somente em TRAIN/VAL, com orçamento declarado. No conjunto VAL independente, descartar candidatos com falha de factibilidade/ação, stall, timeout ou violação de constraints de fairness/custo pré-fixadas; entre viáveis selecionar menor valor de Σ_s w_s média_i(log m_B(s,i)) no VAL (mesmos w_s da competição). Em empate numérico sob tolerância pré-fixada, usar ordem de prioridades congelada (e.g. FCFS-scanning → estimated-HRRN → SEJF → resource-fit); se nenhum candidato for viável, **não abrir TEST** e revisar protocolo. Congelar baseline, versão, hiperparâmetros, tie-break, máscara, seeds e fallback. Reportar **todas** as baselines legais também no TEST como análise descritiva, sem escolher uma nova B* ou um segundo vencedor pelo resultado final. Budget de treinamento do método neural e custo das heurísticas são registrados e guardrails operacionais são aplicadas à seleção.

**Inferência cruzada/pareada (PROPOSTA, D-025 OPEN):** reamostrar cenários inteiros i dentro de cada estrato e, em eixo cruzado, seeds independentes de treino k (mesma seed reamostrada em todos os cenários); preservar os pares de cenário e seed e de avaliação entre A/B*, e o mesmo denominador B*(s,i,e) entre k. Qualquer reamostragem adicional do eixo E deve respeitar o desenho de seeds independentes/pareadas e blocos compartilhados; células (i,k,e) e jobs não são iid. Calcular theta e R_geo em cada repetição; IC/limite superior unilateral para R_geo **sem tratar jobs como amostras independentes**. Selecionar método/bootstrap, número de replicações e nível de confiança antes de TEST; propor 95% family-wise em conjunto com os guardrails via Bonferroni: alpha_total=0,05, alpha_each=0,05/(1+G) para objetivo e G guardrails quantitativos pré-registrados (ou método simultâneo equivalente ratificado antes de TEST). Para guardrail g, declarar orientações, denominadores, margem operacional epsilon_g e exigir limite superior unilateral ajustado da diferença/razão de degradação abaixo da margem. Para action safety, stall e timeout, requerer contagem zero nas execuções confirmatórias, sem inferir "ausência de risco" fora das amostras. Eventual análise de famílias OOD e múltiplas políticas/hipóteses confirmatórias exige correção extra previamente fixada; caso contrário é exploratória. Esta proposta de IC é sensível a n_s e K pequenos; piloto de power/cobertura em VAL define orçamento.

- **H0 confirmatória:** R_geo >= 1 - delta **OU** pelo menos um guardrail especificado falha, ou há cenário TEST não concluído (TIMEOUT, POLICY_STALL, ERROR, censura) em qualquer braço necessário para comparação. Delta é efeito mínimo material a decidir por utilidade operacional ANTES de TEST (5% é exemplo **não ratificado**).
- **H1 confirmatória:** limite superior unilateral ajustado de R_geo < 1 - delta, todos os cenários TEST do protocolo primário completos em ambos os braços, nenhuma violação das guardrails, custos inferência/treino publicados e nenhuma seleção de H1 por subgrupo após TEST. A alegação se restringe às famílias e pesos do pré-registro.
- **Regra de refutação:** ganho insuficiente, IC cruzando margem, violação de guardrail, erro/simulação inválida, leakage ou censura impedem H1; não rejeitar H0 não implica equivalência e não valida uso real. Falhas são contabilizadas, **não censuradas seletivamente** para obter um estimando favorável.
- **H2/H3 exploratórias:** interações com rajadas, mistura de recursos, erro da estimativa e diversidade de treino exigem estratificação, ablações e multiplicidade separadas. Não substituem H1 global nem constituem resultado do presente trabalho.

**Controles negativos bem definidos:** (a) trajetória única: em protocolo A work-conserving, sem WAIT voluntário, há exatamente uma ação START legal em toda decisão alcançável, com mesmos eventos e desempates determinísticos; esperar **mesmo log de decisões e métricas de scheduling** para policies determinísticas, descontado overhead de computação; (b) jobs indistinguíveis **apenas quando** trocas de ordem deixam demandas, chegadas e durações observáveis/verdadeiras simetricamente equivalentes e desempates são canônicos, permitindo equivalência de métricas mesmo se IDs escolhidos diferirem. "Fila unitária", "baixa contenção" e "homogeneidade" isoladas NÃO garantem trajetória idêntica se WAIT voluntário é legal ou chegadas/durações são distintas. Em protocolo B com WAIT, controles negativos validam invariantes de segurança, e a qualidade/ociosidade pode diferir legitimamente. Se o ambiente não possui trajetória determinística única, nenhuma divergência observada é chamada de bug automaticamente. Regimes discriminativos: rajadas, durações bimodais/heavy-tail, CPU-heavy/memory-heavy, estimativas enviesadas, distribuição deslocada e pressão de memória com CPU livre.

#### Dinâmica e fronteira de informação

Um nó, jobs independentes e não preemptivos com requisitos inteiros 0 < cpu_j <= C_cpu e 0 < mem_j <= C_mem; duração verdadeira positiva e estimativa positiva produzidas ex ante. Cada job reserva recursos de START até conclusão; concorrência é permitida se **ambos** os limites forem respeitados. Jobs inviáveis devem ser rejeitados na geração ou categorizados explicitamente; não ficar eternamente na fila invisível. Para comparação pareada, pré-gerar o MESMO trace exógeno (chegadas, demandas, durações verdadeiras e estimativas) para todas as policies. Nenhuma policy pode acessar próximos eventos, duração verdadeira, seed de cenário/split ou duração restante real dos jobs em execução.

Decisões propostas por evento, após processar em ordem canônica todas as conclusões e chegadas no timestamp atual; permitir admissões consecutivas no mesmo instante enquanto houver candidato legal. A ordem final pertence à síntese com RESEARCH-02. WAIT forçado quando não existe elegível difere de WAIT voluntário com elegíveis. Este último somente se aprovado, com avanço de tempo controlado pelo motor até evento exógeno e proibições de laço zero, starvation e WAIT sem evento futuro; o scheduler não enxerga timestamp do evento. O custo de inferência deve ser medido separadamente do relógio simulado e eventualmente contabilizado no objetivo prático.

#### Baselines legais e controles (F01/F07; D-017 ACCEPTED em 2026-11-04)

**ActionA_v0 / Protocolo A — ACCEPTED (D-017, 2026-11-04):** quando existe pelo menos um job elegível, a máscara permite somente START(job_id) elegível e exige uma admissão; se nenhum cabe, o **ambiente** faz avanço forçado até evento exógeno/terminação, sem expor futuro à policy. Nesse protocolo, a baseline clássica FCFS competitiva é **FCFS-scanning = first eligible fit por ordem de chegada/ID**, que percorre READY e admite o primeiro que cabe. Não há reserva para proteger o head, portanto **NÃO** é EASY/conservative backfilling. Pode preterir head repetidamente e sofrer starvation. D-017 **ACCEPTED** conforme [ratificação na Issue #3](https://github.com/Gyliardson/genesis/issues/3#issuecomment-6640438542).

**FCFS estrito/head-of-line**: deliberadamente não inicia um job posterior quando o primeiro da fila não cabe. Por exemplo, head pede CPU=2 e CPU livre=1, enquanto um job posterior pede CPU=1 e é elegível: FCFS estrito precisa esperar; START-only tornaria essa ação ilegal. **Classificar apenas como diagnóstico fora de B* no protocolo A**, não como baseline competitiva equivalente. **ActionB_v1 / Protocolo B DEFERRED**, se futuramente ratificado: WAIT voluntário com bounded idle para TODAS as policies, incluindo FCFS estrito, mesma máscara, limites de progresso, fallback, fairness, custos e orçamento; selecionar B* **dentro** de B, nunca combinar A e B na mesma comparação confirmatória. Comparar A versus B só como estudo separado, não uma competição com ações distintas. Oráculo HOL e caso WAIT no último evento são testes de aceitação futuros da Issue #3, ainda NOT_RUN.

| Policy | Dados observáveis necessários | Papel em ActionA_v0 / falha | Complexidade de seleção (sem overhead compartilhado) |
| --- | --- | --- | --- |
| FCFS-scanning (*first eligible fit*) | chegada/ID e máscara/recursos | baseline competitiva; possível starvation de head | O(n) |
| Shortest **Estimated** Job First (SEJF) | estimated_duration e máscara | competitiva; viés de duração e starvation | O(n) argmin; ordenação total O(n log n) |
| CPU/mem first-fit / best-fit | demandas, capacidade/máscara | competitiva; exige score normalizado explícito | O(n) |
| Estimated-HRRN / aging | age, estimated_duration e máscara | competitiva; erro de estimativa e envelhecimento | O(n) |
| Random-valid / neural sem treino | observação/máscara idêntica à aprendida | controles fracos/ablação, não "melhor heurística" | O(n) + modelo |
| FCFS estrito head-of-line | ordem de chegada/ID e recursos | **somente diagnóstico separado no A**; elegibilidade distinta | O(1) escolha do head, não custo E2E |

**Proibições:** oracle com actual_duration/chegadas futuras, SRPT preemptivo, regras de DAG não disponíveis. Todas as políticas competitivas veem informações permitidas equivalentes e seguem os mesmos safety/fallback e mesmo trace. B* é escolhida em VAL, não após TEST.

**Overhead mensurado end-to-end:** além da complexidade de score/argmin acima, cronometrar por decisão *observation materialization + máscara/feasibility + normalização + inferência/ranking + validação safety/fallback + serialização/log*. Reportar p50/p95, tempo total por episódio, chamadas por job, CPU/RAM e custo total de treino e avaliação por hardware/versão fixos; amortização por throughput, frequência e tamanho de fila. A construção compartilhada de máscara pode custar O(n) até no head O(1). Contabilizar WAIT, ações ilegais e custos de fallback; não usar tempo simulado como custo real de decisão.

#### Métricas, terminal states e censura (F04; alinhamento D-020 OPEN)

| Métrica | Definição e denominador | Risco |
| --- | --- | --- |
| Sojourn mean/median/p95 | f_j - a_j da **coorte completa** só após drain bem-sucedido | completados isolados têm viés se houver inconclusos |
| Waiting mean/p95 | s_j - a_j de iniciados; também contar os **nunca iniciados**, com idade | survivor bias de waiting em jobs longos |
| Throughput | conclusões / janela física ou simulada pré-fixada | pode crescer deixando backlog longo |
| Makespan | max(f_j) - min(a_j), apenas coorte fechada/drenada | indefinido para streaming aberto |
| Utilização CPU/mem | integral de reservas/(capacidade × tempo observado) por recurso | reserva não equivale a trabalho útil |
| Starvation/fairness | max idade, fração acima de limiar, p95 por classe e slowdown offline | limiares/classes devem ser predefinidos |
| Overhead | caminho E2E completo por decisão, p50/p95, total, CPU/RAM/treino | argmin O(1) não é custo total |

**Cohort/time boundary PROPOSTA:** 0 ≤ H_a ≤ H_e, chegadas na janela **[0,H_a)**; chegada em t=H_a não ingressa. Evento COMPLETE em t=H_e conta como concluído; START só em t<H_e (sem START novo exatamente em H_e). Para experimento de *coorte fechada com drain* interromper novas chegadas em H_a e continuar servindo sua coorte sob o MESMO budget de drenagem em tempo simulado/decisões pré-fixado (e hardware/performance limits auditáveis), com cutoffs idênticos para todas as políticas. O horizonte H_e é referência para fixed-H e observação de censura; se o protocolo de drain admitir execução além de H_e, seu limite H_d e regra de START após H_e devem ser **definidos separadamente e ratificados antes do teste**, não inferidos da regra fixed-H. Não tratar dois modos como a mesma janela.

**Estados terminais mutuamente distinguíveis por episódio:** COMPLETED (toda coorte terminou sob budget); TIMEOUT (budget global ou de drain consumido, jobs remanescentes); POLICY_STALL (nenhuma progressão/decisão legal, incluindo WAIT no último evento); ERROR/INVALID_ACTION (rejeição safety, sem mutação parcial); CENSORED/UNFINISHED como **estado por job**, com READY, RUNNING, rejeição por spec inviável e motivo separados. Política de fallback para invalid actions e classificação de erro seguem D-021 OPEN; jamais transformar falha em conclusão sintética. Registrar transições sem duplicar job em READY/RUNNING/COMPLETED e com reservas liberadas somente em conclusão.

**Regra confirmatória sem exclusão seletiva:** congelar denominador como **todos os pares TEST previstos** (família, cenário/trace, seed de treino e baseline). Registrar completed, started, never-started, pending READY/RUNNING e todas as falhas por braço e motivo. Um par com TIMEOUT, POLICY_STALL, ERROR ou qualquer job inconcluso em **qualquer braço necessário** **não pode entrar seletivamente no cálculo de R_geo nem sustentar H1**: o gate confirmatório global é NOT_MET, mesmo se uma tabela *condicional* de pares completos sugerir ganho. Nunca substituir por zero, infinito arbitrário, remover o par ou recalcular pesos w_s com a amostra concluída. Se B* falha e não há baseline válida, resultado é **INCONCLUSIVE/PROTOCOL_FAILURE**, não "aprendido venceu". Relatar número/percentual de pares falhos (por família, política, seed) e manter trace manifest completo. Sensibilidades (bounds, penalidades pré-registradas, survival) são secundárias, não resgatam H1.

**Lower bounds de censura:** para um job que já chegou até o tempo de parada observado t_stop, T_j ≥ t_stop - a_j; não calcular com H_e quando o episódio terminou antecipadamente em t_stop<H_e, nem para job de chegada posterior a t_stop. Em fixed-H, apenas a_j < H_a e a_j ≤ H_e com chegada efetivada pertencem à coorte. Reportar também backlog de recursos e idade na parada; censura pode ser informativa e induzida pela política, logo Kaplan–Meier ou médias de completados não recuperam a primária sem hipóteses extras. TIMEOUT/stall deve permanecer no denominador da análise confirmatória, como falha explícita.

#### Desenho pareado, inferência e segurança científica

Separar **TRAIN/VAL/TEST-ID/TEST-OOD** por seeds e, em traces externos, por tempo/origem; a seleção de modelos, de B*, de margens, estratos, pesos, guardrails, tolerância de desempate, método de bootstrap cruzado e regra de término usa apenas TRAIN/VAL/piloto de power. Usar common random numbers e traces exógenos iguais por cenário para políticas comparadas, e seeds de treinamento independentes sem selecionar a melhor. Nunca ajustar parâmetros ou hipótese após abrir TEST. Dimensionar n_s e K por piloto de validação, não por resultados finais; publicar todos os métodos, inclusive comparadores perdedores, ICs, tamanho de efeito, cenários falhos, fração da coorte atendida e custos. O orçamento inicial de 5 seeds de treino/dezenas de cenários por estrato é apenas exemplo exploratório, não decisão.

**Observabilidade F09 / noninterference (PROPOSAL, NOT_RUN):** snapshot público imutável e versionado, IDs somente para mapeamento/desempate externo, timestamp lógico canônico e histórico agregado explicitamente aprovado; dois truth states com idêntica Observation e mesmo estado público/privado permitido da Policy devem induzir a mesma distribuição de ações, sem consumo de RNG oculto. Testar alteração de actual_duration/futuro/split sem afetar projeção, e permutações da fila com saída por ID invariante sob empate canônico. Contratos e testes exigem #3/#5/#9; nenhuma propriedade de implementação foi provada.

**Reward hacking e regressão:** otimizar throughput isoladamente, manter jobs longos na fila, empurrar conclusões além do horizonte, usar IDs/seed/futuro como proxy, explorar máscaras, liberar memória cedo ou emitir WAIT infinito podem inflar fitness. Especificar guardrails antes de treinar e testar manualmente: recursos CPU livres mas memória insuficiente; simultâneos; estimativas subestimadas; jobs longos; ações ilegais; WAIT no último evento; fila única; invariantes de conservação, monotonicidade e ausência de execução duplicada. Fitness escalar, penalties, política de rejeição e fairness são **DECISION REQUIRED**.

#### Contratos observáveis para #3 (PROPOSAL; não ADR)

- **Job:** id público estável, arrival_time, cpu_units, memory_units, estimated_duration, timestamps e estado. actual_duration permanece **somente na verdade do simulador e avaliação**.
- **Observation:** current_time, capacidade total/livre de CPU e memória, jobs chegados/esperando com campos públicos, waiting age, histórico permitido e eligible_job_ids; wait_allowed explícito; sem futuro, seeds, split labels, duração verdadeira ou próximo término.
- **Action:** START(job_id) de job elegível ou WAIT estritamente legal, com máscara e comportamento para ação inválida/fallback definidos antes da execução. Nenhuma preempção, mudança de quota ou shell.
- **Policy:** reset(policy_seed, public_config), decide(observation) -> Action, serialização opcional com versão, estado interno privado e determinismo configurado; acesso somente à interface, não ao estado real do simulador.

**STATUS NORMATIVO (2026-11-04):** D-017/ActionA_v0 **ACCEPTED**; ActionB_v1 **DEFERRED**. **DECISION REQUIRED:** D-018 (detalhes de eventos), D-020 (cutoff/drain), D-021 (invalid action/fallback) e D-025/D-010 (R_geo, margens, custos e fairness) permanecem OPEN/PROPOSED e dependem de ratificação própria em #2/#8 quando aplicável.  RESEARCH-02 valida time/event/WAIT, censoring e simulador; RESEARCH-03 pesquisa entrada de fila variável, algoritmo e orçamento; somente então formalizar contratos/função de fitness no ADR. EXP-001 não fornece evidência de generalização, validação física ou novidade científica antes de dados reais.

## EXP-002 — Generalização (posterior)

Avaliar políticas treinadas sob rajadas, durações longas/curtas, recursos escassos e estimativas imperfeitas em distribuições deslocadas e capacidade diferente. Não assumir capacidade de generalizar a topologias distribuídas sem treinamento específico.

## EXP-003 — Adaptação online (posterior)

Comparar política fixa versus política com plasticidade/aprendizagem online sob mudança de distribuição, controlando custo e estabilidade. Definir critérios de segurança para impedir que adaptações degradantes entrem na execução real.

## EXP-004 — Ablação (posterior)

Remover observações selecionadas, desligar mecanismo de memória/plasticidade, alterar capacidade da rede e medir efeito, com controle de parâmetros e sementes.

## Conclusões científicas: checklist

- [ ] A hipótese e os testes foram descritos **antes** de avaliar o teste final.
- [ ] As baselines tiveram acesso às mesmas informações permitidas.
- [ ] O simulador foi validado por testes de invariantes e cenários calculáveis à mão.
- [ ] Foram reportados casos em que o método **não** funciona.
- [ ] Não foi atribuída consciência, intenção ou causalidade a partir de padrões visuais.
