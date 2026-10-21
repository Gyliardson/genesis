# Caderno de experimentos — plano inicial

> **Nenhum resultado experimental existe ainda.** Todo número de exemplo abaixo é proposta de protocolo, não métrica observada.

## EXP-001 — Neuroevolução para admissão/seleção de jobs

### Pergunta

Uma política neural evoluída consegue igualar ou superar métodos clássicos de scheduling em cargas heterogêneas **não vistas**, sem usar regras por cenário?

### Hipóteses refutáveis

- **H0:** políticas evoluídas não apresentam ganho robusto sobre a melhor baseline nas condições testadas, ou o custo computacional anula possíveis ganhos.
- **H1:** há vantagens em subconjuntos específicos de condições; precisamos identificar **quais**, **quanto** e **a que custo**.
- **H2 (posterior):** diversidade de ambientes durante o treinamento melhora generalização em relação a treinamento em distribuição única.

### Ambiente mínimo proposto

- Um nó com `cpu_units`, `memory_units` e jobs independentes não preemptivos.
- Chegadas dinâmicas; durações reais geradas pelo simulador, estimativas ruidosas disponíveis às policies.
- Ações: admitir um job elegível ou aguardar (se permitido); máscaras e desempates determinísticos.
- Eventos relevantes: chegada de job, conclusão, desbloqueio de recursos e decisão.

### Baselines obrigatórias

- FIFO/FCFS.
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

#### Estimando, hipótese nula e refutação

Para cada job completado: sojourn T_j = f_j - a_j, espera W_j = s_j - a_j, duração verdadeira d_j = f_j - s_j. Considere B* a **melhor baseline válida escolhida apenas no conjunto de validação**, congelando hiperparâmetros e desempates antes do teste. A métrica principal proposta, em cenários fechados e drenados, é R = média_de_sojourn(adaptativa) / média_de_sojourn(B*), medida em execuções pareadas pelo mesmo workload. Definir antecipadamente uma diferença mínima relevante delta (sugestão **não aceita**: 5%), limites de regressão p95, starvation, fairness e custo por decisão.

- **H0 principal:** R >= 1 - delta, ou há violação de qualquer guardrail pré-registrada. Não há vantagem robusta e operacionalmente relevante sobre B* na família-alvo de workloads não vistos.
- **H1 principal:** R < 1 - delta com limite superior do intervalo de confiança pareado abaixo de 1 - delta, sem violação de guardrails e com custos de treino/inferência reportados. A alegação se restringe às distribuições pré-registradas; melhoria em um subgrupo exploratório não confirma H1 geral.
- **Refutação de H1:** IC toca limiar, efeito perde-se no holdout/shift, custo anula o ganho, estimativas verdadeiras vazam, há aumento relevante de censura/starvation ou violação de capacidade. Não rejeitar H0 NÃO comprova equivalência: testar equivalência requer margem própria e poder adequado.
- **Hipóteses secundárias:** melhora pode concentrar-se em burstiness, mistura de jobs curtos/longos, demandas CPU/mem complementares e erros de estimativa; treinar em várias distribuições pode melhorar robustez em shift. Exigem análise própria, sem escolher post hoc subgrupos vencedores.

**Controles negativos (declarados antes do treino):** fila com um único elegível; ausência de competição; jobs homogêneos sem diferença de recursos/tempo; sequências em que só há uma ação factível. Se as policies têm mesma trajetória, deve haver mesmas métricas dentro da tolerância numérica (sem custo de decisão); qualquer suposto ganho operacional aqui exige investigar bug. Controles discriminativos: chegadas em rajadas versus Poisson, durações bimodais/heavy-tail, CPU-heavy versus memory-heavy, carga estável baixa/média/alta, estimativa precisa versus ruidosa, subestimação versus superestimação e distribuição deslocada.

#### Dinâmica e fronteira de informação

Um nó, jobs independentes e não preemptivos com requisitos inteiros 0 < cpu_j <= C_cpu e 0 < mem_j <= C_mem; duração verdadeira positiva e estimativa positiva produzidas ex ante. Cada job reserva recursos de START até conclusão; concorrência é permitida se **ambos** os limites forem respeitados. Jobs inviáveis devem ser rejeitados na geração ou categorizados explicitamente; não ficar eternamente na fila invisível. Para comparação pareada, pré-gerar o MESMO trace exógeno (chegadas, demandas, durações verdadeiras e estimativas) para todas as policies. Nenhuma policy pode acessar próximos eventos, duração verdadeira, seed de cenário/split ou duração restante real dos jobs em execução.

Decisões propostas por evento, após processar em ordem canônica todas as conclusões e chegadas no timestamp atual; permitir admissões consecutivas no mesmo instante enquanto houver candidato legal. A ordem final pertence à síntese com RESEARCH-02. WAIT forçado quando não existe elegível difere de WAIT voluntário com elegíveis. Este último somente se aprovado, com avanço de tempo controlado pelo motor até evento exógeno e proibições de laço zero, starvation e WAIT sem evento futuro; o scheduler não enxerga timestamp do evento. O custo de inferência deve ser medido separadamente do relógio simulado e eventualmente contabilizado no objetivo prático.

#### Baselines legais e controles

| Policy | Regra e informação permitida | Limitação | Custo típico por decisão |
| --- | --- | --- | --- |
| FCFS head-of-line | primeira chegada/id, requisitos e capacidade | bloqueio por cabeça de fila | O(1) se acesso ao head |
| FCFS com scanning/backfill | primeiro job que cabe mantendo ordenação pública | preterição possível do head | O(n) |
| Shortest **Estimated** Job First | menor estimativa de duração entre jobs que cabem | erro de estimativa, long-job starvation | O(n), ou ordenação O(n log n) |
| First-fit / best-fit recursos | escolher entre elegíveis pelo encaixe CPU/mem com score fixado na validação | ignora duração, pode enviesar classes | O(n) |
| Estimated-HRRN/aging | maior (waiting + estimated_duration)/estimated_duration entre elegíveis | estimativa ruim distorce prioridade | O(n) |
| Random-valid / neural untrained | máscara e observação idênticas à policy aprendida | controle fraco; só testa chance/efeito do treino | O(n) + custo do modelo |

