#pragma once
#include "wii_si_controller_v511.h"
namespace undercover::wii {
// Explicit synthetic type-discovery endpoints. No implicit controller identity,
// live input, periodic polling, or claim of cycle-accurate SI timing.
class SiTypeScheduler {
public:
    using Type = std::array<uint8_t,3>;
    struct Port {
        bool configured=false;
        std::optional<Type> type;
        static Port absent(){return {true,std::nullopt};}
        static Port present(Type t){return {true,t};}
    };
    using Profile=std::array<Port,4>;
    SiTypeScheduler(SiController& ctl,Profile profile,uint64_t latency)
        :ctl_(ctl),profile_(profile),latency_(latency){
        if(!latency_)throw std::invalid_argument("SI scheduler latency");
        if(ctl_.pending())throw std::logic_error("SI scheduler pending at attach");
        for(const auto& p:profile_)if(!p.configured)throw std::invalid_argument("SI port not configured");
    }
    SiTypeScheduler(const SiTypeScheduler&)=delete;
    SiTypeScheduler& operator=(const SiTypeScheduler&)=delete;
    // CPU-thread-only. Ticks are native instruction visits, not bus cycles.
    void advance(uint64_t tick){
        if(tick<last_)throw std::logic_error("SI scheduler time reversal");
        const auto q=ctl_.pending();
        if(!q){last_=tick;token_=0;return;}
        if(q->out_length!=1||q->in_length!=3||q->tx[0]!=0)
            throw std::runtime_error("SI unsupported type command");
        if(q->token!=token_){
            if(tick>std::numeric_limits<uint64_t>::max()-latency_)
                throw std::overflow_error("SI scheduler deadline");
            due_=tick+latency_;token_=q->token;last_=tick;return;
        }
        last_=tick;
        if(tick<due_)return;
        const auto& port=profile_.at(q->channel);
        if(port.type)ctl_.complete(q->token,*port.type);
        else ctl_.complete(q->token,{},SiController::ERR_NOREP);
        ++completed_;token_=0;
    }
    uint64_t completed()const noexcept{return completed_;}
private:
    SiController& ctl_;
    const Profile profile_;
    const uint64_t latency_;
    uint64_t last_=0,due_=0,token_=0,completed_=0;
};
class SiTickBinding {
public:
    explicit SiTickBinding(SiTypeScheduler& scheduler):scheduler_(scheduler){
        if(active_)throw std::logic_error("SI tick already bound");
        active_=this;
    }
    ~SiTickBinding(){active_=nullptr;}
    SiTickBinding(const SiTickBinding&)=delete;
    SiTickBinding& operator=(const SiTickBinding&)=delete;
    static bool active()noexcept{return active_!=nullptr;}
    static void advance(uint64_t tick){if(active_)active_->scheduler_.advance(tick);}
private:
    SiTypeScheduler& scheduler_;
    inline static thread_local SiTickBinding* active_=nullptr;
};
}
