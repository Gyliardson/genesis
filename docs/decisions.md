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
