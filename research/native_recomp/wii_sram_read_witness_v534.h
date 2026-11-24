#pragma once
#include "wii_si_discovery_witness_v529.h"
#include "wii_exi_mx_device_v494.h"
namespace undercover::wii {
// Independent deterministic nonzero SRAM profile. This is not a real console
// dump, identity, or persistent configuration. GBS uses the V60 no-write path.
inline constexpr uint32_t SramGuest=0x806f52c0u;
inline constexpr ExiMxDevice::Sram sram_read_fixture(){
    ExiMxDevice::Sram bytes{};
    for(unsigned i=0;i<bytes.size();++i)bytes[i]=uint8_t(17u*i+7u);
    bytes[60]=0x12;bytes[61]=0;return bytes;
}
class SramCompletionTrace{
public:
    bool begin(bool bound){
        if(!bound||active_||bad_||count_)return false;
        active_=true;return true;
    }
    void record(const ExiController::Request& q,const ExiController& ctl,
                const ExiMxDevice& mx) {
        if(!active_)return;
        if(count_>=2||q.channel!=0||q.device!=1||!q.token||q.token<=token_||
           mx.dirty()||mx.sram()!=sram_read_fixture()||ctl.pending(0)||
           (ctl.read(0,0)&0x380u)!=0x100u||
           !(ctl.read(0,0)&WiiIrqBanks::TC_INT)){bad_=true;return;}
        const auto epoch=ctl.selection_epoch(0);
        if(!count_){
            if(q.dma||q.direction!=1||q.length!=4||q.tx!=0x20000100u||
               ctl.read(0,12)!=0x34u){bad_=true;return;}
            epoch_=epoch;
        }else if(!q.dma||q.direction!=0||q.length!=64||
                 q.physical!=(SramGuest&0x3fffffffu)||epoch!=epoch_||
                 ctl.read(0,12)!=2u){bad_=true;return;}
        token_=q.token;++count_;
    }
    unsigned count()const noexcept{return count_;}
    bool good()const noexcept{return active_&&!bad_;}
    bool finish()noexcept{const bool ok=good()&&count_==2;active_=false;return ok;}
private:unsigned count_=0;uint64_t token_=0,epoch_=0;bool active_=false,bad_=false;
};
inline thread_local SramCompletionTrace sram_completion{};
struct SramReadExpectations{VectorEdge entry;std::array<VectorEdge,11> edges;uint32_t return_word;};
// Read-only observer. No guest RAM, register, cache counter, or device state
// is changed by these checks. The final stop is before the next OSInit opcode.
class SramReadWitness{
public:
    explicit SramReadWitness(const SramReadExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c,bool bound){
        if(stage_||error_||!c.is_running||!matches(c,e_.entry)||
           c.gpr[1]<0x80001000u||(c.msr&0x8000u)||
           !equal(c,c.gpr[13]-3824u,exi_id_completion.id())||
           !equal(c,0x806f156cu,0)||!mapped(c,SramGuest,80)||
           c.guest_data_invalidate_count>c.guest_data_invalidate_lines.size()-2||
           !sram_completion.begin(bound))return fail(1);
        for(unsigned i=0;i<80;++i)if(c.mmu.read8(SramGuest+i))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        cache_=c.guest_data_invalidate_count;
        for(unsigned i=0;i<18;++i)nv_[i]=c.gpr[14+i];
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>12||!c.is_running||c.inst_count<last_||
           c.inst_count-last_>2000000u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||
           !sram_completion.good()||!equal(c,r13_-3824u,exi_id_completion.id()))return fail(2);
        if(addr==Return){
            if(stage_!=12||!equal(c,Return,e_.return_word)||c.lr!=Return||
               c.gpr[1]!=sp_||c.msr!=msr_||!cache_ok(c)||!payload(c)||
               !equal(c,SramGuest+64,64)||!equal(c,SramGuest+68,0)||
               !equal(c,SramGuest+72,0)||!equal(c,SramGuest+76,1)||
               !equal(c,0x806f156cu,0)||!equal(c,0x806f1570u,0)||
               !equal(c,0x806f1574u,command_)||!equal(c,0x806f1578u,1)||
               !sram_completion.finish())return fail(6);
            for(unsigned i=0;i<18;++i)if(c.gpr[14+i]!=nv_[i])return fail(6);
            stage_=13;return true;
        }
        if(stage_<12&&matches(c,e_.edges[stage_-1])){
            if(c.msr!=msr_||c.gpr[1]>=sp_||c.gpr[1]<sp_-1024u)return fail(3);
            const auto ch=c.gpr[3],arg=c.gpr[4],length=c.gpr[5],direction=c.gpr[6],cb=c.gpr[7];
            switch(stage_){
            case 1:
                if(ch!=SramGuest||arg!=64||c.guest_data_invalidate_count!=cache_)return fail(4);
                break;
            case 2:
                if(ch!=0||arg!=1||length!=0||!cache_ok(c)||sram_completion.count()!=0)return fail(4);
                break;
            case 3:
                if(ch!=0||arg!=1||length!=3||!equal(c,0x806f156cu,0x10))return fail(4);
                break;
            case 4:
                if(ch!=0||length!=4||direction!=1||cb!=0||!equal(c,arg,0x20000100u)||
                   !equal(c,0x806f156cu,0x14)||sram_completion.count()!=0)return fail(4);
                command_=arg;break;
            case 5:
                if(ch!=0||!equal(c,0x806f156cu,0x16))return fail(4);
                break;
            case 6:
                if(ch!=0||arg!=SramGuest||length!=64||direction||cb||!cache_ok(c)||
                   !equal(c,0x806f156cu,0x14)||sram_completion.count()!=1)return fail(5);
                for(unsigned i=0;i<64;++i)if(c.mmu.read8(SramGuest+i))return fail(5);
                break;
            case 7:
                if(ch!=0||!equal(c,0x806f156cu,0x15))return fail(5);
                break;
            case 8:
                if(ch!=0||!equal(c,0x806f156cu,0x14)||sram_completion.count()!=2||!payload(c))return fail(5);
                break;
            case 9:
                if(ch!=0||!equal(c,0x806f156cu,0x10)||sram_completion.count()!=2)return fail(5);
                break;
            case 10:case 11:
                if(ch!=0||arg!=20||!equal(c,SramGuest+72,1)||!equal(c,SramGuest+76,1)||
                   !equal(c,0x806f156cu,0)||!payload(c))return fail(5);
                break;
            }
            ++stage_;last_=c.inst_count;return true;
        }
        if(addr!=c.pc||addr&3u||!mapped(c,addr,4)||++extra_>1024u||
           addr==0x80528974u||addr==0x80548798u||addr==0x80531b34u||
           addr==0x80528754u)return fail(7);
        for(auto e:e_.edges)if(addr==e.pc&&c.lr==e.lr)return fail(7);
        return true;
    }
private:
    static constexpr uint32_t Return=0x805208d0u;
    SramReadExpectations e_;unsigned stage_=0,error_=0,extra_=0,cache_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,command_=0;uint64_t last_=0;
    std::array<uint32_t,18> nv_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);}
    template<class Cpu>bool cache_ok(Cpu& c)const{
        return c.guest_data_invalidate_count==cache_+2&&c.guest_data_invalidate_lines[cache_]==SramGuest&&
               c.guest_data_invalidate_lines[cache_+1]==SramGuest+32;
    }
    template<class Cpu>static bool payload(Cpu& c){
        if(!mapped(c,SramGuest,64))return false;
        constexpr auto bytes=sram_read_fixture();
        for(unsigned i=0;i<bytes.size();++i)if(c.mmu.read8(SramGuest+i)!=bytes[i])return false;
        return true;
    }
};
}
