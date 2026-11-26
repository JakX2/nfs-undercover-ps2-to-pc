#pragma once
#include "wii_handler_suffix_guard_v868.h"
#include "wii_alarm_cancel_return_v782.h"
#include "wii_postack_transfer_device_v771.h"
#include "wii_external_return_v706.h"
#include "wii_callback_prefix_v800.h"
#include "wii_callback_identity_v796.h"
#include "wii_callback_time_v810.h"
#include "wii_callback_frontier_v829.h"
#include "wii_wireless_wrapper_v844.h"
#include <optional>
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
        cpu_=&c;device_=&dev;rows_=rows;last_=c.inst_count;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;stage_=1;
        return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,PostAckTransferDevice& dev){
        if(!same(c)||device_!=&dev||stage_>2u||c.inst_count-last_!=unsigned(seen_))return fail(2);
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
                return_pc_=pc;return_word_=w;stage_=3u;return true;
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
        return same(c)&&device_==&dev&&stage_==2u&&c.inst_count==last_&&held(dev)&&alarm_.entry(c,pc,true)?true:fail(6);
    }
    template<class C>bool poll(C& c,const PostAckTransferDevice& dev){
        return same(c)&&device_==&dev&&stage_==2u&&c.inst_count==last_&&held(dev)&&alarm_.poll(c,true)?true:fail(6);
    }
    template<class C>bool finished_at(C& c,uint32_t pc,uint32_t w,const PostAckTransferDevice& dev)const{
        return stage_==3u&&same(c)&&device_==&dev&&held(dev)&&c.inst_count==last_&&
               c.pc==pc&&pc==return_pc_&&w==return_word_&&alarm_.stage()==4u;
    }
