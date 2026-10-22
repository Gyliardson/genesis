# Como contribuir com o GENESIS

GENESIS está em fase de pesquisa. A meta inicial é investigar políticas adaptativas de scheduling sob CPU/memória limitadas; o projeto **não** demonstrou vantagem de neuroevolução sobre baselines clássicas, nem validou controladores em produção.

## Antes de abrir PR

1. Consulte o README, as decisões/hipóteses em `docs/` e a Issue relevante. Para mudanças científicas, explicite qual hipótese ou invariante a proposta testa; não trate decisões `OPEN` ou `PROPOSED` como aceitas.
2. Discuta alterações de contrato, observações, custos experimentais ou comportamento de segurança antes de implementar. Mantenha o PR focalizado e vincule sua Issue. Não misture alterações de segurança com mudanças funcionais não relacionadas.
3. Execute em ambiente limpo e sem credenciais reais: `python -m pip install -e ".[dev]"`, `ruff check .` e `pytest -q`. **A CI existente possui falhas ainda não diagnosticadas** (Issue #4); reporte falhas sem ocultá-las ou enfraquecer testes.
4. Registre como reproduzir, versões, ambiente, comandos, testes positivos/negativos e limitações. Para benchmarks, siga [o protocolo](docs/reproducibility.md): seeds, splits, baselines e informações observáveis devem ser comparáveis. Resultados negativos também devem ser reportados.
5. Nunca adicione arquivos secretos, chaves, dados pessoais, traces privados, checkpoints excessivos ou grandes artefatos binários ao Git. Use fixtures sintéticas e siga [SECURITY.md](SECURITY.md) para vulnerabilidades.

## Revisão e integridade científica

Uma policy deve escolher somente ações legalmente permitidas pelo ambiente, sem acesso a duração real futura ou outros estados ocultos. Corretude do simulador, legalidade de ações, ganho em treino, generalização held-out e utilidade real exigem evidências distintas. Descreva controles, custos de treino/inferência, fairness, starvation, incerteza estatística e falhas; não infira consciência, novidade científica ou superioridade a partir de uma demonstração.

## Licença e direitos

**Não há licença open source aprovada nesta fase.** O projeto está marcado `LicenseRef-Proprietary` e não possui `LICENSE`. Antes de aceitar contribuições distribuíveis, o mantenedor deverá definir licença, titularidade e condições de entrada de contribuições. Não adicione material de terceiros sem direitos de redistribuição comprovados; licenças de dados e artefatos requerem avaliação própria. A submissão de um PR não altera automaticamente o status jurídico do repositório.

Revisão técnica, checks verdes e discussão pública não autorizam merge em `main`; o mantenedor decide cada integração.
