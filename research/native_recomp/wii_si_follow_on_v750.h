#pragma once
#include "wii_si_controller_v511.h"
namespace undercover::wii {
// Independent observer of one guest-initiated post-ACK type transfer.
// No device writes, CPU changes, scheduler advances or synthesized responses.
// A caller must first authenticate the exact guest MMIO store and CPU boundary.
class SiFollowOnWitness {
public:
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    uint64_t token()const{return token_;}
    // Recheck without advancing the observer; the completed source must
    // remain latched and its response immutable until another explicit ACK.
    bool held(uint64_t tick)const{
        if(!common(tick)||tick<last_)return false;
        return stage_==2?tick==last_&&pending_held():stage_==3&&completed_held();
    }
    bool arm(SiController& ctl,const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,
             uint64_t tick,uint32_t value,unsigned expected_channel,
             std::optional<std::array<uint8_t,3>> response,uint64_t latency){
        const uint32_t control=ctl.read(SiController::Control);
        if(stage_||error_||expected_channel>3||!latency||latency>8190u||
           tick>UINT64_MAX-8192u||ctl.pending()||(control&(SiController::TC_INT|SiController::TSTART|SiController::RDST_MASK))||
           !(control&SiController::TC_MASK)||(cause.load()&SiController::PI_SI)||
           (mask.load()&SiController::PI_SI)==0||ctl.issued_tokens()==UINT64_MAX||
           (value&~SiController::ControlWriteBits)||(value&(SiController::RDST_INT|SiController::RDST_MASK))||
           !(value&SiController::TC_MASK)||!(value&SiController::TSTART)||
           ((value>>1)&3u)!=expected_channel||((value>>16)&127u)!=1u||((value>>8)&127u)!=3u||
           (ctl.read(SiController::Buffer)>>24)!=0u)return fail(1);
        ctl_=&ctl;cause_=&cause;mask_=&mask;other_=cause.load();mask_before_=mask.load();
        status_=ctl.read(SiController::Status);channel_=expected_channel;response_=response;
        config_=value&(SiController::ControlParams|SiController::ControlMasks);
        token_=ctl.issued_tokens()+1u;start_=last_=tick;earliest_=tick+1u+latency;
        for(unsigned i=0;i<32;++i)buffer_[i]=ctl.read(SiController::Buffer+4*i);
        stage_=1;return true;
    }
    // Called only AFTER an authenticated original W1C store reached the controller.
    // Keep the completed token, COMCSR, PI mask/cause and response invariant.
    bool accept_status_w1c(uint64_t tick,uint32_t previous,uint32_t value){
        const uint32_t errors=response_?0u:SiController::ERR_NOREP<<((3u-channel_)*8u);
        if(stage_!=3u||status_written_||!common(tick)||tick<last_||
           previous!=(status_|errors)||(value&~0x0f0f0f0fu))return fail(6);
        cleared_=value;status_written_=true;
        return completed_held()?true:fail(6);
    }
    bool started(uint64_t tick){
        if(stage_!=1||!common(tick)||tick!=start_||!pending_held())return fail(2);
        stage_=2;return true;
    }
    // Observe after the real scheduler has advanced, at each audited boundary.
    bool observe(uint64_t tick){
        if(stage_!=2||!common(tick)||tick!=last_+1u)return fail(3);
        last_=tick;
        if(ctl_->pending()){
            if(!pending_held())return fail(4);
            return true;
        }
        if(tick<earliest_||!completed_held())return fail(5);
        stage_=3;return true;
    }
private:
    SiController* ctl_=nullptr;const std::atomic<uint32_t>* cause_=nullptr;const std::atomic<uint32_t>* mask_=nullptr;
    std::array<uint32_t,32> buffer_{};
    std::optional<std::array<uint8_t,3>> response_;
    uint32_t other_=0,mask_before_=0,status_=0,config_=0;unsigned channel_=0,stage_=0,error_=0;
    uint64_t token_=0,start_=0,last_=0,earliest_=0;
    uint32_t cleared_=0;bool status_written_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool common(uint64_t tick)const{
        return !error_&&ctl_&&ctl_->issued_tokens()==token_&&mask_->load()==mask_before_&&
               tick>=start_&&tick-start_<=8192u&&(cause_->load()&~SiController::PI_SI)==other_;
    }
    bool ram(bool completed)const{
        for(unsigned i=0;i<32;++i){
            uint32_t w=buffer_[i];
            if(i==0&&completed&&response_)
                w=(uint32_t((*response_)[0])<<24)|(uint32_t((*response_)[1])<<16)|(uint32_t((*response_)[2])<<8)|(w&255u);
            if(ctl_->read(SiController::Buffer+4*i)!=w)return false;
        }
        return true;
    }
    bool pending_held()const{
        const auto q=ctl_->pending();
        if(!q||q->token!=token_||q->channel!=channel_||q->out_length!=1||q->in_length!=3||
           ctl_->read(SiController::Control)!=(config_|SiController::TSTART)||
           ctl_->read(SiController::Status)!=status_||cause_->load()!=other_||!ram(false))return false;
        for(unsigned i=0;i<128;++i)if(q->tx[i]!=uint8_t(buffer_[i/4]>>(24u-8u*(i%4))))return false;
        return true;
    }
    bool completed_held()const{
        const uint32_t errors=response_?0u:SiController::ERR_NOREP<<((3u-channel_)*8u);
        return !ctl_->pending()&&ctl_->read(SiController::Control)==(config_|SiController::TC_INT|(response_?0u:SiController::COM_ERR))&&
               ctl_->read(SiController::Status)==((status_|errors)&~cleared_)&&cause_->load()==(other_|SiController::PI_SI)&&ram(true);
    }
};
}
