#pragma once
#include "wii_post_ack_open_join_v1242.h"
#include <algorithm>
#include <span>
namespace undercover::wii {
// Original submission, through a single native ACK, not reply delivery.
// MMIO ownership is explicit: caller forwards the original CPU writes only
// through write(), which checks both the previous and resulting snapshots.
class PostAckSubmitJoin {
public:
    static constexpr uint32_t Submit=OpenRequestWitness::Submit,
        Convert=0x805293b0u,Queue=0x8051afe0u,Read=0x8051905cu,
        Write=0x8051906cu,Sleep=0x8052a430u;
    PostAckSubmitJoin(std::span<const VectorEdge> edges,const std::array<uint8_t,28>& vector,unsigned first_kind=0)
        :edges_(edges),sc_(vector,OpenScRoute::SubmitCaller,first_kind),epoch_(first_kind){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned writes()const{return writes_;}
    unsigned write_failure()const{return write_error_;}
    // PPCCTRL Y1/Y2 are W1C, not persistent bits in the written value.
    // X2 is independently writable by Broadway; no reply is pending.
    // Preserve both notification enables and require the actual X1 edge.
    static std::optional<uint32_t> submission_control(uint32_t before,uint32_t value){
        using M=IpcMailbox;
        constexpr uint32_t en=M::IY1|M::IY2;
        if((before&(M::X1|M::Y1|M::Y2))||!(before&M::IY2)||
           (value&~0x3fu)||!(value&M::X1)||(value&en)!=(before&en))return std::nullopt;
        return value&(M::X1|M::X2|en);
    }
    unsigned path_kind()const{return kind_;}
    uint32_t request()const{return req_;}
    template<class C>bool begin(C& c,const PostAckOpenJoin& open,bool device_ok){
        const auto s=NativeIosBinding::cold_snapshot();
        if(stage_||error_||!device_ok||!open.submit_at(c,true)||!s||!epoch_.admits(open.path_kind())||!idle(*s))return fail(1);
        req_=open.request();kind_=open.path_kind();
        if((req_&31u)||!mapped(c,req_,64u))return fail(1);
        path_=c.mmu.read32(req_+12u);
        if(!valid_request(c))return fail(1);
        cpu_=&c;initial_=*s;tick_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool boundary(C& c,bool device_ok)const{
        auto s=NativeIosBinding::cold_snapshot();
        return stage_>=1u&&stage_<=7u&&!error_&&context(c,device_ok)&&s&&
            stable(*s,writes_)&&valid_request(c);
    }
    template<class C>bool observe(C& c,uint32_t pc,bool device_ok){
        using R=OpenScRoute;
        if(!boundary(c,device_ok)||c.pc!=pc)return fail(2);
        if(pc==Submit){
            if(stage_!=1u||entered_||c.lr!=0x80519a3cu||c.inst_count-tick_>1u)return fail(2);
            entered_=true;return true;
        }
        if(pc==R::Vector){
            if(stage_!=4u||!sc_.vector_trace(pc,c))return fail(3);
            return true;
        }
        if(pc==R::Call){
            if(stage_!=3u||c.lr!=R::SubmitCaller||!c.open_cache_range.ready_sc(c))return fail(3);
            try{sc_.arm(pc,c);}catch(const std::exception&){return fail(3);}
            stage_=4;return true;
        }
        if(pc==R::SubmitCaller){
            if(stage_!=4u||!sc_.returned(c)||!c.open_cache_range.finish(c))return fail(3);
            stage_=5;return true;
        }
        const auto it=std::find_if(edges_.begin(),edges_.end(),[&](const auto& e){return e.pc==pc&&e.lr==c.lr;});
        if(it==edges_.end()||!equal(c,pc,it->entry_word)||!equal(c,c.lr-4u,it->branch_word))return fail(2);
        if(pc==Convert&&stage_==1u&&entered_){stage_=2;return true;}
        if(pc==OpenRequestWitness::Flush&&stage_==2u&&c.lr==R::SubmitCaller&&(c.msr&0x8000u)){
            const uint32_t a=c.gpr[3]&0x3fffffffu,n=c.gpr[4],r=req_&0x3fffffffu;
            if(n<32u||n>0x1000u||a>r||uint64_t(a)+n<uint64_t(r)+32u)return fail(3);
            if(epoch_.second()){
                if(!c.open_cache_range.rearm(c))return fail(3);
            }else c.open_cache_range=OpenCacheRangeTrace{};
            if(!c.open_cache_range.begin(c,c.gpr[3],n))return fail(3);
            stage_=3;return true;
        }
        if(pc==OpenRequestWitness::Disable&&stage_==5u&&(c.msr&0x8000u)){stage_=6;return true;}
        if(pc==Queue&&stage_==6u&&!(c.msr&0x8000u)){stage_=7;return true;}
        if((pc==Read||pc==Write)&&stage_==7u&&!(c.msr&0x8000u))return true;
        if(pc==Sleep&&stage_==7u&&writes_==2u&&!(c.msr&0x8000u)){
            sleep_tick_=c.inst_count;sleep_lr_=c.lr;sleep_sp_=c.gpr[1];sleep_queue_=c.gpr[3];
            stage_=8;return true;
        }
        return fail(2);
    }
    template<class C,class Native,class Verify>
    bool dispatch(C& c,bool device_ok,Native native,Verify verify){
        if(stage_!=4u||!boundary(c,device_ok)||sc_.phase()!=OpenScRoute::Phase::Armed)return fail(3);
        try{if(!sc_.dispatch(c,native,verify)||error_)return fail(3);}
        catch(const std::exception&){return fail(3);}
        return true;
    }
    template<class C>bool write(C& c,uint32_t addr,uint32_t value,bool device_ok){
        using M=IpcMailbox;
        if(stage_!=7u||writes_>1u||(c.msr&0x8000u)||!boundary(c,device_ok))return write_fail(1);
        if((addr&0xc0000000u)==0x40000000u)return write_fail(2);
        const uint32_t a=addr&0x3fffffffu;
        const auto offset=writes_?M::PPCCTRL:M::PPCMSG;
        if(a!=IosBus::IPC+offset&&a!=IosBus::MIRROR+offset)return write_fail(2);
        if(writes_){
            const auto next=submission_control(initial_.control,value);
            if(!next)return write_fail(3);
            sent_control_=*next;
        }else if(value!=(req_&0x3fffffffu))return write_fail(3);
        try{if(!NativeIosBinding::write32(addr,value))return write_fail(4);}
        catch(const std::exception&){return write_fail(4);}
        ++writes_;
        auto s=NativeIosBinding::cold_snapshot();
        if(!s||!stable(*s,writes_))return write_fail(5);
        return true;
    }
    template<class C>bool acknowledge(C& c,bool device_ok){
        using M=IpcMailbox;using H=HollywoodIrq;using S=StmIos;
        auto before=NativeIosBinding::cold_snapshot();
        if(stage_!=8u||error_||!context(c,device_ok)||!before||!stable(*before,2u)||
           c.pc!=Sleep||c.lr!=sleep_lr_||c.gpr[1]!=sleep_sp_||c.gpr[3]!=sleep_queue_||
           c.inst_count!=sleep_tick_||(c.msr&0x8000u)||!valid_request(c))return fail(5);
        const auto ack=NativeIosBinding::service_at_guest_boundary(c.msr);
        auto after=NativeIosBinding::cold_snapshot();
        if(!ack||ack->progress!=S::Pump::Ack||!ack->broadway_irq_level||ack->guest_exception_ready||
           !after||after->queued||after->event||after->steps!=initial_.steps+1u||after->replies!=1u||
           after->ppc!=before->ppc||after->arm!=before->arm||after->irq_mask!=before->irq_mask||
           after->pi_mask!=before->pi_mask||after->control!=((sent_control_&~M::X1)|M::Y2)||
           after->flags!=(before->flags|H::IPC_PPC)||after->pi_cause!=(before->pi_cause|H::PI_HOLLYWOOD)||
           !epoch_.acknowledged_descriptors(kind_)||!valid_request(c))return fail(5);
        ack_=*after;stage_=9;return true;
    }
    template<class C>bool ack_at(C& c,bool device_ok)const{
        auto s=NativeIosBinding::cold_snapshot();
        return stage_==9u&&!error_&&context(c,device_ok)&&s&&same(*s,ack_)&&epoch_.acknowledged_descriptors(kind_)&&
            c.pc==Sleep&&c.lr==sleep_lr_&&c.gpr[1]==sleep_sp_&&c.gpr[3]==sleep_queue_&&
            c.inst_count==sleep_tick_&&!(c.msr&0x8000u)&&valid_request(c);
    }
private:
    std::span<const VectorEdge> edges_;
    OpenScRoute sc_;
    OpenTransactionEpoch epoch_;
    const void* cpu_=nullptr;ColdIpcSnapshot initial_{},ack_{};
    unsigned stage_=0,error_=0,writes_=0,kind_=0,write_error_=0;
    uint32_t sent_control_=0;
    bool entered_=false;
    uint32_t req_=0,path_=0,sleep_lr_=0,sleep_sp_=0,sleep_queue_=0;
    uint64_t tick_=0,sleep_tick_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool write_fail(unsigned n){if(!write_error_)write_error_=n;return fail(4);}
    template<class C>bool context(C& c,bool device_ok)const{
        return cpu_==&c&&device_ok&&c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
            c.inst_count>=tick_&&c.inst_count-tick_<=200000u;
    }
    bool idle(const ColdIpcSnapshot& s)const{
        using M=IpcMailbox;using H=HollywoodIrq;
        return epoch_.valid()&&epoch_.descriptor_held()&&!s.queued&&!s.replies&&!s.event&&s.steps==epoch_.steps()&&!(s.control&(M::X1|M::Y1|M::Y2))&&
            (s.control&M::IY2)&&s.irq_mask==H::IPC_PPC&&!(s.flags&H::IPC_PPC)&&
            (s.pi_mask&H::PI_HOLLYWOOD)&&!(s.pi_cause&s.pi_mask);
    }
    static bool same(const ColdIpcSnapshot& a,const ColdIpcSnapshot& b){
        return a.control==b.control&&a.ppc==b.ppc&&a.arm==b.arm&&a.flags==b.flags&&
            a.irq_mask==b.irq_mask&&a.pi_cause==b.pi_cause&&a.pi_mask==b.pi_mask&&
            a.steps==b.steps&&a.replies==b.replies&&a.queued==b.queued&&a.event==b.event;
    }
    bool stable(const ColdIpcSnapshot& s,unsigned n)const{
        auto e=initial_;
        if(n)e.ppc=req_&0x3fffffffu;
        if(n==2u){e.control=sent_control_;e.queued=true;}
        return epoch_.descriptor_held()&&same(s,e);
    }
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        const auto end=uint64_t(a)+n;
        if(!n||!((a>=0x80000000u&&end<=0x81800000ull)||(a>=0x90000000u&&end<=0x94000000ull)))return false;
        auto* p=c.mmu.get_ptr(a);auto* q=c.mmu.get_ptr(a+n-1u);
        return p&&q&&reinterpret_cast<uintptr_t>(q)>=reinterpret_cast<uintptr_t>(p)&&
            reinterpret_cast<uintptr_t>(q)-reinterpret_cast<uintptr_t>(p)==n-1u;
    }
    template<class C>static bool equal(C& c,uint32_t a,uint32_t v){return !(a&3u)&&mapped(c,a,4u)&&c.mmu.read32(a)==v;}
    template<class C>bool valid_request(C& c)const{
        const auto name=kind_==1u?std::string_view("/dev/stm/immediate"):kind_==2u?std::string_view("/dev/stm/eventhook"):std::string_view{};
        if(name.empty()||!path_||path_>=WiiPhysicalRam::MEM1_SIZE||!mapped(c,req_,64u)||
           c.mmu.read32(req_)!=StmIos::Open||c.mmu.read32(req_+12u)!=path_||c.mmu.read32(req_+16u)||
           !mapped(c,path_|0x80000000u,unsigned(name.size()+1u)))return false;
        for(unsigned i=0;i<name.size();++i)if(c.mmu.read8((path_|0x80000000u)+i)!=uint8_t(name[i]))return false;
        return c.mmu.read8((path_|0x80000000u)+uint32_t(name.size()))==0;
    }
};
}