**Exclusões:** SJF-oracle baseado em duração verdadeira, SRPT e outras regras preemptivas, oráculo com futuro conhecido, algoritmos de cluster/DAG que exigem ações ou dados inexistentes. Um oracle pode servir só de bound diagnóstico explicitamente rotulado. Todos recebem **a mesma informação disponível** e máscaras; heurísticas podem ignorar atributos. As decisões de WAIT, desempates, inválidas e fallback precisam ser idênticas entre métodos. Selecionar B* e hiperparâmetros exclusivamente na validação, sem escolher a baseline vencedora olhando o teste.

#### Métricas e censura

| Métrica | Definição | Armadilha |
| --- | --- | --- |
| Sojourn mean/median/p95 | f_j - a_j nos jobs completos de uma coorte | excluir incompletos favorece a policy que os atrasa |
| Waiting mean/p95 | s_j - a_j nos iniciados; idade dos ainda esperando separada | a censura de não iniciados cria viés |
| Throughput | quantidade concluída / janela de tempo definida | completar jobs curtos pode esconder backlog |
| Makespan | max(f_j)-min(a_j), **só** em batch fechado e drenado | não comparar makespan isolado em tráfego contínuo |
| Utilização CPU/mem | integral de reservas / (capacidade * horizonte) por recurso | reserva não mede eficiência de trabalho, uso alto pode ser ruim |
| Starvation | fração não iniciada além do limiar, máximo waiting age, jobs pendentes | limite deve ser fixado sem espiar teste |
| Fairness | estratificação de p95 por classes e slowdown offline (T_j/d_j) | duração verdadeira legal apenas para evaluation, não observation |
| Custo | p50/p95 e total de wall-time por decisão, CPU/RAM e treino | simulação de custo zero não valida utilidade real |

**Horizon / censoring:** declarar janela de admissão [0,H_a), horizonte de observação H_e e budget máximo para **drain** (sem chegadas novas, aguardar todos completarem). Primária de coorte integral só quando todos os jobs terminam sob limite definido; se não, reportar contagem iniciada/concluída/censurada, running vs queued, idades, demanda de trabalho pendente e lower bound de sojourn (T_j >= H_e-a_j) para cada não concluído. Nunca imputar zero, excluir silenciosamente ou chamar de ganho a política que deixa jobs longos fora da amostra. Estimadores de sobrevivência são apenas sensibilidade, pois censura pode ser informativa e induzida pela policy. No-progress, WAIT sem progresso, execução fora do budget e starvation são resultados de falha, não vitórias.

#### Desenho pareado, inferência e segurança científica

Separar **train / validation / final test** por seeds e, para traces externos, por tempo/origem; reservar OOD holdout com mudança de carga, skew, ruído, viés e mix de recursos. Congelar antes do teste: split, B*, definição de delta, tamanho e número de cenários, seeds, guardrails, threshold starvation, agregação, IC, correção de comparações múltiplas e stop rules. Usar common random numbers por cenário/seed para policy A versus B*. Replicar **seeds independentes de treinamento** (proposta piloto: 5 ou mais) e cenários independentes (dezenas por estrato; dimensionar usando piloto de validação, NÃO holdout). IC pareado por cenário com bootstrap hierárquico para seeds de treino; jobs dentro de um cenário NÃO são replicações independentes. Reportar effect sizes, incerteza, perdas, custos de treino/inferência e contagem de casos válidos.

**Reward hacking e regressão:** otimizar throughput isoladamente, manter jobs longos na fila, empurrar conclusões além do horizonte, usar IDs/seed/futuro como proxy, explorar máscaras, liberar memória cedo ou emitir WAIT infinito podem inflar fitness. Especificar guardrails antes de treinar e testar manualmente: recursos CPU livres mas memória insuficiente; simultâneos; estimativas subestimadas; jobs longos; ações ilegais; WAIT no último evento; fila única; invariantes de conservação, monotonicidade e ausência de execução duplicada. Fitness escalar, penalties, política de rejeição e fairness são **DECISION REQUIRED**.

#### Contratos observáveis para #3 (PROPOSAL; não ADR)

- **Job:** id público estável, arrival_time, cpu_units, memory_units, estimated_duration, timestamps e estado. actual_duration permanece **somente na verdade do simulador e avaliação**.
- **Observation:** current_time, capacidade total/livre de CPU e memória, jobs chegados/esperando com campos públicos, waiting age, histórico permitido e eligible_job_ids; wait_allowed explícito; sem futuro, seeds, split labels, duração verdadeira ou próximo término.
- **Action:** START(job_id) de job elegível ou WAIT estritamente legal, com máscara e comportamento para ação inválida/fallback definidos antes da execução. Nenhuma preempção, mudança de quota ou shell.
- **Policy:** reset(policy_seed, public_config), decide(observation) -> Action, serialização opcional com versão, estado interno privado e determinismo configurado; acesso somente à interface, não ao estado real do simulador.

**DECISION REQUIRED / SYNTHESIS:** RESEARCH-02 valida time/event/WAIТ, censoring e simulador; RESEARCH-03 pesquisa entrada de fila variável, algoritmo e orçamento; somente então formalizar contratos/função de fitness no ADR. EXP-001 não fornece evidência de generalização, validação física ou novidade científica antes de dados reais.

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
