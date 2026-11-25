#pragma once
#include "wii_exi_mx_device_v494.h"
namespace undercover::wii {
// Read-only proof of a single offset-addressed SRAM write transaction.
// The endpoint owns every SRAM mutation. The caller supplies a snapshot of
// the intended guest data; this witness never repairs or persists it.
class SramWriteWitness {
public:
    using Bytes=ExiMxDevice::Sram;
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned completed()const{return completed_;}
    unsigned bytes()const{return cursor_-offset_;}
    bool begin(const ExiController& ctl,const ExiMxDevice& mx,unsigned offset,const Bytes& desired){
        if(stage_||error_||offset>=64u||ctl.pending(0)||(ctl.read(0,0)&0x380u))return fail(1);
        old_=mx.sram();wanted_=desired;observed_=old_;
        for(unsigned i=0;i<offset;++i)if(old_[i]!=wanted_[i])return fail(1);
        ctl_=&ctl;mx_=&mx;offset_=cursor_=offset;dirty_=mx.dirty();epoch_=ctl.selection_epoch(0);
        stage_=1;return true;
    }
    // Invoke after the exact real endpoint service returns, not before.
    bool record(const ExiController::Request& q,const ExiController& ctl,const ExiMxDevice& mx){
        if(!same(ctl,mx)||stage_<1||stage_>2||q.channel!=0||q.device!=1||q.dma||
           q.direction!=1u||q.length<1u||q.length>4u||!q.token||q.token<=token_||
           ctl.pending(0)||(ctl.read(0,0)&0x380u)!=0x100u||
           !(ctl.read(0,0)&WiiIrqBanks::TC_INT)||
           (ctl.read(0,12)&0x3fu)!=(((q.length-1u)<<4)|4u)||ctl.read(0,16)!=q.tx)return fail(2);
        const auto epoch=ctl.selection_epoch(0);
        if(stage_==1){
            if(epoch<=epoch_||q.length!=4u||q.tx!=0xa0000100u+offset_*64u||
               mx.sram()!=old_||mx.dirty()!=dirty_)return fail(3);
            epoch_=epoch;stage_=2;
        }else{
            if(epoch!=epoch_||q.length>64u-cursor_)return fail(4);
            for(unsigned i=0;i<q.length;++i){
                const auto v=uint8_t(q.tx>>(24u-i*8u));
                if(v!=wanted_[cursor_+i])return fail(4);
            }
            for(unsigned i=0;i<q.length;++i)observed_[cursor_+i]=wanted_[cursor_+i];
            if(mx.sram()!=observed_||!mx.dirty())return fail(5);
            cursor_+=q.length;
            if(cursor_==64u)stage_=3;
        }
        token_=q.token;++completed_;return true;
    }
    // The command and payload must have completed under one chip-select
    // epoch. Only a later deselection may finalize the witness.
    bool finish(const ExiController& ctl,const ExiMxDevice& mx){
        if(!same(ctl,mx)||stage_!=3||cursor_!=64u||ctl.pending(0)||
           (ctl.read(0,0)&0x380u)||ctl.selection_epoch(0)<=epoch_||
           mx.sram()!=wanted_||!mx.dirty())return fail(6);
        stage_=4;return true;
    }
private:
    const ExiController* ctl_=nullptr;const ExiMxDevice* mx_=nullptr;
    Bytes old_{},wanted_{},observed_{};
    unsigned stage_=0,error_=0,offset_=0,cursor_=0,completed_=0;
    uint64_t token_=0,epoch_=0;bool dirty_=false;
    bool fail(unsigned e){if(!error_)error_=e;return false;}
    bool same(const ExiController& ctl,const ExiMxDevice& mx)const{return !error_&&ctl_==&ctl&&mx_==&mx;}
};
}
