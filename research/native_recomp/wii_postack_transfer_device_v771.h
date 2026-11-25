#pragma once
#include "wii_si_follow_on_v750.h"
#include "wii_si_completion_ack_v668.h"
namespace undercover::wii {
// Scoped device seam for one authenticated transfer after the first ACK.
// Each before() follows the real scheduler's native instruction tick.
// MMIO arguments are matched to the caller's decoded effective address.
// Never writes PI directly, advances time, or fabricates a response.
class PostAckTransferDevice {
public:
    enum class Access : unsigned {None,Read,Write};
    unsigned stage()const noexcept{return stage_;}
    unsigned failure()const noexcept{return error_;}
    unsigned reads()const noexcept{return reads_;}
    unsigned writes()const noexcept{return writes_;}
    unsigned follow_stage()const noexcept{return follow_.stage();}
    unsigned follow_failure()const noexcept{return follow_.failure();}
    uint64_t token()const noexcept{return follow_.token();}
    bool pending()const{return ctl_&&ctl_->pending().has_value();}
    unsigned suffix_status_reads()const noexcept{return status_reads_;}
    std::optional<uint32_t> suffix_status_value()const{return status_reads_==1u&&!status_pending_&&!error_?std::optional<uint32_t>{status_value_}:std::nullopt;}
    unsigned suffix_status_writes()const noexcept{return status_writes_;}
    bool held_now()const{return tick_&&held(*tick_);}
    bool held(uint64_t tick)const{
        return (stage_==1||stage_==2)&&!error_&&!armed_&&!status_pending_&&!status_write_pending_&&tick==last_&&common()&&
            (follow_.stage()?follow_.held(tick):quiescent());
    }
    static std::optional<unsigned> offset(uint32_t a)noexcept{
        if((a&0xc0000000u)==0x40000000u||(a&3u))return std::nullopt;
        const uint32_t p=(a&0x3fffffffu)&~0x00800000u;
        if(p<0x0d006400u||p>=0x0d006500u)return std::nullopt;
        const auto off=p-0x0d006400u;
        return SiController::supported(off)?std::optional<unsigned>{off}:std::nullopt;
    }
    struct WordAccess{
        Access kind=Access::None;uint32_t address=0;std::optional<uint32_t> store;
    };
    // Exact integer word memory instructions emitted by the pinned PPC
    // translator. Reversed stores use the original big-endian bus value.
    template<class C>static WordAccess word_access(const C& c,uint32_t w){
        const auto op=w>>26,xo=(w>>1)&1023u,ra=(w>>16)&31u,rb=(w>>11)&31u,rs=(w>>21)&31u;
        const auto base=ra?c.gpr[ra]:0u;
        const bool read=SiCompletionAckTrace::word_load(w),write=SiCompletionAckTrace::word_store(w);
        if(!read&&!write)return {};
        const uint32_t a=op==31u?base+c.gpr[rb]:base+((w&0xffffu)^0x8000u)-0x8000u;
        if(read)return {Access::Read,a,std::nullopt};
        uint32_t v=c.gpr[rs];
        if(op==31u&&xo==662u)v=(v>>24)|((v>>8)&0xff00u)|((v<<8)&0xff0000u)|(v<<24);
        return {Access::Write,a,v};
    }
    bool begin(SiController& ctl,const std::atomic<uint32_t>& cause,const std::atomic<uint32_t>& mask,
               const SiCompletionAckTrace& ack,const uint64_t& tick,unsigned ch,bool idle,
               std::optional<std::array<uint8_t,3>> response,uint64_t latency){
        if(stage_||error_||!ack.owns_postack(ctl,cause,mask,tick)||ch>3||!latency||latency>8190u||
           tick>UINT64_MAX-8192u||ctl.pending()||!(mask.load()&SiController::PI_SI)||
           (cause.load()&SiController::PI_SI)||ctl.issued_tokens()==UINT64_MAX)return fail(1);
        ctl_=&ctl;cause_=&cause;mask_=&mask;tick_=&tick;other_=cause.load();mask_before_=mask.load();
        seq_=ctl.issued_tokens();initial_control_=ctl.read(SiController::Control);
        status_=ctl.read(SiController::Status);poll_=ctl.read(SiController::Poll);
        for(unsigned i=0;i<32;++i)buffer_[i]=ctl.read(SiController::Buffer+4*i);
        ch_=ch;idle_=idle;response_=response;latency_=latency;start_=last_=tick;stage_=1;return true;
    }
    bool before(uint64_t tick,Access access=Access::None,uint32_t address=0,std::optional<uint32_t> store_value=std::nullopt){
        if(stage_!=1||error_||armed_||tick-last_!=1u||tick-start_>8192u||!common())return fail(2);
        last_=tick;
        if(!device(tick))return fail(3);
        if(access==Access::None)return address==0&&!store_value?true:fail(2);
        if(access==Access::Read&&store_value)return fail(2);
        if(!idle_||access>Access::Write||reads_+writes_>=64u)return fail(2);
        const auto off=offset(address);
        if(!off||*off==SiController::Poll)return fail(2);
        armed_=true;access_=access;off_=*off;store_value_=store_value;return true;
    }
    // One explicitly authenticated resumed-handler status read. Neither
    // the completed response nor the interrupt source may be changed.
    bool arm_suffix_status_read(const uint64_t& tick,uint32_t address){
        if(stage_!=2u||&tick!=tick_||status_pending_||status_reads_||!held(tick)||
           follow_.stage()!=3u||pending()||offset(address)!=SiController::Status)return fail(8);
        status_value_=ctl_->read(SiController::Status);status_pending_=true;return true;
    }
    bool arm_suffix_status_write(const uint64_t& tick,uint32_t address,uint32_t value){
        if(stage_!=2u||&tick!=tick_||status_write_pending_||status_writes_||status_reads_!=1u||
           !held(tick)||follow_.stage()!=3u||pending()||offset(address)!=SiController::Status||
           (value&~0x0f0f0f0fu))return fail(9);
        status_before_write_=ctl_->read(SiController::Status);
        status_write_value_=value;status_write_pending_=true;return true;
    }
    bool read(SiController& ctl,unsigned off,uint32_t& result){
        if(stage_==2u){
            if(error_||!status_pending_||status_reads_||&ctl!=ctl_||off!=SiController::Status||
               !tick_||*tick_!=last_||!common()||follow_.stage()!=3u||!follow_.held(last_)||
               ctl.read(off)!=status_value_)return fail(8);
            result=ctl.read(off);status_pending_=false;++status_reads_;return true;
        }
        if(!consume(ctl,off,Access::Read))return false;
        result=ctl.read(off);++reads_;return true;
    }
    bool write(SiController& ctl,unsigned off,uint32_t value){
        if(stage_==2u){
            if(error_||!status_write_pending_||status_writes_||&ctl!=ctl_||off!=SiController::Status||
               value!=status_write_value_||!tick_||*tick_!=last_||!common()||!follow_.held(last_)||
               ctl.read(off)!=status_before_write_)return fail(9);
            try{ctl.write(off,value);}catch(...){return fail(9);}
            if(!follow_.accept_status_w1c(last_,status_before_write_,value))return fail(9);
            status_write_pending_=false;++status_writes_;return true;
        }
        if((store_value_&&value!=*store_value_)||!consume(ctl,off,Access::Write)||follow_.stage())return fail(4);
        if(off==SiController::Control){
            // The only accepted COMCSR modification is an exact new type
            // transaction on the authenticated channel, with TC mask held.
            if(!follow_.arm(ctl,*cause_,*mask_,last_,value,ch_,response_,latency_))return fail(5);
            try{ctl.write(off,value);}catch(...){return fail(5);}
            if(!follow_.started(last_))return fail(5);
        }else if(off==SiController::Status){
            if(value&~0x0f0f0f0fu)return fail(4);
            ctl.write(off,value);status_&=~value;
            if(!quiescent())return fail(4);
        }else if(off>=SiController::Buffer&&off<0x100u&&!(off&3u)){
            ctl.write(off,value);buffer_[(off-SiController::Buffer)/4u]=value;
            if(!quiescent())return fail(4);
        }else return fail(4);
        ++writes_;return true;
    }
    // Returns at the next authenticated caller boundary, AFTER before().
    // A legitimate new TC may already be pending in PI. Never clear it here.
    bool finish(uint64_t tick,uint32_t result){
        if(stage_!=1||error_||armed_||tick!=last_||!common()||result!=unsigned(idle_))return fail(6);
        if(idle_){
            if(follow_.stage()<2||!reads_||!writes_||ctl_->issued_tokens()!=seq_+1u)return fail(6);
            if(!follow_.held(tick))return fail(6);
        }else if(follow_.stage()||reads_||writes_||!quiescent())return fail(6);
        stage_=2;return true;
    }
    // A later authenticated masked native visit may continue observing the
    // same request until completion. No new MMIO accepted after return.
    bool after_return_at(const uint64_t& tick){
        if(&tick!=tick_)return fail(7);
        return after_return(tick);
    }
    bool after_return(uint64_t tick){
        if(stage_!=2||error_||status_pending_||status_write_pending_||tick-last_!=1u||tick-start_>8192u||!common())return fail(7);
        last_=tick;return device(tick)?true:fail(7);
    }
private:
    SiController* ctl_=nullptr;const std::atomic<uint32_t>* cause_=nullptr,*mask_=nullptr;
    const uint64_t* tick_=nullptr;
    SiFollowOnWitness follow_;
    std::array<uint32_t,32> buffer_{};
    std::optional<std::array<uint8_t,3>> response_;
    std::optional<uint32_t> store_value_;
    unsigned stage_=0,error_=0,reads_=0,writes_=0,ch_=0,off_=0;
    uint64_t seq_=0,start_=0,last_=0,latency_=0;
    uint32_t other_=0,mask_before_=0,initial_control_=0,status_=0,poll_=0;
    unsigned status_reads_=0;uint32_t status_value_=0;bool status_pending_=false;
    unsigned status_writes_=0;uint32_t status_before_write_=0,status_write_value_=0;bool status_write_pending_=false;
    bool idle_=false,armed_=false;Access access_=Access::None;
    bool fail(unsigned n)noexcept{if(!error_)error_=n;return false;}
    bool common()const{return ctl_&&mask_->load()==mask_before_&&(cause_->load()&~SiController::PI_SI)==other_&&ctl_->read(SiController::Poll)==poll_;}
    bool quiescent()const{
        if(!common()||cause_->load()!=other_||ctl_->pending()||ctl_->issued_tokens()!=seq_||
           ctl_->read(SiController::Control)!=initial_control_||ctl_->read(SiController::Status)!=status_)return false;
        for(unsigned i=0;i<32;++i)if(ctl_->read(SiController::Buffer+4*i)!=buffer_[i])return false;
        return true;
    }
    bool device(uint64_t tick){
        if(!follow_.stage())return quiescent();
        if(follow_.stage()==2)return follow_.observe(tick);
        return follow_.held(tick);
    }
    bool consume(SiController& ctl,unsigned off,Access access){
        if(stage_!=1||error_||!armed_||&ctl!=ctl_||off_!=off||access_!=access||!common())return fail(4);
        armed_=false;access_=Access::None;store_value_.reset();return true;
    }
};
}
