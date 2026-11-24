#pragma once
#include "wii_exi_endpoint_scheduler_v495.h"
namespace undercover::wii {
// RAII CPU-thread bridge, separate from MMIO. No endpoint or scheduler is
// created by an instruction tick. The caller owns the scheduler lifetime.
class ExiTickBinding {
public:
    explicit ExiTickBinding(ExiEndpointScheduler& scheduler):scheduler_(scheduler){
        if(active_)throw std::logic_error("EXI tick already bound");
        active_=this;
    }
    ~ExiTickBinding(){active_=nullptr;}
    ExiTickBinding(const ExiTickBinding&)=delete;
    ExiTickBinding& operator=(const ExiTickBinding&)=delete;
    static bool active()noexcept{return active_!=nullptr;}
    static void advance(uint64_t tick){if(active_)active_->scheduler_.advance(tick);}
private:
    ExiEndpointScheduler& scheduler_;
    inline static thread_local ExiTickBinding* active_=nullptr;
};
}
