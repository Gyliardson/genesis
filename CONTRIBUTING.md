# Como contribuir com o GENESIS

GENESIS está em fase de pesquisa. A meta inicial é investigar políticas adaptativas de scheduling sob CPU/memória limitadas; o projeto **não** demonstrou vantagem de neuroevolução sobre baselines clássicas, nem validou controladores em produção.

## Antes de abrir PR

1. Consulte o README, as decisões/hipóteses em `docs/` e a Issue relevante. Para mudanças científicas, explicite qual hipótese ou invariante a proposta testa; não trate decisões `OPEN` ou `PROPOSED` como aceitas.
2. Discuta alterações de contrato, observações, custos experimentais ou comportamento de segurança antes de implementar. Mantenha o PR focalizado e vincule sua Issue. Não misture alterações de segurança com mudanças funcionais não relacionadas.
3. Execute em ambiente limpo e sem credenciais reais: `python -m pip install -e ".[dev]"`, `ruff check .` e `pytest -q`. A CI hash-locked do [PR #24](https://github.com/Gyliardson/genesis/pull/24) passou no GitHub-hosted Ubuntu 24.04/Python 3.11 no [run #41854692099](https://github.com/Gyliardson/genesis/actions/runs/41854692099), associado ao SHA `7a001740110666214858a3228094aa07313d9270`. Isso não comprova a execução dos comandos editable acima nem significa que a `main` já contenha esse workflow. Ao contribuir, confira o workflow, o HEAD e os checks vigentes; reporte falhas sem ocultá-las nem enfraquecer testes.
4. Registre como reproduzir, versões, ambiente, comandos, testes positivos/negativos e limitações. Para benchmarks, siga [o protocolo](docs/reproducibility.md): seeds, splits, baselines e informações observáveis devem ser comparáveis. Resultados negativos também devem ser reportados.
5. Nunca adicione arquivos secretos, chaves, dados pessoais, traces privados, checkpoints excessivos ou grandes artefatos binários ao Git. Use fixtures sintéticas e siga [SECURITY.md](SECURITY.md) para vulnerabilidades.

## Revisão e integridade científica

Uma policy deve escolher somente ações legalmente permitidas pelo ambiente, sem acesso a duração real futura ou outros estados ocultos. Corretude do simulador, legalidade de ações, ganho em treino, generalização held-out e utilidade real exigem evidências distintas. Descreva controles, custos de treino/inferência, fairness, starvation, incerteza estatística e falhas; não infira consciência, novidade científica ou superioridade a partir de uma demonstração.

## Licença e direitos

O mantenedor aprovou **Apache-2.0 para o código**; consulte [LICENSE](LICENSE). Antes de enviar uma contribuição destinada à incorporação ao projeto, confirme que você possui direitos para licenciá-la sob esses termos e declare claramente eventuais atribuições, materiais de terceiros ou condições distintas. Não adicione material de terceiros sem direitos de redistribuição comprovados; licenças de dados e artefatos científicos requerem avaliação própria. **O repositório permanece privado enquanto os gates de preparação pública não forem concluídos.**

Revisão técnica, checks verdes e discussão pública não autorizam merge em `main`; o mantenedor decide cada integração.
