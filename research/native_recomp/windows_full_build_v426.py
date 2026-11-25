#!/usr/bin/env python3
"""Private native Windows x64 link/start lane with an original-free control."""
from __future__ import annotations
import argparse
import hashlib
import os
from pathlib import Path
import struct
import subprocess
import sys
from windows_startup_scope_v434 import SCOPES,contract,audit,launch_flags,requires_exi_profile,requires_si_profile,requires_sram_profile,requires_sc_overlay,requires_external_overlay,REPORT_SCOPES,EXTERNAL_SCOPES
from write_exi_profile_v505 import encode as encode_exi_profile,create as create_exi_profile
from write_sram_profile_v536 import sram_fixture

HOST=Path(__file__).resolve().parent
PIN='595f176f1d24cc54ff2e8389feed12d7fb553cc2'
OWNER_SHA='16a09adcf1987c1f3617d10f3a1cb830f32886afb583f9f8f88e0963ae5fe1f4'
ENTRY=0x80004000
NEXT=ENTRY+32
DATA=0x80001000
SWAP='__builtin_bswap32('
SWAP_NEW='CPUContext::portable_bswap32('
CTX='  CPUContext() : gpr{0}, fpr{0.0}, ps1{0.0}, cr{}, pc(0), lr(0), ctr(0), xer(0), '
CTX_NEW='''  static constexpr uint32_t portable_bswap32(uint32_t v) noexcept {
    return ((v & 0xffu) << 24) | ((v & 0xff00u) << 8) |
           ((v >> 8) & 0xff00u) | (v >> 24);
  }
'''+CTX
MAIN='int main(int argc, char **argv) {'
MAIN_NEW=MAIN+'''\n#ifdef _WIN32
  SDL_SetMainReady();
#endif'''
CMAKE='target_link_libraries(UndercoverWiiLocal PRIVATE nwiiruntime)'
CMAKE_NEW=CMAKE+'''\nif(WIN32)
    target_compile_definitions(UndercoverWiiLocal PRIVATE SDL_MAIN_HANDLED NOMINMAX)
    target_compile_definitions(nwiiruntime PRIVATE NOMINMAX)
endif()
'''
TRACE='void trace_call(uint32_t func_addr, CPUContext &ctx) {'
INTERPRETER=('void interpret_step(CPUContext& ctx) {','void micro_interpret(CPUContext& ctx, uint32_t opcode, uint32_t pc) {')
SYNTH_TRACE=TRACE+'''
  if (std::getenv("UNDERCOVER_V426_SYNTHETIC")) {
    if (func_addr == 0x80004000u) return;
    const bool ok = func_addr == 0x80004020u && ctx.pc == func_addr &&
        ctx.lr == 0x8000401cu && ctx.gpr[6] == 0x12345678u &&
        ctx.mmu.read32(0x80001000u) == 0x78563412u;
    std::cout << "V426_SYNTHETIC_SWAP verified=" << unsigned(ok) << std::endl;
    std::_Exit(ok ? 0 : 82);
  }'''

class BuildError(Exception):
    pass

def one(s,old,new):
    if s.count(old)!=1 or new in s:raise BuildError('source_seam')
    return s.replace(old,new,1)

def portable_patch(root):
    ctx=root/'nWiiRuntime/include/runtime/cpu_context.h';rec=root/'nWiiRecomp/src/recompiler.cpp'
    a=ctx.read_text(encoding='utf-8');b=rec.read_text(encoding='utf-8')
    if a.count(CTX_NEW)==1 and b.count(SWAP_NEW)==2 and SWAP not in b:return
    if b.count(SWAP)!=2 or SWAP_NEW in b:raise BuildError('swap_seam')
    new_a=one(a,CTX,CTX_NEW);new_b=b.replace(SWAP,SWAP_NEW)
    ctx.write_text(new_a,encoding='utf-8');rec.write_text(new_b,encoding='utf-8')

def generated_patch(root,synthetic):
    main=root/'nWiiRuntime/src/core/main.cpp';cm=root/'CMakeLists.txt';stubs=root/'nWiiRuntime/src/core/os_hle_stubs.cpp'
    changes={main:one(main.read_text(encoding='utf-8'),MAIN,MAIN_NEW),cm:one(cm.read_text(encoding='utf-8'),CMAKE,CMAKE_NEW)}
    if synthetic:
        s=stubs.read_text(encoding='utf-8')
        changes[stubs]=one(s,TRACE,SYNTH_TRACE)
        interp=root/'nWiiRuntime/src/hle/interpreter.cpp';s=interp.read_text(encoding='utf-8')
        for anchor in INTERPRETER:
            s=one(s,anchor,anchor+'\n  if (std::getenv("UNDERCOVER_V426_SYNTHETIC")) std::_Exit(83);')
        changes[interp]=s
    for p,s in changes.items():p.write_text(s,encoding='utf-8')

