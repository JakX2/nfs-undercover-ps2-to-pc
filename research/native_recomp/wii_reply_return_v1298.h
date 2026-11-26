#pragma once
#include "wii_reply_completion_v1293.h"
namespace undercover::wii {
// Capture the real caller's nonvolatile state before starting either
// original function. The continuation never restores registers itself.
struct ReplyReturnAbi {
    const void* cpu=nullptr;uint32_t entry=0,ret=0,cr=0,msr=0;
    uint64_t tick=0;std::array<uint32_t,32> gp{};
    template<class C>static uint32_t packed(C& c){
        uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;
    }
    template<class C>static ReplyReturnAbi capture(C& c){
        return {&c,c.pc,c.lr,packed(c)&0x00fff000u,c.msr,c.inst_count,c.gpr};
    }
    template<class C>bool restored(C& c)const{
        if(cpu!=&c||c.inst_count<=tick||c.lr!=ret||c.msr!=msr||
           c.gpr[1]!=gp[1]||c.gpr[2]!=gp[2]||c.gpr[13]!=gp[13]||(packed(c)&0x00fff000u)!=cr)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp[i])return false;
        return true;
    }
};
struct ReplyReturnExpectation {
    uint32_t processor,handler,read_leaf,write_leaf,wake_return,processor_return,dispatcher_return,counter;
    std::span<const ReplyNativeWord> words;std::span<const VectorEdge> edges;bool require_x2=false;
    uint32_t helper=0,helper_return=0;
};
// Continue after the original OSWakeupThread return. The only allowed
// device effect is the native final Hollywood interrupt acknowledgment.
// Actual original processor/handler BLRs must restore both ABI frames.
class ReplyReturnWitness {
public:
    explicit ReplyReturnWitness(ReplyReturnExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned gate_failure()const{return gate_.failure();}
    unsigned visits()const{return visits_;}
    unsigned writes()const{return gate_.writes();}
    unsigned x2_writes()const{return gate_.x2_writes();}
    unsigned helper_returns()const{return helper_returned_?1u:0u;}
    unsigned control_detail()const{return control_detail_;}
    unsigned instruction_detail()const{return instruction_detail_;}
    unsigned instruction_boundary()const{return instruction_boundary_;}
    unsigned instruction_owner()const{return instruction_owner_;}
    unsigned instruction_ticks()const{return instruction_ticks_;}
    unsigned control_target()const{return control_target_;}
    unsigned control_owner()const{return owner_class(last_owner_);}
    unsigned write_detail()const{return gate_.write_detail();}
    unsigned write_register()const{return gate_.write_register();}
    unsigned write_control_bits()const{return gate_.write_control_bits();}
    unsigned write_value_class()const{return gate_.write_value_class();}
    template<class C>bool begin(C& c,const ReplyProcessorWitness& body,const WakeReadyWitness& ready,
        const NestedWakeReturnWitness& nested,ExternalReturnWitness& frame,uint32_t queue,uint32_t request,
        ReplyReturnAbi handler,ReplyReturnAbi processor,bool held){
        if(stage_||error_||handler.cpu!=&c||processor.cpu!=&c||handler.entry!=e_.handler||
           processor.entry!=e_.processor||handler.ret!=e_.dispatcher_return||processor.ret!=e_.processor_return||
           handler.tick>=processor.tick||processor.tick>=c.inst_count||c.pc!=e_.wake_return||c.lr!=c.pc||
           !mapped(c,e_.counter)||!c.mmu.read32(e_.counter)||c.mmu.read32(e_.counter)>1024u||
           e_.words.empty()||e_.words.size()>1024u||e_.edges.size()>64u||
           !known(c,e_.processor,e_.wake_return)||!known(c,e_.handler,e_.processor_return)||
           !known(c,e_.read_leaf,e_.read_leaf)||!known(c,e_.write_leaf,e_.write_leaf)||
           (bool(e_.helper)!=bool(e_.helper_return))||
           (e_.helper&&(!e_.require_x2||!known(c,e_.helper,e_.helper)||!known(c,e_.processor,e_.helper_return)))||
           !gate_.begin(c,body,ready,nested,frame,queue,request,held))return fail(1);
        for(auto x:e_.words)if(std::count_if(e_.words.begin(),e_.words.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(1);
        handler_=handler;processor_=processor;counter_=c.mmu.read32(e_.counter);
        active_=e_.processor;next_=e_.wake_return;last_=c.inst_count;stage_=1;outer_due_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!common(c,held)||!entry_due_||pc!=next_||c.pc!=pc||c.inst_count!=last_||
           c.lr!=ret_||!known(c,pc,pc))return fail(2);
        entry_due_=false;active_=pc;
        if(e_.helper&&pc==e_.helper){if(helper_returned_||gate_.x2_writes()!=1u)return fail(2);helper_abi_=ReplyReturnAbi::capture(c);}
        return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        instruction_owner_=owner_class(active_);
        instruction_ticks_=c.inst_count>=last_&&c.inst_count-last_<=8u?unsigned(c.inst_count-last_):9u;
        if(!common(c,held)){
            instruction_boundary_=!held?1u:stage_!=1u||error_?2u:!gate_.boundary(c,held)?gate_.boundary_class(c,held)+3u:3u;
            return instruction_fail(1);
        }
        if(entry_due_)return instruction_fail(2);
        if(outer_due_)return instruction_fail(3);
        if(poll_due_)return instruction_fail(4);
        if(pc!=next_)return instruction_fail(5);
        if(c.inst_count-last_!=(outer_resume_?2u:1u))return instruction_fail(6);
        if(!known(c,active_,pc,w))return instruction_fail(7);
        if(++visits_>4096u)return instruction_fail(8);
        if(outer_resume_){if(c.pc!=pc)return instruction_fail(9);outer_resume_=false;}
        if(mmio_window()&&(!used_||!mmio_.completed(c,read_value_)))return fail(7);
        last_=c.inst_count;last_pc_=pc;last_owner_=active_;next_=pc+4u;
        mmio_=WordMmioInstruction::decode(c,w);used_=false;read_value_=0;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&1u)){
            const auto dst=target(pc,w);
            if(w&2u)return control_fail(1,dst);
            if(ret_)return control_fail(2,dst);
            if(active_!=e_.processor&&active_!=e_.handler)return control_fail(3,dst);
            if(dst!=e_.read_leaf&&dst!=e_.write_leaf){
                if(!e_.helper||dst!=e_.helper||active_!=e_.processor||pc+4u!=e_.helper_return||
                   helper_returned_||gate_.x2_writes()!=1u)return control_fail(4,dst);
            }
            if(!edge(c,pc,w,dst))return control_fail(5,dst);
            caller_=active_;ret_=next_;next_=dst;entry_due_=true;return true;
        }
        if(op==19u&&xo==16u){
            if(w&1u)return control_fail(6);
            if(!taken(c,w))return true;
            if(ret_){
                if(active_!=e_.read_leaf&&active_!=e_.write_leaf&&(!e_.helper||active_!=e_.helper))return control_fail(7);
                if(c.lr!=ret_)return control_fail(8);
                if(e_.helper&&active_==e_.helper){if(!helper_abi_.restored(c)||helper_returned_)return fail(5);helper_returned_=true;}
                active_=caller_;next_=ret_;ret_=0;return true;
            }
            if(active_==e_.processor){
                if(!processor_.restored(c))return fail(5);
                active_=e_.handler;next_=e_.processor_return;outer_due_=2;return true;
            }
            if(active_!=e_.handler||!processor_returned_||!handler_.restored(c)||!finished(c,held))return fail(5);
            next_=e_.dispatcher_return;outer_due_=3;return true;
        }
        if(op==17u)return control_fail(9);
        if(op==19u&&xo==528u)return control_fail(10);
        if(op==19u&&xo==50u)return control_fail(11);
        if(op==31u&&xo==146u)return control_fail(12);
        if(op==16u&&(w&1u))return control_fail(13);
        if(op==16u||op==18u){
            const auto dst=target(pc,w);
            if(w&3u)return control_fail(14,dst);
            if(!known(c,active_,dst))return control_fail(15,dst);
            if(dst<=pc)poll_due_=true;
            if(op==18u||taken(c,w))next_=dst;
        }
        return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!common(c,held))return fail(6);
        if(outer_due_&&c.pc==next_&&c.lr==next_&&c.inst_count==last_){
            if(outer_due_==3u){
                if(!handler_.restored(c)||!finished(c,held))return fail(5);
                outer_due_=0;stage_=2;return true;
            }
            if(outer_due_==2u){if(!processor_.restored(c))return fail(5);processor_returned_=true;}
            outer_due_=0;outer_resume_=true;return true;
        }
        if(poll_due_&&c.pc==last_pc_&&c.inst_count==last_){poll_due_=false;return true;}
        return fail(6);
    }
    template<class C>std::optional<uint32_t> read(C& c,uint32_t a,bool held){
        if(!authorize(c,a,WordMmioInstruction::Kind::Read,held))return {};
        auto v=gate_.read(c,a,held);if(!v){fail(7);return {};}read_value_=*v;return v;
    }
    template<class C>bool write(C& c,uint32_t a,uint32_t v,bool held){
        if(!authorize(c,a,WordMmioInstruction::Kind::Write,held)||v!=mmio_.value)return fail(7);
        return gate_.write(c,a,v,held)||fail(7);
    }
    template<class C>bool returned(C& c,bool held)const{
        return stage_==2u&&!error_&&c.pc==e_.dispatcher_return&&c.inst_count==last_&&
               handler_.restored(c)&&finished(c,held)&&mapped(c,e_.counter)&&c.mmu.read32(e_.counter)==counter_;
    }
