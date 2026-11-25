#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Read-only, bounded snapshot of the actual OSAlarm queue. The original
// cancellation implementation remains responsible for every guest write.
class AlarmCancelQueueWitness {
public:
    enum class Lane:unsigned {Inactive,Middle,Tail,Singleton,Head};
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned mismatch()const{return mismatch_;}
    bool deferred_clear()const{return deferred_clear_;}
    Lane lane()const{return lane_;}
    unsigned nodes()const{return count_;}
    bool timer_required()const{return lane_==Lane::Head;}
    uint64_t deadline()const{return deadline_;}
    uint32_t expected_dec()const{return expected_dec_;}
    template<class C>bool capture(C& c,uint32_t head,uint32_t tail,uint32_t alarm){
        if(stage_||error_||!safe(c)||!mapped(c,head,4)||!mapped(c,tail,4)||head==tail||
           !mapped(c,alarm,40)||overlap(alarm,40,head,4)||overlap(alarm,40,tail,4)||
           c.inst_count>UINT64_MAX-4096u)return fail(1);
        cpu_=&c;head_=head;tail_=tail;alarm_=alarm;start_=c.inst_count;msr_=c.msr;
        srr0_=c.srr0;srr1_=c.srr1;gp_=c.gpr;cr_=pack(c)&0x00fff000u;
        dec_=c.dec_value;dec_tick_=c.dec_written_tb;dec_pending_=c.dec_irq_pending;
        old_head_=c.mmu.read32(head);old_tail_=c.mmu.read32(tail);
        if(bool(old_head_)!=bool(old_tail_))return fail(2);
        if(!read(c,alarm_,target_))return fail(2);
        uint32_t pc=old_head_,prev=0;
        while(pc){
            if(count_==queue_.size()||overlap(pc,40,head,4)||overlap(pc,40,tail,4)||
               !read(c,pc,queue_[count_])||!queue_[count_].words[0]||
               queue_[count_].words[4]!=prev)return fail(2);
            for(unsigned i=0;i<count_;++i)if(overlap(pc,40,queue_[i].address,40))return fail(2);
            if(pc==alarm_)index_=count_;
            else if(overlap(pc,40,alarm_,40))return fail(2);
            prev=pc;pc=queue_[count_++].words[5];
        }
        if(prev!=old_tail_||bool(target_.words[0])!=(index_<count_))return fail(2);
        if(index_>=count_)lane_=Lane::Inactive;
        else if(count_==1)lane_=Lane::Singleton;
        else if(index_==0){lane_=Lane::Head;deadline_=(uint64_t(queue_[1].words[2])<<32)|queue_[1].words[3];}
        else if(index_+1==count_)lane_=Lane::Tail;
        else lane_=Lane::Middle;
        stage_=1;return true;
    }
    // Must be called only on the authenticated original time-helper return.
    template<class C>bool time_returned(C& c,uint64_t time){
        if(stage_!=1||!timer_required()||!common(c)||c.inst_count<=start_||
           ((uint64_t(c.gpr[3])<<32)|c.gpr[4])!=time||!queue_matches(c,false)||!dec_unchanged(c))return fail(3);
        expected_dec_=deadline_<=time?0u:deadline_-time>0x7fffffffu?0x7fffffffu:uint32_t(deadline_-time);
        time_tick_=c.inst_count;stage_=2;return true;
    }
    // Before exact original mtspr DEC, after the native tick.
    template<class C>bool timer_before(C& c,uint32_t word){
        if(stage_!=2||!common(c)||c.inst_count<=time_tick_||word!=0x7c7603a6u||
           c.gpr[3]!=expected_dec_||!dec_unchanged(c)||!queue_matches(c,false))return fail(4);
        write_tick_=c.inst_count;stage_=3;return true;
    }
    // At the exact successor BLR, after the real translated DEC write.
    template<class C>bool timer_after(C& c){
        if(stage_!=3||!common(c)||c.inst_count-write_tick_!=1u||
           !dec_written(c)||!queue_matches(c,false))return fail(4);
        stage_=4;return true;
    }
    template<class C>bool finish(C& c){
        if(stage_!=(timer_required()?4u:1u)||!common(c)||c.inst_count<=start_||!abi(c)||
           !queue_matches(c,true)||!(timer_required()?dec_written(c):dec_unchanged(c)))return fail(5);
        stage_=5;return true;
    }
private:
    struct Node{uint32_t address=0;std::array<uint32_t,10> words{};};
    std::array<Node,64> queue_{};Node target_{};
    const void* cpu_=nullptr;std::array<uint32_t,32> gp_{};
    unsigned stage_=0,error_=0,count_=0,index_=64;Lane lane_=Lane::Inactive;
    uint32_t head_=0,tail_=0,alarm_=0,old_head_=0,old_tail_=0,msr_=0,srr0_=0,srr1_=0,cr_=0,expected_dec_=0;
    uint64_t start_=0,deadline_=0,time_tick_=0,write_tick_=0,dec_=0,dec_tick_=0;
    bool dec_pending_=false,cleared_=false,deferred_clear_=false;unsigned mismatch_=0;
    bool mismatch(unsigned n){mismatch_=n;return false;}
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    static bool overlap(uint32_t a,unsigned n,uint32_t b,unsigned m){return uint64_t(a)<uint64_t(b)+m&&uint64_t(b)<uint64_t(a)+n;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){
        if(!n||(a&3u)||a<0x80000000u||uint64_t(a)+n>0x81800000u)return false;
        for(unsigned i=0;i<n;i+=4)if(!c.mmu.get_ptr(a+i)||!c.mmu.get_ptr(a+i+3u))return false;
        return true;
    }
    template<class C>static bool read(C& c,uint32_t a,Node& out){
        if(!mapped(c,a,40))return false;
        out.address=a;for(unsigned i=0;i<10;++i)out.words[i]=c.mmu.read32(a+4*i);
        return true;
    }
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>bool common(C& c)const{return !error_&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_&&c.inst_count>=start_&&c.inst_count-start_<=4096u;}
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||c.gpr[13]!=gp_[13]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    template<class C>bool dec_unchanged(C& c)const{return c.dec_value==dec_&&c.dec_written_tb==dec_tick_&&c.dec_irq_pending==dec_pending_;}
    template<class C>bool dec_written(C& c)const{return c.dec_value==expected_dec_&&c.dec_written_tb==write_tick_&&c.dec_irq_pending;}
    template<class C>bool queue_matches(C& c,bool final){
        if(!mapped(c,head_,4)||!mapped(c,tail_,4))return mismatch(1);
        const bool active=index_<count_;
        const uint32_t prev=target_.words[4],next=target_.words[5];
        const uint32_t h=active&&index_==0?next:old_head_,t=active&&index_+1==count_?prev:old_tail_;
        if(c.mmu.read32(head_)!=h||c.mmu.read32(tail_)!=t)return mismatch(2);
        Node actual;auto wanted=target_.words;
        if(!read(c,alarm_,actual))return mismatch(3);
        const auto handler=actual.words[0];
        if(handler==0)cleared_=true;
        else if(final||!timer_required()||cleared_||handler!=wanted[0])return mismatch(4);
        else deferred_clear_=true;
        wanted[0]=handler;
        if(actual.words!=wanted)return mismatch(5);
        for(unsigned i=0;i<count_;++i){
            if(i==index_)continue;
            auto expected=queue_[i].words;
            if(active&&queue_[i].address==prev)expected[5]=next;
            if(active&&queue_[i].address==next)expected[4]=prev;
            if(!read(c,queue_[i].address,actual)||actual.words!=expected)return mismatch(6);
        }
        return true;
    }
};
}
