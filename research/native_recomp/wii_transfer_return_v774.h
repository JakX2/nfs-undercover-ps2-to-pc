#pragma once
#include "wii_si_first_helper_v680.h"
#include "wii_postack_os_leaf_v703.h"
#include "wii_gpr_restore_v736.h"
#include "wii_postack_transfer_device_v771.h"
#include <array>
#include <cstdint>
namespace undercover::wii {
struct TransferReturnExpectation{
    uint32_t site,root,end,branch,entry_word;
    SiHelperExpectation save;
    PostAckLeafExpectation disable;
    uint32_t data;
    std::array<PostAckLeafExpectation,2> irq_restore;
    GprRestoreExpectation restore;
};
class TransferReturnWitness{
public:
    explicit TransferReturnWitness(TransferReturnExpectation e):e_(e),save_(e.save),disable_(e.disable),irq_{PostAckOsLeaf(e.irq_restore[0]),PostAckOsLeaf(e.irq_restore[1])},restore_(e.restore){}
    unsigned stage()const{return stage_;}
    unsigned failure()const{return error_;}
    unsigned visits()const{return visits_;}
    unsigned channel()const{return channel_;}
    bool type()const{return type_;}
    bool idle()const{return idle_;}
    unsigned total()const{return total_;}
    unsigned irq_lane()const{return irq_lane_;}
    unsigned irq_done()const{return irq_lane_<2&&irq_[irq_lane_].stage()==4;}
    unsigned restore_done()const{return restore_.stage()==4;}
    unsigned save_done()const{return save_.stage()==4;}
    unsigned disable_done()const{return disable_.stage()==4;}
    template<class C>bool start(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack){
        if(stage_||error_||!safe(c)||!ack.postack_held()||pc!=e_.site||w!=e_.branch||
           w>>26!=18u||(w&3u)!=1u||target(pc,w)!=e_.root||!mapped(c,e_.data,20)||
           !mapped(c,e_.root,4)||c.mmu.read32(e_.root)!=e_.entry_word||
           c.gpr[3]>3u||c.inst_count>UINT64_MAX-2048u)return fail(1);
        cpu_=&c;gp_=c.gpr;msr_=c.msr;srr0_=c.srr0;srr1_=c.srr1;tick_=last_=c.inst_count;
        channel_=c.gpr[3];idle_=c.mmu.read32(e_.data)==0xffffffffu;
        for(unsigned i=0;i<5;++i)initial_data_[i]=c.mmu.read32(e_.data+4*i);
        cr_=pack(c)&0x00fff000u;
        type_=c.gpr[5]==1u&&c.gpr[7]==3u&&mapped(c,c.gpr[4],1)&&mapped(c,c.gpr[6],3)&&
              mapped(c,c.gpr[8],4)&&!(c.gpr[8]&3u)&&c.mmu.read8(c.gpr[4])==0u;
        if(!type_)return fail(1);
        stage_=1;return true;
    }
    template<class C>bool entry(C& c,uint32_t pc,SiCompletionAckTrace& ack,PostAckTransferDevice& device){
        if(!common(c,ack,device)||c.pc!=pc||c.inst_count!=last_)return fail(2);
        if(stage_==1){
            if(pc!=e_.root||c.lr!=e_.site+4u||c.gpr!=gp_)return fail(2);
            stage_=2;next_=pc;return true;
        }
        if(save_.stage()==1){if(!save_.entry(pc,c))return fail(2);return true;}
        if(disable_.stage()==1){if(!disable_.entry(pc,c))return fail(2);return true;}
        if(irq_lane_<2&&irq_[irq_lane_].stage()==1){if(!irq_[irq_lane_].entry(pc,c))return fail(2);return true;}
        if(restore_.stage()==1){if(!restore_.entry(c,pc))return fail(2);return true;}
        return fail(2);
    }
    template<class C>bool before(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack,PostAckTransferDevice& device){
        if(stage_!=2||!common(c,ack,device)||pending_||pc!=next_||pc<e_.root||pc>=e_.end||
           !mapped(c,pc,4)||c.mmu.read32(pc)!=w||c.inst_count-last_!=1u||++visits_>192u)return fail(3);
        if(save_.stage()==3&&!save_.returned(c,pc))return fail(4);
        if(disable_.stage()==3&&!disable_.returned(c,pc))return fail(4);
        if(irq_lane_<2&&irq_[irq_lane_].stage()==3&&!irq_[irq_lane_].returned(c,pc))return fail(4);
        if(restore_.stage()==3&&!restore_.returned(c,pc))return fail(4);
        last_=c.inst_count;next_=pc+4u;
        const unsigned op=w>>26,xo=(w>>1)&1023u;
        uint32_t addr=0;unsigned width=0,kind=0;
        const unsigned ra=(w>>16)&31u,rb=(w>>11)&31u;
        if(op>=32u&&op<=55u){
            addr=(ra?c.gpr[ra]:0u)+((w&0xffffu)^0x8000u)-0x8000u;
            kind=(op==36u||op==37u||op==38u||op==39u||op==44u||op==45u||op==47u||op>=52u)?2u:1u;
            width=op==34u||op==35u||op==38u||op==39u?1u:op>=40u&&op<=45u?2u:4u;
            if(op==46u||op==47u)width=4u*(32u-(w>>21&31u));
            if(op==50u||op==51u||op==54u||op==55u)width=8u;
        }else if(op==31u){
            switch(xo){
                case 23:case 55:case 534:kind=1;width=4;break;
                case 87:case 119:kind=1;width=1;break;
                case 279:case 311:case 343:case 375:case 790:kind=1;width=2;break;
                case 151:case 183:case 662:kind=2;width=4;break;
                case 215:case 247:kind=2;width=1;break;
                case 407:case 439:case 918:kind=2;width=2;break;
                default:break;
            }
            if(kind)addr=(ra?c.gpr[ra]:0u)+c.gpr[rb];
        }
        if(kind&&!mapped(c,addr,width)){
            const auto a=PostAckTransferDevice::word_access(c,w);
            if(!device.stage()||!save_done()||!disable_done()||width!=4u||!PostAckTransferDevice::offset(addr)||
               a.address!=addr||unsigned(a.kind)!=kind||!device.before(c.inst_count,a.kind,a.address,a.store))return fail(6);
        }else if(device.stage()){
            if(!device.before(c.inst_count))return fail(6);
        }else if(!ack.auxiliary_before())return fail(3);
        if(op==18u&&(w&1u)){
            if(pc==e_.save.site&&save_.stage()==0&&w==e_.save.branch&&!device.stage()){
                if(!save_.start(c,pc,w))return fail(4);
                return true;
            }
            if(pc==e_.disable.site&&save_.stage()==4&&disable_.stage()==0&&w==e_.disable.branch&&!device.stage()){
                if(!disable_.start(c,pc,w))return fail(4);
                return true;
            }
            if(!device.stage()||!save_done()||!disable_done())return fail(5);
            for(unsigned i=0;i<2;++i){
                if(pc==e_.irq_restore[i].site&&w==e_.irq_restore[i].branch&&irq_lane_==2){
                    irq_lane_=i;if(!irq_[i].start(c,pc,w))return fail(4);return true;
                }
            }
            if(pc==e_.restore.site&&w==e_.restore.branch&&irq_done()&&restore_.stage()==0){
                if(!restore_.start(c,pc,w,gp_))return fail(4);
                return true;
            }
            return fail(5);
        }
        if(w==0x4e800020u){
            if(!save_done()||!disable_done()||!irq_done()||!restore_done()||
               !abi(c)||c.lr!=e_.site+4u||c.gpr[3]!=unsigned(idle_))return fail(8);
            stage_=3;return true;
        }
        if(op==17u||(op==31u&&xo==146u)||(op==19u&&(xo==16u||xo==50u||xo==528u)))return fail(5);
        if(op==16u||op==18u){
            if(w&3u)return fail(5);
            const uint32_t dst=target(pc,w);
            if(dst<e_.root||dst>=e_.end)return fail(5);
            if(op==18u||taken(c,w))next_=dst;
            if(dst<=pc){pending_=true;poll_pc_=pc;poll_gp_=c.gpr;poll_cr_=pack(c);poll_lr_=c.lr;poll_ctr_=c.ctr;poll_xer_=c.xer;}
        }
        return next_>=e_.root&&next_<e_.end?true:fail(5);
    }
    template<class C>bool save_before(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack,PostAckTransferDevice& device){
        if(stage_!=2||device.stage()||!common(c,ack,device)||save_.stage()!=2||c.inst_count-last_!=1u||!save_.instruction(c,pc,w,ack))return fail(4);
        last_=c.inst_count;return true;
    }
    template<class C>bool disable_before(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack,PostAckTransferDevice& device){
        if(stage_!=2||device.stage()||!common(c,ack,device)||disable_.stage()!=2||c.inst_count-last_!=1u||!ack.auxiliary_before()||!disable_.before(c,pc,w))return fail(4);
        last_=c.inst_count;return true;
    }
    bool handoff_due()const{return stage_==2&&disable_.stage()==3;}
    template<class C>bool irq_before(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack,PostAckTransferDevice& device){
        if(stage_!=2||!device.stage()||!common(c,ack,device)||irq_lane_>=2||
           irq_[irq_lane_].stage()!=2||c.inst_count-last_!=1u||!device.before(c.inst_count)||!irq_[irq_lane_].before(c,pc,w))return fail(4);
        last_=c.inst_count;return true;
    }
    template<class C>bool restore_before(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack,PostAckTransferDevice& device){
        if(stage_!=2||!device.stage()||!common(c,ack,device)||restore_.stage()!=2||
           c.inst_count-last_!=1u||!device.before(c.inst_count)||!restore_.before(c,pc,w))return fail(4);
        last_=c.inst_count;return true;
    }
    template<class C>bool returned(C& c,uint32_t pc,uint32_t w,SiCompletionAckTrace& ack,PostAckTransferDevice& device){
        if(stage_!=3||!common(c,ack,device)||!abi(c)||pc!=e_.site+4u||c.pc!=pc||c.lr!=pc||
           !mapped(c,pc,4)||c.mmu.read32(pc)!=w||c.inst_count-last_!=1u||!device.before(c.inst_count)||
           !mapped(c,e_.data,20))return fail(8);
        if(idle_){
            if(c.mmu.read32(e_.data)!=channel_||c.mmu.read32(e_.data+8)!=gp_[7]||
               c.mmu.read32(e_.data+12)!=gp_[6]||c.mmu.read32(e_.data+16)!=gp_[8])return fail(8);
        }else for(unsigned i=0;i<5;++i)if(c.mmu.read32(e_.data+4*i)!=initial_data_[i])return fail(8);
        if(!device.finish(c.inst_count,c.gpr[3]))return fail(8);
        total_=unsigned(c.inst_count-tick_-1u);stage_=4;return true;
    }
    template<class C>bool poll(C& c,SiCompletionAckTrace& ack,PostAckTransferDevice& device){
        if(stage_!=2||!common(c,ack,device)||!pending_||c.inst_count!=last_||c.pc!=poll_pc_||
           c.gpr!=poll_gp_||pack(c)!=poll_cr_||c.lr!=poll_lr_||c.ctr!=poll_ctr_||c.xer!=poll_xer_||
           !(device.stage()?device.held(c.inst_count):ack.auxiliary_poll()))return fail(7);
        pending_=false;return true;
    }
private:
    TransferReturnExpectation e_;SiFirstHelper save_;PostAckOsLeaf disable_;
    std::array<PostAckOsLeaf,2> irq_;GprRestoreWitness restore_;
    const void* cpu_=nullptr;unsigned stage_=0,error_=0,visits_=0,channel_=0,total_=0,irq_lane_=2;
    uint32_t msr_=0,srr0_=0,srr1_=0,next_=0,poll_pc_=0,poll_cr_=0,poll_lr_=0,poll_ctr_=0,poll_xer_=0,cr_=0;
    uint64_t tick_=0,last_=0;bool type_=false,idle_=false,pending_=false;
    std::array<uint32_t,32> gp_{},poll_gp_{};
    std::array<uint32_t,5> initial_data_{};
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class C>static bool safe(C& c){return c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&!(c.msr&0x8000u);}
    template<class C>bool common(C& c,SiCompletionAckTrace& ack,PostAckTransferDevice& device)const{return !error_&&cpu_==&c&&safe(c)&&c.msr==msr_&&c.srr0==srr0_&&c.srr1==srr1_&&c.inst_count>=tick_&&c.inst_count-tick_<=2048u&&(device.stage()==1||(!device.stage()&&ack.postack_held()));}
    template<class C>bool abi(C& c)const{
        if(c.gpr[1]!=gp_[1]||c.gpr[2]!=gp_[2]||c.gpr[13]!=gp_[13]||(pack(c)&0x00fff000u)!=cr_)return false;
        for(unsigned i=14;i<32;++i)if(c.gpr[i]!=gp_[i])return false;
        return true;
    }
    template<class C>static bool mapped(C& c,uint32_t a,unsigned n){return n&&a>=0x80000000u&&uint64_t(a)+n<=0x81800000u&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+n-1u);}
    static uint32_t target(uint32_t pc,uint32_t w){const uint32_t bits=w>>26==16u?0xfffcu:0x03fffffcu,sign=w>>26==16u?0x8000u:0x02000000u;return pc+(((w&bits)^sign)-sign);}
    template<class C>static uint32_t pack(C& c){uint32_t v=0;for(const auto& f:c.cr)v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|(unsigned(f.eq)<<1)|unsigned(f.so);return v;}
    template<class C>static bool taken(C& c,uint32_t w){const unsigned bo=(w>>21)&31u,bi=(w>>16)&31u;return ((bo&4u)||(((c.ctr-1u)!=0u)^bool(bo&2u)))&&((bo&16u)||bool((pack(c)>>(31u-bi))&1u)==bool(bo&8u));}
};
}
