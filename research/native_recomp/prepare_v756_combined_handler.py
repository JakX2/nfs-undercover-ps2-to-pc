"""Compose two individually authenticated handler bindings; synthetic integration only."""
from prepare_v419_full_start import replace_exact
from prepare_v738_handler_restore import patch_binding
def combine(s):
    s=patch_binding(s)
    a='#include "wii_si_handler_return_v725.h"'
    s=replace_exact(s,a,a+'\n#include "wii_si_handler_time_binding_v742.h"')
    a='    if(restore.stage()>=1&&restore.stage()<=3){'
    s=replace_exact(s,a,r'''    if(v742::route.active()){
        v742::returned(c,pc);
        if(!witness.helper_returned(c,pc,v742::route.total(),held(),3))reject(3);
        std::cout<<"V742_TIME_RESULT returned=1 abi=1 leaves=3 visits="<<v742::route.visits()<<" total="<<v742::route.total()<<" handler_return=0 boot_verified=0"<<std::endl;
        if(!v742::continue_suffix())std::_Exit(0);
    }
'''+a)
    a='    if(!(allow?witness.before_authenticated(c,pc,w,held(),restore_ordinal):witness.before(c,pc,w,held()))){'
    s=replace_exact(s,a,r'''    const bool time_allow=v742::eligible(pc,w,ordinal,kind);
    if(allow&&time_allow)reject(3);
    const unsigned slot=allow?restore_ordinal:time_allow?3u:0u;
    if(!(slot?witness.before_authenticated(c,pc,w,held(),slot):witness.before(c,pc,w,held()))){''')
    a='        reject(3);\n    }\n'
    s=replace_exact(s,a,r'''        if(v742::continue_suffix()&&v742::route.stage()==4&&witness.failure()==4&&
           ordinal>=4&&ordinal<=12&&kind>=1&&kind<=2){
            std::cout<<"V747_NEXT_BOUNDARY ordinal="<<ordinal<<" kind="<<kind<<" visits="<<witness.visits()<<" polls="<<witness.polls()<<" executed=0"<<std::endl;
        }
        reject(3);
    }
''')
    a='    if(allow){if(!restore.start'
    return replace_exact(s,a,'    if(time_allow){v742::start(c,pc,w);return;}\n'+a)
