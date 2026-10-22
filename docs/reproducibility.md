# Reprodutibilidade científica mínima

> **Status:** protocolo proposto para contribuições. O repositório contém somente um scaffold e smoke test; **ainda não existe benchmark EXP-001 executável nem resultado experimental validado**.

## Reproduzindo as verificações de engenharia

Em ambiente Python 3.11 limpo (compatibilidade com outras versões ainda não aferida):

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

Registre SO/arquitetura, Python, versões resolvidas de pacotes, comando e SHA. A CI da Issue #4 continua com falha sem diagnóstico confirmado; não declare estes comandos PASS sem execução e evidência.

## Contrato de um experimento futuro

Toda avaliação deve registrar, antes do teste final: (1) pergunta falsificável, H0/H1, variáveis e stop rule; (2) commit, versões e hardware; (3) gerador/distribuição de workloads, parâmetros, seeds distintas e splits treino/validação/teste, com casos OOD; (4) estados privados versus observações que cada política pode consultar; (5) conjunto de ações legais, validação independente e comportamento para WAIT/starvation; (6) políticas FIFO/FCFS, SJF por estimativa, políticas de encaixe e aleatória válida quando aplicáveis; (7) orçamento de treinamento e inferência; (8) métricas, repetições, variabilidade e incerteza; (9) failures/censoring e conclusões negativas.

Preferir avaliação pareada dos mesmos workloads com igual informação, sem acesso à duração real oculta, futuro ou seeds de teste para decisões. Reportar completion/sojourn e waiting time (incluindo caudas), throughput, CPU/memória, fairness/starvation, fração não atendida, overhead de decisão e custo de treinamento. Especificar truncamento/horizonte, tie-breaking, eventos e política de censura. Não usar um único melhor seed como prova de melhoria.

## Critérios de divulgação

- **SIMULATOR_RUNS** não prova **SIMULATOR_CORRECT**; verificar invariantes e cenários calculáveis à mão.
- **POLICY_RETURNS_ACTION** não prova **ACTION_VALID**; máscara e safety layer independente são exigidas.
- **TRAIN_FITNESS_UP** não prova **HELD_OUT_GENERALIZATION**; aplicar seeds e distribuições não vistas.
- **BEATS_RANDOM** não prova **BEATS_CLASSICAL_BASELINES**; comparar com baselines justas.
- **CONTROLLER_EXPORT** não prova **REAL_WORKLOAD_SAFE**; workloads reais exigem isolamento, shadow mode, fallback, quotas e autorização específica.

Não publicar logs brutos que revelem segredos ou dados pessoais. Dados externos dependem de licenças, direitos de redistribuição e auditoria independente. Ver as propostas em `docs/experiments.md` e questões abertas em `docs/decisions.md`.
