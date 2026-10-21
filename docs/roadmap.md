# Roadmap e estratégia de execução

> Os itens operacionais devem viver como **GitHub Issues**; este arquivo descreve dependências e critérios de saída, sem espelhar checklists de tarefas.

## M0 — Research Foundation

**Saída:** escopo e hipóteses revisáveis, primeiras referências, contratos de domínio e infraestrutura mínima de testes. Investigar o que pode ser simulado corretamente antes de escolher bibliotecas.

## M1 — Simulation Core

**Saída:** jobs e recursos com invariantes testados; chegadas e durações sintéticas reprodutíveis; métricas; políticas FIFO/SJF/aleatória/encaixe comparadas num benchmark determinístico.

**Portão de qualidade:** cenário calculável manualmente bate com resultados do motor; seeds iguais geram logs equivalentes; nenhuma policy tem acesso indevido à duração real.

## M2 — Neuroevolution (primeiro MVP funcional)

**Saída:** uma pequena policy neural avaliada pelo mesmo contrato que as baselines; seleção, mutação e populações; checkpoint carregável; comparação inicial sem reivindicar ganho.

**Portão de qualidade:** aprendizado repetível, ações sempre válidas, orçamento de treino registrado, métricas de baseline disponíveis.

## M3 — Scientific Validation

**Saída:** variação de cenários, holdout, múltiplas seeds, intervalos de incerteza, análise de falhas e ablações, conclusão técnica documentada.

## M4 — Real Workloads (somente após gates)

**Saída:** workers sintéticos em containers isolados; shadow mode; integração limitada com autorização explícita, quotas, fallback e rollback; sem modificação do escalonador do kernel.

## M5 — Advanced Research

Plasticidade neural, NEAT/RL comparativos, transferência entre ambientes, ecossistemas de vida artificial, conectomas, exploração de previsibilidade e novos casos de uso.

## Backlog

O backlog oficial é [GitHub Issues](../../issues), marcado por prioridade `P0` (fundação e simulação), `P1` (MVP e validação inicial), `P2` (pesquisa avançada e aplicações reais). Se um Project estiver disponível, usar status `Backlog`, `Ready`, `In Progress`, `Review`, `Done`. Não atribuir prazos arbitrários.
