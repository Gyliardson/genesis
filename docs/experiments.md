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
