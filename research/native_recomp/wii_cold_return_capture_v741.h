#pragma once
#include "wii_external_return_v706.h"
namespace undercover::wii {
// This observer never performs IRQ entry, restores registers or enables a switch.
class ColdReturnCapture{
public:
    template<class C>bool operator()(C& c,uint32_t cause,uint32_t mask){
        return witness_.capture(c,cause,mask);
    }
    ExternalReturnWitness& witness(){return witness_;}
    const ExternalReturnWitness& witness()const{return witness_;}
private:
    ExternalReturnWitness witness_;
};
}
