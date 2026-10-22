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
