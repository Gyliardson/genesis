# Publicação pública: procedimento de segurança

## Atualização verificada de execução — 04/11/2026

A fase de execução da CI descrita historicamente abaixo como
`PRIVATE_HOSTED_CI=BLOCKED_RESOURCE` foi **superada para o run
específico** [#41850235467](https://github.com/Gyliardson/genesis/actions/runs/41850235467).
No SHA `da1c6605860ecf842f5b4be81613e0448b71023a` do PR #24,
o GitHub-hosted `ubuntu-24.04`/Python 3.11 concluiu com
`success`: dez wheels com hashes, build e instalação offline,
Ruff, **26 testes + 45 subtests** e `pip check`. A evidência
não garante orçamento de CI futuro nem valida a exposição pública.

Gitleaks 8.30.1 verificado e controles sintéticos reais: PASS;
auditoria local de 46 commits/90 blobs alcançáveis: zero findings
no detector. O inventário remoto listou 11 refs, 112 comentários,
11 reviews e 60 runs com zero artifacts retornados. Checks de
padrões conhecidos nos textos remotos não tiveram matches. **PUB-01
permanece PARTIAL:** logs/annotations históricos inacessíveis,
refs ocultas, anexos externos, análise semântica e direitos não
foram integralmente auditados. A licença Apache-2.0 foi aprovada,
e o mantenedor confirmou direitos sobre o código/documentação atualmente incluídos ([registro](https://github.com/Gyliardson/genesis/issues/23#issuecomment-6634429346)); a revisão independente de atribuições/`NOTICE` continua pendente. `main` segue
`protected=false`, com regras privadas 403 por limitação do
plano; canal confidencial PUB-06 ainda UNVERIFIED.

**A versão atual dos gates deve ser lida junto com os checkpoints da
[Issue #23](https://github.com/Gyliardson/genesis/issues/23).
PREPUBLIC_GATE=FAIL; não foi autorizada mudança de visibilidade.
Os parágrafos abaixo que descrevem bloqueios de CI em 23/10/2026
representam evidências históricas, não o estado de 04/11/2026.**

**Inventário limitado de direitos (PUB-02):** na árvore do PR revisada em 04/11/2026, os 29 arquivos rastreados são texto, código e metadados de engenharia; não foram identificados datasets, imagens, arquivos binários de terceiros ou conteúdos vendorizados. O wheel GENESIS não incorpora `pathspec` (MPL-2.0), que é dependência de build da CI, nem outras bibliotecas de terceiros. Os 47 commits alcançáveis nas branches visíveis foram atribuídos à conta do mantenedor, o que não comprova individualmente a autoria do conteúdo. Não foi identificado aviso de terceiro incorporado que obrigue um `NOTICE` adicional **neste inventário**; a necessidade deve ser reavaliada se ocorrer distribuição de código modificado de terceiros, assets, dados, dependências empacotadas ou contribuições futuras. **PUB-02_OPERATOR_RIGHTS_ATTESTATION=PASS; PUB-02=PARTIAL** enquanto persistir revisão independente de atribuições. Nenhum desses registros autoriza tornar o repositório público.

**Esta é uma política de preparação, não uma autorização de divulgação.** O registro de gates e evidências atuais permanece na [Issue #23](https://github.com/Gyliardson/genesis/issues/23). Não declarar `PREPUBLIC_GATE=PASS` apenas porque um PR foi criado.

## Decisão de licença aprovada — 23/10/2026

O operador escolheu **Apache-2.0 para o código do GENESIS** no escopo da
[Issue #23](https://github.com/Gyliardson/genesis/issues/23). A branch de
preparação do PR #24 incorpora o texto integral [LICENSE](../LICENSE), o
identificador SPDX no `pyproject.toml` e as referências no README/CONTRIBUTING.
Esta decisão **não** libera mudança de visibilidade nem merge em `main`.
A licença do código não substitui a verificação de titularidade,
atribuições, materiais de terceiros, datasets, traces, assets externos
ou direitos de contribuições. Confirmar a necessidade de um `NOTICE` correto
após revisão de atribuições; não inventar declarações de copyright.
Relatos e versões históricos abaixo sobre ausência de licença descrevem
o momento de suas auditorias anteriores; o status vigente de cada gate deve
ser confirmado na Issue #23 e no HEAD do PR #24. **PUB-02=PARTIAL**;
`PREPUBLIC_GATE=FAIL`.

## Gate antes de mudar visibilidade

1. Inventariar todas as refs, commits alcançáveis e objetos sensíveis; executar scanner previamente autenticado e validado pelo wrapper sobre todos os patches alcançáveis (inclusive merges com `-m`) em clone autorizado, sem confundir cobertura de patches com histórico/superfícies completos, revisar achados redigidos e rodar revisão humana. Cobrir também Issues, PRs, comentários, reviews, anexos, Checks/annotations, Actions/logs e artefatos, inclusive referências fora do Git. Se alguma superfície não for auditável, classificar **UNVERIFIED**, não PASS.
2. Corrigir **antes** da publicação qualquer exposição sensível. Para segredo válido: bloquear divulgação, identificar titulares e rotacionar/revogar pelo processo autorizado; avaliar necessidade de tratamento de histórico com autorização separada. Não reproduzir o segredo em Issue, PR ou log.
3. **Licença de código decidida:** Apache-2.0 aprovada pelo operador em 23/10/2026 e preparada no PR #24. Antes de publicar, revisar e comprovar copyright/atribuições, direitos de redistribuição sobre materiais incorporados e a necessidade de `NOTICE`; avaliar separadamente direitos de contribuições e de dados/artefatos. Não confundir licença escolhida com titularidade já verificada.
4. **Revisar estaticamente os controles de CI de forks antes da exposição:** evento `pull_request` não privilegiado, `permissions: contents: read`, actions pinadas por SHA, checkout sem persistência de credenciais, timeout/concurrency e custos proporcionais. A execução hospedada privada está bloqueada por falta de minutos conforme [Issue #4](https://github.com/Gyliardson/genesis/issues/4); o teste real de CI deve ocorrer na fase B descrita abaixo, nunca ser declarado PASS antecipadamente. Não usar `pull_request_target` para executar código de PR externo; não entregar segredos ou runners privilegiados a forks.
5. Obter revisão técnica **independente no exato HEAD** do candidato, incluindo segurança do histórico e da infraestrutura, licenças, integridade de dependências e comunicação científica. Testes, review e autorização de merge são gates diferentes.
6. Deliberar mudanças operacionais pendentes. Merge em `main` exige autorização específica do operador para PR/HEAD, além das proteções reais. Mudança de visibilidade exige autorização **separada** e `PREPUBLIC_GATE=PASS` verificável.

### Gating em duas fases quando os minutos do runner privado estão esgotados

**Restrição confirmada pelo operador em 23/10/2026:** a conta não dispõe de
minutos de GitHub-hosted Actions para este repositório enquanto estiver
privado. A exigência de **CI hospedada PASS antes de abrir** criaria uma
dependência circular; registrar `PRIVATE_HOSTED_CI=BLOCKED_RESOURCE`,
e não reinterpretar seus jobs de início negado como falhas do código.

**Fase A — antes de expor o repositório (obrigatória):** executar checks
locais isolados, scanner verificado em refs alcançáveis, inventário das
superfícies e logs disponíveis, triagem humana de histórico/atribuições e
revisão técnica independente no exato HEAD. Classificar cada superfície
inacessível como `UNVERIFIED` e decidir riscos residuais explicitamente,
sem presumir que um scan negativo em patches libere dados externos.
Resolver os bloqueios não dependentes do runner antes de solicitar
autorização específica de merge do PR #24 em `main` e **autorização
separada** para a mudança de visibilidade. Não expor segredos em logs,
Issues, PRs ou evidências públicas.

**Fase B — após conversão autorizada (verificação operacional):**
sem anunciar conclusão, configurar/verificar proteção efetiva de `main`
e habilitar/verificar Private Vulnerability Reporting quando disponível.
Usar `Actions > CI > Run workflow` na branch `main` (`workflow_dispatch`
somente quando este workflow estiver efetivamente integrado à branch
padrão), e confirmar run/job/steps **realmente executados** em
`ubuntu-24.04`, Python 3.11, Ruff e Pytest no SHA correto. O botão não
equivale a execução nem garante PASS; se não houver runner ou algum teste
falhar, manter `PUBLIC_CI=FAIL/BLOCKED`, suspender anúncio e reavaliar.
Nunca disparar código de fork com privilégios para compensar a cota.
Antes de exigir um check em branch protection, confirmar que ele
efetivamente executa e passa. Reproduzir e validar lock/hashes de
dependências em Python 3.11 conforme `PUB-05`; se não estiver pronto,
o respectivo gate permanece aberto e não deve ser declarado integralmente
reprodutível.

**Janela de exposição:** mudar a visibilidade torna imediatamente
acessíveis histórico e superfícies públicas do repositório; um rollback
não apaga cópias externas. A fase B não serve para descobrir segredos que
deveriam ter sido tratados na fase A. Aprovações de merge e visibilidade
não decorrem de "continuar" ou do resultado de testes locais.

## Janela operacional da conversão

- Predefinir quem configura regras imediatamente após a conversão, quem verifica, critérios de abortar, canais privados para resposta e janela de execução de baixo tráfego.
- Quando regras não estiverem disponíveis no repositório privado/na modalidade atual, minimizar o intervalo sem proteção e **antes de anunciar o link público** configurar proteções de `main`: exigir PR, review de terceiro quando praticável, checks realmente executáveis, bloquear force-push/deleção e restringir bypass/admin conforme plano. Verificar configurações por leitura posterior; não exigir check quebrado como condição sem antes tratar a Issue #4.
- Revisar configurações de GitHub Actions, política de aprovação de PR de forks, permissões padrão do `GITHUB_TOKEN`, acesso de colaboradores e runners, eventos que iniciam jobs, cache e dependências. Avaliar custo/abuso e manter jobs com limites.
- Só depois da autorização operacional e do gate completo usar GitHub Settings para mudar visibilidade. Readback: repositório público, regras efetivas em `main`, status de CI em eventos de fork confiáveis, Issues/PRs/Actions expostos como esperado, ausência de exposição de segredos e consistência de avisos de licença.

## Falha, contenção e rollback

**Voltar a privado não desfaz exposição pública.** Clones, forks, caches e downloads podem persistir. Se for descoberto risco, interromper anúncio e novas integrações; restaurar visibilidade privada se permitido e autorizado, desabilitar temporariamente a entrada insegura de contribuição sem reduzir controles, revogar/rotacionar credenciais com autorização e tratar os artefatos publicados. Registrar alcance e contenção; nunca alegar reversão completa de um vazamento. Preservar evidência privada para investigação.

## PUB-01 — auditoria executável de histórico e superfícies

Procedimento versionável: `scripts/audit-public-readiness.sh` (local/autorizado; exige `git` e `gitleaks`). Executar com **clone autenticado fora do workspace compartilhado**, por exemplo:

```bash
# Configurar autenticação GitHub sem token em argumentos, commit ou terminal compartilhado.
umask 077
bash scripts/audit-public-readiness.sh 'https://github.com/Gyliardson/genesis.git' "$HOME/genesis-private-audit-$(date +%Y%m%d)" "$HOME/security-approved-gitleaks.manifest"
```

O script requer manifesto independente de confiança **antes da primeira execução**, e só então registra versão e hash binário do scanner, `refs`, quantidade de commits, lista de objetos alcançáveis, `git fsck` e Gitleaks com `--all --full-history -m` (patches de todos os parents dos merges). Captura as refs remotas de branches/tags e tenta `refs/pull/*/{head,merge}`. O wrapper zera `GITLEAKS_CONFIG`/`GITLEAKS_CONFIG_TOML`, usa regras embutidas no binário registrado, ignore vazio, `--ignore-gitleaks-allow` e nenhum baseline. **Regras embutidas podem conter allowlists**: não alegar ausência absoluta de supressão. `gitleaks version` e SHA-256 do executável ficam em diretório privado; verificação de autenticidade/proveniência exige fonte confiável independente. Saída e relatórios ficam privados. Código de saída diferente de zero interrompe o gate, inclusive achado confirmado ou erro de ferramenta. Triar falsos positivos separadamente sem copiar segredos em GitHub.

**Cobertura negativa e limites:** scan de patch Git não verifica semanticamente toda propriedade/dado pessoal, blobs inacessíveis ao servidor, objetos dangling não anunciados, refs ocultas/não baixadas, arquivos Git LFS não obtidos, dados de forks independentes, caches, snapshots de terceiros nem conteúdo de Issues/PR/Actions. `git fsck` em clone verifica somente o conjunto de objetos efetivamente transferidos. Registrar SHA/refs e eventuais falhas de fetch; não chamar varredura completa sem revisão dessas lacunas.

### Materiais externos ao Git — coleta privada e verificação humana

**Atualização de segurança (2026-10-23):** o exemplo de `capture_private`
em Bash abaixo é apenas material histórico de planejamento, **não deve ser
executado como está** no Codespace. Testes reais provaram que o redirecionamento
do Bash pode criar arquivos `0646`/`0666` mesmo com `umask 077`. Para a
primeira fase de textos autenticados (Issues, PRs, comentários e reviews), usar
o coletor Python que pré-cria arquivos privados `0600` e nunca transmite
dados brutos ao terminal:

```bash
python scripts/audit-github-text-surfaces.py --selftest
# Somente após PASS do selftest, em Codespace autenticado/autorizado:
python scripts/audit-github-text-surfaces.py --live
```

**Escopo e limites:** a coleta usa `gh api` read-only com paginação, examina
títulos/corpos e texto de comentários/reviews com Gitleaks v8.30.1 validado
por SHA256; os resultados e corpos permanecem em pasta nova `0700` no
`$HOME` (arquivos `0600`). Resumos exibem somente contagens e estados.
Durante a execução do Gitleaks real no Codespace, o arquivo de relatório
pode ser recriado com permissões diferentes de `0600`, mesmo se o placeholder
foi pré-criado. O coletor valida que o diretório privado do scanner é `0700`
e, ao terminar o processo, abre o relatório sem seguir symlinks, verifica
regular file, owner e link count, aplica `fchmod(0600)` via file descriptor
quando necessário e verifica novamente todos os artefatos. Não enfraquece
o teste de modo final; durante a escrita, a confidencialidade contra outros
usuários depende do diretório `0700`. O processo com o mesmo UID permanece
na mesma trust boundary. A hipótese de criação/recriação do arquivo ainda
requer validação operacional no Codespace.

O scanner não valida direitos autorais, PII nem a segurança semântica dos
conteúdos; anexos são apenas contados aproximadamente por links e não baixados.
Histórico de edições de comentários, timelines, Actions/logs/annotations,
anexos, Wiki, LFS, forks e APIs inacessíveis continuam `UNVERIFIED`.
Nenhum resultado autoriza publicação; `PREPUBLIC_GATE=FAIL`.


Exige GitHub CLI autenticada com escopo de **leitura** e acesso a cada superfície. Nunca anexar dumps brutos à Issue/PR:

~~~bash
# Execute somente em máquina autorizada; não em terminal/transcript compartilhado.
set -Eeuo pipefail
umask 077
private_dir="$HOME/genesis-audit-surfaces-$(date +%Y%m%d)"
if [ -e "$private_dir" ] || [ -L "$private_dir" ]; then
  echo 'Destino já existe; não sobrescrever auditoria.' >&2
  exit 73
fi
mkdir -m 700 -- "$private_dir"
capture_private() {
  local label="$1"; shift
  case "$label" in ''|*[!A-Za-z0-9_.-]*) return 64 ;; esac
  : > "$private_dir/$label.stdout.private"
  : > "$private_dir/$label.stderr.private"
  if ! "$@" > "$private_dir/$label.stdout.private" 2> "$private_dir/$label.stderr.private"; then
    printf 'FAILED %s\n' "$label" >> "$private_dir/failures.private"
    return 1
  fi
}
capture_private auth gh auth status
capture_private issues gh api --paginate 'repos/Gyliardson/genesis/issues?state=all&per_page=100'
capture_private issue-comments gh api --paginate 'repos/Gyliardson/genesis/issues/comments?per_page=100'
capture_private pulls gh api --paginate 'repos/Gyliardson/genesis/pulls?state=all&per_page=100'
capture_private review-comments gh api --paginate 'repos/Gyliardson/genesis/pulls/comments?per_page=100'
capture_private runs gh api --paginate 'repos/Gyliardson/genesis/actions/runs?per_page=100'
# Para cada RUN_ID/CHECK_ID numérico descoberto nas listas privadas:
# RUN_ID=...; CHECK_ID=...
# capture_private "run-$RUN_ID-logs" gh run view "$RUN_ID" --log
# capture_private "check-$CHECK_ID-annotations" gh api --paginate \
#   "repos/Gyliardson/genesis/check-runs/$CHECK_ID/annotations"
# NUNCA execute gh run view sem captura.
~~~

Para cada PR enumerado, coletar separadamente `gh api repos/Gyliardson/genesis/pulls/NUM/reviews` e `gh api repos/Gyliardson/genesis/issues/NUM/comments`; para cada run enumerado, `gh api repos/Gyliardson/genesis/actions/runs/ID/jobs`, `capture_private "run-$RUN_ID-logs" gh run view "$RUN_ID" --log` após validar RUN_ID numérico e `gh api repos/Gyliardson/genesis/actions/runs/ID/artifacts`; para cada check-run obtido por `gh api repos/Gyliardson/genesis/commits/SHA/check-runs`, usar `capture_private "check-$CHECK_ID-annotations" gh api --paginate "repos/Gyliardson/genesis/check-runs/$CHECK_ID/annotations"` após validar CHECK_ID numérico. Enumerar pages e preservar status HTTP: **404/403, steps ausentes ou 0 artifacts não significam PASS**. Revisar links `user-attachments`/uploads, imagens, Markdown, releases/tags, Discussions, caches, LFS, URLs externas e referências a forks/manual screenshots sob acesso autorizado. Guardar textos, logs e anexos em diretório 0700 e revisá-los com detector de padrões **e** julgamento humano; dados de terceiros e dados pessoais exigem análise semântica e de direitos. Nenhum desses dumps foi obtido por este procedimento apenas por estar documentado.

Registrar privadamente: data, responsável, scanner/versão/hash, refs e SHAs, contagens esperadas vs obtidas, falhas API, superfícies incluídas/excluídas, falsos positivos redigidos, cobertura manual, owners de remediação. Em checkpoint GitHub, publicar **somente estados, contagens e limites**, jamais o material encontrado. Um segredo válido impõe STOP, rotação/revogação autorizada e avaliação separada do histórico; reescrita é proibida nesta missão.

## PUB-04 — configuração e readback de `main`

Antes de qualquer tentativa, verificar na conta administradora **Settings > Rules > Rulesets** e **Settings > Branches** a disponibilidade efetiva no plano/visibilidade atual. Configuração desejada para `main`: PR obrigatório antes de alteração, review independente quando disponível, bloqueio de force-push/deleção, checks necessários **somente depois** de #4 corrigida e comprovada no HEAD, política de bypass restrita e Actions/fork permissions revisadas. Não executar alteração de settings nem visibilidade nesta missão.

Readback autenticado, após **autorização específica** para configurar e quando o GitHub permitir:

```bash
gh api repos/Gyliardson/genesis/branches/main --jq '{protected,sha:.commit.sha}'
gh api repos/Gyliardson/genesis/branches/main/protection
gh api repos/Gyliardson/genesis/rules/branches/main
```

Checar que `protected=true` e que regras **efetivamente aplicáveis** à ref `main` exigem os controles acordados; conferir ainda Settings/Rulesets em UI e uma tentativa não destrutiva de validação. `403` por plano ou permissão, `404` ou endpoint vazio significa **UNVERIFIED**, não aprovação tácita. Se o plano privado impede pré-configuração, o operador deve **adiar conversão ou decidir conscientemente janela de exposição/upgrade** após checklist independente; não prometer zero janela nem converter automaticamente. Um rollback de visibilidade não recupera cópias/forks.

## Matriz de remediação (sem liberar publicação)

| ID | Situação após procedimentos | Gate restante |
| --- | --- | --- |
| PUB-01 | PARTIAL — roteiro Git, API e revisão humana especificados | scanner real completo, refs/objetos e superfícies fora do Git |
| PUB-02 | PARTIAL — Apache-2.0 aprovada no PR #24, ainda não integrada em main | verificação de titularidade, atribuições/NOTICE, dados e artefatos |
| PUB-03 | BLOCKED_RESOURCE — minutos privados esgotados; checks locais em Python 3.14.2 PASS | CI pública real em Python 3.11 no SHA efetivo após conversão autorizada |
| PUB-04 | FAIL — configuração e readback documentados, nenhuma regra ativada | proteções efetivas de main |
| PUB-05 | OPEN — estratégia causal em docs/reproducibility.md | lock/hashes resolvidos e validação |
| PUB-06 | OPEN — fallback público não tratado como confidencial | canal privado confirmado e teste |
| PUB-07 | BLOCKER — PR Draft não integrado em main | review, CI e aprovação específica de merge |
| PUB-08 | NOTE — protocolo científico prospectivo preservado | ambiente efetivo e experimento futuro |

**PREPUBLIC_GATE=FAIL.** Nenhuma evidência histórica, jurídica, de CI, canal confidencial ou proteção pode ser considerada PASS com base apenas nesta documentação.


## PUBLIC-REVIEW-02 — controles e lacunas de execução (R02-01–06)

| Finding | Correção | Limite / gate |
| --- | --- | --- |
| R02-01 | `git log -p -m --all --full-history` produz patches de merge por parent; teste com segredo **sintético** em resolução de conflito, além de caso negativo | Eficácia das regras de **Gitleaks real** NOT_RUN, confirmar usando binário verificado antes de aceitar PUB-01 |
| R02-02 | `capture_private` coleta stdout **e** stderr (logs de runs, annotations, API) em arquivos 0600 sob diretório 0700 (`umask 077`); comando que falha interrompe sem despejar dados | Para cada job/run/check e paginação, falta coleta real, triagem humana e revisão de 403/404; preservar arquivos somente em estação autorizada e eliminar cópias conforme retenção aprovada |
| R02-03 | URL HTTPS com userinfo/credencial e SSH com password recusados antes de clone, sem eco; SSH agent (`git@...`/`ssh://git@...`) e HTTPS com credential helper externo permitidos | Não inspeciona histórico do shell/segurança do credential helper; nunca usar segredo em argumento |
| R02-04 | Scanner: binário/versão/hash e flags/help, `GITLEAKS_CONFIG` e `GITLEAKS_CONFIG_TOML` zerados, regras embutidas, ignore explícito vazio, `--ignore-gitleaks-allow`, sem baseline | **Allowlists embutidas nas regras não são removidas**; examinar configuração efetiva e proveniência do release/autenticidade; hashes locais isoladamente não bastam |
| R02-05 | Help capturado em arquivo, teste de flags sem `grep -q` alimentado por pipe: elimina falso negativo por SIGPIPE/`pipefail` | Versão que não suporta flags requeridas falha com 65; não relaxar |
| R02-06 | `ls-remote --refs` antes/depois versus refs locais do mirror/fetch PR, verificação de objeto, `git fsck --unreachable` e marcação de refs não reconhecidas | Ref remota pode expirar; objetos não anunciados/inacessíveis, LFS remoto, forks, refs ocultas e superfícies GitHub ficam UNVERIFIED |

Para executar testes de regressão **sem segredos reais** em checkout do candidato:

~~~bash
bash -n scripts/audit-public-readiness.sh
python -m unittest discover -s tests -p 'test_public_audit.py' -v
command -v gitleaks   # apenas localizar caminho; NUNCA executar version/help antes de autenticar hash
~~~

O pacote de testes usa explicitamente **test-double Gitleaks**, validando a passagem dos parâmetros, diferenças de merge, erro seguro, não divulgação no terminal e permissões. **Não é uma varredura Gitleaks real**. Antes da auditoria confidencial, verificar versão exata, distribuição oficial/hash ou assinatura confiável, regras/allowlists e testar o **binário verdadeiro** contra fixtures sintéticas positivas e negativas. Se o scanner real não encontrar a fixture merge-only, `PUB-01=FAIL`. Versão/hash são registrados pelo wrapper, mas por si não demonstram autenticidade.

A execução real deve usar clone privado autenticado, identificar divergências refs/objetos, revisar Git LFS (incluindo objetos efetivamente baixados), forks independentes, refs efêmeras, logs e annotations. `git fsck` apenas vê objetos transferidos; zero findings em patches não equivale a zero segredos, nem é clearance de privacidade ou licenciamento.

**PUB-05:** manter plano de lock/hashes em `docs/reproducibility.md` — não foi criado lock testado. **PUB-06:** manter `SECURITY.md` — nenhum canal confidencial operacional foi comprovado. No checkpoint original deste achado, `LICENSE` estava ausente e `LicenseRef-Proprietary` não tinha sido alterado; a autorização de Apache-2.0 de 23/10/2026 está documentada acima. A investigação de CI é da Issue #4. **PREPUBLIC_GATE=FAIL**.


## Privacidade dos arquivos de auditoria em Codespaces

Em um Codespace, os testes sintéticos observaram arquivos Bash criados por
redirecionamento com permissões `0646` ou `0666`, mesmo após `umask 077`.
A criação com Python `os.open(..., mode=0600)` produziu `0600` e redirecionar
para esses arquivos **já existentes** preservou `0600` tanto em `/tmp` como
em `/workspaces/genesis`. Isso não identifica a causa ambiental.

Por segurança, o wrapper exige agora **Python 3** e pré-cria todos os arquivos
privados conhecidos, inclusive stdout/stderr, relatório do scanner, refs,
manifestos de resultados e status, com criação exclusiva e verificação
`fstat=0600`, **antes da primeira gravação sensível**. Se a pré-criação falha,
a auditoria interrompe sem varrer o repositório. A criação dos arquivos vazios
ocorre exclusivamente no diretório novo `0700`. O mesmo usuário/host
continua sendo uma fronteira de confiança; Gitleaks real e auditoria privada
permanecem `NOT_RUN` até prova operacional.

## R03-01/R03-02 — status explícito e procedência pré-execução

**SCAN_PASS != AUDIT_PASS != PREPUBLIC_GATE=PASS.** O wrapper não autoriza publicação e **nunca retorna exit code 0**. Um scanner que retorna 0 significa somente patches alcançáveis sem finding naquele detector. O wrapper retorna **66** quando os demais gates seguem pendentes. Finding do scanner (1), trust/digest inválido (67), scanner ausente (69) e erros internos também interrompem. Não usar `set +e`, `|| true` nem ignorar o exit code.

O arquivo privado `status.private.env`, criado sob diretório 0700 com `umask 077`, tem estes estados verificáveis: `SCAN_STATUS=NOT_RUN|PASS|FINDINGS|ERROR`; `COVERAGE_STATUS=NOT_RUN|UNVERIFIED|FAIL`; `HUMAN_REVIEW_STATUS=NOT_RUN`; `GIT_LFS_STATUS=UNVERIFIED`; `FORKS_STATUS=UNVERIFIED`; `HIDDEN_REFS_STATUS=UNVERIFIED`; `GITHUB_SURFACES_STATUS=UNVERIFIED`; `AUDIT_STATUS=BLOCKED`; `PREPUBLIC_GATE=FAIL` e `EXIT_STATUS` não zero. Nunca executar esse arquivo como shell. Falhas antes da criação do diretório deixam arquivo ausente, o que **não** significa sucesso. Divergência de refs/objetos pode mudar `COVERAGE_STATUS` para `FAIL`; estado de LFS, forks, refs ocultas, GitHub/Actions/annotations e avaliação humana permanecem não verificados até trabalho independente.

### Manifesto externo de confiança — antes de `gitleaks version`

Um responsável autorizado deve verificar por canal independente a procedência/distribuição oficial do scanner, a versão, a arquitetura e o SHA-256 **obtido de evidência confiável externa ao executável instalado**. Criar fora do repositório/checkout um manifesto privado, arquivo regular modo 0600 com quatro linhas literais (não executáveis):

~~~text
SHA256=<64 dígitos hex de origem independente validada>
SOURCE=https://github.com/gitleaks/gitleaks/releases/download/<versao>/<asset>
DIGEST_SOURCE=<URL/identificador de evidência de digest previamente verificada>
VERIFIED_BY=<identificador do responsável>
~~~

O wrapper valida campos, formato, permissão e namespace oficial de `SOURCE`, isola uma cópia do binário num diretório privado, calcula o digest da cópia e compara ao manifesto **antes de executar** `version`, `--help` ou qualquer scan. Ausência, symlink, digest divergente ou scanner ausente interrompem. Nenhum digest é inferido/calculado a partir do executável e aceito como fonte esperada durante a auditoria. **O texto de SOURCE e a declaração VERIFIED_BY não são assinatura criptográfica**: a confiança no manifesto depende da revisão independente anterior (ex.: checksum de release assinado/pacote de proveniência autenticada, conforme disponível). Um manifesto falso também pode declarar um hash falso: não chamar isto autenticação automática de upstream.

### QA e gates subsequentes

A suíte offline usa binário **test-double** e manifesto de fixture explicitamente sintéticos, somente para testar a ordem de execução, hash divergente, manifesto não confiável, scanner ausente, saída não zero e estados negativos de Git LFS/forks/refs ocultas/superfícies externas. Testes com double não provam regras, parser, autenticidade ou assinaturas reais. Se houver Gitleaks real com release e digest verificados, **antes de auditar o repositório privado**, provar com fixture somente sintética: marcador reconhecido pelo detector, marcador em resolução merge-only com `-m` e controle negativo. Sem detector verificado, registrar `NOT_RUN`.

`PUB-01` permanece BLOCKER até scanner real/objetos/refs/superfícies/humano. `PUB-02` licença e titularidade, `PUB-03` CI Issue #4, `PUB-04` proteção de main, `PUB-05` integridade das dependências, `PUB-06` canal confidencial e `PUB-07` integração autorizada seguem pendentes. A decisão de licença Apache-2.0 foi autorizada em 23/10/2026 apenas para preparação no PR #24. Nenhuma mudança de visibilidade, proteção privilegiada ou merge foi autorizada. **PREPUBLIC_GATE=FAIL.**
