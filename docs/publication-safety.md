# Publicação pública: procedimento de segurança

**Esta é uma política de preparação, não uma autorização de divulgação.** O registro de gates e evidências atuais permanece na [Issue #23](https://github.com/Gyliardson/genesis/issues/23). Não declarar `PREPUBLIC_GATE=PASS` apenas porque um PR foi criado.

## Gate antes de mudar visibilidade

1. Inventariar todas as refs, commits alcançáveis e objetos sensíveis; executar scanner confiável no **histórico completo** (por exemplo, `gitleaks git --log-opts="--all" .` em clone autorizado, validando sintaxe/versão da ferramenta), revisar achados redigidos e rodar revisão humana. Cobrir também Issues, PRs, comentários, reviews, anexos, Checks/annotations, Actions/logs e artefatos, inclusive referências fora do Git. Se alguma superfície não for auditável, classificar **UNVERIFIED**, não PASS.
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
bash scripts/audit-public-readiness.sh 'https://github.com/Gyliardson/genesis.git' "$HOME/genesis-private-audit-$(date +%Y%m%d)"
```

O script registra versão e hash binário do scanner, `refs`, quantidade de commits, lista de objetos alcançáveis, `git fsck` e Gitleaks com `--all --full-history`. Captura as refs remotas de branches/tags e tenta `refs/pull/*/{head,merge}`. Não há allowlists ou baselines para suprimir resultados; saída e relatórios ficam **privados**. Código de saída diferente de zero interrompe o gate, inclusive achado confirmado ou erro de ferramenta. Triar falsos positivos separadamente sem copiar segredos em GitHub.

**Cobertura negativa e limites:** scan de patch Git não verifica semanticamente toda propriedade/dado pessoal, blobs inacessíveis ao servidor, objetos dangling não anunciados, refs ocultas/não baixadas, arquivos Git LFS não obtidos, dados de forks independentes, caches, snapshots de terceiros nem conteúdo de Issues/PR/Actions. `git fsck` em clone verifica somente o conjunto de objetos efetivamente transferidos. Registrar SHA/refs e eventuais falhas de fetch; não chamar varredura completa sem revisão dessas lacunas.

### Materiais externos ao Git — coleta privada e verificação humana

Exige GitHub CLI autenticada com escopo de **leitura** e acesso a cada superfície. Nunca anexar dumps brutos à Issue/PR:

```bash
umask 077
mkdir -m 700 -p "$HOME/genesis-audit-surfaces"
cd "$HOME/genesis-audit-surfaces"
gh auth status
gh api --paginate 'repos/Gyliardson/genesis/issues?state=all&per_page=100' > issues.private.json
gh api --paginate 'repos/Gyliardson/genesis/issues/comments?per_page=100' > issue-comments.private.json
gh api --paginate 'repos/Gyliardson/genesis/pulls?state=all&per_page=100' > pulls.private.json
gh api --paginate 'repos/Gyliardson/genesis/pulls/comments?per_page=100' > inline-review-comments.private.json
gh api --paginate 'repos/Gyliardson/genesis/actions/runs?per_page=100' > actions-runs.private.json
```

Para cada PR enumerado, coletar separadamente `gh api repos/Gyliardson/genesis/pulls/NUM/reviews` e `gh api repos/Gyliardson/genesis/issues/NUM/comments`; para cada run enumerado, `gh api repos/Gyliardson/genesis/actions/runs/ID/jobs`, `gh run view ID --log` (somente arquivo privado) e `gh api repos/Gyliardson/genesis/actions/runs/ID/artifacts`; para cada check-run obtido por `gh api repos/Gyliardson/genesis/commits/SHA/check-runs`, consultar `gh api repos/Gyliardson/genesis/check-runs/CHECK_ID/annotations`. Enumerar pages e preservar status HTTP: **404/403, steps ausentes ou 0 artifacts não significam PASS**. Revisar links `user-attachments`/uploads, imagens, Markdown, releases/tags, Discussions, caches, LFS, URLs externas e referências a forks/manual screenshots sob acesso autorizado. Guardar textos, logs e anexos em diretório 0700 e revisá-los com detector de padrões **e** julgamento humano; dados de terceiros e dados pessoais exigem análise semântica e de direitos. Nenhum desses dumps foi obtido por este procedimento apenas por estar documentado.

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