def synthetic_dol():
    def d(op,rt,ra,imm):return op<<26|rt<<21|ra<<16|(imm&0xffff)
    def x(rt,ra,rb,xo):return 31<<26|rt<<21|ra<<16|rb<<11|xo<<1
    words=(d(15,4,0,0x8000),d(14,5,0,0x1000),d(15,3,0,0x1234),d(24,3,3,0x5678),x(3,4,5,662),x(6,4,5,534),0x48000009,0x4e800020,0x4e800020)
    raw=bytearray(256)
    for at,val in ((0,256),(0x48,ENTRY),(0x90,len(words)*4),(0xe0,ENTRY)):struct.pack_into('>I',raw,at,val)
    return bytes(raw)+struct.pack('>9I',*words)

def validate_pe(path):
    if not path.is_file() or path.is_symlink():raise BuildError('pe_file')
    size=path.stat().st_size
    with path.open('rb') as f:
        head=f.read(64)
        if len(head)!=64 or head[:2]!=b'MZ':raise BuildError('pe_dos')
        offset=struct.unpack_from('<I',head,0x3c)[0]
        if not 64<=offset<=min(size-24,1024*1024):raise BuildError('pe_offset')
        f.seek(offset);coff=f.read(24)
        if coff[:4]!=b'PE\0\0':raise BuildError('pe_magic')
        machine,n,_,_,_,optional,flags=struct.unpack_from('<HHIIIHH',coff,4)
        if machine!=0x8664 or not 1<=n<=96 or not 112<=optional<=4096 or not flags&2 or flags&0x2000:raise BuildError('pe_coff')
        if offset+24+optional+40*n>size:raise BuildError('pe_sections')
        opt=f.read(optional)
        if struct.unpack_from('<H',opt)[0]!=0x20b:raise BuildError('pe_optional')
        entry=struct.unpack_from('<I',opt,16)[0]
        image=struct.unpack_from('<I',opt,56)[0]
        if not 0<entry<image:raise BuildError('pe_entry')
        hits=0
        for _ in range(n):
            sec=f.read(40);virt,addr,raw_size,raw_at=struct.unpack_from('<IIII',sec,8)
            attr=struct.unpack_from('<I',sec,36)[0]
            if raw_size and (raw_at==0 or raw_at+raw_size>size):raise BuildError('pe_raw')
            if attr&0x20000000 and addr<=entry<addr+min(virt,raw_size):hits+=1
        if hits!=1:raise BuildError('pe_entry_section')

# The source-only offline translator is built separately, without SDL/TOML.
def translator_project(host,root,sc_overlay=False):
    def cm(p):return '"'+p.resolve().as_posix()+'"'
    files=[host/'offline_recompiler_driver_v6.cpp']+[root/p for p in (
        'nWiiRuntime/src/core/loader.cpp','nWiiAnalyzer/src/analyzer.cpp',
        'nWiiAnalyzer/src/dolphin_sigdb.cpp','nWiiAnalyzer/src/signature_scanner.cpp',
        'nWiiRecomp/src/symbols.cpp','nWiiRecomp/src/recompiler.cpp')]
    inc=[root/p for p in ('nWiiRuntime/include','nWiiAnalyzer/include','nWiiRecomp/include')]
    return ('cmake_minimum_required(VERSION 3.20)\nproject(PrivateTranslator LANGUAGES CXX)\n'
            'set(CMAKE_CXX_STANDARD 20)\nset(CMAKE_CXX_STANDARD_REQUIRED ON)\n'
            'add_executable(translator '+' '.join(map(cm,files))+')\n'
            'target_include_directories(translator PRIVATE '+' '.join(map(cm,inc))+')\n'
            'target_compile_definitions(translator PRIVATE NOMINMAX'+(' UNDERCOVER_NATIVE_SC_OVERLAY' if sc_overlay else '')+')\n'
            'target_compile_options(translator PRIVATE /bigobj /utf-8 /Zc:__cplusplus)\n'
            'add_executable(dol_equivalence '+cm(host/'check_wii_dol_equivalence_v436.cpp')+' '+cm(root/'nWiiRuntime/src/core/loader.cpp')+')\n'
            'target_include_directories(dol_equivalence PRIVATE '+cm(host)+' '+cm(root/'nWiiRuntime/include')+')\n'
            'target_compile_definitions(dol_equivalence PRIVATE NOMINMAX)\n'
            'target_compile_options(dol_equivalence PRIVATE /utf-8 /Zc:__cplusplus)\n')

