# Reprodutibilidade científica mínima

> **Status:** protocolo proposto para contribuições. O repositório contém somente um scaffold e smoke test; **ainda não existe benchmark EXP-001 executável nem resultado experimental validado**.

## Reproduzindo as verificações de engenharia

Em ambiente Python 3.11 limpo (compatibilidade com outras versões ainda não aferida):

```bash
python -m pip install -e ".[dev]"
ruff check .
pytest -q
```

Registre SO/arquitetura, Python, versões resolvidas de pacotes, comando e SHA. Conforme confirmação do operador em 23/10/2026, a execução de GitHub-hosted Actions no repositório privado está bloqueada por falta de minutos disponíveis (Issue #4); testes locais em Python 3.14.2 não substituem a CI em Python 3.11. Não declare esses comandos PASS sem execução e evidência no SHA relevante.

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

## PUB-05 — integridade da instalação Python (gate ainda aberto)

**Evidência atual:** `pyproject.toml` declara `hatchling>=1.25` para build isolado e extras `pytest>=8`, `ruff>=0.9`; a CI instala `-e ".[dev]"` diretamente do índice, sem pin de versões transitivas, hashes ou lock. `python-version: "3.11"` e a imagem `ubuntu-24.04` também não fixam patch/intermediários. Nenhum lock reproduzível foi gerado ou validado nesta remediação; não tratar a ausência de falha observável como integridade comprovada.

**Estratégia incremental e reversível (sem impor ferramenta arbitrária):**

1. **Antes da exposição:** conservar o inventário e os testes locais (Python 3.14.2, não Python 3.11) e avaliar direitos e riscos sem fazer afirmações de resolução idêntica. **Após autorização de merge e de conversão pública:** executar `workflow_dispatch` na branch `main` em runner GitHub-hosted isolado, Python 3.11/Ubuntu 24.04, sem substituir `pull_request`/push; conferir SHA, run, job e steps e capturar `python --version`, `python -m pip --version`, `python -m pip inspect` e `python -m pip freeze --all` em artefatos de acesso restrito/sem segredos. Identificar versões **efetivamente resolvidas**, `hatchling` e dependências transitivas, plataforma, índices e hashes dos wheels; verificar advisories/CVEs para versões específicas. Até essa execução: `PUBLIC_CI=NOT_RUN` e `PUB-05=OPEN`.
2. Escolher e documentar um único mecanismo para o ambiente de CI: requirements travado com hashes (por exemplo `pip-compile --generate-hashes` a partir de entradas revisadas), lock de ferramenta equivalente ou constraints + prova de integridade dos artefatos. **Constraints com versões sem hashes não dão integridade de download.** Resolver também o build backend/ambiente PEP 517; constraints runtime não fixam automaticamente o build isolado. Preferir wheels confiáveis, versão/hashes registrados; não confiar em lock parcial.
3. Gerar o artefato num ambiente limpo da mesma plataforma alvo e com índice confiável; revisar todas as dependências diretas, transitivas e de build, hashes, licença e relatórios de vulnerabilidade. Provar reconstrução independente e `pip check`; somente depois mudar a CI para uma instalação que **falha fechada** diante de drift/hash inválido. Um possível fluxo é instalar distribuições travadas via `pip install --require-hashes -r <lock-validado>` e então instalar o projeto local com `--no-deps --no-build-isolation` **se** o ambiente de build validado já estiver presente. Não executar este fluxo nem alegar suporte antes de testá-lo.
4. Negative tests: adulterar hash em cópia temporária, remover requisito transiente, mudar versão e verificar que a instalação rejeita divergências; positive tests: instalação limpa, `ruff check .`, `pytest -q` e `pip check` no **mesmo candidate SHA**. Reavaliar versões/lock por PR dependabot/manual periódico, sem jobs de custo ou privilégio adicionais por padrão.
5. Distinguir **reproducibilidade** (mesmas resoluções), **integridade** (artefatos confiáveis/hashes), **vulnerabilidades conhecidas** (avaliação datada) e **execução segura do código de fork** (limites do GITHUB_TOKEN/runner). Nenhum dos quatro é implicado apenas pelos outros. Não fixar versões escolhidas por palpite nem tornar green removendo Ruff/pytest.

**Status:** PLANO DOCUMENTADO; resolução/lock/hashes e teste limpo continuam **UNVERIFIED** e PUB-05 **OPEN**. `pyproject.toml` e a CI de #4 ficam sem mudanças especulativas neste PR.
