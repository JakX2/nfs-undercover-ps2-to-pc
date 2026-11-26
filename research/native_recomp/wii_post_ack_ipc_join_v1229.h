#pragma once
#include "wii_ipc_client_witness_v623.h"
#include "wii_ipc_entry_join_v930.h"
#include <cstdint>

namespace undercover::wii {
// Three real observation seams: caller dispatch before its tick, caller
// instruction after its tick, and direct native callee entry at that tick.
// Keep the old V623 cold checks intact, including their strict tick ordering.
class PostAckIpcJoin {
public:
    PostAckIpcJoin(const IpcClientExpectations& cold,IpcEntryJoinExpectation edge)
        :cold_(cold),join_(edge),edge_(edge){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned cold_refusal()const{return cold_.entry_refusal();}
    unsigned cold_failure()const{return cold_.failure();}
    unsigned join_failure()const{return join_.failure();}
    unsigned client_stage()const{return cold_.stage();}
    uint32_t heap_size()const{return cold_.heap_size();}
    template<class C>bool pre_dispatch(C& c,uint32_t pc,bool leaf_dispatched,bool device_ok){
        if(stage_||error_||!leaf_dispatched||!device_ok||pc!=edge_.call||
           c.inst_count==UINT64_MAX||!cold_.begin(c))return fail(1);
        cpu_=&c;tick_=c.inst_count;stage_=1;return true;
    }
    template<class C>bool before_call(C& c,uint32_t pc,uint32_t w,bool leaf_returned,bool device_ok){
        if(stage_!=1||error_||cpu_!=&c||!leaf_returned||!device_ok||
           c.inst_count!=tick_+1u||!join_.start(c,pc,w,true,true))return fail(2);
        stage_=2;return true;
    }
    template<class C>bool target_entry(C& c,uint32_t pc,bool device_ok){
        if(stage_!=2||error_||cpu_!=&c||!device_ok||c.inst_count!=tick_+1u||
           !join_.entry(c,pc,true)||!cold_.observe(pc,c)||cold_.stage()!=2u)return fail(3);
        stage_=3;return true;
    }
    // The direct callee entry is already consumed. Never replay it or
    // restart the heap witness. Later original call entries advance the
    // same V623 witness, and the final caller return is its terminal seam.
    template<class C>bool continuation(C& c,uint32_t pc,bool device_ok){
        if((stage_!=3u&&stage_!=4u)||error_||cpu_!=&c||!device_ok||
           !cold_.observe(pc,c))return fail(4);
        stage_=cold_.stage()==19u?5u:4u;return true;
    }
private:
    IpcClientWitness cold_;
    IpcEntryJoinWitness join_;
    IpcEntryJoinExpectation edge_;
    const void* cpu_=nullptr;
    uint64_t tick_=0;
    unsigned stage_=0,error_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
};
}
