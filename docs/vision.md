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
