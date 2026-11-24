#pragma once
#include <array>
#include <cstdint>

namespace undercover::wii {
struct VectorEdge {uint32_t pc,lr,branch_word,entry_word;};
struct VectorExpectations {
    std::array<VectorEdge,32> edges;
    unsigned count;
    std::array<uint32_t,15> offsets;
    std::array<uint8_t,152> handler;
    uint32_t stop_word;
};
// First unmarked vector only, following original unmodified OSExceptionInit.
// No guest memory or register is changed by the observer.
class FirstVectorWitness {
public:
    explicit FirstVectorWitness(const VectorExpectations& e):e_(e){}
    unsigned stage() const{return stage_;}
    unsigned failure() const{return failure_;}
    unsigned prelude() const{return prelude_;}
    bool active() const{return begun_&&stage_<4&&!failure_;}
    bool debug_needed() const{return debug_needed_;}
    template<class Cpu> bool begin(Cpu& c){
        if(begun_||failure_||!c.is_running||c.pc!=Entry||c.lr!=0x805208acu||
           c.gpr[13]!=0x8070e8e0u||(c.msr&0x8000u)||c.gpr[1]<0x80000100u||
           c.gpr[1]>0x817ffff8u||e_.count==0||e_.count>e_.edges.size())return fail(1);
        for(unsigned i=0;i<15;++i){
            const uint32_t a=e_.offsets[i];
            if(a<0x100u||a>0x3000u-152u||(a&31u)||!equal(c,Table+i*4u,a))return fail(2);
            for(unsigned j=0;j<i;++j)if(a<e_.offsets[j]+152u&&e_.offsets[j]<a+152u)return fail(2);
        }
        if(!mapped(c,Source,152)||!mapped(c,0x80000060u,4))return fail(2);
        for(unsigned i=0;i<152;++i)if(c.mmu.read8(Source+i)!=e_.handler[i])return fail(3);
        dest_=0x80000000u+e_.offsets[0];sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        debug_needed_=c.mmu.read32(0x80000060u)==0;begun_=true;return true;
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(!active()||!c.is_running||c.pc!=addr||c.inst_count<=last_||
           c.gpr[1]!=sp_-64u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||c.msr!=msr_)return fail(4);
        for(unsigned i=0;i<15;++i)if(!equal(c,Table+4u*i,e_.offsets[i]))return fail(2);
        if(stage_==3){
            if(addr!=Stop||c.lr!=Stop||!equal(c,Stop,e_.stop_word)||!copied(c)||!cache(c,5,5,2,1))return fail(9);
            ++stage_;last_=c.inst_count;return true;
        }
        bool edge=false;
        for(unsigned i=0;i<e_.count;++i){
            const auto& x=e_.edges[i];
            if(x.pc==addr&&x.lr==c.lr&&equal(c,addr,x.entry_word)&&equal(c,x.lr-4u,x.branch_word)){edge=true;break;}
        }
        if(!edge)return fail(5);
        if(stage_==0){
            if(!prelude_&&(addr!=0x805450e8u||c.lr!=Entry+20u))return fail(5);
            if(addr!=Copy||c.lr!=0x80520d9cu){
                if(prelude_>=24||c.lr>0x80520d9cu)return fail(5);
                ++prelude_;last_=c.inst_count;return true;
            }
            if(c.gpr[3]!=dest_||c.gpr[4]!=Source||c.gpr[5]!=152u||c.gpr[29]!=0||
               !equal(c,sp_+4u,0x805208acu)||!mapped(c,dest_-1u,154)||!mapped(c,Source,152))return fail(6);
            if(!mapped(c,r13_-4160u,4))return fail(6);
            const uint32_t db=c.mmu.read32(r13_-4160u);
            if(!mapped(c,db,8)||(c.mmu.read32(db+4u)&1u))return fail(6);
            // Index zero is unmarked. Original template-clear loop changes
            // precisely one word; index-zero mark insertion preserves its word.
            for(unsigned i=0;i<152;++i){
                const uint8_t v=c.mmu.read8(Source+i);
                const uint8_t expected=(i>=0x58u&&i<0x5cu)?(i==0x58u?0x60u:0u):e_.handler[i];
                if(v!=expected)return fail(7);
                source_[i]=v;
            }
            before_=c.mmu.read8(dest_-1u);after_=c.mmu.read8(dest_+152u);
            flush_=c.guest_flush_count;ic_=c.guest_invalidate_count;
            sync_=c.guest_sync_count;isync_=c.guest_isync_count;
            if(uint64_t(flush_)+5u>c.guest_flush_lines.size()||uint64_t(ic_)+5u>c.guest_invalidate_lines.size())return fail(10);
            ++stage_;
        }else if(stage_==1){
            if(addr!=Flush||c.lr!=0x80520da8u||c.gpr[3]!=dest_||c.gpr[4]!=152u||!copied(c)||!cache(c,0,0,0,0))return fail(8);
            ++stage_;
        }else{
            if(addr!=Invalidate||c.lr!=Stop||c.gpr[3]!=dest_||c.gpr[4]!=152u||!copied(c)||!cache(c,5,0,1,0))return fail(9);
            ++stage_;
        }
        last_=c.inst_count;return true;
    }
private:
    static constexpr uint32_t Entry=0x80520bf4u,Source=0x80520ec0u,Table=0x8060bbe0u;
    static constexpr uint32_t Copy=0x80004338u,Flush=0x80522320u,Invalidate=0x80522378u,Stop=0x80520db8u;
    VectorExpectations e_;
    unsigned stage_=0,failure_=0,prelude_=0;bool begun_=false,debug_needed_=false;
    uint32_t dest_=0,sp_=0,r2_=0,r13_=0,msr_=0,flush_=0,ic_=0,sync_=0,isync_=0;
    uint64_t last_=0;uint8_t before_=0,after_=0;
    std::array<uint8_t,152> source_{};
    bool fail(unsigned n){if(!failure_)failure_=n;return false;}
    template<class Cpu> static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu> static bool equal(Cpu& c,uint32_t a,uint32_t v){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==v;}
    template<class Cpu> bool copied(Cpu& c) const{
        if(!mapped(c,dest_-1u,154)||!mapped(c,Source,152)||c.mmu.read8(dest_-1u)!=before_||c.mmu.read8(dest_+152u)!=after_)return false;
        for(unsigned i=0;i<152;++i)if(c.mmu.read8(Source+i)!=source_[i]||c.mmu.read8(dest_+i)!=source_[i])return false;
        return true;
    }
    template<class Cpu> bool cache(Cpu& c,unsigned f,unsigned i,unsigned s,unsigned is) const{
        if(uint64_t(c.guest_flush_count)!=uint64_t(flush_)+f||uint64_t(c.guest_invalidate_count)!=uint64_t(ic_)+i||
           uint64_t(c.guest_sync_count)!=uint64_t(sync_)+s||uint64_t(c.guest_isync_count)!=uint64_t(isync_)+is)return false;
        for(unsigned n=0;n<f;++n)if(c.guest_flush_lines[flush_+n]!=dest_+32u*n)return false;
        for(unsigned n=0;n<i;++n)if(c.guest_invalidate_lines[ic_+n]!=dest_+32u*n)return false;
        return true;
    }
};
}
