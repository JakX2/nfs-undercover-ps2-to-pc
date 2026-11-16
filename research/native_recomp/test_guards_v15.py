#!/usr/bin/env python3
"""Original-free negative tests for V15 generator, patcher and private slicer."""
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from make_dispatch_slice_v15 import make_slice
from apply_nonsplit_dispatch_v15 import apply


def run(args, success=True):
    r = subprocess.run(args, capture_output=True, text=True, timeout=20)
    if (r.returncode == 0) != success:
        raise AssertionError(f'wrong exit status {r.returncode}: {args}; {r.stderr}')


def test(exe:Path, upstream:Path, work:Path):
    checks = 0
    source=upstream/'nWiiRecomp/src/recompiler.cpp'
    # Verify the upstream-copy patch is idempotent and fail-closed, without
    # modifying any real checkout in these guard tests.
    tree=work/'patch-fixture'
    (tree/'nWiiRecomp/src').mkdir(parents=True)
    dst=tree/'nWiiRecomp/src/recompiler.cpp'
    patched=source.read_text()
    begin='    out << "      if (_setjmp(ctx.exception_jmp_buf) == 0) {\\n";'
    malformed='    out << "      try {\\n";'
    closing='''    out << "        }\\n";
    out << "      } else {\\n";
    out << "          continue;\\n";
    out << "      }\\n";
    out << "    }\\n";
'''
    oldclosing='''    out << "        }\\n";
    out << "    }\\n";
'''
    assert patched.count(begin)==2
    assert patched.count(closing)>=1
    old=patched.replace(begin,malformed,1) # must target non-split only below
    if old.count(malformed)!=1:
        raise AssertionError('missing unpatched form fixture')
    # We need to remove the NON-SPLIT else, not the split one.
    i=old.index('UNKNOWN DISPATCH TO')
    j=old.index(closing,i)
    old=old[:j]+oldclosing+old[j+len(closing):]
    dst.write_text(old)
    assert apply(tree) is True; checks+=1
    assert dst.read_text()==patched; checks+=1
    assert apply(tree) is False; checks+=1
    dst.write_text(old.replace(malformed,'    out << "      bad upstream {\\n";'))
    unchanged=dst.read_bytes()
    try:
        apply(tree)
        raise AssertionError('unrecognized upstream emitter was accepted')
    except ValueError:
        assert dst.read_bytes()==unchanged
    checks+=1

    # Synthetic file creation is deterministic and never requires game assets.
    data,entry=make_slice(None)
    fixture=work/'guards_synthetic.dol'
    fixture.write_bytes(data)
    assert entry==0x80004000 and len(data)==296
    checks+=1
    # Empty output directory requirement and strict spans prevent leaking
    # more original code than the two selected functions.
    cases=[
        ('80004000','20','80004018','8'),
        ('80004000','24','80004018','4'),
        ('80004004','24','80004018','8'),
        ('80004000','24','8000401C','8'),
        ('80004000','24','80004200','8'),
        ('80004000','24','80004100','8'),
        ('80004000','24','80004000','24'),
    ]
    for i, spec in enumerate(cases):
        dest=work/f'reject_{i}'
        dest.mkdir()
        run([str(exe),str(fixture),str(dest),*spec],success=False)
        assert not list(dest.iterdir())
        checks+=1
    out=work/'nonempty'
    out.mkdir()
    (out/'other.cpp').write_text('keep')
    run([str(exe),str(fixture),str(out),'80004000','24','80004018','8'],False)
    assert len(list(out.iterdir()))==1
    checks+=1
    truncated=work/'truncated.dol'
    truncated.write_bytes(data[:-1])
    invalid_dest=work/'invalid'
    invalid_dest.mkdir()
    run([str(exe),str(truncated),str(invalid_dest),'80004000','24','80004018','8'],False)
    assert not list(invalid_dest.iterdir())
    checks+=1
    print(f'PASS: {checks} original-free V15 safety/idempotence/rejection checks')


if __name__=='__main__':
    exe,upstream,work=map(Path,sys.argv[1:4])
    test(exe,upstream,work)
