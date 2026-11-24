#pragma once
#include "wii_si_sampling_witness_v524.h"
namespace undercover::wii {
// A cold, explicitly absent four-port profile. Observe the native device
// request and its real scheduled completion, not a fabricated guest IRQ.
class SiDiscoveryTrace {
public:
    bool begin()noexcept{if(active_||stage_||bad_)return false;active_=true;return true;}
    void mmio(bool write,unsigned off,uint32_t v)noexcept{
        if(!active_)return;
        const bool ok=(stage_==0&&!write&&off==SiController::Status&&v==0)||
            (stage_==1&&write&&off==SiController::Status&&(v==0||v==0x0f000000u))||
            (stage_==2&&write&&off==SiController::Buffer&&v==0)||
            (stage_==3&&!write&&off==SiController::Control&&v==0)||
            (stage_==4&&write&&off==SiController::Control&&v==0xc0010301u);
        if(!ok){bad_=true;return;}++stage_;
    }
    void completion(const SiController::Request& q,const SiController& ctl,uint64_t tick){
        if(!active_)return;
        if(stage_!=5||q.token!=1||q.channel!=0||q.out_length!=1||q.in_length!=3||
           q.tx[0]!=0||!tick||ctl.pending()||
           ctl.read(SiController::Control)!=0xe0010300u||
           ctl.read(SiController::Status)!=0x08000000u||
           ctl.read(SiController::Buffer)!=0){bad_=true;return;}
        tick_=tick;++stage_;
    }
    bool good()const noexcept{return active_&&!bad_;}
    unsigned stage()const noexcept{return stage_;}
    uint64_t tick()const noexcept{return tick_;}
    bool finish()noexcept{const bool ok=good()&&stage_==6;active_=false;return ok;}
private:unsigned stage_=0;bool active_=false,bad_=false;uint64_t tick_=0;
};
inline thread_local SiDiscoveryTrace si_discovery_trace{};
struct SiDiscoveryExpectations {
    std::array<VectorEdge,4> type;
    VectorEdge transfer,start,sram;
};
class SiDiscoveryWitness {
public:
    explicit SiDiscoveryWitness(const SiDiscoveryExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    template<class Cpu>bool begin(Cpu& c,bool bound){
        if(stage_||error_||!bound||!c.is_running||!matches(c,e_.type[0])||
           c.gpr[1]<0x80001000u||(c.msr&0x8000u)||c.gpr[3]!=0||
           !equal(c,0x800000f8u,243000000u)||!equal(c,0x80619a60u,0xffffffffu)||
           !equal(c,0x80619a78u,8u)||!equal(c,0x806fe340u,0xffffffffu))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=c.inst_count;
        if(!equal(c,r13_-3148u,0)||!equal(c,r13_-3136u,0)||
           !equal(c,0x80003090u,0x80531b34u)||!si_discovery_trace.begin())return fail(1);
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||stage_<1||stage_>12||!c.is_running||c.inst_count<last_||
           c.inst_count-last_>2000000u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||
           !si_discovery_trace.good()||!equal(c,r13_-3824u,exi_id_completion.id()))return fail(2);
        const unsigned ch=stage_/3u,phase=stage_%3u;
        const auto next=stage_==12?e_.sram:phase==0?e_.type[ch]:phase==1?e_.transfer:e_.start;
        if(matches(c,next)){
            if(c.msr!=msr_)return fail(3);
            if(stage_<12&&!equal(c,r13_-3148u,0))return fail(8);
            if(stage_==12){
                if(c.gpr[1]!=sp_+16u||!final_guest(c)||!si_discovery_trace.finish()||
                   si_discovery_trace.tick()>c.inst_count||
                   c.mmu.read32(0xcd006434u)!=0xe0010300u||
                   c.mmu.read32(0xcd006438u)!=0x08000000u||
                   c.mmu.read32(0xcd006480u)!=0||
                   !(c.mmu.read32(0xcc003000u)&SiController::PI_SI)||
                   !(c.mmu.read32(0xcc003004u)&SiController::PI_SI))return fail(6);
            }else if(phase==0){
                if(c.gpr[1]!=sp_||c.gpr[3]!=ch||!equal(c,TypeData+4*ch,8)||
                   !equal(c,Slot+32*ch,0xffffffffu)||!equal(c,Data,0)||
                   si_discovery_trace.stage()<5)return fail(4);
            }else{
                const uint32_t command=r13_-3144u;
                if(c.gpr[3]!=ch||c.gpr[4]!=command||c.gpr[5]!=1||
                   c.gpr[6]!=TypeData+4*ch||c.gpr[7]!=3||c.gpr[8]!=Callback||
                   !equal(c,Slot+32*ch,0xffffffffu)||!equal(c,Data,ch?0u:0xffffffffu))return fail(5);
                if(phase==1){
                    if(c.gpr[1]!=sp_-32u||c.gpr[9]!=0||c.gpr[10]!=Delay||
                       !equal(c,command,0)||!equal(c,TypeData+4*ch,128u)||
                       !equal(c,Slot+128+8*ch,0)||!equal(c,Slot+132+8*ch,0))return fail(5);
                    const auto t=pair(c,TypeTime+8*ch);
                    if(!t||*t<=Delay||(ch&&*t<=times_[ch-1]))return fail(5);
                    times_[ch]=*t;
                }else if(c.gpr[1]!=sp_-96u)return fail(5);
            }
            ++stage_;last_=c.inst_count;return true;
        }
        if(addr!=c.pc||addr&3u||!mapped(c,addr,4)||++extra_>1024u||
           addr==e_.type[0].pc||addr==e_.transfer.pc||addr==e_.start.pc||addr==e_.sram.pc||
           addr==0x80521384u||addr==Callback||addr==0x80532600u||addr==0x80531b34u)
            return fail(7);
        return true;
    }
private:
    static constexpr uint32_t Data=0x80619a60u,TypeData=Data+24u,Slot=0x806fe340u,
        TypeTime=Slot+160u,Callback=0x805327f8u,Delay=3948u;
    SiDiscoveryExpectations e_;unsigned stage_=0,error_=0,extra_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0;uint64_t last_=0;std::array<uint64_t,4> times_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu>static std::optional<uint64_t> pair(Cpu& c,uint32_t a){
        if(a&7u||!mapped(c,a,8))return std::nullopt;
        return (uint64_t(c.mmu.read32(a))<<32)|c.mmu.read32(a+4);
    }
    template<class Cpu>static bool matches(Cpu& c,const VectorEdge& e){return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry_word)&&equal(c,e.lr-4,e.branch_word);}
    template<class Cpu>bool final_guest(Cpu& c){
        if(!equal(c,r13_-3148u,1)||!equal(c,r13_-3136u,0)||
           !equal(c,Data,0)||!equal(c,Data+4,si_sampling_trace.poll())||
           !equal(c,Data+8,3)||!equal(c,Data+12,TypeData)||!equal(c,Data+16,Callback)||
           !equal(c,0x80003090u,0x80531b34u))return false;
        for(unsigned ch=0;ch<4;++ch){
            if(!equal(c,TypeData+4*ch,128)||pair(c,TypeTime+8*ch)!=times_[ch]||
               pair(c,Slot+128+8*ch)!=0u)return false;
            const std::array<uint32_t,8> packet=ch?
                std::array<uint32_t,8>{ch,r13_-3144u,1,TypeData+4*ch,3,Callback,0,Delay}:
                std::array<uint32_t,8>{0xffffffffu,0,0,0,0,0,0,0};
            for(unsigned i=0;i<8;++i)if(!equal(c,Slot+32*ch+4*i,packet[i]))return false;
        }
        return true;
    }
};
}
