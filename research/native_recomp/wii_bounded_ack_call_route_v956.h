#pragma once
#include <array>
#include <cstdint>
#include <span>
namespace undercover::wii {
struct AckCallSpan{uint32_t root,end;unsigned save_suffix=0,restore_first=0;};
struct AckCallEdge{uint32_t site,target;};
struct AckMsrSite{uint32_t pc,word;};
// Read-only native entry/return witness. It does not emulate any branch,
// alter the stack, or manufacture a return. All spans and edges are
// authenticated independently by the private original-code installer.
class BoundedAckCallRoute {
public:
    unsigned failure()const{return error_;}
    unsigned entries()const{return entries_;}
    unsigned returns()const{return returns_;}
    unsigned depth()const{return depth_;}
    unsigned msr_writes()const{return msr_writes_;}
    template<class C>bool begin(C& c,std::span<const AckCallSpan> spans,std::span<const AckCallEdge> edges,std::span<const AckMsrSite> msr_sites={}){
        if(cpu_||error_||spans.empty()||spans.size()>12||edges.empty()||edges.size()>16||msr_sites.size()>4||
           c.pc!=spans[0].root||!safe(c))return fail(1);
        for(unsigned i=0;i<spans.size();++i){
            const auto s=spans[i];
            if((s.root|s.end)&3u||s.root<0x80000000u||s.end>0x81800000u||s.end<=s.root||
               s.end-s.root>4096u||s.save_suffix>1u||
               (s.restore_first&&(s.restore_first<14u||s.restore_first>31u||s.save_suffix||
                s.end-s.root!=4u*(33u-s.restore_first))))return fail(1);
            if(s.save_suffix&&(s.end-s.root<8u||s.end-s.root>76u))return fail(1);
            for(unsigned j=0;j<i;++j)if(s.root<spans[j].end&&spans[j].root<s.end){
                // An explicitly authenticated compiler save suffix may
                // share an ending with another independently emitted root.
                if(!s.save_suffix||!spans[j].save_suffix||s.end!=spans[j].end||s.root==spans[j].root)return fail(1);
            }
        }
        for(unsigned i=0;i<edges.size();++i){
            const auto e=edges[i];const auto s=owner(spans,e.site),d=owner(spans,e.target);
            if(s>=spans.size()||d>=spans.size()||s==d||e.target!=spans[d].root||spans[s].save_suffix||spans[s].restore_first||
               e.site+4u>=spans[s].end)return fail(1);
            for(unsigned j=0;j<i;++j)if(edges[j].site==e.site)return fail(1);
        }
        for(unsigned i=0;i<msr_sites.size();++i){
            const auto m=msr_sites[i];const auto o=owner(spans,m.pc);
            if(o>=spans.size()||m.pc+4u>=spans[o].end||(m.word>>26)!=31u||((m.word>>1)&1023u)!=146u)return fail(1);
            for(unsigned j=0;j<i;++j)if(msr_sites[j].pc==m.pc)return fail(1);
        }
        cpu_=&c;spans_=spans;edges_=edges;msr_sites_=msr_sites;msr_=c.msr;active_=0;next_=spans[0].root;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,uint32_t native_owner=0){
        if(!same(c)||pending_entry_||(pc&3u))return fail(2);
        if(pending_return_){
            if(!depth_)return fail(3);
            const auto& f=stack_[depth_-1];
            if(pc!=f.ret||c.gpr[1]!=f.gp[1]||c.gpr[2]!=f.gp[2]||c.gpr[13]!=f.gp[13]||c.lr!=f.ret)return fail(3);
            const unsigned first=spans_[active_].restore_first?spans_[active_].restore_first:32u;
            for(unsigned i=14;i<first;++i)if(c.gpr[i]!=f.gp[i])return fail(3);
            active_=f.caller;--depth_;++returns_;pending_return_=false;
        }
        if(active_>=spans_.size()||pc<spans_[active_].root||pc>=spans_[active_].end||
           (native_owner&&native_owner!=spans_[active_].root)||(next_&&pc!=next_))return fail(2);
        next_=0;msr_pending_=false;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        const bool link=(w&1u)&&(op==16u||op==18u||(op==19u&&(xo==16u||xo==528u)));
        for(const auto e:edges_)if(e.site==pc){
            const uint32_t d=((w&0x03fffffcu)^0x02000000u)-0x02000000u;
            if(op!=18u||(w&3u)!=1u||pc+d!=e.target||depth_==stack_.size())return fail(4);
            stack_[depth_++]={pc+4u,active_,c.gpr};
            pending_entry_=e.target;return true;
        }
        if(op==31u&&xo==146u){
            bool allowed=false;for(const auto m:msr_sites_)if(m.pc==pc&&m.word==w)allowed=true;
            if(!allowed||c.gpr[(w>>21)&31u]!=msr_)return fail(4);
            ++msr_writes_;next_=pc+4u;msr_pending_=true;return true;
        }
        if(link||op==17u||(op==19u&&(xo==50u||xo==528u||(xo==16u&&w!=0x4e800020u))))return fail(4);
        if(w==0x4e800020u){
            if(!depth_||c.lr!=stack_[depth_-1].ret)return fail(3);
            pending_return_=true;
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc){
        if(!same(c)||!pending_entry_||!depth_||pc!=pending_entry_||c.pc!=pc||c.lr!=stack_[depth_-1].ret)return fail(5);
        active_=owner(spans_,pc);if(active_>=spans_.size())return fail(5);
        next_=pc;pending_entry_=0;++entries_;return true;
    }
    // Verify an authenticated but deliberately unexecuted direct call at
    // the handler root. No call stack is created and no guest state changes.
    template<class C>bool stop_before_direct(C& c,uint32_t pc,uint32_t w){
        const uint32_t d=((w&0x03fffffcu)^0x02000000u)-0x02000000u;
        const uint32_t dst=pc+d;
        if(!same(c)||!can_poll()||depth_||active_||next_||pc<spans_[0].root||
           pc>=spans_[0].end||(pc&3u)||(w>>26)!=18u||(w&3u)!=1u||
           dst<0x80000000u||dst>=0x81800000u||dst==pc)return fail(4);
        for(const auto e:edges_)if(e.site==pc)return fail(4);
        return true;
    }
    template<class C>bool stop_before_indirect(C& c,uint32_t pc,uint32_t w){
        if(!same(c)||!can_poll()||depth_||active_||next_||pc<spans_[0].root||
           pc>=spans_[0].end||(pc&3u)||w!=0x4e800421u)return fail(4);
        for(const auto e:edges_)if(e.site==pc)return fail(4);
        return true;
    }
    bool can_poll()const{return cpu_&&!error_&&!pending_entry_&&!pending_return_&&!msr_pending_;}
private:
    struct Frame{uint32_t ret=0;unsigned caller=0;std::array<uint32_t,32> gp{};};
    std::array<Frame,8> stack_{};
    std::span<const AckCallSpan> spans_;std::span<const AckCallEdge> edges_;std::span<const AckMsrSite> msr_sites_;
    const void* cpu_=nullptr;unsigned active_=0,depth_=0,entries_=0,returns_=0,error_=0;
    uint32_t pending_entry_=0,next_=0,msr_=0;bool pending_return_=false,msr_pending_=false;unsigned msr_writes_=0;
    bool fail(unsigned e){if(!error_)error_=e;return false;}
    static unsigned owner(std::span<const AckCallSpan> ss,uint32_t pc){
        for(unsigned i=0;i<ss.size();++i)if(pc==ss[i].root)return i;
        for(unsigned i=0;i<ss.size();++i)if(pc>=ss[i].root&&pc<ss[i].end&&!(pc&3u))return i;
        return unsigned(ss.size());
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool same(C& c)const{return !error_&&cpu_==&c&&safe(c)&&c.msr==msr_;}
};
}
