import os,subprocess,tempfile,unittest
from pathlib import Path
from write_si_profile_v1012 import render
HERE=Path(__file__).resolve().parent
FLAGS=("V919_HANDLER_EPILOGUE","V920_HANDLER_RETURN","V921_CAPTURE_JOIN",
       "V922_IRQ_RETURN","V932_PENDING_RFI","V939_SECOND_VECTOR",
       "V951_SECOND_DISPATCH","V958_SECOND_ACK","V967_POST_ACK",
       "V975_SECOND_TIME","V989_SHARED_COMPLETION","V981_SECOND_FRONTIER",
       "V995_SUCCESS_FRONTIER","V1009_SECOND_CALLBACK")
PROFILE="UNDERCOVER_RUN_V1012_SI_PROFILE"

class SiProfileContract(unittest.TestCase):
    def plan(self, profile=None, mode="irq-si-handler-suffix", drop=None):
        env={k:v for k,v in os.environ.items() if not k.startswith("UNDERCOVER_RUN_")}
        for f in FLAGS:
            if f!=drop:env["UNDERCOVER_RUN_"+f]="1"
        if profile is not None:env[PROFILE]=profile
        return subprocess.run(["bash",str(HERE/"run_v575_dsp_sc_launch.sh"),"--describe-mode",mode],
                              env=env,capture_output=True,text=True,timeout=5)
    def test_profile_bytes(self):
        default="UNDERCOVER_SI_PROFILE_V1\nlatency=00000008\nport0=absent\nport1=absent\nport2=absent\nport3=absent\n"
        self.assertEqual(render("absent"),default)
        self.assertEqual(render("port1-present"),default.replace("port1=absent","port1=090000"))
        for bad in ("", "present", "port0-present", "../profile"):
            with self.assertRaises(KeyError):render(bad)
    def test_exclusive_write(self):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/"si-test-profile.txt"
            cmd=["python3",str(HERE/"write_si_profile_v1012.py"),"port1-present",str(p)]
            self.assertEqual(subprocess.run(cmd,capture_output=True,timeout=5).returncode,0)
            self.assertEqual(p.read_bytes(),render("port1-present").encode("ascii"))
            self.assertNotEqual(subprocess.run(cmd,capture_output=True,timeout=5).returncode,0)
            self.assertEqual(p.read_bytes(),render("port1-present").encode("ascii"))
    def test_launch_gate(self):
        default=self.plan()
        self.assertEqual(default.returncode,0,default.stderr)
        self.assertEqual(default.stdout,self.plan("absent").stdout)
        mixed=self.plan("port1-present")
        self.assertEqual(mixed.returncode,0,mixed.stderr)
        self.assertEqual(mixed.stdout,default.stdout+"V1012_SI_PROFILE selected=port1-present cold_port0_absent=1 synthetic=1\n")
        for bad in ("","all-present","port0-present","../profile"):
            got=self.plan(bad)
            self.assertEqual((got.returncode,got.stdout),(2,""))
        for got in (self.plan("port1-present",drop="V1009_SECOND_CALLBACK"),
                    self.plan("port1-present",mode="dsp-return")):
            self.assertEqual((got.returncode,got.stdout),(2,""))

if __name__=="__main__":unittest.main()
