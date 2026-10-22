#!/usr/bin/env bash
# Auditoria CONFIDENCIAL: executar somente em máquina autorizada.
# Não publica o conteúdo dos logs, relatórios ou nomes de refs.
set -Eeuo pipefail
umask 077

usage() { printf 'Uso: %s <URL-git-sem-credenciais> <diretorio-novo-privado>\n' "$0" >&2; }
if [ "$#" -ne 2 ]; then usage; exit 64; fi
repo_url=$1
out=$2

# Validar ANTES de qualquer chamada git ou criação de mirror. Jamais ecoar entrada inválida.
case "$repo_url" in
  https://*)
    authority=${repo_url#https://}; authority=${authority%%/*}
    if [[ "$authority" == *'@'* || ! "$authority" =~ ^[A-Za-z0-9.-]+(:[0-9]+)?$ || "$repo_url" == *'?'* || "$repo_url" == *'#'* ]]; then
      echo 'URL rejeitada: userinfo, query, fragmento ou autoridade inválida.' >&2; exit 64
    fi ;;
  ssh://git@*)
    authority=${repo_url#ssh://git@}; authority=${authority%%/*}
    if [[ ! "$authority" =~ ^[A-Za-z0-9.-]+(:[0-9]+)?$ || "$repo_url" == *'?'* || "$repo_url" == *'#'* ]]; then
      echo 'URL SSH rejeitada.' >&2; exit 64
    fi ;;
  git@*:*)
    authority=${repo_url#git@}; authority=${authority%%:*}
    if [[ ! "$authority" =~ ^[A-Za-z0-9.-]+$ || "$repo_url" == *'?'* || "$repo_url" == *'#'* ]]; then
      echo 'URL SSH rejeitada.' >&2; exit 64
    fi ;;
  /* | ./* | ../*)
    # Origem filesystem para teste ou espelho AUTORIZADO; exige caminho existente.
    if [ ! -d "$repo_url" ]; then echo 'Caminho de origem inexistente.' >&2; exit 64; fi ;;
  *) echo 'Protocolo Git não permitido (HTTPS sem userinfo, SSH agent ou pasta local).' >&2; exit 64 ;;
esac
if [ -e "$out" ] || [ -L "$out" ]; then
  echo 'Diretório de auditoria já existe; evidências não serão sobrescritas.' >&2; exit 73
fi
for bin in git gitleaks sha256sum; do
  command -v "$bin" >/dev/null || { echo "Ferramenta ausente: $bin" >&2; exit 69; }
done
mkdir -m 700 -- "$out"
chmod 700 -- "$out"
out=$(cd -- "$out" && pwd -P)
mirror="$out/mirror.git"

# Todo stdout/stderr potencialmente confidencial de comandos externos fica em arquivos 0600.
# O trap registra uma indicação privada e emite somente um erro genérico.
cleanup() {
  local status=$?
  trap - EXIT
  printf '%s\n' "$status" > "$out/audit-exit-code.private.txt"
  if [ "$status" -ne 0 ]; then
    echo 'AUDIT_NOT_PASSED: consultar evidências privadas; nenhuma conclusão de segurança.' >&2
  fi
}
trap cleanup EXIT

export GIT_TERMINAL_PROMPT=0
# Gitleaks config via ambiente nunca herda conteúdo não auditado; regras padrão
# continuam sujeitas a allowlists embutidas. Ver provenance.private.txt.
unset GITLEAKS_CONFIG GITLEAKS_CONFIG_TOML

git --version > "$out/git-version.private.txt" 2> "$out/git-version.stderr.private.txt"
gitleaks version > "$out/gitleaks-version.private.txt" 2> "$out/gitleaks-version.stderr.private.txt"
sha256sum "$(command -v gitleaks)" > "$out/gitleaks-binary.sha256.private.txt" 2> "$out/hash.stderr.private.txt"

# Sem pipefail/grep -q em produtor de help: SIGPIPE não gera falso negativo.
gitleaks git --help > "$out/gitleaks-help.private.txt" 2> "$out/gitleaks-help.stderr.private.txt"
gitleaks --help > "$out/gitleaks-root-help.private.txt" 2> "$out/gitleaks-root-help.stderr.private.txt"
for option in --log-opts --ignore-gitleaks-allow --gitleaks-ignore-path --report-path --redact; do
  if ! grep -F -- "$option" "$out/gitleaks-help.private.txt" "$out/gitleaks-root-help.private.txt" >/dev/null; then
    echo 'Scanner incompatível com flags de segurança exigidas.' >&2; exit 65
  fi
done
: > "$out/empty-ignore.private.txt"
cat > "$out/provenance.private.txt" <<'PROVENANCE'
GITLEAKS_CONFIG=unset
GITLEAKS_CONFIG_TOML=unset
Gitleaks configuration=embedded defaults from recorded binary version/SHA
Gitleaks ignore file=explicitly empty, stored privately
Gitleaks ignore comments=disabled via --ignore-gitleaks-allow
Gitleaks baseline=none
Gitleaks extra rule selection=none
Gitleaks builtin rule allowlists=possible; human inspection/second detector still required
Git patch format=git log -p -m --all --full-history (per-parent merge diffs)
No claim of complete server-side refs, forks, LFS or unreachable objects
PROVENANCE

# ls-remote captura SOMENTE refs anunciadas, não refs ocultas/efêmeras.
git ls-remote --refs "$repo_url" > "$out/remote-before.private.tsv" 2> "$out/remote-before.stderr.private.txt"
git clone --mirror --quiet -- "$repo_url" "$mirror" > "$out/clone.stdout.private.txt" 2> "$out/clone.stderr.private.txt"
# Refs PR podem não vir em clone --mirror; verificar após fetch adicional.
git -C "$mirror" fetch --quiet --no-tags origin \
  '+refs/heads/*:refs/heads/*' \
  '+refs/tags/*:refs/tags/*' \
  '+refs/pull/*/head:refs/audit/pulls/*/head' \
  '+refs/pull/*/merge:refs/audit/pulls/*/merge' \
  > "$out/fetch.stdout.private.txt" 2> "$out/fetch.stderr.private.txt"
git ls-remote --refs "$repo_url" > "$out/remote-after.private.tsv" 2> "$out/remote-after.stderr.private.txt"
git -C "$mirror" for-each-ref --format='%(objectname)%09%(refname)' > "$out/local.private.tsv" 2> "$out/refs.stderr.private.txt"

# Comparar refs anunciadas ANTES/DEPOIS e objeto local; refs não reconhecidas
# também são lacuna, nunca descartadas silenciosamente.
coverage_gap=0
if ! cmp -s "$out/remote-before.private.tsv" "$out/remote-after.private.tsv"; then
  echo 'Remote refs changed during scan: unstable/ephemeral snapshot' >> "$out/coverage-gaps.private.txt"
  coverage_gap=1
fi
while IFS=$'\t' read -r oid ref; do
  [ -n "$ref" ] || continue
  case "$ref" in
    refs/heads/* | refs/tags/*) local_ref="$ref" ;;
    refs/pull/*/head | refs/pull/*/merge)
      local_ref="$ref"
      if ! git -C "$mirror" show-ref --verify --quiet "$local_ref"; then
        local_ref="refs/audit/pulls/${ref#refs/pull/}"
      fi ;;
    *) echo "UNCLASSIFIED $ref" >> "$out/coverage-gaps.private.txt"; coverage_gap=1; continue ;;
  esac
  local_oid=$(git -C "$mirror" show-ref --verify -s "$local_ref" 2> /dev/null || true)
  if [ "$oid" != "$local_oid" ] || ! git -C "$mirror" cat-file -e "$oid^{object}" 2> /dev/null; then
    echo "MISSING_OR_CHANGED $ref" >> "$out/coverage-gaps.private.txt"
    coverage_gap=1
  fi
done < "$out/remote-before.private.tsv"

git -C "$mirror" rev-list --all --count > "$out/reachable-commit-count.private.txt" 2> "$out/revlist.stderr.private.txt"
git -C "$mirror" rev-list --objects --all > "$out/reachable-objects.private.txt" 2> "$out/objects.stderr.private.txt"
# 0 exit code de fsck NÃO significa zero objetos inalcançáveis.
git -C "$mirror" fsck --full --no-reflogs --unreachable > "$out/fsck.private.txt" 2> "$out/fsck.stderr.private.txt"
if grep -E '(^| )(unreachable|dangling)( |$)' "$out/fsck.private.txt" "$out/fsck.stderr.private.txt" >/dev/null; then
  echo 'UNREACHABLE_OR_DANGLING_OBJECTS: review private fsck output' >> "$out/coverage-gaps.private.txt"
  coverage_gap=1
fi
# Não presumir cobertura de conteúdo LFS remoto nem dos forks independentes.
printf 'GIT_LFS=UNVERIFIED: pointers/history and remote LFS objects require separate authorized audit\nFORKS=UNVERIFIED: enumerate and scan independently if exposed\nHIDDEN_REFS=UNVERIFIED: server may not advertise all refs\n' >> "$out/coverage-gaps.private.txt"
# A coleta pode ser incompleta: executar o detector sobre o subconjunto alcançável,
# mas nunca retornar PASS se houver divergências/unreachable. Preservar achados.

# Flags testadas pelo preflight; scanner lida com -m (merge diff por parent).
# Saída do scanner e relatório 100% redigidos, NUNCA stdout/stderr do terminal.
set +e
gitleaks git --redact=100 --ignore-gitleaks-allow \
  --gitleaks-ignore-path "$out/empty-ignore.private.txt" \
  --log-opts='--all --full-history -m' \
  --report-format=json --report-path "$out/gitleaks.redacted.private.json" \
  "$mirror" > "$out/gitleaks.stdout.private.txt" 2> "$out/gitleaks.stderr.private.txt"
scan_status=$?
set -e
printf '%s\n' "$scan_status" > "$out/gitleaks-exit-code.private.txt"
if [ "$scan_status" -ne 0 ]; then
  echo 'SCAN_NOT_PASSED: resultado ou erro do detector demanda triagem confidencial.' >&2
  exit "$scan_status"
fi
if [ "$coverage_gap" -ne 0 ]; then
  echo 'COVERAGE_UNVERIFIED: refs/objetos divergentes; análise privada necessária.' >&2
  exit 66
fi
echo 'Scan de patches de objetos alcançáveis anunciado sem finding; Git LFS/forks/refs ocultas/superfícies GitHub ainda UNVERIFIED.'
