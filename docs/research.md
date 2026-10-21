# Pesquisa inicial e bibliografia viva

> Revisão **exploratória**, iniciada em 2026-10-21. Links são pontos de partida, não prova de que uma técnica servirá ao GENESIS. Atualizar após leitura dos artigos e reprodução dos resultados.

## 1. Escalonamento aprendido

- **Decima (Mao et al., SIGCOMM 2019)** — `Learning Scheduling Algorithms for Data Processing Clusters`: demonstra RL para políticas de escalonamento em clusters. É **antecedente importante**, então não devemos anunciar scheduling por IA como conceito inédito. [Página do MIT](https://web.mit.edu/decima/index.html) · [Registro do artigo](https://dspace.mit.edu/entities/publication/b5ecbc09-0de5-401e-b4e6-55d58e3ac242) · [Simulador de referência](https://github.com/hongzimao/decima-sim).
- **Pesquisa a fazer:** diferenças de objetivos e workloads entre Decima e GENESIS; comparações honestas com heurísticas; viabilidade de neuroevolução sob chegadas estocásticas; overhead e generalização.

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
