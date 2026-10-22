# Visão e limites — GENESIS

> **Status:** documento de direção; revisável após pesquisa e experimentos. Data inicial: 2026-10-21.

## Por que o projeto existe

Investigar **autonomia computacional que não se resume à execução de scripts ou a chamadas de LLM**. A inspiração original foi vida artificial: indivíduos que acumulam experiência, possuem sistemas nervosos artificiais, evoluem e produzem comportamentos não especificados linha a linha.

O desejo de utilidade prática levou à primeira aplicação: **políticas adaptativas para escalonamento de workloads e alocação de recursos**. É um caso concreto que oferece restrições, dados, métodos clássicos de comparação e integração progressiva com sistemas reais.

## Missão

Projetar um laboratório que produza, avalie e exporte **controladores autônomos** por neuroevolução e, futuramente, aprendizagem individual, com experimentos reproduzíveis e limitações explicitadas.

## O que conta como autonomia

- O engenheiro define **observações, ações físicas/operacionais possíveis, limites de segurança e dinâmica do ambiente**.
- A política decide *qual* ação válida executar com base nas observações.
- A política evolutiva pode adaptar seus pesos e/ou estrutura no treinamento; plasticidade durante execução é um tema separado.
- Comportamentos **não são automaticamente emergentes** só porque foram produzidos por uma rede: precisamos de comparação e testes causais.
- Um controlador pode permanecer ativo e aprender sem constituir consciência. O projeto não fará alegações de consciência artificial.

## Primeira aplicação: GENESIS Core

Um controlador externo, inicialmente inteiramente simulado, decide a ordem de admissão e seleção de jobs sob restrições de CPU, memória e simultaneidade. Workloads podem ter chegadas dinâmicas, durações heterogêneas e estimativas imprecisas. Métricas incluem latência de conclusão, espera, throughput, utilização, fairness, custo do controlador e generalização.

**MVP delimitado:** um nó simulado, jobs independentes, execução **não preemptiva**, recursos discretos, estados observáveis definidos, políticas de referência e neuroevolução de uma pequena rede neural. Não pretende competir de imediato com o kernel nem com escalonadores de cluster sofisticados.


## Modelo operacional do primeiro experimento — RESEARCH-01

**PROPOSAL, não decisão arquitetural.** Estudar *online non-preemptive scheduling* em um nó com capacidade discreta (C_cpu, C_mem), jobs independentes e chegadas dinâmicas. Para cada job j: chegada a_j, reservas positivas (cpu_j, mem_j), começo s_j, conclusão f_j e duração verdadeira d_j = f_j - s_j. Jobs executam concorrentemente somente quando a soma de **ambas** as reservas não excede a capacidade. Recursos são reservados do início ao fim, sem preempção ou migração. Excluir DAGs, variação dinâmica de paralelismo, GPUs, deadlines e prioridades do escopo inicial, salvo decisão explícita.

**PROPOSAL — informação.** O estado verdadeiro do ambiente contém d_j, estado/seed do gerador e futuros eventos; nenhum desses dados pode aparecer na observação. A policy pode ver tempo atual, total/livre por recurso, fila de jobs chegados não iniciados, requisitos e duração **estimada** (dhat_j), tempo de espera já decorrido, histórico agregado permitido e máscara de ações. Não codificar o futuro/verdade em IDs, ordenação da fila, métricas auxiliares ou aleatoriedade. Estimativas são produzidas sem conhecimento da policy e podem ter viés, ruído, erro correlacionado com classe e deslocamento entre treino e teste. Duração real é legal somente para simulação e avaliação posterior, nunca para escolha da ação.

**PROPOSAL — eventos versus ticks.** Preferir decisões a cada chegada, conclusão e nova admissão no mesmo tempo lógico, em vez de tick fixo. Agrupar eventos simultâneos, liberar reservas concluídas e tornar chegadas visíveis antes de produzir uma observação, sujeitos à validação de RESEARCH-02. Após START de um job, permitir novas admissões no mesmo instante enquanto houver elegíveis; impedir decisões de tempo zero infinitas. Ticks introduzem granularidade e oportunidades de decisão artificiais e devem ser comparados apenas como alternativa metodológica.

