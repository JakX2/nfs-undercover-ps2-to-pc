#pragma once
#include "wii_si_controller_v511.h"
#include <atomic>
#include <cstdint>
#include <stdexcept>

namespace undercover::wii {
// Observe the first actual transfer-complete W1C, then the next native
// instruction boundary. No synthetic acknowledgement, PI write or context
// change. The installer must authenticate every supplied label/opcode.
class SiCompletionAckTrace {
public:
    enum class Phase {Idle, Armed, Acknowledged, Complete, Failed};
    static constexpr bool word_store(uint32_t w) noexcept {
        const auto op=w>>26,xo=(w>>1)&1023u;
        return op==36u||op==37u||(op==31u&&(xo==151u||xo==183u||xo==662u));
    }
    Phase phase()const noexcept{return phase_;}
    unsigned failure()const noexcept{return error_;}
    unsigned writes()const noexcept{return writes_;}
    uint32_t store_pc()const noexcept{return store_pc_;}
    bool arm(SiController& ctl,const std::atomic<uint32_t>& cause,
             const std::atomic<uint32_t>& mask,const uint64_t& tick,
             uint32_t first,uint32_t end){
        if(phase_!=Phase::Idle||((first|end)&3u)||first<0x80000000u||end>0x81800000u||
           end<=first||end-first>0x1000u||tick>UINT64_MAX-8192u||
           (cause.load()&mask.load())!=SiController::PI_SI||
           ctl.read(SiController::Control)!=0xe0010300u||
           ctl.read(SiController::Status)!=0x08000000u||ctl.pending())return fail(1);
        ctl_=&ctl;cause_=&cause;mask_=&mask;tick_=&tick;
        cause_before_=cause.load();mask_before_=mask.load();
        first_=first;end_=end;start_tick_=last_tick_=tick;
        phase_=Phase::Armed;return true;
    }
    // Called at a real native instruction label, after its visit counter
    // increments but BEFORE executing that instruction.
    bool before(uint32_t pc,uint32_t word){
        if(phase_!=Phase::Armed&&phase_!=Phase::Acknowledged)return fail(2);
        if(!tick_||*tick_<=last_tick_||*tick_-start_tick_>8192u||pc<first_||pc>=end_||(pc&3u))
            return fail(2);
        if(phase_==Phase::Acknowledged){
            if(pc!=store_pc_+4u||*tick_!=store_tick_+1u||mask_->load()!=mask_before_||
               cause_->load()!=(cause_before_&~SiController::PI_SI)||
               ctl_->read(SiController::Control)!=ack_control_||
               ctl_->read(SiController::Status)!=ack_status_||ctl_->pending())return fail(3);
            phase_=Phase::Complete;return true;
        }
        // In the handler-only lane every native instruction is instrumented.
        // A gap before acknowledgement is just as invalid as a gap after it.
        if(*tick_-last_tick_!=1u)return fail(2);
        if(!source_held())return fail(4);
        pc_=pc;last_tick_=*tick_;store_=word_store(word);return true;
    }
    // This wrapper makes exactly one real backend write with the unchanged
    // guest arguments. It never writes PI, manufactures an IOS result or
    // clears TC on behalf of the guest. All checks precede/observe the write.
    void write(SiController& ctl,unsigned off,uint32_t value){
        if(phase_==Phase::Idle){ctl.write(off,value);return;}
        if(phase_!=Phase::Armed||&ctl!=ctl_||!store_||*tick_!=last_tick_||
           pc_<first_||pc_>=end_||writes_>=16u||!source_held())reject(5);
        store_=false; // at most one device write per authenticated store
        const auto old_control=ctl.read(SiController::Control),old_status=ctl.read(SiController::Status);
        const bool ack=off==SiController::Control&&(value&SiController::TC_INT);
        if(off!=SiController::Control&&off!=SiController::Status)reject(6);
        if(off==SiController::Control&&
           ((value&SiController::TSTART)||!(value&SiController::TC_MASK)))reject(6);
        // The actual backend is responsible for W1C, register semantics and
        // propagation to PI. Only its resulting state is accepted.
        try{ctl.write(off,value);}catch(...){fail(7);throw;}
        ++writes_;
        const auto control=ctl.read(SiController::Control),status=ctl.read(SiController::Status);
        if(mask_->load()!=mask_before_||ctl.pending())reject(7);
        if(ack){
            if(!(old_control&SiController::TC_INT)||(control&SiController::TC_INT)||
               status!=old_status||cause_->load()!=(cause_before_&~SiController::PI_SI))
                reject(7);
            ack_control_=control;ack_status_=status;store_pc_=pc_;store_tick_=*tick_;
            phase_=Phase::Acknowledged;return;
        }
        if(!source_held()||
           (off==SiController::Status&&(control!=old_control||status!=(old_status&~value)))||
           (off==SiController::Control&&status!=old_status))reject(7);
    }
private:
    Phase phase_=Phase::Idle;unsigned error_=0,writes_=0;bool store_=false;
    SiController* ctl_=nullptr;const std::atomic<uint32_t>* cause_=nullptr;
    const std::atomic<uint32_t>* mask_=nullptr;const uint64_t* tick_=nullptr;
    uint32_t first_=0,end_=0,pc_=0,store_pc_=0,cause_before_=0,mask_before_=0,ack_control_=0,ack_status_=0;
    uint64_t start_tick_=0,last_tick_=0,store_tick_=0;
    bool fail(unsigned reason)noexcept{if(!error_)error_=reason;phase_=Phase::Failed;return false;}
    [[noreturn]]void reject(unsigned reason){fail(reason);throw std::runtime_error("SI completion ACK trace rejected");}
    bool source_held()const{
        return ctl_&&cause_->load()==cause_before_&&mask_->load()==mask_before_&&!ctl_->pending()&&
           (ctl_->read(SiController::Control)&(SiController::TC_INT|SiController::TC_MASK))==
                (SiController::TC_INT|SiController::TC_MASK);
    }
};
inline thread_local SiCompletionAckTrace si_completion_ack_trace{};
}
