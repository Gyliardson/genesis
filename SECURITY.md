# Política de segurança (pré-publicação)

GENESIS é um laboratório experimental, sem serviços de produção oficialmente suportados. Não presumir isolamento, segurança de um controlador ou aptidão para workloads reais a partir de um resultado em simulação.

## Divulgação responsável

- **Não publique** tokens, credenciais, logs sensíveis, dados privados, proof-of-concept explorável ou detalhes de vulnerabilidades em Issues, PRs, Discussions e comentários públicos.
- Quando o recurso estiver efetivamente habilitado, use **Private vulnerability reporting** na aba Security do GitHub para relatos confidenciais. **A disponibilidade desse recurso não está confirmada.**
- **PUB-06 permanece ABERTO:** não foi verificado um canal confidencial operacional. A possibilidade de contatar o perfil público do proprietário não é, por si, um canal privado. Enquanto não houver canal validado, **não envie o relato, PoC, anexos ou evidências sensíveis por Issues, PRs ou mensagens públicas**. Um primeiro contato estritamente sem detalhes pode somente solicitar um endereço/canal seguro; não equivale a receber um reporte. Não presuma SLA.
- Informe, pelo canal privado, versão/commit, impacto, pré-condições, reprodução mínima com dados sintéticos e sugestão de contenção. Evite publicar tokens mesmo nesse relato; comunique presença e categoria, não o valor.
- Se uma credencial tiver sido exposta, interrompa a preparação pública e avalie revogação/rotação com o titular autorizado. Reescrita de histórico não substitui rotação; ambas exigem avaliação/autorizações próprias.

## Limites e política de contribuições

Workflows de pull requests de forks devem executar sem segredos privilegiados, com `GITHUB_TOKEN` de leitura mínima e sem `pull_request_target` para código não confiável. Nenhum resultado de pesquisa deve acionar shell arbitrário, contornar quotas ou administrar infraestrutura de produção.

Reportes de dependências vulneráveis, riscos de runner, acesso indevido a Actions/logs e exposição de dados também pertencem ao escopo da revisão de segurança. A confirmação do recebimento, triagem e divulgação coordenada será decidida pelo mantenedor caso a caso; esta política não promete prazos específicos.

## Gate operacional do canal (PUB-06)

Antes de convidar reports públicos, o mantenedor deve configurar e comprovar um canal confidencial. Opção preferida, **somente quando o repositório for público e o recurso estiver disponível**: GitHub **Settings > Security and quality > Advanced Security > Private vulnerability reporting > Enable**. Isso é uma **instrução futura**, não uma configuração executada/autorizada nesta remediação.

Verificar com conta autorizada: `gh api repos/Gyliardson/genesis/private-vulnerability-reporting --jq .enabled` (resposta booleana `true`), confirmar que um pesquisador elegível visualiza **Security / Report a vulnerability**, que o formulário privado está acessível e que a notificação/triagem chega ao mantenedor sem publicação do conteúdo. Não criar um reporte real com segredo para testar. `false`, 403, 404, ferramenta indisponível ou só existir `SECURITY.md` **não** constituem PASS.

Alternativa: endereço/portal privado definido expressamente pelo operador, acessível ao público-alvo e **testado ponta a ponta com uma mensagem sintética**, com proprietário, controle de acesso e fluxo de triagem. Não inventar e-mail, SLA ou chave PGP. Registrar a comprovação sem expor endereços privados, tokens ou conteúdos. Até confirmação: **PUB-06=UNVERIFIED / canal não estabelecido**.
