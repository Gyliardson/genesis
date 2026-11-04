#!/usr/bin/env bash
# Auditoria CONFIDENCIAL: executar somente em máquina autorizada.
# Não publica o conteúdo dos logs, relatórios ou nomes de refs.
set -Eeuo pipefail
umask 077

usage() { printf 'Uso: %s <URL-git-sem-credenciais> <diretorio-novo-privado> <manifesto-sha256-prevalidado>\n' "$0" >&2; }
if [ "$#" -ne 3 ]; then usage; exit 64; fi
repo_url=$1
out=$2
trust_manifest=$3

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
for bin in git sha256sum python3; do
  command -v "$bin" >/dev/null || { echo "Ferramenta ausente: $bin" >&2; exit 69; }
done
mkdir -m 700 -- "$out"
chmod 700 -- "$out"
out=$(cd -- "$out" && pwd -P)
mirror="$out/mirror.git"

# Em certos ambientes (incluindo Codespaces), a criacao por redirecionamento
# Bash ignorou umask 077. Criar arquivos VAZIOS com mode 0600 e verificar
# ANTES de qualquer gravacao sensivel; redirecionamentos posteriores truncam
# arquivos existentes sem alterar a permissao. Ambiente e diretório exclusivos.
python3 - "$out" <<'PY_PRIVFILE'
import os
import stat
import sys
from pathlib import Path

root = Path(sys.argv[1])
names = (
    'audit-exit-code.private.txt',
    'clone.stderr.private.txt',
    'clone.stdout.private.txt',
    'coverage-gaps.private.txt',
    'empty-ignore.private.txt',
    'fetch.stderr.private.txt',
    'fetch.stdout.private.txt',
    'fsck.private.txt',
    'fsck.stderr.private.txt',
    'git-version.private.txt',
    'git-version.stderr.private.txt',
    'gitleaks-binary.sha256.private.txt',
    'gitleaks-exit-code.private.txt',
    'gitleaks-help.private.txt',
    'gitleaks-help.stderr.private.txt',
    'gitleaks-root-help.private.txt',
    'gitleaks-root-help.stderr.private.txt',
    'gitleaks-verified-digest.private.txt',
    'gitleaks-version.private.txt',
    'gitleaks-version.stderr.private.txt',
    'gitleaks.redacted.private.json',
    'gitleaks.stderr.private.txt',
    'gitleaks.stdout.private.txt',
    'hash.stderr.private.txt',
    'local.private.tsv',
    'objects.stderr.private.txt',
    'provenance.private.txt',
    'reachable-commit-count.private.txt',
    'reachable-objects.private.txt',
    'refs.stderr.private.txt',
    'remote-after.private.tsv',
    'remote-after.stderr.private.txt',
    'remote-before.private.tsv',
    'remote-before.stderr.private.txt',
    'revlist.stderr.private.txt',
    'scanner-source.private.txt',
    'status.private.env',
)
try:
    for name in names:
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        fd = os.open(root / name, flags, 0o600)
        try:
            if stat.S_IMODE(os.fstat(fd).st_mode) != 0o600:
                raise RuntimeError("private output mode mismatch")
        finally:
            os.close(fd)
except (OSError, RuntimeError):
    raise SystemExit("PRIVATE_OUTPUT_PRECREATE_FAILED")
PY_PRIVFILE


# Estados machine-readable são sempre bloqueantes para publicação.
scan_status=NOT_RUN
coverage_status=NOT_RUN
human_status=NOT_RUN
lfs_status=UNVERIFIED
forks_status=UNVERIFIED
hidden_refs_status=UNVERIFIED
github_surfaces_status=UNVERIFIED

# Todo stdout/stderr potencialmente confidencial de comandos externos fica em arquivos 0600.
# O trap registra uma indicação privada e emite somente um erro genérico.
cleanup() {
  local status=$?
  trap - EXIT
  if [ "$status" -eq 0 ]; then status=66; fi
  printf 'SCAN_STATUS=%s\nCOVERAGE_STATUS=%s\nHUMAN_REVIEW_STATUS=%s\nGIT_LFS_STATUS=%s\nFORKS_STATUS=%s\nHIDDEN_REFS_STATUS=%s\nGITHUB_SURFACES_STATUS=%s\nAUDIT_STATUS=BLOCKED\nPREPUBLIC_GATE=FAIL\nEXIT_STATUS=%s\n' \
    "$scan_status" "$coverage_status" "$human_status" \
    "$lfs_status" "$forks_status" "$hidden_refs_status" \
    "$github_surfaces_status" "$status" > "$out/status.private.env"
  printf '%s\n' "$status" > "$out/audit-exit-code.private.txt"
  echo 'AUDIT_BLOCKED: PREPUBLIC_GATE=FAIL; verifique evidências somente em diretório privado.' >&2
  exit "$status"
}
trap cleanup EXIT

