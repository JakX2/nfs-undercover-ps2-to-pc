#pragma once
#include "wii_ipc_ring_dispatch.h"
#include "wii_ipc_profile_execution.h"
#include <algorithm>
#include <span>
namespace undercover::wii {
struct IpcDispatchWord {uint32_t owner,pc,word;};
struct IpcDispatchEdge {uint32_t call,target,word;};
struct IpcDispatchExpectation {
    uint32_t submit,start,stop;
    std::array<IpcDispatchEdge,3> calls;
    std::span<const IpcDispatchWord> words;
    AllocatorRange ring,credit;
    unsigned slots;
    IpcProfileLayout profile;
};
// Bounded instruction witness. The bus is owned by an independent device
// gate. A callback is only authorized at the predicted original MMIO site.
// No instructions or memory stores are synthesized here.
class IpcDispatchExecution {
public:
    explicit IpcDispatchExecution(IpcDispatchExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned memory_failure()const{return ring_.failure();}
    unsigned visits()const{return visits_;}
    unsigned stores()const{return ring_.stores();}
    unsigned polls()const{return polls_;}
    unsigned calls()const{return call_count_;}
    unsigned writes()const{return writes_;}
    unsigned reads()const{return reads_;}
    unsigned ordinal()const{return ordinal_;}
    unsigned detail()const{return detail_;}
    template<class C>bool begin(C& c,bool held,AllocatorRange request,AllocatorRange stack){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.start||!known(c,e_.submit,e_.start)||
           !known(c,e_.submit,e_.stop)||e_.start>=e_.calls[0].call||
           e_.calls[0].call>=e_.calls[1].call||e_.calls[1].call>=e_.calls[2].call||
           e_.stop!=e_.calls[2].call+4u||e_.stop-e_.start>512u||
           e_.calls[0].target!=e_.calls[2].target||e_.calls[0].target==e_.calls[1].target||
           stack.base!=c.gpr[1]||stack.size<8u||stack.size>520u||
           !ring_.begin(c,e_.ring,e_.credit,request,stack,e_.slots,true))return fail(1);
        for(auto edge:e_.calls)
            if(edge.word>>26!=18u||(edge.word&3u)!=1u||target(edge.call,edge.word)!=edge.target||
               !known(c,e_.submit,edge.call,edge.word)||!known(c,edge.target,edge.target))return fail(1);
        protected_={stack,e_.profile.pending,e_.profile.unissued,e_.profile.pointers,e_.profile.descriptors};
        for(unsigned i=0;i<protected_.size();++i){
            auto a=protected_[i];
            if(!mapped(c,a)||a.size>520u||overlap(a,request)||overlap(a,e_.ring)||overlap(a,e_.credit))return fail(1);
            for(unsigned j=0;j<i;++j)if(overlap(a,protected_[j]))return fail(1);
            for(unsigned j=0;j<a.size;++j)shadow_[i].push_back(c.mmu.read8(a.base+j));
        }
        request_=request.base;gp_=c.gpr;msr_=c.msr;cpu_=&c;
        owner_=e_.submit;next_=e_.start;last_=start_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!live(c,held)||entry_due_||return_due_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,owner_,pc,w)||++visits_>512u)return fail(2);
        ordinal_=(pc-owner_)/4u+1u;
        if(!settle(c))return fail(3);
        last_=c.inst_count;next_=pc+4u;poll_pc_=0;polled_=false;
        const unsigned op=w>>26,xo=(w>>1)&1023u,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
        const bool st=op==36u||(op==31u&&xo==151u),ld=op==32u||(op==31u&&xo==23u);
        if(owner_!=e_.submit&&(st||ld)){
            // MMIO-only helpers. Compute the original effective address;
            // the host callback must match it and the exact source word.
            if(call_count_<1u||call_count_>3u||access_seen_||st!=(call_count_!=2u))return fail(4);
            uint32_t a=uint32_t(ra?c.gpr[ra]:0u)+(op==31u?c.gpr[rb]:uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000));
            // The pinned runtime MMU forwards physical addresses, not the
            // original guest alias, to HW_Reg_Read32/Write32.
            if((a&3u)||(a&0xc0000000u)==0x40000000u)return fail(4);
            access_due_=st?2u:1u;access_addr_=a&0x3fffffffu;access_reg_=rs;access_value_=c.gpr[rs];access_seen_=true;
        }else if(st){
            const int64_t ea=int64_t(ra?c.gpr[ra]:0u)+(op==31u?int64_t(c.gpr[rb]):int64_t(int32_t((w&0xffffu)^0x8000u)-0x8000));
            if(ea<0||ea>0xffffffffll||!ring_.authorize(c,uint32_t(ea),c.gpr[rs],4u,true)){
                detail_=ring_.stage();return fail(3);
            }
        }else if(op==37u||op==38u||op==39u||op==44u||op==45u||op==47u||
                 op==52u||op==53u||op==54u||op==55u||op==60u||op==61u||
                 (op==31u&&(xo==183u||xo==215u||xo==247u||xo==407u||xo==439u||xo==661u||xo==662u||
                    xo==725u||xo==918u||xo==663u||xo==695u||xo==727u||xo==759u||xo==983u||xo==1014u||xo==150u)))return fail(3);
        if(op==17u||(op==19u&&(xo==50u||xo==528u))||(op==31u&&(xo==146u||xo==467u)))return fail(4);
        if(op==18u&&(w&1u)){
            if(owner_!=e_.submit||call_count_>=3u)return fail(4);
            auto edge=e_.calls[call_count_];
            if(pc!=edge.call||w!=edge.word||!known(c,edge.target,edge.target))return fail(4);
            if(call_count_==0u&&ring_.stage()!=1u)return fail(4);
            if(call_count_==1u&&ring_.stage()!=2u)return fail(4);
            if(call_count_==2u&&(!ring_.control_ready(c,true)||reads_!=1u))return fail(4);
            next_=edge.target;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(owner_==e_.submit||w!=0x4e800020u||!access_seen_||!helper_abi(c)||c.lr!=e_.calls[call_count_-1u].call+4u)return fail(4);
            return_due_=true;next_=c.lr;return true;
        }
        if(op==16u||op==18u){
            if(w&3u||owner_!=e_.submit)return fail(4);
            const uint32_t dst=target(pc,w);
            if(dst<=pc)poll_pc_=pc;
            if(op==18u||taken(c,w))next_=dst;
            if(op==16u&&!((w>>21)&4u)){ctr_due_=true;ctr_expected_=c.ctr-1u;}
        }
        if(!known(c,owner_,next_))return fail(4);
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!entry_due_||call_count_>=3u||c.pc!=pc||pc!=next_||
           c.inst_count!=last_||!settle(c))return fail(5);
        const auto edge=e_.calls[call_count_];
        if(pc!=edge.target||c.lr!=edge.call+4u)return fail(5);
        ++call_count_;owner_=pc;entry_due_=false;access_seen_=false;helper_=c.gpr;helper_cr_=pack(c)&0x00fff000u;
        return true;
    }
    // A native read callback returns its actual result. Verify the
    // translated load placed that result in the expected guest register.
    template<class C>bool read_allowed(C& c,uint32_t addr,bool held){
        return live(c,held)&&access_due_==1u&&addr==access_addr_&&c.inst_count==last_&&call_count_==2u&&reads_==0u&&ring_.settled(c);
    }
    template<class C>bool read_done(C& c,uint32_t value,bool held){
        if(!read_allowed(c,access_addr_,held))return fail(6);
        access_due_=0;load_due_=true;load_value_=value;++reads_;return true;
    }
    template<class C>bool write_allowed(C& c,uint32_t addr,uint32_t value,bool held){
        return live(c,held)&&access_due_==2u&&addr==access_addr_&&value==access_value_&&c.inst_count==last_&&
            ((call_count_==1u&&writes_==0u&&value==(request_&0x3fffffffu)&&ring_.stage()==1u&&ring_.settled(c))||
             (call_count_==3u&&writes_==1u&&ring_.control_ready(c,true)));
    }
    template<class C>bool write_done(C& c,uint32_t addr,uint32_t value,bool held){
        if(!write_allowed(c,addr,value,held))return fail(6);
        if(writes_==0u){if(!ring_.message_written(c,value,true))return fail(6);}
        else if(!ring_.control_written(c,true))return fail(6);
        access_due_=0;++writes_;return true;
    }
    // Local continuation hook before the next original tick.
    template<class C>bool returned(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!return_due_||entry_due_||c.pc!=pc||pc!=next_||c.lr!=pc||
           c.inst_count!=last_||!settle(c)||!helper_abi(c)||!known(c,e_.submit,pc))return fail(7);
        owner_=e_.submit;return_due_=false;
        if(call_count_==3u){
            if(pc!=e_.stop||writes_!=2u||reads_!=1u||!ring_.complete(c))return fail(7);
            stage_=2;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||!poll_pc_||polled_||c.pc!=poll_pc_||c.inst_count!=last_||
           access_due_||!ring_.settled(c)||!protected_unchanged(c)||++polls_>128u)return fail(8);
        polled_=true;return true;
    }
    template<class C>bool reached(C& c,bool held){
        return stage_==2u&&live(c,held)&&c.pc==e_.stop&&c.inst_count==last_&&
            !entry_due_&&!return_due_&&writes_==2u&&reads_==1u&&ring_.complete(c)&&protected_unchanged(c);
    }
