#pragma once
#include "wii_exi_profile_v501.h"
#include "wii_wireless_sram_write_v857.h"
namespace undercover::wii {
// Bind V857 to the existing CPU-thread profile, not a new scheduler.
// Call observe after each authenticated native instruction boundary.
class WirelessProfileTrace {
public:
    using Bytes=ExiMxDevice::Sram;
    unsigned stage()const{return trace_.stage();}
    unsigned failure()const{return error_;}
    unsigned witness_failure()const{return trace_.failure();}
    unsigned completed()const{return trace_.completed();}
    unsigned bytes()const{return trace_.bytes();}
    bool begin(const Bytes& guest,unsigned channel,uint16_t id,uint64_t tick){
        auto* s=ExiProfileSession::current();
        if(session_||error_||!s||tick>UINT64_MAX-16384u||
           s->controller().selection_epoch(0)>UINT64_MAX-2u||
           !trace_.begin(s->controller(),s->endpoint(),s->completed(),guest,channel,id))return fail(1);
        session_=s;seen_=s->completed();epoch_=s->controller().selection_epoch(0);
        for(unsigned ch=1;ch<3;++ch){
            epochs_[ch-1]=s->controller().selection_epoch(ch);
            for(unsigned i=0;i<5;++i)regs_[ch-1][i]=s->controller().read(ch,4u*i);
        }
        start_=last_=tick;return true;
    }
    bool observe(uint64_t tick){
        if(!common()||stage()<1u||stage()>5u||tick-last_!=1u||tick-start_>16384u)return fail(2);
        last_=tick;const auto& s=*session_;const auto& ctl=s.controller();
        const auto ep=ctl.selection_epoch(0);const auto cs=ctl.read(0,0)&0x380u;
        if(stage()==1u){
            if(ep!=epoch_||cs||ctl.pending(0)||s.completed()!=seen_)return fail(3);
        }else if(stage()==2u||stage()==3u){
            if(ep==epoch_){
                if(cs||ctl.pending(0)||stage()!=2u||s.completed()!=seen_)return fail(3);
            }else if(ep==epoch_+1u){
                if(cs!=0x100u)return fail(3);
                if(auto q=ctl.pending(0);q&&(!valid(*q)||stage()!=2u))return fail(3);
            }else if(ep==epoch_+2u){
                if(cs||ctl.pending(0)||stage()!=3u||s.completed()!=seen_)return fail(3);
            }else return fail(3);
        }else if(ep!=epoch_+2u||cs||ctl.pending(0)||s.completed()!=seen_)return fail(3);
        if(s.completed()!=seen_){
            if(stage()!=2u||ep!=epoch_+1u||s.completed()-seen_!=1u)return fail(4);
            const auto& q=s.scheduler().last_completion();
            if(!q||!valid(*q)||!trace_.record(*q,ctl,s.endpoint(),s.completed()))return fail(4);
            seen_=s.completed();
        }
        return stage()!=5u||held()?true:fail(5);
    }
    // Outer dispatcher tick: no guest instruction or endpoint service.
    // Only an already completed and still-held transaction can cross it.
    bool observe_dispatch(uint64_t tick){
        if(stage()!=5u||!held())return fail(2);
        return observe(tick);
    }
    bool preselect(const Bytes& guest,uint64_t tick){
        if(!common()||tick!=last_||!trace_.preselect(session_->controller(),session_->endpoint(),session_->completed(),guest))return fail(5);
        return true;
    }
    bool deselected(const Bytes& guest,uint64_t tick){
        if(!common()||tick!=last_||session_->controller().selection_epoch(0)!=epoch_+2u||
           !trace_.deselected(session_->controller(),session_->endpoint(),session_->completed(),guest))return fail(5);
        return true;
    }
    bool returned(const Bytes& guest,uint64_t tick){
        if(!common()||tick!=last_||!trace_.returned(session_->controller(),session_->endpoint(),session_->completed(),guest))return fail(5);
        return true;
    }
    bool held()const{
        return common()&&trace_.held(session_->controller(),session_->endpoint(),session_->completed());
    }
private:
    WirelessSramWriteTrace trace_;
    const ExiProfileSession* session_=nullptr;
    std::array<uint64_t,2> epochs_{};
    std::array<std::array<uint32_t,5>,2> regs_{};
    uint64_t seen_=0,epoch_=0,start_=0,last_=0;
    unsigned error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool valid(const ExiController::Request& q){return q.channel==0u&&q.device==1u&&!q.dma&&q.direction==1u&&q.length==4u&&q.token!=0u;}
    bool common()const{
        if(error_||!session_||ExiProfileSession::current()!=session_)return false;
        const auto& c=session_->controller();
        for(unsigned ch=1;ch<3;++ch){
            if(c.pending(ch)||c.selection_epoch(ch)!=epochs_[ch-1])return false;
            for(unsigned i=0;i<5;++i)if(c.read(ch,4u*i)!=regs_[ch-1][i])return false;
        }
        return true;
    }
};
}
