# Política de segurança (pré-publicação)

GENESIS é um laboratório experimental, sem serviços de produção oficialmente suportados. Não presumir isolamento, segurança de um controlador ou aptidão para workloads reais a partir de um resultado em simulação.

## Divulgação responsável

- **Não publique** tokens, credenciais, logs sensíveis, dados privados, proof-of-concept explorável ou detalhes de vulnerabilidades em Issues, PRs, Discussions e comentários públicos.
- Quando o recurso estiver efetivamente habilitado, use **Private vulnerability reporting** na aba Security do GitHub para relatos confidenciais. **A disponibilidade desse recurso não está confirmada.**
- Se não houver canal privado habilitado, solicite ao mantenedor, pelo perfil do proprietário no GitHub, uma forma de contato privado **sem incluir detalhes sensíveis** no primeiro contato. Não presuma SLA ou resposta garantida.
- Informe, pelo canal privado, versão/commit, impacto, pré-condições, reprodução mínima com dados sintéticos e sugestão de contenção. Evite publicar tokens mesmo nesse relato; comunique presença e categoria, não o valor.
- Se uma credencial tiver sido exposta, interrompa a preparação pública e avalie revogação/rotação com o titular autorizado. Reescrita de histórico não substitui rotação; ambas exigem avaliação/autorizações próprias.

## Limites e política de contribuições

Workflows de pull requests de forks devem executar sem segredos privilegiados, com `GITHUB_TOKEN` de leitura mínima e sem `pull_request_target` para código não confiável. Nenhum resultado de pesquisa deve acionar shell arbitrário, contornar quotas ou administrar infraestrutura de produção.

Reportes de dependências vulneráveis, riscos de runner, acesso indevido a Actions/logs e exposição de dados também pertencem ao escopo da revisão de segurança. A confirmação do recebimento, triagem e divulgação coordenada será decidida pelo mantenedor caso a caso; esta política não promete prazos específicos.
