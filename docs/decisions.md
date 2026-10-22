# Decision Log — decisões, propostas e dúvidas

**Convenção:** `ACCEPTED` = decisão de escopo confirmada; `PROPOSED` = preferida, não aprovada definitivamente; `OPEN` = exige pesquisa/experimento; `DEFERRED` = fora do MVP. Atualizar este registro em toda decisão que altere o desenho.

| ID | Estado | Assunto | Posição e justificativa |
| --- | --- | --- | --- |
| D-001 | ACCEPTED | Nome | GENESIS (`Gyliardson/genesis`), privado inicialmente. |
| D-002 | ACCEPTED | Foco | Laboratório de neuroevolução; aplicação inicial em gestão de workloads. |
| D-003 | ACCEPTED | Aplicação segura | Simulação antes da execução real; não substituir scheduler do kernel no MVP. |
| D-004 | ACCEPTED | Ciência | Medir baselines, variância e generalização sem prometer superioridade. |
| D-005 | PROPOSED | Linguagem e ferramentas | Python, NumPy, pytest, Ruff; adicionar tecnologias por necessidade. |
| D-006 | OPEN | Simulação | SimPy vs. motor mínimo próprio; benchmark/corretude decidirão. |
| D-007 | OPEN | Algoritmo evolutivo | GA com topologia fixa vs NEAT vs alternativas. MLP mínima preferida no MVP, mas não final. |
| D-008 | OPEN | Política para filas variáveis | Score por job, top-K ou rede permutacional; pesquisar viés e custo. |
| D-009 | PROPOSED | Modelo inicial | Um nó, tarefas independentes, sem preempção, recursos discretos. |
| D-010 | OPEN | Objetivos | Fitness, fairness, tradeoffs e custo de treinamento; definir antes de treinar. |
| D-011 | OPEN | Transferência | Avaliar workloads sintéticos -> traces -> workers reais sob controle. |
| D-012 | DEFERRED | Integração física/produção | Docker isolado, shadow mode e fallback após validação. |
| D-013 | DEFERRED | Linhas de vida artificial | Ecossistemas e evolução aberta fora do MVP, mas preservados na visão. |
| D-014 | DEFERRED | Neurociência | Plasticidade, conectomas, intervenção neural, 'Soulkiller' como analogia. |
| D-015 | DEFERRED | Previsão | Inferência de passado/futuro e limites de previsibilidade (Laplace). |
| D-016 | PROPOSED | Organização | README e docs para conhecimento; GitHub Issues para tarefas; milestones/Projects se disponíveis. |

