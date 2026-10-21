# Arquitetura provisória

> **Proposta, não implementação existente.** Este documento não autoriza incorporar dependências sem benchmark e revisão.

## Componentes conceituais

1. **Simulation Core:** relógio lógico, eventos, recursos, filas e semântica de execução. Seed e desempates determinísticos. SimPy ou motor próprio — **a decidir**.
2. **Workload Generator:** tarefas sintéticas, distribuições de duração, chegadas, requisitos de memória/CPU, estimativas observáveis; futuramente replay de traces públicos.
3. **Policy Interface:** recebe somente a observação permitida e retorna uma ação (p.ex. id de job admissível ou `WAIT`, quando permitido). A observação e a action mask são estáveis e documentadas.
4. **Safety/Feasibility Layer:** valida capacidade, elegibilidade, deadlines e ações ilegais; usa fallback predefinido quando necessário. Política não pode contornar regras do ambiente.
5. **Evolution Engine:** representação de genoma, mutação, seleção, população, avaliação sobre múltiplos cenários; no MVP é possível usar MLP de topologia fixa. NEAT, CMA-ES e outras técnicas serão avaliadas depois.
6. **Evaluation Lab:** executa políticas com os **mesmos workloads e seeds**, produz métricas, agregações, incerteza estatística, artefatos e metadados de configuração.
7. **Deployment Adapter (futuro):** execução de tarefas sintéticas de verdade, em workers isolados, inicialmente observação/sugestão sem atuar; limites e rollback são obrigatórios.

## Fluxo simplificado

```text
Scenarios / Seeds ──> Simulation Core <────> Policy (FIFO / SJF / Neural)
                            │                           ↑
                   events + telemetry            Evolution Engine
                            │                           │
                            └──> Evaluation Lab <──────┘
                                     │
                             results / snapshots
                                     │
                           (futuro) Safe Adapter
```

## Domínio inicial (proposta de contratos)

- `Job`: `id`, `arrival_time`, `cpu_units`, `memory_units`, `estimated_duration`, `actual_duration` (oculto da policy até conclusão), estado e carimbos de tempo.
- `ResourcePool`: CPU/slots discretos, memória fixa; limites e disponibilidade.
- `Observation`: tempo lógico, recursos livres, fila de jobs prontos e atributos permitidos, histórico agregado autorizado, máscara de ações possíveis.
- `Action`: selecionar job elegível por identificador ou aguardar, se o protocolo permitir.
- `Policy`: `reset(seed, config)`, `decide(observation)` e opcional `state`/serialização.
- `Experiment`: cenário versionado, política, seeds, versão de código, métricas e artefatos.

**Especificar invariantes antes de codificar:** nunca alocar recursos indisponíveis; um job não executa duas vezes; capacidade liberada ao concluir; tempos monotônicos; nenhum vazamento de `actual_duration` para políticas.

## Escopo da simulação M1

- Um nó, jobs independentes, sem preempção e sem migração.
- Jobs concorrentes se houver recursos; política decide admissões em eventos relevantes.
- Recursos CPU e memória modelados como **capacidades discretas reservadas** (não simular uso percentual dinâmico no primeiro ciclo).
- Durabilidade dos eventos, determinismo dos desempates e limite para episódios sem progresso.
- Possibilidade de benchmark com execução repetida sem interface gráfica.

## Interface de redes neurais

MLP pequena com entradas normalizadas, observações mascaradas e saídas comparáveis entre jobs elegíveis. A representação de filas de tamanho variável é uma **questão aberta crítica**: candidatas incluem score por job baseado em atributos do job + estado global, janela top-K documentada ou arquitetura permutacional; evitar definir dimensão fixa arbitrária sem medir vieses.

## Estrutura prevista

```text
src/genesis/
  simulation/    # estado, eventos, recursos, geradores
  policies/      # contrato, baselines, controlador neural
  evolution/     # genomas, população, operadores
  evaluation/    # métricas, benchmarks, reprodutibilidade
  adapters/      # execução real futuramente
tests/
docs/
.github/
```

Pacotes e subdiretórios serão criados **quando houver implementação**, não como placeholders vazios.

## Segurança de execução real (M4)

- Apenas workloads de demonstração explicitamente autorizados em containers/VM isolados, quotas e timeouts.
- `dry-run` e `shadow mode` antes de qualquer intervenção; nunca ajustar automaticamente serviços de produção.
- Fallback determinístico, auditoria e desligamento manual; testar sobrecarga, deadlock/starvation e perda de observabilidade.
- Nunca permitir que políticas emitam comandos shell arbitrários ou elevem privilégios.
