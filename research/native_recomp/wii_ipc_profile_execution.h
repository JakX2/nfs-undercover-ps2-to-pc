#pragma once
#include "wii_ipc_profile_enqueue_v1415.h"
#include <algorithm>
#include <span>
namespace undercover::wii {
struct IpcProfileNativeWord {uint32_t pc,word;};
struct IpcProfileExecutionExpectation {
    uint32_t helper,call,branch_word,return_word;
    std::span<const IpcProfileNativeWord> words;
    IpcProfileLayout layout;
};
// Read-only native instruction observer. The caller must establish the
// preceding ring-enqueue boundary and authenticated private geometry.
// Nothing here executes instructions, seeds data or performs IOS work.
class IpcProfileExecutionWitness {
public:
    explicit IpcProfileExecutionWitness(IpcProfileExecutionExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned memory_failure()const{return profile_.failure();}
    unsigned visits()const{return visits_;}
    unsigned stores()const{return profile_.stores();}
    unsigned polls()const{return polls_;}
    unsigned ordinal()const{return ordinal_;}
    bool slot_available()const{return profile_.slot_available();}
    template<class C>bool begin(C& c,bool held,AllocatorRange request,AllocatorRange stack,AllocatorRange ring,uint32_t fd){
        if(stage_||error_||!held||!safe(c)||!e_.helper||e_.call>0xfffffffbu||
           c.pc!=e_.helper||c.lr!=e_.call+4u||c.gpr[3]!=request.base||c.gpr[4]!=fd||
           fd>1u||request.size<64u||request.size>4096u||(request.base&31u)||
           stack.base!=c.gpr[1]||(stack.base&7u)||stack.size<8u||stack.size>520u||
           ring.size<24u||ring.size>272u||(ring.size-16u)%4u||(ring.base&3u)||
           e_.words.empty()||e_.words.size()>256u||
           e_.branch_word>>26!=18u||(e_.branch_word&3u)!=1u||
           target(e_.call,e_.branch_word)!=e_.helper||
           !word(c,e_.call,e_.branch_word)||!word(c,e_.call+4u,e_.return_word)||
           !known(c,e_.helper))return fail(1);
        protected_={request,stack,ring};
        for(unsigned i=0;i<protected_.size();++i){
            auto a=protected_[i];
            if(!mapped(c,a))return fail(1);
            for(unsigned j=0;j<i;++j)if(overlap(a,protected_[j]))return fail(1);
            for(unsigned off=0;off<a.size;++off)shadow_[i].push_back(c.mmu.read8(a.base+off));
        }
        if(c.mmu.read32(request.base+8u)!=fd||
           !profile_.begin(c,e_.layout,request,stack,ring,fd,true))return fail(1);
        gp_=c.gpr;msr_=c.msr;cr_=pack(c)&0x00fff000u;cpu_=&c;
        next_=e_.helper;start_=last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!live(c,held)||return_due_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,pc)||!word(c,pc,w)||++visits_>1024u)return fail(2);
        ordinal_=(pc-e_.helper)/4u+1u;
        if(!protected_unchanged(c)||!profile_.settled(c))return fail(3);
        if(ctr_due_&&c.ctr!=ctr_expected_)return fail(4);
        ctr_due_=false;
        last_=c.inst_count;next_=pc+4u;poll_pc_=0;polled_=false;
        const unsigned op=w>>26,xo=(w>>1)&1023u,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
        if(op==36u||(op==31u&&xo==151u)){
            const int64_t ea=int64_t(ra?c.gpr[ra]:0u)+(op==31u?int64_t(c.gpr[rb]):
                int64_t(int32_t((w&0xffffu)^0x8000u)-0x8000));
            if(ea<0||ea>0xffffffffll||!profile_.authorize(c,uint32_t(ea),c.gpr[rs],4u,true))return fail(3);
        }else if(op==37u||op==38u||op==39u||op==44u||op==45u||op==47u||
                 op==52u||op==53u||op==54u||op==55u||op==60u||op==61u||
                 (op==31u&&(xo==183u||xo==215u||xo==247u||xo==407u||xo==439u||
                 xo==661u||xo==662u||xo==725u||xo==918u||xo==663u||xo==695u||xo==727u||xo==759u||xo==983u)))
            return fail(3);
        if(op==17u||(op==19u&&(xo==50u||xo==528u))||
           (op==31u&&(xo==146u||xo==150u||xo==1014u)))return fail(4);
        if(op==31u&&xo==467u){
            const unsigned spr=ra|(rb<<5);
            if(spr!=9u)return fail(4);
            ctr_due_=true;ctr_expected_=c.gpr[rs];
        }
        if(op==19u&&xo==16u){
            if(w&1u)return fail(4);
            const bool transfer=taken(c,w);
            if(!branch_ctr(c,w))return fail(4);
            if(transfer){
                if(!abi(c)||!profile_.complete(c))return fail(5);
                next_=e_.call+4u;return_due_=true;return true;
            }
        }
        if(op==16u||op==18u){
            if(w&3u)return fail(4);
            const uint32_t dst=target(pc,w);
            if(!known(c,dst))return fail(4);
            if(dst<=pc)poll_pc_=pc;
            if(op==18u||taken(c,w))next_=dst;
            if(op==16u&&!branch_ctr(c,w))return fail(4);
        }
        if(!known(c,next_))return fail(4);
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||!live(c,held)||!poll_pc_||polled_||c.pc!=poll_pc_||
           c.inst_count!=last_||!protected_unchanged(c)||!profile_.settled(c)||++polls_>256u)return fail(6);
        polled_=true;return true;
    }
    template<class C>bool returned(C& c,uint32_t pc,bool held){
        if(stage_!=1u||!live(c,held)||!return_due_||pc!=e_.call+4u||pc!=next_||
           c.pc!=pc||c.inst_count!=last_||!word(c,pc,e_.return_word)||
           (ctr_due_&&c.ctr!=ctr_expected_)||!abi(c)||!protected_unchanged(c)||
           !profile_.complete(c))return fail(7);
        stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held){
        return stage_==2u&&live(c,held)&&return_due_&&c.pc==e_.call+4u&&
               c.inst_count==last_&&word(c,c.pc,e_.return_word)&&abi(c)&&
               protected_unchanged(c)&&profile_.complete(c);
    }
