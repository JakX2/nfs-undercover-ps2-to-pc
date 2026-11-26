#pragma once
#include "wii_ipc_dispatch_execution.h"
namespace undercover::wii {
struct AsyncWrapperReturnExpectation {
    uint32_t wrapper,start,caller,caller_word,restore_count;
    IpcDispatchEdge restore;
    std::span<const IpcDispatchWord> words;
};
// Original wrapper epilogue: read-only frame restoration, no device
// access, no request release and no fabricated caller result.
class AsyncWrapperReturnWitness {
public:
    explicit AsyncWrapperReturnWitness(AsyncWrapperReturnExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned loads()const{return loads_;}
    unsigned restored()const{return restored_;}
    unsigned ordinal()const{return ordinal_;}
    unsigned polls()const{return polls_;}
    unsigned return_detail()const{return return_detail_;}
    template<class C>bool begin(C& c,bool held,uint32_t caller_sp){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.start||c.gpr[3]!=0u||
           !known(c,e_.wrapper,e_.start)||!word(c,e_.caller,e_.caller_word)||
           !known(c,e_.wrapper,e_.restore.call,e_.restore.word)||!known(c,e_.restore.target,e_.restore.target)||
           e_.restore.word>>26!=18u||(e_.restore.word&3u)!=1u||target(e_.restore.call,e_.restore.word)!=e_.restore.target||
           e_.restore_count<1u||e_.restore_count>18u||caller_sp<=c.gpr[1]||
           caller_sp-c.gpr[1]>512u||(caller_sp&7u)||(c.gpr[1]&7u))return fail(1);
        sp_=c.gpr[1];caller_sp_=caller_sp;msr_=c.msr;r2_=c.gpr[2];r13_=c.gpr[13];
        frame_={sp_,caller_sp_-sp_+8u};
        if(!mapped(c,frame_))return fail(1);
        for(unsigned i=0;i<frame_.size;++i)shadow_.push_back(c.mmu.read8(frame_.base+i));
        cpu_=&c;owner_=e_.wrapper;next_=e_.start;tick_=last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!live(c,held)||entry_due_||return_due_||pc!=next_||
           c.inst_count-last_!=1u||!known(c,owner_,pc,w)||++visits_>128u||!settled(c))return fail(2);
        ordinal_=(pc-owner_)/4u+1u;last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
        if(op==32u){
            const int64_t ea=int64_t(ra?c.gpr[ra]:0u)+int32_t((w&0xffffu)^0x8000u)-0x8000;
            if(!ra||ea<0||ea>0xffffffffll||(ea&3)||!frame_.contains(uint32_t(ea),4u))return fail(3);
            if(owner_==e_.restore.target){
                if(restored_>=e_.restore_count||rs!=32u-e_.restore_count+restored_)return fail(3);
                ++restored_;
            }else if(rs!=0u)return fail(3);
            pending_=true;load_reg_=rs;load_value_=c.mmu.read32(uint32_t(ea));++loads_;
        }else if(op==18u&&(w&1u)){
            if(owner_!=e_.wrapper||entered_||pc!=e_.restore.call||w!=e_.restore.word||c.gpr[1]!=sp_)return fail(4);
            next_=e_.restore.target;entry_due_=true;return true;
        }else if(op==19u&&xo==16u){
            if(w!=0x4e800020u)return fail(4);
            if(owner_==e_.restore.target){
                if(restored_!=e_.restore_count||c.lr!=e_.restore.call+4u||c.gpr[1]!=sp_)return fail(4);
                for(unsigned i=0;i<32u-e_.restore_count;++i)if(c.gpr[i]!=helper_[i])return fail(4);
                owner_=e_.wrapper;next_=c.lr;return true;
            }
            if(!entered_||restored_!=e_.restore_count||c.lr!=e_.caller||c.gpr[1]!=caller_sp_||c.gpr[3]!=0u)return fail(4);
            return_due_=true;next_=e_.caller;return true;
        }else if(op==31u&&xo==467u){
            if(owner_!=e_.wrapper||(ra|(rb<<5))!=8u||c.gpr[rs]!=e_.caller)return fail(4);
        }else if(op==16u||op==18u){
            if(owner_!=e_.wrapper||(w&3u)||target(pc,w)<=pc)return fail(4);
            if(op==16u&&!((w>>21)&4u))return fail(4);
            if(op==18u||taken(c,w))next_=target(pc,w);
        }else if(owner_!=e_.wrapper||
                 !(op==10u||op==11u||op==14u||op==15u||op==20u||op==21u||op==23u||
                   (op>=24u&&op<=29u)||(op==31u&&(xo==0u||xo==32u||xo==28u||xo==444u||xo==266u||xo==316u))))return fail(4);
        if(!known(c,owner_,next_))return fail(4);
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!live(c,held)||!entry_due_||entered_||c.pc!=pc||pc!=next_||pc!=e_.restore.target||
           c.lr!=e_.restore.call+4u||c.inst_count!=last_||!settled(c))return fail(5);
        owner_=pc;entry_due_=false;entered_=true;helper_=c.gpr;return true;
    }
    // The pinned emitter may poll at the local return after the final
    // BLR. Admit only the exact not-yet-executed STM continuation.
    template<class C>bool poll(C& c,bool held,bool caller_abi){
        if(stage_!=1u||!live(c,held)||!return_due_||polls_||!caller_abi||
           c.pc!=e_.caller||c.lr!=e_.caller||c.inst_count!=last_||
           c.gpr[1]!=caller_sp_||c.gpr[3]!=0u||!word(c,c.pc,e_.caller_word)||!settled(c))return fail(7);
        ++polls_;return true;
    }
    template<class C>bool returned(C& c,uint32_t pc,bool held,bool caller_abi){
        if(stage_!=1u||!live(c,held)||!return_due_)return bad_return(1);
        if(!caller_abi)return bad_return(2);
        if(pc!=e_.caller||c.pc!=pc||c.lr!=pc||!word(c,pc,e_.caller_word))return bad_return(3);
        // The authenticated outer dispatcher polls before its own dispatch
        // tick. A direct local continuation has no extra tick.
        if(c.inst_count-last_!=unsigned(polls_==1u))return bad_return(4);
        if(c.gpr[1]!=caller_sp_||c.gpr[3]!=0u||!settled(c))return bad_return(5);
        last_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool reached(C& c,bool held,bool caller_abi){
        return stage_==2u&&live(c,held)&&caller_abi&&c.pc==e_.caller&&c.lr==e_.caller&&
            c.inst_count==last_&&c.gpr[1]==caller_sp_&&c.gpr[3]==0u&&settled(c);
    }
private:
    AsyncWrapperReturnExpectation e_;
    const void* cpu_=nullptr;
    AllocatorRange frame_{};
    std::vector<uint8_t> shadow_;
    std::array<uint32_t,32> helper_{};
    uint32_t sp_=0,caller_sp_=0,msr_=0,r2_=0,r13_=0,owner_=0,next_=0,load_reg_=0,load_value_=0;
    uint64_t tick_=0,last_=0;
    unsigned stage_=0,error_=0,visits_=0,loads_=0,restored_=0,ordinal_=0,polls_=0,return_detail_=0;
    bool entry_due_=false,entered_=false,return_due_=false,pending_=false;
    bool bad_return(unsigned n){return_detail_=n;return fail(6);}
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool live(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.gpr[2]==r2_&&c.gpr[13]==r13_&&
            (c.gpr[1]==sp_||c.gpr[1]==caller_sp_)&&c.inst_count>=tick_&&c.inst_count-tick_<=128u;
    }
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||a.base<0x80000000u||a.end()>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
    template<class C>bool settled(C& c){
        if(!mapped(c,frame_)||(pending_&&c.gpr[load_reg_]!=load_value_))return false;
        pending_=false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,{a,4})&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;return (bo&16u)||bit==bool(bo&8u);}
};
}
