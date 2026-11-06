# D006 — custódia técnica do plano A (operador único)

**Objeto:** repositório público `Gyliardson/genesis`, decisão metodológica [D1–D3 ratificada](https://github.com/Gyliardson/genesis/issues/5#issuecomment-6690931333). Este pacote é um **registro anterior à execução**, não um disparo nem uma autorização de freeze, S1, benchmarks ou merge.

- `expected_plan_A_v1.json`: 16 descriptors canônicos ordenados, **3305 bytes**, SHA256 `77934cf30e3937a9f339f3f6cc4144b9fa67ae2531c0185a8565acd5d0e789ba`; nenhum job/trace.
- `lock.json`: vincula a identidade do plano ao **PR27 HEAD `0399e842722e9bffe3063308e622830816744dc3`**, Git tree `e692edb46a4fd7e0689c83e621c8b1346d4f3fe7`, base PR26 e ambiente CPython 3.11.18/Ubuntu 24.04.
- `verify_plan.py`: valida plano/lock com stdlib **sem importar o gerador ou produzir jobs**. Executar `python3 docs/custody/d006/verify_plan.py --self-test` (positivos e negativos).

**Auditoria temporal:** referenciar o **SHA exato do commit GitHub** contendo estes bytes + os timestamps **servidor** do PR e do checkpoint de Issue #5; confirmar via leitura posterior os mesmos blobs. Não depender do timestamp autor/committer editável nem de branch móvel. O GitHub preserva evidência útil de precedência e versões, mas **não fornece por si só timestamp criptograficamente incontestável**, assinatura independente ou separação de pessoas. Esta distinção é assumida para um laboratório individual; não declarar `external human APPROVED`.

**Fail closed:** qualquer mudança do plano, HEAD/tree/base, arquivos determinantes, deps ou runtime exige novo lock/review. Antes do futuro input-only freeze será necessário conferir no host real a origem dos imports, arquivos determinantes e versão Python e revisar limites de memória/disco/tempo para N=100000. Obter autorização humana **específica** para gerar os 16 A; `verify_plan.py` **não** executa `freeze_a`. Guardas da reserva pública `910000..919999` não a tornam holdout cego. D4/D5/D6 e S1 seguem pendentes.
