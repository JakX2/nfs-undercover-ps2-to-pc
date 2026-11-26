#pragma once
#include "wii_ipc_dispatch_execution.h"
#include "wii_ipc_deferred_ack_memory.h"
#include "wii_stm_deferred_event_gate.h"
namespace undercover::wii {
struct DeferredAckExpectation {
    uint32_t handler,returned,return_word,final_blr,read_root,write_root,profile_root,credit_site,profile_site;
    std::span<const IpcDispatchWord> words;
    std::span<const IpcDispatchEdge> calls;
};
// Observe original handler, MMIO leaves, and accounting helper. The
// native emitter performs every guest instruction and every RAM store.
class DeferredAckExecution {
public:
    explicit DeferredAckExecution(DeferredAckExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned reads()const{return reads_;}
    unsigned writes()const{return writes_;}
    unsigned stack_stores()const{return stack_stores_;}
    unsigned calls()const{return calls_;}
    unsigned polls()const{return polls_;}
    unsigned ordinal()const{return ordinal_;}
    template<class C>bool begin(C& c,StmDeferredEventGate& gate,IpcDeferredAckMemory& mem,bool held){
        if(stage_||error_||!held||!safe(c)||c.pc!=e_.handler||c.lr!=e_.returned||
           !known(c,e_.handler,e_.handler)||!word(c,e_.returned,e_.return_word)||
           !known(c,e_.handler,e_.final_blr,0x4e800020u)||
           !known(c,e_.handler,e_.credit_site)||!known(c,e_.profile_root,e_.profile_site)||
           e_.words.empty()||e_.words.size()>512u||e_.calls.empty()||e_.calls.size()>32u||
           c.gpr[1]<0x80000200u||c.gpr[1]>0x817ffff0u||(c.gpr[1]&7u)||
           !gate.deferred_held(true)||mem.stage()!=1u||!mem.settled(c))return fail(1);
        for(auto edge:e_.calls)
            if(edge.word>>26!=18u||(edge.word&3u)!=1u||target(edge.call,edge.word)!=edge.target||
               !known(c,e_.handler,edge.call,edge.word)||!admitted(edge.target)||
               !known(c,edge.target,edge.target))return fail(1);
        frame_={c.gpr[1]-512u,520u};
        if(!mapped(c,frame_))return fail(1);
        for(unsigned i=0;i<frame_.size;++i)stack_.push_back(c.mmu.read8(frame_.base+i));
        gate_=&gate;mem_=&mem;cpu_=&c;gp_=c.gpr;msr_=c.msr;cr_=pack(c)&0x00fff000u;
        owner_=e_.handler;next_=c.pc;start_=last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!live(c,held)||entry_due_||return_due_||(initial_poll_&&!resumed_)||pc!=next_||
           c.inst_count-last_!=1u||!known(c,owner_,pc,w)||++visits_>1024u||!settled(c))return fail(2);
        last_=c.inst_count;ordinal_=(pc-owner_)/4u+1u;next_=pc+4u;poll_pc_=0;polled_=false;
        const unsigned op=w>>26,xo=(w>>1)&1023u,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
        const bool st=op==36u||op==37u||op==47u||(op==31u&&xo==151u);
        const bool ld=op==32u||(op==31u&&xo==23u);
        const bool bus=owner_==e_.read_root||owner_==e_.write_root;
        if(bus&&(st||ld)){
            if(access_seen_||st!=(owner_==e_.write_root)||op==37u||op==47u)return fail(3);
            auto a=ea(c,w);
            if(a>0xffffffffull||(a&3u)||(a&0xc0000000u)==0x40000000u)return fail(3);
            access_addr_=uint32_t(a)&0x3fffffffu;access_value_=c.gpr[rs];access_reg_=rs;
            access_due_=st?2u:1u;access_seen_=true;
        }else if(st){
            auto a=ea(c,w);
            if(a>0xffffffffull||(a&3u))return fail(4);
            if((owner_==e_.handler&&pc==e_.credit_site)||(owner_==e_.profile_root&&pc==e_.profile_site)){
                if(op!=36u||!gate_->ack_latch_cleared(true)||!mem_->authorize(c,uint32_t(a),c.gpr[rs],4u,true))return fail(4);
            }else{
                const unsigned count=op==47u?32u-rs:1u;
                if(owner_!=e_.handler||ra!=1u||!frame_.contains(uint32_t(a),4u*count)||++stack_stores_>32u||
                   (op==37u&&(rs!=1u||a>=c.gpr[1])))return fail(4);
                for(unsigned j=0;j<count;++j)for(unsigned i=0;i<4;++i)
                    stack_[uint32_t(a)-frame_.base+j*4u+i]=uint8_t(c.gpr[rs+j]>>(24u-i*8u));
                if(op==37u){sp_due_=true;sp_expected_=uint32_t(a);}
            }
        }else if(op==38u||op==39u||op==44u||op==45u||op==52u||op==53u||op==54u||op==55u||op==60u||op==61u||
                 (op==31u&&(xo==150u||xo==183u||xo==215u||xo==247u||xo==407u||xo==439u||xo==661u||xo==662u||
                    xo==725u||xo==918u||xo==663u||xo==695u||xo==727u||xo==759u||xo==983u||xo==1014u)))return fail(4);
        if(op==17u||(op==19u&&(xo==50u||xo==528u))||(op==31u&&xo==146u))return fail(5);
        if(op==31u&&xo==467u){
            const auto spr=ra|(rb<<5);
            if(owner_!=e_.handler||spr!=8u||c.gpr[rs]!=e_.returned)return fail(5);
        }
        if(op==18u&&(w&1u)){
            if(owner_!=e_.handler||calls_>=32u)return fail(5);
            auto it=std::find_if(e_.calls.begin(),e_.calls.end(),[&](auto x){return x.call==pc&&x.word==w;});
            if(it==e_.calls.end()||!admitted(it->target))return fail(5);
            if(it->target==e_.profile_root&&(!gate_->ack_latch_cleared(true)||mem_->stores()!=1u))return fail(5);
            next_=it->target;helper_return_=pc+4u;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w!=0x4e800020u)return fail(5);
            if(owner_!=e_.handler){
                if(c.lr!=helper_return_||!helper_abi(c)||(bus&&!access_seen_)||
                   (owner_==e_.profile_root&&mem_->stores()!=2u))return fail(5);
                owner_=e_.handler;next_=c.lr;return true;
            }
            if(pc!=e_.final_blr||c.lr!=e_.returned||!caller_abi(c)||!gate_->completed(true)||
               !mem_->complete(c,true)||writes_!=2u||!reads_||!stack_stores_)return fail(5);
            return_due_=true;next_=e_.returned;return true;
        }
        if(op==16u||op==18u){
            if(w&3u||owner_!=e_.handler)return fail(5);
            const auto dst=target(pc,w);
            if(dst<=pc)poll_pc_=pc;
            if(op==18u||taken(c,w))next_=dst;
            if(op==16u&&!((w>>21)&4u)){ctr_due_=true;ctr_expected_=c.ctr-1u;}
        }
        if(!known(c,owner_,next_))return fail(5);
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        // A stopped dispatcher checkpoint is resumed by the authentic
        // outer dispatcher, adding one dispatch tick before root entry.
        if(!visits_&&!entry_due_&&initial_poll_&&!resumed_){
            if(!live(c,held)||pc!=e_.handler||c.pc!=pc||c.lr!=e_.returned||
               c.inst_count-last_!=1u||c.gpr!=gp_||!settled(c))return fail(6);
            resumed_=true;last_=c.inst_count;return true;
        }
        if(!live(c,held)||!entry_due_||c.pc!=pc||pc!=next_||c.lr!=helper_return_||
           c.inst_count!=last_||!settled(c)||!admitted(pc))return fail(6);
        owner_=pc;entry_due_=false;access_seen_=false;helper_=c.gpr;helper_cr_=pack(c)&0x00fff000u;++calls_;return true;
    }
    template<class C>std::optional<uint32_t> read(C& c,uint32_t a,bool held){
        if(!live(c,held)||access_due_!=1u||a!=access_addr_||c.inst_count!=last_||reads_>=32u){fail(7);return {};}
        auto v=gate_->read_ack(a,c.msr,true);
        if(!v){fail(7);return {};}
        ++reads_;access_due_=0;load_due_=true;load_value_=*v;return v;
    }
    template<class C>bool write(C& c,uint32_t a,uint32_t v,bool held){
        if(!live(c,held)||access_due_!=2u||a!=access_addr_||v!=access_value_||c.inst_count!=last_||writes_>=2u||
           !gate_->ack_write(a,v,c.msr,true))return fail(7);
        access_due_=0;++writes_;
        // The original handler accounts for the consumed request after
        // clearing Y2, potentially before the separate Hollywood W1C.
        if(writes_==1u&&!mem_->latch_cleared(c,gate_->ack_latch_cleared(true)))return fail(7);
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!live(c,held)||c.inst_count!=last_||++polls_>128u)return fail(8);
        // Backward-edge callbacks occur before the emitter's CTR update.
        const bool ctr_pending=ctr_due_;ctr_due_=false;
        const bool stable=settled(c);ctr_due_=ctr_pending;
        if(!stable)return fail(8);
        if(!visits_&&!initial_poll_&&c.pc==e_.handler&&c.lr==e_.returned&&c.gpr==gp_){
            initial_poll_=true;return true;
        }
        if(return_due_&&c.pc==e_.returned&&c.lr==e_.returned&&caller_abi(c)&&
           mem_->preserved(c)&&gate_->completed(true)){
            stage_=2;return true;
        }
        if(poll_pc_&&c.pc==poll_pc_&&!polled_){polled_=true;return true;}
        return fail(8);
    }
    template<class C>bool reached(C& c,bool held){
        return stage_==2u&&live(c,held)&&return_due_&&c.pc==e_.returned&&c.lr==e_.returned&&
            c.inst_count==last_&&caller_abi(c)&&mem_->preserved(c)&&gate_->completed(true)&&settled(c);
    }
