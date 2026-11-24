#include "arena_cache_range_trace_v596.h"
#include "flat_cacheline_zero_v67.h"
#include <array>
#include <iostream>
#include <vector>
#include <source_location>
using namespace undercover::wii;
using Trace=ArenaCacheRangeTrace;
static void need(bool b,const std::source_location loc=std::source_location::current()){
    if(!b)throw std::runtime_error("V596 line "+std::to_string(loc.line()));
}
struct Mmu {
    static constexpr uint32_t Size=0x100000;
    std::vector<uint8_t> m1=std::vector<uint8_t>(Size,0x5a),m2=std::vector<uint8_t>(Size,0xa5);
    uint8_t* get_ptr(uint32_t a){
        if(a>=0x80000000u&&a-0x80000000u<Size)return m1.data()+a-0x80000000u;
        if(a>=0x90000000u&&a-0x90000000u<Size)return m2.data()+a-0x90000000u;
        return nullptr;
    }
    uint8_t read8(uint32_t a){auto* p=get_ptr(a);if(!p)throw std::out_of_range("test memory");return *p;}
};
struct Cpu {
    Mmu mmu;std::array<uint32_t,32> gpr{};bool is_running=true;uint32_t msr=2;
    nwii::runtime::FlatCachelineZeroTrace guest_dcbz_trace;
    uint32_t guest_flush_count=87,guest_last_flush=0;
    std::array<uint32_t,256> guest_flush_lines{};
    Trace trace;
    void zero(uint32_t a){trace.on_zero(a);guest_dcbz_trace.zero(mmu,a);}
    void flush(uint32_t a){trace.on_flush(a);guest_last_flush=a&~31u;
        if(guest_flush_count<guest_flush_lines.size())guest_flush_lines[guest_flush_count]=guest_last_flush;
        ++guest_flush_count;
    }
};
int main(){
    static_assert(sizeof(Trace)<=128);
    constexpr uint32_t size=0x80000;
    for(unsigned fault=0;fault<=17;++fault){
        Cpu c;auto& t=c.trace;c.gpr[1]=0x80751c20;c.gpr[2]=0x80715ee0;c.gpr[13]=0x8070e8e0;
        c.zero(0x80000000);c.flush(0x80000000); // inactive prior diagnostics
        need(t.zeros()==0&&t.flushes()==0);
        bool failed=false;
        try {
            for(unsigned lane=1;lane<=2;++lane){
                uint32_t lo=(lane==1?0x80000000u:0x90000000u)+0x1000,hi=lo+size;
                if(lane==1&&fault==1)lo++;
                if(lane==1&&fault==2)hi=0x90081000;
                if(lane==1&&fault==3)c.guest_flush_count=0xfffffff0u;
                if(!t.begin(c,lane,lo,hi)){failed=true;break;}
                if(lane==1&&fault==4)c.zero(lo+32);
                if(lane==1&&fault==5)c.flush(lo);
                for(uint32_t a=lo;a<hi;a+=32){
                    if(lane==1&&fault==6&&a==lo+32)c.zero(lo);
                    if(lane==1&&fault==7&&a==hi-32)break;
                    c.zero(a);
                }
                if(lane==1&&fault==8)*c.mmu.get_ptr(lo+123)=1;
                if(lane==1&&fault==9)*c.mmu.get_ptr(hi)^=1;
                if(lane==1&&fault==10)c.gpr[13]^=4;
                if(!t.begin_flush(c,hi-Trace::Tail,lane==1&&fault==11?Trace::Tail-32:Trace::Tail)){failed=true;break;}
                if(lane==1&&fault==12)c.zero(lo);
                for(uint32_t a=hi-Trace::Tail;a<hi;a+=32){
                    if(lane==1&&fault==13&&a==hi-32)break;
                    if(lane==1&&fault==14&&a==hi-64)c.flush(a+32);
                    c.flush(a);
                }
                if(lane==1&&fault==15)c.guest_flush_count--;
                if(!t.ready_sc(c)){failed=true;break;}
                if(lane==1&&fault==16)c.flush(hi-32);
                if(lane==2&&fault==17)*c.mmu.get_ptr(lo-1)^=1;
                if(!t.finish(c)){failed=true;break;}
            }
        }catch(const std::exception&){failed=true;}
        need(failed==(fault!=0));
        if(!fault){
            need(t.lanes()==2&&t.zeros()==2*size/32&&t.flushes()==2*Trace::Tail/32&&t.phase()==Trace::Phase::Done);
            need(c.guest_flush_count==88+2*Trace::Tail/32&&c.guest_dcbz_trace.count==1+2*size/32);
            need(c.mmu.read8(0x80000fff)==0x5a&&c.mmu.read8(0x80081000)==0x5a&&c.mmu.read8(0x90000fff)==0xa5&&c.mmu.read8(0x90081000)==0xa5);
            need(!t.begin(c,3,0x90001000,0x90081000));
        }else need(t.failure()!=0&&t.phase()==Trace::Phase::Failed);
    }
    std::cout<<"V596_ARENA_CACHE lanes=2 zero_lines=32768 flush_lines=16384 refusal=17 constant_space=1 cache_hardware=0\n";
}
