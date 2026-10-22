#!/usr/bin/env bash
# Execute somente em estação autorizada, com credenciais configuradas fora da linha de comando.
# Saída contém metadados sensíveis; não publicar o diretório de auditoria.
set -Eeuo pipefail
umask 077
if [ "$#" -ne 2 ]; then
  echo "Uso: $0 <URL-git-autenticável> <diretório-novo-privado>" >&2
  exit 64
fi
repo_url="$1"
out="$2"
if [ -e "$out" ]; then
  echo "Diretório de saída já existe; use outro para evitar sobrescrever evidências." >&2
  exit 73
fi
for bin in git gitleaks sha256sum; do
  command -v "$bin" >/dev/null || { echo "Falta ferramenta: $bin" >&2; exit 69; }
done
mkdir -m 700 -p "$out"
git --version > "$out/git-version.txt"
gitleaks version > "$out/gitleaks-version.txt"
sha256sum "$(command -v gitleaks)" > "$out/gitleaks-binary.sha256"
if ! gitleaks git --help | grep -q -- '--log-opts'; then
  echo "Versão do Gitleaks incompatível com 'git --log-opts'; abortado." >&2
  exit 65
fi
git clone --mirror --quiet "$repo_url" "$out/mirror.git"
# Captura branches, tags e refs PR anunciadas pelo servidor; refs não transferidas seguem fora de cobertura.
git -C "$out/mirror.git" fetch --quiet --no-tags origin   '+refs/heads/*:refs/heads/*'   '+refs/tags/*:refs/tags/*'   '+refs/pull/*/head:refs/audit/pulls/*/head'   '+refs/pull/*/merge:refs/audit/pulls/*/merge'
git -C "$out/mirror.git" for-each-ref --format='%(refname) %(objectname)' > "$out/refs.private.txt"
git -C "$out/mirror.git" rev-list --all --count > "$out/reachable-commit-count.txt"
git -C "$out/mirror.git" rev-list --objects --all > "$out/reachable-objects.private.txt"
git -C "$out/mirror.git" fsck --full --no-reflogs --unreachable > "$out/fsck.private.txt" 2>&1
set +e
gitleaks git --redact=100 --log-opts="--all --full-history"   --report-format=json --report-path "$out/gitleaks.redacted.private.json"   "$out/mirror.git" > "$out/gitleaks.execution.private.log" 2>&1
status=$?
set -e
printf '%s\n' "$status" > "$out/gitleaks-exit-code.txt"
if [ "$status" -ne 0 ]; then
  echo "SCAN NÃO APROVADO: findings ou falha de ferramenta. Fazer triagem local privada; não publicar relatório." >&2
  exit "$status"
fi
echo "Varredura Gitleaks sem finding reportado sobre objetos alcançáveis baixados. Outras superfícies ainda UNVERIFIED."
