#pragma once
#include "wii_exi_mx_device_v494.h"
namespace undercover::wii {
// CPU-thread scheduler. Latency is in native instruction visits, not
// Broadway bus cycles; no claim of cycle-accurate clock rates.
// Endpoint protocol progress is independent of guest MMIO polling.
class ExiEndpointScheduler {
public:
    ExiEndpointScheduler(ExiController& ctl,ExiMxDevice& mx,ExiIdEndpoint& id,uint64_t latency)
        :ctl_(ctl),mx_(mx),id_(id),latency_(latency),epoch_(ctl.selection_epoch(0)){
        if(!latency_)throw std::invalid_argument("EXI scheduler latency");
        if(ctl_.pending(0))throw std::logic_error("EXI scheduler pending");
        ctl_.attach(0,1,true);ctl_.attach(0,2,true);
    }
    ExiEndpointScheduler(const ExiEndpointScheduler&)=delete;
    ExiEndpointScheduler& operator=(const ExiEndpointScheduler&)=delete;
    // Call only from the CPU thread after a genuine instruction visit.
    void advance(uint64_t tick){
        if(tick<last_)throw std::logic_error("EXI scheduler time reversal");
        last_=tick;
        const auto epoch=ctl_.selection_epoch(0);
        if(epoch!=epoch_){mx_.deselect();id_.deselect();epoch_=epoch;token_=0;}
        const auto req=ctl_.pending(0);
        if(!req){token_=0;return;}
        if(req->device!=1&&req->device!=2)throw std::runtime_error("EXI endpoint missing");
        if(req->token!=token_){
            token_=req->token;
            if(tick>std::numeric_limits<uint64_t>::max()-latency_)throw std::overflow_error("EXI scheduler deadline");
            due_=tick+latency_;return;
        }
        if(tick<due_)return;
        if(req->device==1)mx_.service(ctl_,*req);else id_.service(ctl_,*req);
        last_completion_=*req;++completed_;token_=0;
    }
    uint64_t completed()const noexcept{return completed_;}
    // The last successfully serviced real request; count detects gaps.
    const std::optional<ExiController::Request>& last_completion()const noexcept{return last_completion_;}
private:
    ExiController& ctl_;ExiMxDevice& mx_;ExiIdEndpoint& id_;
    uint64_t latency_,epoch_,last_=0,due_=0,token_=0,completed_=0;
    std::optional<ExiController::Request> last_completion_;
};
}
