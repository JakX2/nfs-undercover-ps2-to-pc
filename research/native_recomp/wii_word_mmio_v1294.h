#pragma once
#include <cstdint>
namespace undercover::wii {
// Capture the architectural address and store value BEFORE the native
// instruction executes. NWii MMU forwards physical addresses to MMIO;
// never let the callback choose a different register or repeat a store.
struct WordMmioInstruction {
    enum class Kind:unsigned{None,Read,Write};
    Kind kind=Kind::None;unsigned form=0;uint32_t ea=0,value=0;
    bool address(uint32_t a)const{
        return kind!=Kind::None&&!(ea&3u)&&!(a&3u)&&
            (ea&0xc0000000u)!=0x40000000u&&(a&0xc0000000u)!=0x40000000u&&
            (ea&0x3fffffffu)==(a&0x3fffffffu);
    }
    static constexpr uint32_t swap(uint32_t v){
        return (v>>24)|((v>>8)&0xff00u)|((v<<8)&0xff0000u)|(v<<24);
    }
    template<class C>static WordMmioInstruction decode(const C& c,uint32_t w){
        const unsigned op=w>>26,xo=(w>>1)&1023u,rs=(w>>21)&31u,ra=(w>>16)&31u,rb=(w>>11)&31u;
        WordMmioInstruction q;bool update=false,reverse=false,index=false;
        if(op==32u||op==33u||op==36u||op==37u){
            q.kind=op<36u?Kind::Read:Kind::Write;update=op==33u||op==37u;q.form=update?3u:1u;
        }else if(op==31u&&!(w&1u)&&(xo==23u||xo==55u||xo==151u||xo==183u||xo==534u||xo==662u)){
            q.kind=xo==23u||xo==55u||xo==534u?Kind::Read:Kind::Write;
            update=xo==55u||xo==183u;reverse=xo==534u||xo==662u;index=true;
            q.form=reverse?4u:update?3u:2u;
        }else return q;
        if(update&&(!ra||(q.kind==Kind::Read&&ra==rs)))return {};
        const uint32_t base=ra?c.gpr[ra]:0u;
        const uint32_t d=(w&0xffffu);q.ea=base+(index?c.gpr[rb]:((d^0x8000u)-0x8000u));
        if(q.kind==Kind::Write)q.value=reverse?swap(c.gpr[rs]):c.gpr[rs];
        return q;
    }
};
}