private:
    IpcProfileExecutionExpectation e_;IpcProfileEnqueueWitness profile_;
    std::array<AllocatorRange,3> protected_{};
    std::array<std::vector<uint8_t>,3> shadow_{};
    std::array<uint32_t,32> gp_{};
    const void* cpu_=nullptr;
    uint32_t msr_=0,cr_=0,next_=0,poll_pc_=0,ctr_expected_=0;
    uint64_t start_=0,last_=0;
    unsigned stage_=0,error_=0,visits_=0,polls_=0,ordinal_=0;
    bool return_due_=false,polled_=false,ctr_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool overlap(AllocatorRange a,AllocatorRange b){return a.size&&b.size&&a.base<b.end()&&b.base<a.end();}
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||!((a.base>=0x80000000u&&a.end()<=0x81800000ull)||
                      (a.base>=0x90000000u&&a.end()<=0x94000000ull)))return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){
        return !(a&3u)&&mapped(c,{a,4})&&c.mmu.read32(a)==w;
    }
    template<class C>bool known(C& c,uint32_t pc)const{
        return pc>=e_.helper&&pc-e_.helper<1024u&&
            std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>static bool safe(C& c){
        return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);
    }
    template<class C>bool live(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.lr==e_.call+4u&&
               c.gpr[1]==gp_[1]&&c.gpr[2]==gp_[2]&&c.gpr[13]==gp_[13]&&
               c.inst_count>=start_&&c.inst_count-start_<=1024u;
    }
    template<class C>bool protected_unchanged(C& c){
        for(unsigned i=0;i<protected_.size();++i){
            auto a=protected_[i];
            if(!mapped(c,a))return false;
            for(unsigned j=0;j<a.size;++j)if(c.mmu.read8(a.base+j)!=shadow_[i][j])return false;
        }
        return true;
    }
    template<class C>static uint32_t pack(C& c){
        uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;
    }
    template<class C>bool abi(C& c)const{
        if((pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
    }
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));
    }
    template<class C>bool branch_ctr(C& c,uint32_t w){
        if(!((w>>21)&4u)){ctr_due_=true;ctr_expected_=c.ctr-1u;}
        return true;
    }
};
}
