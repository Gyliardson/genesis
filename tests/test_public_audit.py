"""Offline deterministic security regressions for the public-readiness audit wrapper."""
import hashlib
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / 'scripts' / 'audit-public-readiness.sh'
FAKE = 'SYNTHETIC_MERGE_ONLY_MARKER_5a938bad4b72'


def run(*args, check=True, cwd=None, env=None):
    p = subprocess.run(args, cwd=cwd, env=env, text=True, capture_output=True)
    if check and p.returncode:
        raise AssertionError(f'command failed (rc={p.returncode}): {args[0]} {args[1:3]}')
    return p


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='genesis-audit-test-')
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.source = self.root / 'source'
        run('git', 'init', '-q', '-b', 'main', str(self.source))
        run('git', 'config', 'user.email', 'synthetic@example.invalid', cwd=self.source)
        run('git', 'config', 'user.name', 'Synthetic Fixture', cwd=self.source)
        (self.source / 'config.txt').write_text('base\n')
        run('git', 'add', '.', cwd=self.source)
        run('git', 'commit', '-qm', 'init', cwd=self.source)
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        g = self.bin / 'gitleaks'
        g.write_text('''#!/usr/bin/env python3
import os, sys, subprocess
args = sys.argv[1:]
if args == ['version']:
    print('test-double-0.1'); sys.exit(0)
if '--help' in args:
    print('--log-opts --ignore-gitleaks-allow --gitleaks-ignore-path --report-path --redact')
    for _ in range(2000): print('extra-help-line')
    sys.exit(0)
if not args or args[0] != 'git': sys.exit(3)
assert '--ignore-gitleaks-allow' in args
assert '--all --full-history -m' in ' '.join(args)
assert '--gitleaks-ignore-path' in args
assert 'GITLEAKS_CONFIG' not in os.environ
assert 'GITLEAKS_CONFIG_TOML' not in os.environ
repo = args[-1]
assert os.getcwd() == os.path.dirname(repo)
proc = subprocess.run(['git', '-C', repo, 'log', '-p', '-m', '--all', '--full-history'], text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
print('PRIVATE_SCANNER_OUTPUT_DO_NOT_STREAM')
if proc.returncode: sys.exit(3)
if 'SYNTHETIC_MERGE_ONLY_MARKER_5a938bad4b72' in proc.stdout: sys.exit(1)
sys.exit(0)
''')
        g.chmod(0o700)
        self.manifest = self.root / 'trusted-scanner.manifest'
        digest = hashlib.sha256(g.read_bytes()).hexdigest()
        # TEST ONLY: declarations are synthetic; not authenticated upstream claims.
        self.manifest.write_text(
            f'SHA256={digest}\n'
            'SOURCE=https://github.com/gitleaks/gitleaks/releases/tag/TEST-FIXTURE\n'
            'DIGEST_SOURCE=https://github.com/gitleaks/gitleaks/releases/tag/TEST-FIXTURE\n'
            'VERIFIED_BY=synthetic-fixture\n'
        )
        self.manifest.chmod(0o600)
        self.env = dict(os.environ, PATH=str(self.bin) + os.pathsep + os.environ['PATH'])

    def scan(self, source=None, out=None, manifest=None):
        return run('bash', str(SCRIPT), str(source or self.source),
                   str(out or self.root/'out'), str(manifest or self.manifest),
                   check=False, env=self.env)

    def test_no_finding_and_private_permissions(self):
        result = self.scan()
        self.assertEqual(result.returncode, 66, result.stderr)
        self.assertNotIn('PRIVATE_SCANNER_OUTPUT_DO_NOT_STREAM', result.stdout + result.stderr)
        self.assertEqual(stat.S_IMODE((self.root/'out').stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.root/'out/gitleaks.stdout.private.txt').stat().st_mode), 0o600)
        # Todos os artefatos privados (inclusive relatorios e status) sao
        # precriados em 0600, nao apenas stdout. Nao relaxar para 0646/0666.
        private_files = [p for p in (self.root/'out').iterdir()
                         if '.private.' in p.name]
        self.assertGreaterEqual(len(private_files), 30)
        for p in private_files:
            with self.subTest(path=p.name):
                self.assertTrue(p.is_file())
                self.assertEqual(stat.S_IMODE(p.stat().st_mode), 0o600)

        self.assertIn('PRIVATE_SCANNER_OUTPUT_DO_NOT_STREAM', (self.root/'out/gitleaks.stdout.private.txt').read_text())
        self.assertEqual((self.root/'out/gitleaks-exit-code.private.txt').read_text().strip(), '0')
        self.assertIn('GIT_LFS=UNVERIFIED', (self.root/'out/coverage-gaps.private.txt').read_text())
        self.assertIn('GITLEAKS_CONFIG=unset', (self.root/'out/provenance.private.txt').read_text())
        status = (self.root/'out/status.private.env').read_text()
        for field in ('SCAN_STATUS=PASS', 'COVERAGE_STATUS=UNVERIFIED',
                      'HUMAN_REVIEW_STATUS=NOT_RUN', 'GIT_LFS_STATUS=UNVERIFIED',
                      'FORKS_STATUS=UNVERIFIED', 'HIDDEN_REFS_STATUS=UNVERIFIED',
                      'GITHUB_SURFACES_STATUS=UNVERIFIED', 'PREPUBLIC_GATE=FAIL',
                      'AUDIT_STATUS=BLOCKED', 'EXIT_STATUS=66'):
            self.assertIn(field + '\n', status)

    def test_merge_resolution_only_is_detected(self):
        run('git', 'checkout', '-qb', 'feature', cwd=self.source)
        (self.source / 'config.txt').write_text('feature\n')
        run('git', 'commit', '-qam', 'feature edit', cwd=self.source)
        run('git', 'checkout', '-q', 'main', cwd=self.source)
        (self.source / 'config.txt').write_text('main\n')
        run('git', 'commit', '-qam', 'main edit', cwd=self.source)
        merge = run('git', 'merge', '--no-commit', '--no-ff', 'feature', cwd=self.source, check=False)
        self.assertNotEqual(merge.returncode, 0)  # actual merge conflict
        (self.source / 'config.txt').write_text(f'resolved\n{FAKE}\n')
        run('git', 'add', 'config.txt', cwd=self.source)
        run('git', 'commit', '-qm', 'resolve merge with synthetic marker', cwd=self.source)
        old = run('git', 'log', '-p', '--all', '--full-history', cwd=self.source).stdout
        new = run('git', 'log', '-p', '-m', '--all', '--full-history', cwd=self.source).stdout
        self.assertNotIn(FAKE, old)
        self.assertIn(FAKE, new)
        result = self.scan()
        self.assertEqual(result.returncode, 1, result.stderr + (self.root/'out/coverage-gaps.private.txt').read_text())
        self.assertNotIn(FAKE, result.stdout + result.stderr)
        self.assertEqual((self.root/'out/gitleaks-exit-code.private.txt').read_text().strip(), '1')

    def test_reject_userinfo_without_echo_or_files(self):
        fake = 'https://person:EXAMPLE_PRIVATE_NOT_REAL@github.com/acme/repo.git'
        result = run('bash', str(SCRIPT), fake, str(self.root/'reject'), check=False, env=self.env)
        self.assertEqual(result.returncode, 64)
        self.assertNotIn('EXAMPLE_PRIVATE_NOT_REAL', result.stdout+result.stderr)
        self.assertFalse((self.root/'reject').exists())

    def test_ssh_credential_path_only_rejects_password(self):
        fake = 'ssh://git:EXAMPLE_PASSWORD@github.com/acme/repo.git'
        result = run('bash', str(SCRIPT), fake, str(self.root/'reject'), check=False, env=self.env)
        self.assertEqual(result.returncode, 64)
        self.assertNotIn('EXAMPLE_PASSWORD', result.stdout+result.stderr)

    def test_unclassified_advertised_ref_fails_closed(self):
        sha = run('git', 'rev-parse', 'HEAD', cwd=self.source).stdout.strip()
        run('git', 'update-ref', 'refs/notes/synthetic', sha, cwd=self.source)
        result = self.scan()
        self.assertEqual(result.returncode, 66, result.stderr)
        self.assertIn('UNCLASSIFIED', (self.root/'out/coverage-gaps.private.txt').read_text())

    def test_inherited_scanner_config_is_ignored(self):
        self.env['GITLEAKS_CONFIG'] = '/untrusted/config.toml'
        self.env['GITLEAKS_CONFIG_TOML'] = '[[rules]]\u005cnid = "untrusted"'
        result = self.scan()
        self.assertEqual(result.returncode, 66, result.stderr)

    def test_bad_checksum_never_executes_scanner(self):
        original = self.manifest.read_text()
        digest = original.splitlines()[0][7:]
        self.manifest.write_text(original.replace(digest, '0' * 64))
        result = self.scan()
        self.assertEqual(result.returncode, 67)
        out = self.root / 'out'
        self.assertFalse((out / 'gitleaks-version.private.txt').exists())
        self.assertFalse((out / 'gitleaks-help.private.txt').exists())
        self.assertIn('SCAN_STATUS=NOT_RUN', (out / 'status.private.env').read_text())

    def test_untrusted_provenance_rejected(self):
        original = self.manifest.read_text()
        self.manifest.write_text(original.replace(
            'SOURCE=https://github.com/gitleaks/gitleaks/releases/tag/TEST-FIXTURE',
            'SOURCE=https://untrusted.invalid/not-an-official-release'))
        result = self.scan()
        self.assertEqual(result.returncode, 67)
        self.assertFalse((self.root / 'out/gitleaks-version.private.txt').exists())

    def test_missing_scanner_never_executes(self):
        (self.bin / 'gitleaks').unlink()
        result = self.scan()
        self.assertEqual(result.returncode, 69)
        self.assertFalse((self.root / 'out/gitleaks-version.private.txt').exists())
        self.assertIn('SCAN_STATUS=NOT_RUN', (self.root / 'out/status.private.env').read_text())

    def test_missing_manifest_blocks(self):
        self.manifest.unlink()
        result = self.scan()
        self.assertEqual(result.returncode, 67)
        self.assertIn('PREPUBLIC_GATE=FAIL', (self.root / 'out/status.private.env').read_text())

    def test_clean_scan_is_not_prepublic_pass(self):
        result = self.scan()
        self.assertEqual(result.returncode, 66)
        status = (self.root / 'out/status.private.env').read_text()
        for key in ('GIT_LFS', 'FORKS', 'HIDDEN_REFS', 'GITHUB_SURFACES'):
            self.assertIn(key + '_STATUS=UNVERIFIED', status)
        self.assertIn('HUMAN_REVIEW_STATUS=NOT_RUN', status)
        self.assertIn('PREPUBLIC_GATE=FAIL', status)
        self.assertIn('AUDIT_STATUS=BLOCKED', status)

    def test_existing_destination_is_not_overwritten(self):
        out = self.root / 'out'
        out.mkdir()
        result = self.scan(out=out)
        self.assertEqual(result.returncode, 73)
        self.assertFalse((out/'mirror.git').exists())

    def test_missing_argument(self):
        self.assertEqual(run('bash', str(SCRIPT), check=False, env=self.env).returncode, 64)


if __name__ == '__main__':
    unittest.main(verbosity=2)
