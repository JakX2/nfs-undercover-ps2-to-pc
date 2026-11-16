"""Original-free regression tests for NWiiRecomp's CSV/TOML input adapter."""
from pathlib import Path
import tempfile
import unittest

from wii_recomp_nwii_bridge import canonical_functions, emit_nwii, write_config, quote_toml_path
from wii_recomp_preflight import PreflightError
from test_wii_recomp_preflight import make_pair


class AdapterTests(unittest.TestCase):
    def fake_root(self, base):
        root = Path(base, 'upstream')
        (root / 'nWiiRecomp/src').mkdir(parents=True)
        (root / 'nWiiRecomp/src/main.cpp').write_text('// synthetic fixture\n')
        (root / 'nWiiRuntime').mkdir()
        (root / 'nWiiRuntime/CMakeLists.txt').write_text('# synthetic fixture\n')
        return root

    def test_csv_and_manifest(self):
        elf, dol = make_pair()
        with tempfile.TemporaryDirectory() as d:
            root = self.fake_root(d)
            out = Path(d) / 'private-results'
            result = emit_nwii(elf, dol, out, root)
            csv = (out / 'undercover-nwii-symbols.csv').read_text().splitlines()
            self.assertEqual(csv[0], 'Name,Location,Size')
            self.assertEqual(len(csv), 3)
            self.assertEqual(result['symbol_count'], 2)
            self.assertIn('80004000', csv[1])
            self.assertIn('80004018', csv[2])
            config = write_config(out, Path(d)/'game.dol', root)
            self.assertIn('input_game_dir', config.read_text())
            self.assertIn('symbols_csv', config.read_text())
            self.assertNotIn('hle_hooks', config.read_text())

    def test_duplicate_address_deterministic(self):
        symbols = [(0x80004000, 16, 'weak', 0), (0x80004000, 16, 'strong', 1)]
        self.assertEqual(canonical_functions(symbols), [(0x80004000, 16, 'strong')])

    def test_reject_bad_alignment(self):
        with self.assertRaisesRegex(PreflightError, 'bad PPC function span'):
            canonical_functions([(0x80004002, 4, 'x', 1)])

    def test_reject_source_tree_output(self):
        elf, dol = make_pair()
        with tempfile.TemporaryDirectory() as d:
            root = self.fake_root(d)
            with self.assertRaisesRegex(PreflightError, 'OUTSIDE'):
                emit_nwii(elf, dol, root / 'generated', root)

    def test_reject_missing_source(self):
        elf, dol = make_pair()
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(PreflightError, 'source root'):
                emit_nwii(elf, dol, Path(d)/'out', Path(d)/'bogus')

    def test_windows_style_path_escaped(self):
        with tempfile.TemporaryDirectory() as d:
            escaped = quote_toml_path(Path(d)/'a "b".dol')
            self.assertIn('\\"', escaped)

if __name__ == '__main__':
    unittest.main()
