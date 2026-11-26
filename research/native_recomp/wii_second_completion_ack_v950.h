#pragma once
#include "wii_postack_transfer_device_v771.h"
namespace undercover::wii {
// A separate successor-token ACK transaction. No cold COMCSR constants,
// no PI writes, no token reset, and no implicit acknowledgement on handoff.
class SecondCompletionAck {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned reads()const{return reads_;}
    unsigned writes()const{return writes_;}
    uint64_t token()const{return token_;}
    bool arm(SiController& ctl,const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,
             const uint64_t& tick,uint64_t token,bool previous_held){
        const uint32_t ctrl=ctl.read(SiController::Control);
        if(stage_||error_||!previous_held||token<2u||ctl.issued_tokens()!=token||ctl.pending()||
           (cause.load()&mask.load())!=SiController::PI_SI||
           (ctrl&(SiController::TC_INT|SiController::TC_MASK|SiController::TSTART|SiController::RDST_MASK))!=
                (SiController::TC_INT|SiController::TC_MASK)||tick>UINT64_MAX-8192u)return fail(1);
        ctl_=&ctl;cause_=&cause;mask_=&mask;tick_=&tick;token_=token;
        cause_before_=cause.load();mask_before_=mask.load();control_=ctrl;status_=ctl.read(SiController::Status);
        poll_=ctl.read(SiController::Poll);
        for(unsigned i=0;i<32;++i)buffer_[i]=ctl.read(SiController::Buffer+4*i);
        start_=last_=tick;stage_=1;return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,bool authenticated){
        if(!authenticated||!safe(c)||!tick_||&c.inst_count!=tick_||armed_||
           (pc&3u)||pc<0x80000000u||pc>0x817ffffcu||c.inst_count-last_!=1u||
           c.inst_count-start_>8192u||!c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||c.mmu.read32(pc)!=w)
            return fail(2);
        if(stage_==2u){
            if(pc!=ack_pc_+4u||!state(false))return fail(5);
            last_=c.inst_count;successor_word_=w;stage_=3;return true;
        }
        if((stage_!=1u&&stage_!=4u)||!state(stage_==1u))return fail(2);
        last_=c.inst_count;return arm_access(c,pc,w);
    }
    // The ACK successor was witnessed before it executed. Resume that exact
    // instruction once, without adding a tick or replaying the W1C.
    template<class C>bool resume_after_ack(C& c,uint32_t pc,uint32_t w){
        if(stage_!=3u||error_||armed_||!safe(c)||!tick_||&c.inst_count!=tick_||
           c.inst_count!=last_||pc!=ack_pc_+4u||w!=successor_word_||!state(false)||
           !c.mmu.get_ptr(pc)||!c.mmu.get_ptr(pc+3u)||c.mmu.read32(pc)!=w)return fail(5);
        stage_=4u;return arm_access(c,pc,w);
    }
    // A separately witnessed native indirect dispatch consumes one outer
    // dispatcher tick, but performs no guest instruction or device access.
    template<class C>bool accept_dispatch_tick(C& c){
        if(stage_!=4u||error_||armed_||!safe(c)||!tick_||&c.inst_count!=tick_||
           c.inst_count-last_!=1u||!state(false))return fail(5);
        last_=c.inst_count;return true;
    }
    bool postack_held()const{return stage_==4u&&!armed_&&tick_&&*tick_==last_&&state(false);}
    // Read-only terminal observation after independently witnessed native RFI.
    bool postack_held_after_rfi(uint64_t tick,unsigned delta)const{
        return stage_==4u&&!armed_&&tick_&&*tick_==tick&&delta<=2u&&tick>=last_&&tick-last_==delta&&state(false);
    }
    bool owns_postack(const SiController& ctl,const std::atomic<uint32_t>& cause,
                      const std::atomic<uint32_t>& mask,const uint64_t& tick)const{
        return &ctl==ctl_&&&cause==cause_&&&mask==mask_&&&tick==tick_&&postack_held();
    }
    // Retire this completed token's witness only after the next device
    // owner has admitted the exact same controller, PI bank and tick.
    bool handoff_follow_on(PostAckTransferDevice& next,SiController& ctl,
                          const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,
                          const uint64_t& tick,unsigned ch,bool idle,
                          std::optional<std::array<uint8_t,3>> response,uint64_t latency){
        if(!owns_postack(ctl,cause,mask,tick)||!next.begin(ctl,cause,mask,*this,tick,ch,idle,response,latency))return false;
        stage_=5u;return true;
    }
private:
    template<class C>bool arm_access(C& c,uint32_t pc,uint32_t w){
        pc_=pc;
        const auto a=PostAckTransferDevice::word_access(c,w);
        const auto off=PostAckTransferDevice::offset(a.address);
        if(!off){
            // Reject decoded word operations that overlap either SI aperture
            // but cannot be routed to a supported, aligned register.
            if(a.kind!=PostAckTransferDevice::Access::None){
                const uint32_t p=a.address&0x3fffffffu;
                const auto overlap=[p](uint32_t base){
                    return p<base+0x100u&&uint64_t(p)+4u>base;
                };
                if(overlap(0x0d006400u)||overlap(0x0d806400u))return fail(2);
            }
            // Non-SI instructions are still accounted for; never allow an
            // unarmed SI MMIO operation via the read/write entry points.
            return true;
        }
        if(a.kind==PostAckTransferDevice::Access::None||*off==SiController::Poll||reads_+writes_>=128u)return fail(2);
        armed_=true;off_=*off;access_=a.kind;value_=a.store;return true;
    }
public:
    bool read(SiController& ctl,unsigned off,uint32_t& result){
        if(!consume(ctl,off,PostAckTransferDevice::Access::Read))return false;
        result=ctl.read(off);++reads_;return state(stage_==1u)?true:fail(3);
    }
    bool write(SiController& ctl,unsigned off,uint32_t v){
        if(!value_||*value_!=v||!consume(ctl,off,PostAckTransferDevice::Access::Write))return fail(3);
        if(off==SiController::Status){
            if(v&~0x0f0f0f0fu)return fail(4);
            try{ctl.write(off,v);}catch(...){return fail(4);}
            status_&=~v;++writes_;return state(stage_==1u)?true:fail(4);
        }
        if(stage_==4u){
            // After ACK permit only real communication RAM writes and
            // status W1C; new COMCSR transactions need a separate witness.
            if(off<SiController::Buffer||off>=0x100u||(off&3u))return fail(4);
            try{ctl.write(off,v);}catch(...){return fail(4);}
            buffer_[(off-SiController::Buffer)/4u]=v;++writes_;
            return state(false)?true:fail(4);
        }
        // The guest must explicitly W1C TC while preserving the current
        // transfer parameters and interrupt masks; no new transaction.
        if(off!=SiController::Control||!(v&SiController::TC_INT)||
           (v&~SiController::ControlWriteBits)||(v&(SiController::TSTART|SiController::RDST_INT))||
           (v&(SiController::ControlParams|SiController::ControlMasks))!=
             (control_&(SiController::ControlParams|SiController::ControlMasks)))return fail(4);
        try{ctl.write(off,v);}catch(...){return fail(4);}
        ++writes_;control_&=~SiController::TC_INT;ack_pc_=pc_;
        if(!state(false))return fail(4);
        stage_=2;return true;
    }
    bool poll(uint64_t tick)const{
        return (stage_==1u||stage_==4u)&&!error_&&!armed_&&tick_&&*tick_==tick&&tick==last_&&state(stage_==1u);
    }
private:
    SiController* ctl_=nullptr;const std::atomic<uint32_t>* cause_=nullptr,*mask_=nullptr;
    const uint64_t* tick_=nullptr;uint64_t token_=0,start_=0,last_=0;
    uint32_t cause_before_=0,mask_before_=0,control_=0,status_=0,poll_=0,pc_=0,ack_pc_=0,successor_word_=0;
    std::array<uint32_t,32> buffer_{};std::optional<uint32_t> value_;
    PostAckTransferDevice::Access access_=PostAckTransferDevice::Access::None;
    unsigned stage_=0,error_=0,reads_=0,writes_=0,off_=0;bool armed_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    bool state(bool asserted)const{
        if(error_||!ctl_||!tick_||*tick_<start_||*tick_-start_>8192u||
           ctl_->issued_tokens()!=token_||ctl_->pending()||mask_->load()!=mask_before_||
           cause_->load()!=(asserted?cause_before_:cause_before_&~SiController::PI_SI)||
           ctl_->read(SiController::Control)!=control_||ctl_->read(SiController::Status)!=status_||
           ctl_->read(SiController::Poll)!=poll_)return false;
        for(unsigned i=0;i<32;++i)if(ctl_->read(SiController::Buffer+4*i)!=buffer_[i])return false;
        return true;
    }
    bool consume(SiController& ctl,unsigned off,PostAckTransferDevice::Access kind){
        if((stage_!=1u&&stage_!=4u)||error_||!armed_||!tick_||*tick_!=last_||&ctl!=ctl_||off!=off_||kind!=access_||!state(stage_==1u))return fail(3);
        armed_=false;return true;
    }
};
}
