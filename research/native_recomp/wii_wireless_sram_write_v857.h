#pragma once
#include "wii_sram_write_witness_v818.h"
#include <cstdint>

namespace undercover::wii {
// Tracks the actual device from the setter call through the 44-byte write.
// Read-only: only ExiController and ExiMxDevice may change their own state.
// The guest buffer is observed, not used to invent an endpoint response.
class WirelessSramWriteTrace {
public:
    using Bytes=ExiMxDevice::Sram;
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned completed()const{return transfer_.completed();}
    unsigned bytes()const{return transfer_.bytes();}
    unsigned witness_failure()const{return transfer_.failure();}
    bool begin(const ExiController& ctl,const ExiMxDevice& mx,uint64_t count,
               const Bytes& guest,unsigned channel,uint16_t id){
        if(stage_||error_||channel>3u||count>UINT64_MAX-12u||
           !idle(ctl)||guest!=mx.sram())return fail(1);
        original_=guest;wanted_=guest;
        wanted_[48u+2u*channel]=uint8_t(id>>8);
        wanted_[49u+2u*channel]=uint8_t(id);
        if(original_==wanted_)return fail(1);
        ctl_=&ctl;mx_=&mx;count_=count;epoch_=ctl.selection_epoch(0);dirty_=mx.dirty();
        stage_=1;return true;
    }
    bool preselect(const ExiController& ctl,const ExiMxDevice& mx,uint64_t count,const Bytes& guest){
        if(!same(ctl,mx)||stage_!=1u||count!=count_||!idle(ctl)||
           ctl.selection_epoch(0)!=epoch_||mx.sram()!=original_||mx.dirty()!=dirty_||
           guest!=wanted_||!transfer_.begin(ctl,mx,20u,wanted_))return fail(2);
        stage_=2;return true;
    }
    // Called only after a real scheduler completion, with its actual
    // request and monotonic lifetime completion counter.
    bool record(const ExiController::Request& q,const ExiController& ctl,const ExiMxDevice& mx,uint64_t count){
        if(!same(ctl,mx)||stage_!=2u||q.length!=4u||count!=count_+1u||
           transfer_.completed()>=12u||!transfer_.record(q,ctl,mx))return fail(3);
        count_=count;
        if(transfer_.stage()==3u){
            if(transfer_.completed()!=12u||transfer_.bytes()!=44u)return fail(3);
            stage_=3;
        }
        return true;
    }
    bool deselected(const ExiController& ctl,const ExiMxDevice& mx,uint64_t count,const Bytes& guest){
        if(!same(ctl,mx)||stage_!=3u||count!=count_||!idle(ctl)||
           guest!=wanted_||!transfer_.finish(ctl,mx))return fail(4);
        final_epoch_=ctl.selection_epoch(0);stage_=4;return true;
    }
    bool returned(const ExiController& ctl,const ExiMxDevice& mx,uint64_t count,const Bytes& guest){
        if(!same(ctl,mx)||stage_!=4u||count!=count_||!idle(ctl)||
           ctl.selection_epoch(0)!=final_epoch_||guest!=wanted_||mx.sram()!=wanted_||!mx.dirty())return fail(5);
        stage_=5;return true;
    }
    bool held(const ExiController& ctl,const ExiMxDevice& mx,uint64_t count)const{
        return same(ctl,mx)&&stage_==5u&&count==count_&&idle(ctl)&&
            ctl.selection_epoch(0)==final_epoch_&&mx.sram()==wanted_&&mx.dirty();
    }
private:
    const ExiController* ctl_=nullptr;
    const ExiMxDevice* mx_=nullptr;
    Bytes original_{},wanted_{};
    SramWriteWitness transfer_;
    uint64_t count_=0,epoch_=0,final_epoch_=0;
    unsigned stage_=0,error_=0;
    bool dirty_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool same(const ExiController& ctl,const ExiMxDevice& mx)const{return !error_&&ctl_==&ctl&&mx_==&mx;}
    static bool idle(const ExiController& ctl){
        return !ctl.pending(0)&&!ctl.pending(1)&&!ctl.pending(2)&&!(ctl.read(0,0)&0x380u);
    }
};
}