def command(args,log,seconds,env=None,cwd=None):
    with log.open('wb') as f:
        p=subprocess.Popen([str(a) for a in args],stdout=f,stderr=subprocess.STDOUT,env=env,cwd=cwd)
        try:return p.wait(timeout=seconds)
        except subprocess.TimeoutExpired:
            if os.name=='nt':subprocess.run(['taskkill','/T','/F','/PID',str(p.pid)],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,timeout=15,check=False)
            else:p.kill()
            p.wait(timeout=15);return 124

def run_stage(name,args,work,seconds,**kwargs):
    rc=command(args,work/(name+'.log'),seconds,**kwargs)
    if rc:raise BuildError(name+('_timeout' if rc==124 else '_failed'))
    print(f'V426_WINDOWS_STAGE stage={name} passed=1',flush=True)

def owner_scope(scope,synthetic):
    try:patches,observer,_=contract(scope,synthetic)
    except ValueError as e:raise BuildError('owner_scope') from e
    return patches,observer

def audit_owner_start(raw,rc,scope):
    owner_scope(scope,False)
    return audit(raw,rc,scope)

def build(root,work,dol=None,elf=None,scope='startup',legacy_loader=False,legacy_ticks=False):
    if os.name!='nt':raise BuildError('windows_required')
    root=root.resolve();work=work.absolute()
    if work.exists() or work.is_symlink() or root==work or root in work.resolve().parents:raise BuildError('fresh_work')
    synthetic=dol is None
    if synthetic!=(elf is None):raise BuildError('input_pair')
    extra_patches,observer=owner_scope(scope,synthetic)
    if requires_exi_profile(scope) and legacy_ticks:raise BuildError('exi_requires_native_ticks')
    if not synthetic and hashlib.sha256(dol.read_bytes()).hexdigest()!=OWNER_SHA:raise BuildError('owner_dol')
    if subprocess.check_output(['git','-C',str(root),'rev-parse','HEAD'],text=True).strip()!=PIN:raise BuildError('pin')
    if subprocess.check_output(['git','-C',str(root),'status','--porcelain'],text=True).strip():raise BuildError('dirty_upstream')
    work.mkdir(parents=True)
    symbols=work/'symbols.csv'
    if synthetic:
        dol=work/'synthetic.dol';dol.write_bytes(synthetic_dol());symbols.write_text(f'Name,Location,Size\nfn_{ENTRY:08X},{ENTRY:08X},32\nfn_{NEXT:08X},{NEXT:08X},4\n',encoding='utf-8')
    elif scope in REPORT_SCOPES:run_stage('symbols',[sys.executable,HOST/'make_v586_bat_roots.py',dol,elf,symbols],work,120)
    else:run_stage('symbols',[sys.executable,HOST/'make_private_elf_symbol_map.py',elf,symbols],work,120)
    for patch in ('apply_psq_indexed_patch','apply_psq_estimate_and_gqr_v5','apply_verified_elf_spans_v6')+extra_patches:
        run_stage(patch,[sys.executable,HOST/(patch+'.py'),root],work,60)
    if not legacy_ticks:
        run_stage('native_tick_labels',[sys.executable,HOST/'apply_native_tick_v438.py',root],work,60)
    if requires_exi_profile(scope):
        run_stage('exi_tick_labels',[sys.executable,HOST/'apply_exi_tick_v497.py',root,'emitter'],work,60)
    if requires_si_profile(scope):
        run_stage('si_tick_labels',[sys.executable,HOST/'apply_si_tick_v515.py',root,'emitter'],work,60)
    if scope in ('os-dsp-return',*REPORT_SCOPES):
        run_stage('aram_tick_labels',[sys.executable,HOST/'apply_aram_binding_v553.py',root,'emitter'],work,60)
    if scope in REPORT_SCOPES:
        run_stage('bat_roots',[sys.executable,HOST/'apply_bat_roots_v586.py',root],work,60)
        run_stage('report_table',[sys.executable,HOST/'apply_report_table_v594.py',root,dol,elf],work,60)
    if scope in EXTERNAL_SCOPES[1:]:
        run_stage('si_roots',[sys.executable,HOST/'apply_si_roots_v669.py',root,dol,elf],work,120)
    portable_patch(root)
    sc_overlay=requires_sc_overlay(scope)
    src=work/'translator-src';src.mkdir();(src/'CMakeLists.txt').write_text(translator_project(HOST,root,sc_overlay),encoding='utf-8')
    tb=work/'translator-build';gen=['-G','Visual Studio 17 2022','-A','x64']
    run_stage('translator_config',['cmake','-S',src,'-B',tb,*gen],work,180)
    run_stage('translator_build',['cmake','--build',tb,'--config','Release','--parallel','2'],work,600)
    if not legacy_loader:
        run_stage('dol_equivalence',[tb/'Release/dol_equivalence.exe',dol],work,60)
    generated=work/'generated';generated.mkdir()
    run_stage('translation',[tb/'Release/translator.exe',dol,symbols,generated,'--strict-symbol-spans',*(['--native-sc-overlay'] if sc_overlay else []),*(['--native-external-overlay-preflight'] if requires_external_overlay(scope) else []),'--generate',root/'nWiiRuntime'],work,1200)
    shards=list(generated.glob('output_*.cpp'))
    if len(shards)<(1 if synthetic else 20) or not (generated/'main_output.cpp').is_file():raise BuildError('shards')
    swaps=0
    for shard in shards:
        source=shard.read_text(encoding='utf-8')
        if 'UNIMPLEMENTED Opcode' in source or SWAP in source:raise BuildError('generated_opcode')
        swaps+=source.count(SWAP_NEW)
    if synthetic and swaps!=2:raise BuildError('synthetic_swap')
    generated_patch(generated,synthetic)
    if not synthetic:
        observer_inputs=[dol,elf,generated] if scope in REPORT_SCOPES else [dol,generated]
        run_stage('startup_observer',[sys.executable,HOST/observer,*observer_inputs],work,1200 if scope in EXTERNAL_SCOPES else 900 if scope=='os-arena-clear' else 600 if scope=='os-report' else 180)
        if requires_external_overlay(scope):
            run_stage('external_observer',[sys.executable,HOST/'prepare_v663_external_entry.py',dol,elf,generated],work,300)
            if scope in EXTERNAL_SCOPES[1:]:
                run_stage('si_dispatch_observer',[sys.executable,HOST/'prepare_v667_si_dispatch.py',dol,elf,generated],work,300)
            if scope=='os-si-ack':
                run_stage('si_ack_observer',[sys.executable,HOST/'prepare_v672_si_ack_route.py',dol,elf,generated],work,300)
            run_stage('external_translation_audit',[sys.executable,HOST/'audit_v662_external_overlay.py',dol,generated],work,300)
        if scope in REPORT_SCOPES:
            run_stage('report_translation_audit',[sys.executable,HOST/'audit_v594_report_translation.py',dol,elf,generated],work,300)
            run_stage('bat_translation_audit',[sys.executable,HOST/'audit_v584_bat_translation.py',dol,generated],work,300)
    if not legacy_loader:
        run_stage('strict_runtime_loader',[sys.executable,HOST/'apply_dol_loader_v431.py',generated],work,60)
    out=work/'native-build'
    run_stage('native_config',['cmake','-S',generated,'-B',out,*gen,'-DCMAKE_CXX_FLAGS_RELEASE=/Od /DNDEBUG /bigobj /utf-8 /Zc:__cplusplus','-DCMAKE_C_FLAGS_RELEASE=/Od /DNDEBUG'],work,600)
    run_stage('native_build',['cmake','--build',out,'--config','Release','--target','UndercoverWiiLocal','--parallel','2'],work,5400)
    exe=out/'Release/UndercoverWiiLocal.exe';validate_pe(exe)
    print(f'V426_WINDOWS_LINK linked=1 platform=windows-x64 synthetic={int(synthetic)} boot_verified=0',flush=True)
    launch=work/'launch';launch.mkdir();config=launch/'config.toml';config.write_text('[system]\nplatform = "Wii"\n[input]\nmode = 6\n',encoding='utf-8')
    env={k:v for k,v in os.environ.items() if k.upper() in ('PATH','SYSTEMROOT','WINDIR','COMSPEC','TEMP','TMP','PATHEXT')}
    env.update(NWII_HEADLESS='1',NWII_TRACE_CALLS='1',SDL_VIDEODRIVER='dummy',SDL_AUDIODRIVER='dummy',USERPROFILE=str(launch),HOME=str(launch))
    env.update(launch_flags(scope,synthetic))
    if requires_exi_profile(scope):
        profile=launch/'exi-test-profile.txt'
        sram=sram_fixture() if requires_sram_profile(scope) else bytes(64)
        create_exi_profile(profile,encode_exi_profile(0xbeef0010,1,0x12345678,8,sram))
        env['UNDERCOVER_V501_EXI_PROFILE']=str(profile)
        print('V505_EXI_TEST_PROFILE created=1 synthetic=1 bytes=64',flush=True)
    if requires_si_profile(scope):
        profile=launch/'si-test-profile.txt'
        with profile.open('xb') as f:f.write(b'UNDERCOVER_SI_PROFILE_V1\nlatency=00000008\nport0=absent\nport1=absent\nport2=absent\nport3=absent\n')
        env['UNDERCOVER_V518_SI_PROFILE']=str(profile)
    rc=command([exe,dol,config],launch/'private.log',20,env=env,cwd=launch)
    if (launch/'private.log').stat().st_size>8*1024*1024:raise BuildError('launch_log')
    raw=(launch/'private.log').read_bytes()
    if synthetic:
        markers=[l for l in raw.splitlines() if l.startswith(b'V426_SYNTHETIC_SWAP')]
        ok=rc==0 and markers==[b'V426_SYNTHETIC_SWAP verified=1']
    else:
        row,ok=audit_owner_start(raw,rc,scope);print(row)
        if scope in REPORT_SCOPES:
            from report_diagnostic_v643 import diagnostic as report_diag
            from audit_v591_memory_init import mapper_diagnostic
            mapping=b'V612_MAPPING_PROFILE accepted=1 mem1=24 mem2=64 mapped_mem2=52 ipc_kib=512 synthetic=1'
            mapping_ok=raw.splitlines().count(mapping)==1
            print(f'V612_MAPPING_LAUNCH verified={int(mapping_ok)}',flush=True)
            ok=ok and mapping_ok
            for diag in (report_diag(raw,rc),mapper_diagnostic(raw,rc)):
                if diag:print(diag,flush=True)
        if scope in ('os-dsp-sc','os-dsp-return'):
            from audit_v575_dsp_sc_frontier import frontier
            census,diag=frontier(raw,rc if 0<=rc<=255 else 255)
            print(census,flush=True)
            if diag:print(diag,flush=True)
        elif scope in ('os-si-sample','os-si-return','os-sram','os-thread','os-audio','os-dsp-stage'):
            from audit_v524_si_sampling import diagnostic
            diag=diagnostic(raw,rc)
            if diag:print(diag,flush=True)
        if scope in EXTERNAL_SCOPES:
            import re
            for line in raw.splitlines():
                if re.fullmatch(rb'V663_EXTERNAL_INVALID reason=[1-9] stage=[0-6]|V663_EXTERNAL_PENDING active=[0-9]{1,10}|V670_VECTOR_REFUSAL mask=[0-9]{1,4}|V667_SI_DISPATCH_INVALID reason=[1-6] stage=[0-6]|V672_SI_ACK_INVALID reason=[1-6] trace=[0-7]|V673_SI_ACK_CALL ordinal=[0-9]{1,2} kind=[0-2]|V677_SI_ACK_WRITE_INVALID trace=[1-7]',line):
                    print(line.decode(),flush=True)
        print(f'V429_WINDOWS_OWNER_SCOPE scope={scope} verified={int(ok)} boot_verified=0',flush=True)
    print(f'V426_WINDOWS_START synthetic={int(synthetic)} verified={int(ok)} boot_verified=0',flush=True)
    if not ok:raise BuildError('launch_gate')
    print(f'V436_WINDOWS_LOADER strict={int(not legacy_loader)} equivalence={int(not legacy_loader)} launch_verified=1 boot_verified=0',flush=True)
    print(f'V441_WINDOWS_TICKS corrected={int(not legacy_ticks)} launch_verified=1 boot_verified=0',flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('upstream',type=Path);p.add_argument('work',type=Path);p.add_argument('--owner-dol',type=Path);p.add_argument('--owner-elf',type=Path);p.add_argument('--owner-scope',choices=tuple(SCOPES),default='startup');p.add_argument('--legacy-loader',action='store_true');p.add_argument('--legacy-ticks',action='store_true');a=p.parse_args()
    try:build(a.upstream,a.work,a.owner_dol.resolve() if a.owner_dol else None,a.owner_elf.resolve() if a.owner_elf else None,a.owner_scope,a.legacy_loader,a.legacy_ticks)
    except BuildError as e:
        print('V426_WINDOWS_FAILED reason='+str(e));return 1
    except (OSError,ValueError,struct.error,subprocess.SubprocessError):
        print('V426_WINDOWS_FAILED reason=host_error');return 1
    return 0
if __name__=='__main__':raise SystemExit(main())
