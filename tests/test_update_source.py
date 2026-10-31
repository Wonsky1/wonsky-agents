"""Source acquisition checks use synthetic archives and mocked HTTP only."""

import io
import json
import os
from pathlib import Path
import stat
import tempfile
import unittest
from unittest import mock
from urllib.error import HTTPError, URLError
import zipfile

from scripts import update_source
from scripts.update_source import open_update_source


REVISION = 'a' * 40


def collection_entries(prefix='wonsky-agents-' + REVISION):
    return {
        prefix + '/install.py': 'raise RuntimeError("never execute downloaded code")',
        prefix + '/scripts/updater.py': '# example',
        prefix + '/skills/example/SKILL.md': '---\nname: example\n---\n',
    }


def make_zip(entries):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for name, contents in entries.items():
            archive.writestr(name, contents)
    return output.getvalue()


class UpdateSourceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name).resolve()

    def local_collection(self):
        root = self.root / 'local'
        for name, contents in collection_entries('local').items():
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(contents, encoding='utf-8')
        return root

    def responses(self, zip_bytes=None, metadata=None):
        api = json.dumps({'sha': REVISION} if metadata is None else metadata).encode('utf-8')
        return [io.BytesIO(api), io.BytesIO(zip_bytes or make_zip(collection_entries()))]

    def test_explicit_folder_never_uses_network_or_claims_original_revision(self):
        root = self.local_collection()
        with mock.patch.object(update_source, 'urlopen') as opener:
            with open_update_source(root) as source:
                self.assertEqual(source.root, root)
                self.assertEqual(source.revision, 'unknown')
                self.assertIn('local folder:', source.provenance)
            opener.assert_not_called()
        self.assertTrue(root.exists())

    def test_download_pins_resolved_revision_and_removes_staging_on_exit(self):
        with mock.patch.object(update_source, 'urlopen', side_effect=self.responses()) as opener:
            with open_update_source() as source:
                staging = source.root
                self.assertEqual(source.revision, REVISION)
                self.assertTrue((staging / 'skills/example/SKILL.md').is_file())
                self.assertIn(REVISION, source.provenance)
                self.assertEqual(opener.call_args_list[0].args[0].full_url, update_source.API_URL)
                self.assertEqual(opener.call_args_list[1].args[0].full_url,
                                 'https://api.github.com/repos/Wonsky1/wonsky-agents/zipball/' + REVISION)
            self.assertFalse(staging.exists())

    def test_consumer_failure_also_removes_download(self):
        with mock.patch.object(update_source, 'urlopen', side_effect=self.responses()):
            with self.assertRaisesRegex(RuntimeError, 'consumer failed'):
                with open_update_source() as source:
                    staging = source.root
                    raise RuntimeError('consumer failed')
            self.assertFalse(staging.exists())

    def test_invalid_metadata_does_not_fetch_or_extract_archive(self):
        for metadata in ({'sha': '../../escape'}, {'sha': 'abc'}, {}, {'sha': None}, []):
            with self.subTest(metadata=metadata):
                with mock.patch.object(update_source, 'urlopen', side_effect=self.responses(metadata=metadata)) as opener:
                    with self.assertRaisesRegex(ValueError, 'invalid revision metadata'):
                        with open_update_source():
                            self.fail('Invalid metadata must not yield a source')
                    self.assertEqual(opener.call_count, 1)

    def test_http_errors_are_readable_without_response_or_token(self):
        secret = 'private-test-token-value'
        for status in (401, 403, 404, 500):
            error = HTTPError(update_source.API_URL, status, secret, {}, io.BytesIO(secret.encode()))
            with self.subTest(status=status), mock.patch.dict(os.environ, {'GH_TOKEN': secret}):
                with mock.patch.object(update_source, 'urlopen', side_effect=error):
                    with self.assertRaises(ValueError) as caught:
                        with open_update_source():
                            self.fail('HTTP error must not yield a source')
                    self.assertIn(str(status), str(caught.exception))
                    self.assertNotIn(secret, str(caught.exception))
                    self.assertTrue(error.closed)

    def test_network_errors_do_not_echo_credentials_or_response_body(self):
        with mock.patch.object(update_source, 'urlopen', side_effect=URLError('sensitive error payload')):
            with self.assertRaisesRegex(ValueError, 'network access') as caught:
                with open_update_source():
                    self.fail('Network error must not yield a source')
            self.assertNotIn('sensitive', str(caught.exception))

    def test_token_is_unredirected_and_invalid_control_chars_are_rejected(self):
        with mock.patch.dict(os.environ, {'GH_TOKEN': 'a-token'}):
            request = update_source._request(update_source.API_URL, api=True)
            self.assertNotIn('Authorization', request.headers)
            self.assertEqual(request.unredirected_hdrs['Authorization'], 'Bearer a-token')
        with mock.patch.dict(os.environ, {'GH_TOKEN': 'token\nsecret'}):
            with self.assertRaises(ValueError) as caught:
                update_source._request(update_source.API_URL)
            self.assertNotIn('secret', str(caught.exception))

    def test_bounded_download_handles_missing_content_length(self):
        target = self.root / 'bounded'
        with mock.patch.object(update_source, 'urlopen', return_value=io.BytesIO(b'123456')):
            with self.assertRaisesRegex(ValueError, 'download size'):
                update_source._fetch(update_source.API_URL, target, 5)
        self.assertLessEqual(target.stat().st_size, 5)

    def test_private_and_generated_files_are_not_staged(self):
        entries = collection_entries()
        prefix = 'wonsky-agents-' + REVISION
        for name in ('.git/config', '.env', '.env.production', '.env-secrets/value',
                     '.wonsky-state/collection.json', 'scripts/__pycache__/module.pyc',
                     'skills/github-pr-review/reviewer-preferences.md'):
            entries[prefix + '/' + name] = 'sensitive'
        entries[prefix + '/.env.example'] = 'PUBLIC_EXAMPLE='
        with mock.patch.object(update_source, 'urlopen', side_effect=self.responses(make_zip(entries))):
            with open_update_source() as source:
                self.assertTrue((source.root / '.env.example').is_file())
                self.assertFalse((source.root / '.git').exists())
                self.assertFalse((source.root / '.env').exists())
                self.assertFalse((source.root / '.env-secrets').exists())
                self.assertFalse((source.root / 'skills/github-pr-review/reviewer-preferences.md').exists())

    def test_missing_local_collection_entries_are_rejected(self):
        for missing in ('install.py', 'scripts', 'skills'):
            with self.subTest(missing=missing):
                root = self.root / missing
                root.mkdir()
                for name in ('install.py', 'scripts', 'skills'):
                    if name != missing:
                        target = root / name
                        target.write_text('') if name == 'install.py' else target.mkdir()
                with self.assertRaisesRegex(ValueError, 'missing a regular'):
                    with open_update_source(root):
                        self.fail('Incomplete source must not be accepted')

    def test_empty_or_missing_skill_definitions_are_rejected(self):
        root = self.local_collection()
        (root / 'skills/example/SKILL.md').unlink()
        with self.assertRaisesRegex(ValueError, 'SKILL.md'):
            with open_update_source(root):
                self.fail('Missing skill definition must not be accepted')

    def test_local_source_symlink_is_rejected_without_following(self):
        root = self.local_collection()
        link = self.root / 'linked'
        try:
            link.symlink_to(root, target_is_directory=True)
        except (OSError, NotImplementedError):
            self.skipTest('Symlink creation is not available')
        with self.assertRaisesRegex(ValueError, 'regular collection'):
            with open_update_source(link):
                self.fail('Linked collection must not be accepted')


class ArchiveValidationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def extract(self, entries):
        archive = self.root / 'source.zip'
        archive.write_bytes(make_zip(entries))
        return update_source._extract(archive, self.root / 'out')

    def test_traversal_absolute_windows_and_ambiguous_paths_are_rejected(self):
        for path in ('../outside', '/absolute', 'repo/../outside', 'repo/./same',
                     'repo//same', 'repo\\escape', 'C:/escape', 'repo/a:stream',
                     'repo/CON.txt', 'repo/LPT9', 'repo/trailing.', 'repo/trailing ',
                     'repo/COM\u00b9', 'repo/CON .txt', 'repo/question?'):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    self.extract({path: 'bad'})
                self.assertFalse((self.root / 'out').exists())

    def test_duplicate_archive_entries_are_rejected(self):
        output = io.BytesIO()
        with zipfile.ZipFile(output, 'w') as archive:
            archive.writestr('repo/file', 'first')
            with self.assertWarns(UserWarning):
                archive.writestr('repo/file', 'second')
        target = self.root / 'duplicate.zip'
        target.write_bytes(output.getvalue())
        with self.assertRaisesRegex(ValueError, 'duplicate entries'):
            update_source._extract(target, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())

    def test_embedded_null_in_raw_zip_name_is_rejected(self):
        archive = self.root / 'null.zip'
        archive.write_bytes(make_zip({'repo/null_ignored': 'bad'}).replace(
            b'repo/null_ignored', b'repo/null\x00ignored'))
        with self.assertRaisesRegex(ValueError, 'unsafe path'):
            update_source._extract(archive, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())

    def test_case_and_unicode_collisions_are_rejected_before_extraction(self):
        for paths in (('repo/A/file', 'repo/a/other'),
                      ('repo/caf\u00e9/file', 'repo/cafe\u0301/other')):
            with self.subTest(paths=paths):
                with self.assertRaisesRegex(ValueError, 'collide'):
                    self.extract(dict.fromkeys(paths, 'bad'))
                self.assertFalse((self.root / 'out').exists())

    def test_file_parent_conflict_is_rejected_in_either_order(self):
        for paths in (('repo/a', 'repo/a/b'), ('repo/a/b', 'repo/a')):
            with self.subTest(paths=paths):
                with self.assertRaisesRegex(ValueError, 'parent directory'):
                    self.extract(dict.fromkeys(paths, 'bad'))
                self.assertFalse((self.root / 'out').exists())

    def test_symlinks_and_special_entries_are_rejected(self):
        for kind in (stat.S_IFLNK, stat.S_IFIFO, stat.S_IFSOCK):
            member = zipfile.ZipInfo('repo/entry')
            member.create_system = 3
            member.external_attr = (kind | 0o777) << 16
            with self.subTest(kind=kind):
                with self.assertRaisesRegex(ValueError, 'symlink or special'):
                    self.extract({member: 'target'})
                self.assertFalse((self.root / 'out').exists())

    def test_one_top_level_directory_is_required(self):
        for entries in ({'a/file': 'a', 'b/file': 'b'}, {'single': 'file'}, {}):
            with self.subTest(entries=entries):
                with self.assertRaises(ValueError):
                    self.extract(entries)
                self.assertFalse((self.root / 'out').exists())

    def test_expanded_size_and_file_count_are_bounded(self):
        entries = collection_entries('repo')
        with mock.patch.object(update_source, 'MAX_EXPANDED_BYTES', 1):
            with self.assertRaisesRegex(ValueError, 'extracted size'):
                self.extract(entries)
        with mock.patch.object(update_source, 'MAX_MEMBERS', 1):
            with self.assertRaisesRegex(ValueError, 'too many entries'):
                self.extract(entries)
        self.assertFalse((self.root / 'out').exists())

    def test_corrupt_zip_is_reported_without_extracting(self):
        archive = self.root / 'broken.zip'
        archive.write_bytes(b'not a zip')
        with self.assertRaisesRegex(ValueError, 'invalid or unsupported'):
            update_source._extract(archive, self.root / 'out')
        self.assertFalse((self.root / 'out').exists())


if __name__ == '__main__':
    unittest.main()
