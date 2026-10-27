"""Pure-function tests for jobq: probe parsing, node qualification, unit command, config loading, task slots."""
import importlib.machinery, importlib.util, os, subprocess, sys, tempfile, unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BIN = os.path.join(ROOT, "bin", "jobq")


def load(cfgpath):
    os.environ["JOBQ_CONFIG"] = cfgpath
    loader = importlib.machinery.SourceFileLoader("jobq_mod", BIN)
    spec = importlib.util.spec_from_loader("jobq_mod", loader)
    mod = importlib.util.module_from_spec(spec)
    loader.exec_module(mod)
    return mod


class T(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.cfg = os.path.join(self.tmp.name, "c.toml")
        with open(self.cfg, "w") as f:
            f.write('default_node = "a"\n[nodes.a]\nssh = "host-a"\nproperties = ["MemoryMax=1G"]\n[nodes.b]\nssh = "host-b"\n'
                    '[classes.test]\nslots = 2\nenv = { X = "1" }\n')
        self.j = load(self.cfg)

    def tearDown(self):
        self.tmp.cleanup()

    def test_config_merge(self):
        self.assertEqual(self.j.CFG["classes"]["test"]["slots"], 2)
        self.assertEqual(self.j.CFG["classes"]["gate"]["slots"], 1)
        self.assertEqual(self.j.CFG["nodes"]["a"]["hostname"], "host-a")

    def test_probe_and_qualify(self):
        s = self.j.parse_probe("mem=16777216\nload=2.0\nnproc=8\ntemp=50000\nblock=0\n")
        self.assertAlmostEqual(s["avail_gb"], 16.0)
        self.assertAlmostEqual(s["ratio"], 0.25)
        self.assertTrue(self.j.qualifies("a", s, 6))
        self.assertFalse(self.j.qualifies("a", s, 32))
        s["block"] = True
        self.assertFalse(self.j.qualifies("a", s, 6))
        self.assertIsNone(self.j.parse_probe("mem=1\n"))

    def test_unit_cmd(self):
        cmd = self.j.build_unit_cmd("u1", self.tmp.name, ["/bin/true"], "test", "a")
        self.assertIn("jobq-bg.slice", cmd)
        self.assertIn("X=1", cmd)
        self.assertIn("MemoryMax=1G", cmd)
        self.assertEqual(cmd[-1], "/bin/true")

    def test_slot_and_safe(self):
        i, f = self.j.take_slot(2, d=self.tmp.name, prefix="p")
        self.assertIn(i, (0, 1))
        f.close()
        self.assertEqual(self.j.safe("a b/c"), "a-b-c")

    def test_help(self):
        p = subprocess.run([sys.executable, BIN, "--help"], capture_output=True, text=True, timeout=30)
        self.assertEqual(p.returncode, 0)


if __name__ == "__main__":
    unittest.main()