private:
    DeferredAckExpectation e_;StmDeferredEventGate* gate_=nullptr;IpcDeferredAckMemory* mem_=nullptr;
    const void* cpu_=nullptr;AllocatorRange frame_{};std::vector<uint8_t> stack_;
    std::array<uint32_t,32> gp_{},helper_{};
    uint32_t msr_=0,cr_=0,owner_=0,next_=0,poll_pc_=0,helper_return_=0,helper_cr_=0,
             access_addr_=0,access_value_=0,load_value_=0,sp_expected_=0,ctr_expected_=0;
    uint64_t start_=0,last_=0;
    unsigned stage_=0,error_=0,visits_=0,ordinal_=0,reads_=0,writes_=0,calls_=0,stack_stores_=0,polls_=0,
             access_due_=0,access_reg_=0;
    bool entry_due_=false,return_due_=false,access_seen_=false,load_due_=false,sp_due_=false,ctr_due_=false,polled_=false,initial_poll_=false,resumed_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool admitted(uint32_t pc)const{return pc==e_.read_root||pc==e_.write_root||pc==e_.profile_root;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool live(C& c,bool held)const{
        return !error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.gpr[2]==gp_[2]&&c.gpr[13]==gp_[13]&&
            c.gpr[1]>=frame_.base&&c.gpr[1]<=gp_[1]&&!(c.gpr[1]&7u)&&
            c.inst_count>=start_&&c.inst_count-start_<=1024u&&gate_&&gate_->ack_held(true);
    }
    template<class C>bool settled(C& c){
        if(access_due_||!mem_||!mem_->settled(c)||!mapped(c,frame_)||
           (load_due_&&c.gpr[access_reg_]!=load_value_)||(sp_due_&&c.gpr[1]!=sp_expected_)||
           (ctr_due_&&c.ctr!=ctr_expected_))return false;
        load_due_=sp_due_=ctr_due_=false;
        for(unsigned i=0;i<stack_.size();++i)if(c.mmu.read8(frame_.base+i)!=stack_[i])return false;
        return true;
    }
    template<class C>static uint64_t ea(C& c,uint32_t w){
        unsigned ra=(w>>16)&31u,rb=(w>>11)&31u;
        int64_t a=int64_t(ra?c.gpr[ra]:0u)+(w>>26==31u?int64_t(c.gpr[rb]):
            int64_t(int32_t((w&0xffffu)^0x8000u)-0x8000));
        return uint64_t(a);
    }
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||a.base<0x80000000u||a.end()>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,{a,4})&&c.mmu.read32(a)==w;}
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        return std::count_if(e_.words.begin(),e_.words.end(),[&](auto x){return x.owner==owner&&x.pc==pc&&word(c,pc,x.word);})==1;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{return known(c,owner,pc)&&word(c,pc,w);}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool helper_abi(C& c)const{
        if(c.gpr[1]!=helper_[1]||c.gpr[2]!=helper_[2]||(pack(c)&0x00fff000u)!=helper_cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=helper_[i])return false;
        return true;
    }
    template<class C>bool caller_abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=13;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    static uint32_t target(uint32_t pc,uint32_t w){const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;return pc+(((w&m)^s)-s);}
    template<class C>static bool taken(C& c,uint32_t w){const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;const auto& f=c.cr[bi/4u];
        const bool bit=bi%4u==0u?f.lt:bi%4u==1u?f.gt:bi%4u==2u?f.eq:f.so;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bit==bool(bo&8u));}
};
}