private:
    ReplyReturnExpectation e_;ReplyCompletionGate gate_;ReplyReturnAbi handler_,processor_,helper_abi_;
    WordMmioInstruction mmio_{};uint32_t counter_=0,active_=0,caller_=0,next_=0,ret_=0,last_pc_=0,last_owner_=0,read_value_=0;
    uint64_t last_=0;unsigned stage_=0,error_=0,visits_=0,outer_due_=0;
    bool entry_due_=false,poll_due_=false,outer_resume_=false,processor_returned_=false,used_=false,helper_returned_=false;
    unsigned control_detail_=0,control_target_=0,instruction_detail_=0,instruction_boundary_=0,instruction_owner_=0,instruction_ticks_=0;
    bool instruction_fail(unsigned d){if(!instruction_detail_)instruction_detail_=d;return fail(3);}
    unsigned owner_class(uint32_t a)const{
        return a==e_.processor?1u:a==e_.handler?2u:a==e_.read_leaf?3u:a==e_.write_leaf?4u:(e_.helper&&a==e_.helper)?5u:0u;
    }
    // Fixed categories for the already-known candidate helper roots.
    // Never publish a guest address or the original opcode.
    unsigned target_class(uint32_t a)const{
        const auto k=owner_class(a);if(k)return k;
        if(a==0x8051b060u)return 5u;
        if(a==0x8051b070u)return 6u;
        if(a==0x8051ad3cu)return 7u;
        if(a==0x80522af4u)return 8u;
        if(a==0x805228ccu)return 9u;
        if(a==0x80522294u)return 10u;
        if(a==0x8052a51cu)return 11u;
        return a?12u:0u;
    }
    bool control_fail(unsigned detail,uint32_t dst=0){
        if(!control_detail_){control_detail_=detail;control_target_=target_class(dst);}
        return fail(4);
    }
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>bool finished(C& c,bool held)const{
        return gate_.finished(c,held)&&(!e_.require_x2||gate_.x2_writes()==1u)&&(!e_.helper||helper_returned_);
    }
    template<class C>bool common(C& c,bool held)const{
        return stage_==1u&&!error_&&gate_.boundary(c,held)&&mapped(c,e_.counter)&&c.mmu.read32(e_.counter)==counter_;
    }
    bool mmio_window()const{return mmio_.targets_window(IosBus::IPC,0x40u)||mmio_.targets_window(IosBus::MIRROR,0x40u);}
    template<class C>bool authorize(C& c,uint32_t a,WordMmioInstruction::Kind kind,bool held){
        if(!common(c,held)||c.inst_count!=last_||used_||mmio_.kind!=kind||!mmio_.address(a)||
           (last_owner_!=e_.processor&&last_owner_!=e_.handler&&last_owner_!=(kind==WordMmioInstruction::Kind::Read?e_.read_leaf:e_.write_leaf)))return fail(7);
        used_=true;return true;
    }
    template<class C>static bool mapped(C& c,uint32_t a){
        return !(a&3u)&&a>=0x80000000u&&a<=0x817ffffcu&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3u);
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc)const{
        for(auto x:e_.words)if(x.owner==owner&&x.pc==pc)return mapped(c,pc)&&c.mmu.read32(pc)==x.word;
        return false;
    }
    template<class C>bool known(C& c,uint32_t owner,uint32_t pc,uint32_t w)const{
        return known(c,owner,pc)&&c.mmu.read32(pc)==w;
    }
    template<class C>bool edge(C& c,uint32_t pc,uint32_t w,uint32_t dst)const{
        return std::count_if(e_.edges.begin(),e_.edges.end(),[&](auto e){
            return e.pc==dst&&e.lr==pc+4u&&e.branch_word==w&&known(c,dst,dst,e.entry_word);
        })==1;
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