# TRUST-ANCHOR: manifesto preparado ANTES do trabalho pelo responsável de segurança,
# fora do checkout, cujo SHA foi obtido de fonte independente identificada e aprovada.
# Manifesto exige quatro linhas LITERAIS (não é um script e nunca é "source"):
# SHA256=<64 hex>
# SOURCE=https://github.com/gitleaks/gitleaks/releases/...
# DIGEST_SOURCE=<referência verificável independente da distribuição>
# VERIFIED_BY=<identificador do responsável que validou a referência>
if [ ! -f "$trust_manifest" ] || [ -L "$trust_manifest" ] ||
   [ "$(stat -c '%a' "$trust_manifest" 2>/dev/null)" != 600 ]; then
  echo 'TRUST_NOT_VERIFIED: manifesto ausente, symlink ou permissões diferentes de 0600.' >&2
  exit 67
fi
mapfile -t trust_lines < "$trust_manifest"
if [ "${#trust_lines[@]}" -ne 4 ] ||
   [[ ! "${trust_lines[0]}" =~ ^SHA256=[a-fA-F0-9]{64}$ ]] ||
   [[ ! "${trust_lines[1]}" =~ ^SOURCE=https://github[.]com/gitleaks/gitleaks/releases/.+$ ]] ||
   [[ ! "${trust_lines[2]}" =~ ^DIGEST_SOURCE=[^[:space:]]{8,}$ ]] ||
   [[ ! "${trust_lines[3]}" =~ ^VERIFIED_BY=[A-Za-z0-9_.@:-]{3,}$ ]]; then
  echo 'TRUST_NOT_VERIFIED: manifesto inválido ou procedência não identificada.' >&2
  exit 67
fi
expected_digest="${trust_lines[0]#SHA256=}"
expected_digest="${expected_digest,,}"
candidate=$(type -P gitleaks || true)
if [ -z "$candidate" ] || [ ! -f "$candidate" ] || [ ! -x "$candidate" ]; then
  echo 'SCANNER_NOT_AVAILABLE: nenhuma execução de binário desconhecido.' >&2
  exit 69
fi
# Copiar para diretório privado: verificar o MESMO objeto que será executado,
# reduzindo troca de path/arquivo entre verificação e invocação.
scanner="$out/gitleaks.verified"
cp -- "$candidate" "$scanner"
chmod 500 "$scanner"
digest_actual=$(sha256sum "$scanner" | cut -d ' ' -f1)
if [ "$digest_actual" != "$expected_digest" ]; then
  echo 'TRUST_NOT_VERIFIED: checksum divergente, execução bloqueada.' >&2
  exit 67
fi
printf '%s\n' "$digest_actual" > "$out/gitleaks-verified-digest.private.txt"
printf '%s\n' "${trust_lines[1]}" "${trust_lines[2]}" "${trust_lines[3]}" > "$out/scanner-source.private.txt"

export GIT_TERMINAL_PROMPT=0
# Gitleaks config via ambiente nunca herda conteúdo não auditado; regras padrão
# continuam sujeitas a allowlists embutidas. Ver provenance.private.txt.
unset GITLEAKS_CONFIG GITLEAKS_CONFIG_TOML

git --version > "$out/git-version.private.txt" 2> "$out/git-version.stderr.private.txt"
"$scanner" version > "$out/gitleaks-version.private.txt" 2> "$out/gitleaks-version.stderr.private.txt"
sha256sum "$scanner" > "$out/gitleaks-binary.sha256.private.txt" 2> "$out/hash.stderr.private.txt"

# Sem pipefail/grep -q em produtor de help: SIGPIPE não gera falso negativo.
"$scanner" git --help > "$out/gitleaks-help.private.txt" 2> "$out/gitleaks-help.stderr.private.txt"
"$scanner" --help > "$out/gitleaks-root-help.private.txt" 2> "$out/gitleaks-root-help.stderr.private.txt"
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
coverage_status=UNVERIFIED
if [ ! -s "$out/remote-before.private.tsv" ]; then
  echo 'EMPTY_REMOTE_ADVERTISEMENT: incomplete reference inventory' >> "$out/coverage-gaps.private.txt"
  coverage_gap=1
fi
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
( cd -- "$out" && "$scanner" git --redact=100 --ignore-gitleaks-allow \
  --gitleaks-ignore-path "$out/empty-ignore.private.txt" \
  --log-opts='--all --full-history -m' \
  --report-format=json --report-path "$out/gitleaks.redacted.private.json" \
  "$mirror" ) > "$out/gitleaks.stdout.private.txt" 2> "$out/gitleaks.stderr.private.txt"
scanner_exit=$?
set -e
if [ "$scanner_exit" -eq 0 ]; then scan_status=PASS
elif [ "$scanner_exit" -eq 1 ]; then scan_status=FINDINGS
else scan_status=ERROR
fi
printf '%s\n' "$scanner_exit" > "$out/gitleaks-exit-code.private.txt"
if [ "$scanner_exit" -ne 0 ]; then
  echo 'SCAN_NOT_PASSED: resultado ou erro do detector demanda triagem confidencial.' >&2
  exit "$scanner_exit"
fi
if [ "$coverage_gap" -ne 0 ]; then
  coverage_status=FAIL
  echo 'COVERAGE_UNVERIFIED: refs/objetos divergentes; análise privada necessária.' >&2
  exit 66
fi
echo 'SCAN_STATUS=PASS; COVERAGE_STATUS=UNVERIFIED; HUMAN_REVIEW_STATUS=NOT_RUN; PREPUBLIC_GATE=FAIL.'
exit 66
