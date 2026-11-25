#pragma once
#include "wii_postack_transfer_device_v771.h"
namespace undercover::wii {
// A bctrl outer-dispatch tick is not a guest instruction and must not
// manufacture SI completion. Only a previously completed, still-held
// transaction may be observed at that existing tick. The surrounding
// callback witness independently verifies the CPU and exact poll/tick.
inline bool observe_completed_callback_dispatch(PostAckTransferDevice& device,const uint64_t& tick){
    if(device.stage()!=2||device.follow_stage()!=3||device.pending())return false;
    return device.after_return_at(tick)&&device.held(tick);
}
}
