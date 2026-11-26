#pragma once
#include "wii_handler_suffix_guard_v868.h"
#include "wii_alarm_cancel_return_v782.h"
#include "wii_postack_transfer_device_v771.h"
namespace undercover::wii {
// Continue the same third token after SITransfer, without clearing its PI
// source or granting the retired second ACK any MMIO ownership.
class ThirdAlarmSuffixRoute {
public:
    explicit ThirdAlarmSuffixRoute(AlarmCancelExpectation e):expected_(e),alarm_(e){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned suffix_visits()const{return suffix_.visits();}
    const AlarmCancelReturnWitness& alarm()const{return alarm_;}
    template<class C>bool start(C& c,uint32_t resume,std::span<const HandlerSuffixLabel> rows,PostAckTransferDevice& dev){
        if(stage_||error_||!safe(c)||!held(dev)||c.pc!=resume||
           !suffix_.start(c,rows,resume,256u,true))return fail(1);
        cpu_=&c;rows_=rows;last_=c.inst_count;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;stage_=1;
        return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,PostAckTransferDevice& dev){
        if(!same(c)||stage_>2u||c.inst_count-last_!=unsigned(seen_))return fail(2);
        if(seen_&&!dev.after_return_at(c.inst_count))return fail(2);
        last_=c.inst_count;seen_=true;
        if(!held(dev))return fail(2);
        if(read_reg_<32u){
            const auto got=dev.suffix_status_value();
            if(!got||c.gpr[read_reg_]!=*got)return fail(3);
            read_reg_=32u;
        }
        if(write_due_){
            if(dev.suffix_status_writes()!=1u)return fail(3);
            write_due_=false;
        }
        const auto a=PostAckTransferDevice::word_access(c,w);
        const auto off=PostAckTransferDevice::offset(a.address);
        if(stage_==2u){
            if(off||overlaps_si(a.address))return fail(4);
            if(alarm_.stage()==3u){
                if(!alarm_.returned(c,pc,w,true))return fail(5);
                stage_=3u;return true;
            }
            return alarm_.native_before(c,pc,w,true)?true:fail(5);
        }
        const HandlerSuffixLabel* row=nullptr;
        for(const auto& x:rows_)if(x.pc==pc){row=&x;break;}
        if(!row)return fail(3);
        using Access=PostAckTransferDevice::Access;
        const bool rd=off&&*off==SiController::Status&&a.kind==Access::Read;
        const bool wr=off&&*off==SiController::Status&&a.kind==Access::Write;
        if((off||overlaps_si(a.address))&&!rd&&!wr)return fail(4);
        if(!suffix_.before(c,pc,w,row->ordinal,row->kind,rd,wr))return fail(3);
        if(row->kind||w==0x4e800020u){
            if(row->kind!=1u||row->ordinal!=5u||pc!=expected_.site||w!=expected_.branch||
               !alarm_.start(c,pc,w,true))return fail(5);
            stage_=2u;return true;
        }
        if(rd){
            if(!dev.arm_suffix_status_read(c.inst_count,a.address))return fail(4);
            read_reg_=(w>>21)&31u;
        }
        if(wr){
            if(!a.store||!dev.arm_suffix_status_write(c.inst_count,a.address,*a.store))return fail(4);
            write_due_=true;
        }
        return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,const PostAckTransferDevice& dev){
        return same(c)&&stage_==2u&&c.inst_count==last_&&held(dev)&&alarm_.entry(c,pc,true)?true:fail(6);
    }
    template<class C>bool poll(C& c,const PostAckTransferDevice& dev){
        return same(c)&&stage_==2u&&c.inst_count==last_&&held(dev)&&alarm_.poll(c,true)?true:fail(6);
    }
private:
    AlarmCancelExpectation expected_;AlarmCancelReturnWitness alarm_;HandlerSuffixGuard suffix_;
    std::span<const HandlerSuffixLabel> rows_{};const void* cpu_=nullptr;
    uint64_t last_=0;uint32_t msr_=0,srr0_=0,srr1_=0;
    unsigned stage_=0,error_=0,read_reg_=32u;bool seen_=false,write_due_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool held(const PostAckTransferDevice& d){return d.stage()==2u&&d.token()==3u&&d.follow_stage()==3u&&!d.pending()&&d.held_now();}
    static bool overlaps_si(uint32_t a){
        const uint32_t p=a&0x3fffffffu;
        return (p<0x0d006500u&&uint64_t(p)+4u>0x0d006400u)||(p<0x0d806500u&&uint64_t(p)+4u>0x0d806400u);
    }
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool same(C& c)const{return cpu_==&c&&stage_&&!error_&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_;}
};
}