private:
    const PostAckTransferDevice* device_=nullptr;
    uint32_t return_pc_=0,return_word_=0;
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
// Same held third token across the alarm return and callback prefix.
// This route does not grant the retired ACK any bus ownership. Its
// exact rows and full callback identity must come from the private
// native installer, not a guest-provided address or arbitrary target.
template<std::size_t P,std::size_t S,std::size_t N>
class ThirdAlarmCallbackRoute {
public:
    ThirdAlarmCallbackRoute(uint32_t root,uint32_t save,std::array<uint32_t,P> prefix,
            std::array<uint32_t,S> leaf,std::array<uint32_t,N> words,std::array<uint32_t,2> sites):
        root_(root),words_(words),sites_(sites),prefix_(root,save,prefix,leaf){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned suffix_visits()const{return suffix_.visits();}
    unsigned prefix_visits()const{return prefix_.visits();}
    unsigned writes()const{return prefix_.writes();}
    unsigned prefix_failure()const{return prefix_.failure();}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,const ThirdAlarmSuffixRoute& alarm,
            PostAckTransferDevice& dev,const ExternalReturnWitness& frame,uint32_t context,
            std::span<const HandlerSuffixLabel> rows){
        if(stage_||error_||!alarm.finished_at(c,pc,w,dev)||!frame.saved_integer(c,context).ok()||
           !suffix_.start(c,rows,pc,256u,true))return fail(1);
        cpu_=&c;dev_=&dev;frame_=&frame;context_=context;rows_=rows;last_=c.inst_count;stage_=1;
        return true;
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w){
        if(!common(c)||(stage_!=1u&&stage_!=2u)||c.inst_count-last_!=unsigned(seen_)||
           (seen_&&!dev_->after_return_at(c.inst_count))||!held())return fail(2);
        last_=c.inst_count;seen_=true;
        const auto a=PostAckTransferDevice::word_access(c,w);const uint32_t p=a.address&0x3fffffffu;
        if(PostAckTransferDevice::offset(a.address)||
           (p<0x0d006500u&&uint64_t(p)+4u>0x0d006400u)||
           (p<0x0d806500u&&uint64_t(p)+4u>0x0d806400u))return fail(3);
        if(stage_==2u){
            if(!prefix_.before(c,pc,w,true))return fail(5);
            if(prefix_.stage()==6u)stage_=3u;
            return true;
        }
        const HandlerSuffixLabel* row=nullptr;
        for(const auto& x:rows_)if(x.pc==pc){row=&x;break;}
        if(!row||!suffix_.before(c,pc,w,row->ordinal,row->kind))return fail(3);
        if(row->kind||w==0x4e800020u){
            if(row->ordinal!=6u||row->kind!=2u||c.gpr[3]>=4u||
               classify_callback_identity(c,pc,w,row->ordinal,row->kind,root_,words_,sites_)!=2u||
               !prefix_.start_dispatch(c,pc,w,true,true))return fail(4);
            channel_=c.gpr[3];stage_=2u;
        }
        return true;
    }
    template<class C>bool poll(C& c){
        return stage_==2u&&common(c)&&c.inst_count==last_&&held()&&prefix_.dispatch_poll(c,true)?true:fail(6);
    }
    template<class C>bool entry(C& c,uint32_t pc){
        const bool outer=prefix_.stage()==1u;
        if(stage_!=2u||!common(c)||c.inst_count-last_!=unsigned(outer)||
           (outer&&!dev_->after_return_at(c.inst_count))||!held()||!prefix_.entry(c,pc,true))return fail(6);
        last_=c.inst_count;return true;
    }
    // The prefix has already charged this exact label to the device.
    // Do not advance it again when handing over to the time witness.
    template<class C>bool start_time(C& c,uint32_t pc,uint32_t w,CallbackTimeExpectation e){
        if(stage_!=3u||time_||!common(c)||!held()||c.inst_count!=last_||
           prefix_.stage()!=6u||pc!=prefix_.resume()||e.callback!=root_||e.resume!=pc||
           P>N||w!=words_[P-1u])return fail(7);
        time_.emplace(e);
        if(!time_->start(c,pc,w,true,true)||!time_->before(c,pc,w,true))return fail(7);
        stage_=4u;return true;
    }
    unsigned time_failure()const{return time_?time_->failure():0u;}
    const CallbackTimeWitness* time_witness()const{return time_?&*time_:nullptr;}
    template<class C>bool time_before(C& c,uint32_t pc,uint32_t w){
        if(stage_!=4u||!time_||!common(c)||c.inst_count-last_!=1u||
           !dev_->after_return_at(c.inst_count)||!held()||!time_->before(c,pc,w,true))return fail(8);
        last_=c.inst_count;
        if(time_->stage()==5u){time_resume_=pc;time_word_=w;stage_=5u;}
        return true;
    }
    template<class C>bool time_poll(C& c){
        return stage_==4u&&time_&&common(c)&&c.inst_count==last_&&held()&&time_->poll(c,true)?true:fail(9);
    }
    template<class C>bool time_entry(C& c,uint32_t pc){
        return stage_==4u&&time_&&common(c)&&c.inst_count==last_&&held()&&time_->entry(c,pc,true)?true:fail(9);
    }
    // The time return label has already advanced the held device.
    template<class C>bool start_frontier(C& c,uint32_t pc,uint32_t w,CallbackFrontierExpectation e){
        if(stage_!=5u||frontier_||!time_||time_->stage()!=5u||!common(c)||!held()||
           c.inst_count!=last_||pc!=time_resume_||w!=time_word_||e.root!=root_||e.resume!=pc||channel_>=4u)
            return fail(10);
        frontier_.emplace(e);
        if(!frontier_->start(c,pc,w,channel_,true,true)||!frontier_->before(c,pc,w,true))return fail(10);
        stage_=frontier_->stage()==2u?7u:6u;
        if(stage_==7u){frontier_site_=pc;frontier_word_=w;}return true;
    }
    template<class C>bool frontier_before(C& c,uint32_t pc,uint32_t w){
        if(stage_!=6u||!frontier_||!common(c)||c.inst_count-last_!=1u||
           !dev_->after_return_at(c.inst_count)||!held()||!frontier_->before(c,pc,w,true))return fail(11);
        last_=c.inst_count;if(frontier_->stage()==2u){frontier_site_=pc;frontier_word_=w;stage_=7u;}return true;
    }
    unsigned frontier_failure()const{return frontier_?frontier_->failure():0u;}
    const CallbackFrontierWitness* frontier_witness()const{return frontier_?&*frontier_:nullptr;}
    // Retain the asserted third token across the unchanged wireless setter.
    // The previous frontier already paid the call-site tick.
    template<class C>bool start_wireless(C& c,uint32_t pc,uint32_t w,WirelessExpectation e){
        if(stage_!=7u||wireless_||!frontier_||frontier_->stage()!=2u||frontier_->ordinal()!=3u||
           frontier_->zero_id()!=1u||!common(c)||!held()||c.inst_count!=last_||
           pc!=frontier_site_||w!=frontier_word_||c.gpr[3]!=channel_||c.gpr[4]!=0u)return fail(12);
        wireless_.emplace(e);
        if(!wireless_->start(c,pc,w,true,true)||wireless_->changed()||wireless_->ordinal()!=3u)return fail(12);
        stage_=8u;return true;
    }
    template<class C>bool wireless_before(C& c,uint32_t pc,uint32_t w){
        if(stage_!=8u||!wireless_||!common(c)||c.inst_count-last_!=1u||
           !dev_->after_return_at(c.inst_count)||!held()||!wireless_->before(c,pc,w,true))return fail(13);
        last_=c.inst_count;if(wireless_->stage()==2u){wireless_resume_=pc;wireless_word_=w;stage_=9u;}return true;
    }
    template<class C>bool wireless_entry(C& c,uint32_t pc){
        return stage_==8u&&wireless_&&common(c)&&c.inst_count==last_&&held()&&
               wireless_->entry(c,pc,true)&&wireless_->stage()==1u?true:fail(14);
    }
    unsigned wireless_failure()const{return wireless_?wireless_->failure():0u;}
    const WirelessWrapperWitness* wireless_witness()const{return wireless_?&*wireless_:nullptr;}
private:
    std::optional<WirelessWrapperWitness> wireless_;
    uint32_t frontier_site_=0,frontier_word_=0,wireless_resume_=0,wireless_word_=0;
    std::optional<CallbackTimeWitness> time_;
    std::optional<CallbackFrontierWitness> frontier_;
    uint32_t channel_=4u,time_resume_=0,time_word_=0;
    uint32_t root_,context_=0;std::array<uint32_t,N> words_;std::array<uint32_t,2> sites_;
    CallbackPrefixWitness<P,S> prefix_;HandlerSuffixGuard suffix_;
    std::span<const HandlerSuffixLabel> rows_{};const void* cpu_=nullptr;
    PostAckTransferDevice* dev_=nullptr;const ExternalReturnWitness* frame_=nullptr;
    uint64_t last_=0;unsigned stage_=0,error_=0;bool seen_=false;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    bool held()const{return dev_&&dev_->stage()==2u&&dev_->token()==3u&&dev_->follow_stage()==3u&&!dev_->pending()&&dev_->held_now();}
    template<class C>bool common(C& c)const{
        return cpu_==&c&&!error_&&frame_&&dev_&&frame_->saved_integer(c,context_).ok()&&
               c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);
    }
};
}
