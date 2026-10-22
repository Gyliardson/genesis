# Publicação pública: procedimento de segurança

**Esta é uma política de preparação, não uma autorização de divulgação.** O registro de gates e evidências atuais permanece na [Issue #23](https://github.com/Gyliardson/genesis/issues/23). Não declarar `PREPUBLIC_GATE=PASS` apenas porque um PR foi criado.

## Gate antes de mudar visibilidade

1. Inventariar todas as refs, commits alcançáveis e objetos sensíveis; executar scanner confiável no **histórico completo** (por exemplo, `gitleaks git --log-opts="--all --full-history -m" .` em clone autorizado, validando sintaxe/versão da ferramenta), revisar achados redigidos e rodar revisão humana. Cobrir também Issues, PRs, comentários, reviews, anexos, Checks/annotations, Actions/logs e artefatos, inclusive referências fora do Git. Se alguma superfície não for auditável, classificar **UNVERIFIED**, não PASS.
2. Corrigir **antes** da publicação qualquer exposição sensível. Para segredo válido: bloquear divulgação, identificar titulares e rotacionar/revogar pelo processo autorizado; avaliar necessidade de tratamento de histórico com autorização separada. Não reproduzir o segredo em Issue, PR ou log.
3. Decidir expressamente licença, copyright/atribuições, direitos sobre contribuições e sobre dados/artefatos. **Apache-2.0 é apenas proposta para o código.** Até decisão, manter `LicenseRef-Proprietary`, ausência de `LICENSE` e terminologia que não prometa open source.
4. Validar CI de forks: eventos `pull_request` não privilegiados, `permissions: contents: read`, actions pinadas por SHA, checkout sem persistência de credenciais, timeout/concurrency e custos proporcionais. Diagnosticar separadamente a falha preexistente da [Issue #4](https://github.com/Gyliardson/genesis/issues/4). Não usar `pull_request_target` para executar código de PR externo; não entregar segredos ou runners privilegiados a forks.
5. Obter revisão técnica **independente no exato HEAD** do candidato, incluindo segurança do histórico e da infraestrutura, licenças, integridade de dependências e comunicação científica. Testes, review e autorização de merge são gates diferentes.
6. Deliberar mudanças operacionais pendentes. Merge em `main` exige autorização específica do operador para PR/HEAD, além das proteções reais. Mudança de visibilidade exige autorização **separada** e `PREPUBLIC_GATE=PASS` verificável.

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
| PUB-02 | BLOCKER — direitos proprietários preservados, LICENSE ausente | decisão expressa do operador e chain-of-title/dados |
| PUB-03 | FAIL — sem alteração de assertions/workflow | causa CI #4, ambiente limpo e exact-head |
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
command -v gitleaks && gitleaks version   # presença e versão apenas, NÃO é scan
~~~

O pacote de testes usa explicitamente **test-double Gitleaks**, validando a passagem dos parâmetros, diferenças de merge, erro seguro, não divulgação no terminal e permissões. **Não é uma varredura Gitleaks real**. Antes da auditoria confidencial, verificar versão exata, distribuição oficial/hash ou assinatura confiável, regras/allowlists e testar o **binário verdadeiro** contra fixtures sintéticas positivas e negativas. Se o scanner real não encontrar a fixture merge-only, `PUB-01=FAIL`. Versão/hash são registrados pelo wrapper, mas por si não demonstram autenticidade.

A execução real deve usar clone privado autenticado, identificar divergências refs/objetos, revisar Git LFS (incluindo objetos efetivamente baixados), forks independentes, refs efêmeras, logs e annotations. `git fsck` apenas vê objetos transferidos; zero findings em patches não equivale a zero segredos, nem é clearance de privacidade ou licenciamento.

**PUB-05:** manter plano de lock/hashes em `docs/reproducibility.md` — não foi criado lock testado. **PUB-06:** manter `SECURITY.md` — nenhum canal confidencial operacional foi comprovado. `LICENSE` permanece ausente e `LicenseRef-Proprietary` inalterado; a investigação de CI é da Issue #4. **PREPUBLIC_GATE=FAIL**.


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

`PUB-01` permanece BLOCKER até scanner real/objetos/refs/superfícies/humano. `PUB-02` licença e titularidade, `PUB-03` CI Issue #4, `PUB-04` proteção de main, `PUB-05` integridade das dependências, `PUB-06` canal confidencial e `PUB-07` integração autorizada seguem pendentes. Nenhuma alteração de licença, visibilidade, proteção privilegiada ou merge foi autorizada. **PREPUBLIC_GATE=FAIL.**
