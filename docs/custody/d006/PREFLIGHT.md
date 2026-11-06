# D006 — preflight A de identidade e host (somente inspeção)

**Escopo:** PR #28 registra o plano; o preflight propõe verificações antes de solicitar autorização de geração. **Não executa o gerador, não cria inputs A, não mede N=100.000 nem autoriza freeze/S1/benchmark/merge.**

O procedimento exige dois **checkouts separados e limpos**: PR28 custody HEAD b9f25b0fe4fd9390be05deec396ea1c799d5e83b tree b4f7b47720fc98fccbaec03782cb8811dc11cac7; PR27 generator HEAD 0399e842722e9bffe3063308e622830816744dc3 tree e692edb46a4fd7e0689c83e621c8b1346d4f3fe7. Não aceite checkout de merge sintético, branch móvel ou o PR novo como substituto. O preflight fixa hashes do plano (3305 bytes) e lock (926 bytes), compara bytes, Git objects e seis determinantes rastreados; não aceita digests fornecidos via CLI.

Requer CPython3.11.18, Ubuntu24.04 x86_64, sem PYTHONPATH; destino absoluto, ausente e fora dos checkouts; espaço livre observado mínimo 1 GiB e 32 inodes (triagem proposta, **não** prova de orçamento). A inspeção não reserva recursos e pode sofrer TOCTOU.

Exemplo documental, **não executar sem checkouts apropriados**:

    python3 docs/custody/d006/preflight.py \
      --custody-checkout /isolated/PR28-HEAD \
      --generator-checkout /isolated/PR27-HEAD \
      --output-destination /isolated/output/A-freeze

Em inconsistência: FAIL_CLOSED, exit 2, nenhum input. Em match: IDENTITY_AND_HOST_PREVIEW_PASS_ONLY, exit 0; ainda freeze_authorized=false, memory_limit_verified=false, wall_timeout_enforced=false, N100000_feasibility_proven=false.

**Gates restantes antes de qualquer freeze A:** (1) autorização humana distinta para os 16 inputs, SHA, destino e recursos; (2) launcher revisado com cgroup/RLIMIT e watchdog/process-group kill, quotas, no retry, audit/rollback; (3) avaliação de N100000 (RSS/tempo/disco/atomicidade/replay) e testes de falhas sintéticas; (4) atestar imports/determinantes até execução, revalidando imediatamente antes do primeiro job para mitigar TOCTOU. Um preview isolado **não substitui** a fronteira de execução. O holdout público não é cego. Nenhuma seleção de motor D006 foi feita.

tests/test_d006_preflight.py usa **Git repos sintéticos mínimos**, não os workloads A; testa checks positivos e negativos de hash, commit/tree, bytes rastreados, runtime/PYTHONPATH, destino, disco/inodes e JSON. A CI deve executar Ruff, pytest e pip check. O PASS não prova viabilidade nem autoridade experimental.
