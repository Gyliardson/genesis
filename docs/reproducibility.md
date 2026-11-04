# Reprodutibilidade científica mínima

> **Status:** protocolo proposto para contribuições. O repositório contém somente um scaffold e smoke test; **ainda não existe benchmark EXP-001 executável nem resultado experimental validado**.

## Reproduzindo as verificações de engenharia

Em ambiente Python 3.11 limpo (compatibilidade com outras versões ainda não aferida):

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

Registre SO/arquitetura, Python, versões resolvidas de pacotes, comando e SHA. O comando de instalação editable acima é uma conveniência para desenvolvimento: **não é equivalente** ao fluxo hash-locked do CI. A restrição de minutos privados relatada em 23/10/2026 é um registro histórico, superado para o run específico do PR #24 em 04/11/2026, mas não comprova disponibilidade futura ilimitada. Não declare comandos PASS sem execução e evidência no SHA relevante.

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

## PUB-05 — dependências fixadas e instalação CI (evidências de 04/11/2026)

O workflow do PR #24 usa `ubuntu-24.04`, Python 3.11 e
`requirements/ci-py311-ubuntu24.04-x86_64.txt`: dez wheels pinados
por versão e SHA-256, `--require-hashes`, `--only-binary=:all:`,
build do projeto com `--no-index --no-deps --no-build-isolation`
após instalar o Hatchling verificado, Ruff, pytest e `pip check`.
**Este lock é específico de plataforma/arquitetura, não universal.**

**Execução hospedada efetiva:** [GitHub Actions run #41850235467](https://github.com/Gyliardson/genesis/actions/runs/41850235467)
em 04/11/2026, evento `pull_request`, SHA
`da1c6605860ecf842f5b4be81613e0448b71023a`, job
`python` em GitHub-hosted Ubuntu 24.04/Python 3.11: **PASS** em
instalação com hashes, build/instalação, Ruff, **26 testes e 45
subtests**, `pip check`. Essa evidência é vinculada ao SHA indicado;
commits posteriores precisam de checks próprios.

**Verificação independente no Codespace:** Ubuntu 24.04.5,
Python 3.11.17, `actionlint v1.7.12`, download de dez wheels
com hashes, venv novo, instalação offline, build e import de wheel,
Ruff, 26 testes/45 subtests e `pip check`: **PASS**. Quatro controles
negativos com `pip` rejeitaram hash adulterado, dependência transitiva
omitida, wheel de arquitetura incompatível e versão divergente.
O wheel GENESIS foi construído a partir de `git archive` do SHA acima;
esse ensaio não substitui a execução hospedada, também confirmada.

**Advisories e procedência:** consultas GHSA e OSV de 04/11/2026
retornaram zero advisories *conhecidos* para essas dez versões.
Todos os digests de wheel conferiram com metadados oficiais do PyPI;
sete attestations de publicação disponíveis foram validadas
criptograficamente com `pypi-attestations==0.0.31` contra os respectivos
repositórios publicadores. O PyPI Integrity API retornou 404 para a
provenance dos wheels exatos de `pygments 2.21.0`,
`ruff 0.17.2` (Linux x86-64) e `tomlkit 0.15.2`: **não atestados
neste procedimento**, não necessariamente comprometidos.
Esses controles não provam ausência de malware nem reprodutibilidade
source-to-wheel.

**Gates separados:** aceite de titularidade, atribuição e redistribuição
de terceiros; varredura histórica/remota completa; proteção efetiva de
`main`; canal confidencial de vulnerabilidades; revisão final de
publicação. **PUB-05 — CI e testes hash-locked: PASS no SHA acima,
com limitações de provenance documentadas. PREPUBLIC_GATE=FAIL.**
