"""Install the production observer seams into synthetic generated output."""
import sys,shutil
from pathlib import Path
from prepare_v672_si_ack_route import patch_shard,patch_si
from prepare_v680_si_helper import patch_helper,patch_binding as first_patch,exact_function,verify_direct
from prepare_v688_si_second import patch_binding
from prepare_v693_si_nested import patch_second
from prepare_v709_os_leaves import patch_nested,patch_leaf,render
from prepare_v625_ipc_client import audit_native
HOST=Path(__file__).resolve().parent
H=0x80004000;A=0x80005004;B=0x80006000;N=0x80007000;D=0x80008000;T=0x80009000;R=0x8000a000
def bl(a,b):return 0x48000001|((b-a)&0x03fffffc)
handler=[bl(H,A),bl(H+4,B),0x91070000,0x60000000,0x4e800020]
first=[0x900b0000|(r<<21)|((-4*(32-r))&0xffff) for r in range(29,32)]+[0x4e800020]
second=[0x81070000,0x91070000,0x90c50000,0x7c0802a6,0x90010004,bl(B+20,N),0x80010004,0x7c0803a6,0x4e800020]
nested=[0x80850000,0x910a0000,0x7c0802a6,0x90010008,0x2c090000,0x40820008,bl(N+24,D),bl(N+28,T),0x38600000,bl(N+36,R),0x80010008,0x7c0803a6,0x4e800020]
leaves=[(N+24,D,D+16,bl(N+24,D),1,[0x7c0000a6,0x7c000124,0x38600000,0x4e800020],[]),
        (N+28,T,T+12,bl(N+28,T),2,[0x7c8c42e6,0x7c6d42e6,0x4e800020],[]),
        (N+36,R,R+12,bl(N+36,R),3,[0x7c0000a6,0x7c000124,0x4e800020],[])]
def install(root,inc):
    paths=list(root.glob('*.cpp'));original={p:p.read_text() for p in paths}
    main=(root/('main_output.cpp' if (root/'main_output.cpp').is_file() else 'output.cpp')).read_text()
    outer=main[main.index('extern "C" void run_game('):]
    seen_roots=set()
    for p,s in original.items():
        changed=s
        if f'void func_{H:X}(CPUContext& ctx) {{' in s:
            verify_direct(exact_function(s,H),H,A);verify_direct(exact_function(s,H),H+4,B)
            changed,seen=patch_shard(changed,handler,H)
            assert audit_native([exact_function(s,H)],outer,seen)==5
            seen_roots.add(H)
        if f'void func_{B:X}(CPUContext& ctx) {{' in s:verify_direct(exact_function(s,B),B+20,N)
        for root_pc,words,is_second,is_nested in ((A,first,False,False),(B,second,True,False),(N,nested,False,True)):
            changed,seen=patch_helper(changed,root_pc,words,is_second,is_nested)
            if seen:
                assert root_pc not in seen_roots and audit_native([exact_function(s,root_pc)],outer,seen)==len(words)
                seen_roots.add(root_pc)
        if f'void func_{N:X}(CPUContext& ctx) {{' in s:
            for site,dst,*_ in leaves:verify_direct(exact_function(s,N),site,dst)
        for site,dst,end,w,kind,code,mt in leaves:
            changed,seen=patch_leaf(changed,dst,code,kind)
            if seen:
                assert dst not in seen_roots and audit_native([exact_function(s,dst)],outer,seen)==len(code)
                seen_roots.add(dst)
        if changed!=s:p.write_text(changed)
    assert seen_roots=={H,A,B,N,D,T,R}
    dest=inc/'undercover';dest.mkdir(parents=True)
    for n in ('wii_si_controller_v511.h','wii_si_completion_ack_v668.h','wii_si_first_helper_v680.h','wii_si_helper_binding_v680.h','wii_si_second_binding_v688.h','wii_si_nested_binding_v693.h','wii_si_type_scheduler_v514.h','wii_postack_os_leaf_v703.h','wii_si_os_leaf_binding_v709.h'):
        shutil.copyfile(HOST/n,dest/n)
    (dest/'wii_si_binding_v512.h').write_text(patch_si((HOST/'wii_si_binding_v512.h').read_text()))
    (dest/'wii_si_ack_binding_v672.h').write_text(patch_binding(first_patch((HOST/'wii_si_ack_binding_v672.h').read_text())))
    (dest/'v672_private_si_ack_expectations.h').write_text('#pragma once\n#include <cstdint>\nnamespace undercover::wii::v672 {inline constexpr uint32_t handler_first=0x80004000u,handler_end=0x80004014u;}\n')
    (dest/'v680_private_si_helper_expectations.h').write_text(f'#pragma once\nnamespace undercover::wii::v680 {{inline constexpr SiHelperExpectation expected{{0x{H:08x}u,0x{A:08x}u,0x{A+16:08x}u,0x{handler[0]:08x}u,29,11,-12}};}}\n')
    (dest/'v688_private_si_second_expectations.h').write_text(f'#pragma once\nnamespace undercover::wii::v688 {{inline constexpr SiHelperExpectation expected_second{{0x{H+4:08x}u,0x{B:08x}u,0x{B+36:08x}u,0x{handler[1]:08x}u}};}}\n')
    (dest/'wii_si_second_binding_v688.h').write_text(patch_second((HOST/'wii_si_second_binding_v688.h').read_text()))
    (dest/'v693_private_si_nested_expectations.h').write_text(f'#pragma once\nnamespace undercover::wii::v693 {{inline constexpr SiHelperExpectation expected_nested{{0x{B+20:08x}u,0x{N:08x}u,0x{N+52:08x}u,0x{second[5]:08x}u}};}}\n')
    (dest/'wii_si_nested_binding_v693.h').write_text(patch_nested((HOST/'wii_si_nested_binding_v693.h').read_text()))
    (dest/'v709_private_os_leaf_expectations.h').write_text(render(leaves))
    hw=inc/'runtime/hw/hw.h';hw.parent.mkdir(parents=True)
    hw.write_text('#pragma once\n#include <atomic>\n#include <cstdint>\nnamespace nwii::runtime::hw {inline std::atomic<uint32_t> pi_intsr{0},pi_intmr{0};}\n')
    print('V710_PATCH native_labels=41 direct_edges=6')
if __name__=='__main__':install(Path(sys.argv[1]),Path(sys.argv[2]))
