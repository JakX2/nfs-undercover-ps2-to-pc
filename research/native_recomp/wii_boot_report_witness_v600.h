#pragma once
#include <array>
#include <cstdint>
#include <cstddef>
#include <vector>
namespace undercover::wii {
struct BootReportEdge {uint32_t pc,lr,branch,entry;};
struct BootReportSite {uint32_t lr,branch,resume;};
struct BootReportExpectations {
    BootReportEdge report,console,mem2;
    std::array<BootReportEdge,6> getters;
    std::vector<BootReportSite> calls;
    std::vector<BootReportEdge> helpers;
    uint32_t bctr,bctr_word,console_return,return_word,entry_word;
    std::array<uint32_t,26> table;
    std::array<uint32_t,7> case_words;
    std::array<uint8_t,600> data;
    std::array<uint8_t,24> small;
};
// Read-only proof of the original outer boot report, not an OSReport
// implementation or a proof of the internal formatting/output backend.
class BootReportWitness {
public:
    static constexpr uint32_t Begin=0x805208f4u,Return=0x80520908u,
        Data=0x8060b7a8u,Small=0x8070a898u,Print=0x80522f00u,Case=0x805204ecu;
    explicit BootReportWitness(const BootReportExpectations& e):e_(e){}
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    unsigned reports()const noexcept{return reports_;}
    unsigned getters()const noexcept{return getters_;}
    bool computed()const noexcept{return case_seen_;}
    template<class Cpu>bool begin(Cpu& c){
        if(stage_||error_||!c.is_running||c.pc!=Begin||c.lr!=Begin||
           (c.msr&0x8000u)||c.gpr[13]!=0x8070e8e0u||!equal(c,Begin,e_.entry_word)||
           !equal(c,c.gpr[13]-3400u,1)||!equal(c,Small,Data)||
           !bytes(c,Data,e_.data)||!bytes(c,Small,e_.small))return fail(1);
        sp_=c.gpr[1];r2_=c.gpr[2];r13_=c.gpr[13];msr_=c.msr;last_=start_=c.inst_count;
        for(unsigned i=0;i<4;++i){const uint32_t a=r13_-ArenaOffsets[i];
            if(!mapped(c,a,4))return fail(1);
            arena_[i]=c.mmu.read32(a);}
        if(arena_[0]>=arena_[1]||arena_[2]>=arena_[3]||
           arena_[0]<0x80000000u||arena_[1]>0x81800000u||
           arena_[2]<0x90000000u||arena_[3]>0x94000000u)return fail(1);
        for(unsigned i=0;i<4;++i)if(!mapped(c,Lowmem[i],4))return fail(1);else low_[i]=c.mmu.read32(Lowmem[i]);
        stage_=1;return true;
    }
    template<class Cpu>bool observe(uint32_t addr,Cpu& c){
        if(error_||!stage_||stage_==3||!c.is_running||c.inst_count<last_||
           c.inst_count-start_>20000000u||c.gpr[2]!=r2_||c.gpr[13]!=r13_||
           c.gpr[1]>sp_||sp_-c.gpr[1]>0x10000u||!mapped(c,addr,4))return fail(2);
        if(pending_){
            if(addr==pending_->lr){
                if(c.pc!=addr||c.lr!=addr||c.gpr[1]!=print_sp_||c.msr!=msr_||
                   c.inst_count<=print_tick_||!equal(c,addr,pending_->resume))return fail(3);
                pending_=nullptr;++reports_;last_=c.inst_count;
                if(addr==Return){
                    if(reports_!=10||getters_!=6||!console_returned_||branch_seen_!=case_seen_||
                       c.gpr[1]!=sp_||!equal(c,Return,e_.return_word)||!preserved(c))return fail(3);
                    stage_=3;
                }
                return true;
            }
            // The original OSReport backend may traverse its own call graph.
            // Only count its bounded visits; the separately witnessed caller
            // resume, not a trace at a nested entry, proves the outer return.
            if(addr==Print||addr==Return||c.pc!=addr||(addr&3u)||
               c.gpr[1]>print_sp_||++nested_>16384)return fail(3);
            return true;
        }
        if(c.msr!=msr_||!preserved(c))return fail(2);
        if(stage_==1){
            if(addr!=e_.report.pc||!matches(c,e_.report)||c.gpr[1]!=sp_)return fail(4);
            stage_=2;last_=c.inst_count;return true;
        }
        if(addr==e_.console.pc){
            if(console_||reports_!=3||!matches(c,e_.console)||c.gpr[1]!=sp_-16)return fail(5);
            console_=true;last_=c.inst_count;return true;
        }
        if(addr==e_.mem2.pc&&c.lr==e_.mem2.lr){
            if(!console_||console_returned_||mem2_||!matches(c,e_.mem2))return fail(5);
            mem2_=true;return true;
        }
        if(addr==e_.console.lr){
            if(!console_||console_returned_||reports_!=3||c.pc!=addr||c.lr!=addr||
               c.gpr[1]!=sp_-16||!equal(c,addr,e_.console_return))return fail(5);
            console_value_=c.gpr[3];console_returned_=true;last_=c.inst_count;return true;
        }
        if(addr==e_.bctr){
            if(!console_returned_||reports_!=3||branch_seen_||!table_mode()||
               !equal(c,addr,e_.bctr_word)||c.ctr!=e_.table[console_value_-0x10000008u]||
               !equal(c,Data+496u+4u*(console_value_-0x10000008u),c.ctr))return fail(6);
            branch_seen_=true;target_=c.ctr;return true;
        }
        if(addr>=Case&&addr<=Case+96u&&!((addr-Case)%16u)){
            if(!branch_seen_||case_seen_||reports_!=3||addr!=target_||c.pc!=addr||
               c.ctr!=addr||!equal(c,addr,e_.case_words[(addr-Case)/16u]))return fail(6);
            case_seen_=true;return true;
        }
        for(unsigned i=0;i<6;++i)if(addr==e_.getters[i].pc&&c.lr==e_.getters[i].lr){
            if(i!=getters_||reports_!=6+i/2u||!matches(c,e_.getters[i])||c.gpr[1]!=sp_-16)return fail(7);
            ++getters_;return true;
        }
        if(addr==Print){
            if(reports_>=10||c.pc!=addr||c.gpr[1]!=(reports_==9?sp_:sp_-16)||
               c.cr[1].eq||!print_args(c))return fail(8);
            const auto* call=site(c.lr);
            if(!call||!equal(c,call->lr-4u,call->branch))return fail(8);
            pending_=call;print_sp_=c.gpr[1];print_tick_=c.inst_count;return true;
        }
        // Exact direct helper edges derived from authenticated report and
        // console bodies, with no arbitrary extension of the outer route.
        if(++extra_>64)return fail(9);
        for(auto& e:e_.helpers)if(matches(c,e))return true;
        return fail(9);
    }
private:
    static constexpr std::array<uint32_t,4> ArenaOffsets{16400,3472,16396,3468};
    static constexpr std::array<uint32_t,4> Lowmem{0x80003100,0x8000311c,0x80003140,0x80003144};
    BootReportExpectations e_;unsigned stage_=0,error_=0,reports_=0,getters_=0,nested_=0,extra_=0;
    uint32_t sp_=0,r2_=0,r13_=0,msr_=0,print_sp_=0,console_value_=0,target_=0;
    uint64_t start_=0,last_=0,print_tick_=0;
    std::array<uint32_t,4> arena_{},low_{};
    bool console_=false,mem2_=false,console_returned_=false,branch_seen_=false,case_seen_=false;
    const BootReportSite* pending_=nullptr;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool table_mode()const{return console_value_>=0x10000008u&&console_value_<=0x10000021u;}
    const BootReportSite* site(uint32_t lr)const{
        for(auto& s:e_.calls)if(s.lr==lr)return &s;
        return nullptr;
    }
    static uint32_t bcd(uint32_t v){return (v>>4)*10u+(v&15u);}
    template<class Cpu>static bool mapped(Cpu& c,uint32_t a,unsigned n){
        return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000ull&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);
    }
    template<class Cpu>static bool equal(Cpu& c,uint32_t a,uint32_t w){return !(a&3u)&&mapped(c,a,4)&&c.mmu.read32(a)==w;}
    template<class Cpu,std::size_t N>static bool bytes(Cpu& c,uint32_t a,const std::array<uint8_t,N>& expected){
        if(!mapped(c,a,N))return false;
        for(unsigned i=0;i<N;++i)if(c.mmu.read8(a+i)!=expected[i])return false;
        return true;
    }
    template<class Cpu>static bool matches(Cpu& c,const BootReportEdge& e){
        return c.pc==e.pc&&c.lr==e.lr&&equal(c,e.pc,e.entry)&&equal(c,e.lr-4,e.branch);
    }
    template<class Cpu>bool preserved(Cpu& c)const{
        if(!equal(c,r13_-3400u,1))return false;
        for(unsigned i=0;i<4;++i)if(!equal(c,r13_-ArenaOffsets[i],arena_[i])||!equal(c,Lowmem[i],low_[i]))return false;
        return bytes(c,Data,e_.data)&&bytes(c,Small,e_.small);
    }
    template<class Cpu>bool print_args(Cpu& c)const{
        uint32_t lr=0,fmt=0;std::array<uint32_t,3> a{};unsigned n=0;
        switch(reports_){
        case 0:lr=0x805203ecu;fmt=Data+72;break;
        case 1:lr=0x80520400u;fmt=Data+88;a={Data+112,Data+124,0};n=2;break;
        case 2:lr=0x8052040cu;fmt=Data+136;break;
        case 3:
            if(!console_returned_)return false;
            if(console_value_==17){lr=0x8052047cu;fmt=Data+152;}
            else if(table_mode()){
                if(!branch_seen_||!case_seen_)return false;
                if(target_!=Case+96){lr=target_+12;fmt=Data+244+12*((target_-Case)/16);break;}
                lr=0x8052055cu;fmt=Data+328;a[0]=console_value_;n=1;
            }else{if(branch_seen_||case_seen_)return false;lr=0x8052055cu;fmt=Data+328;a[0]=console_value_;n=1;}
            break;
        case 4:lr=0x805205acu;fmt=Data+384;a={(low_[2]>>16)&255,(low_[2]>>8)&255,low_[2]&255};n=3;break;
        case 5:lr=0x805205f8u;fmt=Data+412;a={bcd((low_[3]>>16)&255),bcd((low_[3]>>8)&255),2000+bcd(low_[3]&255)};n=3;break;
        case 6:if(getters_!=2)return false;lr=0x80520618u;fmt=Data+424;a[0]=(low_[0]+low_[1])>>20;n=1;break;
        case 7:if(getters_!=4)return false;lr=0x80520638u;fmt=Data+440;a={arena_[0],arena_[1],0};n=2;break;
        case 8:if(getters_!=6)return false;lr=0x80520658u;fmt=Data+468;a={arena_[2],arena_[3],0};n=2;break;
        case 9:lr=Return;fmt=r13_-16436u;a[0]=Data;n=1;break;
        default:return false;
        }
        if(c.lr!=lr||c.gpr[3]!=fmt)return false;
        for(unsigned i=0;i<n;++i)if(c.gpr[4+i]!=a[i])return false;
        return true;
    }
};
}
