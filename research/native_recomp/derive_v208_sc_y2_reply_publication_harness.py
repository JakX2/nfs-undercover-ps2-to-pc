#!/usr/bin/env python3
"""V208: publish second original IOS_Open reply at owner-verified Wii guest yield.

The V207 owner trace reached PC 0x80529434 / LR 0x80526CB0 after the
authentic second-Y2 PPCCTRL and Hollywood W1C, with a single completion
queued and SC state unchanged. Permit exactly ONE deterministic native
IOS scheduler step at this already-proven PowerPC yield point. Observe
the real original request-buffer reply, Y1 IRQ and unchanged guest CPU.
Do not synthesize any MMIO, patch PowerPC registers, or force SC ready.
"""
import argparse
from pathlib import Path
from derive_v207_sc_y2_helper_next_harness import (
    derive as previous, OBSERVER as PREVIOUS_OBSERVER,
    NEXT_END as PREVIOUS_END,
)
from derive_v194_osrestore_next_harness import STATE, RESET, once

STOP='''    v207_next_pc=addr;v207_next_lr=ctx.lr;
    v207_sc=sc;v207_queue=queued;v207_reply=replied;
    ++v207_next_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
PUBLISH='''    check(addr==0x80529434u&&ctx.lr==0x80526cb0u&&
          ack&&irq_down&&queued&&open&&!replied&&
          guest&&caller&&coherent&&irqflag&&mapped&&sc==1u&&!ee,
          "V208 verified original second Y2 IOS yield boundary differs");
    using S=undercover::wii::StmIos;
    using B=undercover::wii::IosBus;
    using M=undercover::wii::IpcMailbox;
    using H=undercover::wii::HollywoodIrq;
    const uint32_t req=v183_second_phys;
    check(req!=0u&&ipc70_ram.valid(req,64u)&&
          ipc70_ram.read32(req)==S::Open&&
          ipc70_bus.services().queued_replies()==1u&&
          !ipc70_bus.pending_native_ios_request(),
          "V208 second IOS_Open no longer waiting at genuine guest yield");
    const uint32_t pc_before=ctx.pc,lr_before=ctx.lr,msr_before=ctx.msr;
    const uint64_t inst_before=ctx.inst_count;
    std::array<uint32_t,32> gprs_before{};
    for(unsigned i=0u;i<32u;++i)gprs_before[i]=ctx.gpr[i];
    undercover::wii::IosYieldScheduler scheduler(ipc70_bus);
    const auto service=scheduler.service_one(ctx.msr);
    const auto ctrl_after=ipc70_bus.read32(B::IPC+M::PPCCTRL);
    const auto flag_after=ipc70_bus.read32(B::IPC+H::PPC_FLAG);
    const auto arm=ipc70_bus.read32(B::IPC+M::ARMMSG);
    const bool step=service.progress==S::Pump::Replied&&
          service.serviced_steps==1u;
    const bool wire=arm.has_value()&&*arm==req&&
          ipc70_ram.read32(req)==S::Reply&&
          ipc70_ram.read32(req+8u)==S::Open;
    const uint32_t fd=ipc70_ram.read32(req+4u);
    // IOS_Open can legally return handles for STM, ES or FS devices,
    // not just regular files. Accept only a live handle of a known
    // dispatcher class; retain a negative result as a genuine failure.
    const bool known_fd=fd<S::DescriptorCount;
    const bool immediate=known_fd&&ipc70_bus.services().is_open(fd,S::Device::Immediate);
    const bool event=known_fd&&ipc70_bus.services().is_open(fd,S::Device::Event);
    const bool fs=known_fd&&ipc70_bus.services().is_open(fd,S::Device::Fs);
    const bool file=known_fd&&ipc70_bus.services().is_open(fd,S::Device::File);
    const bool es=known_fd&&ipc70_bus.services().is_open(fd,S::Device::Es);
    const bool opened=immediate||event||fs||file||es;
    // This is an IOS Open with a -4 result. The native Open dispatcher
    // produces Invalid only when its path argument is zero or its mode >3.
    // Classify those original request words without printing private bytes.
    const uint32_t path_arg=ipc70_ram.read32(req+12u);
    const uint32_t mode_arg=ipc70_ram.read32(req+16u);
    const bool sent=v208_send_seen==1u;
    const bool stable_path=sent&&v208_send_path==path_arg;
    const bool stable_mode=sent&&v208_send_mode==mode_arg;
    std::cout<<"V208_Y2_STABLE sent="<<sent
             <<" path="<<stable_path<<" mode="<<stable_mode<<std::endl;
    // Detect a possible argument transposition without exposing guest bytes.
    // Physical IOS memory aliases MEM2 virtual 0x90000000..0x93FFFFFF.
    const bool path_small_mode=path_arg>=1u&&path_arg<=3u;
    const bool mode_mem2virt=mode_arg>=0x90000000u&&mode_arg<0x94000000u;
    const uint32_t mode_as_phys=mode_arg&0x1fffffffu;
    const bool mode_ptr=mode_mem2virt&&ipc70_ram.valid(mode_as_phys,1u);
    const bool mode_slash=mode_ptr&&ipc70_ram.read8(mode_as_phys)==uint8_t('/');
    bool mode_string=false;
    if(mode_slash){
      for(unsigned i=1u;i<64u;++i){
        if(mode_as_phys>0xffffffffu-i||
           !ipc70_ram.valid(mode_as_phys+i,1u))break;
        const uint8_t ch=ipc70_ram.read8(mode_as_phys+i);
        if(ch==0u){mode_string=true;break;}
        if(ch<0x20u||ch>0x7eu)break;
      }
    }
    std::cout<<"V208_Y2_SWAP path_mode="<<path_small_mode
             <<" mode_mem2="<<mode_mem2virt<<" mode_mapped="<<mode_ptr
             <<" mode_slash="<<mode_slash<<" mode_string="<<mode_string
             <<std::endl;
    // The real IOS ABI requires mode at +0x10 and path pointer at +0x0C.
    // Inspect neighboring request words *only as classes*, to distinguish
    // an extra argument word from badly initialized headers.
    const uint32_t alt14=ipc70_ram.read32(req+20u);
    const uint32_t alt18=ipc70_ram.read32(req+24u);
    const uint32_t alt1c=ipc70_ram.read32(req+28u);
    const auto modeclass=[](uint32_t word){return word<=3u;};
    const auto pathclass=[&](uint32_t word){
      const bool v1=word>=0x80000000u&&word<0x81800000u;
      const bool v2=word>=0x90000000u&&word<0x94000000u;
      const bool phys=word<0x01800000u||
           (word>=0x10000000u&&word<0x14000000u);
      if(!(v1||v2||phys))return false;
      const uint32_t addr=(v1||v2)?(word&0x1fffffffu):word;
      if(!ipc70_ram.valid(addr,1u)||
         ipc70_ram.read8(addr)!=uint8_t('/'))return false;
      for(uint32_t i=1u;i<64u;++i){
        if(addr>0xffffffffu-i||!ipc70_ram.valid(addr+i,1u))return false;
        const uint8_t ch=ipc70_ram.read8(addr+i);
        if(ch==0u)return true;
        if(ch<0x20u||ch>0x7eu)return false;
      }
      return false;
    };
    std::cout<<"V208_Y2_LAYOUT ptr0c="<<pathclass(path_arg)
             <<" ptr10="<<pathclass(mode_arg)
             <<" ptr14="<<pathclass(alt14)
             <<" ptr18="<<pathclass(alt18)
             <<" ptr1c="<<pathclass(alt1c)
             <<" mode0c="<<modeclass(path_arg)
             <<" mode10="<<modeclass(mode_arg)
             <<" mode14="<<modeclass(alt14)
             <<" mode18="<<modeclass(alt18)
             <<" mode1c="<<modeclass(alt1c)<<std::endl;
    // Compare against the authenticated prior first SC SYSCONF IOS reply,
    // whose request buffer was accepted by the native filesystem. No raw
    // game string, request pointer or descriptor is printed.
    const bool first_valid=v153_phys!=0u&&ipc70_ram.valid(v153_phys,64u);
    const uint32_t first_path=first_valid?ipc70_ram.read32(v153_phys+12u):0u;
    const uint32_t first_mode=first_valid?ipc70_ram.read32(v153_phys+16u):0xffffffffu;
    const bool first_reply=first_valid&&
          ipc70_ram.read32(v153_phys)==IOS::Reply;
    const bool first_pathok=first_valid&&pathclass(first_path);
    const bool first_modeok=first_valid&&modeclass(first_mode);
    const bool first_open=first_reply&&
          ipc70_bus.services().is_open(v153_fd,IOS::Device::File);
    const bool same_ptr=first_valid&&first_path==mode_arg;
    std::cout<<"V208_Y2_BASE old_valid="<<first_valid
             <<" old_reply="<<first_reply
             <<" old_path="<<first_pathok
             <<" old_mode="<<first_modeok
             <<" old_open="<<first_open
             <<" same_ptr="<<same_ptr<<std::endl;

    const bool path_zero=path_arg==0u;
    const bool path_mapped=!path_zero&&ipc70_ram.valid(path_arg,1u);
    const bool mode_valid=mode_arg<=3u;
    const bool mode_hi8=mode_arg>255u;
    std::cout<<"V208_Y2_OPEN_ARGS zero="<<path_zero
             <<" mapped="<<path_mapped<<" mode_valid="<<mode_valid
             <<" mode_hi8="<<mode_hi8
             <<" invalid="<<(path_zero||!mode_valid)<<std::endl;
    // Examine byte order and pointer-like ranges without disclosing
    // the second request's raw words or pathname.
    const uint32_t swapped_mode=((mode_arg&0x000000ffu)<<24u)|
          ((mode_arg&0x0000ff00u)<<8u)|
          ((mode_arg&0x00ff0000u)>>8u)|
          ((mode_arg&0xff000000u)>>24u);
    const bool swapped_valid=swapped_mode<=3u;
    const bool mem1_virtual=mode_arg>=0x80000000u&&mode_arg<0x81800000u;
    const bool mem2_virtual=mode_arg>=0x90000000u&&mode_arg<0x94000000u;
    const bool mem1_physical=mode_arg>3u&&mode_arg<0x01800000u;
    const bool mem2_physical=mode_arg>=0x10000000u&&mode_arg<0x14000000u;
    const bool same_path=mode_arg==path_arg;
    const bool mode_aligned=(mode_arg&3u)==0u;
    const bool path_slash=path_mapped&&ipc70_ram.read8(path_arg)==uint8_t('/');
    std::cout<<"V208_Y2_MODE swap_valid="<<swapped_valid
             <<" mem1virt="<<mem1_virtual<<" mem2virt="<<mem2_virtual
             <<" mem1phys="<<mem1_physical<<" mem2phys="<<mem2_physical
             <<" same_path="<<same_path<<" aligned="<<mode_aligned
             <<" path_slash="<<path_slash<<std::endl;
    std::cout<<"V208_Y2_KIND immediate="<<immediate<<" event="<<event
             <<" fs="<<fs<<" file="<<file<<" es="<<es
             <<" negative="<<(int32_t(fd)<0)
             <<" result="<<int32_t(fd)<<std::endl;
    const bool signal=ctrl_after.has_value()&&flag_after.has_value()&&
          ((*ctrl_after&M::Y1)!=0u)&&((*ctrl_after&M::Y2)==0u)&&
          ((*flag_after&H::IPC_PPC)!=0u)&&
          ipc70_bus.external_irq_level()&&
          service.broadway_irq_level&&!service.guest_exception_ready;
    const bool drained=ipc70_bus.services().queued_replies()==0u&&
          !ipc70_bus.pending_native_ios_request();
    bool cpu=ctx.pc==pc_before&&ctx.lr==lr_before&&
          ctx.msr==msr_before&&ctx.inst_count==inst_before;
    for(unsigned i=0u;i<32u;++i)cpu&=ctx.gpr[i]==gprs_before[i];
    const bool sc_before=ctx.mmu.read8(ctx.gpr[13]-3176u)==1u;
    std::cout<<"V208_Y2_REPLY step="<<step<<" wire="<<wire
             <<" opened="<<opened<<" signal="<<signal
             <<" drained="<<drained<<" cpu="<<cpu
             <<" sc="<<sc_before<<" pc="<<std::hex<<addr
             <<" lr="<<ctx.lr<<std::dec<<std::endl;
    // Each condition has a distinct source-only assertion label. Owner
    // diagnostics report only the failing category, never guest data.
    check(sent,"V208 second IOS original guest submission not witnessed");
    check(step,"V208 second IOS native reply service step failed");
    check(wire,"V208 second IOS original request reply wire failed");
    check(signal,"V208 second IOS Y1 and Hollywood IRQ publication failed");
    check(drained,"V208 second IOS reply queue did not drain");
    check(cpu,"V208 second IOS service unexpectedly modified guest CPU");
    check(sc_before,"V208 second IOS service unexpectedly changed SC status");
    check(opened,"V208 second IOS opened file descriptor kind differs");
    v207_next_pc=addr;v207_next_lr=ctx.lr;
    v207_sc=sc;v207_queue=queued;v207_reply=replied;
    ++v207_next_seen;
    v208_fd=fd;
    ++v208_reply_seen;
    ctx.is_running=false;throw ExceptionStop{};
  }'''
TRACE_ANCHOR='''void trace_call(uint32_t addr, CPUContext&ctx){'''
TRACE_HOOK='''void trace_call(uint32_t addr, CPUContext&ctx){
  // Genuine ISFS_OpenAsync caller ABI before the IOS_OpenAsync wrapper.
  // Whitelisted return-site classes distinguish NAND open and logging.
  if(v208_async_seen==0u&&v183_second_msg==0u&&
     v208_isfs_seen<32u&&addr==0x804f1e2cu&&
     ctx.gpr[13]==v147_first_r13){
    const uint32_t path=ctx.gpr[3],mode=ctx.gpr[4];
    const bool mapped=ctx.mmu.get_ptr(path)!=nullptr;
    const bool slash=mapped&&ctx.mmu.read8(path)==uint8_t('/');
    const bool modevalid=mode<=3u;
    const bool modemem2=mode>=0x90000000u&&mode<0x94000000u;
    const bool modemapped=modemem2&&ctx.mmu.get_ptr(mode)!=nullptr;
    const bool modeslash=modemapped&&ctx.mmu.read8(mode)==uint8_t('/');
    const bool nand=ctx.lr==0x8051de3cu;
    const bool logging=ctx.lr==0x8051f700u;
    v208_isfs_path=path;v208_isfs_mode=mode;
    ++v208_isfs_seen;
    v208_isfs_inst=ctx.inst_count;
    std::cout<<"V208_Y2_ISFS_ENTRY seen=1 count="<<v208_isfs_seen
             <<" nand="<<nand<<" logging="<<logging
             <<" mapped="<<mapped<<" slash="<<slash
             <<" modevalid="<<modevalid<<" modemem2="<<modemem2
             <<" modeslash="<<modeslash<<std::endl;
    // Keep tracing: inherited authentic call observations must run.
  }
  // Observe only the original second IOS_OpenAsync entry. The real
  // original Wii PowerPC routine receives path in r3 and mode in r4,
  // then writes their physical/path and scalar/mode values to the
  // standard request ABI slots. No original instruction is replaced.
  if(v177_next_seen==1u&&v183_second_msg==0u&&
     v208_async_seen==0u&&addr==0x8051982cu){
    const uint32_t path=ctx.gpr[3],mode=ctx.gpr[4];
    const bool tracked=ctx.gpr[13]==v147_first_r13;
    const bool pathmap=ctx.mmu.get_ptr(path)!=nullptr;
    const bool pathslash=pathmap&&ctx.mmu.read8(path)==uint8_t('/');
    const bool modevalid=mode<=3u;
    const bool modemem2=mode>=0x90000000u&&mode<0x94000000u;
    const bool modemapped=modemem2&&ctx.mmu.get_ptr(mode)!=nullptr;
    const bool modeslash=modemapped&&ctx.mmu.read8(mode)==uint8_t('/');
    // Compare the original ISFS input ABI to the IOS wrapper's input
    // without logging the pathname, pointers or private owner bytes.
    const bool from_isfs=v208_isfs_seen>=1u&&
          ctx.lr==0x804f1eccu&&ctx.inst_count>v208_isfs_inst;
    const bool inherited_mode=from_isfs&&mode==v208_isfs_mode;
    const bool isfs_mapped=from_isfs&&
          ctx.mmu.get_ptr(v208_isfs_path)!=nullptr;
    const bool isfs_slash=isfs_mapped&&
          ctx.mmu.read8(v208_isfs_path)==uint8_t('/');
    bool copied=from_isfs&&isfs_mapped&&pathmap,terminated=false;
    if(copied)for(unsigned i=0u;i<64u;++i){
      if(v208_isfs_path>0xffffffffu-i||path>0xffffffffu-i||
         ctx.mmu.get_ptr(v208_isfs_path+i)==nullptr||
         ctx.mmu.get_ptr(path+i)==nullptr){copied=false;break;}
      const uint8_t a=ctx.mmu.read8(v208_isfs_path+i);
      const uint8_t b=ctx.mmu.read8(path+i);
      if(a!=b){copied=false;break;}
      if(a==0u){terminated=true;break;}
    }
    copied=copied&&terminated;
    std::cout<<"V208_Y2_ISFS_TO_IOS witnessed="<<from_isfs
             <<" mode="<<inherited_mode<<" copy="<<copied
             <<" source_slash="<<isfs_slash<<" dest_slash="<<pathslash
             <<" modevalid="<<modevalid<<std::endl;
    v208_async_path=path;v208_async_mode=mode;
    ++v208_async_seen;
    std::cout<<"V208_Y2_ASYNC_ENTRY seen="<<(v208_async_seen==1u)
             <<" tracked="<<tracked<<" pathmap="<<pathmap
             <<" pathslash="<<pathslash<<" modevalid="<<modevalid
             <<" modemem2="<<modemem2<<" modeslash="<<modeslash
             <<" lr="<<std::hex<<ctx.lr<<std::dec<<std::endl;
    // Preserve inherited trace observers for this same original call.
  }
'''
SEND='''      // Observe only the actual guest-owned second IPC request at PPCMSG.
      // Keep its source arguments privately for a post-ACK stability check.
      const uint32_t a=ipc70_ram.read32(value+12u);
      const uint32_t b=ipc70_ram.read32(value+16u);
      v208_send_path=a;v208_send_mode=b;
      ++v208_send_seen;
      const bool prior_async=v208_async_seen==1u;
      const bool path_same=prior_async&&a==(v208_async_path&0x1fffffffu);
      const bool mode_same=prior_async&&b==v208_async_mode;
      const bool path_is_mode=prior_async&&a==v208_async_mode;
      const bool mode_is_path=prior_async&&b==v208_async_path;
      std::cout<<"V208_Y2_ASYNC_LINK witnessed="<<prior_async
               <<" path_same="<<path_same<<" mode_same="<<mode_same
               <<" path_is_mode="<<path_is_mode
               <<" mode_is_path="<<mode_is_path<<std::endl;
      const bool ptr=a!=0u&&ipc70_ram.valid(a,1u);
      const bool slash=ptr&&ipc70_ram.read8(a)==uint8_t('/');
      // Authentic guest PPCMSG write provenance: no RAM writes, no
      // unpublished pathnames or raw physical request pointers in CI.
      const auto* send_cpu=ipc70_ram.cpu;
      const uint32_t send_pc=send_cpu?send_cpu->pc:0u;
      const uint32_t send_lr=send_cpu?send_cpu->lr:0u;
      const bool pc_text=send_pc>=0x80400000u&&send_pc<0x80600000u;
      const bool lr_text=send_lr>=0x80400000u&&send_lr<0x80600000u;
      const bool request_mem1=value<0x01800000u;
      const bool request_mem2=value>=0x10000000u&&value<0x14000000u;
      const bool reused=value==v153_phys;
      const bool collides=value<v153_phys+64u&&v153_phys<value+64u;
      const bool ablock=ptr&&ipc70_ram.valid(a,64u);
      const bool anested=ablock&&
            ipc70_ram.read32(a)==undercover::wii::StmIos::Open;
      const bool areply=ablock&&
            ipc70_ram.read32(a)==undercover::wii::StmIos::Reply;
      unsigned request_regs=0u,path_regs=0u;
      if(send_cpu)for(unsigned i=3u;i<=10u;++i){
        const uint32_t reg=send_cpu->gpr[i];
        if(reg==value||((reg&0x1fffffffu)==value))
          request_regs|=1u<<(i-3u);
        if(reg==b||((reg&0x1fffffffu)==(b&0x1fffffffu)))
          path_regs|=1u<<(i-3u);
      }
      std::cout<<"V208_Y2_ORIGIN pc_text="<<pc_text
               <<" lr_text="<<lr_text
               <<" mem1="<<request_mem1<<" mem2="<<request_mem2
               <<" reused="<<reused<<" overlap="<<collides
               <<" a_block="<<ablock<<" a_open="<<anested
               <<" a_reply="<<areply
               <<" req_regs="<<request_regs<<" path_regs="<<path_regs
               <<" pc="<<std::hex<<send_pc<<" lr="<<send_lr
               <<std::dec<<std::endl;
      // Classify the genuine guest-selected pathname in the *unexpected*
      // +0x10 word. The actual string stays private, even in failure logs.
      const bool bmem1=b>=0x80000000u&&b<0x81800000u;
      const bool bmem2=b>=0x90000000u&&b<0x94000000u;
      const uint32_t bphys=(bmem1||bmem2)?(b&0x1fffffffu):b;
      std::string candidate;
      bool ascii=false,terminated=false;
      if((bmem1||bmem2)&&ipc70_ram.valid(bphys,1u)){
        ascii=true;
        for(unsigned i=0u;i<64u;++i){
          if(bphys>0xffffffffu-i||
             !ipc70_ram.valid(bphys+i,1u)){ascii=false;break;}
          const uint8_t ch=ipc70_ram.read8(bphys+i);
          if(ch==0u){terminated=true;break;}
          if(ch<0x20u||ch>0x7eu){ascii=false;break;}
          candidate.push_back(char(ch));
        }
      }
      const bool bounded_path=ascii&&terminated&&
            !candidate.empty()&&candidate.front()=='/';
      const bool dev=bounded_path&&candidate.rfind("/dev/",0u)==0u;
      const bool stm=bounded_path&&candidate.rfind("/dev/stm/",0u)==0u;
      const bool fs=bounded_path&&candidate=="/dev/fs";
      const bool es=bounded_path&&candidate=="/dev/es";
      const bool shared2=bounded_path&&candidate.rfind("/shared2/",0u)==0u;
      const bool sysconf=bounded_path&&candidate=="/shared2/sys/SYSCONF";
      const bool title=bounded_path&&candidate.rfind("/title/",0u)==0u;
      std::cout<<"V208_Y2_PATHCLASS valid="<<bounded_path
               <<" dev="<<dev<<" stm="<<stm<<" fs="<<fs
               <<" es="<<es<<" shared2="<<shared2
               <<" sysconf="<<sysconf<<" title="<<title<<std::endl;

      std::cout<<"V208_Y2_SEND witness="<<(v208_send_seen==1u)
               <<" ptr="<<ptr<<" slash="<<slash
               <<" mode_valid="<<(b<=3u)
               <<" mode_mem2="<<(b>=0x90000000u&&b<0x94000000u)
               <<std::endl;
      v183_second_phys=value;'''
NEXT_END='''      using B=undercover::wii::IosBus;
      using M=undercover::wii::IpcMailbox;
      using H=undercover::wii::HollywoodIrq;
      using S=undercover::wii::StmIos;
      const uint32_t req=nwii::runtime::v183_second_phys;
      const auto ctrl=nwii::runtime::ipc70_bus.read32(B::IPC+M::PPCCTRL);
      const auto flag=nwii::runtime::ipc70_bus.read32(B::IPC+H::PPC_FLAG);
      const auto arm=nwii::runtime::ipc70_bus.read32(B::IPC+M::ARMMSG);
      const bool done=ctrl.has_value()&&flag.has_value()&&arm.has_value()&&
            ((*ctrl&M::Y1)!=0u)&&((*ctrl&M::Y2)==0u)&&
            ((*flag&H::IPC_PPC)!=0u)&&*arm==req&&
            nwii::runtime::ipc70_bus.external_irq_level()&&
            nwii::runtime::ipc70_bus.services().queued_replies()==0u&&
            nwii::runtime::ipc70_ram.valid(req,64u)&&
            nwii::runtime::ipc70_ram.read32(req)==S::Reply&&
            nwii::runtime::ipc70_ram.read32(req+8u)==S::Open&&
            nwii::runtime::ipc70_ram.read32(req+4u)==nwii::runtime::v208_fd;
      check(stopped&&nwii::runtime::v196_vector_seen==1u&&
            nwii::runtime::v204_ack_seen==1u&&
            nwii::runtime::v205_flag_seen==1u&&
            nwii::runtime::v206_post_seen==1u&&
            nwii::runtime::v207_next_seen==1u&&
            nwii::runtime::v208_reply_seen==1u&&
            done&&!c.is_running&&c.pc==0x80529434u&&
            c.lr==0x80526cb0u&&
            c.mmu.read8(c.gpr[13]-3176u)==1u,
            "V208 original second IOS reply native publication checkpoint failed");'''

def derive(source:str)->str:
    s=previous(source)
    if PREVIOUS_OBSERVER.count(STOP)!=1 or s.count(PREVIOUS_END)!=1:
        raise ValueError("V208 authenticated original second Y2 yield changed")
    s=once(s,STATE,STATE+'''
 static unsigned v208_reply_seen=0u;
 static uint32_t v208_fd=0u;
 static unsigned v208_send_seen=0u;
 static uint32_t v208_send_path=0u,v208_send_mode=0u;
 static unsigned v208_async_seen=0u;
 static uint32_t v208_async_path=0u,v208_async_mode=0u;
 static unsigned v208_isfs_seen=0u;
 static uint32_t v208_isfs_path=0u,v208_isfs_mode=0u;
 static uint64_t v208_isfs_inst=0u;''')
    s=once(s,RESET,RESET+'''
     nwii::runtime::v208_reply_seen=0u;
     nwii::runtime::v208_fd=0u;
     nwii::runtime::v208_send_seen=0u;
     nwii::runtime::v208_send_path=nwii::runtime::v208_send_mode=0u;
     nwii::runtime::v208_async_seen=0u;
     nwii::runtime::v208_async_path=nwii::runtime::v208_async_mode=0u;
     nwii::runtime::v208_isfs_seen=0u;
     nwii::runtime::v208_isfs_path=nwii::runtime::v208_isfs_mode=0u;
     nwii::runtime::v208_isfs_inst=0u;''')
    s=once(s,TRACE_ANCHOR,TRACE_HOOK)
    s=once(s,'      v183_second_phys=value;',SEND)
    s=once(s,PREVIOUS_OBSERVER,PREVIOUS_OBSERVER.replace(STOP,PUBLISH,1))
    s=once(s,PREVIOUS_END,NEXT_END)
    return s

if __name__=="__main__":
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path)
    p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
