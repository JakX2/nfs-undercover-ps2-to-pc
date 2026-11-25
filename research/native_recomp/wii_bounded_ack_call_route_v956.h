#pragma once
#include <array>
#include <cstdint>
#include <span>
namespace undercover::wii {
struct AckCallSpan{uint32_t root,end;};
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
        if(cpu_||error_||spans.empty()||spans.size()>8||edges.empty()||edges.size()>8||msr_sites.size()>4||
           c.pc!=spans[0].root||!safe(c))return fail(1);
        for(unsigned i=0;i<spans.size();++i){
            const auto s=spans[i];
            if((s.root|s.end)&3u||s.root<0x80000000u||s.end>0x81800000u||s.end<=s.root||
               s.end-s.root>4096u)return fail(1);
            for(unsigned j=0;j<i;++j)if(s.root<spans[j].end&&spans[j].root<s.end)return fail(1);
        }
        for(unsigned i=0;i<edges.size();++i){
            const auto e=edges[i];const auto s=owner(spans,e.site),d=owner(spans,e.target);
            if(s>=spans.size()||d>=spans.size()||s==d||e.target!=spans[d].root||
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
    template<class C>bool before(C& c,uint32_t pc,uint32_t w){
        if(!same(c)||pending_entry_||(pc&3u))return fail(2);
        if(pending_return_){
            if(!depth_)return fail(3);
            const auto& f=stack_[depth_-1];
            if(pc!=f.ret||c.gpr[1]!=f.gp[1]||c.gpr[2]!=f.gp[2]||c.gpr[13]!=f.gp[13]||c.lr!=f.ret)return fail(3);
            for(unsigned i=14;i<32;++i)if(c.gpr[i]!=f.gp[i])return fail(3);
            active_=f.caller;--depth_;++returns_;pending_return_=false;
        }
        if(owner(spans_,pc)!=active_||(next_&&pc!=next_))return fail(2);
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
    bool can_poll()const{return cpu_&&!error_&&!pending_entry_&&!pending_return_&&!msr_pending_;}
private:
    struct Frame{uint32_t ret=0;unsigned caller=0;std::array<uint32_t,32> gp{};};
    std::array<Frame,8> stack_{};
    std::span<const AckCallSpan> spans_;std::span<const AckCallEdge> edges_;std::span<const AckMsrSite> msr_sites_;
    const void* cpu_=nullptr;unsigned active_=0,depth_=0,entries_=0,returns_=0,error_=0;
    uint32_t pending_entry_=0,next_=0,msr_=0;bool pending_return_=false,msr_pending_=false;unsigned msr_writes_=0;
    bool fail(unsigned e){if(!error_)error_=e;return false;}
    static unsigned owner(std::span<const AckCallSpan> ss,uint32_t pc){
        for(unsigned i=0;i<ss.size();++i)if(pc>=ss[i].root&&pc<ss[i].end&&!(pc&3u))return i;
        return unsigned(ss.size());
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool same(C& c)const{return !error_&&cpu_==&c&&safe(c)&&c.msr==msr_;}
};
}
