#pragma once
#include "wii_second_completion_ack_v950.h"
#include "wii_external_return_v706.h"
#include "v958_private_second_ack.h"
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
#include "wii_third_si_transfer_v1028.h"
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
#include "wii_third_alarm_suffix_v1047.h"
#include "v786_private_alarm.h"
#ifdef UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME
#include "v813_private_callback_time.h"
#ifdef UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER
#include "v831_private_callback_frontier.h"
#ifdef UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS
#include "v847_private_wireless_wrapper.h"
#ifdef UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX
#include "v1123_private_postalarm_suffix.h"
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
#include "v1132_private_postalarm_return.h"
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
#include "v1139_private_postalarm_handler.h"
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
#include "v1145_private_postalarm_handler_return.h"
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
#include "wii_held_pending_epilogue_v1149.h"
#include "v1151_private_held_epilogue.h"
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
#include "v1158_private_held_dispatch.h"
#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK
#include "v1167_private_third_ack.h"
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
#include "wii_si_transfer_arguments_v981.h"
#endif
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
#include "wii_callback_identity_v796.h"
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
#include "wii_callback_prefix_v800.h"
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
#include "v813_private_callback_time.h"
#endif
#endif
#include <cstdlib>
#include <iostream>
namespace undercover::wii::v958 {
inline thread_local SecondCompletionAck ack;
inline thread_local ExternalReturnWitness* frame=nullptr;
#ifdef UNDERCOVER_V1025_PRIVATE_TRANSFER
// Only an independently authenticated third-transfer installer may enable this.
inline thread_local PostAckTransferDevice next_device;
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
inline thread_local ThirdSiTransferRoute third_route;
inline thread_local bool third_ready=false;
inline thread_local unsigned third_admission=0;
inline thread_local uint64_t third_ready_tick=0;
inline thread_local std::array<uint32_t,8> third_packet{};
inline bool third_enabled(){const char* v=std::getenv("UNDERCOVER_V1028_THIRD_TRANSFER");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool third_active(){return third_route.stage()==1u;}
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
inline thread_local ThirdAlarmSuffixRoute third_alarm(v786::expected);
inline bool third_alarm_enabled(){const char* v=std::getenv("UNDERCOVER_V1048_THIRD_ALARM");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool third_alarm_active(){return third_alarm.stage()==1u||third_alarm.stage()==2u;}
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
inline thread_local ThirdAlarmCallbackRoute<third_postalarm_prefix.size(),third_postalarm_save.size(),third_postalarm_words.size()>
    third_postalarm(transfer_callback,third_postalarm_save_root,third_postalarm_prefix,third_postalarm_save,third_postalarm_words,third_postalarm_sites);
inline bool third_postalarm_enabled(){const char* v=std::getenv("UNDERCOVER_V1095_AFTER_ALARM");return v&&v[0]=='1'&&v[1]=='\0';}
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
inline thread_local HeldPendingEpilogueWitness held_epilogue(v1151::epilogue,v1151::vector);
inline bool held_epilogue_enabled(){const char* v=std::getenv("UNDERCOVER_V1151_HELD_EPILOGUE");return v&&v[0]=='1'&&v[1]==0;}
inline bool held_epilogue_active(){return held_epilogue.stage()!=0u;}
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
inline bool held_dispatch_enabled(){const char* v=std::getenv("UNDERCOVER_V1158_HELD_DISPATCH");return v&&v[0]=='1'&&v[1]==0;}
inline bool held_dispatch_active(){return held_epilogue.stage()==6u;}
#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK
inline bool third_ack_enabled(){const char* v=std::getenv("UNDERCOVER_V1167_THIRD_ACK");return v&&v[0]=='1'&&v[1]==0;}
inline bool third_ack_active(){return held_epilogue.stage()==8u||held_epilogue.stage()==9u;}
#endif
#endif
[[noreturn]]inline void reject_held_epilogue(){
    std::cout<<std::dec<<"V1151_HELD_EPILOGUE_FAULT stage="<<held_epilogue.stage()<<" reason="<<held_epilogue.failure()
             <<" epilogue="<<held_epilogue.epilogue_failure()<<" reentry="<<held_epilogue.reentry_failure()<<std::endl;std::_Exit(126);
}
#endif
inline bool third_postalarm_active(){
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
    if(held_epilogue_active())return true;
#endif
    return third_postalarm.stage()==1u||third_postalarm.stage()==2u||third_postalarm.stage()==4u||third_postalarm.stage()==6u||third_postalarm.stage()==8u||third_postalarm.stage()==10u||third_postalarm.stage()==12u||third_postalarm.stage()==14u||third_postalarm.stage()==16u;}
#ifdef UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME
inline bool third_postalarm_time_enabled(){const char* v=std::getenv("UNDERCOVER_V1103_POSTALARM_TIME");return v&&v[0]=='1'&&v[1]=='\0';}
#ifdef UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER
inline bool third_postalarm_frontier_enabled(){const char* v=std::getenv("UNDERCOVER_V1111_POSTALARM_FRONTIER");return v&&v[0]=='1'&&v[1]==0;}
[[noreturn]]inline void reject_postalarm_frontier(){
    std::cout<<std::dec<<"V1111_POSTALARM_FRONTIER_FAULT route="<<third_postalarm.failure()
             <<" witness="<<third_postalarm.frontier_failure()<<" stage="<<third_postalarm.stage()<<std::endl;
    std::_Exit(126);
}
#ifdef UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS
inline bool third_postalarm_wireless_enabled(){const char* v=std::getenv("UNDERCOVER_V1118_POSTALARM_WIRELESS");return v&&v[0]=='1'&&v[1]==0;}
#ifdef UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX
inline bool third_postalarm_suffix_enabled(){const char* v=std::getenv("UNDERCOVER_V1123_POSTALARM_SUFFIX");return v&&v[0]=='1'&&v[1]==0;}
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
inline bool third_postalarm_handler_enabled(){const char* v=std::getenv("UNDERCOVER_V1139_POSTALARM_HANDLER");return v&&v[0]=='1'&&v[1]==0;}
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
inline bool third_postalarm_handler_return_enabled(){const char* v=std::getenv("UNDERCOVER_V1145_POSTALARM_HANDLER_RETURN");return v&&v[0]=='1'&&v[1]==0;}
[[noreturn]]inline void reject_postalarm_handler_return(){
    const auto* w=third_postalarm.handler_return_witness();
    std::cout<<std::dec<<"V1145_POSTALARM_HANDLER_RETURN_FAULT route="<<third_postalarm.failure()
             <<" witness="<<(w?w->failure():0u)<<" native="<<(w?w->native_failure():0u)
             <<" stage="<<third_postalarm.stage()<<std::endl;std::_Exit(126);
}
template<class C>void postalarm_handler_dispatch_resume(C& c,uint32_t pc,uint32_t w){
    if(third_postalarm.stage()==16u&&!third_postalarm.handler_return_dispatch(c,pc,w))reject_postalarm_handler_return();
}
#endif
[[noreturn]]inline void reject_postalarm_handler(){
    const auto* w=third_postalarm.handler_witness();
    std::cout<<std::dec<<"V1139_POSTALARM_HANDLER_FAULT route="<<third_postalarm.failure()
             <<" witness="<<(w?w->failure():0u)<<" stage="<<third_postalarm.stage()<<std::endl;
    std::_Exit(126);
}
#endif
inline bool third_postalarm_return_enabled(){const char* v=std::getenv("UNDERCOVER_V1132_POSTALARM_RETURN");return v&&v[0]=='1'&&v[1]==0;}
[[noreturn]]inline void reject_postalarm_return(){
    std::cout<<std::dec<<"V1132_POSTALARM_RETURN_FAULT route="<<third_postalarm.failure()
             <<" witness="<<third_postalarm.callback_return_failure()<<" stage="<<third_postalarm.stage()<<std::endl;std::_Exit(126);
}
template<class C>void postalarm_dispatch_resume(C& c,uint32_t pc,uint32_t w){
    if(third_postalarm.stage()==12u&&!third_postalarm.callback_return_dispatch(c,pc,w))reject_postalarm_return();
}
#endif
[[noreturn]]inline void reject_postalarm_suffix(){
    std::cout<<std::dec<<"V1123_POSTALARM_SUFFIX_FAULT route="<<third_postalarm.failure()
             <<" witness="<<third_postalarm.callback_suffix_failure()<<" stage="<<third_postalarm.stage()<<std::endl;
    std::_Exit(126);
}
#endif
[[noreturn]]inline void reject_postalarm_wireless(){
    std::cout<<std::dec<<"V1118_POSTALARM_WIRELESS_FAULT route="<<third_postalarm.failure()
             <<" witness="<<third_postalarm.wireless_failure()<<" stage="<<third_postalarm.stage()<<std::endl;
    std::_Exit(126);
}
#endif
template<class C>void finish_postalarm_frontier(C& c,uint32_t pc,uint32_t w){
    (void)c;(void)pc;(void)w;
    if(third_postalarm.stage()!=7u)return;
    const auto& f=*third_postalarm.frontier_witness();
    std::cout<<std::dec<<"V1111_POSTALARM_FRONTIER ordinal="<<f.ordinal()<<" visits="<<f.visits()
             <<" writes="<<f.writes()<<" zero_id="<<f.zero_id()
             <<" token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS
    if(third_postalarm_wireless_enabled()){
        if(!third_postalarm.start_wireless(c,pc,w,v847::expected))reject_postalarm_wireless();
        return;
    }
#endif
    std::_Exit(0);
}
#endif
[[noreturn]]inline void reject_postalarm_time(){
    std::cout<<std::dec<<"V1103_POSTALARM_TIME_FAULT route="<<third_postalarm.failure()
             <<" witness="<<third_postalarm.time_failure()<<" stage="<<third_postalarm.stage()<<std::endl;
    std::_Exit(126);
}
#endif
[[noreturn]]inline void reject_postalarm(){
    std::cout<<std::dec<<"V1095_AFTER_ALARM_FAULT route="<<third_postalarm.failure()
             <<" prefix="<<third_postalarm.prefix_failure()<<" stage="<<third_postalarm.stage()<<std::endl;
    std::_Exit(126);
}
template<class C>void postalarm_before(C& c,uint32_t pc,uint32_t w,bool guard){
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
    if(third_postalarm.stage()==16u){
        if(guard||!third_postalarm.handler_return_before(c,pc,w))reject_postalarm_handler_return();
        if(third_postalarm.stage()==17u){
            std::cout<<std::dec<<"V1145_POSTALARM_HANDLER_RETURN original_restore=1 original_return=1 visits="
                     <<third_postalarm.handler_return_witness()->visits()
                     <<" restored_gprs=15 token=3 held=1 saved_fields=38 dispatcher_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
            if(held_epilogue_enabled()){
                const auto* prior=third_postalarm.handler_return_witness();
                if(!frame||!prior||!held_epilogue.begin_bound(c,pc,w,*prior,*frame,next_device))reject_held_epilogue();
                return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
    if(third_postalarm.stage()==14u){
        if(guard||!third_postalarm.handler_before(c,pc,w))reject_postalarm_handler();
        if(third_postalarm.stage()==15u){
            const auto& t=*third_postalarm.handler_witness();
            std::cout<<std::dec<<"V1139_POSTALARM_HANDLER ordinal=12 branch_taken="<<t.taken()
                     <<" visits="<<t.visits()<<" stores="<<t.stores()
                     <<" status_reads=1 status_writes=1 token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
            if(third_postalarm_handler_return_enabled()){
                if(!third_postalarm.start_handler_return(c,pc,w))reject_postalarm_handler_return();
                return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
    if(third_postalarm.stage()==12u){
        if(guard||!third_postalarm.callback_return_before(c,pc,w))reject_postalarm_return();
        if(third_postalarm.stage()==13u){
            std::cout<<std::dec<<"V1132_POSTALARM_RETURN original_restore=1 original_return=1 visits="
                     <<third_postalarm.callback_return_witness()->visits()
                     <<" token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
            if(third_postalarm_handler_enabled()){
                if(!third_postalarm.start_handler_suffix(c,pc,w,v1139::rows,v1139::index,v1139::rd,v1139::wr))
                    reject_postalarm_handler();
                return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX
    if(third_postalarm.stage()==10u){
        if(guard||!third_postalarm.callback_suffix_before(c,pc,w))reject_postalarm_suffix();
        if(third_postalarm.stage()==11u){
            const auto& t=*third_postalarm.callback_suffix_witness();
            std::cout<<std::dec<<"V1123_POSTALARM_SUFFIX ordinal="<<t.ordinal()<<" target_class="<<t.target_class()
                     <<" visits="<<t.visits()<<" writes="<<t.writes()<<" polls="<<t.polls()
                     <<" token=3 held=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
            if(third_postalarm_return_enabled()){
                if(!third_postalarm.start_callback_return(c,pc,w,v1132::expected))reject_postalarm_return();
                return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS
    if(third_postalarm.stage()==8u){
        if(guard||!third_postalarm.wireless_before(c,pc,w))reject_postalarm_wireless();
        if(third_postalarm.stage()==9u){
            const auto& t=*third_postalarm.wireless_witness();
            std::cout<<std::dec<<"V1118_POSTALARM_WIRELESS_RETURN original_setter=1 original_unlock=1 changed=0 visits="<<t.visits()
                     <<" stores="<<t.writes()<<" token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX
            if(third_postalarm_suffix_enabled()){
                if(!third_postalarm.start_callback_suffix(c,pc,w,v1123::expected)||third_postalarm.stage()!=10u)
                    reject_postalarm_suffix();
                return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER
    if(third_postalarm.stage()==6u){
        if(guard||!third_postalarm.frontier_before(c,pc,w))reject_postalarm_frontier();
        finish_postalarm_frontier(c,pc,w);return;
    }
#endif
#ifdef UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME
    if(third_postalarm.stage()==4u){
        if(guard||!third_postalarm.time_before(c,pc,w))reject_postalarm_time();
        if(third_postalarm.stage()==5u){
            const auto& t=*third_postalarm.time_witness();
            std::cout<<std::dec<<"V1103_POSTALARM_TIME_RETURN original_return=1 leaves="<<t.cursor()
                     <<" system_visits="<<t.time_visits()<<" leaf_visits="<<t.leaf_visits()
                     <<" polls="<<t.polls()<<" reads="<<t.reads()
                     <<" offset=1 token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER
            if(third_postalarm_frontier_enabled()){
                if(!third_postalarm.start_frontier(c,pc,w,v831::expected))reject_postalarm_frontier();
                finish_postalarm_frontier(c,pc,w);return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
    if(guard||!third_postalarm.before(c,pc,w))reject_postalarm();
    if(third_postalarm.stage()==3u){
        std::cout<<std::dec<<"V1095_AFTER_ALARM_PREFIX original_indirect=1 original_prologue=1 save_return=1 suffix_visits="
                 <<third_postalarm.suffix_visits()<<" visits="<<third_postalarm.prefix_visits()<<" writes="<<third_postalarm.writes()
                 <<" token=3 held=1 saved_fields=38 continuation_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME
        if(third_postalarm_time_enabled()){
            if(!third_postalarm.start_time(c,pc,w,v813::expected))reject_postalarm_time();
            return;
        }
#endif
        std::_Exit(0);
    }
}
#endif
#endif
#endif
#endif
inline thread_local BoundedAckCallRoute calls;
inline thread_local unsigned visits=0,post_visits=0,post_returns=0;
#ifdef UNDERCOVER_V975_PRIVATE_TIME
inline thread_local unsigned time_tick=0,time_entries=0,time_returns=0,time_msr=0;
inline thread_local bool post_seen=false;
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
inline thread_local unsigned shared_tick=0,shared_entries=0,shared_returns=0,shared_msr=0;
inline thread_local bool shared_seen=false;
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
inline thread_local unsigned helper_return_visits=0;
inline thread_local bool error_helper_seen=false;
inline bool error_frontier_enabled(){const char* v=std::getenv("UNDERCOVER_V1021_ERROR_FRONTIER");return v&&v[0]=='1'&&v[1]=='\0';}
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
inline thread_local CallbackPrefixWitness<second_callback_prefix.size(),second_callback_save.size()> callback_prefix(transfer_callback,second_callback_save_root,second_callback_prefix,second_callback_save);
inline bool callback_enabled(){const char* v=std::getenv("UNDERCOVER_V1009_SECOND_CALLBACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool prefix_active(){return callback_prefix.stage()>=1u&&callback_prefix.stage()<=5u;}
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
inline thread_local CallbackTimeWitness callback_time(v813::expected);
inline bool callback_time_enabled(){const char* v=std::getenv("UNDERCOVER_V1014_SECOND_CALLBACK_TIME");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool callback_time_active(){return callback_time.stage()>=1u&&callback_time.stage()<=4u;}
#endif
inline bool callback_active(){
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_active())return true;
#endif
    return prefix_active();
}
#endif
inline bool success_frontier_enabled(){const char* v=std::getenv("UNDERCOVER_V995_SUCCESS_FRONTIER");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
inline bool shared_enabled(){const char* v=std::getenv("UNDERCOVER_V989_SHARED_COMPLETION");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool error_completion_enabled(){const char* v=std::getenv("UNDERCOVER_V1015_ERROR_COMPLETION");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
inline thread_local bool time_seen=false;
inline thread_local unsigned time_return_visits=0;
inline thread_local SiQueueHistory queue_history;
inline bool queue_detail_enabled(){const char* v=std::getenv("UNDERCOVER_V1034_QUEUE_DETAIL");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool six_arguments_enabled(){const char* v=std::getenv("UNDERCOVER_V1040_SIX_ARGS");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool frontier_enabled(){const char* v=std::getenv("UNDERCOVER_V981_SECOND_FRONTIER");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
inline bool time_enabled(){const char* v=std::getenv("UNDERCOVER_V975_SECOND_TIME");return v&&v[0]=='1'&&v[1]=='\0';}
#endif
inline bool post_enabled(){const char* v=std::getenv("UNDERCOVER_V967_POST_ACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool enabled(){const char* v=std::getenv("UNDERCOVER_V958_SECOND_ACK");return v&&v[0]=='1'&&v[1]=='\0';}
inline bool active(){return ack.stage()!=0u;}
[[noreturn]]inline void reject(unsigned kind){
    std::cout<<std::dec<<"V958_ACK_INVALID kind="<<kind<<" stage="<<ack.stage()<<" reason="<<ack.failure()
             <<" call_reason="<<calls.failure()<<" visits="<<visits<<std::endl;std::_Exit(126);
}
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
// Distinguish the three fail-closed shared-time checks without exposing
// guest addresses, register values, original words, or raw traces.
[[noreturn]]inline void reject_shared(unsigned phase){
    const bool started=shared_tick!=0u;
    std::cout<<std::dec<<"V989_SHARED_DETAIL phase="<<phase<<" depth="<<calls.depth()
             <<" started="<<started<<" seen="<<shared_seen<<" post="<<post_seen
             <<" held="<<ack.postack_held()<<" entries="<<calls.entries()-(started?shared_entries:0u)
             <<" returns="<<calls.returns()-(started?shared_returns:0u)
             <<" msr="<<calls.msr_writes()-(started?shared_msr:0u)
             <<" visits="<<visits<<std::endl;
    reject(12);
}
#endif
template<class C>bool start(C& c,ExternalReturnWitness& captured){
    if(frame||active()||!captured.saved_integer(c,context).ok())return false;
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
    if(six_arguments_enabled()&&!queue_detail_enabled())return false;
#endif
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
    if(third_enabled()&&!error_frontier_enabled())return false;
#ifndef UNDERCOVER_V1049_PRIVATE_ABI_PROVEN
    if(third_enabled()&&six_arguments_enabled())return false;
#endif
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
    if(third_alarm_enabled()&&(!third_enabled()||!six_arguments_enabled()))return false;
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
    if(third_postalarm_enabled()&&!third_alarm_enabled())return false;
#ifdef UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME
    if(third_postalarm_time_enabled()&&!third_postalarm_enabled())return false;
#ifdef UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER
    if(third_postalarm_frontier_enabled()&&!third_postalarm_time_enabled())return false;
#ifdef UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS
    if(third_postalarm_wireless_enabled()&&!third_postalarm_frontier_enabled())return false;
#ifdef UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX
    if(third_postalarm_suffix_enabled()&&!third_postalarm_wireless_enabled())return false;
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
    if(third_postalarm_return_enabled()&&!third_postalarm_suffix_enabled())return false;
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
    if(third_postalarm_handler_enabled()&&!third_postalarm_return_enabled())return false;
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
    if(third_postalarm_handler_return_enabled()&&!third_postalarm_handler_enabled())return false;
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
    if(held_epilogue_enabled()&&!third_postalarm_handler_return_enabled())return false;
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
    if(held_dispatch_enabled()&&!held_epilogue_enabled())return false;
#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK
    if(third_ack_enabled()&&!held_dispatch_enabled())return false;
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
    if(callback_enabled()&&!success_frontier_enabled())return false;
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_enabled()&&!callback_enabled())return false;
#endif
#endif
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
    if(success_frontier_enabled()&&(!shared_enabled()||!time_enabled()||!frontier_enabled()||!post_enabled()))return false;
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
    if(frontier_enabled()&&(!time_enabled()||!post_enabled()))return false;
#endif
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
    if(error_completion_enabled()&&!shared_enabled())return false;
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
    if(error_frontier_enabled()&&(!error_completion_enabled()||!success_frontier_enabled()||!time_enabled()||!frontier_enabled()))return false;
    if(error_completion_enabled()&&time_enabled()&&!error_frontier_enabled())return false;
#else
    if(error_completion_enabled()&&time_enabled())return false;
#endif
    if(shared_enabled()){
        if(!post_enabled()||!calls.begin(c,time_spans,shared_edges,msr_sites))return false;
    }else
#endif
#ifdef UNDERCOVER_V975_PRIVATE_TIME
    if(time_enabled()){
        if(!post_enabled()||!calls.begin(c,time_spans,time_edges,msr_sites))return false;
    }else
#endif
    if(!calls.begin(c,spans,edges))return false;
    frame=&captured;
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
    if(third_postalarm_handler_return_enabled()&&!third_postalarm.capture_handler_entry(c,spans[0].root,v1145::expected,captured,context))return false;
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
    if(queue_detail_enabled()&&!queue_history.begin(c,transfer_slots))return false;
#endif
    return true;
}
template<class C>void before(C& c,uint32_t pc,uint32_t w,bool guard){
    if(!active())return;
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
    if(held_epilogue_active()){
#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK
        if(third_ack_active()){
            const auto owner=third_ack_native_owner(v1167::labels,pc,w);
            if(!owner||second_dispatch_mmio||!held_epilogue.ack_before(c,owner,pc,w,guard))reject_held_epilogue();
            if(held_epilogue.stage()==9u){
                const auto& a=held_epilogue.completion_ack();const auto& calls3=held_epilogue.ack_calls();
                if(ack.stage()!=5u||next_device.stage()!=3u||!held_epilogue.ack_saved(c))reject_held_epilogue();
                std::cout<<std::dec<<"V1167_THIRD_ACK original_w1c=1 next_label=1 token=3 no_response="<<a.no_response_verified()
                         <<" visits="<<held_epilogue.ack_visits()<<" entries="<<calls3.entries()<<" returns="<<calls3.returns()
                         <<" reads="<<a.reads()<<" writes="<<a.writes()<<" saved_fields=38 retired_transfer=1 pi_cleared=1 successor_executed=0 boot_verified=0"<<std::endl;
                std::_Exit(0);
            }
            return;
        }
#endif
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
        if(held_epilogue.stage()==6u){
            if(second_dispatch_mmio!=held_epilogue.dispatch_witness()||!held_epilogue.dispatch_before(c,pc,w,guard))reject_held_epilogue();
            return;
        }
#endif
        if(guard||!held_epilogue.before(c,pc,w))reject_held_epilogue();
        return;
    }
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
    if(queue_detail_enabled()&&!queue_history.sample(c))reject(18);
#endif
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
    if(third_postalarm_active()){postalarm_before(c,pc,w,guard);return;}
#endif
    if(third_alarm_active()){
        if(guard||!frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
           !third_alarm.before(c,pc,w,next_device)){
            std::cout<<std::dec<<"V1048_THIRD_ALARM_FAULT route="<<third_alarm.failure()<<" alarm="<<third_alarm.alarm().failure()
                     <<" queue="<<third_alarm.alarm().queue_failure()<<" stage="<<third_alarm.stage()<<std::endl;
            reject(19);
        }
        if(third_alarm.stage()==3u){
            const auto& a=third_alarm.alarm();
            std::cout<<std::dec<<"V1048_THIRD_ALARM_RETURN original_return=1 queue=1 token=3 lane="<<a.lane()
                     <<" timer="<<a.timer_required()<<" calls="<<a.calls()<<" visits="<<a.total()
                     <<" suffix_visits="<<third_alarm.suffix_visits()<<" status_reads="<<next_device.suffix_status_reads()
                     <<" status_writes="<<next_device.suffix_status_writes()<<" token_held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
            if(third_postalarm_enabled()){
                if(!third_postalarm.start(c,pc,w,third_alarm,next_device,*frame,context,third_postalarm_suffix))reject_postalarm();
                postalarm_before(c,pc,w,false);return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
    if(third_active()){
        if(guard||!frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
           !third_route.before(c,pc,w,next_device))reject(17);
        if(third_route.stage()==2u){
            std::cout<<std::dec<<"V1028_THIRD_RETURN original_transfer=1 token=3 pending="<<next_device.pending()
                <<" visits="<<third_route.visits()<<" entries="<<third_route.entries()<<" returns="<<third_route.returns()
                <<" reads="<<next_device.reads()<<" writes="<<next_device.writes()
                <<" saved_fields=38 handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
            if(third_alarm_enabled()){
                const bool started=third_alarm.start(c,pc,third_alarm_suffix,next_device);
                const bool first=started&&third_alarm.before(c,pc,w,next_device);
                std::cout<<std::dec<<"V1087_ALARM_HANDOFF started="<<started<<" first="<<first
                         <<" stage="<<third_alarm.stage()<<" reason="<<third_alarm.failure()<<std::endl;
                if(!first)reject(19);
                return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_active()){
        if(guard||!frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
           !ack.before(c,pc,w,true)||!ack.postack_held()||!callback_time.before(c,pc,w,true))reject(15);
        if(callback_time.stage()==5u){
            std::cout<<std::dec<<"V1014_CALLBACK_TIME original_return=1 leaves="<<callback_time.cursor()
                     <<" system_visits="<<callback_time.time_visits()<<" leaf_visits="<<callback_time.leaf_visits()
                     <<" polls="<<callback_time.polls()<<" reads="<<callback_time.reads()
                     <<" offset=1 token_preserved=1 saved_fields=38 continuation_executed=0 boot_verified=0"<<std::endl;
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
    if(prefix_active()){
        if(guard||!frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
           !ack.before(c,pc,w,true)||!ack.postack_held()||!callback_prefix.before(c,pc,w,true))reject(14);
        if(callback_prefix.stage()==6u){
            std::cout<<std::dec<<"V1009_CALLBACK_PREFIX original_indirect=1 original_prologue=1 save_return=1 writes="<<callback_prefix.writes()
                     <<" visits="<<callback_prefix.visits()<<" token_preserved=1 saved_fields=38 continuation_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
            if(callback_time_enabled()){
                // Prefix already consumed this native label and SI tick.
                if(!callback_time.start(c,pc,w,ack.postack_held(),true)||
                   !callback_time.before(c,pc,w,ack.postack_held()))reject(15);
                return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
    if(success_frontier_enabled()&&pc==success_callback_sites[0]){
        if(!guard||(!shared_seen&&!error_helper_seen)||!post_seen||!helper_return_visits||time_seen||w!=0x4e800421u||
           !frame||!frame->saved_integer(c,context).ok()||++visits>8192u||
           !ack.before(c,pc,w,true)||!ack.postack_held()||!calls.stop_before_indirect(c,pc,w))reject(13);
        if(error_frontier_enabled()){
            if(!error_helper_seen||!ack.no_response_verified()||shared_seen||shared_tick||
               visits-helper_return_visits!=71u)reject(16);
            std::cout<<"V1021_ERROR_FRONTIER branch=6 visits=71 handler_time=0 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
        }
        const auto category=classify_callback_identity(c,pc,w,6u,2u,transfer_callback,success_callback_words,success_callback_sites);
        std::cout<<std::dec<<"V995_CALLBACK_FRONTIER target_class="<<category<<" aligned="<<(!(c.ctr&3u))
                 <<" visits="<<visits-helper_return_visits<<" token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
        if(callback_enabled()&&category==2u&&c.ctr==transfer_callback){
            if(c.gpr[3]>=4u||!callback_prefix.start_dispatch(c,pc,w,true,true))reject(14);
            return;
        }
#endif
        std::_Exit(0);
    }
#endif
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
    if(frontier_enabled()&&time_seen&&pc==transfer_call){
        if(!guard||w!=transfer_branch||!frame||!frame->saved_integer(c,context).ok()||
           ++visits>8192u||!ack.before(c,pc,w,true)||!ack.postack_held()||!calls.stop_before_direct(c,pc,w))reject(11);
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
        if(error_frontier_enabled()){
            if(!error_helper_seen||!ack.no_response_verified()||shared_seen||shared_tick||
               visits-helper_return_visits!=78u)reject(16);
            std::cout<<"V1021_ERROR_FRONTIER branch=4 visits=78 handler_time=1 token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
        }
#endif
        const auto a=inspect_si_transfer_arguments(c,transfer_data,transfer_slots,transfer_callback);
        SiQueueHistoryResult hist;
        if(queue_detail_enabled()){
            hist=queue_history.finish(c,a);
            if(!hist.valid)reject(18);
            std::cout<<std::dec<<"V1034_QUEUE_DETAIL mismatch_mask="<<a.mismatch_mask<<" slot_kind="<<a.slot_kind
                <<" arg_time_zero="<<a.argument_time_zero<<" queue_time_zero="<<a.queued_time_zero<<std::endl;
            std::cout<<"V1037_QUEUE_HISTORY initial_mismatch="<<hist.initial_mismatch<<" current_mismatch="<<hist.current_mismatch
                <<" changed="<<hist.changed<<" initial_slot_kind="<<hist.initial_slot_kind<<" samples="<<hist.samples<<std::endl;
        }
        std::cout<<std::dec<<"V981_TRANSFER_FRONTIER type="<<a.type<<" idle="<<a.idle<<" queue_match="<<a.queue_match
            <<" callback_known="<<a.callback_known<<" admitted="<<a.admitted()<<" visits="<<visits-time_return_visits
            <<" token_preserved=1 saved_fields=38 call_executed=0 boot_verified=0"<<std::endl;
        if(six_arguments_enabled()){
            const auto admission=si_transfer_admission(a,&hist);
            std::cout<<"V1040_TRANSFER_ABI admission="<<admission<<" timing_only="<<bool(admission==2u)
                <<" unchanged_slot="<<bool(hist.valid&&!hist.changed&&hist.initial_slot_kind==1u)
                <<" call_executed=0 boot_verified=0"<<std::endl;
        }
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
        if(third_enabled()){
            const auto decision=si_transfer_admission(a,six_arguments_enabled()?&hist:nullptr);
            if(decision){third_ready=true;third_admission=decision;third_ready_tick=c.inst_count;third_packet=a.packet;return;}
        }
#endif
        std::_Exit(0);
    }
#endif
    if(guard||!frame||!frame->saved_integer(c,context).ok()){
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
        if(shared_enabled())std::cout<<std::dec<<"V989_SHARED_REFUSAL guard="<<guard<<" frame="<<bool(frame&&frame->saved_integer(c,context).ok())<<" depth="<<calls.depth()<<" visits="<<visits<<std::endl;
#endif
        reject(1);
    }
    if(++visits>8192u||
       !ack.before(c,pc,w,true)||!calls.before(c,pc,w))reject(1);
    if(ack.stage()==3u){
        if(ack.token()<2u||!ack.reads()||!ack.writes()||calls.entries()<2u||!calls.returns())reject(2);
        std::cout<<std::dec<<"V958_ACK_RESULT original_w1c=1 next_label=1 saved_fields=38 token_preserved=1 visits="
                 <<visits<<" reads="<<ack.reads()<<" writes="<<ack.writes()<<" boot_verified=0"<<std::endl;
        if(!post_enabled())std::_Exit(0);
        post_visits=visits;post_returns=calls.returns();
        if(!ack.resume_after_ack(c,pc,w))reject(9);
        return;
    }
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
    if(shared_enabled()&&pc==completion_time_call){
        if(shared_tick||post_seen||ack.stage()!=4u||calls.depth()!=2u||!ack.postack_held())reject_shared(1);
        shared_tick=visits;shared_entries=calls.entries();shared_returns=calls.returns();shared_msr=calls.msr_writes();
    }
    if(shared_enabled()&&shared_tick&&pc==completion_time_call+4u){
        if(shared_seen||calls.depth()!=1u||calls.entries()-shared_entries!=4u||calls.returns()-shared_returns!=4u||
           calls.msr_writes()-shared_msr!=2u||!ack.postack_held()||visits<=shared_tick)reject_shared(2);
        shared_seen=true;
        std::cout<<std::dec<<"V989_SHARED_TIME_RESULT original_time=1 leaves=3 unchanged_msr=2 visits="<<visits-shared_tick
                 <<" token_preserved=1 saved_fields=38 boot_verified=0"<<std::endl;
    }
#endif
#ifdef UNDERCOVER_V975_PRIVATE_TIME
    if(time_enabled()&&post_seen&&pc==time_call){
        if(time_tick||calls.depth()!=1u||!ack.postack_held())reject(10);
        time_tick=visits;time_entries=calls.entries();time_returns=calls.returns();time_msr=calls.msr_writes();
    }
    if(time_enabled()&&time_tick&&pc==time_call+4u){
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
        if(time_seen)reject(11);
#endif
        if(calls.depth()!=0u||calls.entries()-time_entries!=4u||calls.returns()-time_returns!=4u||
           calls.msr_writes()-time_msr!=2u||!ack.postack_held()||visits<=time_tick)reject(10);
        std::cout<<std::dec<<"V975_TIME_RESULT original_time=1 original_leaves=3 unchanged_msr=2 saved_fields=38 token_preserved=1 visits="
                 <<visits-time_tick<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V981_PRIVATE_FRONTIER
        if(frontier_enabled()){time_seen=true;time_return_visits=visits;return;}
#endif
        std::_Exit(0);
    }
    if(post_seen)return;
#endif
    if(ack.stage()==4u&&pc>=spans[0].root&&pc<spans[0].end&&calls.depth()==0u){
        if(!post_visits||visits<=post_visits||calls.returns()<=post_returns||!ack.postack_held())reject(9);
#ifdef UNDERCOVER_V989_PRIVATE_SHARED
        if(shared_enabled()&&!shared_seen){
            // V1013: 32 original no-response returns, never a waiver
            // of the successful-response timing-call requirement.
            if(!error_completion_enabled()||!ack.no_response_verified()||
               shared_tick||calls.entries()!=6u||calls.returns()!=6u||
               calls.msr_writes()!=2u||visits-post_visits!=130u)reject_shared(3);
            std::cout<<std::dec<<"V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits="
                     <<visits-post_visits<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
            std::cout<<"V1015_ERROR_HELPER_RETURN original_helper_return=1 no_response=1 shared_time=0 entries=6 returns=6 msr=2 visits=130 token_preserved=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
            if(error_frontier_enabled()){
                error_helper_seen=true;helper_return_visits=visits;post_seen=true;return;
            }
#endif
            std::_Exit(0);
        }
        if(error_completion_enabled()&&ack.no_response_verified())reject_shared(3);
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
        if(error_frontier_enabled())reject(16);
#endif
#endif
        std::cout<<std::dec<<"V967_POST_ACK_RESULT original_helper_return=1 saved_fields=38 token_preserved=1 visits="
                 <<visits-post_visits<<" handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V975_PRIVATE_TIME
        if(time_enabled()){
#ifdef UNDERCOVER_V995_PRIVATE_SUCCESS_FRONTIER
            if(success_frontier_enabled())helper_return_visits=visits;
#endif
            post_seen=true;return;
        }
#endif
        std::_Exit(0);
    }
}
template<class C>bool poll(C& c){
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
    if(held_epilogue_active()){
        using Poll=HeldPendingEpilogueWitness::PollResult;
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
        if(held_epilogue.stage()==6u&&second_dispatch_mmio!=held_epilogue.dispatch_witness())reject_held_epilogue();
#endif
#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK
        if(third_ack_active()&&second_dispatch_mmio)reject_held_epilogue();
#endif
        const auto p=held_epilogue.poll(c,v1151::image);
        if(p==Poll::Rejected)reject_held_epilogue();
        if(p==Poll::Entered){
            std::cout<<std::dec<<"V1151_HELD_PENDING_RFI native_rfi=1 pending_exception=1 visits="<<held_epilogue.visits()
                     <<" token=3 held=1 resumed_instruction_executed=0 boot_verified=0"<<std::endl;
            return true;
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
    if(third_postalarm.stage()==16u){if(!third_postalarm.handler_return_poll(c))reject_postalarm_handler_return();return false;}
#endif
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
    if(third_postalarm.stage()==14u)reject_postalarm_handler();
#endif
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
    if(third_postalarm.stage()==12u){if(!third_postalarm.callback_return_poll(c))reject_postalarm_return();return false;}
#endif
#ifdef UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX
    if(third_postalarm.stage()==10u){if(!third_postalarm.callback_suffix_poll(c))reject_postalarm_suffix();return false;}
#endif
#ifdef UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS
    if(third_postalarm.stage()==8u)reject_postalarm_wireless();
#endif
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
#ifdef UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME
    if(third_postalarm.stage()==4u){if(!third_postalarm.time_poll(c))reject_postalarm_time();return false;}
#ifdef UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER
    if(third_postalarm.stage()==6u)reject_postalarm_frontier();
#endif
#endif
    if(third_postalarm_active()){if(!third_postalarm.poll(c))reject_postalarm();return false;}
#endif
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
    if(third_alarm_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!third_alarm.poll(c,next_device)){
            std::cout<<std::dec<<"V1087_ALARM_SEAM kind=1 stage="<<third_alarm.stage()<<" reason="<<third_alarm.failure()<<std::endl;
            reject(19);
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
    if(third_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!third_route.poll(c,next_device))reject(17);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!ack.postack_held()||!callback_time.poll(c,true))reject(15);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
    if(prefix_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!ack.postack_held()||!callback_prefix.dispatch_poll(c,true))reject(14);
        return false;
    }
#endif
    if(!frame||!frame->saved_integer(c,context).ok()||!calls.can_poll()||!ack.poll(c.inst_count))reject(3);
    return false;
}
template<class C>void observe(uint32_t pc,C& c){
#ifdef UNDERCOVER_V1151_PRIVATE_HELD_EPILOGUE
    if(held_epilogue_active()){
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
        if(held_epilogue.stage()==6u&&second_dispatch_mmio!=held_epilogue.dispatch_witness())reject_held_epilogue();
#endif
#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK
        if(third_ack_active()&&second_dispatch_mmio)reject_held_epilogue();
#endif
        if(!held_epilogue.entry(c,pc))reject_held_epilogue();
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
        if(held_epilogue.stage()==7u){
            if(!held_epilogue.dispatch_saved(c))reject_held_epilogue();
            second_dispatch_mmio=nullptr;
            std::cout<<std::dec<<"V1158_HELD_DISPATCH original_dispatcher=1 original_leaves=4 original_indirect=1 visits="
                     <<held_epilogue.dispatch_visits()<<" entries="<<held_epilogue.dispatch_entries()
                     <<" pi_reads="<<held_epilogue.dispatch_reads()<<" polls="<<held_epilogue.dispatch_polls()
                     <<" token=3 held=1 saved_fields=38 handler_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1167_PRIVATE_THIRD_ACK
            if(third_ack_enabled()){
                if(ack.stage()!=5u||!held_epilogue.begin_ack(c,v1167::spans,v1167::edges,v1167::msr))reject_held_epilogue();
                return;
            }
#endif
            std::_Exit(0);
        }
#endif
        if(held_epilogue.stage()==5u){
            if(!held_epilogue.saved(c))reject_held_epilogue();
            std::cout<<std::dec<<"V1151_HELD_VECTOR_JOIN original_vector=1 original_trampoline=1 saved_fields=38 vector_visits="
                     <<held_epilogue.vector_visits()<<" trampoline_visits="<<held_epilogue.trampoline_visits()
                     <<" token=3 held=1 dispatcher_instruction_executed=0 boot_verified=0"<<std::endl;
#ifdef UNDERCOVER_V1158_PRIVATE_HELD_DISPATCH
            if(held_dispatch_enabled()){
                if(second_dispatch_mmio||!held_epilogue.begin_dispatch(c,v1158::expected))reject_held_epilogue();
                second_dispatch_mmio=held_epilogue.dispatch_witness();return;
            }
#endif
            std::_Exit(0);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1145_PRIVATE_POSTALARM_HANDLER_RETURN
    if(third_postalarm.stage()==16u){if(!third_postalarm.handler_return_entry(c,pc))reject_postalarm_handler_return();return;}
#endif
#ifdef UNDERCOVER_V1139_PRIVATE_POSTALARM_HANDLER
    if(third_postalarm.stage()==14u)reject_postalarm_handler();
#endif
#ifdef UNDERCOVER_V1132_PRIVATE_POSTALARM_RETURN
    if(third_postalarm.stage()==12u){if(!third_postalarm.callback_return_entry(c,pc))reject_postalarm_return();return;}
#endif
#ifdef UNDERCOVER_V1123_PRIVATE_POSTALARM_SUFFIX
    if(third_postalarm.stage()==10u)reject_postalarm_suffix();
#endif
#ifdef UNDERCOVER_V1118_PRIVATE_POSTALARM_WIRELESS
    if(third_postalarm.stage()==8u){if(!third_postalarm.wireless_entry(c,pc))reject_postalarm_wireless();return;}
#endif
#ifdef UNDERCOVER_V1095_PRIVATE_AFTER_ALARM
#ifdef UNDERCOVER_V1103_PRIVATE_POSTALARM_TIME
    if(third_postalarm.stage()==4u){if(!third_postalarm.time_entry(c,pc))reject_postalarm_time();return;}
#ifdef UNDERCOVER_V1111_PRIVATE_POSTALARM_FRONTIER
    if(third_postalarm.stage()==6u)reject_postalarm_frontier();
#endif
#endif
    if(third_postalarm_active()){if(!third_postalarm.entry(c,pc))reject_postalarm();return;}
#endif
#ifdef UNDERCOVER_V1048_PRIVATE_THIRD_ALARM
    if(third_alarm_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!third_alarm.entry(c,pc,next_device)){
            std::cout<<std::dec<<"V1087_ALARM_SEAM kind=2 stage="<<third_alarm.stage()<<" reason="<<third_alarm.failure()<<std::endl;
            reject(19);
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1028_PRIVATE_THIRD_ROUTE
    if(third_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!third_route.entry(c,pc,next_device))reject(17);
        return;
    }
#endif
#ifdef UNDERCOVER_V1014_PRIVATE_CALLBACK_TIME
    if(callback_time_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||!ack.postack_held()||!callback_time.entry(c,pc,true))reject(15);
        return;
    }
#endif
#ifdef UNDERCOVER_V1009_PRIVATE_CALLBACK
    if(prefix_active()){
        if(!frame||!frame->saved_integer(c,context).ok()||(callback_prefix.stage()==1u&&!ack.accept_dispatch_tick(c))||
           !ack.postack_held()||!callback_prefix.entry(c,pc,true))reject(14);
        return;
    }
#endif
    if(!frame||!frame->saved_integer(c,context).ok()||!calls.entry(c,pc)||!ack.poll(c.inst_count))reject(4);
}
}
