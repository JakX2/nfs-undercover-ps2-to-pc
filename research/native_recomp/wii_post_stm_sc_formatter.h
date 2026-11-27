#pragma once
#include "wii_post_stm_sc_report_helper.h"
#include "wii_formatter_caller_integer.h"
#include <bit>
#include <optional>
namespace undercover::wii {
struct ScFormatterAccess {
    uint32_t pc,width;
    int64_t address; // caller-relative for stack sites; absolute otherwise
    bool stack,write;
    std::optional<uint32_t> expected_value{}; // independently authenticated raw load value
};
struct ScFormatterBoundary {uint32_t address=0,width=0;bool stack=false;int32_t caller_offset=0;bool instruction=false;};
struct ScFormatterControlBoundary {uint32_t destination=0,word=0,owner_size=0;};
struct ScCallerIntegerStep {
    uint32_t pc,word;
    std::span<const CallerIntegerInput> inputs;
};
struct ScCallerMixedStep {
    uint32_t pc,word;
    std::span<const CallerIntegerInput> inputs;
    uint32_t next_pc,other_pc; // other_pc==0 for register-only operations
    bool taken;
};
struct ScFormatterExpectation {
    uint32_t root,entry_lr,target,target_word,frame_size;
    std::span<const IpcDispatchWord> path;
    std::span<const ScFormatterAccess> accesses;
    std::span<const StmFinalSlot> slots;
    ScFormatterBoundary boundary{}; // optional local load that must not execute
    ScFormatterControlBoundary control{}; // optional authenticated local bctr stop
};
class ScFormatterWitness {
public:
    explicit ScFormatterWitness(ScFormatterExpectation e):e_(e){}
    unsigned stage()const{return stage_;}unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}unsigned back_polls()const{return back_polls_;}unsigned loads()const{return loads_;}unsigned stores()const{return stores_;}
    unsigned authenticated_loads()const{return authenticated_loads_;}
    uint32_t expected_sp()const{return gp_[1];}
    uint32_t linkage_word()const{
        uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|shadow_[e_.frame_size+4+i];return v;
    }
    template<class C>bool begin(C& c,bool held){
        if(stage_||error_||!held||!safe(c)||!(c.msr&0x8000u)||c.pc!=e_.root||c.lr!=e_.entry_lr||
           e_.frame_size<32u||e_.frame_size>704u||(e_.frame_size&7u)||(c.gpr[1]&7u)||
           c.gpr[1]<0x80000000u+e_.frame_size||e_.path.empty()||e_.path.size()>(local_stop()?128u:64u)||
           e_.accesses.size()>(local_stop()?24u:8u)||e_.slots.empty()||e_.slots.size()>19u||
           e_.path.front().pc!=e_.root||!word(c,e_.target,e_.target_word))return fail(1);
        frame_={c.gpr[1]-e_.frame_size,e_.frame_size+8u};
        if(!mapped(c,frame_))return fail(1);
        for(auto x:e_.path)if(x.owner!=e_.root||!word(c,x.pc,x.word)||
            std::count_if(e_.path.begin(),e_.path.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(1);
        for(auto s:e_.slots){
            const auto at=int64_t(c.gpr[1])+s.caller_offset;
            if(s.reg<14u||s.reg>32u||at<0||at>0xffffffffll||(at&3)||!frame_.contains(uint32_t(at),4u)||
               (s.reg==32u)!=(s.caller_offset==4)||uint32_t(at)==frame_.base||
               std::count_if(e_.slots.begin(),e_.slots.end(),[&](auto x){return x.reg==s.reg||x.caller_offset==s.caller_offset;})!=1)return fail(1);
        }
        if(std::count_if(e_.slots.begin(),e_.slots.end(),[](auto s){return s.reg==32u;})!=1)return fail(1);
        if(e_.control.destination){
            const auto dst=e_.control.destination,n=e_.control.owner_size;
            const auto inside=[&](uint32_t a){return !(a&3u)&&a>=e_.root&&uint64_t(a)+4u<=uint64_t(e_.root)+n;};
            if(e_.boundary.width||n<8u||n>65536u||(n&3u)||e_.target_word!=0x4e800420u||
               !inside(e_.target)||!inside(dst)||dst==e_.root||dst==e_.target||
               !word(c,dst,e_.control.word)||
               std::any_of(e_.path.begin(),e_.path.end(),[&](auto x){return !inside(x.pc)||x.pc==dst||x.pc==e_.target;}))return fail(1);
        }else if(e_.control.word||e_.control.owner_size)return fail(1);
        if(e_.boundary.instruction)return fail(1); // only via authenticated stack continuation
        if(e_.boundary.width){
            if(e_.boundary.stack||e_.boundary.caller_offset)return fail(1); // only via authenticated control continuation
            const auto form=decode_load(e_.target_word);
            const unsigned n=form.width;
            if(!n||n!=e_.boundary.width||
               e_.boundary.address%n||!mapped(c,{e_.boundary.address,n})||e_.target<e_.root||
               std::any_of(e_.path.begin(),e_.path.end(),[&](auto x){return x.pc==e_.target;}))return fail(1);
        }
        for(auto a:e_.accesses)if(!a.width||a.width>128u||(a.write&&!a.stack)||
            (a.expected_value&&(a.write||(a.width!=1u&&a.width!=2u&&a.width!=4u)))||
            std::count_if(e_.path.begin(),e_.path.end(),[&](auto x){return x.pc==a.pc;})!=1||
            std::count_if(e_.accesses.begin(),e_.accesses.end(),[&](auto x){return x.pc==a.pc;})!=1)return fail(1);
        for(unsigned i=0;i<frame_.size;++i)shadow_.push_back(c.mmu.read8(frame_.base+i));
        written_.resize(frame_.size);cpu_=&c;gp_=incoming_=c.gpr;gqr_=c.gqr;msr_=c.msr;
        cr_=pack(c);lr_=c.lr;ctr_=c.ctr;xer_=c.xer;srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(stage_!=1u||c.inst_count!=last_)return fail(2);
        if(!visits_&&!initial_poll_&&c.pc==e_.root&&common(c,held)){
            initial_poll_=true;return true;
        }
        // NWiiRecomp polls at the source PC of a local backward branch
        // after its instruction tick, but BEFORE CTR decrement or branch.
        if(!back_poll_due_||c.pc!=poll_pc_||!common(c,held,true))return fail(2);
        back_poll_due_=false;++back_polls_;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(stage_!=1u||back_poll_due_||!common(c,held)||c.pc!=pc)return fail(3);
        if(!visits_){
            if(!initial_poll_||entry_seen_||pc!=e_.root||c.inst_count-last_!=1u)return fail(3);
            entry_seen_=true;return true;
        }
        if(local_stop()||!due_||pc!=e_.target||c.inst_count!=last_||!word(c,pc,e_.target_word)||!abi(c))return fail(3);
        stage_=2;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!common(c,held)||due_||back_poll_due_||visits_>=e_.path.size()||
           c.inst_count-last_!=(visits_?1u:2u)||(!visits_&&(!initial_poll_||!entry_seen_||c.pc!=pc))||
           e_.path[visits_].pc!=pc||e_.path[visits_].word!=w||!word(c,pc,w))return fail(4);
        ++visits_;last_=c.inst_count;uint32_t next=pc+4u;
        const unsigned op=w>>26,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u,xo=(w>>1)&1023u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        const uint32_t ea=(ra?gp_[ra]:0u)+imm;
        if(op==37u&&rs==1u&&ra==1u){
            if(stores_||gp_[1]!=incoming_[1]||ea!=frame_.base||!access(pc,ea,4,true)||!store(pc,ea,4,gp_[1]))return fail(5);
            ++stores_;gp_[1]=ea;
        }else if(op==36u||op==38u||op==44u||op==47u||op==37u||op==39u||op==45u){
            const unsigned n=op==36u||op==37u||op==47u?4u:op==38u||op==39u?1u:2u,count=op==47u?32u-rs:1u;
            if(gp_[1]!=frame_.base||!access(pc,ea,n*count,true))return fail(5);
            for(unsigned i=0;i<count;++i)if(!store(pc,ea+n*i,n,gp_[rs+i]))return fail(5);
            ++stores_;
            if(op==37u||op==39u||op==45u){if(!ra||ra==1u)return fail(5);gp_[ra]=ea;}
        }else if(op==31u&&(xo==151u||xo==183u||xo==215u||xo==247u||xo==407u||xo==439u)){
            const unsigned n=xo==151u||xo==183u?4u:xo==215u||xo==247u?1u:2u;
            const uint32_t a=(ra?gp_[ra]:0u)+gp_[rb];
            if(gp_[1]!=frame_.base||!access(pc,a,n,true)||!store(pc,a,n,gp_[rs]))return fail(5);
            ++stores_;
            if(xo==183u||xo==247u||xo==439u){if(!ra||ra==1u)return fail(5);gp_[ra]=a;}
        }else if(const auto form=decode_load(w);form.width){
            const unsigned n=form.width;
            const uint32_t a=(ra?gp_[ra]:0u)+(form.indexed?gp_[rb]:imm);
            if(!access(pc,a,n,false)||!mapped(c,{a,n})||(a%n))return fail(5);
            uint32_t v=0;for(unsigned i=0;i<n;++i)v=(v<<8)|c.mmu.read8(a+i);
            const auto site=std::find_if(e_.accesses.begin(),e_.accesses.end(),[&](auto x){return x.pc==pc;});
            if(site->expected_value){
                if(v!=*site->expected_value)return fail(5);
                ++authenticated_loads_;
            }
            gp_[rs]=form.sign&&(v&0x8000u)?v|0xffff0000u:v;++loads_;
            if(form.update)gp_[ra]=a;
        }else if(op==31u&&xo==339u&&!(w&1u)&&(ra|(rb<<5))==8u&&rs!=1u)gp_[rs]=lr_;
        else if(op==31u&&xo==467u&&!(w&1u)&&(ra|(rb<<5))==9u)ctr_=gp_[rs];
        else if(op==31u&&xo==467u&&!(w&1u)&&(ra|(rb<<5))==8u)lr_=gp_[rs];
        else if(op==14u&&rs==1u&&ra==1u){
            // The one authorized epilogue instruction releases precisely
            // this child frame, after all return ABI identities are proven.
            if(!release_authorized_||frame_released_||imm!=e_.frame_size||
               gp_[1]!=frame_.base||ea!=incoming_[1]||visits_!=e_.path.size()||
               lr_!=e_.entry_lr)return fail(6);
            gp_[1]=ea;frame_released_=true;release_authorized_=false;
        }else if((op==14u||op==15u)&&rs!=1u)gp_[rs]=(ra?gp_[ra]:0u)+(op==15u?imm<<16u:imm);
        else if(op==10u||op==11u){
            if(w&0x00200000u)return fail(6);
            const uint32_t a=gp_[ra],b=op==10u?w&0xffffu:imm;
            compare((w>>23)&7u,op==10u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
        }else if(op==31u&&(xo==0u||xo==32u)){
            if(w&0x00200000u)return fail(6);
            const uint32_t a=gp_[ra],b=gp_[rb];
            compare((w>>23)&7u,xo==32u?a<b:std::bit_cast<int32_t>(a)<std::bit_cast<int32_t>(b),a==b);
        }else if(op==31u&&xo==444u&&rs==rb&&ra!=1u){
            gp_[ra]=gp_[rs];if(w&1u)record(gp_[ra]);
        }else if(op==31u&&(xo==922u||xo==954u)&&ra!=1u){
            const uint32_t m=xo==922u?0xffffu:0xffu,s=xo==922u?0x8000u:0x80u;
            gp_[ra]=((gp_[rs]&m)^s)-s;if(w&1u)record(gp_[ra]);
        }else if((op==20u||op==21u||op==23u)&&ra!=1u){
            const unsigned sh=op==23u?gp_[rb]&31u:rb,mb=(w>>6)&31u,me=(w>>1)&31u;
            const uint32_t m=mask(mb,me),v=std::rotl(gp_[rs],int(sh))&m;
            gp_[ra]=op==20u?(gp_[ra]&~m)|v:v;if(w&1u)record(gp_[ra]);
        }else if(op>=24u&&op<=29u&&ra!=1u){
            const uint32_t n=(w&0xffffu)<<((op&1u)?16u:0u);
            gp_[ra]=op<26u?gp_[rs]|n:op<28u?gp_[rs]^n:gp_[rs]&n;if(op>=28u)record(gp_[ra]);
        }else if(op==31u&&(xo==266u||xo==40u)&&rs!=1u){
            gp_[rs]=xo==266u?gp_[ra]+gp_[rb]:gp_[rb]-gp_[ra];if(w&1u)record(gp_[rs]);
        }else if(op==18u&&(w&3u)==1u){
            if(local_stop()||visits_!=e_.path.size()||target(pc,w)!=e_.target||!abi(c))return fail(6);
            lr_=pc+4u;due_=true;return true;
        }else if(op==16u||op==18u){
            if(w&3u)return fail(6);
            const auto dst=target(pc,w);
            if(dst>=e_.root&&dst<=pc){
                back_poll_due_=true;poll_pc_=pc;poll_ctr_=ctr_;
            }
            const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;bool ct=true;
            if(op==16u&&!(bo&4u)){--ctr_;ct=bool(ctr_)!=bool(bo&2u);}
            if(op==18u||(ct&&((bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u))))next=target(pc,w);
        }else return fail(6);
        if(visits_==e_.path.size()&&local_stop()){
            if(next!=e_.target)return fail(6);
            boundary_due_=true;return true;
        }
        if(visits_>=e_.path.size()||e_.path[visits_].pc!=next)return fail(6);
        return true;
    }
    // The instrumented label ticks, then stops before the native load body.
    // Unlike a direct call entry, ctx.pc need not track every local label.
    template<class C>bool stop_before_load(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!e_.boundary.width||!boundary_due_||back_poll_due_||due_||
           visits_!=e_.path.size()||pc!=e_.target||w!=e_.target_word||
           c.inst_count-last_!=1u||!common(c,held)||!word(c,pc,w)||!abi(c))return fail(6);
        const auto form=decode_load(w);
        const unsigned ra=(w>>16)&31u,rb=(w>>11)&31u;
        const uint32_t imm=uint32_t(int32_t((w&0xffffu)^0x8000u)-0x8000);
        const uint32_t address=e_.boundary.stack?uint32_t(int64_t(incoming_[1])+e_.boundary.caller_offset):e_.boundary.address;
        if(!form.width||form.width!=e_.boundary.width||
           (ra?gp_[ra]:0u)+(form.indexed?gp_[rb]:imm)!=address||
           !mapped(c,{address,e_.boundary.width}))return fail(6);
        last_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool reached_load_boundary(C& c,bool held)const{
        return stage_==2u&&e_.boundary.width&&boundary_due_&&!due_&&!back_poll_due_&&common(c,held)&&
            c.inst_count==last_&&abi(c)&&word(c,e_.target,e_.target_word);
    }
    // Report only which bytes were written by the witnessed instructions.
    // The initial frame snapshot is not original-value provenance. No guest
    // byte is modified or exposed, and the unresolved load remains stopped.
    template<class C>std::optional<uint32_t> stack_boundary_written_mask(C& c,bool held)const{
        if(!e_.boundary.stack||e_.boundary.width!=4u||!reached_load_boundary(c,held))return {};
        const auto a=uint32_t(int64_t(incoming_[1])+e_.boundary.caller_offset);
        if(!frame_.contains(a,4u))return {};
        uint32_t mask=0;
        for(unsigned i=0;i<4u;++i)if(written_[a-frame_.base+i])mask|=0xffu<<(24u-8u*i);
        return mask;
    }
    // Stop at the instrumented bctr label before executing its native body.
    template<class C>bool stop_before_control(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!e_.control.destination||!boundary_due_||back_poll_due_||due_||
           visits_!=e_.path.size()||pc!=e_.target||w!=0x4e800420u||w!=e_.target_word||
           c.inst_count-last_!=1u||!common(c,held)||!word(c,pc,w)||!abi(c)||
           ctr_!=e_.control.destination||!word(c,e_.control.destination,e_.control.word))return fail(6);
        last_=c.inst_count;stage_=2;return true;
    }
    template<class C>bool reached_control_boundary(C& c,bool held)const{
        return stage_==2u&&e_.control.destination&&boundary_due_&&!due_&&!back_poll_due_&&
            common(c,held)&&c.inst_count==last_&&abi(c)&&ctr_==e_.control.destination&&
            word(c,e_.target,e_.target_word)&&word(c,e_.control.destination,e_.control.word);
    }
    // Optional continuation of the verified pre-transfer stop. The native
    // bctr body must perform the PC change; these observers never set it.
    // The pinned run_game polls before its dispatcher tick, then the
    // translated interior label ticks once before executing its body.
    template<class C>bool control_transfer_poll(C& c,bool held){
        if(!reached_control_boundary(c,held)||c.pc!=e_.control.destination)return fail(6);
        stage_=3u;return true;
    }
    template<class C>bool control_destination_entry(C& c,uint32_t pc,bool held){
        if(stage_!=3u||pc!=e_.control.destination||c.pc!=pc||
           c.inst_count-last_!=1u||!control_storage(c,held))return fail(6);
        stage_=4u;return true;
    }
    // Continue the same shadow after the authenticated dispatcher entry.
    // The full new contract must retain every already executed row/access
    // and contain the exact original bctr followed by its destination.
    template<class C>bool resume_control_path(C& c,ScFormatterExpectation next,bool held){
        if(stage_!=4u||c.pc!=e_.control.destination||c.inst_count-last_!=1u||
           !control_storage(c,held)||next.root!=e_.root||next.entry_lr!=e_.entry_lr||
           next.frame_size!=e_.frame_size||next.control.destination||next.control.word||next.control.owner_size||
           !next.boundary.stack||next.boundary.instruction||next.boundary.address||next.boundary.width!=4u||
           next.boundary.caller_offset%4||next.boundary.caller_offset<4-int64_t(e_.frame_size)||
           next.boundary.caller_offset>-4||decode_load(next.target_word).width!=4u||
           next.path.size()<e_.path.size()+2u||next.path.size()>128u||
           next.accesses.size()<e_.accesses.size()||next.accesses.size()>24u||
           next.slots.size()!=e_.slots.size()||!word(c,next.target,next.target_word))return fail(6);
        const auto i=e_.path.size();
        if(next.path[i].pc!=e_.target||next.path[i].word!=e_.target_word||
           next.path[i+1].pc!=e_.control.destination||next.path[i+1].word!=e_.control.word)return fail(6);
        const auto inside=[&](uint32_t a){return !(a&3u)&&a>=e_.root&&uint64_t(a)+4u<=uint64_t(e_.root)+e_.control.owner_size;};
        if(!inside(next.target))return fail(6);
        for(unsigned j=0;j<next.path.size();++j){
            const auto x=next.path[j];
            if(x.owner!=e_.root||!inside(x.pc)||x.pc==next.target||!word(c,x.pc,x.word)||
               std::count_if(next.path.begin(),next.path.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(6);
            if(j<i&&(x.pc!=e_.path[j].pc||x.word!=e_.path[j].word))return fail(6);
        }
        for(unsigned j=0;j<next.slots.size();++j)if(next.slots[j].reg!=e_.slots[j].reg||
            next.slots[j].caller_offset!=e_.slots[j].caller_offset)return fail(6);
        for(unsigned j=0;j<next.accesses.size();++j){
            const auto x=next.accesses[j];
            if(j<e_.accesses.size()){
                const auto y=e_.accesses[j];
                if(x.pc!=y.pc||x.width!=y.width||x.address!=y.address||x.stack!=y.stack||x.write!=y.write||x.expected_value!=y.expected_value)return fail(6);
            }else if(x.write||(x.width!=1u&&x.width!=2u&&x.width!=4u)||
                (!x.stack&&!x.expected_value)||
                std::none_of(next.path.begin()+i+1,next.path.end(),[&](auto y){return x.pc==y.pc;}))return fail(6);
            if(std::count_if(next.accesses.begin(),next.accesses.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(6);
        }
        // The native branch has already completed and the outer dispatcher
        // tick is observed. No CPU or guest memory state is changed here.
        owner_size_=e_.control.owner_size;e_=next;++visits_;last_=c.inst_count;boundary_due_=false;stage_=1u;return true;
    }
    // Continue at the already-ticked, verified partial load. The caller
    // shadow is owned by the original parent witness, not a new guest seed.
    // Unknown initial bytes remain conditional live observations.
    template<class C>bool resume_stack_path(C& c,ScFormatterExpectation next,
            const ScFormatterWitness& parent,uint32_t written_mask,bool held){
        if(!reached_load_boundary(c,held)||!e_.boundary.stack||!owner_size_||caller_parent_||
           stack_boundary_written_mask(c,held)!=written_mask||std::popcount(written_mask)!=16||
           next.root!=e_.root||next.entry_lr!=e_.entry_lr||next.frame_size!=e_.frame_size||
           next.control.destination||next.control.word||next.control.owner_size||
           !next.boundary.instruction||next.boundary.width||next.boundary.address||next.boundary.stack||next.boundary.caller_offset||
           next.path.size()<=e_.path.size()||next.path.size()>128u||
           next.accesses.size()<=e_.accesses.size()||next.accesses.size()>32u||
           next.slots.size()!=e_.slots.size()||!word(c,next.target,next.target_word)||
           !parent.child_frame_held(c,held,frame_.base,linkage_word())||
           parent.frame_.base!=incoming_[1]||parent.cpu_!=cpu_||parent.e_.frame_size!=704u)return fail(6);
        const auto i=e_.path.size(),j=e_.accesses.size();
        const auto inside=[&](uint32_t a){return !(a&3u)&&a>=e_.root&&uint64_t(a)+4u<=uint64_t(e_.root)+owner_size_;};
        if(!inside(next.target)||next.path[i].pc!=e_.target||next.path[i].word!=e_.target_word)return fail(6);
        for(unsigned k=0;k<next.path.size();++k){
            const auto x=next.path[k];
            if(x.owner!=e_.root||!inside(x.pc)||x.pc==next.target||!word(c,x.pc,x.word)||
               std::count_if(next.path.begin(),next.path.end(),[&](auto y){return x.pc==y.pc;})!=1||
               (k<i&&(x.pc!=e_.path[k].pc||x.word!=e_.path[k].word)))return fail(6);
        }
        for(unsigned k=0;k<next.slots.size();++k)if(next.slots[k].reg!=e_.slots[k].reg||
            next.slots[k].caller_offset!=e_.slots[k].caller_offset)return fail(6);
        std::vector<ScFormatterAccess> permitted;
        // Preflight new access rows in execution order. A later stack load
        // must read bytes already covered by the observed child/parent
        // writes or the exact conditional word admitted at this boundary.
        // Never mistake arbitrary initial frame contents for provenance.
        auto child_readable=written_,parent_readable=parent.written_;
        auto prev_path=next.path.begin()+i;
        const auto partial=next.accesses[j];
        if(partial.pc!=e_.target||partial.width!=4u||partial.address!=e_.boundary.caller_offset||
           !partial.stack||partial.write||partial.expected_value)return fail(6);
        for(unsigned k=0;k<next.accesses.size();++k){
            const auto x=next.accesses[k];
            if(k<j){
                const auto y=e_.accesses[k];
                if(x.pc!=y.pc||x.width!=y.width||x.address!=y.address||x.stack!=y.stack||x.write!=y.write||x.expected_value!=y.expected_value)return fail(6);
            }else{
                if((x.width!=1u&&x.width!=2u&&x.width!=4u)||
                   std::none_of(next.path.begin()+i,next.path.end(),[&](auto y){return x.pc==y.pc;})||
                   (!x.stack&&(!x.expected_value||x.write))||(x.stack&&x.expected_value))return fail(6);
                const auto row=std::find_if(next.path.begin()+i,next.path.end(),[&](auto y){return x.pc==y.pc;});
                if(row==next.path.end()||(k==j?row!=prev_path:row<=prev_path))return fail(6);
                prev_path=row;
                if(x.stack&&!x.write){
                    const auto off=x.address;
                    if(off%x.width)return fail(6);
                    if(off>=-int64_t(e_.frame_size)&&off<=8-int64_t(x.width)){
                        const auto a=unsigned(off+e_.frame_size);
                        if(k==j){for(unsigned q=0;q<x.width;++q)child_readable[a+q]=1;}
                        else for(unsigned q=0;q<x.width;++q)if(!child_readable[a+q])return fail(6);
                    }else if(off>=8&&off<=int64_t(parent.e_.frame_size)-x.width){
                        for(unsigned q=0;q<x.width;++q)if(!parent_readable[unsigned(off)+q])return fail(6);
                    }else return fail(6);
                }
                if(x.write){
                    // Every new store must target a distinct unused byte
                    // range within the parent's real frame, never linkage,
                    // backchain, saved registers or inherited writes.
                    if(x.address<8||x.address>int64_t(parent.e_.frame_size)-x.width||x.address%x.width||
                       permitted.size()>=8u)return fail(6);
                    for(unsigned q=0;q<x.width;++q)if(parent.written_[unsigned(x.address)+q])return fail(6);
                    for(auto y:permitted)if(x.address<y.address+y.width&&y.address<x.address+x.width)return fail(6);
                    for(unsigned q=0;q<x.width;++q)parent_readable[unsigned(x.address)+q]=1;
                    permitted.push_back(x);
                }
            }
            if(std::count_if(next.accesses.begin(),next.accesses.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(6);
        }
        if(permitted.empty()||!last_)return fail(6);
        caller_parent_=&parent;caller_stores_=std::move(permitted);
        caller_expected_=parent.shadow_;caller_written_.resize(parent.shadow_.size());
        // The boundary hook already counted its native label tick, but
        // the load body has not run. Reuse that tick in before(), not a
        // second guest tick. No register or guest memory is modified.
        const auto pc=e_.target,w=e_.target_word;
        conditional_offset_=e_.boundary.caller_offset;
        e_=next;boundary_due_=false;stage_=1u;--last_;
        return before(c,pc,w,held);
    }
    // A later original instruction boundary keeps the exact same CPU,
    // caller overlay and access history. This read-only extension is
    // deliberately narrower than resume_stack_path: no fresh writes or
    // additional conditional bytes are authorized here.
    template<class C>bool resume_instruction_path(C& c,ScFormatterExpectation next,bool held){
        if(!reached_instruction_boundary(c,held)||frame_released_||!caller_parent_||!conditional_offset_||!owner_size_||!last_||
           !caller_parent_->child_frame_held_with_stores(c,held,*this)||
           next.root!=e_.root||next.entry_lr!=e_.entry_lr||next.frame_size!=e_.frame_size||
           next.control.destination||next.control.word||next.control.owner_size||
           !next.boundary.instruction||next.boundary.width||next.boundary.address||next.boundary.stack||next.boundary.caller_offset||
           next.path.size()<=e_.path.size()||next.path.size()>128u||
           next.accesses.size()<e_.accesses.size()||next.accesses.size()>64u||
           next.slots.size()!=e_.slots.size()||!word(c,next.target,next.target_word))return fail(6);
        const auto i=e_.path.size(),j=e_.accesses.size();
        const auto inside=[&](uint32_t a){return !(a&3u)&&a>=e_.root&&uint64_t(a)+4u<=uint64_t(e_.root)+owner_size_;};
        if(!inside(next.target)||next.path[i].pc!=e_.target||next.path[i].word!=e_.target_word)return fail(6);
        for(unsigned k=0;k<next.path.size();++k){
            const auto x=next.path[k];
            if(x.owner!=e_.root||!inside(x.pc)||x.pc==next.target||!word(c,x.pc,x.word)||
               std::count_if(next.path.begin(),next.path.end(),[&](auto y){return x.pc==y.pc;})!=1||
               (k<i&&(x.pc!=e_.path[k].pc||x.word!=e_.path[k].word)))return fail(6);
        }
        for(unsigned k=0;k<next.slots.size();++k)if(next.slots[k].reg!=e_.slots[k].reg||
            next.slots[k].caller_offset!=e_.slots[k].caller_offset)return fail(6);
        auto prev=next.path.begin()+i;
        for(unsigned k=0;k<next.accesses.size();++k){
            const auto x=next.accesses[k];
            if(k<j){
                const auto y=e_.accesses[k];
                if(x.pc!=y.pc||x.width!=y.width||x.address!=y.address||x.stack!=y.stack||x.write!=y.write||x.expected_value!=y.expected_value)return fail(6);
            }else{
                if(x.write||(x.width!=1u&&x.width!=2u&&x.width!=4u)||(x.stack==x.expected_value.has_value()))return fail(6);
                const auto row=std::find_if(next.path.begin()+i,next.path.end(),[&](auto y){return x.pc==y.pc;});
                if(row==next.path.end()||row<prev||decode_load(row->word).width!=x.width)return fail(6);
                prev=row+1;
                if(x.stack){
                    const auto off=x.address;
                    if(off%x.width)return fail(6);
                    if(off>=-int64_t(e_.frame_size)&&off<=8-int64_t(x.width)){
                        for(unsigned q=0;q<x.width;++q){
                            const auto byte=off+q;
                            if(!written_[unsigned(byte+e_.frame_size)]&&
                               (byte<*conditional_offset_||byte>=int64_t(*conditional_offset_)+4))return fail(6);
                        }
                    }else if(off>=8&&off<=int64_t(caller_parent_->e_.frame_size)-x.width){
                        for(unsigned q=0;q<x.width;++q){
                            const auto byte=unsigned(off)+q;
                            if(!caller_written_[byte]&&!caller_parent_->written_[byte])return fail(6);
                        }
                    }else return fail(6);
                }else if(x.address<0x80000000ll||x.address>0x81800000ll-x.width||x.address%x.width||
                         !mapped(c,{uint32_t(x.address),x.width}))return fail(6);
            }
            if(std::count_if(next.accesses.begin(),next.accesses.end(),[&](auto y){return x.pc==y.pc;})!=1)return fail(6);
        }
        const auto pc=e_.target,w=e_.target_word;
        e_=next;boundary_due_=false;stage_=1u;--last_;
        return before(c,pc,w,held);
    }
    // Authenticate a single frame-release instruction and stop before
    // the original unconditional return. Neither SP nor LR is assigned
    // by this observer to the actual CPU.
    template<class C>bool resume_frame_release(C& c,ScFormatterExpectation next,bool held){
        if(!reached_instruction_boundary(c,held)||frame_released_||release_authorized_||
           !caller_parent_||e_.target_word!=(0x38210000u|e_.frame_size)||
           next.path.size()!=e_.path.size()+1u||next.accesses.size()!=e_.accesses.size()||
           next.target!=e_.target+4u||next.target_word!=0x4e800020u||
           gp_[1]!=frame_.base||lr_!=e_.entry_lr||!return_registers_held())return fail(6);
        release_authorized_=true;
        return resume_instruction_path(c,next,held);
    }
    bool frame_released()const{return frame_released_;}
    // The local blr label has already ticked. Arm only the exact original
    // return, and require the unchanged native body to reach the guard
    // at the caller's dispatcher poll. No guest PC is assigned here.
    template<class C>bool arm_native_return(C& c,uint32_t caller,uint32_t guard_word,bool held){
        if(!reached_instruction_boundary(c,held)||!frame_released_||!caller_parent_||
           e_.target_word!=0x4e800020u||caller!=e_.entry_lr||lr_!=caller||
           (caller&3u)||guard_word!=0x44000002u||!word(c,caller,guard_word)||
           caller==e_.target||!return_registers_held()||
           !caller_parent_->child_frame_held_with_stores(c,held,*this))return fail(6);
        return_pc_=caller;return_word_=guard_word;stage_=6u;return true;
    }
    // A distinct future checkpoint may replace the synthetic caller guard
    // with an authenticated original label. Verify the original direct
    // call edge as well as both current code words; never synthesize PC.
    template<class C>bool arm_caller_arrival(C& c,uint32_t owner,uint32_t caller,uint32_t caller_word,
                                             uint32_t call_word,bool held){
        if(!reached_instruction_boundary(c,held)||!frame_released_||!caller_parent_||
           e_.target_word!=0x4e800020u||caller!=e_.entry_lr||lr_!=caller||
           owner!=caller_parent_->e_.root||(owner&3u)||(caller&3u)||caller<=owner||
           uint64_t(caller)-owner>65536u||caller==e_.target||caller_word==0x44000002u||
           call_word>>26!=18u||(call_word&3u)!=1u||target(caller-4u,call_word)!=e_.root||
           !word(c,caller-4u,call_word)||!word(c,caller,caller_word)||
           !return_registers_held()||!caller_parent_->child_frame_held_with_stores(c,held,*this))return fail(6);
        return_pc_=caller;return_word_=caller_word;caller_arrival_=true;stage_=6u;return true;
    }
    template<class C>bool native_return_poll(C& c,bool held){
        if(stage_!=6u||!return_storage(c,held))return fail(6);
        ++visits_;stage_=7u;return true;
    }
    template<class C>bool reached_native_return(C& c,bool held)const{
        return stage_==7u&&return_storage(c,held)&&visits_==e_.path.size()+1u;
    }
    // The pinned dispatcher increments once before entering the caller.
    // The original local label then increments once before its body.
    // These are boundary ticks, not additional completed guest visits.
    template<class C>bool caller_arrival_entry(C& c,uint32_t pc,bool held){
        if(stage_!=7u||!caller_arrival_||pc!=return_pc_||!return_storage(c,held,1u))return fail(6);
        stage_=8u;return true;
    }
    template<class C>bool stop_before_caller_instruction(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=8u||!caller_arrival_||pc!=return_pc_||w!=return_word_||!return_storage(c,held,2u))return fail(6);
        stage_=9u;return true;
    }
    template<class C>bool reached_caller_arrival(C& c,bool held)const{
        return stage_==9u&&caller_arrival_&&return_storage(c,held,2u)&&visits_==e_.path.size()+1u;
    }
    // Execute only a single non-updating byte load from a proven child
    // output byte in the still-live parent frame. Keep the nested census
    // separate; the caller's load is counted only after its native body.
    template<class C>bool resume_caller_byte(C& c,int32_t offset,uint8_t expected,
                                            uint32_t next_pc,uint32_t next_word,bool held){
        if(!reached_caller_arrival(c,held)||!caller_parent_||offset<8||
           uint32_t(offset)>=caller_parent_->e_.frame_size||
           next_pc!=return_pc_+4u||next_word==0x44000002u||!word(c,next_pc,next_word)||
           !caller_written_[unsigned(offset)]||caller_expected_[unsigned(offset)]!=expected)return fail(6);
        const auto form=decode_load(return_word_);
        const unsigned rt=(return_word_>>21)&31u,ra=(return_word_>>16)&31u,rb=(return_word_>>11)&31u;
        const uint32_t imm=uint32_t(int32_t((return_word_&0xffffu)^0x8000u)-0x8000);
        const uint32_t a=(ra?gp_[ra]:0u)+(form.indexed?gp_[rb]:imm);
        if(form.width!=1u||form.update||form.sign||(rt!=0u&&(rt<3u||rt>12u))||
           a!=incoming_[1]+uint32_t(offset)||!mapped(c,{a,1u})||c.mmu.read8(a)!=expected)return fail(6);
        gp_[rt]=expected;caller_next_pc_=next_pc;caller_next_word_=next_word;stage_=10u;
        return true;
    }
    template<class C>bool stop_after_caller_byte(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=10u||pc!=caller_next_pc_||w!=caller_next_word_||
           !word(c,pc,w)||!return_storage(c,held,3u))return fail(6);
        stage_=11u;return true;
    }
    template<class C>bool reached_caller_byte(C& c,bool held)const{
        return stage_==11u&&word(c,caller_next_pc_,caller_next_word_)&&
            return_storage(c,held,3u)&&visits_==e_.path.size()+1u;
    }
    // A bounded straight-line register-only continuation. Each predicted
    // effect must be observed at the next original label before counting it.
    // The parent frame, child output overlay and restored ABI stay live.
    template<class C>bool resume_caller_integers(C& c,std::span<const ScCallerIntegerStep> path,
                                                 uint32_t end_pc,uint32_t end_word,bool held){
        if(!reached_caller_byte(c,held)||path.empty()||path.size()>8u||
           path.front().pc!=caller_next_pc_||path.front().word!=caller_next_word_||
           uint64_t(caller_next_pc_)+4u*path.size()!=end_pc||end_word==0x44000002u||
           !word(c,end_pc,end_word))return fail(6);
        for(unsigned i=0;i<path.size();++i)
            if(path[i].pc!=caller_next_pc_+4u*i||path[i].word==0x44000002u||
               path[i].inputs.size()>3u||!word(c,path[i].pc,path[i].word))return fail(6);
        integer_path_=path;integer_end_pc_=end_pc;integer_end_word_=end_word;
        if(!predict_integer(c,path.front()))return fail(6);
        stage_=12u;return true;
    }
    template<class C>bool caller_integer_boundary(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=12u||integer_completed_>=integer_path_.size()||
           !return_storage(c,held,4u+integer_completed_)||!integer_code(c))return fail(6);
        const auto i=integer_completed_+1u;
        const bool done=i==integer_path_.size();
        if(pc!=(done?integer_end_pc_:integer_path_[i].pc)||
           w!=(done?integer_end_word_:integer_path_[i].word))return fail(6);
        ++integer_completed_;
        if(done){stage_=13u;return true;}
        if(!predict_integer(c,integer_path_[i]))return fail(6);
        return true;
    }
    unsigned caller_integer_visits()const{return integer_completed_;}
    template<class C>bool reached_caller_integers(C& c,bool held)const{
        return stage_==13u&&!integer_path_.empty()&&integer_completed_==integer_path_.size()&&
            integer_code(c)&&return_storage(c,held,3u+integer_completed_)&&visits_==e_.path.size()+1u;
    }
    // A forward local branch can be admitted only after the actual
    // integer effects are observed. CR is already independently predicted.
    // No CTR update, link, absolute transfer, or backward poll is allowed.
    template<class C>bool resume_caller_branch(C& c,uint32_t owner_size,bool taken,
                                                uint32_t next_pc,uint32_t next_word,bool held){
        const bool first=reached_caller_integers(c,held);
        const bool after_post=branch_completed_==2u&&reached_caller_post_integers(c,held);
        const bool consecutive=(branch_completed_==1u||branch_completed_==3u)&&reached_caller_branch(c,held);
        if((!first&&!consecutive&&!after_post)||branch_completed_>=branches_.size()||
           !caller_parent_||owner_size<8u||owner_size>65536u||(owner_size&3u)||
           next_word==0x44000002u||!word(c,next_pc,next_word))return branch_reject(1);
        const auto owner=caller_parent_->e_.root;
        const auto pc=first?integer_end_pc_:after_post?post_integer_end_pc_:branches_[branch_completed_-1].next_pc;
        const auto w=first?integer_end_word_:after_post?post_integer_end_word_:branches_[branch_completed_-1].next_word;
        if(w&3u||(!first&&owner_size!=branch_owner_size_))return branch_reject(2);
        const auto inside=[&](uint32_t a){return !(a&3u)&&a>=owner&&uint64_t(a)+4u<=uint64_t(owner)+owner_size;};
        if(!inside(pc)||!inside(next_pc))return branch_reject(3);
        const unsigned op=w>>26,bo=(w>>21)&31u,bi=(w>>16)&31u;
        if(op!=16u&&op!=18u)return branch_reject(4);
        const auto dst=target(pc,w);
        if(!inside(dst)||dst<=pc+4u)return branch_reject(5);
        if(op==16u&&!(bo&4u))return branch_reject(6);
        const bool outcome=op==18u||(bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u);
        if(outcome!=taken||next_pc!=(outcome?dst:pc+4u))return branch_reject(7);
        // Keep the untaken edge guarded. For a direct branch, the skipped
        // fallthrough is guarded too, although the emitter never takes it.
        const auto other=outcome?pc+4u:dst;
        if(!inside(other)||!word(c,other,0x44000002u))return branch_reject(8);
        // A later selected edge may not overwrite an earlier guard.
        for(unsigned i=0;i<branch_completed_;++i)
            if(next_pc==branches_[i].other_pc)return branch_reject(9);
        branch_owner_size_=owner_size;
        branches_[branch_completed_]={pc,w,next_pc,next_word,other};
        stage_=14u;return true;
    }
    template<class C>bool stop_after_caller_branch(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=14u||branch_completed_>=branches_.size())return branch_reject(10);
        if(pc!=branches_[branch_completed_].next_pc)return branch_reject(11);
        if(w!=branches_[branch_completed_].next_word)return branch_reject(12);
        if(!held)return branch_reject(13);
        if(branch_completed_>=2u&&!post_integer_code(c))return branch_reject(14);
        const uint64_t delta=3u+integer_completed_+branch_completed_+1u+
            (branch_completed_>=2u?post_integer_completed_:0u);
        if(!branch_storage(c,held,branch_completed_+1u,branch_completed_>=2u?post_integer_completed_:0u)){
            if(c.inst_count<last_||c.inst_count-last_!=delta)return branch_reject(15);
            if(c.pc!=return_pc_)return branch_reject(16);
            if(!common(c,held))return branch_reject(17);
            if(!abi(c))return branch_reject(18);
            if(!caller_parent_||!caller_parent_->child_frame_held_with_stores(c,held,*this))return branch_reject(19);
            return branch_reject(20);
        }
        ++branch_completed_;stage_=15u;return true;
    }
    unsigned caller_branch_visits()const{return branch_completed_;}
    unsigned branch_refusal_detail()const{return branch_detail_;}
    template<class C>bool reached_caller_branch(C& c,bool held)const{
        return stage_==15u&&branch_completed_&&
            branch_storage(c,held,branch_completed_,branch_completed_>=3u?post_integer_completed_:0u)&&
            (branch_completed_<3u||post_integer_code(c))&&visits_==e_.path.size()+1u;
    }
    // A second register-only block begins at the selected branch label.
    // Preserve the first block and both edge proofs throughout this stage.
    template<class C>bool resume_caller_post_integers(C& c,std::span<const ScCallerIntegerStep> path,
                                                      uint32_t end_pc,uint32_t end_word,bool held){
        if(!reached_caller_branch(c,held)||branch_completed_!=2u||path.empty()||path.size()>8u||
           path.front().pc!=branches_[1].next_pc||path.front().word!=branches_[1].next_word||
           uint64_t(path.front().pc)+4u*path.size()!=end_pc||end_word==0x44000002u||
           !word(c,end_pc,end_word))return fail(6);
        const auto owner=caller_parent_->e_.root;
        if(end_pc<owner||uint64_t(end_pc)+4u>uint64_t(owner)+branch_owner_size_)return fail(6);
        for(unsigned i=0;i<path.size();++i)
            if(path[i].pc!=path.front().pc+4u*i||path[i].word==0x44000002u||
               path[i].inputs.size()>3u||!word(c,path[i].pc,path[i].word))return fail(6);
        for(unsigned i=0;i<branch_completed_;++i)
            if(branches_[i].other_pc>=path.front().pc&&branches_[i].other_pc<=end_pc)return fail(6);
        post_integer_path_=path;post_integer_end_pc_=end_pc;post_integer_end_word_=end_word;
        if(!predict_integer(c,path.front()))return fail(6);
        stage_=16u;return true;
    }
    template<class C>bool caller_post_integer_boundary(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=16u||post_integer_completed_>=post_integer_path_.size()||
           !post_integer_storage(c,held,post_integer_completed_+1u))return fail(6);
        const auto i=post_integer_completed_+1u;
        const bool done=i==post_integer_path_.size();
        if(pc!=(done?post_integer_end_pc_:post_integer_path_[i].pc)||
           w!=(done?post_integer_end_word_:post_integer_path_[i].word))return fail(6);
        ++post_integer_completed_;
        if(done){
            // Freeze the proven 104-instruction checkpoint's parent-frame
            // age. Only the exact subsequent witnessed caller instruction
            // budget may extend this baseline; no unbounded age relaxation.
            if(frame_released_&&caller_parent_&&integer_completed_==2u&&
               branch_completed_==2u&&post_integer_completed_==1u){
                const auto age=caller_parent_->frame_age(c);
                if(age>128u)return fail(6);
                parent_checkpoint_age_=age;parent_checkpoint_valid_=true;
            }
            stage_=17u;return true;
        }
        if(!predict_integer(c,post_integer_path_[i]))return fail(6);
        return true;
    }
    unsigned caller_post_integer_visits()const{return post_integer_completed_;}
    template<class C>bool reached_caller_post_integers(C& c,bool held)const{
        return stage_==17u&&!post_integer_path_.empty()&&post_integer_completed_==post_integer_path_.size()&&
            post_integer_storage(c,held,post_integer_completed_)&&visits_==e_.path.size()+1u;
    }
    // Authenticate a bounded mixed continuation with one observer per
    // original label. No live register, CR or guest PC is assigned here.
    template<class C>bool resume_caller_mixed(C& c,std::span<const ScCallerMixedStep> path,
                                              uint32_t end_pc,uint32_t end_word,bool held){
        if(!reached_caller_branch(c,held)||branch_completed_!=4u||path.empty()||path.size()>16u||
           path.front().pc!=branches_[3].next_pc||path.front().word!=branches_[3].next_word||
           end_word==0x44000002u||!word(c,end_pc,end_word))return fail(6);
        const auto owner=caller_parent_->e_.root;
        const auto inside=[&](uint32_t a){return !(a&3u)&&a>=owner&&uint64_t(a)+4u<=uint64_t(owner)+branch_owner_size_;};
        if(!inside(end_pc))return fail(6);
        for(unsigned i=0;i<path.size();++i){
            const auto& s=path[i];
            if(!inside(s.pc)||!inside(s.next_pc)||s.next_pc<=s.pc||
               s.next_pc!=(i+1u==path.size()?end_pc:path[i+1u].pc)||
               s.word==0x44000002u||s.inputs.size()>3u||!word(c,s.pc,s.word))return fail(6);
            for(unsigned j=0;j<branch_completed_;++j)
                if(s.pc==branches_[j].other_pc||s.next_pc==branches_[j].other_pc)return fail(6);
            for(auto t:path)if(t.other_pc&&(s.pc==t.other_pc||s.next_pc==t.other_pc))return fail(6);
            if(s.other_pc){
                if(!inside(s.other_pc)||s.other_pc==s.next_pc||!s.inputs.empty()||
                   !word(c,s.other_pc,0x44000002u)||!mixed_edge(s,false))return fail(6);
            }else if(s.taken||uint64_t(s.pc)+4u!=s.next_pc)return fail(6);
        }
        mixed_path_=path;mixed_end_pc_=end_pc;mixed_end_word_=end_word;
        if(!predict_mixed(c,path.front()))return fail(6);
        stage_=18u;return true;
    }
    template<class C>bool caller_mixed_boundary(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=18u||mixed_completed_>=mixed_path_.size()||!mixed_storage(c,held,mixed_completed_+1u))return fail(6);
        const unsigned i=mixed_completed_+1u;const bool done=i==mixed_path_.size();
        if(pc!=(done?mixed_end_pc_:mixed_path_[i].pc)||w!=(done?mixed_end_word_:mixed_path_[i].word))return fail(6);
        if(mixed_path_[mixed_completed_].other_pc){
            if(mixed_path_[mixed_completed_].taken)++mixed_taken_;else ++mixed_fallthrough_;
        }else ++mixed_integers_;
        ++mixed_completed_;
        if(done){stage_=19u;return true;}
        if(!predict_mixed(c,mixed_path_[i]))return fail(6);
        return true;
    }
    unsigned caller_mixed_visits()const{return mixed_completed_;}
    unsigned caller_mixed_integers()const{return mixed_integers_;}
    unsigned caller_mixed_taken()const{return mixed_taken_;}
    unsigned caller_mixed_fallthrough()const{return mixed_fallthrough_;}
    template<class C>bool reached_caller_mixed(C& c,bool held)const{
        return stage_==19u&&!mixed_path_.empty()&&mixed_completed_==mixed_path_.size()&&
            mixed_integers_+mixed_taken_+mixed_fallthrough_==mixed_completed_&&
            mixed_storage(c,held,mixed_completed_)&&visits_==e_.path.size()+1u;
    }
    // Observe the next original byte load only after the complete mixed
    // path. Predict its GPR effect without writing any live CPU state.
    template<class C>bool resume_caller_mixed_byte(C& c,int32_t offset,uint8_t expected,
                                                   uint32_t next_pc,uint32_t next_word,bool held,
                                                   std::span<const ScCallerMixedStep> post_path={},
                                                   uint32_t post_end=0,uint32_t post_word=0){
        if(!reached_caller_mixed(c,held)||!caller_parent_||offset<8||
           uint32_t(offset)>=caller_parent_->e_.frame_size||
           uint64_t(mixed_end_pc_)+4u!=next_pc||next_word==0x44000002u||
           uint64_t(next_pc)+8u>uint64_t(caller_parent_->e_.root)+branch_owner_size_||
           !word(c,next_pc,next_word)||
           !caller_written_[unsigned(offset)]||caller_expected_[unsigned(offset)]!=expected)return fail(6);
        for(unsigned j=0;j<branch_completed_;++j)
            if(next_pc==branches_[j].other_pc)return fail(6);
        for(auto s:mixed_path_)if(next_pc==s.other_pc)return fail(6);
        if(post_path.empty()){
            if(post_end||post_word||!word(c,next_pc+4u,0x44000002u))return fail(6);
        }else if(!valid_post_mixed(c,post_path,next_pc,next_word,post_end,post_word))return fail(6);
        const auto form=decode_load(mixed_end_word_);
        const unsigned rt=(mixed_end_word_>>21)&31u,ra=(mixed_end_word_>>16)&31u,rb=(mixed_end_word_>>11)&31u;
        const uint32_t imm=uint32_t(int32_t((mixed_end_word_&0xffffu)^0x8000u)-0x8000);
        const uint32_t a=(ra?gp_[ra]:0u)+(form.indexed?gp_[rb]:imm);
        if(form.width!=1u||form.update||form.sign||(rt!=0u&&(rt<3u||rt>12u))||
           a!=incoming_[1]+uint32_t(offset)||!mapped(c,{a,1u})||c.mmu.read8(a)!=expected)return fail(6);
        gp_[rt]=expected;mixed_byte_next_pc_=next_pc;mixed_byte_next_word_=next_word;
        post_mixed_path_=post_path;post_mixed_end_pc_=post_end;post_mixed_end_word_=post_word;stage_=20u;
        return true;
    }
    template<class C>bool stop_after_caller_mixed_byte(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=20u||pc!=mixed_byte_next_pc_||w!=mixed_byte_next_word_||
           !mixed_byte_code(c)||!mixed_storage(c,held,mixed_completed_+1u))return fail(6);
        mixed_byte_completed_=true;stage_=21u;return true;
    }
    unsigned caller_mixed_byte_visits()const{return mixed_byte_completed_&&!error_?1u:0u;}
    template<class C>bool reached_caller_mixed_byte(C& c,bool held)const{
        return stage_==21u&&mixed_byte_completed_&&mixed_byte_code(c)&&
            mixed_storage(c,held,mixed_completed_+1u)&&visits_==e_.path.size()+1u;
    }
    // A second mixed segment may replace the byte-only successor guard
    // only when its complete forward geometry was admitted at byte arm.
    // All previous alternate guards and memory/ABI proofs remain active.
    template<class C>bool resume_caller_post_mixed(C& c,bool held){
        if(!reached_caller_mixed_byte(c,held)||post_mixed_path_.empty()||
           !predict_mixed(c,post_mixed_path_.front()))return fail(6);
        stage_=22u;return true;
    }
    template<class C>bool caller_post_mixed_boundary(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=22u||post_mixed_completed_>=post_mixed_path_.size()||!mixed_byte_code(c)||
           !mixed_storage(c,held,mixed_completed_+2u+post_mixed_completed_))return fail(6);
        const unsigned i=post_mixed_completed_+1u;const bool done=i==post_mixed_path_.size();
        if(pc!=(done?post_mixed_end_pc_:post_mixed_path_[i].pc)||
           w!=(done?post_mixed_end_word_:post_mixed_path_[i].word))return fail(6);
        const auto& s=post_mixed_path_[post_mixed_completed_];
        if(s.other_pc){if(s.taken)++post_mixed_taken_;else ++post_mixed_fallthrough_;}
        else ++post_mixed_integers_;
        ++post_mixed_completed_;
        if(done){stage_=23u;return true;}
        if(!predict_mixed(c,post_mixed_path_[i]))return fail(6);
        return true;
    }
    unsigned caller_post_mixed_visits()const{return post_mixed_completed_;}
    unsigned caller_post_mixed_integers()const{return post_mixed_integers_;}
    unsigned caller_post_mixed_taken()const{return post_mixed_taken_;}
    unsigned caller_post_mixed_fallthrough()const{return post_mixed_fallthrough_;}
    template<class C>bool reached_caller_post_mixed(C& c,bool held)const{
        return stage_==23u&&mixed_byte_completed_&&!post_mixed_path_.empty()&&
            post_mixed_completed_==post_mixed_path_.size()&&
            post_mixed_integers_+post_mixed_taken_+post_mixed_fallthrough_==post_mixed_completed_&&
            mixed_byte_code(c)&&mixed_storage(c,held,mixed_completed_+1u+post_mixed_completed_)&&
            visits_==e_.path.size()+1u;
    }
    // The pointer is a privately authenticated relative identity, not an
    // inferred constant. Predict only a volatile register copy; no memory
    // is accessed at the resulting pointer.
    template<class C>bool resume_caller_stack_move(C& c,int32_t offset,uint32_t next_pc,uint32_t next_word,bool held,
        std::optional<ScCallerIntegerStep> final_integer={},uint32_t final_pc=0,uint32_t final_word=0){
        if(!reached_caller_post_mixed(c,held)||!caller_parent_||
           uint64_t(post_mixed_end_pc_)+4u!=next_pc||next_word==0x44000002u||
           uint64_t(next_pc)+8u>uint64_t(caller_parent_->e_.root)+branch_owner_size_||
           !word(c,next_pc,next_word))return fail(6);
        if(final_integer){
            if(final_integer->pc!=next_pc||final_integer->word!=next_word||next_word>>26!=14u||
               final_integer->inputs.size()>1u||uint64_t(next_pc)+4u!=final_pc||
               uint64_t(final_pc)+8u>uint64_t(caller_parent_->e_.root)+branch_owner_size_||
               final_word>>26!=18u||(final_word&3u)!=1u||
               !word(c,final_pc,final_word)||!word(c,final_pc+4u,0x44000002u))return fail(6);
            for(unsigned j=0;j<branch_completed_;++j)if(final_pc==branches_[j].other_pc)return fail(6);
            for(auto s:mixed_path_)if(final_pc==s.other_pc)return fail(6);
            for(auto s:post_mixed_path_)if(final_pc==s.other_pc)return fail(6);
        }else if(final_pc||final_word||!word(c,next_pc+4u,0x44000002u))return fail(6);
        for(unsigned j=0;j<branch_completed_;++j)if(next_pc==branches_[j].other_pc)return fail(6);
        for(auto s:mixed_path_)if(next_pc==s.other_pc)return fail(6);
        for(auto s:post_mixed_path_)if(next_pc==s.other_pc)return fail(6);
        const auto effect=predict_caller_stack_move(post_mixed_end_word_,gp_,cr_,incoming_[1],offset);
        if(!effect||!effect->reg)return fail(6);
        gp_[*effect->reg]=effect->value;
        stack_move_next_pc_=next_pc;stack_move_next_word_=next_word;
        final_integer_=final_integer;final_integer_pc_=final_pc;final_integer_word_=final_word;
        stage_=24u;return true;
    }
    template<class C>bool stop_after_caller_stack_move(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=24u||pc!=stack_move_next_pc_||w!=stack_move_next_word_||
           !stack_move_code(c)||!mixed_byte_code(c)||
           !mixed_storage(c,held,mixed_completed_+2u+post_mixed_completed_))return fail(6);
        stack_move_completed_=true;stage_=25u;return true;
    }
    unsigned caller_stack_move_visits()const{return stack_move_completed_&&!error_?1u:0u;}
    template<class C>bool reached_caller_stack_move(C& c,bool held)const{
        return stage_==25u&&stack_move_completed_&&mixed_byte_completed_&&
            post_mixed_completed_==post_mixed_path_.size()&&stack_move_code(c)&&mixed_byte_code(c)&&
            mixed_storage(c,held,mixed_completed_+2u+post_mixed_completed_)&&visits_==e_.path.size()+1u;
    }
    // Authenticate the last register-only operation before an external BL.
    // The branch itself remains unexecuted at stage 27.
    template<class C>bool resume_caller_final_integer(C& c,bool held){
        if(!reached_caller_stack_move(c,held)||!final_integer_||
           !predict_integer(c,*final_integer_))return fail(6);
        stage_=26u;return true;
    }
    template<class C>bool stop_after_caller_final_integer(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=26u||pc!=final_integer_pc_||w!=final_integer_word_||
           !stack_move_code(c)||!mixed_byte_code(c)||
           !mixed_storage(c,held,mixed_completed_+3u+post_mixed_completed_))return fail(6);
        final_integer_completed_=true;stage_=27u;return true;
    }
    unsigned caller_final_integer_visits()const{return final_integer_completed_&&!error_?1u:0u;}
    template<class C>bool reached_caller_final_integer(C& c,bool held)const{
        return stage_==27u&&final_integer_completed_&&stack_move_completed_&&mixed_byte_completed_&&
            post_mixed_completed_==post_mixed_path_.size()&&stack_move_code(c)&&mixed_byte_code(c)&&
            mixed_storage(c,held,mixed_completed_+3u+post_mixed_completed_)&&visits_==e_.path.size()+1u;
    }
    // A linked branch is an architectural LR/PC transition, not a local
    // branch or another register-only instruction. Keep the historical
    // return LR proof intact and verify the new LR separately.
    template<class C>bool resume_caller_next_entry(C& c,uint32_t dst,uint32_t w,uint32_t ret,bool held,
                                                   std::optional<uint32_t> successor={},
                                                   std::optional<uint32_t> following={},
                                                   std::optional<uint32_t> third={},
                                                    std::optional<uint32_t> fourth={}){
        if(!reached_caller_final_integer(c,held)||!caller_parent_||
           final_integer_word_>>26!=18u||(final_integer_word_&3u)!=1u||
           target(final_integer_pc_,final_integer_word_)!=dst||
           uint64_t(final_integer_pc_)+4u!=ret||dst>=caller_parent_->e_.root||
           !decode_load(w).width||!word(c,dst,w)||
           !word(c,dst+4u,successor.value_or(0x44000002u))||
           (following&&!successor)||(third&&!following)||(fourth&&!third)||
           (successor&&(*successor==0x44000002u||
             uint64_t(dst)+(fourth?24u:third?20u:following?16u:12u)>caller_parent_->e_.root||
             !word(c,dst+8u,following.value_or(0x44000002u))))||
           (following&&(*following==0x44000002u||!word(c,dst+12u,third.value_or(0x44000002u))))||
           (third&&(*third==0x44000002u||!word(c,dst+16u,fourth.value_or(0x44000002u))))||
            (fourth&&(*fourth==0x44000002u||!word(c,dst+20u,0x44000002u)))||
           !word(c,ret,0x44000002u))return fail(6);
        next_entry_pc_=dst;next_entry_word_=w;next_entry_lr_=ret;
        next_entry_successor_=successor;next_entry_following_=following;
        next_entry_third_=third;next_entry_fourth_=fourth;stage_=28u;return true;
    }
    // Authenticate the pinned direct function's root trace before its
    // first label tick. No outer dispatcher or callback poll intervenes.
    template<class C>bool caller_next_entry_trace(C& c,uint32_t pc,bool held){
        if(stage_!=28u||next_entry_trace_seen_||pc!=next_entry_pc_||!next_entry_storage(c,held,false))return fail(6);
        next_entry_trace_seen_=true;return true;
    }
    template<class C>bool stop_at_caller_next_entry(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=28u||!next_entry_trace_seen_||pc!=next_entry_pc_||w!=next_entry_word_||
           !next_entry_storage(c,held))return fail(6);
        next_entry_completed_=true;stage_=29u;return true;
    }
    unsigned caller_next_entry_visits()const{return next_entry_completed_&&!error_?1u:0u;}
    template<class C>bool reached_caller_next_entry(C& c,bool held)const{
        return stage_==29u&&next_entry_trace_seen_&&next_entry_completed_&&next_entry_storage(c,held);
    }
    // Continue only after a separately authenticated report-byte transition
    // has been armed. Keep every older frame and guard in the joined witness.
    // The guest's actual load is performed by translated code, never here.
    template<class C>bool resume_caller_report_byte(C& c,int32_t parent_offset,uint32_t report_offset,
        uint8_t expected,bool transition_armed,bool held){
        if(!reached_caller_next_entry(c,held)||!next_entry_successor_||!transition_armed||
           report_offset<8u||report_offset>=128u||
           parent_offset!=int32_t(736u+report_offset))return fail(6);
        const auto form=decode_load(next_entry_word_);
        const unsigned rt=(next_entry_word_>>21)&31u,ra=(next_entry_word_>>16)&31u,rb=(next_entry_word_>>11)&31u;
        const uint32_t delta=form.indexed?gp_[rb]:uint32_t(int32_t((next_entry_word_&0xffffu)^0x8000u)-0x8000);
        const int64_t address=int64_t(gp_[1])+parent_offset;
        const uint32_t effective=(ra?gp_[ra]:0u)+delta;
        if(form.width!=1u||form.update||form.sign||(rt!=0u&&(rt<3u||rt>12u))||
           address!=effective||address<0x80000000ll||address>=0x81800000ll||
           !mapped(c,{uint32_t(address),1u})||c.mmu.read8(uint32_t(address))!=expected)return fail(6);
        report_byte_address_=uint32_t(address);report_byte_expected_=expected;
        gp_[rt]=expected;stage_=30u;return true;
    }
    template<class C>bool stop_after_caller_report_byte(C& c,uint32_t pc,uint32_t w,bool transition_verified,bool held){
        if(stage_!=30u||!transition_verified||!next_entry_successor_||pc!=next_entry_pc_+4u||w!=*next_entry_successor_||
           !report_byte_storage(c,held))return fail(6);
        report_byte_completed_=true;stage_=31u;return true;
    }
    unsigned caller_report_byte_visits()const{return report_byte_completed_&&!error_?1u:0u;}
    template<class C>bool reached_caller_report_byte(C& c,bool held)const{
        return stage_==31u&&report_byte_completed_&&report_byte_storage(c,held);
    }
    // The independently proven GPR constant is checked at the native label.
    // The original translated instruction changes only the selected CR field.
    template<class C>bool resume_caller_report_compare(C& c,unsigned source_reg,
        uint32_t source_value,bool transition_armed,bool held){
        if(!reached_caller_report_byte(c,held)||!next_entry_following_||
           !transition_armed||source_reg>=32u||
           ((next_entry_successor_.value()>>16u)&31u)!=source_reg)return fail(6);
        const std::array<CallerIntegerInput,1> input{{{source_reg,source_value}}};
        const auto predicted=predict_caller_integer(*next_entry_successor_,c.gpr,
            pack(c),c.xer,input);
        if(!predicted||predicted->reg)return fail(6);
        cr_=predicted->cr;
        stage_=32u;
        return true;
    }
    template<class C>bool stop_after_caller_report_compare(C& c,uint32_t pc,
        uint32_t w,bool transition_verified,bool held){
        if(stage_!=32u||!transition_verified||!next_entry_following_||
           pc!=next_entry_pc_+8u||w!=*next_entry_following_||
           !report_byte_storage(c,held,2u))return fail(6);
        compare_completed_=true;stage_=33u;return true;
    }
    unsigned caller_report_compare_visits()const{
        return compare_completed_&&!error_?1u:0u;
    }
    template<class C>bool reached_caller_report_compare(C& c,bool held)const{
        return stage_==33u&&compare_completed_&&report_byte_storage(c,held,2u);
    }
    // Admit the original stack-derived PPC register copy without producing
    // a fabricated numeric input or authorizing any memory dereference.
    template<class C>bool resume_caller_report_copy(C& c,unsigned src,unsigned dst,
        int32_t offset,bool held){
        if(!reached_caller_report_compare(c,held)||!next_entry_third_||
           src>=32u||dst>=32u||src==dst||
           !next_entry_following_)return fail(6);
        const uint32_t w=*next_entry_following_;
        if(w>>26!=31u||((w>>1u)&1023u)!=444u||(w&1u)||
           ((w>>21u)&31u)!=src||((w>>11u)&31u)!=src||
           ((w>>16u)&31u)!=dst)return fail(6);
        // Keep this native path as narrow as its independent symbolic
        // provenance: an ABI-saved nonvolatile destination is not sufficient.
        const auto predicted=predict_caller_stack_relative(
            w,c.gpr,pack(c),gp_[1],src,offset);
        const int64_t address=int64_t(gp_[1])+int64_t(offset);
        if(!predicted||predicted->reg!=dst||predicted->cr!=cr_||
           address<0x80000000ll||address>=0x81800000ll||
           predicted->value!=uint32_t(address)||
           gp_[src]!=uint32_t(address)||c.gpr[src]!=uint32_t(address))
            return fail(6);
        gp_[dst]=predicted->value;
        report_copy_destination_=dst;report_copy_value_=predicted->value;
        stage_=34u;return true;
    }
    template<class C>bool stop_after_caller_report_copy(C& c,uint32_t pc,
        uint32_t w,bool held){
        if(stage_!=34u||!next_entry_third_||pc!=next_entry_pc_+12u||
           w!=*next_entry_third_||c.gpr[report_copy_destination_]!=report_copy_value_||
           gp_[report_copy_destination_]!=report_copy_value_||
           !report_byte_storage(c,held,3u))
            return fail(6);
        report_copy_completed_=true;stage_=35u;return true;
    }
    unsigned caller_report_copy_visits()const{
        return report_copy_completed_&&!error_?1u:0u;
    }
    template<class C>bool reached_caller_report_copy(C& c,bool held)const{
        return stage_==35u&&report_copy_completed_&&report_byte_storage(c,held,3u);
    }
    // Optional original 121 (PPC li): preserve the previous caller state
    // and authorize one translated zero-input addi. The fourth original
    // word stays unexecuted behind the following test-only guard.
    template<class C>bool resume_caller_report_immediate(C& c,unsigned dst,
        uint32_t expected,bool held){
        if(!reached_caller_report_copy(c,held)||!next_entry_third_||
           !next_entry_fourth_)return fail(6);
        const auto predicted=predict_caller_zero_input_addi(
            *next_entry_third_,c.gpr,pack(c),c.xer);
        // PPC li reads no source GPR and fully replaces its volatile
        // destination. The reached_caller_report_copy predecessor above
        // still authenticates *all* live GPRs; avoid a redundant check
        // in the instruction-specific effect predictor.
        if(!predicted||predicted->reg!=dst||predicted->value!=expected||
           predicted->cr!=cr_)return fail(6);
        gp_[dst]=expected;
        report_immediate_destination_=dst;
        report_immediate_value_=expected;
        stage_=36u;
        return true;
    }
    template<class C>bool stop_after_caller_report_immediate(C& c,
        uint32_t pc,uint32_t w,bool held){
        if(stage_!=36u||!next_entry_fourth_||pc!=next_entry_pc_+16u||
           w!=*next_entry_fourth_||
           c.gpr[report_immediate_destination_]!=report_immediate_value_||
           gp_[report_immediate_destination_]!=report_immediate_value_||
           !report_byte_storage(c,held,4u))return fail(6);
        report_immediate_completed_=true;
        stage_=37u;
        return true;
    }
    unsigned caller_report_immediate_visits()const{
        return report_immediate_completed_&&!error_?1u:0u;
    }
    template<class C>bool reached_caller_report_immediate(C& c,bool held)const{
        return stage_==37u&&report_immediate_completed_&&
            report_byte_storage(c,held,4u);
    }
    template<class C>bool stop_before_instruction(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=1u||!e_.boundary.instruction||!boundary_due_||back_poll_due_||due_||
           visits_!=e_.path.size()||pc!=e_.target||w!=e_.target_word||
           c.inst_count-last_!=1u||!common(c,held)||!word(c,pc,w)||!abi(c)||
           caller_stores_.size()!=caller_store_count_)return fail(6);
        last_=c.inst_count;stage_=2u;return true;
    }
    template<class C>bool reached_instruction_boundary(C& c,bool held)const{
        return stage_==2u&&e_.boundary.instruction&&boundary_due_&&!due_&&!back_poll_due_&&
            common(c,held)&&c.inst_count==last_&&abi(c)&&word(c,e_.target,e_.target_word)&&
            caller_stores_.size()==caller_store_count_;
    }
    unsigned caller_store_count()const{return caller_store_count_;}
    template<class C>bool stop_before_control_destination(C& c,uint32_t pc,uint32_t w,bool held){
        if(stage_!=4u||pc!=e_.control.destination||c.pc!=pc||w!=e_.control.word||
           c.inst_count-last_!=2u||!control_storage(c,held))return fail(6);
        last_=c.inst_count;stage_=5u;return true;
    }
    template<class C>bool reached_control_destination(C& c,bool held)const{
        return stage_==5u&&c.pc==e_.control.destination&&c.inst_count==last_&&control_storage(c,held);
    }
    template<class C>bool reached(C& c,bool held)const{
        return stage_==2u&&!local_stop()&&due_&&common(c,held)&&c.pc==e_.target&&c.inst_count==last_&&abi(c);
    }
    // A frameless descendant may change volatile registers but must not
    // alter any byte of this completed formatter prologue frame.
    template<class C>bool frame_held(C& c,bool held)const{
        if(stage_!=2u||error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=frame_.base||
           c.inst_count<last_||c.inst_count-last_>128u||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
    // One bounded 48-byte nested frame may use the ABI's linkage word.
    // The child's own shadow supplies the expected current linkage value.
    template<class C>bool child_frame_held(C& c,bool held,uint32_t child_sp,uint32_t child_link)const{
        if(stage_!=2u||!due_||error_||!held||cpu_!=&c||!safe(c)||c.gpr[1]!=child_sp||
           (child_sp!=frame_.base&&child_sp!=frame_.base-48u)||c.inst_count<last_||
           c.inst_count-last_>128u||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i){
            if(i>=4u&&i<8u&&written_[i])return false;
            const auto v=(i>=4u&&i<8u)?uint8_t(child_link>>(24u-8u*(i-4u))):shadow_[i];
            if(c.mmu.read8(frame_.base+i)!=v)return false;
        }
        return true;
    }
    // Parent checks *all* original bytes, replacing only the exact
    // child-predicted values at already witnessed caller-store sites.
    template<class C>bool child_frame_held_with_stores(C& c,bool held,const ScFormatterWitness& child)const{
        if(child.caller_parent_!=this||child.cpu_!=cpu_||child.error_||!held||stage_!=2u||!due_||
           error_||cpu_!=&c||!safe(c)||c.gpr[1]!=(child.frame_released_?frame_.base:frame_.base-48u)||
           c.inst_count<last_||c.inst_count-last_>child.caller_parent_tick_limit()||!mapped(c,frame_)||
           child.caller_expected_.size()!=shadow_.size()||child.caller_written_.size()!=shadow_.size())return false;
        for(unsigned i=0;i<shadow_.size();++i){
            if(i>=4u&&i<8u&&written_[i])return false;
            if(child.caller_written_[i]&&(i<8u||i>=e_.frame_size||written_[i]))return false;
            const auto v=(i>=4u&&i<8u)?uint8_t(child.linkage_word()>>(24u-8u*(i-4u))):
                child.caller_written_[i]?child.caller_expected_[i]:shadow_[i];
            if(c.mmu.read8(frame_.base+i)!=v)return false;
        }
        return true;
    }
    template<class C>uint64_t frame_age(C& c)const{
        return c.inst_count>=last_?c.inst_count-last_:UINT64_MAX;
    }
    uint64_t caller_parent_baseline()const{return parent_checkpoint_valid_?parent_checkpoint_age_:0u;}
    uint64_t caller_parent_tick_limit()const{
        if(!parent_checkpoint_valid_||!frame_released_||branch_completed_<2u||
           integer_completed_!=2u||post_integer_completed_!=1u)return 128u;
        // The current instruction is counted only in an armed stage.
        // Return-storage checks still enforce its exact one-tick delta.
        const bool armed=stage_==14u||stage_==18u||stage_==20u||stage_==22u||stage_==24u||stage_==26u||stage_==28u||stage_==30u||stage_==32u||stage_==34u||stage_==36u;
        const auto extra=branch_completed_-2u+mixed_completed_+unsigned(mixed_byte_completed_)+post_mixed_completed_+unsigned(stack_move_completed_)+unsigned(final_integer_completed_)+unsigned(next_entry_completed_)+unsigned(report_byte_completed_)+unsigned(compare_completed_)+unsigned(report_copy_completed_)+unsigned(report_immediate_completed_)+unsigned(armed);
        if(extra>41u)return 128u;
        return std::max<uint64_t>(128u,parent_checkpoint_age_+extra);
    }
    // Only the already-observed fourth branch can open a continuation
    // budget for an ancestor frame. No budget comes from the live counter.
    std::optional<unsigned> caller_post_fourth_tick_budget()const{
        if(error_||!frame_released_||branch_completed_!=4u||integer_completed_!=2u||
           post_integer_completed_!=1u||!(stage_==15u||(stage_>=18u&&stage_<=37u)))return {};
        const bool armed=stage_==18u||stage_==20u||stage_==22u||stage_==24u||stage_==26u||stage_==28u||stage_==30u||stage_==32u||stage_==34u||stage_==36u;
        const unsigned n=mixed_completed_+unsigned(mixed_byte_completed_)+post_mixed_completed_+
            unsigned(stack_move_completed_)+unsigned(final_integer_completed_)+unsigned(next_entry_completed_)+unsigned(report_byte_completed_)+unsigned(compare_completed_)+unsigned(report_copy_completed_)+unsigned(report_immediate_completed_)+unsigned(armed);
        if(n>39u)return {};
        return n;
    }
    bool has_caller_stores()const{return caller_parent_!=nullptr;}
private:
    struct LoadForm {unsigned width=0;bool indexed=false,update=false,sign=false;};
    static LoadForm decode_load(uint32_t w){
        const unsigned op=w>>26,rt=(w>>21)&31u,ra=(w>>16)&31u,xo=(w>>1)&1023u;
        LoadForm f;
        if((op>=32u&&op<=35u)||(op>=40u&&op<=43u)){
            f={op<=33u?4u:op<=35u?1u:2u,false,bool(op&1u),op>=42u};
        }else if(op==31u&&!(w&1u)){
            switch(xo){
            case 23:case 55:f={4,true,xo==55,false};break;
            case 87:case 119:f={1,true,xo==119,false};break;
            case 279:case 311:case 343:case 375:f={2,true,xo==311||xo==375,xo==343||xo==375};break;
            default:return {};
            }
        }
        if(rt==1u||(f.update&&(!ra||ra==rt||ra==1u)))return {};
        return f;
    }
    ScFormatterExpectation e_;const void* cpu_=nullptr;AllocatorRange frame_{};
    std::array<uint32_t,32> gp_{},incoming_{};std::array<uint32_t,8> gqr_{};
    std::vector<uint8_t> shadow_,written_;
    const ScFormatterWitness* caller_parent_=nullptr;
    std::vector<ScFormatterAccess> caller_stores_;
    std::vector<uint8_t> caller_expected_,caller_written_;
    unsigned caller_store_count_=0;uint32_t owner_size_=0;
    std::optional<int32_t> conditional_offset_;
    uint32_t msr_=0,cr_=0,lr_=0,ctr_=0,xer_=0,srr0_=0,srr1_=0;
    uint64_t last_=0,seen_=0;unsigned stage_=0,error_=0,visits_=0,stores_=0,loads_=0,authenticated_loads_=0;
    bool initial_poll_=false,entry_seen_=false,due_=false,back_poll_due_=false,boundary_due_=false;
    bool release_authorized_=false,frame_released_=false;
    uint32_t return_pc_=0,return_word_=0;
    bool caller_arrival_=false;
    uint32_t caller_next_pc_=0,caller_next_word_=0;
    std::span<const ScCallerIntegerStep> integer_path_{};
    uint32_t integer_end_pc_=0,integer_end_word_=0;
    unsigned integer_completed_=0;
    struct CallerBranchEdge {uint32_t pc,word,next_pc,next_word,other_pc;};
    std::array<CallerBranchEdge,4> branches_{};
    unsigned branch_completed_=0;
    uint32_t branch_owner_size_=0;
    struct CallerArrival {uint32_t pc,lr;};
    template<class C>bool branch_storage(C& c,bool held,unsigned n,unsigned extra=0u,
                                        std::optional<CallerArrival> arrival={})const{
        if(!n||n>branches_.size()||integer_completed_!=integer_path_.size()||!integer_code(c)||
           !return_storage(c,held,3u+integer_completed_+n+extra,arrival))return false;
        for(unsigned i=0;i<n;++i){
            const auto& b=branches_[i];
            if(!word(c,b.pc,b.word)||!word(c,b.next_pc,b.next_word)||
               !word(c,b.other_pc,0x44000002u))return false;
        }
        return true;
    }
    std::span<const ScCallerIntegerStep> post_integer_path_{};
    uint32_t post_integer_end_pc_=0,post_integer_end_word_=0;
    unsigned post_integer_completed_=0;
    uint64_t parent_checkpoint_age_=0;
    bool parent_checkpoint_valid_=false;
    template<class C>bool post_integer_code(C& c)const{
        if(post_integer_path_.empty()||!word(c,post_integer_end_pc_,post_integer_end_word_))return false;
        for(auto step:post_integer_path_)if(!word(c,step.pc,step.word))return false;
        return true;
    }
    template<class C>bool post_integer_storage(C& c,bool held,unsigned n)const{
        return branch_completed_==2u&&branch_storage(c,held,2u,n)&&post_integer_code(c);
    }
    std::span<const ScCallerMixedStep> mixed_path_{};
    uint32_t mixed_end_pc_=0,mixed_end_word_=0,mixed_byte_next_pc_=0,mixed_byte_next_word_=0;
    bool mixed_byte_completed_=false;
    bool stack_move_completed_=false;
    uint32_t stack_move_next_pc_=0,stack_move_next_word_=0;
    std::optional<ScCallerIntegerStep> final_integer_{};
    uint32_t final_integer_pc_=0,final_integer_word_=0;
    bool final_integer_completed_=false;
    uint32_t next_entry_pc_=0,next_entry_word_=0,next_entry_lr_=0;
    bool next_entry_completed_=false,next_entry_trace_seen_=false;
    std::optional<uint32_t> next_entry_successor_{},next_entry_following_{},next_entry_third_{},next_entry_fourth_{};
    uint32_t report_byte_address_=0;uint8_t report_byte_expected_=0;
    bool report_byte_completed_=false,compare_completed_=false,report_copy_completed_=false;
    unsigned report_copy_destination_=0u;uint32_t report_copy_value_=0u;
    unsigned report_immediate_destination_=0u;uint32_t report_immediate_value_=0u;
    bool report_immediate_completed_=false;
    template<class C>bool report_byte_storage(C& c,bool held,unsigned tick=1u)const{
        return next_entry_completed_&&next_entry_trace_seen_&&next_entry_successor_&&
            next_entry_storage(c,held,true,tick)&&mapped(c,{report_byte_address_,1u})&&
            c.mmu.read8(report_byte_address_)==report_byte_expected_;
    }
    template<class C>bool next_entry_storage(C& c,bool held,bool label_tick=true,unsigned extra=0u)const{
        return final_integer_completed_&&stack_move_completed_&&mixed_byte_completed_&&
            post_mixed_completed_==post_mixed_path_.size()&&stack_move_code(c)&&mixed_byte_code(c)&&
            word(c,next_entry_pc_,next_entry_word_)&&
            word(c,next_entry_pc_+4u,next_entry_successor_.value_or(0x44000002u))&&
            (!next_entry_successor_||word(c,next_entry_pc_+8u,next_entry_following_.value_or(0x44000002u)))&&
            (!next_entry_following_||word(c,next_entry_pc_+12u,next_entry_third_.value_or(0x44000002u)))&&
            (!next_entry_third_||word(c,next_entry_pc_+16u,next_entry_fourth_.value_or(0x44000002u)))&&
            (!next_entry_fourth_||word(c,next_entry_pc_+20u,0x44000002u))&&
            word(c,next_entry_lr_,0x44000002u)&&
            mixed_storage(c,held,mixed_completed_+3u+post_mixed_completed_+unsigned(label_tick)+extra,
                CallerArrival{next_entry_pc_,next_entry_lr_})&&visits_==e_.path.size()+1u;
    }
    template<class C>bool stack_move_code(C& c)const{
        if(!word(c,stack_move_next_pc_,stack_move_next_word_))return false;
        if(!final_integer_)return word(c,stack_move_next_pc_+4u,0x44000002u);
        return word(c,final_integer_pc_,final_integer_word_)&&word(c,final_integer_pc_+4u,0x44000002u);
    }
    std::span<const ScCallerMixedStep> post_mixed_path_{};
    uint32_t post_mixed_end_pc_=0,post_mixed_end_word_=0;
    unsigned post_mixed_completed_=0,post_mixed_integers_=0,post_mixed_taken_=0,post_mixed_fallthrough_=0;
    template<class C>bool valid_post_mixed(C& c,std::span<const ScCallerMixedStep> path,
                                          uint32_t start,uint32_t start_word,uint32_t end,uint32_t end_word)const{
        if(!caller_parent_||path.empty()||path.size()>16u||path.front().pc!=start||
           path.front().word!=start_word||end_word==0x44000002u||!word(c,end,end_word))return false;
        const auto owner=caller_parent_->e_.root;
        const auto inside=[&](uint32_t a){return !(a&3u)&&a>=owner&&uint64_t(a)+4u<=uint64_t(owner)+branch_owner_size_;};
        if(!inside(end))return false;
        for(unsigned i=0;i<path.size();++i){
            const auto& s=path[i];
            if(!inside(s.pc)||!inside(s.next_pc)||s.next_pc<=s.pc||
               s.next_pc!=(i+1u==path.size()?end:path[i+1u].pc)||
               s.word==0x44000002u||s.inputs.size()>3u||!word(c,s.pc,s.word))return false;
            for(unsigned j=0;j<branch_completed_;++j)
                if(s.pc==branches_[j].other_pc||s.next_pc==branches_[j].other_pc)return false;
            for(auto t:mixed_path_)if(t.other_pc&&(s.pc==t.other_pc||s.next_pc==t.other_pc))return false;
            for(auto t:path)if(t.other_pc&&(s.pc==t.other_pc||s.next_pc==t.other_pc))return false;
            if(s.other_pc){
                if(!inside(s.other_pc)||s.other_pc==s.next_pc||!s.inputs.empty()||
                   !word(c,s.other_pc,0x44000002u)||!mixed_edge(s,false))return false;
            }else if(s.taken||uint64_t(s.pc)+4u!=s.next_pc)return false;
        }
        return true;
    }
    template<class C>bool mixed_byte_code(C& c)const{
        if(!word(c,mixed_byte_next_pc_,mixed_byte_next_word_))return false;
        if(post_mixed_path_.empty())return word(c,mixed_byte_next_pc_+4u,0x44000002u);
        return valid_post_mixed(c,post_mixed_path_,mixed_byte_next_pc_,mixed_byte_next_word_,post_mixed_end_pc_,post_mixed_end_word_);
    }
    unsigned mixed_completed_=0,mixed_integers_=0,mixed_taken_=0,mixed_fallthrough_=0;
    bool mixed_edge(const ScCallerMixedStep& s,bool check_condition)const{
        const unsigned op=s.word>>26,bo=(s.word>>21)&31u,bi=(s.word>>16)&31u;
        if((op!=16u&&op!=18u)||(s.word&3u)||(op==16u&&!(bo&4u)))return false;
        const auto dst=target(s.pc,s.word);
        if(uint64_t(dst)<=uint64_t(s.pc)+4u||s.next_pc!=(s.taken?dst:s.pc+4u)||
           s.other_pc!=(s.taken?s.pc+4u:dst)||(!s.taken&&op==18u))return false;
        const bool outcome=op==18u||(bo&16u)||bool((cr_>>(31u-bi))&1u)==bool(bo&8u);
        return !check_condition||outcome==s.taken;
    }
    template<class C>bool predict_mixed(C& c,const ScCallerMixedStep& s){
        return s.other_pc?mixed_edge(s,true):predict_integer(c,{s.pc,s.word,s.inputs});
    }
    template<class C>bool mixed_storage(C& c,bool held,unsigned n,std::optional<CallerArrival> arrival={})const{
        if(branch_completed_!=4u||!branch_storage(c,held,4u,post_integer_completed_+n,arrival)||
           !post_integer_code(c)||!word(c,mixed_end_pc_,mixed_end_word_))return false;
        for(auto s:mixed_path_){
            if(!word(c,s.pc,s.word)||(s.other_pc&&!word(c,s.other_pc,0x44000002u)))return false;
        }
        return true;
    }
    uint32_t caller_modified_mask_=0;
    // The child's return ABI was already observed strictly. Subsequent
    // caller writes are allowed only for a register whose ORIGINAL caller
    // value is still saved in an independently witnessed caller-frame slot.
    template<class C>bool parent_saved_register(C& c,unsigned r)const{
        if(!caller_parent_||r<14u||r>=32u)return false;
        const auto& p=*caller_parent_;
        const auto it=std::find_if(p.e_.slots.begin(),p.e_.slots.end(),[&](auto x){return x.reg==r;});
        if(it==p.e_.slots.end())return false;
        const int64_t at=int64_t(p.incoming_[1])+it->caller_offset;
        const int64_t off=at-p.frame_.base;
        if(off<8||off>int64_t(p.e_.frame_size)-4||off%4||
           !mapped(c,{uint32_t(at),4u}))return false;
        uint32_t v=0;
        for(unsigned i=0;i<4u;++i){
            const auto j=unsigned(off)+i;
            if(!p.written_[j]||caller_written_[j])return false;
            v=(v<<8)|p.shadow_[j];
        }
        return v==p.incoming_[r]&&c.mmu.read32(uint32_t(at))==v;
    }
    template<class C>bool predict_integer(C& c,const ScCallerIntegerStep& step){
        uint32_t saved=0;
        for(unsigned r=14;r<32u;++r)if(parent_saved_register(c,r))saved|=uint32_t(1)<<r;
        const auto effect=predict_caller_integer(step.word,gp_,cr_,xer_,step.inputs,saved);
        if(!effect)return false;
        if(effect->reg){
            const auto r=*effect->reg;
            if(r>=14u)caller_modified_mask_|=uint32_t(1)<<r;
            gp_[r]=effect->value;
        }
        cr_=effect->cr;return true;
    }
    template<class C>bool caller_return_registers_held(C& c)const{
        if(gp_[2]!=incoming_[2]||gp_[13]!=incoming_[13])return false;
        for(unsigned r=14;r<32u;++r){
            if(caller_modified_mask_&(uint32_t(1)<<r)){
                if(!parent_saved_register(c,r))return false;
            }else if(gp_[r]!=incoming_[r])return false;
        }
        return true;
    }
    template<class C>bool integer_code(C& c)const{
        for(auto step:integer_path_)if(!word(c,step.pc,step.word))return false;
        return word(c,integer_end_pc_,integer_end_word_);
    }
    template<class C>bool return_storage(C& c,bool held,uint64_t delta=0,std::optional<CallerArrival> arrival={})const{
        return frame_released_&&caller_parent_&&return_pc_==e_.entry_lr&&
            c.pc==(arrival?arrival->pc:return_pc_)&&c.inst_count>=last_&&c.inst_count-last_==delta&&word(c,return_pc_,return_word_)&&
            word(c,e_.target,e_.target_word)&&common(c,held,false,arrival?std::optional<uint32_t>{arrival->lr}:std::nullopt)&&abi(c)&&
            caller_parent_->child_frame_held_with_stores(c,held,*this);
    }
    uint32_t poll_pc_=0,poll_ctr_=0;unsigned back_polls_=0;
    template<class C>bool control_storage(C& c,bool held)const{
        return e_.control.destination&&boundary_due_&&!due_&&!back_poll_due_&&common(c,held)&&abi(c)&&
            ctr_==e_.control.destination&&word(c,e_.target,e_.target_word)&&word(c,e_.control.destination,e_.control.word);
    }
    bool local_stop()const{return e_.boundary.width||e_.boundary.instruction||e_.control.destination;}
    unsigned branch_detail_=0;
    bool branch_reject(unsigned detail){if(!branch_detail_)branch_detail_=detail;return fail(6);}
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static uint32_t mask(unsigned mb,unsigned me){
        uint32_t v=0;for(unsigned i=0;i<32u;++i)if(mb<=me?(i>=mb&&i<=me):(i>=mb||i<=me))v|=1u<<(31u-i);return v;
    }
    void compare(unsigned f,bool lt,bool eq){
        const unsigned sh=28u-4u*f;
        cr_=(cr_&~(15u<<sh))|(((lt?8u:eq?2u:4u)|((xer_>>31)&1u))<<sh);
    }
    void record(uint32_t v){compare(0u,(v&0x80000000u)!=0u,v==0u);}
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool bc=w>>26==16u;const uint32_t m=bc?0xfffcu:0x03fffffcu,s=bc?0x8000u:0x02000000u;
        return pc+(((w&m)^s)-s);
    }
    bool access(uint32_t pc,uint32_t a,unsigned n,bool wr){
        const auto x=std::find_if(e_.accesses.begin(),e_.accesses.end(),[&](auto v){return v.pc==pc;});
        if(x==e_.accesses.end()||x->width!=n||x->write!=wr)return false;
        const int64_t expected=x->stack?int64_t(incoming_[1])+x->address:x->address;
        if(expected<0||expected>0xffffffffll||a!=uint32_t(expected))return false;
        const auto i=unsigned(x-e_.accesses.begin());
        if(i>=64u)return false;
        const auto bit=uint64_t(1)<<i;
        if(seen_&bit)return false;
        seen_|=bit;return true;
    }
    bool store(uint32_t pc,uint32_t a,unsigned n,uint32_t v){
        if(caller_parent_&&a>=incoming_[1]+8u){
            const auto off=int64_t(a)-incoming_[1];
            const auto it=std::find_if(caller_stores_.begin(),caller_stores_.end(),[&](auto x){return x.pc==pc&&x.address==off&&x.width==n;});
            if(it==caller_stores_.end()||off<8||off+n>caller_parent_->e_.frame_size||a%n)return false;
            for(unsigned i=0;i<n;++i)if(caller_written_[unsigned(off)+i])return false;
            for(unsigned i=0;i<n;++i){const auto j=unsigned(off)+i;caller_written_[j]=1;
                caller_expected_[j]=uint8_t(v>>(8u*(n-i-1u)));}
            ++caller_store_count_;return true;
        }
        if(!frame_.contains(a,n)||(a%n)||(a>=incoming_[1]&&(a!=incoming_[1]+4u||n!=4u||v!=e_.entry_lr)))return false;
        for(unsigned i=0;i<n;++i){const auto j=a-frame_.base+i;if(written_[j])return false;written_[j]=1;
            shadow_[j]=uint8_t(v>>(8u*(n-i-1u)));}
        return true;
    }
    bool return_registers_held()const{
        for(unsigned r=14;r<32u;++r)if(gp_[r]!=incoming_[r])return false;
        return gp_[2]==incoming_[2]&&gp_[13]==incoming_[13];
    }
    template<class C>bool abi(C& c)const{
        if(stores_+loads_!=e_.accesses.size()||unsigned(std::popcount(seen_))!=e_.accesses.size()||authenticated_loads_!=unsigned(std::count_if(e_.accesses.begin(),e_.accesses.end(),[](auto a){return a.expected_value.has_value();}))||
           gp_[1]!=(frame_released_?incoming_[1]:frame_.base)||c.mmu.read32(frame_.base)!=incoming_[1]||
           (frame_released_&&(lr_!=e_.entry_lr||
             !(stage_>=12u?caller_return_registers_held(c):return_registers_held())))||
           gp_[2]!=incoming_[2]||gp_[13]!=incoming_[13])return false;
        for(auto s:e_.slots){
            const auto a=uint32_t(int64_t(incoming_[1])+s.caller_offset);
            if(c.mmu.read32(a)!=(s.reg==32u?e_.entry_lr:incoming_[s.reg]))return false;
        }
        for(unsigned r=14;r<32u;++r)if(gp_[r]!=incoming_[r]&&
            !(stage_>=12u&&(caller_modified_mask_&(uint32_t(1)<<r)))&&
            std::none_of(e_.slots.begin(),e_.slots.end(),[&](auto s){return s.reg==r;}))return false;
        return true;
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx;}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>static bool mapped(C& c,AllocatorRange a){
        if(!a.size||a.base<0x80000000u||a.end()>0x81800000ull)return false;
        auto p=c.mmu.get_ptr(a.base),q=c.mmu.get_ptr(uint32_t(a.end()-1u));
        return p&&q&&reinterpret_cast<uintptr_t>(q)==reinterpret_cast<uintptr_t>(p)+a.size-1u;
    }
    template<class C>static bool word(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,{a,4})&&c.mmu.read32(a)==w;}
    template<class C>bool common(C& c,bool held,bool pre_branch=false,std::optional<uint32_t> arrival_lr={})const{
        if(error_||!held||cpu_!=&c||!safe(c)||c.gpr!=gp_||c.gqr!=gqr_||c.msr!=msr_||
           pack(c)!=cr_||c.lr!=(arrival_lr?*arrival_lr:lr_)||c.ctr!=(pre_branch?poll_ctr_:ctr_)||c.xer!=xer_||c.srr0!=srr0_||c.srr1!=srr1_||!mapped(c,frame_))return false;
        for(unsigned i=0;i<shadow_.size();++i)if(c.mmu.read8(frame_.base+i)!=shadow_[i])return false;
        return true;
    }
};
}
