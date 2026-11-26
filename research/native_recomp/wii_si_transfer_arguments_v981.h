#pragma once
#include <array>
#include <cstdint>
namespace undercover::wii {
// Read-only admission of a queued SI type request at a native call boundary.
// Never fixes invalid packet fields or changes CPU/device state.
struct SiTransferArguments {
    unsigned channel=4;bool type=false,idle=false,queue_match=false,callback_known=false;
    std::array<uint32_t,8> packet{};
    unsigned mismatch_mask=255u,slot_kind=0u;bool argument_time_zero=false,queued_time_zero=false;
    bool admitted()const{return type&&idle&&queue_match&&callback_known;}
};
// Read-only, per-handler queue lifetime census. Captures every slot before
// the original handler enters, then observes changes on authenticated labels.
// No guest address or value is emitted by the public summary.
struct SiQueueHistoryResult{
    unsigned initial_mismatch=255u,current_mismatch=255u,changed=0u,initial_slot_kind=0u,samples=0u;
    bool valid=false;
};
// V1036 original differential: the lower-level transfer consumes the
// six device arguments independently of the two high-level timing words.
// Keep the exact legacy rule. The optional ABI-specific rule accepts
// only a tail mismatch with an unchanged, originally occupied slot.
inline unsigned si_transfer_admission(const SiTransferArguments& a,const SiQueueHistoryResult* h=nullptr){
    if(a.admitted())return 1u;
    if(!a.type||!a.idle||!a.callback_known||a.channel>=4u||a.slot_kind!=1u||
       !a.mismatch_mask||a.mismatch_mask>255u||(a.mismatch_mask&63u)||
       !h||!h->valid||!h->samples||h->samples>8192u||h->initial_slot_kind!=1u||
       h->changed||h->initial_mismatch!=a.mismatch_mask||h->current_mismatch!=a.mismatch_mask)return 0u;
    return 2u;
}
class SiQueueHistory{
public:
    template<class C>bool begin(C& c,uint32_t slots){
        if(cpu_||slots&3u||slots<0x80000000u||uint64_t(slots)+128u>0x81800000u)return false;
        for(unsigned i=0;i<128u;++i)if(!c.mmu.get_ptr(slots+i))return false;
        cpu_=&c;base_=slots;first_=last_=c.inst_count;
        for(unsigned i=0;i<32u;++i)initial_[i]=latest_[i]=c.mmu.read32(base_+4u*i);
        return true;
    }
    template<class C>bool sample(C& c){
        if(cpu_!=&c||c.inst_count<last_||c.inst_count-first_>8192u)return false;
        // A shared frontier/handoff tick is counted once but must still
        // re-read memory: the same mismatch mask can hide a changed word.
        const bool repeated=samples_&&last_==c.inst_count;
        if(!repeated&&samples_>=8192u)return false;
        for(unsigned i=0;i<128u;++i)if(!c.mmu.get_ptr(base_+i))return false;
        for(unsigned i=0;i<32u;++i){
            const auto v=c.mmu.read32(base_+4u*i);
            if(v!=latest_[i])changed_[i/8u]|=1u<<(i%8u);
            latest_[i]=v;
        }
        last_=c.inst_count;if(!repeated)++samples_;return true;
    }
    template<class C>SiQueueHistoryResult finish(C& c,const SiTransferArguments& a){
        SiQueueHistoryResult out;
        if(a.channel>=4u||!sample(c)||!samples_)return out;
        const unsigned at=8u*a.channel;out.initial_mismatch=out.current_mismatch=0u;
        for(unsigned i=0;i<8u;++i){
            if(initial_[at+i]!=a.packet[i])out.initial_mismatch|=1u<<i;
            if(latest_[at+i]!=a.packet[i])out.current_mismatch|=1u<<i;
        }
        out.changed=changed_[a.channel];
        out.initial_slot_kind=initial_[at]==a.channel?1u:initial_[at]==0xffffffffu?2u:0u;
        out.samples=samples_;out.valid=out.current_mismatch==a.mismatch_mask;return out;
    }
private:
    const void* cpu_=nullptr;uint32_t base_=0;uint64_t first_=0,last_=0;unsigned samples_=0;
    std::array<uint32_t,32> initial_{},latest_{};
    std::array<unsigned,4> changed_{};
};
template<class C>SiTransferArguments inspect_si_transfer_arguments(C& c,uint32_t data,uint32_t slots,uint32_t callback){
    SiTransferArguments a;
    auto mapped=[&](uint32_t p,unsigned n){
        if(!n||p<0x80000000u||uint64_t(p)+n>0x81800000ull)return false;
        for(unsigned i=0;i<n;++i)if(!c.mmu.get_ptr(p+i))return false;
        return true;
    };
    if(c.gpr[3]>3u||data&3u||slots&3u||!mapped(data,20)||!mapped(slots,128))return a;
    a.channel=c.gpr[3];a.idle=c.mmu.read32(data)==0xffffffffu;
    for(unsigned i=0;i<8;++i)a.packet[i]=c.gpr[3+i];
    a.callback_known=c.gpr[8]==callback&&!(callback&3u)&&mapped(callback,4);
    a.type=c.gpr[5]==1u&&c.gpr[7]==3u&&mapped(c.gpr[4],1)&&mapped(c.gpr[6],3)&&
           !(c.gpr[8]&3u)&&mapped(c.gpr[8],4)&&c.mmu.read8(c.gpr[4])==0u;
    std::array<uint32_t,8> queued{};
    a.mismatch_mask=0;
    for(unsigned i=0;i<8;++i){
        queued[i]=c.mmu.read32(slots+32u*a.channel+4u*i);
        if(queued[i]!=a.packet[i])a.mismatch_mask|=1u<<i;
    }
    a.queue_match=a.mismatch_mask==0u;
    a.slot_kind=queued[0]==a.channel?1u:queued[0]==0xffffffffu?2u:0u;
    a.argument_time_zero=(a.packet[6]|a.packet[7])==0u;
    a.queued_time_zero=(queued[6]|queued[7])==0u;
    return a;
}
}