private:
    IpcDispatchExpectation e_;IpcRingDispatchWitness ring_;
    std::array<AllocatorRange,5> protected_{};
    std::array<std::vector<uint8_t>,5> shadow_{};
    std::array<uint32_t,32> gp_{},helper_{};
    const void* cpu_=nullptr;
    uint32_t request_=0,msr_=0,owner_=0,next_=0,poll_pc_=0,helper_cr_=0,ctr_expected_=0,
             access_addr_=0,access_value_=0,load_value_=0;
    uint64_t start_=0,last_=0;
    unsigned stage_=0,error_=0,visits_=0,ordinal_=0,detail_=0,polls_=0,call_count_=0,writes_=0,reads_=0,
             access_due_=0,access_reg_=0;
    bool entry_due_=false,return_due_=false,polled_=false,ctr_due_=false,access_seen_=false,load_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool overlap(AllocatorRange a,AllocatorRange b){return a.size&&b.size&&a.base<b.end()&&b.base<a.end();}
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||!((a.base>=0x80000000u&&a.end()<=0x81800000ull)||(a.base>=0x90000000u&&a.end()<=0x94000000ull)))return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return !(pc&3u)&&mapped(c,{pc,4})&&std::count_if(e_.words.begin(),e_.words.end(),
            [&](auto x){return x.owner==owner&&x.pc==pc&&c.mmu.read32(pc)==x.word;})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&c.mmu.read32(pc)==w;}
    template<class C>bool protected_unchanged(C& c){
        for(unsigned i=0;i<protected_.size();++i){
            auto a=protected_[i];if(!mapped(c,a))return false;
            for(unsigned j=0;j<a.size;++j)if(c.mmu.read8(a.base+j)!=shadow_[i][j])return false;
        }return true;
    }
    template<class C>bool settle(C& c){
        if(access_due_||!ring_.settled(c)||!protected_unchanged(c)||(ctr_due_&&c.ctr!=ctr_expected_)||
           (load_due_&&c.gpr[access_reg_]!=load_value_))return false;
        ctr_due_=false;load_due_=false;return true;
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool live(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.gpr[1]==gp_[1]&&c.gpr[2]==gp_[2]&&
               c.gpr[13]==gp_[13]&&c.inst_count>=start_&&c.inst_count-start_<=512u;
    }
    template<class C>static uint32_t pack(C& c){
        uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;
    }
    template<class C>bool helper_abi(C& c)const{
        if((pack(c)&0x00fff000u)!=helper_cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=helper_[i])return false;
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
};
}
