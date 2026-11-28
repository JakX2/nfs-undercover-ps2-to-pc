#include "wii_post_stm_sc_formatter.h"
#include <cassert>
#include <iostream>
#include <limits>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,T=B+0x200u,L=B+0x400u,A=B+0x500u,SP=B+0xe00u;
constexpr uint32_t ins(unsigned op,unsigned r,unsigned a,int n){return (op<<26)|(r<<21)|(a<<16)|(uint32_t(n)&0xffffu);}
constexpr uint32_t bl(uint32_t a,uint32_t b){return 0x48000001u|((b-a)&0x03fffffcu);}
struct Mem {
    std::array<uint8_t,4096> ram{};
    unsigned unresolved_reads=0;
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){if(a>=A+4&&a<A+8)++unresolved_reads;auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=R,lr=L,ctr=1,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
// Independent synthetic instruction effects; no owner code.
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.mmu.write32(A,0x12345678);
    for(unsigned i=14;i<32;++i)c.gpr[i]=0x100u+i;
    constexpr uint32_t link=R+20,stop=T+24,load=ins(32,7,3,4);
    const std::array<IpcDispatchWord,5> parent_path{{{R,R,ins(37,1,1,-704)},{R,R+4,0x7c0802a6},
        {R,R+8,ins(36,0,1,708)},{R,R+12,ins(47,16,1,640)},{R,R+16,bl(R+16,T)}}};
    const std::array<ScFormatterAccess,3> pa{{{R,4,-704,true,true},{R+8,4,4,true,true},{R+12,64,-64,true,true}}};
    std::array<StmFinalSlot,17> ps{};ps[0]={4,32};for(unsigned r=16;r<32;++r)ps[r-15]={int32_t(4*(int(r)-32)),r};
    const std::array<IpcDispatchWord,6> child_path{{{T,T,ins(37,1,1,-48)},{T,T+4,0x7c0802a6},
        {T,T+8,ins(36,0,1,52)},{T,T+12,ins(36,31,1,44)},{T,T+16,ins(14,31,31,1)},{T,T+20,ins(32,6,3,0)}}};
    const std::array<ScFormatterAccess,4> ca{{{T,4,-48,true,true},{T+8,4,4,true,true},{T+12,4,-4,true,true},
        {T+20,4,A,false,false,0x12345678u}}};
    const std::array<StmFinalSlot,2> cs{{{4,32},{-4,31}}};
    for(auto x:parent_path)c.mmu.write32(x.pc,x.word);
    for(auto x:child_path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(stop,load);
    ScFormatterWitness parent({R,L,T,child_path[0].word,704,parent_path,pa,ps});
    assert(parent.begin(c,true)&&parent.poll(c,true));++c.inst_count;assert(parent.entry(c,R,true));
    for(auto x:parent_path){
        ++c.inst_count;assert(parent.before(c,x.pc,x.word,true));
        if(x.pc==R){c.gpr[1]=SP-704;c.mmu.write32(SP-704,SP);}
        else if(x.pc==R+4)c.gpr[0]=L;
        else if(x.pc==R+8)c.mmu.write32(SP+4,L);
        else if(x.pc==R+12)for(unsigned r=16;r<32;++r)c.mmu.write32(SP-64+4*(r-16),c.gpr[r]);
        else if(x.pc==R+16){c.pc=T;c.lr=link;}
    }
    assert(parent.entry(c,T,true)&&parent.reached(c,true));
    const auto parent_sp=c.gpr[1];
    ScFormatterWitness child({T,link,stop,load,48,child_path,ca,cs,{A+4,4}});
    assert(child.begin(c,parent.frame_held(c,true)));
    auto held=[&](bool device=true){return parent.child_frame_held(c,device,c.gpr[1],child.linkage_word());};
    assert(child.poll(c,held()));++c.inst_count;assert(child.entry(c,T,held()));
    for(auto x:child_path){
        ++c.inst_count;
        const bool ok=child.before(c,x.pc,x.word,held());
        if((fault==1&&x.pc==T+12)||(fault==2&&x.pc==T+12)||(fault==3&&x.pc==T+16)||
           (fault==4&&x.pc==T+20)){assert(!ok);return;}
        assert(ok);
        if(x.pc==T){c.gpr[1]-=48;c.mmu.write32(c.gpr[1],parent_sp);}
        else if(x.pc==T+4)c.gpr[0]=link;
        else if(x.pc==T+8){
            c.mmu.write32(parent_sp+4,fault==1?link+4:link);
            if(fault==2)c.mmu.write32(SP-4,0);
        }else if(x.pc==T+12)c.mmu.write32(parent_sp-4,fault==3?0:c.gpr[31]);
        else if(x.pc==T+16){++c.gpr[31];if(fault==4)c.mmu.write32(A,0);}
        else if(x.pc==T+20)c.gpr[6]=0x12345678;
    }
    if(fault==5)c.gpr[3]+=4;
    if(fault==7)c.gpr[1]-=8;
    ++c.inst_count;const bool ok=child.stop_before_load(c,stop,load,held(fault!=6));
    if(fault>=5){assert(!ok);return;}
    assert(ok&&child.reached_load_boundary(c,held())&&!parent.frame_held(c,true));
    assert(child.visits()==6&&child.loads()==1&&child.authenticated_loads()==1&&child.stores()==3&&c.mmu.unresolved_reads==0);
}
// Synthetic joined frames: original computed transfer, partial load and
// two caller stores. The observer predicts effects; the fixture applies
// the independent instruction effects, including deliberately varied bytes.
static void caller_trial(unsigned fault,uint32_t seed,unsigned follow=0,uint64_t parent_delay=0,uint64_t* measured=nullptr){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.mmu.write32(A,T+0x100u);
    for(unsigned i=14;i<32;++i)c.gpr[i]=0x100u+i;
    constexpr uint32_t link=R+20,dst=T+0x100u,site=T+24u,partial=dst+4u;
    const uint32_t stop=dst+(fault>=11?24u:20u);
    const auto parent_sp=SP-704u,child_sp=parent_sp-48u;
    // Cross-frame pointers are established before either witness begins.
    // These are synthetic inputs, not values learned from a stopped CPU.
    const int32_t move_offset=follow>=318?752:follow>=268?(follow==269?-48:864):0;
    const unsigned move_source=follow>=268?14u:1u;
    const uint32_t move_value=uint32_t(int64_t(parent_sp)+move_offset);
    if(follow>=268)c.gpr[14]=move_value;
    c.mmu.write32(child_sp+8,seed);c.mmu.write32(parent_sp+16,0xfacecafeu);
    const std::array<IpcDispatchWord,5> pp{{{R,R,ins(37,1,1,-704)},{R,R+4,0x7c0802a6},
        {R,R+8,ins(36,0,1,708)},{R,R+12,ins(47,16,1,640)},{R,R+16,bl(R+16,T)}}};
    const std::array<ScFormatterAccess,3> pa{{{R,4,-704,true,true},{R+8,4,4,true,true},{R+12,64,-64,true,true}}};
    std::array<StmFinalSlot,17> ps{};ps[0]={4,32};for(unsigned r=16;r<32;++r)ps[r-15]={int32_t(4*(int(r)-32)),r};
    for(auto x:pp)c.mmu.write32(x.pc,x.word);
    ScFormatterWitness parent({R,L,T,ins(37,1,1,-48),704,pp,pa,ps});
    // Child entry word must be mapped before parent.begin.
    c.mmu.write32(T,ins(37,1,1,-48));
    assert(parent.begin(c,true)&&parent.poll(c,true));++c.inst_count;assert(parent.entry(c,R,true));
    for(auto x:pp){
        ++c.inst_count;assert(parent.before(c,x.pc,x.word,true));
        if(x.pc==R){c.gpr[1]=parent_sp;c.mmu.write32(parent_sp,SP);}
        else if(x.pc==R+4)c.gpr[0]=L;
        else if(x.pc==R+8)c.mmu.write32(SP+4,L);
        else if(x.pc==R+12)for(unsigned r=16;r<32;++r)c.mmu.write32(SP-64+4*(r-16),c.gpr[r]);
        else {c.pc=T;c.lr=link;}
    }
    assert(parent.entry(c,T,true)&&parent.reached(c,true));
    c.inst_count+=parent_delay;
    const std::array<IpcDispatchWord,6> cp{{{T,T,ins(37,1,1,-48)},{T,T+4,0x7c0802a6},
        {T,T+8,ins(36,0,1,52)},{T,T+12,ins(44,5,1,8)},{T,T+16,ins(32,6,3,0)},{T,T+20,0x7cc903a6}}};
    const std::array<ScFormatterAccess,4> ca{{{T,4,-48,true,true},{T+8,4,4,true,true},
        {T+12,2,-40,true,true},{T+16,4,A,false,false,dst}}};
    const std::array<StmFinalSlot,1> cs{{{4,32}}};
    const uint32_t branch=0x4e800420u,body=ins(14,7,0,9),load=ins(32,9,1,8);
    const uint32_t guard=follow>=13?(31u<<26)|((follow>=15&&follow!=22?0u:7u)<<21)|(8u<<16)|(467u<<1):0x60000000u;
    std::vector<IpcDispatchWord> mid(cp.begin(),cp.end());mid.push_back({T,site,branch});mid.push_back({T,dst,body});
    std::vector<IpcDispatchWord> full(mid);full.push_back({T,partial,load});
    full.push_back({T,dst+8,ins(36,7,1,64)});full.push_back({T,dst+12,ins(36,9,1,68)});
    full.push_back({T,dst+16,ins(14,8,7,1)});
    if(fault>=11)full.push_back({T,dst+20,ins(32,10,1,fault==11?68:fault==12?8:fault==13?72:64)});
    std::vector<ScFormatterAccess> more(ca.begin(),ca.end());
    more.push_back({partial,4,-40,true,false});
    more.push_back({dst+8,4,16,true,true});
    more.push_back({dst+12,4,20,true,true});
    if(fault>=11)more.push_back({dst+20,4,fault==11?20:fault==12?-40:fault==13?24:16,true,false});
    if(fault==14)std::swap(more[5],more[7]); // reordered proof must not authorize future writes
    for(auto x:full)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(stop,guard);
    ScFormatterWitness child({T,link,site,branch,48,cp,ca,cs,{}, {dst,body,follow?0x300u:0x200u}});
    auto held=[&](){return child.has_caller_stores()?parent.child_frame_held_with_stores(c,true,child):
        parent.child_frame_held(c,true,c.gpr[1],child.linkage_word());};
    assert(child.begin(c,parent.frame_held(c,true))&&child.poll(c,held()));++c.inst_count;assert(child.entry(c,T,held()));
    c.gpr[5]=0; // Must match the initial state captured by both witnesses.
    for(auto x:cp){
        ++c.inst_count;assert(child.before(c,x.pc,x.word,held()));
        if(x.pc==T){c.gpr[1]=child_sp;c.mmu.write32(child_sp,parent_sp);}
        else if(x.pc==T+4)c.gpr[0]=link;
        else if(x.pc==T+8)c.mmu.write32(parent_sp+4,link);
        else if(x.pc==T+12){
            // A halfword store leaves the other two bytes physically untouched.
            *c.mmu.get_ptr(child_sp+8)=0;
            *c.mmu.get_ptr(child_sp+9)=0;
        }
        else if(x.pc==T+16)c.gpr[6]=dst;
        else c.ctr=dst;
    }
    ++c.inst_count;assert(child.stop_before_control(c,site,branch,held()));
    c.pc=dst;assert(child.control_transfer_poll(c,held()));++c.inst_count;assert(child.control_destination_entry(c,dst,held()));
    ScFormatterExpectation m{T,link,partial,load,48,mid,ca,cs,{0,4,true,-40}};
    assert(child.resume_control_path(c,m,held()));++c.inst_count;assert(child.before(c,dst,body,held()));c.gpr[7]=9;
    ++c.inst_count;assert(child.stop_before_load(c,partial,load,held()));
    ScFormatterExpectation next{T,link,stop,guard,48,full,more,cs,{0,0,false,0,true}};
    if(fault==1)more[5].address=640;
    if(fault==2)more[6].address=16;
    if(fault==3)more[5].address=4;
    if(fault==4)more[4].address=-36;
    if(fault==5)more[5].address=704;
    if(fault==6)full[8].word^=1u;
    if(fault==17)more[5].address=std::numeric_limits<int64_t>::max()-3;
    if(fault==18)more[7].address=std::numeric_limits<int64_t>::max()-3;
    if(fault==19)more[7].address=std::numeric_limits<int64_t>::min();
    if(fault==20)more[7].address=17;
    const bool resumed=child.resume_stack_path(c,next,parent,fault==7?0xffffu:0xffff0000u,held());
    if((fault>=1&&fault<=7)||fault==13||fault==14||fault>=17){assert(!resumed);return;}assert(resumed);
    c.gpr[9]=seed&0xffffu; // Actual original load would read these live bytes.
    ++c.inst_count;assert(child.before(c,dst+8,full[9].word,held()));
    c.mmu.write32(parent_sp+16,fault==8?10u:9u);
    if(fault==9)c.mmu.write32(parent_sp+24,0x11u);
    ++c.inst_count;const bool ok=child.before(c,dst+12,full[10].word,held());
    if(fault==8||fault==9){assert(!ok);return;}assert(ok);
    c.mmu.write32(parent_sp+20,fault==10?c.gpr[9]^1u:c.gpr[9]);
    ++c.inst_count;const bool ok2=child.before(c,dst+16,full[11].word,held());
    if(fault==10){assert(!ok2);return;}assert(ok2);c.gpr[8]=10;
    if(fault>=11){
        ++c.inst_count;assert(child.before(c,dst+20,full[12].word,held()));
        c.gpr[10]=fault==15?9u:seed&0xffffu;
        if(fault==16)c.gpr[10]^=1u;
    }
    ++c.inst_count;
    const bool stopped=child.stop_before_instruction(c,stop,guard,held());
    if(fault==16){assert(!stopped);return;}
    assert(stopped&&child.reached_instruction_boundary(c,held()));
    assert(child.caller_store_count()==2&&child.visits()==(fault>=11?13u:12u)&&child.loads()==(fault>=11?3u:2u)&&child.stores()==5);
    assert(c.mmu.read32(parent_sp+20)==(seed&0xffffu));
    assert(!parent.child_frame_held(c,true,c.gpr[1],child.linkage_word()));
    if(!follow)return;
    const unsigned extra=follow==1?57u:follow==2?58u:2u;
    std::vector<IpcDispatchWord> later(full);later.push_back({T,stop,guard});
    std::vector<ScFormatterAccess> later_access(more);
    for(unsigned i=0;i<extra;++i){
        const auto pc=stop+4u*(i+1u);
        const int offset=follow==3?72:follow==4?12:follow==10?8:68;
        const auto word=ins(follow==11?36:32,12,1,offset);
        later.push_back({T,pc,word});
        later_access.push_back({pc,4,offset-48,true,follow==11});
        c.mmu.write32(pc,word);
    }
    const auto end=stop+4u*(extra+1u);
    const auto end_word=follow>=15?ins(14,1,1,follow==23?44:48):guard;
    c.mmu.write32(end,end_word);
    ScFormatterExpectation later_e{T,link,end,end_word,48,later,later_access,cs,{0,0,false,0,true}};
    if(follow==5)later[0].word^=1u;
    if(follow==6)later_access[0].address=-44;
    if(follow==8)later_e.target=stop;
    if(follow==9)std::swap(later_access[later_access.size()-1],later_access[later_access.size()-2]);
    const bool continued=child.resume_instruction_path(c,later_e,held()&&follow!=12);
    if(follow==2||follow==3||follow==4||follow==5||follow==6||follow==8||follow==9||follow==11||follow==12){
        assert(!continued);return;
    }
    assert(continued);
    // Independent synthetic CPU effect of the boundary instruction.
    // The usual ori is a no-op; the new mtlr copies all 32 source bits.
    if(follow>=13)c.lr=follow>=15&&follow!=22?link:follow==14?8u:9u;
    for(unsigned i=0;i<extra;++i){
        ++c.inst_count;const auto& row=later[full.size()+1u+i];
        const bool ok=child.before(c,row.pc,row.word,held());
        if((follow==7&&i==1)||(follow==14&&i==0)){assert(!ok);return;}
        assert(ok);c.gpr[12]=(seed&0xffffu)^unsigned(follow==7);
    }
    ++c.inst_count;
    assert(child.stop_before_instruction(c,end,end_word,held())&&child.reached_instruction_boundary(c,held()));
    assert(child.caller_store_count()==2&&child.visits()==full.size()+1u+extra&&child.loads()==2u+extra&&child.stores()==5);
    assert(c.mmu.read32(parent_sp+20)==(seed&0xffffu));
    if(follow<15)return;
    const auto ret=end+(follow==24?8u:4u),ret_word=follow==17?0x60000000u:0x4e800020u;
    c.mmu.write32(ret,ret_word);
    auto epilogue=later;epilogue.push_back({T,end,end_word});
    auto epi_access=later_access;
    if(follow==18)epi_access.push_back({end,4,20,true,false});
    if(follow==25)epilogue[0].word^=1u;
    ScFormatterExpectation ep{T,link,ret,ret_word,48,epilogue,epi_access,cs,{0,0,false,0,true}};
    const bool released=follow==16?child.resume_instruction_path(c,ep,held()):
        child.resume_frame_release(c,ep,held());
    if(follow==16||follow==17||follow==18||follow==22||follow==23||follow==24||follow==25){
        assert(!released);return;
    }
    assert(released&&child.frame_released()&&child.expected_sp()==parent_sp&&c.gpr[1]==child_sp);
    // Independent execution of addi r1,r1,48; wrong SP or corrupted frame
    // bytes are rejected by the next boundary even after prediction.
    c.gpr[1]=parent_sp-(follow==19?4u:0u);
    if(follow==20)c.mmu.write32(parent_sp+20,0);
    if(follow==21)c.mmu.write32(child_sp+8,0);
    if(follow==27)c.gpr[14]^=1u;
    ++c.inst_count;
    const bool ret_held=child.stop_before_instruction(c,ret,ret_word,held());
    if(follow==19||follow==20||follow==21||follow==27){assert(!ret_held);return;}
    assert(ret_held&&child.reached_instruction_boundary(c,held())&&child.visits()==epilogue.size());
    assert(c.lr==link&&c.gpr[1]==parent_sp&&c.mmu.read32(parent_sp+20)==(seed&0xffffu));
    if(follow==26){assert(!child.resume_instruction_path(c,ep,held()));return;}
    if(follow<28)return;
    constexpr uint32_t guard_word=0x44000002u;
    const auto caller_word=follow>=51?
        ins(follow==59?35u:34u,follow==60?14u:3u,1,follow==61?18:19):
        ins(32,3,1,16);
    const auto call_word=pp.back().word;
    c.mmu.write32(link,follow>=40?caller_word:guard_word);
    if(follow==30)c.mmu.write32(link,0x60000000u);
    if(follow==43)c.mmu.write32(link-4,0x60000000u);
    const bool armed=follow>=40?
        child.arm_caller_arrival(c,follow==41?R+4:R,link,follow==44?guard_word:caller_word,
                                 follow==42?call_word^4u:call_word,held()):
        child.arm_native_return(c,link+(follow==29?4u:0u),guard_word,held()&&follow!=31);
    if(follow==29||follow==30||follow==31||(follow>=41&&follow<=44)){assert(!armed);return;}
    assert(armed&&child.stage()==6u&&child.visits()==epilogue.size());
    assert(c.pc==dst); // observer has not redirected the guest
    // Independent architectural effect of the original blr.
    c.pc=follow==32?link+4u:link;
    if(follow==33)++c.inst_count;
    if(follow==34)c.gpr[3]^=1u;
    if(follow==35)c.mmu.write32(parent_sp+20,0u);
    if(follow==36)c.mmu.write32(link,0x60000000u);
    if(follow==37)c.lr^=4u;
    const bool arrived=child.native_return_poll(c,held()&&follow!=38);
    if(follow>=32&&follow<=38){assert(!arrived);return;}
    assert(arrived&&child.reached_native_return(c,held())&&child.visits()==epilogue.size()+1u);
    if(follow==39){assert(!child.native_return_poll(c,held()));return;} // no double counting
    if(follow<40)return;
    c.inst_count+=follow==45?2u:1u;
    if(follow==46)c.pc+=4;
    const bool entry=child.caller_arrival_entry(c,link,held());
    if(follow==45||follow==46){assert(!entry);return;}
    assert(entry&&child.stage()==8u);
    c.inst_count+=follow==47?2u:1u;
    if(follow==48)c.gpr[3]=9; // caller load body must not have run
    if(follow==49)c.mmu.write32(link,guard_word);
    const bool arrival=child.stop_before_caller_instruction(c,link,caller_word,held());
    if(follow>=47&&follow<=49){assert(!arrival);return;}
    assert(arrival&&child.reached_caller_arrival(c,held())&&child.visits()==epilogue.size()+1u);
    if(follow==50){assert(!child.stop_before_caller_instruction(c,link,caller_word,held()));return;}
    if(follow<51)return;
    const unsigned saved_dest=follow==86?14u:follow==87?2u:16u;
    const auto next_pc=link+4u,next_word=follow>=85?
        (31u<<26)|(3u<<21)|(saved_dest<<16)|(3u<<11)|(444u<<1):
        follow>=67?ins(14,4,3,-10):0x60000000u;
    c.mmu.write32(next_pc,follow==54?guard_word:next_word);
    const auto offset=follow==52?18:follow==53?24:follow==62?704:19;
    const bool caller_load=child.resume_caller_byte(c,offset,follow==55?8u:9u,
                                            next_pc+(follow==56?4u:0u),next_word,held()&&follow!=57);
    if((follow>=52&&follow<=57)||(follow>=59&&follow<=62)){assert(!caller_load);return;}
    assert(caller_load&&child.stage()==10u&&c.gpr[3]==A);
    c.gpr[3]=follow==58?8u:9u; // independent native lbz effect
    if(follow==63)c.mmu.write32(parent_sp+16,8u);
    if(follow==64)c.mmu.write32(next_pc,guard_word);
    c.inst_count+=follow==65?2u:1u;
    const bool loaded=child.stop_after_caller_byte(c,next_pc,next_word,held());
    if(follow==58||(follow>=63&&follow<=65)){assert(!loaded);return;}
    assert(loaded&&child.reached_caller_byte(c,held())&&child.visits()==epilogue.size()+1u);
    if(follow==66){assert(!child.stop_after_caller_byte(c,next_pc,next_word,held()));return;}
    if(follow<67)return;
    const auto cmp_pc=next_pc+4u,cmp_word=ins(11,0,follow>=85?saved_dest:4u,0),end_pc=cmp_pc+4u;
    const auto end_word2=follow>=93?
        (16u<<26)|((follow==97?8u:12u)<<21)|((follow==94||follow>=108?0u:1u)<<16)|
        (follow==99?0xfff0u:16u)|unsigned(follow==98):
        0x60000000u;
    c.mmu.write32(cmp_pc,follow==70?guard_word:cmp_word);
    c.mmu.write32(end_pc,end_word2);
    const std::array<CallerIntegerInput,1> in1{{{3,follow==72?8u:9u}}},in2{{{follow>=85?saved_dest:4u,follow>=85?9u:follow==78?0u:0xffffffffu}}};
    std::array<ScCallerIntegerStep,2> sequence{{{next_pc,next_word,in1},{cmp_pc,cmp_word,in2}}};
    if(follow==71)sequence[1].pc+=4u;
    if(follow==73)sequence[0].inputs={};
    const auto path=follow==68?std::span<const ScCallerIntegerStep>{}:std::span<const ScCallerIntegerStep>{sequence};
    const auto armed_integer=child.resume_caller_integers(c,path,end_pc+(follow==69?4u:0u),end_word2,held());
    if((follow>=68&&follow<=73)||follow==86||follow==87){assert(!armed_integer);return;}
    assert(armed_integer&&child.stage()==12u&&child.caller_integer_visits()==0u&&c.gpr[4]!=0xffffffffu);
    if(follow>=85)c.gpr[saved_dest]=follow==88?8u:9u;
    else c.gpr[4]=follow==74?0u:0xffffffffu;
    if(follow==89)c.mmu.write32(SP-64u,0u);
    if(follow==90)c.gpr[17]^=1u;
    if(follow==75)c.mmu.write32(parent_sp+16,8u);
    if(follow==76)c.mmu.write32(next_pc,guard_word);
    c.inst_count+=follow==77?2u:1u;
    const auto second=child.caller_integer_boundary(c,cmp_pc,cmp_word,held());
    if((follow>=74&&follow<=78)||(follow>=88&&follow<=90)){assert(!second);return;}
    assert(second&&child.caller_integer_visits()==1u&&child.stage()==12u);
    c.cr[0]={follow<85,follow>=85,false,false};
    if(follow==79)c.cr[0].lt=false;
    if(follow==80)c.gpr[8]^=1u;
    if(follow==81)c.mmu.write32(end_pc,guard_word);
    if(follow==91)c.gpr[16]=0x110u; // restoring early is also a wrong instruction effect
    if(follow==92)c.mmu.write32(SP-64u,0u);
    ++c.inst_count;
    const auto finished=child.caller_integer_boundary(c,end_pc+(follow==82?4u:0u),end_word2,held()&&follow!=83);
    if((follow>=79&&follow<=83)||follow==91||follow==92){assert(!finished);return;}
    assert(finished&&child.reached_caller_integers(c,held())&&child.caller_integer_visits()==2u);
    assert(child.visits()==epilogue.size()+1u);
    if(follow==84){assert(!child.caller_integer_boundary(c,end_pc,end_word2,held()));return;}
    if(follow<93)return;
    const auto target_pc=end_pc+16u,fallthrough=end_pc+4u;
    const bool taken=follow!=94&&follow<108;
    const auto chosen=taken?target_pc:fallthrough,other=taken?fallthrough:target_pc;
    const uint32_t boundary_word=follow>=108?
        (16u<<26)|(12u<<21)|(1u<<16)|(follow==113?12u:24u):0x60000000u;
    c.mmu.write32(chosen,follow==96?guard_word:boundary_word);
    c.mmu.write32(other,follow==100?boundary_word:guard_word);
    const bool branch_armed=child.resume_caller_branch(c,0x100u,follow==95?!taken:taken,
        chosen,boundary_word,held());
    if(follow>=95&&follow<=100){assert(!branch_armed);return;}
    assert(branch_armed&&child.stage()==14u&&c.pc==link);
    // A local forward branch enters the selected label without dispatcher
    // re-entry. No CPU PC assignment or condition modification is needed.
    if(follow==103)c.cr[0].gt=false;
    if(follow==104)c.mmu.write32(other,boundary_word);
    if(follow==105)c.mmu.write32(end_pc,guard_word);
    c.inst_count+=follow==102?2u:1u;
    const auto branch_stopped=child.stop_after_caller_branch(c,follow==101?other:chosen,boundary_word,held()&&follow!=106);
    if(follow>=101&&follow<=106){assert(!branch_stopped);return;}
    assert(branch_stopped&&child.reached_caller_branch(c,held())&&child.caller_integer_visits()==2u);
    if(follow==107){assert(!child.stop_after_caller_branch(c,chosen,boundary_word,held()));return;}
    if(follow<108)return;
    assert(child.caller_branch_visits()==1u);
    const auto second_target=chosen+(follow==113?12u:24u),second_other=chosen+4u;
    const uint32_t after_branch=follow>=122?ins(11,0,16,9):0x60000000u;
    if(follow!=113)c.mmu.write32(second_target,after_branch);
    c.mmu.write32(second_other,follow==112?after_branch:guard_word);
    if(follow==111)c.mmu.write32(other,after_branch);
    const bool second_armed=child.resume_caller_branch(c,follow==110?0x104u:0x100u,
        follow!=109,second_target,after_branch,held());
    if(follow>=109&&follow<=113){assert(!second_armed);return;}
    assert(second_armed&&child.stage()==14u&&child.caller_branch_visits()==1u&&c.pc==link);
    if(follow==116)c.mmu.write32(other,after_branch);
    if(follow==117)c.mmu.write32(second_other,after_branch);
    if(follow==118)c.cr[0].gt=false;
    if(follow==119)c.mmu.write32(chosen,after_branch);
    c.inst_count+=follow==115?2u:1u;
    const bool second_stopped=child.stop_after_caller_branch(c,follow==114?second_other:second_target,after_branch,held()&&follow!=120);
    if(follow>=114&&follow<=120){assert(!second_stopped);return;}
    assert(second_stopped&&child.reached_caller_branch(c,held())&&child.caller_branch_visits()==2u);
    assert(!child.caller_post_fourth_tick_budget());
    if(follow==121){assert(!child.resume_caller_branch(c,0x100u,true,second_target,after_branch,held()));return;}
    if(follow<122)return;
    const auto post_end=second_target+4u;
    const auto post_word=follow>=139?(16u<<26)|((follow==144?8u:12u)<<21)|(follow==145?0xfff0u:16u)|unsigned(follow==146):0x60000000u;
    c.mmu.write32(post_end,follow==125?guard_word:post_word);
    const std::array<CallerIntegerInput,1> post_input{{{16,follow==126?8u:9u}}};
    std::array<ScCallerIntegerStep,1> post_sequence{{{second_target,after_branch,post_input}}};
    if(follow==127)post_sequence[0].pc+=4u;
    if(follow==128)post_sequence[0].inputs={};
    const auto post_path=follow==123?std::span<const ScCallerIntegerStep>{}:std::span<const ScCallerIntegerStep>{post_sequence};
    const bool post_armed=child.resume_caller_post_integers(c,post_path,post_end+(follow==124?4u:0u),post_word,held()&&follow!=129);
    if(follow>=123&&follow<=129){assert(!post_armed);return;}
    assert(post_armed&&child.stage()==16u&&child.caller_post_integer_visits()==0u);
    c.cr[0]={false,false,true,false};
    if(follow==130)c.cr[0].eq=false;
    if(follow==131)c.mmu.write32(other,post_word);
    if(follow==132)c.mmu.write32(second_other,post_word);
    if(follow==133)c.mmu.write32(second_target,guard_word);
    if(follow==134)c.gpr[16]^=1u;
    c.inst_count+=follow==135?2u:1u;
    const bool post_stopped=child.caller_post_integer_boundary(c,post_end+(follow==136?4u:0u),post_word,held()&&follow!=137);
    if(follow>=130&&follow<=137){assert(!post_stopped);return;}
    assert(post_stopped&&child.reached_caller_post_integers(c,held())&&child.caller_post_integer_visits()==1u);
    assert(child.caller_integer_visits()==2u&&child.caller_branch_visits()==2u);
    if(measured)*measured=child.caller_parent_baseline();
    if(parent_delay)assert(child.caller_parent_baseline()==128u&&parent.frame_age(c)==128u&&child.caller_parent_tick_limit()==128u);
    if(follow==138){assert(!child.caller_post_integer_boundary(c,post_end,post_word,held()));return;}
    if(follow<139)return;
    const auto third_target=post_end+16u,third_next=post_end+4u;
    const uint32_t third_boundary=follow>=158?
        (16u<<26)|((follow==164?8u:12u)<<21)|((follow==159?0u:2u)<<16)|
        (follow==165?0xfff0u:follow==166?12u:24u)|unsigned(follow==167):0x60000000u;
    c.mmu.write32(third_target,follow==143?third_boundary:guard_word);
    c.mmu.write32(third_next,follow==142?guard_word:third_boundary);
    if(follow==147)c.mmu.write32(other,third_boundary);
    const bool third_armed=child.resume_caller_branch(c,follow==141?0x104u:0x100u,follow==140,
        third_next,third_boundary,held());
    if(follow>=140&&follow<=147){assert(!third_armed);return;}
    assert(third_armed&&child.stage()==14u&&child.caller_branch_visits()==2u);
    if(follow==249){
        assert(parent_delay&&child.caller_parent_tick_limit()==129u);
        c.inst_count+=2u;
        assert(!held());
        assert(!child.stop_after_caller_branch(c,third_next,third_boundary,held()));
        return;
    }
    if(follow==150)c.cr[0].eq=false;
    if(follow==151)c.mmu.write32(other,third_boundary);
    if(follow==152)c.mmu.write32(second_other,third_boundary);
    if(follow==153)c.mmu.write32(third_target,third_boundary);
    if(follow==154)c.mmu.write32(second_target,guard_word);
    if(follow==155)c.mmu.write32(post_end,guard_word);
    c.inst_count+=follow==149?2u:1u;
    const bool third_stopped=child.stop_after_caller_branch(c,follow==148?third_target:third_next,third_boundary,held()&&follow!=156);
    if(follow>=148&&follow<=156){assert(!third_stopped);return;}
    assert(third_stopped&&child.reached_caller_branch(c,held())&&child.caller_branch_visits()==3u);
    assert(!child.caller_post_fourth_tick_budget());
    if(parent_delay)assert(parent.frame_age(c)==129u&&child.caller_parent_tick_limit()==129u);
    assert(child.caller_integer_visits()==2u&&child.caller_post_integer_visits()==1u);
    if(follow==157){assert(!child.resume_caller_branch(c,0x100u,false,third_next,third_boundary,held()));return;}
    if(follow<158)return;
    const auto fourth_target=third_next+(follow==166?12u:24u),fourth_fallthrough=third_next+4u;
    const bool fourth_taken=follow!=159;
    const auto fourth_next=fourth_taken?fourth_target:fourth_fallthrough;
    const auto fourth_other=fourth_taken?fourth_fallthrough:fourth_target;
    const uint32_t fourth_boundary=follow>=180?ins(14,5,16,1):0x60000000u;
    if(follow!=166)c.mmu.write32(fourth_next,follow==162?guard_word:fourth_boundary);
    c.mmu.write32(fourth_other,follow==163?fourth_boundary:guard_word);
    if(follow==168)c.mmu.write32(second_other,fourth_boundary);
    const bool fourth_armed=child.resume_caller_branch(c,follow==161?0x104u:0x100u,
        follow==160?!fourth_taken:fourth_taken,fourth_next,fourth_boundary,held());
    if(follow>=160&&follow<=168){assert(!fourth_armed);return;}
    assert(fourth_armed&&child.stage()==14u&&child.caller_branch_visits()==3u);
    if(follow==171)c.cr[0].eq=false;
    if(follow==172)c.mmu.write32(other,fourth_boundary);
    if(follow==173)c.mmu.write32(second_other,fourth_boundary);
    if(follow==174)c.mmu.write32(third_target,fourth_boundary);
    if(follow==175)c.mmu.write32(fourth_other,fourth_boundary);
    if(follow==176)c.mmu.write32(second_target,guard_word);
    if(follow==177)c.mmu.write32(post_end,guard_word);
    c.inst_count+=follow==170?2u:1u;
    const bool fourth_stopped=child.stop_after_caller_branch(c,follow==169?fourth_other:fourth_next,fourth_boundary,held()&&follow!=178);
    if(follow>=169&&follow<=178){assert(!fourth_stopped);return;}
    assert(fourth_stopped&&child.reached_caller_branch(c,held())&&child.caller_branch_visits()==4u);
    assert(child.caller_post_fourth_tick_budget()==0u);
    assert(child.caller_integer_visits()==2u&&child.caller_post_integer_visits()==1u);
    if(follow==179){assert(!child.resume_caller_branch(c,0x100u,true,fourth_next,fourth_boundary,held()));return;}
    if(follow<180)return;
    const auto mix_cmp=fourth_next+4u,mix_branch=fourth_next+8u,mix_other=mix_branch+4u,mix_end=mix_branch+16u;
    const auto mix_cmp_word=ins(11,0,5,10);
    const auto mix_branch_word=(16u<<26)|((follow==190?8u:12u)<<21)|(2u<<16)|16u|unsigned(follow==191);
    const uint32_t mix_end_word=follow>=207?ins(follow==213?35u:34u,follow==214?14u:6u,1,19):0x60000000u;
    c.mmu.write32(mix_cmp,mix_cmp_word);
    c.mmu.write32(mix_branch,mix_branch_word);
    c.mmu.write32(mix_other,follow==187?mix_end_word:guard_word);
    c.mmu.write32(mix_end,follow==186?guard_word:mix_end_word);
    const std::array<CallerIntegerInput,1> mix_in1{{{16,follow==184?8u:9u}}},mix_in2{{{5,follow==194?9u:10u}}};
    std::array<ScCallerMixedStep,3> mix{{
        {fourth_next,fourth_boundary,mix_in1,mix_cmp,0u,false},
        {mix_cmp,mix_cmp_word,mix_in2,mix_branch,0u,false},
        {mix_branch,mix_branch_word,{},mix_end,mix_other,true}
    }};
    if(follow==183)mix[0].next_pc+=4u;
    if(follow==185)mix[0].inputs={};
    if(follow==188)mix[2].other_pc=third_target;
    if(follow==189)mix[2].taken=false;
    const auto mix_path=follow==181?std::span<const ScCallerMixedStep>{}:std::span<const ScCallerMixedStep>{mix};
    const bool mix_armed=child.resume_caller_mixed(c,mix_path,mix_end+(follow==182?4u:0u),mix_end_word,held()&&follow!=192);
    if(follow>=181&&follow<=192){assert(!mix_armed);return;}
    assert(mix_armed&&child.stage()==18u&&child.caller_mixed_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==1u);
    c.gpr[5]=follow==193?9u:10u;
    if(follow==195)c.mmu.write32(mix_other,mix_end_word);
    if(follow==196)c.mmu.write32(other,mix_end_word);
    c.inst_count+=follow==197?2u:1u;
    const bool mix_one=child.caller_mixed_boundary(c,mix_cmp,mix_cmp_word,held());
    if(follow>=193&&follow<=197){assert(!mix_one);return;}
    assert(mix_one&&child.caller_mixed_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==2u);
    c.cr[0]={false,false,true,false};
    if(follow==198)c.cr[0].eq=false;
    if(follow==199)c.mmu.write32(mix_branch,guard_word);
    ++c.inst_count;
    const bool mix_two=child.caller_mixed_boundary(c,mix_branch,mix_branch_word,held());
    if(follow==198||follow==199){assert(!mix_two);return;}
    assert(mix_two&&child.caller_mixed_visits()==2u);
    assert(child.caller_post_fourth_tick_budget()==3u);
    if(follow==202)c.mmu.write32(mix_other,mix_end_word);
    if(follow==203)c.gpr[5]^=1u;
    if(follow==204)c.mmu.write32(fourth_other,mix_end_word);
    c.inst_count+=follow==201?2u:1u;
    const bool mix_three=child.caller_mixed_boundary(c,follow==200?mix_other:mix_end,mix_end_word,held()&&follow!=205);
    if(follow>=200&&follow<=205){assert(!mix_three);return;}
    assert(mix_three&&child.reached_caller_mixed(c,held())&&child.caller_mixed_visits()==3u);
    assert(child.caller_post_fourth_tick_budget()==3u);
    assert(child.caller_mixed_integers()==2u&&child.caller_mixed_taken()==1u&&child.caller_mixed_fallthrough()==0u);
    if(follow==206){assert(!child.caller_mixed_boundary(c,mix_end,mix_end_word,held()));return;}
    if(follow<207)return;
    const auto byte_next=mix_end+4u;
    const uint32_t byte_next_word=follow>=228?ins(11,0,6,9):0x60000000u;
    const auto post_mix_branch=byte_next+4u,post_mix_other=post_mix_branch+4u,post_mix_end=post_mix_branch+16u;
    const uint32_t post_mix_word=(16u<<26)|(12u<<21)|(2u<<16)|16u;
    const uint32_t post_mix_end_word=follow>=250?
        (31u<<26)|(move_source<<21)|(7u<<16)|(move_source<<11)|(444u<<1)|unsigned(follow==254):0x60000000u;
    c.mmu.write32(byte_next,follow==211?guard_word:byte_next_word);
    c.mmu.write32(byte_next+4u,follow>=228?post_mix_word:follow==212?byte_next_word:guard_word);
    const std::array<CallerIntegerInput,1> post_mix_inputs{{{6,follow==234?8u:9u}}};
    std::array<ScCallerMixedStep,2> post_mix{{
        {byte_next,byte_next_word,post_mix_inputs,post_mix_branch,0u,false},
        {post_mix_branch,post_mix_word,{},post_mix_end,post_mix_other,true}
    }};
    if(follow>=228){
        c.mmu.write32(post_mix_other,follow==232?byte_next_word:guard_word);
        c.mmu.write32(post_mix_end,follow==233?guard_word:post_mix_end_word);
        if(follow==229)post_mix[0].pc+=4u;
        if(follow==230)post_mix[1].other_pc=mix_other;
        if(follow==231)post_mix[1].taken=false;
    }
    const auto post_mix_path=follow>=228?std::span<const ScCallerMixedStep>{post_mix}:std::span<const ScCallerMixedStep>{};
    if(follow==215)c.mmu.write32(mix_other,byte_next_word);
    if(follow==216)c.mmu.write32(parent_sp+16,8u);
    const bool byte_armed=child.resume_caller_mixed_byte(c,follow==208?18:follow==209?24:19,
        follow==210?8u:9u,byte_next+(follow==217?4u:0u),byte_next_word,held()&&follow!=218,
        post_mix_path,follow>=228?post_mix_end:0u,follow>=228?post_mix_end_word:0u);
    if((follow>=208&&follow<=218)||(follow>=229&&follow<=233)){assert(!byte_armed);return;}
    assert(byte_armed&&child.stage()==20u&&child.caller_mixed_byte_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==4u);
    // Separate synthetic architectural effect, not a witness assignment.
    c.gpr[6]=follow==219?8u:9u;
    if(follow==221)c.mmu.write32(parent_sp+16,8u);
    if(follow==222)c.mmu.write32(byte_next,guard_word);
    if(follow==223)c.mmu.write32(byte_next+4u,byte_next_word);
    if(follow==224)c.mmu.write32(mix_other,byte_next_word);
    c.inst_count+=follow==220?2u:1u;
    const bool byte_done=child.stop_after_caller_mixed_byte(c,follow==225?mix_other:byte_next,byte_next_word,held()&&follow!=226);
    if(follow>=219&&follow<=226){assert(!byte_done);return;}
    assert(byte_done&&child.reached_caller_mixed_byte(c,held())&&child.caller_mixed_byte_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==4u);
    if(follow==227){assert(!child.stop_after_caller_mixed_byte(c,byte_next,byte_next_word,held()));return;}
    if(follow<228)return;
    const bool post_mix_armed=child.resume_caller_post_mixed(c,held()&&follow!=235);
    if(follow==234||follow==235){assert(!post_mix_armed);return;}
    assert(post_mix_armed&&child.stage()==22u&&child.caller_post_mixed_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==5u);
    c.cr[0]={false,false,follow!=236,false};
    if(follow==237)c.mmu.write32(post_mix_other,byte_next_word);
    if(follow==238)c.mmu.write32(mix_other,byte_next_word);
    if(follow==239)c.mmu.write32(byte_next,guard_word);
    c.inst_count+=follow==240?2u:1u;
    const bool post_mix_first=child.caller_post_mixed_boundary(c,follow==241?post_mix_end:post_mix_branch,post_mix_word,held());
    if(follow>=236&&follow<=241){assert(!post_mix_first);return;}
    assert(post_mix_first&&child.caller_post_mixed_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==6u);
    if(follow==242)c.gpr[6]^=1u;
    if(follow==243)c.mmu.write32(post_mix_end,guard_word);
    if(follow==244)c.mmu.write32(other,byte_next_word);
    c.inst_count+=follow==245?2u:1u;
    const bool post_mix_done=child.caller_post_mixed_boundary(c,follow==246?post_mix_other:post_mix_end,post_mix_end_word,held()&&follow!=247);
    if(follow>=242&&follow<=247){assert(!post_mix_done);return;}
    assert(post_mix_done&&child.reached_caller_post_mixed(c,held())&&child.caller_mixed_byte_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==6u);
    assert(child.caller_post_mixed_visits()==2u&&child.caller_post_mixed_integers()==1u&&child.caller_post_mixed_taken()==1u&&child.caller_post_mixed_fallthrough()==0u);
    if(parent_delay)assert(parent.frame_age(c)==136u&&child.caller_parent_tick_limit()==136u);
    if(follow==248){assert(!child.caller_post_mixed_boundary(c,post_mix_end,post_mix_end_word,held()));return;}
    if(follow<250)return;
    const auto move_next=post_mix_end+4u;
    const uint32_t move_word=follow>=272?ins(14,8,6,3):0x60000000u;
    const auto final_pc=move_next+4u;
    constexpr uint32_t next_entry=B+0x40u;
    const auto final_word=bl(final_pc,follow>=292?next_entry:T);
    const std::array<CallerIntegerInput,1> final_input{{{6,follow==280?8u:9u}}};
    const auto final_step=follow>=272?std::optional<ScCallerIntegerStep>{{move_next,move_word,final_input}}:std::nullopt;
    c.mmu.write32(move_next,follow==252?guard_word:move_word);
    c.mmu.write32(move_next+4u,follow>=272?(follow==273?guard_word:final_word):follow==253?move_word:guard_word);
    if(follow>=272)c.mmu.write32(final_pc+4u,follow==274?move_word:guard_word);
    if(follow==255)c.mmu.write32(post_mix_other,move_word);
    const bool move_armed=child.resume_caller_stack_move(c,(follow==251||follow==270)?move_offset+8:move_offset,
        move_next+(follow==256?4u:0u),move_word,held()&&follow!=257,final_step,
        follow>=272?final_pc+(follow==275?4u:0u):0u,follow>=272?(follow==276?final_word^1u:final_word):0u);
    if((follow>=251&&follow<=257)||follow==270||(follow>=273&&follow<=276)){assert(!move_armed);return;}
    assert(move_armed&&child.stage()==24u&&child.caller_stack_move_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==7u);
    c.gpr[7]=move_value^((follow==258||follow==271)?1u:0u);
    if(follow==260)c.mmu.write32(move_next,guard_word);
    if(follow==261)c.mmu.write32(move_next+4u,move_word);
    if(follow==262)c.mmu.write32(post_mix_other,move_word);
    if(follow==263)c.mmu.write32(other,move_word);
    if(follow==264)c.gpr[16]^=1u;
    c.inst_count+=follow==259?2u:1u;
    const bool move_done=child.stop_after_caller_stack_move(c,follow==265?post_mix_other:move_next,move_word,held()&&follow!=266);
    if((follow>=258&&follow<=266)||follow==271){assert(!move_done);return;}
    assert(move_done&&child.reached_caller_stack_move(c,held())&&child.caller_stack_move_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==7u);
    if(parent_delay)assert(parent.frame_age(c)==137u&&child.caller_parent_tick_limit()==137u);
    if(follow==267){assert(!child.stop_after_caller_stack_move(c,move_next,move_word,held()));return;}
    if(follow<272)return;
    const bool final_armed=child.resume_caller_final_integer(c,held()&&follow!=281);
    if(follow==280||follow==281){assert(!final_armed);return;}
    assert(final_armed&&child.stage()==26u&&child.caller_final_integer_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==8u);
    c.gpr[8]=follow==282?13u:12u;
    if(follow==284)c.mmu.write32(final_pc,guard_word);
    if(follow==285)c.mmu.write32(final_pc+4u,move_word);
    if(follow==286)c.mmu.write32(move_next,guard_word);
    if(follow==287)c.mmu.write32(other,move_word);
    if(follow==288)c.lr^=4u;
    c.inst_count+=follow==283?2u:1u;
    const bool final_done=child.stop_after_caller_final_integer(c,follow==289?final_pc+4u:final_pc,final_word,held()&&follow!=290);
    if(follow>=282&&follow<=290){assert(!final_done);return;}
    assert(final_done&&child.reached_caller_final_integer(c,held())&&child.caller_final_integer_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==8u);
    if(parent_delay)assert(parent.frame_age(c)==138u&&child.caller_parent_tick_limit()==138u);
    if(follow==291){assert(!child.stop_after_caller_final_integer(c,final_pc,final_word,held()));return;}
    if(follow<292)return;
    const uint32_t entry_word=ins(follow>=318?34:32,9,7,0),next_ret=final_pc+4u;
    const uint32_t entry_successor=follow>=338?
        ((11u<<26)|(1u<<23)|(8u<<16)|16u):ins(14,10,9,1);
    const unsigned copy_source=follow==368?1u:7u;
    const unsigned copy_destination=follow==367?14u:10u;
    const uint32_t copy_word=(31u<<26u)|(copy_source<<21u)|(copy_destination<<16u)|(copy_source<<11u)|(444u<<1u);
    const uint32_t after_compare=follow>=348?copy_word:0x60000000u;
    const uint32_t after_copy=ins(14,3,follow>=369?0u:3u,1);
    // The later opt-in scenario exercises the authentic opcode families:
    // original 122 extsb of the 121 result, then original 123 zero-base addi.
    const uint32_t after_immediate=follow>=393?
        ((31u<<26u)|(3u<<21u)|(3u<<16u)|(954u<<1u)):
        ins(14,4,0,0xfffe);
    const uint32_t after_signext=ins(14,4,0,0xfffe);
    const uint32_t after_second=follow>=417?ins(14,5,0,0x1234):0x60000000u;
    const uint32_t after_third=follow>=436?ins(14,6,0,0xfffe):0x60000000u;
    const uint32_t after_fourth=follow>=450?ins(14,7,0,0x7fff):0x60000000u;
    const uint32_t after_fifth=follow>=470?ins(14,8,0,0x8000):0x60000000u;
    const uint32_t after_sixth=follow>=490?
        ((16u<<26u)|(12u<<21u)|(4u<<16u)|24u):0x60000000u;
    if(follow>=318){
        c.mmu.write32(move_value,0x5a000000u);
        c.mmu.write32(next_entry+8u,follow>=338?after_compare:guard_word);
        if(follow>=338)c.mmu.write32(next_entry+12u,follow>=348?after_copy:guard_word);
        if(follow>=348)c.mmu.write32(next_entry+16u,guard_word);
        if(follow>=369){
            c.mmu.write32(next_entry+16u,after_immediate);
            c.mmu.write32(next_entry+20u,follow==370?entry_word:guard_word);
            if(follow==371)c.mmu.write32(next_entry+16u,entry_word);
            if(follow>=393){
                c.mmu.write32(next_entry+20u,after_signext);
                c.mmu.write32(next_entry+24u,after_second);
                c.mmu.write32(next_entry+28u,guard_word);
                if(follow>=417){
                    c.mmu.write32(next_entry+28u,after_third);
                    c.mmu.write32(next_entry+32u,follow>=436?after_fourth:guard_word);
                    if(follow>=436){
                        c.mmu.write32(next_entry+36u,follow>=450?after_fifth:guard_word);
                        if(follow>=450)c.mmu.write32(next_entry+40u,
                            follow>=470?after_sixth:guard_word);
                        if(follow>=470)c.mmu.write32(next_entry+44u,guard_word);
                    }
                }
            }
        }
    }
    c.mmu.write32(next_entry,follow==294?guard_word:entry_word);
    c.mmu.write32(next_entry+4u,follow==295?entry_word:follow>=318?entry_successor:guard_word);
    if(follow==296)c.mmu.write32(next_ret,entry_word);
    const bool entry_armed=child.resume_caller_next_entry(c,follow==293?next_entry+4u:next_entry,
        follow==297?0x60000000u:entry_word,next_ret+(follow==298?4u:0u),held()&&follow!=299,
        follow>=318?std::optional<uint32_t>{entry_successor}:std::nullopt,
        follow>=338?std::optional<uint32_t>{after_compare}:std::nullopt,
        follow>=348?std::optional<uint32_t>{after_copy}:std::nullopt,
        follow>=369&&follow!=372?
            std::optional<uint32_t>{follow==374?guard_word:after_immediate}:std::nullopt,
        follow>=393?std::optional<uint32_t>{after_signext}:std::nullopt,
        follow>=393?std::optional<uint32_t>{after_second}:std::nullopt,
        follow>=417?std::optional<uint32_t>{after_third}:std::nullopt,
        follow>=436?std::optional<uint32_t>{after_fourth}:std::nullopt,
        follow>=450?std::optional<uint32_t>{after_fifth}:std::nullopt,
        follow>=470?std::optional<uint32_t>{after_sixth}:std::nullopt);
    if((follow>=293&&follow<=299)||(follow>=370&&follow<=372)||follow==374){
        assert(!entry_armed);return;
    }
    assert(entry_armed&&child.stage()==28u&&child.caller_next_entry_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==9u);
    // Execute only the synthetic BL effect. The callee's load never runs.
    c.pc=follow==300?next_entry+4u:next_entry;
    c.lr=follow==301?next_ret+4u:next_ret;
    if(follow==317)++c.inst_count;
    if(follow!=314){
        const bool traced=child.caller_next_entry_trace(c,follow==316?next_entry+4u:next_entry,held());
        if(follow==300||follow==301||follow==316||follow==317){assert(!traced);return;}
        assert(traced);
        if(follow==315){assert(!child.caller_next_entry_trace(c,next_entry,held()));return;}
    }
    if(follow==302)c.gpr[7]^=1u;
    if(follow==304)c.mmu.write32(next_entry,guard_word);
    if(follow==305)c.mmu.write32(next_entry+4u,entry_word);
    if(follow==306)c.mmu.write32(next_ret,entry_word);
    if(follow==307)c.mmu.write32(other,entry_word);
    if(follow==308)c.mmu.write32(parent_sp+16,8u);
    if(follow==309)c.cr[0].eq=false;
    if(follow==310)c.ctr^=1u;
    c.inst_count+=follow==303?2u:1u;
    const bool entry_done=child.stop_at_caller_next_entry(c,follow==311?next_entry+4u:next_entry,entry_word,held()&&follow!=312);
    if((follow>=300&&follow<=312)||follow==314){assert(!entry_done);return;}
    assert(entry_done&&child.reached_caller_next_entry(c,held())&&child.caller_next_entry_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==9u);
    if(parent_delay)assert(parent.frame_age(c)==139u&&child.caller_parent_tick_limit()==139u);
    if(follow==313){assert(!child.stop_at_caller_next_entry(c,next_entry,entry_word,held()));return;}
    if(follow<318)return;
    if(follow==323)c.mmu.write32(move_value,0x5b000000u);
    if(follow==324)c.mmu.write32(next_entry+8u,entry_word);
    const bool report_armed=child.resume_caller_report_byte(c,follow==321?753:752,follow==322?17:16,
        follow==320?0x5b:0x5a,follow!=319,held()&&follow!=325);
    if(follow>=319&&follow<=325){assert(!report_armed);return;}
    assert(report_armed&&child.stage()==30u&&child.caller_report_byte_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==10u);
    // Standalone transition checks are covered separately with a report witness.
    // The guest load is modeled independently here; the witness predicts only.
    c.gpr[9]=follow==326?0x5bu:0x5au;
    if(follow==328)c.mmu.write32(move_value,0x5b000000u);
    if(follow==329)c.mmu.write32(next_ret,entry_word);
    if(follow==330)c.lr^=4u;
    if(follow==331)c.mmu.write32(parent_sp+16,8u);
    if(follow==332)c.mmu.write32(next_entry+8u,entry_word);
    if(follow==333)c.gpr[14]^=1u;
    c.inst_count+=follow==327?2u:1u;
    const bool done=child.stop_after_caller_report_byte(c,follow==334?next_entry+8u:next_entry+4u,
        entry_successor,follow!=336,held()&&follow!=335);
    if(follow>=326&&follow<=336){assert(!done);return;}
    assert(done&&child.reached_caller_report_byte(c,held())&&child.caller_report_byte_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==10u);
    if(parent_delay)assert(parent.frame_age(c)==140u&&child.caller_parent_tick_limit()==140u);
    if(follow==337)assert(!child.stop_after_caller_report_byte(c,next_entry+4u,entry_successor,true,held()));
    if(follow<338)return;
    CallerImmediateCompareWitness compare;
    const bool compare_armed=compare.arm(c,next_entry,next_entry+4u,
        entry_successor,after_compare,{follow==339?7u:8u,12u},
        follow>=348?std::optional<uint32_t>{after_copy}:std::nullopt,
        follow>=369?std::optional<uint32_t>{after_immediate}:std::nullopt,
        follow>=393?std::optional<uint32_t>{after_signext}:std::nullopt,
        follow>=393?std::optional<uint32_t>{after_second}:std::nullopt,
        follow>=417?std::optional<uint32_t>{after_third}:std::nullopt,
        follow>=436?std::optional<uint32_t>{after_fourth}:std::nullopt,
        follow>=450?std::optional<uint32_t>{after_fifth}:std::nullopt,
        follow>=470?std::optional<uint32_t>{after_sixth}:std::nullopt);
    if(follow==339){assert(!compare_armed);return;}
    assert(compare_armed&&compare.stage()==1u);
    const bool joined=child.resume_caller_report_compare(c,8u,12u,
        follow!=340,held());
    if(follow==340){assert(!joined);return;}
    assert(joined&&child.stage()==32u);
    assert(child.caller_post_fourth_tick_budget()==11u);
    // Original cmpwi cr1,r8,16: r8 is 12, independent of the r9 byte load.
    c.cr[1]={follow!=341,false,false,bool(c.xer>>31u)};
    if(follow==345)c.cr[0].eq=!c.cr[0].eq;
    if(follow==343)c.gpr[5]^=1u;
    if(follow==344)c.mmu.write32(next_entry+12u,entry_word);
    c.inst_count+=follow==342?2u:1u;
    const bool observed=compare.observe(c,next_entry+8u,after_compare);
    if(follow>=341&&follow<=345){assert(!observed);return;}
    assert(observed&&compare.stage()==2u);
    const bool done_compare=child.stop_after_caller_report_compare(c,
        next_entry+8u,follow==346?entry_word:after_compare,true,held()&&follow!=347);
    if(follow==346||follow==347){assert(!done_compare);return;}
    assert(done_compare&&child.stage()==33u&&
        child.reached_caller_report_compare(c,held())&&
        child.caller_report_compare_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==11u);
    if(follow<348)return;
    const auto prior_regs=c.gpr;
    if(follow==352)c.mmu.write32(next_entry+16u,entry_word);
    const bool copy_armed=child.resume_caller_report_copy(c,
        follow==349?8u:copy_source,follow==350?11u:copy_destination,
        follow==351?move_offset+1:follow==368?0:move_offset,held()&&follow!=353);
    // A saved nonvolatile destination must not widen the private copy proof.
    if((follow>=349&&follow<=353)||follow==367){assert(!copy_armed);return;}
    assert(copy_armed&&child.stage()==34u&&child.caller_report_copy_visits()==0u);
    assert(c.gpr==prior_regs);
    assert(child.caller_post_fourth_tick_budget()==12u);
    c.gpr[10]=follow==354?move_value^1u:follow==368?parent_sp:move_value;
    if(follow==356)c.gpr[7]^=1u;
    if(follow==357)c.gpr[14]^=1u;
    if(follow==358)c.cr[1].lt=false;
    if(follow==359)c.mmu.write32(next_entry+12u,entry_word);
    if(follow==360)c.mmu.write32(next_entry+16u,entry_word);
    if(follow==361)c.mmu.write32(next_ret,entry_word);
    if(follow==362)c.mmu.write32(move_value,0x5b000000u);
    if(follow==373)c.mmu.write32(next_entry+20u,entry_word);
    if(follow==375)c.mmu.write32(next_entry+16u,entry_word);
    c.inst_count+=follow==355?2u:1u;
    const bool copy_done=child.stop_after_caller_report_copy(c,
        follow==363?next_entry+8u:next_entry+12u,
        follow==364?entry_word:after_copy,held()&&follow!=365);
    if((follow>=354&&follow<=365)||follow==373||follow==375){
        assert(!copy_done);return;
    }
    assert(copy_done&&child.stage()==35u&&child.reached_caller_report_copy(c,held()));
    assert(child.caller_report_copy_visits()==1u&&child.caller_post_fourth_tick_budget()==12u);
    if(parent_delay)assert(parent.frame_age(c)==142u&&child.caller_parent_tick_limit()==142u);
    if(follow==366)assert(!child.stop_after_caller_report_copy(c,next_entry+12u,after_copy,held()));
    if(follow<376)return;
    // The full predecessor still refuses untracked volatile mutations.
    // Only the isolated zero-input predictor may ignore a stale destination.
    const auto prior_immediate=c.gpr;
    if(follow==380)c.mmu.write32(next_entry+12u,entry_word);
    if(follow==381)c.mmu.write32(next_entry+20u,entry_word);
    if(follow==382)c.mmu.write32(next_entry+16u,entry_word);
    if(follow==383)++c.inst_count;
    if(follow==384)c.gpr[3]^=0xa5a5a5a5u;
    const bool immediate_armed=child.resume_caller_report_immediate(
        c,follow==377?11u:3u,follow==378?2u:1u,held()&&follow!=379);
    if(follow>=377&&follow<=384){assert(!immediate_armed);return;}
    assert(immediate_armed&&child.stage()==36u&&child.caller_report_immediate_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==13u&&c.gpr==prior_immediate);
    c.gpr[3]=follow==385?0u:1u;
    if(follow==389)c.gpr[8]^=1u;
    if(follow==390)c.mmu.write32(next_entry+20u,entry_word);
    if(follow==391)c.cr[1].lt=!c.cr[1].lt;
    c.inst_count+=follow==386?2u:1u;
    const bool immediate_done=child.stop_after_caller_report_immediate(c,
        follow==387?next_entry+12u:next_entry+16u,
        follow==388?entry_word:after_immediate,held());
    if(follow>=385&&follow<=391){assert(!immediate_done);return;}
    assert(immediate_done&&child.stage()==37u&&
           child.reached_caller_report_immediate(c,held())&&
           child.caller_report_immediate_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==13u);
    if(follow==392){
        assert(!child.stop_after_caller_report_immediate(c,next_entry+16u,after_immediate,held()));
        return;
    }
    if(follow<393)return;

    // Original-free native-witness joining of fifth/sixth PPC instructions.
    // The fixture uses a concrete synthetic li r3,1 followed by extsb r3,r3.
    // The signext must preserve 1; the next zero-input li writes 0xfffffffe.
    if(follow==398)c.mmu.write32(next_entry+20u,entry_word);
    if(follow==399)c.gpr[3]^=1u;
    const bool signext_armed=child.resume_caller_report_signext(c,
        follow==395?4u:3u,follow==394?2u:1u,
        follow==396?2u:1u,held()&&follow!=397);
    if(follow>=394&&follow<=399){
        assert(!signext_armed);return;
    }
    assert(signext_armed&&child.stage()==38u&&
           child.caller_report_signext_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==14u);
    c.gpr[3]=follow==400?0u:1u;
    if(follow==404)c.gpr[5]^=1u;
    if(follow==405)c.cr[1].lt=!c.cr[1].lt;
    c.inst_count+=follow==403?2u:1u;
    const bool signext_done=child.stop_after_caller_report_signext(c,
        follow==401?next_entry+16u:next_entry+20u,
        follow==402?entry_word:after_signext,held());
    if(follow>=400&&follow<=405){
        assert(!signext_done);return;
    }
    assert(signext_done&&child.stage()==39u&&
           child.reached_caller_report_signext(c,held())&&
           child.caller_report_signext_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==14u);
    if(follow==409)c.mmu.write32(next_entry+24u,entry_word);
    const bool second_immediate_armed=child.resume_caller_report_second_immediate(
        c,follow==406?5u:4u,follow==407?0u:0xfffffffeu,
        held()&&follow!=408);
    if(follow>=406&&follow<=409){
        assert(!second_immediate_armed);return;
    }
    assert(second_immediate_armed&&child.stage()==40u&&
           child.caller_report_second_immediate_visits()==0u);
    assert(child.caller_post_fourth_tick_budget()==15u);
    c.gpr[4]=follow==410?0u:0xfffffffeu;
    if(follow==413)c.mmu.write32(next_entry+28u,entry_word);
    if(follow==415)c.gpr[5]^=1u;
    if(follow==416)c.cr[1].lt=!c.cr[1].lt;
    c.inst_count+=follow==414?2u:1u;
    const bool second_done=child.stop_after_caller_report_second_immediate(c,
        follow==411?next_entry+20u:next_entry+24u,
        follow==412?entry_word:after_second,held());
    if(follow>=410&&follow<=416){
        assert(!second_done);return;
    }
    assert(second_done&&child.stage()==41u&&
           child.reached_caller_report_second_immediate(c,held())&&
           child.caller_report_second_immediate_visits()==1u);

    assert(child.caller_post_fourth_tick_budget()==15u);
    if(follow<417)return;
    // The following two original-free effects are modelled by a real
    // register update; the joined parent observes their native boundaries.
    if(follow==421)c.mmu.write32(next_entry+28u,guard_word);
    const bool report_third_armed=child.resume_caller_report_third_immediate(c,
        follow==418?4u:5u,follow==419?0u:0x1234u,held()&&follow!=420);
    if(follow>=418&&follow<=421){assert(!report_third_armed);return;}
    assert(report_third_armed&&child.stage()==42u);
    assert(child.caller_post_fourth_tick_budget()==16u);
    c.gpr[5]=follow==422?0u:0x1234u;
    if(follow==423)c.gpr[9]^=1u;
    if(follow==424)c.cr[1].lt=!c.cr[1].lt;
    if(follow==425)c.mmu.write32(next_entry+28u,entry_word);
    c.inst_count+=follow==426?2u:1u;
    const bool third_done=child.stop_after_caller_report_third_immediate(
        c,follow==427?next_entry+24u:next_entry+28u,
        follow==428?entry_word:after_third,held()&&follow!=429);
    if(follow>=422&&follow<=429){assert(!third_done);return;}
    assert(third_done&&child.stage()==43u&&
           child.reached_caller_report_third_immediate(c,held())&&
           child.caller_report_third_immediate_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==16u);
    if(follow==430){
        assert(!child.stop_after_caller_report_third_immediate(
            c,next_entry+28u,after_third,held()));return;
    }
    if(follow<436)return;
    if(follow==440)c.mmu.write32(next_entry+32u,guard_word);
    const bool report_fourth_armed=child.resume_caller_report_fourth_immediate(
        c,follow==437?4u:6u,follow==438?0u:0xfffffffeu,
        held()&&follow!=439);
    if(follow>=437&&follow<=440){assert(!report_fourth_armed);return;}
    assert(report_fourth_armed&&child.stage()==44u);
    assert(child.caller_post_fourth_tick_budget()==17u);
    c.gpr[6]=follow==441?0u:0xfffffffeu;
    if(follow==442)c.gpr[9]^=1u;
    if(follow==443)c.cr[1].lt=!c.cr[1].lt;
    if(follow==444)c.mmu.write32(next_entry+36u,entry_word);
    c.inst_count+=follow==445?2u:1u;
    const bool fourth_done=child.stop_after_caller_report_fourth_immediate(
        c,follow==446?next_entry+28u:next_entry+32u,
        follow==447?entry_word:after_fourth,held()&&follow!=448);
    if(follow>=441&&follow<=448){assert(!fourth_done);return;}
    assert(fourth_done&&child.stage()==45u&&
           child.reached_caller_report_fourth_immediate(c,held())&&
           child.caller_report_fourth_immediate_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==17u);
    if(follow==449){
        assert(!child.stop_after_caller_report_fourth_immediate(
            c,next_entry+32u,after_fourth,held()));return;
    }
    if(follow<450)return;
    // Step 126 uses the ninth authenticated label and the earlier
    // fourth-stage register lease; the model never executes guest code.
    if(follow==454)c.mmu.write32(next_entry+36u,guard_word);
    const bool fifth_armed=child.resume_caller_report_fifth_immediate(
        c,follow==451?6u:7u,follow==452?0u:0x7fffu,
        held()&&follow!=453);
    if(follow>=451&&follow<=454){assert(!fifth_armed);return;}
    assert(fifth_armed&&child.stage()==46u);
    assert(child.caller_post_fourth_tick_budget()==18u);
    c.gpr[7]=follow==455?0u:0x7fffu;
    if(follow==456)c.gpr[9]^=1u;
    if(follow==457)c.cr[1].lt=!c.cr[1].lt;
    if(follow==458)c.mmu.write32(next_entry+40u,entry_word);
    c.inst_count+=follow==459?2u:1u;
    const bool fifth_done=child.stop_after_caller_report_fifth_immediate(
        c,follow==460?next_entry+32u:next_entry+36u,
        follow==461?entry_word:after_fifth,held()&&follow!=462);
    if(follow>=455&&follow<=462){assert(!fifth_done);return;}
    assert(fifth_done&&child.stage()==47u&&
           child.reached_caller_report_fifth_immediate(c,held())&&
           child.caller_report_fifth_immediate_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==18u);
    if(follow==463){
        assert(!child.stop_after_caller_report_fifth_immediate(
            c,next_entry+36u,after_fifth,held()));return;
    }
    if(follow<470)return;
    // Step 127 consumes the already classified tenth successor, then
    // refuses every incorrect register, counter, PC, word or guard.
    if(follow==474)c.mmu.write32(next_entry+40u,guard_word);
    const bool sixth_armed=child.resume_caller_report_sixth_immediate(
        c,follow==471?7u:8u,follow==472?0u:0xffff8000u,
        held()&&follow!=473);
    if(follow>=471&&follow<=474){assert(!sixth_armed);return;}
    assert(sixth_armed&&child.stage()==48u);
    assert(child.caller_post_fourth_tick_budget()==19u);
    c.gpr[8]=follow==475?0u:0xffff8000u;
    if(follow==476)c.gpr[9]^=1u;
    if(follow==477)c.cr[1].lt=!c.cr[1].lt;
    if(follow==478)c.mmu.write32(next_entry+44u,entry_word);
    c.inst_count+=follow==479?2u:1u;
    const bool sixth_done=child.stop_after_caller_report_sixth_immediate(
        c,follow==480?next_entry+36u:next_entry+40u,
        follow==481?entry_word:after_sixth,held()&&follow!=482);
    if(follow>=475&&follow<=482){assert(!sixth_done);return;}
    assert(sixth_done&&child.stage()==49u&&
           child.reached_caller_report_sixth_immediate(c,held())&&
           child.caller_report_sixth_immediate_visits()==1u);
    assert(child.caller_post_fourth_tick_budget()==19u);
    if(follow==483){
        assert(!child.stop_after_caller_report_sixth_immediate(
            c,next_entry+40u,after_sixth,held()));return;
    }
    if(follow<490)return;
    const uint32_t target128=next_entry+64u;
    const bool compare129=follow>=520u;
    const uint32_t target_word=compare129?
        (11u<<26u)|(3u<<23u)|(8u<<16u)|0x8000u:0x60000000u;
    const uint32_t successor129=0x60000000u;
    c.mmu.write32(target128,follow==495?guard_word:target_word);
    c.mmu.write32(target128+4u,compare129?successor129:
                  follow==496?target_word:guard_word);
    if(compare129)c.mmu.write32(target128+8u,guard_word);
    if(follow==497)c.mmu.write32(next_entry+44u,target_word);
    const bool branch128_armed=child.resume_caller_report_branch_128(
        c,follow==491?target128+4u:target128,
        follow==492?guard_word:target_word,
        follow==493?64u:80u,held()&&follow!=494,
        compare129?std::optional<uint32_t>{successor129}:std::nullopt);
    if(follow>=491&&follow<=497){assert(!branch128_armed);return;}
    assert(branch128_armed&&child.stage()==50u);
    assert(child.caller_post_fourth_tick_budget()==20u);
    assert(child.caller_report_branch_128_visits()==0u);
    // The selected target is a separate generated root: NWiiRecomp
    // switches dispatch PC and traces entry before the target label tick.
    c.pc=follow==507?next_entry:target128;
    if(follow==508)++c.inst_count;
    if(follow!=509){
        const bool traced=child.caller_report_branch_128_trace(
            c,follow==510?target128+4u:target128,held()&&follow!=511);
        if(follow==507||follow==508||follow==510||follow==511){
            assert(!traced);return;
        }
        assert(traced);
        if(follow==512){
            assert(!child.caller_report_branch_128_trace(c,target128,held()));return;
        }
    }
    if(follow==499)c.cr[1].lt=false;
    if(follow==500)c.gpr[5]^=1u;
    if(follow==501)c.mmu.write32(target128+4u,target_word);
    c.inst_count+=follow==502?2u:1u;
    const bool branch_done=child.stop_after_caller_report_branch_128(
        c,follow==503?target128+4u:target128,
        follow==504?guard_word:target_word,held()&&follow!=505);
    if((follow>=499&&follow<=505)||follow==509){assert(!branch_done);return;}
    assert(branch_done&&child.stage()==51u&&
           child.caller_report_branch_128_visits()==1u&&
           child.reached_caller_report_branch_128(c,held()));
    assert(child.caller_post_fourth_tick_budget()==20u);
    if(follow==506){
        assert(!child.stop_after_caller_report_branch_128(
            c,target128,target_word,held()));return;
    }
    if(!compare129)return;
    if(follow==525)c.mmu.write32(target128+8u,successor129);
    const bool compare_armed=child.resume_caller_report_compare_129(
        c,follow==521?7u:8u,follow==522?0u:0xffff8000u,
        follow!=523,held()&&follow!=524);
    if(follow>=521&&follow<=525){assert(!compare_armed);return;}
    assert(compare_armed&&child.stage()==52u&&
           child.caller_post_fourth_tick_budget()==21u&&
           child.caller_report_compare_129_visits()==0u);
    // Synthetic architectural effect: equal signed operands, plus XER.SO.
    c.cr[3]={false,false,true,bool(c.xer&0x80000000u)};
    if(follow==526)c.cr[3].eq=false;
    if(follow==527)c.cr[2].lt=!c.cr[2].lt;
    if(follow==528)c.gpr[8]^=1u;
    if(follow==529)c.pc=target128+4u;
    if(follow==535)c.mmu.write32(target128+8u,successor129);
    c.inst_count+=follow==530?2u:1u;
    const bool compare_done=child.stop_after_caller_report_compare_129(
        c,follow==531?target128:target128+4u,
        follow==532?guard_word:successor129,follow!=533,held()&&follow!=534);
    if(follow>=526&&follow<=535){assert(!compare_done);return;}
    assert(compare_done&&child.stage()==53u&&
           child.caller_report_compare_129_visits()==1u&&
           child.caller_report_branch_128_visits()==1u&&
           child.reached_caller_report_compare_129(c,held())&&
           child.caller_post_fourth_tick_budget()==21u);
    if(follow==536){
        assert(!child.stop_after_caller_report_compare_129(
            c,target128+4u,successor129,true,held()));return;
    }
}
int main(){for(unsigned i=0;i<8;++i)trial(i);
    for(unsigned i=0;i<=20;++i)caller_trial(i,0x1234beefu);
    caller_trial(0,0u);caller_trial(0,0xffffffffu);
    // Each opaque byte position exercises all 256 possible values.
    for(unsigned i=0;i<256;++i)caller_trial(11,0x5a5a0000u|(i<<8)|(255u-i));
    for(unsigned follow=1;follow<=248;++follow)caller_trial(0,0x1234beefu,follow);
    uint64_t baseline=0,stressed=0;
    caller_trial(0,0x1234beefu,228,0,&baseline);
    assert(baseline>0u&&baseline<128u);
    caller_trial(0,0x1234beefu,228,128u-baseline,&stressed);
    assert(stressed==128u);
    caller_trial(0,0x1234beefu,249,128u-baseline);
    for(unsigned follow=250;follow<=267;++follow)caller_trial(0,0x1234beefu,follow);
    caller_trial(0,0x1234beefu,250,128u-baseline);
    for(unsigned follow=268;follow<=271;++follow)caller_trial(0,0x1234beefu,follow);
    caller_trial(0,0x1234beefu,268,128u-baseline);
    for(unsigned follow=272;follow<=291;++follow)caller_trial(0,0x1234beefu,follow);
    caller_trial(0,0x1234beefu,272,128u-baseline);
    for(unsigned follow=292;follow<=317;++follow)caller_trial(0,0x1234beefu,follow);
    caller_trial(0,0x1234beefu,292,128u-baseline);
    for(unsigned follow=318;follow<=337;++follow)caller_trial(0,0x1234beefu,follow);
    caller_trial(0,0x1234beefu,318,128u-baseline);
    for(unsigned follow=338;follow<=347;++follow)caller_trial(0,0x1234beefu,follow);
    for(unsigned follow=348;follow<=483;++follow)caller_trial(0,0x1234beefu,follow);
    for(unsigned follow=490;follow<=512;++follow)caller_trial(0,0x1234beefu,follow);
    for(unsigned follow=520;follow<=536;++follow)caller_trial(0,0x1234beefu,follow);
    caller_trial(0,0x1234beefu,348,128u-baseline);
    // The full 124/125 stage transitions must also survive the original
    // parent's independently measured 128-tick lease threshold.
    caller_trial(0,0x1234beefu,417,128u-baseline);
    caller_trial(0,0x1234beefu,436,128u-baseline);
    caller_trial(0,0x1234beefu,450,128u-baseline);
    caller_trial(0,0x1234beefu,470,128u-baseline);
    caller_trial(0,0x1234beefu,490,128u-baseline);
    caller_trial(0,0x1234beefu,520,128u-baseline);
    std::cout<<"FORMATTER_NESTED_JOIN_TEST cases=801 compare_cases=10 copy_cases=46 immediate_cases=17 signext_second_cases=24 third_fourth_cases=33 fifth_sixth_cases=34 branch_128_cases=23 original_execution=0\n";
    std::cout<<"FORMATTER_COMPARE_129_PARENT_SOURCE_ONLY cases=18 lease_budget=21 original_execution=0\n";}
