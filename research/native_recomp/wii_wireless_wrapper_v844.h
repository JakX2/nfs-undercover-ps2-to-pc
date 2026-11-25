#pragma once
#include <array>
#include <cstdint>
#include <span>
namespace undercover::wii {
struct WirelessCode{uint32_t root;std::span<const uint32_t> words;};
struct WirelessEdge{uint32_t site,word,resume_word;unsigned ordinal;};
struct WirelessExpectation{
    // Setter, getter, UnlockSram, OSDisableInterrupts, OSRestoreInterrupts.
    std::array<WirelessCode,5> code;
    std::array<WirelessEdge,2> edges;
    uint32_t lock,lock_word,sram;
};
struct WirelessRestoreRule{uint32_t root;unsigned count,base;int32_t disp;};
struct WirelessWriteExtension{
    std::span<const WirelessCode> code;
    std::span<const WirelessRestoreRule> restores;
    uint32_t revision,revision_read,exi_state;
};
// Read-only observer for the original wrappers. No host/device writes,
// no successful EXI stub. The changed lane stops at real EXILock entry.
class WirelessWrapperWitness{
public:
    explicit WirelessWrapperWitness(WirelessExpectation e):e_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned writes()const{return writes_;}
    unsigned ordinal()const{return ordinal_;}
    bool changed()const{return changed_;}
    bool extended()const{return extended_;}
    unsigned polls()const{return polls_;}
    unsigned mmio()const{return mmio_;}
    const std::array<uint8_t,64>& initial_payload()const{return initial_;}
    const std::array<uint8_t,64>& desired_payload()const{return desired_;}
    unsigned channel()const{return channel_;}
    uint32_t returning_root()const{return returned_&&depth_?frames_[depth_-1].root:0u;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,bool frontier,bool held){
        if(stage_||error_||!frontier||!held||!safe(c)||c.gpr[3]>3u||c.gpr[1]<0x80000400u||
           c.gpr[1]>0x817fff00u||(c.gpr[1]&3u)||c.inst_count>UINT64_MAX-320u||
           !mapped(c,e_.sram,80u)||!metadata(c,64,0,1)||!match(c,pc,w)||!match(c,e_.lock,e_.lock_word))return fail(1);
        const WirelessEdge* edge=nullptr;
        unsigned mask=0;
        for(auto& x:e_.edges){
            if((x.ordinal!=3u&&x.ordinal!=5u)||(mask&(1u<<x.ordinal))||
               !match(c,x.site,x.word)||!match(c,x.site+4u,x.resume_word)||
               !direct(x.site,x.word,e_.code[x.ordinal==3u?0u:1u].root))return fail(1);
            mask|=1u<<x.ordinal;if(x.site==pc&&x.word==w)edge=&x;
        }
        if(!edge||mask!=((1u<<3)|(1u<<5))||(edge->ordinal==3u&&c.gpr[4]>0xffffu))return fail(1);
        constexpr std::array<unsigned,5> extents{39,30,184,5,9};
        for(unsigned i=0;i<5;++i){
            const auto& f=e_.code[i];
            if(f.words.size()!=extents[i]||!mapped(c,f.root,4u*extents[i])||
               (f.root&3u)||f.root==e_.lock)return fail(1);
            for(unsigned j=0;j<i;++j)if(overlap(f.root,4u*extents[i],e_.code[j].root,4u*extents[j]))return fail(1);
            for(unsigned j=0;j<f.words.size();++j)if(!match(c,f.root+4u*j,f.words[j]))return fail(1);
        }
        for(unsigned i=0;i<64;++i)initial_[i]=c.mmu.read8(e_.sram+i);
        desired_=initial_;channel_=c.gpr[3];ordinal_=edge->ordinal;resume_=pc+4u;resume_word_=edge->resume_word;
        const unsigned at=48u+2u*channel_;initial_id_=(unsigned(initial_[at])<<8)|initial_[at+1u];
        if(ordinal_==3u){desired_[at]=uint8_t(c.gpr[4]>>8);desired_[at+1u]=uint8_t(c.gpr[4]);}
        changed_=desired_!=initial_;
        cpu_=&c;sp_=c.gpr[1];msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;last_=c.inst_count;
        next_=e_.code[ordinal_==3u?0u:1u].root;
        frames_[depth_++]={next_,resume_,c.gpr,pack(c)&0x00fff000u};
        entry_due_=true;stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,bool held){
        if(!common(c,held)||!entry_due_||!depth_||pc!=next_||c.pc!=pc||c.inst_count!=last_||c.lr!=frames_[depth_-1].ret)return fail(2);
        entry_due_=false;
        if(pc==e_.code[3].root)++disables_;
        if(pc==e_.code[4].root)++restores_;
        if(pc==e_.code[2].root){
            if(++unlocks_!=1u||c.gpr[3]!=unsigned(changed_)||c.gpr[4]!=20u||
               !metadata(c,64,1,1)||!payload(c,desired_))return fail(3);
        }
        if(pc==e_.lock){
            if(extended_)return fail(3);
            if(!changed_||ordinal_!=3u||depth_!=3u||unlocks_!=1u||disables_!=1u||restores_||
               c.gpr[3]!=0u||c.gpr[4]!=1u||!c.gpr[5]||(c.gpr[5]&3u)||
               c.gpr[5]<0x80000000u||c.gpr[5]>0x817ffffcu||
               !match(c,pc,e_.lock_word)||!metadata(c,20,1,1)||!payload(c,desired_))return fail(3);
            stage_=3;return true;
        }
        return true;
    }
    // Explicit opt-in handoff at the authenticated EXILock entry. This
    // retains the real caller frames, exact tick and already checked stores.
    // The external device observer must independently prove the transaction.
    template<class C>bool continue_write(C& c,WirelessWriteExtension ext,bool held){
        if(stage_!=3u||error_||extended_||!held||cpu_!=&c||!safe(c)||
           c.msr!=msr_||c.srr0!=srr0_||c.srr1!=srr1_||c.inst_count!=last_||
           c.pc!=e_.lock||next_!=e_.lock||depth_!=3u||entry_due_||returned_||pending_||
           !changed_||ordinal_!=3u||ext.code.empty()||ext.code.size()>32u||
           ext.restores.size()>16u||!ext.revision||ext.exi_state!=0x806f1560u||
           (ext.revision_read&3u)||((ext.revision_read&0x3fffffffu)!=0x0d006024u&&
            (ext.revision_read&0x3fffffffu)!=0x0d806024u)||
           c.inst_count>UINT64_MAX-12000u)return fail(8);
        bool lock=false,rev=false;
        for(unsigned i=0;i<ext.code.size();++i){
            const auto& f=ext.code[i];
            if(f.words.empty()||f.words.size()>1024u||!mapped(c,f.root,4u*unsigned(f.words.size()))||
               (f.root&3u))return fail(8);
            if(f.root==e_.lock){lock=true;if(f.words.front()!=e_.lock_word)return fail(8);}
            if(f.root==ext.revision)rev=true;
            for(auto& b:e_.code)if(overlap(f.root,4u*unsigned(f.words.size()),b.root,4u*unsigned(b.words.size())))return fail(8);
            for(unsigned j=0;j<i;++j){
                const auto& b=ext.code[j];
                if(f.root==b.root)return fail(8);
                if(overlap(f.root,4u*unsigned(f.words.size()),b.root,4u*unsigned(b.words.size()))){
                    const auto& lo=f.root<b.root?f:b;const auto& hi=f.root<b.root?b:f;
                    if(uint64_t(lo.root)+4u*lo.words.size()!=uint64_t(hi.root)+4u*hi.words.size())return fail(8);
                    for(unsigned k=0;k<hi.words.size();++k)
                        if(lo.words[(hi.root-lo.root)/4u+k]!=hi.words[k])return fail(8);
                }
            }
            for(unsigned j=0;j<f.words.size();++j)if(!match(c,f.root+4u*j,f.words[j]))return fail(8);
        }
        if(!lock||!rev)return fail(8);
        for(unsigned i=0;i<ext.restores.size();++i){
            const auto& r=ext.restores[i];const WirelessCode* f=nullptr;
            for(auto& x:ext.code)if(x.root==r.root)f=&x;
            if(!f||!r.count||r.count>18u||(r.base!=1u&&r.base!=11u)||f->words.size()!=r.count+1u||
               f->words.back()!=0x4e800020u)return fail(8);
            for(unsigned j=0;j<i;++j)if(ext.restores[j].root==r.root)return fail(8);
            for(unsigned k=0;k<r.count;++k){
                const uint32_t w=f->words[k];
                if(w>>26!=32u||((w>>21)&31u)!=32u-r.count+k||((w>>16)&31u)!=r.base||
                   int32_t(int16_t(w&0xffffu))!=r.disp+int32_t(4u*k))return fail(8);
            }
        }
        ext_=ext;extended_=true;stage_=1u;return true;
    }
    template<class C>bool poll(C& c,bool held){
        if(!extended_||!common(c,held)||!backward_||pending_||c.inst_count!=last_||
           c.pc!=poll_pc_||c.gpr!=poll_gp_||c.lr!=poll_lr_||c.ctr!=poll_ctr_||
           c.xer!=poll_xer_||pack(c)!=poll_cr_||++polls_>4096u)return fail(9);
        backward_=false;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool held){
        if(!common(c,held)||entry_due_||backward_||!depth_||pc!=next_||c.inst_count-last_!=1u||
           ++visits_>(extended_?12000u:320u)||!match(c,pc,w))return fail(4);
        last_=c.inst_count;
        if(pending_){
            for(unsigned i=0;i<pending_;++i)
                if(!mapped(c,store_addr_+i,1)||c.mmu.read8(store_addr_+i)!=store_[i])return fail(5);
            pending_=0;
        }
        if(returned_){
            if(c.pc!=pc||c.lr!=pc||!abi(c,frames_[depth_-1]))return fail(6);
            --depth_;returned_=false;
            if(!depth_){
                if(changed_!=extended_||pc!=resume_||w!=resume_word_||unlocks_!=1u||
                   (!extended_&&(disables_!=1u||restores_!=1u))||(extended_&&disables_!=restores_)||
                   !metadata(c,64,0,1)||!payload(c,changed_?desired_:initial_)||(ordinal_==5u&&c.gpr[3]!=initial_id_))return fail(6);
                stage_=2;return true;
            }
        }
        const auto* f=code(frames_[depth_-1].root);
        if(!f||pc<f->root||uint64_t(pc)>=uint64_t(f->root)+4u*f->words.size()||w!=f->words[(pc-f->root)/4u]||!memory(c,w))return fail(7);
        next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        if(op==18u&&(w&3u)==1u){
            const auto dst=target(pc,w);
            if((dst!=e_.lock&&!code(dst))||depth_>=frames_.size()||
               (dst==e_.lock&&(!changed_||f->root!=e_.code[2].root)))return fail(7);
            if(extended_&&dst==e_.lock)return fail(7);
            frames_[depth_++]={dst,pc+4u,c.gpr,pack(c)&0x00fff000u};
            if(extended_)for(auto rule:ext_.restores)if(rule.root==dst){
                for(unsigned i=0;i<rule.count;++i){
                    const uint32_t a=c.gpr[rule.base]+uint32_t(rule.disp)+4u*i;
                    if(!within(a,4u,sp_-0x800u,sp_+0x100u)||!mapped(c,a,4u)||(a&3u))return fail(8);
                    frames_[depth_-1].gp[32u-rule.count+i]=c.mmu.read32(a);
                }
            }
            next_=dst;entry_due_=true;return true;
        }
        if(w==0x4e800020u){
            if(c.lr!=frames_[depth_-1].ret)return fail(6);
            next_=c.lr;returned_=true;return true;
        }
        if(op==16u||op==18u){
            const uint32_t dst=target(pc,w);
            if((w&3u)||(!extended_&&dst<=pc)||dst<f->root||uint64_t(dst)>=uint64_t(f->root)+4u*f->words.size())return fail(7);
            if(dst<=pc){backward_=true;poll_pc_=pc;poll_gp_=c.gpr;poll_lr_=c.lr;poll_ctr_=c.ctr;poll_xer_=c.xer;poll_cr_=pack(c);}
            if(op==18u||taken(c,w))next_=dst;
        }else if(op==17u||(op==19u&&(xo==16u||xo==50u||xo==528u))||
                 (op==31u&&xo==146u&&f->root!=e_.code[3].root&&f->root!=e_.code[4].root))return fail(7);
        return next_>=f->root&&uint64_t(next_)<uint64_t(f->root)+4u*f->words.size()?true:fail(7);
    }
private:
    struct Frame{uint32_t root,ret;std::array<uint32_t,32> gp;uint32_t cr;};
    WirelessExpectation e_;WirelessWriteExtension ext_{};std::array<Frame,16> frames_{};
    std::array<uint8_t,64> initial_{},desired_{};std::array<uint8_t,128> store_{};
    const void* cpu_=nullptr;
    uint32_t sp_=0,msr_=0,srr0_=0,srr1_=0,next_=0,resume_=0,resume_word_=0,store_addr_=0;
    uint64_t last_=0;
    unsigned stage_=0,error_=0,visits_=0,writes_=0,ordinal_=0,channel_=0,initial_id_=0,depth_=0,pending_=0,unlocks_=0,disables_=0,restores_=0;
    bool changed_=false,entry_due_=false,returned_=false,extended_=false,backward_=false;
    unsigned polls_=0,mmio_=0;
    uint32_t poll_pc_=0,poll_lr_=0,poll_ctr_=0,poll_xer_=0,poll_cr_=0;
    std::array<uint32_t,32> poll_gp_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    const WirelessCode* code(uint32_t a)const{for(auto& f:e_.code)if(f.root==a)return &f;if(extended_)for(auto& f:ext_.code)if(f.root==a)return &f;return nullptr;}
    static bool overlap(uint32_t a,unsigned n,uint32_t b,unsigned m){return uint64_t(a)<uint64_t(b)+m&&uint64_t(b)<uint64_t(a)+n;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,bool held)const{return stage_==1u&&!error_&&held&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_;}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||a<0x80000000u||uint64_t(a)+n>0x81800000ull)return false;
        for(unsigned i=0;i<n;++i)if(!c.mmu.get_ptr(a+i))return false;
        return true;
    }
    template<class C>static bool match(C& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class C>bool metadata(C& c,uint32_t off,uint32_t locked,uint32_t ok)const{
        return match(c,e_.sram+64u,off)&&match(c,e_.sram+68u,0u)&&match(c,e_.sram+72u,locked)&&match(c,e_.sram+76u,ok);
    }
    template<class C>bool payload(C& c,const std::array<uint8_t,64>& b)const{
        if(!mapped(c,e_.sram,64))return false;
        for(unsigned i=0;i<64;++i)if(c.mmu.read8(e_.sram+i)!=b[i])return false;
        return true;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(auto f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>static bool abi(C& c,const Frame& f){
        if(c.gpr[1]!=f.gp[1]||c.gpr[2]!=f.gp[2]||c.gpr[13]!=f.gp[13]||(pack(c)&0x00fff000u)!=f.cr)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=f.gp[i])return false;
        return true;
    }
    static uint32_t target(uint32_t pc,uint32_t w){
        const bool s=w>>26==16u;const uint32_t b=s?0xfffcu:0x03fffffcu,v=s?0x8000u:0x02000000u;return pc+(((w&b)^v)-v);
    }
    static bool direct(uint32_t pc,uint32_t w,uint32_t dst){return w>>26==18u&&(w&3u)==1u&&target(pc,w)==dst;}
    template<class C>static bool taken(C& c,uint32_t w){
        const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;
        return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((pack(c)>>(31u-bi))&1u)==bool(bo&8u));
    }
    static bool within(uint32_t a,unsigned n,uint32_t lo,uint32_t hi){return n&&a>=lo&&uint64_t(a)+n<=hi;}
    template<class C>bool memory(C& c,uint32_t w){
        const unsigned op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rb=(w>>11)&31u,rs=(w>>21)&31u;
        const uint32_t base=ra?c.gpr[ra]:0u;
        unsigned n=0;uint32_t a=0;bool write=false,reversed=false,multiple=false;
        if(op>=32u&&op<=47u){
            a=base+((w&0xffffu)^0x8000u)-0x8000u;
            n=op==34u||op==35u||op==38u||op==39u?1u:op>=40u&&op<=45u?2u:4u;
            multiple=op==46u||op==47u;if(multiple)n=4u*(32u-rs);
            write=op==36u||op==37u||op==38u||op==39u||op==44u||op==45u||op==47u;
        }else if(op==31u){
            a=base+c.gpr[rb];
            switch(xo){
            case 23:case 55:case 534:n=4;break;
            case 87:case 119:n=1;break;
            case 279:case 311:case 343:case 375:case 790:n=2;break;
            case 151:case 183:n=4;write=true;break;
            case 215:case 247:n=1;write=true;break;
            case 407:case 439:n=2;write=true;break;
            case 662:n=4;write=true;reversed=true;break;
            case 918:n=2;write=true;reversed=true;break;
            case 20:case 150:case 533:case 597:case 661:case 725:
            case 535:case 567:case 599:case 631:case 663:case 695:case 727:case 759:case 983:
            case 54:case 86:case 246:case 278:case 470:case 982:case 1014:return false;
            default:break;
            }
        }else if(op>=48u||op==4u)return false;
        if(!n)return true;
        if(extended_&&n==4u&&!(a&3u)&&(a&0xc0000000u)!=0x40000000u){
            const uint32_t p=a&0x3fffffffu;
            if(p==0x0c003004u||(p>=0x0d006800u&&p<0x0d00683cu)){
                if(write&&p>=0x0d006800u){
                    const unsigned off=p-0x0d006800u;
                    if(off%20u==0u){if((c.gpr[rs]&0x380u)&&!(off==0u&&(c.gpr[rs]&0x380u)==0x100u))return false;}
                    else if(off!=12u&&off!=16u)return false;
                    if(reversed||multiple)return false;
                }
                return ++mmio_<=4096u;
            }
            if(p==(ext_.revision_read&0x3fffffffu))return !write&&frames_[depth_-1].root==ext_.revision&&++mmio_<=4096u;
        }
        if(!mapped(c,a,n)||(n>1u&&(a&(n==2u?1u:3u)))||
           !(within(a,n,sp_-(extended_?0x800u:0x400u),sp_+0x100u)||within(a,n,e_.sram,e_.sram+80u)||
             (extended_&&(within(a,n,ext_.exi_state,ext_.exi_state+0x100u)||within(a,n,0x800000c0u,0x800000d0u)))))return false;
        if(!write)return true;
        if(++writes_>(extended_?1024u:64u)||n>store_.size())return false;
        for(auto& f:e_.code)if(overlap(a,n,f.root,4u*unsigned(f.words.size())))return false;
        if(extended_)for(auto& f:ext_.code)if(overlap(a,n,f.root,4u*unsigned(f.words.size())))return false;
        store_addr_=a;pending_=n;
        for(unsigned i=0;i<n;++i){
            const unsigned reg=rs+(multiple?i/4u:0u);
            const unsigned shift=multiple?8u*(3u-i%4u):8u*(reversed?i:n-1u-i);
            store_[i]=uint8_t(c.gpr[reg]>>shift);
        }
        return true;
    }
};
}
