#include "wii_boot_sc_binding_v574.h"
namespace nwii::runtime {
unsigned v578_delegated=0;
const void* v578_route_identity(){return &undercover::wii::v574::route;}
// Same entry seam as the generated production IOS implementation.
// The sentinel stands in for its existing unrelated syscall body.
bool handle_syscall(CPUContext& c){
    if(undercover::wii::v574::try_sc(c))return false;
    ++v578_delegated;return false;
}
}