**PROPOSAL — WAIT / FCFS e D-017 OPEN.** Distinguir avanço *forçado* do motor quando não há elegível de WAIT *voluntário* com job elegível. Sob **protocolo A candidato não ratificado**, uma ação START é obrigatória quando cabe algum job; **FCFS-scanning / first eligible fit** é baseline competitiva, enquanto **FCFS estrito head-of-line é diagnóstico separado**, pois exige esperar quando o head não cabe mas um job posterior cabe. Exemplo: head CPU=2 e livre=1, posterior CPU=1; no protocolo A estrito violaria a máscara. Alternativa **protocolo B** permitiria WAIT voluntário limitado e idêntico para todas as policies, com avanço até evento exógeno sem revelá-lo, fairness, stall e fallback pré-fixados. Nunca comparar A e B como se compartilhassem o mesmo espaço de ações. Não chamar scanning de EASY/conservative backfilling sem reserva de head. A decisão D-017 pertence ao gate G-003/PR #22.

**HYPOTHESIS e controles negativos condicionais (F05).** Políticas adaptativas podem explorar fragmentação CPU/memória, estimativas, rajadas e aging. Empate de **trajetória** só é controle negativo obrigatório com action space work-conserving sem WAIT voluntário, eventos/desempates determinísticos e exatamente uma ação legal em cada decisão alcançável. Filas unitárias ou baixa contenção isoladas não bastam quando WAIT pode ociosar; jobs homogêneos com chegadas diferentes não asseguram mesmo sojourn. Sob protocolo B com WAIT, avaliar invariantes de capacidade/progresso e diferenças legítimas de espera; não rotular qualquer divergência como bug.

**DECISION REQUIRED.** A síntese de RESEARCH-01/02/03 deve fixar a semântica de eventos, máscara e WAIT; campos de observação; tratamento de jobs inviáveis; horizons/drain e fairness; objetivos de fitness e limites de overhead. Estas propostas não alteram as decisões OPEN do registro de ADRs nem afirmam validação científica.

## O que não faremos no MVP

- Não desenvolver UI web, chatbot, agente LLM ou ferramenta RAG.
- Não treinar um cérebro biológico completo nem alegar consciência.
- Não executar decisões evoluídas sobre o computador do usuário sem isolamento e validação.
- Não presumir que evolução supera FIFO, SJF ou algoritmos clássicos.
- Não usar apenas vídeos impressionantes como evidência de melhoria.
- Não exigir GPU, cluster, Kubernetes ou infraestrutura de alto custo.

## Trilhas futuras preservadas

1. **Artificial Life / Open-Ended Evolution:** ecossistemas onde sensores, estratégias e estruturas neurais evoluem; possível laboratório paralelo em outro ambiente com a mesma interface de políticas.
2. **Neurociência computacional:** conectoma da mosca (*Drosophila*) e de *C. elegans*, neuroplasticidade, neurônios pulsados, experimentos de ablação e causalidade.
3. **“Soulkiller” (Cyberpunk), como metáfora técnica:** exportar/duplicar cérebro artificial (topologia, pesos e estado, quando disponível), transferir controladores entre ambientes/corpos e testar generalização. **Não** é transferência de consciência.
4. **Demônio de Laplace:** previsão de estados, problemas inversos, inferência causal, análise da informação acessível ao observador e limites da previsibilidade.
5. **Swarm/robótica/astronomia:** possíveis adaptadores futuros, desde que exista problema bem especificado e métrica verificável.

Essas ideias **não são funcionalidades aprovadas para o MVP**. Permanecem registradas para não desaparecerem durante o desenvolvimento.

## Definição de valor

O projeto terá valor como (a) sistema de engenharia experimental reutilizável, (b) portfólio que demonstre modelagem, algoritmos, testes e análise de resultados, e (c) estudo independente. **Valor científico novo** depende de contribuição original, revisão da literatura, protocolos robustos e evidências; implementar algoritmos conhecidos isoladamente não caracteriza descoberta.

## Princípios

- Problema/hipótese antes de biblioteca; baselines antes de treinar redes.
- Cenários reproduzíveis e estratificação treino/validação/teste.
- Segurança operacional separada da política neural.
- Custo de complexidade justificado por métricas.
- Documentos são fonte para decisões; **GitHub Issues** são fonte para tarefas.