| D-017 | OPEN / DECISION_REQUIRED | WAIT voluntário versus FCFS estrito | Preferência revisável: protocolo A sem WAIT voluntário + FCFS scanning como baseline principal; FCFS estrito apenas diagnóstico separado. Alternativa B concede WAIT controlado para **todas** as policies e exige testes de stall/fairness. Exceção só para FCFS estrito é comparação inválida. **Não ratificado.** |
| D-018 | PROPOSED | Ordenação de eventos e tempo | Inteiros em ticks positivos para duração; `COMPLETE → ARRIVE → DECIDE/START` no mesmo timestamp, IDs estáveis e limite de START por tick; clock monotônico. Comparar com engine de referência/oráculos antes da aceitação. |
| D-019 | PROPOSED | Domínio público e máscara | Truth privado separado de ObservationV0 imutável; ready ID/arrival/req/estimate/age, tempo e recursos; sem duration real, future events, seed/split, remaining-time ou rank oculto. Máscara por recursos públicos, safety valida novamente. Agregados adicionais exigem schema/testes. |
| D-020 | PROPOSED | Horizonte/coorte e censura | Chegadas [0,H_a); conclusão em H_e incluída; START apenas t<H_e; drain sob budget fixado é primário candidato. Fixed-H reporta READY/RUNNING/censurados, não imputa/descarta; timeout não ganha por survivor-only mean. |
| D-021 | OPEN / DECISION_REQUIRED | Ação inválida e falha | Candidata: INVALID_ACTION rejeitada sem mutação, run ERROR e resultados pendentes; alternativa fallback determinístico comum com overhead explícito. Antes de implementação confirmar classificação ERROR/POLICY_STALL/TIMEOUT e exposição das razões sem leakage. |
| D-022 | PROPOSED | Determinismo/isolamento experimental | Traces pré-gerados, IDs opacos independentes da truth, streams RNG policy/exógenos separados e seed derivation estável, hashes/log canonical, TRAIN/VAL/TEST-ID/OOD separados e comparações pareadas. |
| D-023 | OPEN | Abstração de policies / filas N variáveis | API mínima reset/decide versionada com lista variável e mask; scorer compartilhado candidato inicial, Deep Sets se ganho comprovar interação; top-K/attention/memória adiados. Exigir equivariância/permutação, tie externo e perfil de custo antes de D-008. |
| D-024 | PROPOSED | Component boundaries e execução real | Core, Policy, Safety/Feasibility, Evolution e Evaluation isolados; sem engine evolutiva no experimento de baselines nem adapter real no MVP. Retenção dos requisitos de isolamento/shadow mode para futuro. |
| D-025 | OPEN / DECISION_REQUIRED | Métrica primária, custo e limiares | DRAIN coorte completa e média sojourn pareada contra B* escolhida em VAL são candidatos, não fitness aprovado. Delta mínimo, fairness, starvation, multiplicidade, sizing e budgets requerem piloto/autoridade (#2/#8/#12), sem otimizar TEST. |

### Revisão de escolhas materiais (CONTRACT-01, PROPOSAL)

| Decisão / questão | Alternativas e tradeoffs | Evidência disponível (nível) | Menor experimento / critério de revisão |
| --- | --- | --- | --- |
| **D-017 WAIT/FCFS** | **A:** START forçado quando cabe, FCFS-scanning legal, mais fácil de provar progresso, mas não modela idle estratégico nem FCFS HOL. **B:** WAIT comum a todas, FCFS estrito possível, risco de stall/censura, mais estados e custos; WAIT encerra decisões no tick e só avança para próximo evento exógeno. **C:** WAIT excepcional só para FCFS, descartar em competição por actions distintas | Síntese #3 + PR #21 (proposta); observações de eventos #5 (proposta); **nenhum** resultado de simulação | Oráculo head-of-line (head requer mais do que o free pool e job seguinte cabe), último-evento sem progresso e controle de timeout; comparar A e B em mesmas condições **dentro de cada protocolo**. Decidir valor científico do idle, métricas de fairness e custo antes de ACCEPTED |
| **D-018 ordering/time** | DES event-driven com ordem explícita vs passo de tempo fixo. Inteiros preservam reprodutibilidade e controle; exigem quantização/tamanho de tick. Engine depende de D-006 | #5 golden A/B/C (cálculos manuais), não executados | A/B/C + conclusão/chegada no mesmo instante; t=H_a, completion t=H_e; colisões, monotonicidade, event log idêntico após permutação |
| **D-019 observation** | Lista pública mínima sem running remaining versus mais history/features. Minimal reduz leakage e complexidade, mas pode perder informação útil; versões preservam opção futura | #3 síntese, PR #21, #9 pesquisa de modelos (apenas proposta) | Property-based noninterference sob alteração de truth futura, `actual_duration`, RNG, split e IDs; mesma decisão com mesmo estado da policy; teste negativo de bypass da máscara |
| **D-020 horizon** | Drain coorte íntegra melhora identificabilidade da média; custo pode ser alto e falhar. Fixed-H modela streaming, mas censura induzida pela policy inviabiliza média complete-only como estimando principal | PR #21 / #8 planos metodológicos (propostas); sem EXP-001 | A/B/C, job ao cutoff, conclusão no cutoff, timeout e backlog; manter todos os casos em relatórios. Determinar budget via piloto em VAL, antes de TEST |
| **D-021 invalid/fallback** | Fail-fast torna bugs observáveis; fallback comum protege exploração e mantém episódio, porém mistura mérito da policy com heurística e exige custo/frequency accounting | #3 / #5 / #9 (propostas) | Ações desconhecidas, já iniciadas, inelegíveis, NaN/Inf, stale mask; nenhuma mutação parcial, razões sanitizadas; avaliar taxa de falhas/fallback por policy antes de escolher |
| **D-006 simulator** | SimPy = manutenção madura, ordem interna exige adapter; DES heap próprio = controle/possível performance, mais manutenção; ticks = oráculo de referência, risco de discretização | #5/#8 pré-registro de microbenchmark; **não rodado** | Correção isomórfica sobre goldens/invariantes primeiro. Depois teste perfilado com vários N, carga, repetição, RSS, latência e throughput no mesmo hardware; gate de desempenho proposto em #8, a revisar **antes** de observar dados |
| **D-008 / D-023 neural** | Scorer compartilhado O(NP) barato/equivariante; Deep Sets suporta contexto simétrico; top-K trunca opções; attention O(N²d) aumenta custo; GRU requer memória temporal | #9 matriz de tradeoffs + literatura; nenhum modelo treinado | Fila 0/1/K/K+1/grande, scores sob permutação, mask, latência e ablação em VAL; migrar modelo só se scorer falhar critério pré-fixado |
| **D-007 evolution** | GA fixo simples versus random search/ES/CMA/NEAT/RL. Complexidade/amostragem devem ser cobradas, não presumir superioridade | #10/#19 pesquisa, zero treinamento | Primeiro #5-#9 válidos; então random-search versus GA sob seeds, mesma info e budget; expandir para #19 só após #12 |
| **D-010/D-025 objective** | Sojourn coorte drain + constraints vs escalarização multiobjetivo; penalidade WAIT/stall e overhead são materiais; B* selecionada em VAL | PR #21 / #8 / #10 / #19 = desenho científico sem resultados | Pré-registrar delta, margem, IC hierárquico/pareado, guardrails, orçamento e split antes de TEST; piloto independente para power/custo; resultados negativos publicados |

**Autoridade / lifecycle:** Todas as D-017–D-025 estão PROPOSED ou OPEN; nenhuma nova ACCEPTED. D-006/D-007/D-008/D-010 **permanecem OPEN**, D-009 permanece PROPOSED; D-011 permanece OPEN. Aceitação futura exige: (1) revisão independente exata do PR #21 e incorporação de findings; (2) resolução explícita de D-017 na Issue #3; (3) evidência de oráculos, leakage, permissões de actions, cutoff e censura; (4) revisão científica e critérios pré-registrados para D-010/D-025. Nunca usar CI verde ou revisão como autorização automática para merge. Uma decisão editorial sobre o protocolo também não valida sua implementação.

**Fonte e rastreabilidade:** [Síntese #3](https://github.com/Gyliardson/genesis/issues/3#issuecomment-6330212075) · [PR #21](https://github.com/Gyliardson/genesis/pull/21) · [simulação #5](https://github.com/Gyliardson/genesis/issues/5#issuecomment-6330082567) · [workloads #6](https://github.com/Gyliardson/genesis/issues/6#issuecomment-6330083124) · [benchmark #8](https://github.com/Gyliardson/genesis/issues/8#issuecomment-6330083784) · [neural #9](https://github.com/Gyliardson/genesis/issues/9#issuecomment-6330082508) · [evolução #10](https://github.com/Gyliardson/genesis/issues/10#issuecomment-6330083086) · [comparação futura #19](https://github.com/Gyliardson/genesis/issues/19#issuecomment-6330083740).

## Principais riscos científicos e operacionais

- **Proxy reward e atalhos:** controlador pode otimizar métricas enquanto degrada fairness ou simular trabalho.
- **Leakage:** `actual_duration`, seed de teste ou outras variáveis ocultas não podem vazar para a policy.
- **Overfitting:** melhoria em treino pode desaparecer em workloads inéditos.
- **Desacoplamento simulação/realidade:** traces e distribuição sintética não reproduzem toda a complexidade de uma máquina.
- **Custos omitidos:** overhead de treinamento e inferência podem inviabilizar a política.
- **Premature framework choice:** escolher stack/arquitetura pela familiaridade antes de medir necessidades.
- **Antropomorfização:** redes neurais e dinâmica emergente não implicam vida biológica ou consciência.

## Questões para próxima conversa de pesquisa profunda

1. Qual é a formulação de scheduling ideal para um MVP justo e computacionalmente tratável?
2. Qual a melhor representação de observações e ações com tamanho variável da fila?
3. Quais baselines, constraints e datasets aparecem nas pesquisas recentes de learned scheduling?
4. SimPy oferece desempenho suficiente para avaliar centenas de políticas por geração?
5. Quais funções de fitness e restrições evitam starvation sem enviesar o experimento?
6. Qual protocolo de validação estatística pode ser executado em hardware comum?
7. Como separar evolução (entre gerações) de plasticidade/adaptação online (durante execução)?
8. Quais decisões permanecerão válidas quando passarmos a workers Docker?

## Processo de mudança

Uma escolha `OPEN` vira `ACCEPTED` apenas com: contexto, alternativas consideradas, evidência de protótipo/literatura, tradeoffs, critério de revisão e Issue/PR associado. Documentar quando um resultado contrariar a hipótese inicial.
