#include "runtime/cpu_context.h"
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
#include "wii_formatter_report_byte_transition.h"
#endif
#include "functions.h"
#include "v624_private_ipc_expectations.h"
#include "v626_private_words.h"
#include "wii_post_ack_sleep_join_v1252.h"
#include "v1252_private_sleep.h"
#include "v1256_private_scheduler.h"
#ifdef UNDERCOVER_V1315_COOP_SAVE
#include "v1314_private_save.h"
#endif
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
#include "wii_scheduler_irq_entry_v1259.h"
#include "v1259_private_vector.h"
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
#include "wii_second_vector_v939.h"
#include "v1260_private_vector.h"
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
#include "v1261_private_dispatch.h"
#include "wii_initialized_dol_data_v1264.h"
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
#include "v1266_private_ack.h"
#include "wii_joined_ipc_ack_v1266.h"
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
#include "v1270_private_epilogue.h"
#include "wii_scheduler_reply_irq_v1268.h"
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
#include "wii_joined_ipc_reply_entry_v1273.h"
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
#include "v1281_private_reply.h"
#endif
#ifdef UNDERCOVER_V1289_WAKE_READY
#include "v1289_private_wake.h"
#endif
#ifdef UNDERCOVER_V1292_NESTED_WAKE
#include "v1292_private_nested.h"
#endif
#ifdef UNDERCOVER_V1300_REPLY_RETURN
#include "v1299_private_return.h"
#ifdef UNDERCOVER_V1316_REPLY_HELPER
#include "wii_private_expansion_seed_v1323.h"
#endif
#endif
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
#include "wii_ready_idle_return_v1304.h"
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
#include "v1321_private_selection.h"
#include "wii_idle_route_v1327.h"
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
#include "wii_sleep_resume_v1335.h"
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
#include "wii_sleep_exit_v1339.h"
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
#include "wii_submit_resume_v1342.h"
#include "v1344_private_submit.h"
#ifdef UNDERCOVER_V1356_ALLOCATOR_METADATA
#include "v1356_private_descriptor.h"
#endif
#ifdef UNDERCOVER_V1358_OPEN_RETURN
#include "v1358_private_open_return.h"
#ifdef UNDERCOVER_V1359_SECOND_OPEN
#include "v1359_private_second.h"
#ifdef UNDERCOVER_V1379_SECOND_RETURN
#include "v1379_private_second_return.h"
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
#include "v1383_private_stm_ioctl.h"
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
#include "v1386_private_ioctl_prefix.h"
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
#include "v1387_private_ioctl_allocation.h"
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
#include "v1392_private_ioctl_construction.h"
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
#include "v1398_private_ioctl_flush.h"
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
#include "v1401_private_ioctl_output.h"
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
#include "v1404_private_ioctl_submit_prefix.h"
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
#include "v1410_private_ioctl_queue.h"
#ifdef UNDERCOVER_IPC_PROFILE
#include "private_ipc_profile.h"
#ifdef UNDERCOVER_IPC_DISPATCH
#include "private_ipc_dispatch.h"
#include "wii_stm_deferred_event_gate.h"
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
#include "private_async_submit_return.h"
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
#include "private_async_wrapper_return.h"
#ifdef UNDERCOVER_STM_EVENT_RETURN
#include "private_stm_event_return.h"
#ifdef UNDERCOVER_STM_OUTER_RESTORE
#include "private_stm_outer_restore.h"
#include "wii_deferred_stm_irq_entry.h"
#ifdef UNDERCOVER_STM_DEFERRED_VECTOR
#include "wii_ipc_deferred_ack_memory.h"
#ifdef UNDERCOVER_STM_DEFERRED_ACK
#include "private_deferred_ack_execution.h"
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
#include "wii_deferred_active_return.h"
#ifdef UNDERCOVER_STM_RESUMED_RESTORE
#include "wii_stm_resumed_restore.h"
#ifdef UNDERCOVER_STM_FINAL_RETURN
#include "private_stm_final_return.h"
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
#include "private_post_stm_sc.h"
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
#include "private_post_stm_sc_disable.h"
#ifdef UNDERCOVER_POST_STM_SC_DECISION
#include "private_post_stm_sc_decision.h"
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
#include "private_post_stm_sc_restore.h"
#ifdef UNDERCOVER_POST_STM_SC_VERSION
#include "private_post_stm_sc_version.h"
#ifdef UNDERCOVER_POST_STM_SC_REPORT
#include "private_post_stm_sc_report.h"
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
#include "private_post_stm_sc_report_helper.h"
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
#include "private_post_stm_sc_report_dependency.h"
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
#include "private_post_stm_sc_report_resume.h"
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
#include "private_post_stm_sc_formatter.h"
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER_LEAF
#include "private_post_stm_sc_formatter_leaf.h"
#ifdef UNDERCOVER_FORMATTER_CONTINUATION
#include "private_formatter_continuation.h"
#ifdef UNDERCOVER_FORMATTER_NESTED
#include "private_formatter_nested.h"
#include "wii_initialized_cell_observation.h"
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
#endif
#include "v639_private_open_expectations.h"
#include "v629_private_stm_expectations.h"
#include "v1243_private_stm_data.h"
#include "wii_second_completion_ack_v950.h"
#include <algorithm>
#include <iostream>
#include <string_view>
#include <memory>
#include <source_location>
#include <stdexcept>
using namespace undercover::wii;
using W=IpcClientWitness;using B=NativeIosBinding;using H=HollywoodIrq;using M=IpcMailbox;
namespace nw=nwii::runtime;
static std::atomic<uint32_t> cause{0},mask{0xf0};
static PostAckIpcJoin* witness=nullptr;
static PostAckStmJoin* stm_witness=nullptr;
static PostAckOpenJoin* open_witness=nullptr;
static unsigned stm_entries=0,open_entries=0,open_vectors=0,open_returns=0,open_polls=0;
struct RequestReached{};struct SubmitStop{};struct SleepStop{};
static PostAckSleepJoin* sleep_join=nullptr;
static unsigned sleep_count=0;
struct SchedulerStop{};
static PostAckSchedulerJoin* sched_join=nullptr;
static unsigned scheduler_count=0;
#ifdef UNDERCOVER_V1315_COOP_SAVE
static CooperativeSaveLane* coop_save=nullptr;
static unsigned coop_save_count=0;
#ifdef UNDERCOVER_V1320_SAVE_CONTINUITY
static const CooperativeSaveLane* coop_saved=nullptr;
static unsigned coop_idle_count=0;
#endif
#endif
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
static unsigned irq_count=0;
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
static ExternalReturnWitness irq_capture;
static constexpr SecondVectorExpectation ipc_vector_expected{v1260::trampoline,v1260::dispatcher,
    PostAckSchedulerJoin::Idle,v1260::dispatcher_word,v1260::vector_words,v1260::trampoline_words};
static SecondVectorWitness ipc_vector(ipc_vector_expected);
static bool vector_active=false;
static unsigned vector_count=0;
static uint64_t vector_tick=0;
static ColdIpcSnapshot vector_mail{};
struct VectorStop{};
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
static IpcDispatchWitness* ipc_dispatch=nullptr;
static uint32_t dispatch_queue=0;
static unsigned dispatch_count=0;
struct DispatchStop{};
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
static JoinedIpcAck* joined_ack=nullptr;
static nw::CPUContext* joined_cpu=nullptr;
static unsigned joined_count=0;
struct AckReturned{};
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
static LiveEpilogueWitness* epilogue=nullptr;
static NativeIosTransport* epilogue_host=nullptr;
static ExternalReturnWitness reply_capture;
static ColdIpcSnapshot reply_mail{};
static uint32_t reply_request=0,reply_queue=0;
static uint64_t epilogue_tick=0;
static unsigned rfi_count=0,reply_vector_count=0;
static bool reply_vector=false;
struct ReplyEntered{};
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
static JoinedIpcReplyEntry* reply_entry=nullptr;
static nw::CPUContext* reply_cpu=nullptr;
static bool second_dispatch=false;
static unsigned second_dispatch_count=0,reply_entry_count=0;
struct ReplyProcessorReached{};
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
static ReplyProcessorWitness* reply_body=nullptr;
static nw::CPUContext* body_cpu=nullptr;
static unsigned wake_entry_count=0;
struct WakeEntryReached{};
#endif
#ifdef UNDERCOVER_V1289_WAKE_READY
static WakeReadyWitness* wake_ready=nullptr;
static unsigned ready_count=0;
struct ReadyReached{};
#endif
#ifdef UNDERCOVER_V1292_NESTED_WAKE
static NestedWakeReturnWitness* nested_wake=nullptr;
static unsigned nested_count=0;
struct NestedReturned{};
#endif
#ifdef UNDERCOVER_V1300_REPLY_RETURN
static ReplyReturnWitness* reply_return=nullptr;
static nw::CPUContext* return_cpu=nullptr;
static unsigned return_count=0;
struct ReplyHandlerReturned{};
#endif
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
static ReadyIdleReturnJoin* ready_idle=nullptr;
static LiveEpilogueWitness* idle_epilogue=nullptr;
static uint64_t idle_tick=0;
static unsigned idle_return_count=0;
struct IdleRfiReturned{};
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
static IdleSelectionWitness* selection_witness=nullptr;
static IdleRouteWitness* selection_route=nullptr;
static unsigned selection_count=0;
struct LoaderReached{};
#ifdef UNDERCOVER_V1334_COOP_LOAD
static CooperativeLoadLane* coop_load=nullptr;
static CooperativeSaveLane* load_save=nullptr;
static bool load_active=false;
static unsigned load_count=0;
struct CooperativeReturned{};
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
static SleepResumeWitness* sleep_resume=nullptr;
static bool sleep_active=false;
static unsigned resumed_sleep_count=0;
struct SleepRestoreReached{};
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
static SleepExitWitness* sleep_exit=nullptr;
static bool exit_active=false;
static unsigned sleep_exit_count=0;
struct SleepExited{};
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
static SubmitResumeWitness* submit_resume=nullptr;
static bool submit_resume_active=false;
static unsigned release_count=0;
struct ReleaseReached{};
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
static AllocatorReleaseWitness* allocator_release=nullptr;
static bool allocator_active=false;
static AllocatorRange allocator_heap{};
#ifdef UNDERCOVER_V1356_ALLOCATOR_METADATA
static AllocatorDescriptorWitness* allocator_descriptor=nullptr;
#endif
static uint32_t allocator_request=0;
static unsigned allocator_count=0;
struct AllocatorReturned{};
#ifdef UNDERCOVER_V1358_OPEN_RETURN
static OpenReturnWitness* open_return=nullptr;
static bool open_return_active=false;
static StmIos::Device open_return_device=StmIos::Device::None;
static unsigned open_return_count=0;
struct OpenReturned{};
#ifdef UNDERCOVER_V1359_SECOND_OPEN
static StmSecondWitness* second_open=nullptr;
static bool second_open_active=false;
static unsigned second_open_count=0;
struct SecondOpenReached{};
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
static PostAckOpenJoin* second_request=nullptr;
static bool second_request_active=false;
static unsigned second_request_count=0,second_request_vectors=0,second_request_returns=0,second_request_polls=0;
struct SecondRequestReached{};
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
static PostAckSubmitJoin* second_submit=nullptr;
static nw::CPUContext* second_submit_cpu=nullptr;
static bool second_submit_active=false;
static unsigned second_submit_count=0,second_submit_vectors=0,second_submit_returns=0,second_submit_polls=0;
struct SecondSubmitAcked{};
#ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
static bool second_scheduler_lane=false;
static unsigned second_sleep_count=0,second_scheduler_count=0,second_save_count=0;
#ifdef UNDERCOVER_V1370_SECOND_REPLY
static unsigned second_irq_kind=0,second_ack_irq_count=0,second_ack_vector_count=0,second_ack_dispatch_count=0,second_ack_return_count=0;
static unsigned second_reply_rfi_count=0,second_reply_vector2_count=0,second_reply_dispatch2_count=0,second_reply_entry2_count=0,second_wake_entry_count=0;
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
static unsigned second_ready_count=0,second_nested_count=0,second_return_count=0,second_idle_return_count=0,second_selection_count=0,second_load_count=0,second_resumed_sleep_count=0,second_sleep_exit_count=0;
#ifdef UNDERCOVER_V1378_SECOND_FREE
static SubmitResumeWitness* second_resume_capture=nullptr;
static unsigned second_release_count=0,second_allocator_count=0;
#ifdef UNDERCOVER_V1379_SECOND_RETURN
static OpenReturnWitness* second_open_capture=nullptr;
static unsigned second_open_return_count=0;
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
static StmIoctlEntryWitness* stm_ioctl=nullptr;
static unsigned stm_ioctl_count=0;
struct StmIoctlReached{};
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
static IoctlPrefixWitness* ioctl_prefix=nullptr;
static unsigned ioctl_prefix_count=0;
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
static IoctlAllocationWitness* ioctl_alloc=nullptr;
static unsigned ioctl_alloc_count=0;
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
static IoctlConstructionWitness* ioctl_build=nullptr;
static unsigned ioctl_build_count=0;
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
static std::unique_ptr<IoctlFirstFlushWitness> ioctl_flush;
static unsigned ioctl_flush_count=0;
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
static std::unique_ptr<IoctlFlushTailWitness> ioctl_tail;
static unsigned ioctl_output_count=0,ioctl_submit_count=0,ioctl_input_lines=0,ioctl_output_lines=0;
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
static std::unique_ptr<IoctlSubmitPrefixWitness> ioctl_submit_prefix;
static unsigned ioctl_header_entry_count=0,ioctl_queue_init_count=0,ioctl_queue_skip_count=0;
#ifdef UNDERCOVER_V1407_IOCTL_HEADER
static unsigned ioctl_header_return_count=0;
static std::vector<uint8_t> ioctl_header_shadow;
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
static std::unique_ptr<IoctlSubmitQueueWitness> ioctl_submit_queue;
static unsigned ioctl_queue_entry_count=0,ioctl_header_lines=0;
#ifdef UNDERCOVER_IPC_PROFILE
static std::unique_ptr<IpcProfileExecutionWitness> ioctl_profile;
static unsigned ioctl_profile_return_count=0;
#ifdef UNDERCOVER_IPC_DISPATCH
static std::unique_ptr<IpcDispatchExecution> ioctl_dispatch;
static std::unique_ptr<StmDeferredEventGate> ioctl_event_gate;
static nw::CPUContext* ioctl_dispatch_cpu=nullptr;
static unsigned ioctl_dispatch_count=0;
#ifdef UNDERCOVER_IPC_DEFERRED
static unsigned ioctl_deferred_count=0;
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
static std::unique_ptr<AsyncSubmitReturnWitness> async_return;
static unsigned async_return_count=0;
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
static std::unique_ptr<AsyncWrapperReturnWitness> async_wrapper;
static unsigned async_wrapper_count=0;
#ifdef UNDERCOVER_STM_EVENT_RETURN
static std::unique_ptr<StmEventReturnWitness> stm_event_return;
static unsigned stm_event_return_count=0;
#ifdef UNDERCOVER_STM_OUTER_RESTORE
static std::unique_ptr<StmOuterRestoreWitness> stm_outer;
static unsigned stm_outer_count=0,stm_irq_entry_count=0;
#ifdef UNDERCOVER_STM_DEFERRED_VECTOR
static SecondVectorWitness* third_vector=nullptr;
static ExternalReturnWitness* third_frame_ptr=nullptr;
static IpcDeferredAckMemory* third_memory=nullptr;
static uint64_t third_vector_tick=0;
static uint32_t third_context=0,third_wait=0;
static std::array<uint32_t,8> third_thread_tail{};
static unsigned third_vector_count=0;
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
static IpcDispatchWitness* third_dispatch=nullptr;
static unsigned third_dispatch_count=0;
static uint32_t third_request=0;
#ifdef UNDERCOVER_STM_DEFERRED_ACK
static DeferredAckExecution* third_ack=nullptr;
static unsigned third_ack_count=0;
struct DeferredAckStop{};
static bool third_ack_held(nw::CPUContext&);
[[noreturn]]static void third_ack_refuse(unsigned);
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
static LiveEpilogueWitness* third_return_route=nullptr;
static DeferredActiveReturnJoin* third_return_join=nullptr;
static unsigned third_return_count=0;
static uint64_t third_return_tick=0;
struct DeferredActiveRfiStop{};
static bool third_return_storage(nw::CPUContext&);
[[noreturn]]static void third_return_refuse(unsigned);
#ifdef UNDERCOVER_STM_RESUMED_RESTORE
static StmResumedRestoreWitness* third_resume=nullptr;
static unsigned third_resume_count=0;
struct StmResumedRestoreStop{};
static bool third_resume_held(nw::CPUContext&);
[[noreturn]]static void third_resume_refuse(unsigned);
#ifdef UNDERCOVER_STM_FINAL_RETURN
static StmFinalReturnWitness* stm_final=nullptr;
static unsigned stm_final_count=0;
struct StmFinalReturnStop{};
static bool stm_final_held(nw::CPUContext&);
[[noreturn]]static void stm_final_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
static PostStmScEntryWitness* post_stm_sc=nullptr;
static unsigned post_stm_sc_count=0;
struct PostStmScStop{};
static bool post_stm_sc_held(nw::CPUContext&);
[[noreturn]]static void post_stm_sc_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
static PostStmScDisableWitness* post_stm_disable=nullptr;
static PostStmScEntryWitness* post_stm_frame=nullptr;
static unsigned post_stm_disable_count=0;
struct PostStmDisableStop{};
static bool post_stm_disable_held(nw::CPUContext&);
[[noreturn]]static void post_stm_disable_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_DECISION
static ScDecisionWitness* post_stm_decision=nullptr;
static unsigned post_stm_decision_count=0;
struct PostStmDecisionStop{};
static bool post_stm_decision_held(nw::CPUContext&);
[[noreturn]]static void post_stm_decision_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
static ScQuietRestoreWitness* post_stm_restore=nullptr;
static ScDecisionWitness* post_stm_objects=nullptr;
static unsigned post_stm_restore_count=0;
struct PostStmRestoreEnableStop{};
struct PostStmRestoreStop{};
static bool post_stm_restore_held(nw::CPUContext&);
[[noreturn]]static void post_stm_restore_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_VERSION
static ScVersionWitness* post_stm_version=nullptr;
static unsigned post_stm_version_count=0;
static uint32_t post_stm_version_msr=0;
struct PostStmVersionStop{};
static bool post_stm_version_held(nw::CPUContext&);
[[noreturn]]static void post_stm_version_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_REPORT
static ScReportWitness* post_stm_report=nullptr;
static ScVersionWitness* post_stm_version_data=nullptr;
static unsigned post_stm_report_count=0;
struct PostStmReportStop{};
static bool post_stm_report_held(nw::CPUContext&);
[[noreturn]]static void post_stm_report_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
static ScReportHelperWitness* post_stm_helper=nullptr;
static unsigned post_stm_helper_count=0;
struct PostStmHelperStop{};
static bool post_stm_helper_held(nw::CPUContext&);
[[noreturn]]static void post_stm_helper_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
static ScLeafShadow* post_stm_dependency=nullptr;
static unsigned post_stm_dependency_count=0;
struct PostStmDependencyStop{};
static bool post_stm_dependency_held(nw::CPUContext&);
[[noreturn]]static void post_stm_dependency_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
static ScLeafShadow* post_stm_resume=nullptr;
static unsigned post_stm_resume_count=0;
struct PostStmResumeStop{};
static bool post_stm_resume_held(nw::CPUContext&);
[[noreturn]]static void post_stm_resume_refuse(unsigned);
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
static ScFormatterWitness* post_stm_formatter=nullptr;
static unsigned post_stm_formatter_count=0;
struct PostStmFormatterStop{};
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER_LEAF
static ScLeafShadow* post_stm_formatter_leaf=nullptr;
static unsigned post_stm_formatter_leaf_count=0;
struct PostStmFormatterLeafStop{};
#ifdef UNDERCOVER_FORMATTER_CONTINUATION
static RegisterContinuationWitness* formatter_continuation=nullptr;
static unsigned formatter_continuation_count=0;
struct FormatterContinuationStop{};
#ifdef UNDERCOVER_FORMATTER_NESTED
static ScFormatterWitness* formatter_nested=nullptr;
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
static std::optional<FormatterReportByteTransition> formatter_report_byte;
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
static std::optional<CallerImmediateCompareWitness> formatter_report_compare;
#endif
#endif
static unsigned formatter_nested_count=0;
static unsigned nested_cold_match=0,nested_live_match=0,nested_sample_equal=0;
#if defined(UNDERCOVER_FORMATTER_CONTROL)
static_assert(formatter_nested_private::path.size()==76u&&formatter_nested_private::accesses.size()==19u);
static_assert(formatter_nested_private::expected.control.destination&&formatter_nested_private::expected.boundary.width==0u);
static constexpr unsigned nested_visits=76u,nested_loads=6u,nested_stores=13u;
#ifdef UNDERCOVER_FORMATTER_POST_CTR
static_assert(formatter_post_ctr_private::path.size()==84u&&formatter_post_ctr_private::accesses.size()==21u);
static_assert(formatter_post_ctr_private::expected.boundary.stack&&formatter_post_ctr_private::expected.boundary.width==4u);
static constexpr unsigned post_ctr_authenticated=std::count_if(formatter_post_ctr_private::accesses.begin(),formatter_post_ctr_private::accesses.end(),[](auto a){return a.expected_value.has_value();});
static_assert(post_ctr_authenticated==5u);
static_assert(std::count_if(formatter_post_ctr_private::accesses.begin(),formatter_post_ctr_private::accesses.end(),[](auto a){return a.stack&&!a.write;})==3u);
static_assert(formatter_post_ctr_private::slots.size()==4u);
static constexpr uint32_t post_ctr_written_mask=[]{
    uint32_t m=0;
    for(const auto a:formatter_post_ctr_private::accesses)if(a.stack&&a.write)
        for(unsigned i=0;i<4u;++i){
            const auto p=int64_t(formatter_post_ctr_private::expected.boundary.caller_offset)+i;
            if(a.address<=p&&p<a.address+a.width)m|=0xffu<<(24u-8u*i);
        }
    return m;
}();
static_assert(std::popcount(post_ctr_written_mask)==16);
#ifdef UNDERCOVER_FORMATTER_PARTIAL
static_assert(formatter_partial_private::path.size()==95u&&formatter_partial_private::accesses.size()==32u);
#ifdef UNDERCOVER_FORMATTER_SPECIAL
static_assert(formatter_special_private::path.size()==96u&&formatter_special_private::accesses.size()==32u);
static_assert(formatter_special_private::expected.boundary.instruction&&formatter_special_private::slots.size()==4u);
static_assert(formatter_special_private::path.back().pc==formatter_partial_private::expected.target);
#ifdef UNDERCOVER_FORMATTER_RELEASE
static_assert(formatter_release_private::path.size()==97u&&formatter_release_private::accesses.size()==32u);
static_assert(formatter_release_private::expected.target_word==0x4e800020u&&formatter_release_private::expected.boundary.instruction);
static_assert(formatter_release_private::path.back().pc==formatter_special_private::expected.target);
#ifdef UNDERCOVER_FORMATTER_RETURN
static_assert(formatter_return_private::caller==formatter_release_private::expected.entry_lr);
static_assert(formatter_return_private::owner==formatter_continuation_private::expected.owner);
static_assert(formatter_return_private::guard==0x44000002u);
#ifdef UNDERCOVER_FORMATTER_CALLER_ARRIVAL
static_assert(formatter_caller_private::owner==formatter_return_private::owner);
static_assert(formatter_caller_private::caller==formatter_return_private::caller);
static_assert(formatter_caller_private::word!=formatter_return_private::guard);
static_assert(formatter_caller_private::call==formatter_continuation_private::path.back().word);
#ifdef UNDERCOVER_FORMATTER_CALLER_BYTE
static_assert(formatter_caller_byte_private::next_pc==formatter_caller_private::caller+4u);
static_assert(formatter_caller_byte_private::offset>=8&&formatter_caller_byte_private::offset<704);
#ifdef UNDERCOVER_FORMATTER_CALLER_INTEGERS
static_assert(formatter_caller_integer_private::path.size()==UNDERCOVER_EXPECTED_CALLER_INTEGER_COUNT);
static_assert(!formatter_caller_integer_private::path.empty()&&formatter_caller_integer_private::path.size()<=8u);
static_assert(formatter_caller_integer_private::path.front().pc==formatter_caller_byte_private::next_pc);
static_assert(formatter_caller_integer_private::path.front().word==formatter_caller_byte_private::next_word);
static_assert(formatter_caller_integer_private::end_pc==formatter_caller_integer_private::path.back().pc+4u);
#ifdef UNDERCOVER_FORMATTER_CALLER_BRANCH
static_assert(formatter_caller_branch_private::pc==formatter_caller_integer_private::end_pc);
static_assert(formatter_caller_branch_private::word==formatter_caller_integer_private::end_word);
static_assert(formatter_caller_branch_private::owner==formatter_caller_private::owner);
static_assert(!formatter_caller_branch_private::taken);
static_assert(formatter_caller_branch_private::next_pc==formatter_caller_branch_private::pc+4u);
#ifdef UNDERCOVER_FORMATTER_CALLER_SECOND_BRANCH
static_assert(formatter_caller_second_branch_private::pc==formatter_caller_branch_private::next_pc);
static_assert(formatter_caller_second_branch_private::word==formatter_caller_branch_private::next_word);
static_assert(formatter_caller_second_branch_private::owner==formatter_caller_branch_private::owner);
static_assert(formatter_caller_second_branch_private::owner_size==formatter_caller_branch_private::owner_size);
static_assert(formatter_caller_second_branch_private::taken);
static_assert(formatter_caller_second_branch_private::next_pc!=formatter_caller_branch_private::other_pc);
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_INTEGERS
static_assert(formatter_caller_post_integer_private::path.size()==UNDERCOVER_EXPECTED_CALLER_POST_INTEGER_COUNT);
static_assert(!formatter_caller_post_integer_private::path.empty()&&formatter_caller_post_integer_private::path.size()<=8u);
static_assert(formatter_caller_post_integer_private::path.front().pc==formatter_caller_second_branch_private::next_pc);
static_assert(formatter_caller_post_integer_private::path.front().word==formatter_caller_second_branch_private::next_word);
static_assert(formatter_caller_post_integer_private::end_pc==formatter_caller_post_integer_private::path.back().pc+4u);
#ifdef UNDERCOVER_FORMATTER_CALLER_THIRD_BRANCH
static_assert(formatter_caller_third_branch_private::pc==formatter_caller_post_integer_private::end_pc);
static_assert(formatter_caller_third_branch_private::word==formatter_caller_post_integer_private::end_word);
static_assert(formatter_caller_third_branch_private::owner==formatter_caller_branch_private::owner);
static_assert(formatter_caller_third_branch_private::owner_size==formatter_caller_branch_private::owner_size);
static_assert(!formatter_caller_third_branch_private::taken);
static_assert(formatter_caller_third_branch_private::next_pc==formatter_caller_third_branch_private::pc+4u);
#ifdef UNDERCOVER_FORMATTER_CALLER_FOURTH_BRANCH
static_assert(formatter_caller_fourth_branch_private::pc==formatter_caller_third_branch_private::next_pc);
static_assert(formatter_caller_fourth_branch_private::word==formatter_caller_third_branch_private::next_word);
static_assert(formatter_caller_fourth_branch_private::owner==formatter_caller_branch_private::owner);
static_assert(formatter_caller_fourth_branch_private::owner_size==formatter_caller_branch_private::owner_size);
static_assert(!formatter_caller_fourth_branch_private::taken);
static_assert(formatter_caller_fourth_branch_private::next_pc==formatter_caller_fourth_branch_private::pc+4u);
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED
static_assert(formatter_caller_mixed_private::path.size()>=1u&&formatter_caller_mixed_private::path.size()<=16u);
static_assert(formatter_caller_mixed_private::path.front().pc==formatter_caller_fourth_branch_private::next_pc);
static_assert(formatter_caller_mixed_private::path.front().word==formatter_caller_fourth_branch_private::next_word);
static_assert(formatter_caller_mixed_private::end_pc==formatter_caller_mixed_private::path.back().next_pc);
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE
static_assert(formatter_caller_mixed_byte_private::next_pc==formatter_caller_mixed_private::end_pc+4u);
static_assert(formatter_caller_mixed_byte_private::offset>=8&&formatter_caller_mixed_byte_private::offset<704);
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_MIXED
static_assert(formatter_caller_post_mixed_private::path.size()==2u);
static_assert(formatter_caller_post_mixed_private::path.front().pc==formatter_caller_mixed_byte_private::next_pc);
static_assert(formatter_caller_post_mixed_private::path.front().word==formatter_caller_mixed_byte_private::next_word);
static_assert(!formatter_caller_post_mixed_private::path[0].other_pc&&formatter_caller_post_mixed_private::path[1].other_pc&&formatter_caller_post_mixed_private::path[1].taken);
static_assert(formatter_caller_post_mixed_private::end_pc==formatter_caller_post_mixed_private::path.back().next_pc);
#ifdef UNDERCOVER_FORMATTER_CALLER_STACK_MOVE
static_assert(formatter_caller_stack_move_private::next_pc==formatter_caller_post_mixed_private::end_pc+4u);
static_assert(formatter_caller_stack_move_private::offset>-0x01800000&&formatter_caller_stack_move_private::offset<0x01800000);
#ifdef UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER
static_assert(formatter_caller_final_integer_private::path.size()==1u);
static_assert(formatter_caller_final_integer_private::path.front().pc==formatter_caller_stack_move_private::next_pc);
static_assert(formatter_caller_final_integer_private::path.front().word==formatter_caller_stack_move_private::next_word);
static_assert(formatter_caller_final_integer_private::end_word>>26==18u&&(formatter_caller_final_integer_private::end_word&3u)==1u);
#ifdef UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
static_assert(formatter_caller_next_entry_private::return_pc==formatter_caller_final_integer_private::end_pc+4u);
static_assert(formatter_caller_next_entry_private::target<formatter_caller_final_integer_private::end_pc);
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
static_assert(formatter_caller_report_byte_private::pc==formatter_caller_next_entry_private::target);
static_assert(formatter_caller_report_byte_private::word==formatter_caller_next_entry_private::word);
static_assert(formatter_caller_report_byte_private::return_pc==formatter_caller_next_entry_private::return_pc);
static_assert(formatter_caller_report_byte_private::next_pc==formatter_caller_report_byte_private::pc+4u);
static_assert(formatter_caller_report_byte_private::report_offset>=8u&&formatter_caller_report_byte_private::report_offset<128u);
static_assert(formatter_caller_report_byte_private::parent_offset==736+int32_t(formatter_caller_report_byte_private::report_offset));
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
static_assert(formatter_report_compare_private::root==formatter_caller_report_byte_private::pc);
static_assert(formatter_report_compare_private::compare_pc==formatter_caller_report_byte_private::next_pc);
static_assert(formatter_report_compare_private::compare_word==formatter_caller_report_byte_private::next_word);
static_assert(formatter_report_compare_private::next_pc==formatter_report_compare_private::root+8u);
static_assert(formatter_report_compare_private::return_pc==formatter_caller_report_byte_private::return_pc);
static_assert(((formatter_report_compare_private::compare_word>>16u)&31u)==formatter_report_compare_private::source_reg);
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
static_assert(formatter_report_copy_private::root==formatter_report_compare_private::root);
static_assert(formatter_report_copy_private::pc==formatter_report_compare_private::next_pc);
static_assert(formatter_report_copy_private::word==formatter_report_compare_private::next_word);
static_assert(formatter_report_copy_private::next_pc==formatter_report_copy_private::pc+4u);
static_assert(formatter_report_copy_private::return_pc==formatter_report_compare_private::return_pc);
static_assert((formatter_report_copy_private::word>>26u)==31u);
static_assert(((formatter_report_copy_private::word>>1u)&1023u)==444u);
static_assert((formatter_report_copy_private::word&1u)==0u);
static_assert(((formatter_report_copy_private::word>>21u)&31u)==formatter_report_copy_private::source_reg);
static_assert(((formatter_report_copy_private::word>>11u)&31u)==formatter_report_copy_private::source_reg);
static_assert(((formatter_report_copy_private::word>>16u)&31u)==formatter_report_copy_private::destination_reg);
#endif
#endif
#endif
#endif // UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
#endif
#endif
#endif
#endif
static_assert(std::count_if(formatter_caller_mixed_private::path.begin(),formatter_caller_mixed_private::path.end(),[](auto s){return !s.other_pc;})==UNDERCOVER_EXPECTED_CALLER_MIXED_INTEGERS);
static_assert(std::count_if(formatter_caller_mixed_private::path.begin(),formatter_caller_mixed_private::path.end(),[](auto s){return s.other_pc&&s.taken;})==UNDERCOVER_EXPECTED_CALLER_MIXED_TAKEN);
static_assert(std::count_if(formatter_caller_mixed_private::path.begin(),formatter_caller_mixed_private::path.end(),[](auto s){return s.other_pc&&!s.taken;})==UNDERCOVER_EXPECTED_CALLER_MIXED_FALLTHROUGH);
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
static_assert(formatter_partial_private::expected.boundary.instruction&&formatter_partial_private::slots.size()==4u);
static_assert(std::count_if(formatter_partial_private::accesses.begin(),formatter_partial_private::accesses.end(),[](auto a){return a.write;})==17u);
static_assert(std::count_if(formatter_partial_private::accesses.begin(),formatter_partial_private::accesses.end(),[](auto a){return !a.write;})==15u);
static_assert(std::count_if(formatter_partial_private::accesses.begin(),formatter_partial_private::accesses.end(),[](auto a){return a.expected_value.has_value();})==5u);
#endif
#endif
#elif defined(UNDERCOVER_FORMATTER_THIRD)
static_assert(formatter_nested_private::path.size()==74u&&formatter_nested_private::accesses.size()==18u);
static constexpr unsigned nested_visits=74u,nested_loads=5u,nested_stores=13u;
#elif defined(UNDERCOVER_FORMATTER_SECOND)
static_assert(formatter_nested_private::path.size()==44u&&formatter_nested_private::accesses.size()==14u);
static constexpr unsigned nested_visits=44u,nested_loads=2u,nested_stores=12u;
#else
static_assert(formatter_nested_private::path.size()==35u&&formatter_nested_private::accesses.size()==13u);
static constexpr unsigned nested_visits=35u,nested_loads=1u,nested_stores=12u;
#endif
static constexpr unsigned nested_saved=formatter_nested_private::slots.size()-1u;
static constexpr unsigned nested_authenticated=std::count_if(formatter_nested_private::accesses.begin(),formatter_nested_private::accesses.end(),[](auto a){return a.expected_value.has_value();});
static_assert(std::all_of(formatter_nested_private::accesses.begin(),formatter_nested_private::accesses.end(),[](auto a){return a.write||a.stack||a.expected_value.has_value();}));
static_assert(std::count_if(formatter_nested_private::accesses.begin(),formatter_nested_private::accesses.end(),[](auto a){return a.write;})==nested_stores);
 #if defined(UNDERCOVER_FORMATTER_CONTROL)
static_assert(nested_saved==3u&&nested_authenticated==5u);
#elif defined(UNDERCOVER_FORMATTER_THIRD)
static_assert(nested_saved>=3u&&nested_saved<=18u&&nested_authenticated>=3u&&nested_authenticated<=nested_loads);
#else
static_assert(nested_saved==3u&&nested_authenticated==nested_loads);
#endif
struct FormatterNestedStop{};
#endif
#endif
#endif
static bool post_stm_formatter_held(nw::CPUContext&);
[[noreturn]]static void post_stm_formatter_refuse(unsigned);
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
#endif
[[noreturn]]static void third_dispatch_refuse(unsigned);
#endif
static bool third_irq_held(nw::CPUContext&);
[[noreturn]]static void third_vector_refuse(unsigned);
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
#endif
#endif
#endif
#endif
#endif
#endif
#endif
static NativeIosTransport* submit_host=nullptr;
static nw::CPUContext* submit_cpu=nullptr;
static PostAckSubmitJoin* submit_join=nullptr;
static unsigned submit_stage=0,submit_vectors=0,submit_acks=0;
static unsigned submit_polls=0;
static SecondCompletionAck* si_ack=nullptr;
static unsigned callbacks=0,loop_polls=0,control_writes=0,last_stage=0,last_reason=0,last_trial=0;
struct HarnessFailure:std::runtime_error{unsigned line;explicit HarnessFailure(unsigned n):std::runtime_error("harness assertion"),line(n){}};
struct WitnessFailure:std::runtime_error{WitnessFailure():std::runtime_error("witness refusal"){}};
static void need(bool b,const std::source_location l=std::source_location::current()){
    if(!b)throw HarnessFailure(l.line());
}
static bool raw_device_ok(nw::CPUContext& c){
    return si_ack&&si_ack->token()==3u&&si_ack->postack_device_quiescent(c.inst_count);
}
static bool device_ok(nw::CPUContext& c){
    const bool ok=raw_device_ok(c);
#ifdef UNDERCOVER_V1320_SAVE_CONTINUITY
    return ok&&(!coop_saved||coop_saved->preserved(c,true));
#else
    return ok;
#endif
}
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
[[noreturn]]static void selection_refuse(unsigned kind){
    std::cout<<"V1328_SELECTION_REFUSAL kind="<<kind<<" stage="<<selection_witness->stage()
        <<" reason="<<selection_witness->failure()<<" route="<<selection_route->stage()
        <<" route_reason="<<selection_route->failure()<<" visits="<<selection_route->visits()<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_V1334_COOP_LOAD
static bool load_held(nw::CPUContext& c){
    return selection_witness&&selection_witness->loader_boundary(c,raw_device_ok(c));
}
[[noreturn]]static void load_refuse(unsigned kind){
    std::cout<<"V1334_LOAD_REFUSAL kind="<<kind<<" stage="<<coop_load->stage()
        <<" reason="<<coop_load->failure()<<" abi="<<load_save->context().failure()
        <<" visits="<<coop_load->visits()<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
[[noreturn]]static void sleep_resume_refuse(unsigned kind){
    std::cout<<"V1336_SLEEP_REFUSAL kind="<<kind<<" stage="<<sleep_resume->stage()
        <<" reason="<<sleep_resume->failure()<<" visits="<<sleep_resume->visits()<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
[[noreturn]]static void sleep_exit_refuse(unsigned kind){
    std::cout<<"V1340_EXIT_REFUSAL kind="<<kind<<" stage="<<sleep_exit->stage()
        <<" reason="<<sleep_exit->failure()<<" visits="<<sleep_exit->visits()<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
static bool submit_held(nw::CPUContext& c){
    return selection_witness&&submit_resume&&!(cause.load()&mask.load())&&
        selection_witness->selected_response_held(c,raw_device_ok(c),submit_resume->expected_msr());
}
[[noreturn]]static void submit_resume_refuse(unsigned kind){
    std::cout<<"V1344_SUBMIT_REFUSAL kind="<<kind<<" stage="<<submit_resume->stage()
        <<" reason="<<submit_resume->failure()<<" visits="<<submit_resume->visits()<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
static bool allocator_held(nw::CPUContext& c){
    return selection_witness&&allocator_release&&!(cause.load()&mask.load())&&
        selection_witness->selected_response_held(c,raw_device_ok(c),allocator_release->expected_msr());
}
#ifdef UNDERCOVER_V1358_OPEN_RETURN
static bool open_return_held(nw::CPUContext& c){
    return open_return&&allocator_release&&allocator_held(c)&&allocator_release->storage_preserved(c,true);
}
static bool open_descriptor(nw::CPUContext& c){
#ifdef UNDERCOVER_V1379_SECOND_RETURN
    if(second_scheduler_lane)return allocator_descriptor&&allocator_release&&allocator_descriptor->second_completed()&&
        allocator_descriptor->identity_after_release(c)&&OpenTransactionEpoch(second_irq_kind).acknowledged_descriptors(3u-second_irq_kind);
#endif
    return allocator_descriptor&&allocator_release&&allocator_descriptor->returned(c,allocator_release->metadata_stores())&&B::is_open(0u,open_return_device);
}
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
static bool stm_ioctl_held(nw::CPUContext& c){
    return stm_ioctl&&selection_witness&&allocator_release&&open_descriptor(c)&&!(cause.load()&mask.load())&&
        selection_witness->selected_response_held(c,raw_device_ok(c),stm_ioctl->expected_msr())&&
        allocator_release->storage_preserved_at(c,true,stm_ioctl->expected_msr());
}
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
static bool ioctl_alloc_held(nw::CPUContext& c){
    // Retire the already released wire and heap snapshot, not the native
    // mailbox, selected OSContext, completed descriptors or device guards.
    return ioctl_alloc&&selection_witness&&allocator_descriptor&&allocator_descriptor->second_completed()&&
        OpenTransactionEpoch(second_irq_kind).acknowledged_descriptors(3u-second_irq_kind)&&!(cause.load()&mask.load())&&
        selection_witness->selected_after_release(c,raw_device_ok(c));
}
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
[[noreturn]]static void ioctl_build_refuse(unsigned kind){
    std::cout<<"V1392_CONSTRUCTION_REFUSAL kind="<<kind<<" stage="<<ioctl_build->stage()<<" reason="<<ioctl_build->failure()
        <<" visits="<<ioctl_build->visits()<<" stores="<<ioctl_build->stores()<<" request="<<ioctl_build->request_stores()
        <<" fence="<<ioctl_build->store_failure()<<" range="<<ioctl_build->range_failure()<<" base_class="<<ioctl_build->base_class()
        <<" ordinal="<<ioctl_build->ordinal()<<" wire="<<ioctl_build->wire_failure()<<" control="<<ioctl_build->control_failure()<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
static bool ioctl_flush_held(nw::CPUContext& c){
#ifdef UNDERCOVER_V1407_IOCTL_HEADER
    // Prefix construction still needs the old wrapper-frame guard.
    if(ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u){
        if(!ioctl_build||!ioctl_build->identity_preserved(c,ioctl_alloc_held(c))||
           ioctl_header_shadow.size()!=ioctl_build->allocated_size())return false;
        for(unsigned i=0;i<ioctl_header_shadow.size();++i)
            if(c.mmu.read8(ioctl_build->request()+i)!=ioctl_header_shadow[i])return false;
        return true;
    }
#endif
    return ioctl_build&&ioctl_build->preserved(c,ioctl_alloc_held(c));
}
[[noreturn]]static void ioctl_flush_refuse(unsigned kind){
    std::cout<<"V1398_FLUSH_REFUSAL kind="<<kind<<" stage="<<(ioctl_flush?ioctl_flush->stage():0u)
        <<" reason="<<(ioctl_flush?ioctl_flush->failure():0u)<<" lines="<<(ioctl_flush?ioctl_flush->lines():0u)
        <<" polls="<<(ioctl_flush?ioctl_flush->polls():0u)<<" empty="<<(ioctl_flush?ioctl_flush->zero():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
[[noreturn]]static void ioctl_tail_refuse(unsigned kind){
    std::cout<<"V1401_TAIL_REFUSAL kind="<<kind<<" stage="<<(ioctl_tail?ioctl_tail->stage():0u)
        <<" reason="<<(ioctl_tail?ioctl_tail->failure():0u)<<" visits="<<(ioctl_tail?ioctl_tail->visits():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
static bool ioctl_submit_prefix_held(nw::CPUContext& c){return ioctl_build&&ioctl_build->identity_preserved(c,ioctl_alloc_held(c));}
[[noreturn]]static void ioctl_submit_prefix_refuse(unsigned kind){
    std::cout<<"V1404_PREFIX_REFUSAL kind="<<kind<<" stage="<<(ioctl_submit_prefix?ioctl_submit_prefix->stage():0u)
        <<" reason="<<(ioctl_submit_prefix?ioctl_submit_prefix->failure():0u)<<" visits="<<(ioctl_submit_prefix?ioctl_submit_prefix->visits():0u)
        <<" stores="<<(ioctl_submit_prefix?ioctl_submit_prefix->stores():0u)<<" queue="<<(ioctl_submit_prefix?ioctl_submit_prefix->queue_stores():0u)
        <<" fence="<<(ioctl_submit_prefix?ioctl_submit_prefix->store_failure():0u)<<" range="<<(ioctl_submit_prefix?ioctl_submit_prefix->range_failure():0u)
        <<" ordinal="<<(ioctl_submit_prefix?ioctl_submit_prefix->ordinal():0u)
        <<" detail="<<(ioctl_submit_prefix?ioctl_submit_prefix->detail():0u)<<" queue_path="<<(ioctl_submit_prefix?ioctl_submit_prefix->queue_path():0u)
        <<" queue_class="<<(ioctl_submit_prefix?ioctl_submit_prefix->queue_class():0u)<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
[[noreturn]]static void ioctl_submit_queue_refuse(unsigned kind){
    std::cout<<"V1410_QUEUE_REFUSAL kind="<<kind<<" stage="<<(ioctl_submit_queue?ioctl_submit_queue->stage():0u)
             <<" reason="<<(ioctl_submit_queue?ioctl_submit_queue->failure():0u)
             <<" visits="<<(ioctl_submit_queue?ioctl_submit_queue->visits():0u)
             <<" stores="<<(ioctl_submit_queue?ioctl_submit_queue->stores():0u)
             <<" polls="<<(ioctl_submit_queue?ioctl_submit_queue->polls():0u)
             <<" ordinal="<<(ioctl_submit_queue?ioctl_submit_queue->ordinal():0u)
             <<" fence="<<(ioctl_submit_queue?ioctl_submit_queue->fence_error():0u)
             <<" range="<<(ioctl_submit_queue?ioctl_submit_queue->range_error():0u)
             <<" base="<<(ioctl_submit_queue?ioctl_submit_queue->base_class():0u)
             <<" dest="<<(ioctl_submit_queue?ioctl_submit_queue->destination_class():0u)
             <<" value="<<(ioctl_submit_queue?ioctl_submit_queue->value_class():0u)
             <<" form="<<(ioctl_submit_queue?ioctl_submit_queue->store_form():0u)
             <<" ring="<<(ioctl_submit_queue?ioctl_submit_queue->ring_error():0u)
             <<" ring_stores="<<(ioctl_submit_queue?ioctl_submit_queue->ring_stores():0u)<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_IPC_PROFILE
[[noreturn]]static void ioctl_profile_refuse(unsigned kind){
    std::cout<<"IPC_PROFILE_REFUSAL kind="<<kind<<" stage="<<(ioctl_profile?ioctl_profile->stage():0u)
             <<" reason="<<(ioctl_profile?ioctl_profile->failure():0u)<<" memory="<<(ioctl_profile?ioctl_profile->memory_failure():0u)
             <<" visits="<<(ioctl_profile?ioctl_profile->visits():0u)<<" stores="<<(ioctl_profile?ioctl_profile->stores():0u)
             <<" polls="<<(ioctl_profile?ioctl_profile->polls():0u)<<" ordinal="<<(ioctl_profile?ioctl_profile->ordinal():0u)<<'\n';
    throw WitnessFailure{};
}
void ipc_profile_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(ioctl_profile&&!ioctl_profile->before(c,pc,w,ioctl_flush_held(c)))ioctl_profile_refuse(2);
}
#ifdef UNDERCOVER_IPC_DISPATCH
static bool ioctl_dispatch_storage_held(nw::CPUContext& c,bool deferred=false,uint32_t restored_msr=0){
    // The device gate owns the third transport. Do not compare the
    // retired second mailbox snapshot after original PPCMSG/PPCCTRL.
    const bool held=ioctl_dispatch_cpu==&c&&ioctl_alloc&&selection_witness&&allocator_descriptor&&
        allocator_descriptor->second_completed()&&allocator_descriptor->identity_after_release(c)&&
        OpenTransactionEpoch(second_irq_kind).acknowledged_descriptors(3u-second_irq_kind)&&
        (deferred?(cause.load()&mask.load())==H::PI_HOLLYWOOD:!(cause.load()&mask.load()))&&
        selection_witness->selected_storage_after_release(c,raw_device_ok(c));
    if(!ioctl_build||!(restored_msr?ioctl_build->identity_after_enable(c,held,restored_msr):
          ioctl_build->identity_preserved(c,held))||ioctl_header_shadow.size()!=ioctl_build->allocated_size())return false;
    for(unsigned i=0;i<ioctl_header_shadow.size();++i)
        if(c.mmu.read8(ioctl_build->request()+i)!=ioctl_header_shadow[i])return false;
    return true;
}
static bool ioctl_dispatch_held(nw::CPUContext& c){
    return ioctl_event_gate&&ioctl_event_gate->submission_held(ioctl_dispatch_storage_held(c));
}
[[noreturn]]static void ioctl_dispatch_refuse(unsigned kind){
    std::cout<<"IPC_DISPATCH_REFUSAL kind="<<kind<<" stage="<<(ioctl_dispatch?ioctl_dispatch->stage():0u)
             <<" reason="<<(ioctl_dispatch?ioctl_dispatch->failure():0u)<<" memory="<<(ioctl_dispatch?ioctl_dispatch->memory_failure():0u)
             <<" gate="<<(ioctl_event_gate?ioctl_event_gate->failure():0u)<<" gate_stage="<<(ioctl_event_gate?ioctl_event_gate->stage():0u)
             <<" visits="<<(ioctl_dispatch?ioctl_dispatch->visits():0u)<<" stores="<<(ioctl_dispatch?ioctl_dispatch->stores():0u)
             <<" calls="<<(ioctl_dispatch?ioctl_dispatch->calls():0u)<<" writes="<<(ioctl_dispatch?ioctl_dispatch->writes():0u)
             <<" reads="<<(ioctl_dispatch?ioctl_dispatch->reads():0u)<<" ordinal="<<(ioctl_dispatch?ioctl_dispatch->ordinal():0u)
             <<" detail="<<(ioctl_dispatch?ioctl_dispatch->detail():0u)<<'\n';
    throw WitnessFailure{};
}
void ipc_dispatch_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
    if(third_return_route)third_return_refuse(1); // no IPC submit leaf is expected here
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACK
    if(third_ack){
        if(std::count_if(deferred_ack_private::words.begin(),deferred_ack_private::words.end(),
            [&](auto x){return x.pc==pc&&x.word==w;})!=1)third_ack_refuse(1);
        return;
    }
#endif
    if(ioctl_dispatch&&!ioctl_dispatch->before(c,pc,w,ioctl_dispatch_held(c)))ioctl_dispatch_refuse(2);
}
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
static bool async_held(nw::CPUContext& c){
    return ioctl_event_gate&&ioctl_event_gate->deferred_held(ioctl_dispatch_storage_held(c,true))&&
        ioctl_dispatch&&ioctl_dispatch->storage_preserved(c);
}
[[noreturn]]static void async_refuse(unsigned kind){
    std::cout<<"ASYNC_SUBMIT_REFUSAL kind="<<kind<<" stage="<<(async_return?async_return->stage():0u)
             <<" reason="<<(async_return?async_return->failure():0u)<<" visits="<<(async_return?async_return->visits():0u)
             <<" polls="<<(async_return?async_return->polls():0u)<<" ordinal="<<(async_return?async_return->ordinal():0u)<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
[[noreturn]]static void async_wrapper_refuse(unsigned kind){
    std::cout<<"ASYNC_WRAPPER_REFUSAL kind="<<kind<<" stage="<<(async_wrapper?async_wrapper->stage():0u)
             <<" reason="<<(async_wrapper?async_wrapper->failure():0u)<<" visits="<<(async_wrapper?async_wrapper->visits():0u)
             <<" loads="<<(async_wrapper?async_wrapper->loads():0u)<<" restored="<<(async_wrapper?async_wrapper->restored():0u)
             <<" ordinal="<<(async_wrapper?async_wrapper->ordinal():0u)
             <<" detail="<<(async_wrapper?async_wrapper->return_detail():0u)<<'\n';
    throw WitnessFailure{};
}
void async_wrapper_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(async_wrapper&&!async_wrapper->before(c,pc,w,async_held(c)))async_wrapper_refuse(2);
}
#ifdef UNDERCOVER_STM_EVENT_RETURN
[[noreturn]]static void stm_event_refuse(unsigned kind){
    std::cout<<"STM_EVENT_RETURN_REFUSAL kind="<<kind<<" stage="<<(stm_event_return?stm_event_return->stage():0u)
             <<" reason="<<(stm_event_return?stm_event_return->failure():0u)<<" visits="<<(stm_event_return?stm_event_return->visits():0u)
             <<" stores="<<(stm_event_return?stm_event_return->stores():0u)<<" ordinal="<<(stm_event_return?stm_event_return->ordinal():0u)<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_STM_OUTER_RESTORE
static bool stm_outer_held(nw::CPUContext& c){
    if(!stm_outer||!stm_event_return||!stm_event_return->flag_preserved(c))return false;
    const auto restored=(c.msr&0x8000u)?stm_outer->expected_msr():0u;
    return ioctl_event_gate&&ioctl_event_gate->deferred_held(ioctl_dispatch_storage_held(c,true,restored))&&
        ioctl_dispatch&&ioctl_dispatch->storage_preserved(c);
}
#ifdef UNDERCOVER_STM_DEFERRED_VECTOR
static bool third_storage_held(nw::CPUContext& c,bool ack){
    // Retired wrapper frames are no longer owned by the submit observer.
    // The interrupt may update the active OSContext; its scheduler tail
    // and all independently authenticated IPC objects remain immutable.
    if(!third_vector||!third_frame_ptr||!third_memory||!ioctl_event_gate||!ioctl_build||!stm_event_return||
       !raw_device_ok(c)||!(ack?ioctl_event_gate->ack_held(true):ioctl_event_gate->deferred_held(true))||!third_memory->settled(c)||
       !stm_event_return->flag_preserved(c)||!ioctl_build->identity_storage_after_irq(c,true)||
       !allocator_descriptor||!allocator_descriptor->identity_after_release(c)||
       c.mmu.read32(0x800000c0u)!=(third_context&0x3fffffffu)||c.mmu.read32(0x800000d4u)!=third_context||
       c.mmu.read32(0x800000e4u)!=third_context||c.mmu.read32(third_wait)||c.mmu.read32(third_wait+4u)||
       !(ack?third_frame_ptr->saved_integer(c,third_context).ok():third_frame_ptr->pending_source(c,cause.load(),mask.load())))return false;
    for(unsigned i=0;i<third_thread_tail.size();++i)
        if(c.mmu.read32(third_context+712u+4u*i)!=third_thread_tail[i])return false;
    return true;
}
static bool third_irq_held(nw::CPUContext& c){return third_storage_held(c,false);}
#ifdef UNDERCOVER_STM_DEFERRED_ACK
static bool third_ack_held(nw::CPUContext& c){return third_storage_held(c,true);}
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
static bool third_return_storage(nw::CPUContext& c){
    // Once the original loader starts, its RFI witness owns the saved
    // integer context. Do not compare a retired pre-RFI frame afterwards.
    return third_return_route&&third_return_join&&raw_device_ok(c)&&
        ioctl_build&&ioctl_build->identity_storage_after_irq(c,true)&&
        stm_event_return&&stm_event_return->flag_preserved(c)&&
        allocator_descriptor&&allocator_descriptor->identity_after_release(c);
}
#ifdef UNDERCOVER_STM_RESUMED_RESTORE
static bool third_resume_held(nw::CPUContext& c){
    return third_resume&&third_return_join&&third_return_join->continuation_held(c,third_return_storage(c));
}
#ifdef UNDERCOVER_STM_FINAL_RETURN
static bool stm_final_held(nw::CPUContext& c){
    return stm_final&&third_return_join&&third_return_join->continuation_held(c,third_return_storage(c));
}
[[noreturn]]static void stm_final_refuse(unsigned kind){
    std::cout<<"STM_FINAL_RETURN_REFUSAL kind="<<kind<<" stage="<<(stm_final?stm_final->stage():0u)
        <<" reason="<<(stm_final?stm_final->failure():0u)<<" visits="<<(stm_final?stm_final->visits():0u)
        <<" loads="<<(stm_final?stm_final->loads():0u)<<" stores="<<(stm_final?stm_final->stores():0u)<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
static bool post_stm_sc_held(nw::CPUContext& c){
    return post_stm_sc&&third_return_join&&third_return_join->continuation_held(c,third_return_storage(c));
}
[[noreturn]]static void post_stm_sc_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_REFUSAL kind="<<kind<<" stage="<<(post_stm_sc?post_stm_sc->stage():0u)
        <<" reason="<<(post_stm_sc?post_stm_sc->failure():0u)<<" visits="<<(post_stm_sc?post_stm_sc->visits():0u)
        <<" stores="<<(post_stm_sc?post_stm_sc->stores():0u)<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
static bool post_stm_formatter_held(nw::CPUContext& c){
    if(!post_stm_formatter||!post_stm_resume||!post_stm_dependency||!post_stm_helper||!post_stm_report||
       !post_stm_version_data||!post_stm_objects||!post_stm_frame||!third_return_join)return false;
    const auto sp=post_stm_formatter->expected_sp();
    const auto outer=post_stm_frame->nested_frame_held(c,
        third_return_join->post_resume_storage_held(c,third_return_storage(c),post_stm_version_msr),
        sp,post_stm_report->linkage_word(),864u,256u);
    const auto report=post_stm_report->child_frame_held(c,outer,sp,post_stm_helper->linkage_word(),736u);
    const auto helper=post_stm_helper->child_frame_held(c,report,sp,post_stm_formatter->linkage_word(),704u);
    return post_stm_resume->object_held(c,post_stm_dependency->object_held(c,
        post_stm_version_data->data_held(c,post_stm_objects->objects_held(c,helper))));
}
[[noreturn]]static void post_stm_formatter_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_FORMATTER_REFUSAL kind="<<kind<<" stage="<<(post_stm_formatter?post_stm_formatter->stage():0u)
        <<" reason="<<(post_stm_formatter?post_stm_formatter->failure():0u)
        <<" visits="<<(post_stm_formatter?post_stm_formatter->visits():0u)
        <<" loads="<<(post_stm_formatter?post_stm_formatter->loads():0u)
        <<" stores="<<(post_stm_formatter?post_stm_formatter->stores():0u)<<'\n';
    throw WitnessFailure{};
}
void post_stm_sc_formatter_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_formatter||!post_stm_formatter->before(c,pc,w,post_stm_formatter_held(c)))post_stm_formatter_refuse(2);
}
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER_LEAF
static bool post_stm_formatter_leaf_held(nw::CPUContext& c){
    return post_stm_formatter&&post_stm_formatter->frame_held(c,post_stm_formatter_held(c));
}
[[noreturn]]static void post_stm_formatter_leaf_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_FORMATTER_LEAF_REFUSAL kind="<<kind<<" stage="<<(post_stm_formatter_leaf?post_stm_formatter_leaf->stage():0u)
        <<" reason="<<(post_stm_formatter_leaf?post_stm_formatter_leaf->failure():0u)
        <<" visits="<<(post_stm_formatter_leaf?post_stm_formatter_leaf->visits():0u)
        <<" loads="<<(post_stm_formatter_leaf?post_stm_formatter_leaf->loads():0u)
        <<" stores="<<(post_stm_formatter_leaf?post_stm_formatter_leaf->stores():0u)<<'\n';
    throw WitnessFailure{};
}
void post_stm_sc_formatter_leaf_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_formatter_leaf||!post_stm_formatter_leaf->before(c,pc,w,post_stm_formatter_leaf_held(c)))post_stm_formatter_leaf_refuse(2);
}
#ifdef UNDERCOVER_FORMATTER_CONTINUATION
static bool formatter_continuation_held(nw::CPUContext& c){
    return post_stm_formatter_leaf&&post_stm_formatter_leaf->object_held(c,post_stm_formatter_leaf_held(c));
}
[[noreturn]]static void formatter_continuation_refuse(unsigned kind){
    std::cout<<"FORMATTER_CONTINUATION_REFUSAL kind="<<kind<<" stage="<<(formatter_continuation?formatter_continuation->stage():0u)
        <<" reason="<<(formatter_continuation?formatter_continuation->failure():0u)
        <<" visits="<<(formatter_continuation?formatter_continuation->visits():0u)<<'\n';
    throw WitnessFailure{};
}
void formatter_continuation_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!formatter_continuation||!formatter_continuation->before(c,pc,w,formatter_continuation_held(c)))formatter_continuation_refuse(2);
}
#ifdef UNDERCOVER_FORMATTER_NESTED
static unsigned formatter_nested_held_mask=0;
static uint64_t formatter_nested_parent_age=0,formatter_nested_parent_limit=0,formatter_nested_parent_baseline=0;
static uint64_t formatter_nested_outer_age=0,formatter_nested_outer_limit=0,formatter_nested_outer_baseline=0;
static bool formatter_nested_held(nw::CPUContext& c){
    formatter_nested_held_mask=0;formatter_nested_parent_age=0;formatter_nested_parent_limit=0;formatter_nested_parent_baseline=0;
    formatter_nested_outer_age=0;formatter_nested_outer_limit=0;formatter_nested_outer_baseline=0;
    if(!formatter_nested||!post_stm_formatter||!post_stm_formatter_leaf||!post_stm_resume||
       !post_stm_dependency||!post_stm_helper||!post_stm_report||!post_stm_version_data||
       !post_stm_objects||!post_stm_frame||!third_return_join)return false;
    const auto sp=c.gpr[1],parent=post_stm_formatter->expected_sp();
    if(sp!=parent&&sp!=parent-48u)return false;
    const unsigned extra=parent-sp;
    const auto joined=third_return_join->post_resume_storage_held(c,third_return_storage(c),post_stm_version_msr);
    const auto budget=formatter_nested->caller_post_fourth_tick_budget();
    const bool captured=post_stm_frame->nested_checkpoint_valid();
    const auto outer=captured?(budget&&post_stm_frame->nested_frame_held_after_checkpoint(c,joined,
        sp,post_stm_report->linkage_word(),864u+extra,*budget)):
        post_stm_frame->nested_frame_held(c,joined,sp,post_stm_report->linkage_word(),864u+extra,256u);
    formatter_nested_outer_age=std::min<uint64_t>(999u,post_stm_frame->frame_age(c));
    formatter_nested_outer_baseline=post_stm_frame->nested_checkpoint_age();
    formatter_nested_outer_limit=captured&&budget?formatter_nested_outer_baseline+*budget:256u;
    const auto report=post_stm_report->child_frame_held(c,outer,sp,post_stm_helper->linkage_word(),736u+extra,extra);
    const auto helper=post_stm_helper->child_frame_held(c,report,sp,post_stm_formatter->linkage_word(),704u+extra,extra);
    const auto parent_held=formatter_nested->has_caller_stores()?
        post_stm_formatter->child_frame_held_with_stores(c,helper,*formatter_nested):
        post_stm_formatter->child_frame_held(c,helper,sp,formatter_nested->linkage_word());
    const auto objects=post_stm_objects->objects_held(c,parent_held);
    const auto data=post_stm_version_data->data_held(c,objects);
    const auto dependency=post_stm_dependency->object_held(c,data);
    const auto resume=post_stm_resume->object_held(c,dependency);
    const auto leaf=post_stm_formatter_leaf->object_held(c,resume);
    formatter_nested_held_mask=unsigned(joined)|(unsigned(outer)<<1)|(unsigned(report)<<2)|(unsigned(helper)<<3)|
        (unsigned(parent_held)<<4)|(unsigned(objects)<<5)|(unsigned(data)<<6)|(unsigned(dependency)<<7)|
        (unsigned(resume)<<8)|(unsigned(leaf)<<9);
    formatter_nested_parent_age=std::min<uint64_t>(999u,post_stm_formatter->frame_age(c));
    formatter_nested_parent_limit=formatter_nested->caller_parent_tick_limit();
    formatter_nested_parent_baseline=formatter_nested->caller_parent_baseline();
    return leaf;
}
[[noreturn]]static void formatter_nested_refuse(unsigned kind){
    std::cout<<"FORMATTER_NESTED_REFUSAL kind="<<kind<<" stage="<<(formatter_nested?formatter_nested->stage():0u)
        <<" reason="<<(formatter_nested?formatter_nested->failure():0u)
        <<" visits="<<(formatter_nested?formatter_nested->visits():0u)
        <<" loads="<<(formatter_nested?formatter_nested->loads():0u)
        <<" stores="<<(formatter_nested?formatter_nested->stores():0u)
        <<" branches="<<(formatter_nested?formatter_nested->caller_branch_visits():0u)
        <<" post="<<(formatter_nested?formatter_nested->caller_post_integer_visits():0u)
        <<" branch_detail="<<(formatter_nested?formatter_nested->branch_refusal_detail():0u)
        <<" held_mask="<<formatter_nested_held_mask<<" parent_age="<<formatter_nested_parent_age
        <<" parent_limit="<<formatter_nested_parent_limit<<" parent_baseline="<<formatter_nested_parent_baseline
        <<" outer_age="<<formatter_nested_outer_age<<" outer_limit="<<formatter_nested_outer_limit
        <<" outer_baseline="<<formatter_nested_outer_baseline<<'\n';
    throw WitnessFailure{};
}
void formatter_nested_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!formatter_nested)formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_ARRIVAL
#ifdef UNDERCOVER_FORMATTER_CALLER_BYTE
#ifdef UNDERCOVER_FORMATTER_CALLER_INTEGERS
#ifdef UNDERCOVER_FORMATTER_CALLER_BRANCH
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED
    if(formatter_nested->stage()==18u){
        if(!formatter_nested->caller_mixed_boundary(c,pc,w,formatter_nested_held(c)))formatter_nested_refuse(2);
        if(formatter_nested->stage()==19u){
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE
            if(!formatter_nested->resume_caller_mixed_byte(c,formatter_caller_mixed_byte_private::offset,
                formatter_caller_mixed_byte_private::value,formatter_caller_mixed_byte_private::next_pc,
                formatter_caller_mixed_byte_private::next_word,formatter_nested_held(c)
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_MIXED
                ,formatter_caller_post_mixed_private::path,formatter_caller_post_mixed_private::end_pc,formatter_caller_post_mixed_private::end_word
#endif
                ))formatter_nested_refuse(2);
#else
            ++formatter_nested_count;throw FormatterNestedStop{};
#endif
        }
        return;
    }
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE
    if(formatter_nested->stage()==20u){
        if(!formatter_nested->stop_after_caller_mixed_byte(c,pc,w,formatter_nested_held(c)))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_MIXED
        if(!formatter_nested->resume_caller_post_mixed(c,formatter_nested_held(c)))formatter_nested_refuse(2);
        return;
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_MIXED
    if(formatter_nested->stage()==22u){
        if(!formatter_nested->caller_post_mixed_boundary(c,pc,w,formatter_nested_held(c)))formatter_nested_refuse(2);
        if(formatter_nested->stage()==23u){
#ifdef UNDERCOVER_FORMATTER_CALLER_STACK_MOVE
            if(!formatter_nested->resume_caller_stack_move(c,formatter_caller_stack_move_private::offset,
                formatter_caller_stack_move_private::next_pc,formatter_caller_stack_move_private::next_word,formatter_nested_held(c)
#ifdef UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER
                ,undercover::wii::ScCallerIntegerStep{formatter_caller_final_integer_private::path.front().pc,formatter_caller_final_integer_private::path.front().word,formatter_caller_final_integer_private::path.front().inputs},formatter_caller_final_integer_private::end_pc,formatter_caller_final_integer_private::end_word
#endif
                ))formatter_nested_refuse(2);
#else
            ++formatter_nested_count;throw FormatterNestedStop{};
#endif
        }
        return;
    }
#ifdef UNDERCOVER_FORMATTER_CALLER_STACK_MOVE
    if(formatter_nested->stage()==24u){
        if(!formatter_nested->stop_after_caller_stack_move(c,pc,w,formatter_nested_held(c)))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER
        if(!formatter_nested->resume_caller_final_integer(c,formatter_nested_held(c)))formatter_nested_refuse(2);
        return;
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#ifdef UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER
    if(formatter_nested->stage()==26u){
        if(!formatter_nested->stop_after_caller_final_integer(c,pc,w,formatter_nested_held(c)))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
        if(!formatter_nested->resume_caller_next_entry(c,formatter_caller_next_entry_private::target,
             formatter_caller_next_entry_private::word,formatter_caller_next_entry_private::return_pc,formatter_nested_held(c)
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
             ,formatter_caller_report_byte_private::next_word
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
             ,formatter_report_compare_private::next_word
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
             ,formatter_report_copy_private::next_word
#endif
#endif
             ))formatter_nested_refuse(2);
        return;
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#ifdef UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
    if(formatter_nested->stage()==28u){
        const bool held=formatter_nested_held(c);
        if(!formatter_nested->stop_at_caller_next_entry(c,pc,w,held))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
        if(!formatter_report_byte||!post_stm_report||!post_stm_helper)formatter_nested_refuse(2);
        const uint64_t address=uint64_t(c.gpr[1])+uint32_t(formatter_caller_report_byte_private::parent_offset);
        if(address>=0x81800000ull)formatter_nested_refuse(2);
        const FormatterReportByteStep step{pc,w,formatter_caller_report_byte_private::next_pc,
            formatter_caller_report_byte_private::next_word,formatter_caller_report_byte_private::return_pc,
            uint32_t(address),c.gpr[1],post_stm_helper->linkage_word(),736u,0u,
            formatter_caller_report_byte_private::value};
        if(!formatter_report_byte->arm_native(c,*post_stm_report,step,held
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
                ,formatter_report_compare_private::next_word
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
                ,formatter_report_copy_private::next_word
#endif
#endif
                )||
           !formatter_nested->resume_caller_report_byte(c,formatter_caller_report_byte_private::parent_offset,
             formatter_caller_report_byte_private::report_offset,formatter_caller_report_byte_private::value,
             formatter_report_byte->stage()==1u,held))formatter_nested_refuse(2);
        return; // the original translated byte load executes
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
    if(formatter_nested->stage()==30u){
        const bool held=formatter_nested_held(c);
        if(!formatter_report_byte||!post_stm_report||
           !formatter_report_byte->observe_native_label(c,*post_stm_report,pc,w,held)||
           !formatter_nested->stop_after_caller_report_byte(c,pc,w,formatter_report_byte->stage()==2u,held))
            formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
        if(!formatter_report_compare||
           !formatter_report_compare->arm(c,formatter_report_compare_private::root,
               formatter_report_compare_private::compare_pc,
               formatter_report_compare_private::compare_word,
               formatter_report_compare_private::next_word,
               {formatter_report_compare_private::source_reg,
                formatter_report_compare_private::source_value}
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
               ,formatter_report_copy_private::next_word
#endif
               )||
           !formatter_nested->resume_caller_report_compare(c,
               formatter_report_compare_private::source_reg,
               formatter_report_compare_private::source_value,
               formatter_report_compare->stage()==1u,held))formatter_nested_refuse(2);
        return; // original AOT comparison executes and updates CR
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
    if(formatter_nested->stage()==32u){
        const bool held=formatter_nested_held(c);
        if(!formatter_report_compare||
           !formatter_report_compare->observe(c,pc,w)||
           !formatter_nested->stop_after_caller_report_compare(c,pc,w,
               formatter_report_compare->stage()==2u,held))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
        if(!formatter_nested->resume_caller_report_copy(c,
                formatter_report_copy_private::source_reg,
                formatter_report_copy_private::destination_reg,
                formatter_report_copy_private::source_offset,held))
            formatter_nested_refuse(2);
        return; // the original translated register copy executes
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
    if(formatter_nested->stage()==34u){
        if(!formatter_nested->stop_after_caller_report_copy(c,pc,w,
               formatter_nested_held(c)))formatter_nested_refuse(2);
        ++formatter_nested_count;throw FormatterNestedStop{};
    }
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif // UNDERCOVER_FORMATTER_CALLER_MIXED
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_INTEGERS
    if(formatter_nested->stage()==16u){
        if(!formatter_nested->caller_post_integer_boundary(c,pc,w,formatter_nested_held(c)))formatter_nested_refuse(2);
        if(formatter_nested->stage()==17u){
#ifdef UNDERCOVER_FORMATTER_CALLER_THIRD_BRANCH
            if(!formatter_nested->resume_caller_branch(c,formatter_caller_third_branch_private::owner_size,
                formatter_caller_third_branch_private::taken,formatter_caller_third_branch_private::next_pc,
                formatter_caller_third_branch_private::next_word,formatter_nested_held(c)))formatter_nested_refuse(2);
#else
            ++formatter_nested_count;throw FormatterNestedStop{};
#endif
        }
        return;
    }
#endif
    if(formatter_nested->stage()==14u){
        const bool held=formatter_nested_held(c);
        if(!formatter_nested->stop_after_caller_branch(c,pc,w,held))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_SECOND_BRANCH
        if(formatter_nested->caller_branch_visits()==1u){
            if(!formatter_nested->resume_caller_branch(c,formatter_caller_second_branch_private::owner_size,
                formatter_caller_second_branch_private::taken,formatter_caller_second_branch_private::next_pc,
                formatter_caller_second_branch_private::next_word,held))formatter_nested_refuse(2);
            return; // the original second branch body executes
        }
#ifdef UNDERCOVER_FORMATTER_CALLER_THIRD_BRANCH
        if(formatter_nested->caller_branch_visits()==3u){
#ifdef UNDERCOVER_FORMATTER_CALLER_FOURTH_BRANCH
            if(!formatter_nested->resume_caller_branch(c,formatter_caller_fourth_branch_private::owner_size,
                formatter_caller_fourth_branch_private::taken,formatter_caller_fourth_branch_private::next_pc,
                formatter_caller_fourth_branch_private::next_word,held))formatter_nested_refuse(2);
            return;
#else
            ++formatter_nested_count;throw FormatterNestedStop{};
#endif
        }
#ifdef UNDERCOVER_FORMATTER_CALLER_FOURTH_BRANCH
        if(formatter_nested->caller_branch_visits()==4u){
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED
            // The fourth-branch boundary has just passed the full existing
            // chain. Freeze the outer frame's real age before extending it.
            if(!formatter_nested->reached_caller_branch(c,held)||
               !post_stm_frame->capture_nested_checkpoint(c,held,c.gpr[1],post_stm_report->linkage_word(),864u))
                formatter_nested_refuse(2);
            if(!formatter_nested->resume_caller_mixed(c,formatter_caller_mixed_private::path,
                formatter_caller_mixed_private::end_pc,formatter_caller_mixed_private::end_word,held))formatter_nested_refuse(2);
            return;
#else
            ++formatter_nested_count;throw FormatterNestedStop{};
#endif
        }
#endif
#endif
        if(formatter_nested->caller_branch_visits()!=2u)formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_INTEGERS
        if(!formatter_nested->resume_caller_post_integers(c,formatter_caller_post_integer_private::path,
            formatter_caller_post_integer_private::end_pc,formatter_caller_post_integer_private::end_word,held))formatter_nested_refuse(2);
        return; // the original post-branch integer body executes
#endif
#endif
        ++formatter_nested_count;throw FormatterNestedStop{};
    }
#endif
    if(formatter_nested->stage()==12u){
        const bool held=formatter_nested_held(c);
        if(!formatter_nested->caller_integer_boundary(c,pc,w,held))formatter_nested_refuse(2);
        if(formatter_nested->stage()==13u){
#ifdef UNDERCOVER_FORMATTER_CALLER_BRANCH
            if(!formatter_nested->resume_caller_branch(c,formatter_caller_branch_private::owner_size,
                formatter_caller_branch_private::taken,formatter_caller_branch_private::next_pc,
                formatter_caller_branch_private::next_word,held))formatter_nested_refuse(2);
#else
            ++formatter_nested_count;throw FormatterNestedStop{};
#endif
        }
        return; // the original next integer or branch body executes
    }
#endif
    if(pc==formatter_caller_byte_private::next_pc){
        const bool held=formatter_nested_held(c);
        if(!formatter_nested->stop_after_caller_byte(c,pc,w,held))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_INTEGERS
        if(!formatter_nested->resume_caller_integers(c,formatter_caller_integer_private::path,
             formatter_caller_integer_private::end_pc,formatter_caller_integer_private::end_word,held))formatter_nested_refuse(2);
        return;
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#endif
    if(pc==formatter_caller_private::caller){
        const bool held=formatter_nested_held(c);
        if(!formatter_nested->stop_before_caller_instruction(c,pc,w,held))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_CALLER_BYTE
        if(!formatter_nested->resume_caller_byte(c,formatter_caller_byte_private::offset,formatter_caller_byte_private::value,
                                                 formatter_caller_byte_private::next_pc,formatter_caller_byte_private::next_word,held))formatter_nested_refuse(2);
        return; // the original load body reads the established output byte
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#endif
#ifdef UNDERCOVER_FORMATTER_POST_CTR
#ifdef UNDERCOVER_FORMATTER_PARTIAL
#ifdef UNDERCOVER_FORMATTER_SPECIAL
#ifdef UNDERCOVER_FORMATTER_RELEASE
    if(pc==formatter_release_private::expected.target){
        if(!formatter_nested->stop_before_instruction(c,pc,w,formatter_nested_held(c))||
           !formatter_nested->frame_released()||c.lr!=formatter_release_private::expected.entry_lr||
           c.gpr[1]!=post_stm_formatter->expected_sp())formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_RETURN
#ifdef UNDERCOVER_FORMATTER_CALLER_ARRIVAL
        if(!formatter_nested->arm_caller_arrival(c,formatter_caller_private::owner,formatter_caller_private::caller,
                                                 formatter_caller_private::word,formatter_caller_private::call,
                                                 formatter_nested_held(c)))formatter_nested_refuse(2);
#else
        if(!formatter_nested->arm_native_return(c,formatter_return_private::caller,formatter_return_private::guard,
                                                formatter_nested_held(c)))formatter_nested_refuse(2);
#endif
        return; // the original translated blr transfers to LR
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#endif
    if(pc==formatter_special_private::expected.target){
        const bool held=formatter_nested_held(c);
        if(!formatter_nested->stop_before_instruction(c,pc,w,held)||
           c.lr!=formatter_special_private::expected.entry_lr)formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_RELEASE
        if(!formatter_nested->resume_frame_release(c,formatter_release_private::expected,held))formatter_nested_refuse(2);
        return; // the original addi restores SP; the observer does not
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#endif
    if(pc==formatter_partial_private::expected.target){
        const bool held=formatter_nested_held(c);
        if(!formatter_nested->stop_before_instruction(c,pc,w,held))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_SPECIAL
        if(!formatter_nested->resume_instruction_path(c,formatter_special_private::expected,held))formatter_nested_refuse(2);
        return; // the original mtlr executes; never assign LR in the hook
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#endif
    if(pc==formatter_post_ctr_private::expected.target){
        const bool held=formatter_nested_held(c);
        if(!formatter_nested->stop_before_load(c,pc,w,held))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_PARTIAL
        if(!formatter_nested->resume_stack_path(c,formatter_partial_private::expected,*post_stm_formatter,post_ctr_written_mask,held))formatter_nested_refuse(2);
        return; // the original load body reads the existing guest bytes
#else
        ++formatter_nested_count;throw FormatterNestedStop{};
#endif
    }
#elif defined(UNDERCOVER_FORMATTER_ARRIVAL)
    if(pc==formatter_nested_private::expected.control.destination){
        if(!formatter_nested->stop_before_control_destination(c,pc,w,formatter_nested_held(c)))formatter_nested_refuse(2);
        ++formatter_nested_count;throw FormatterNestedStop{};
    }
#endif
    if(pc==formatter_nested_private::expected.target){
        const bool held=formatter_nested_held(c);
        if(formatter_nested_private::expected.control.destination){
            if(!formatter_nested->stop_before_control(c,pc,w,held))formatter_nested_refuse(2);
#ifdef UNDERCOVER_FORMATTER_ARRIVAL
            return; // let the unchanged translated bctr execute
#endif
        }else if(!formatter_nested->stop_before_load(c,pc,w,held))formatter_nested_refuse(2);
        ++formatter_nested_count;throw FormatterNestedStop{};
    }
    if(!formatter_nested->before(c,pc,w,formatter_nested_held(c)))formatter_nested_refuse(2);
}
#endif
#endif
#endif
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
static bool post_stm_resume_held(nw::CPUContext& c){
    return post_stm_resume&&post_stm_dependency&&post_stm_dependency->object_held(c,post_stm_dependency_held(c));
}
[[noreturn]]static void post_stm_resume_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_REPORT_RESUME_REFUSAL kind="<<kind<<" stage="<<(post_stm_resume?post_stm_resume->stage():0u)
        <<" reason="<<(post_stm_resume?post_stm_resume->failure():0u)
        <<" visits="<<(post_stm_resume?post_stm_resume->visits():0u)<<'\n';
    throw WitnessFailure{};
}
void post_stm_sc_report_resume_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_resume||!post_stm_resume->before(c,pc,w,post_stm_resume_held(c)))post_stm_resume_refuse(2);
}
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
static bool post_stm_dependency_held(nw::CPUContext& c){
    return post_stm_dependency&&post_stm_helper&&post_stm_helper->frame_held(c,post_stm_helper_held(c));
}
[[noreturn]]static void post_stm_dependency_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_REPORT_DEPENDENCY_REFUSAL kind="<<kind<<" stage="<<(post_stm_dependency?post_stm_dependency->stage():0u)
        <<" reason="<<(post_stm_dependency?post_stm_dependency->failure():0u)
        <<" visits="<<(post_stm_dependency?post_stm_dependency->visits():0u)
        <<" loads="<<(post_stm_dependency?post_stm_dependency->loads():0u)
        <<" stores="<<(post_stm_dependency?post_stm_dependency->stores():0u)<<'\n';
    throw WitnessFailure{};
}
void post_stm_sc_report_dependency_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_dependency||!post_stm_dependency->before(c,pc,w,post_stm_dependency_held(c)))post_stm_dependency_refuse(2);
}
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
static bool post_stm_helper_held(nw::CPUContext& c){
    return post_stm_helper&&post_stm_report&&post_stm_version_data&&post_stm_objects&&post_stm_frame&&third_return_join&&
        post_stm_version_data->data_held(c,post_stm_objects->objects_held(c,
        post_stm_report->child_frame_held(c,post_stm_frame->nested_frame_held(c,
        third_return_join->post_resume_storage_held(c,third_return_storage(c),post_stm_version_msr),
        post_stm_helper->expected_sp(),post_stm_report->linkage_word()),
        post_stm_helper->expected_sp(),post_stm_helper->linkage_word())));
}
[[noreturn]]static void post_stm_helper_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_REPORT_HELPER_REFUSAL kind="<<kind<<" stage="<<(post_stm_helper?post_stm_helper->stage():0u)
        <<" reason="<<(post_stm_helper?post_stm_helper->failure():0u)
        <<" visits="<<(post_stm_helper?post_stm_helper->visits():0u)
        <<" stores="<<(post_stm_helper?post_stm_helper->stores():0u)<<'\n';
    throw WitnessFailure{};
}
void post_stm_sc_report_helper_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_helper||!post_stm_helper->before(c,pc,w,post_stm_helper_held(c)))post_stm_helper_refuse(2);
}
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT
static bool post_stm_report_held(nw::CPUContext& c){
    return post_stm_report&&post_stm_version_data&&post_stm_objects&&post_stm_frame&&third_return_join&&
        post_stm_version_data->data_held(c,post_stm_objects->objects_held(c,
        post_stm_frame->nested_frame_held(c,
        third_return_join->post_resume_storage_held(c,third_return_storage(c),post_stm_version_msr),
        post_stm_report->expected_sp(),post_stm_report->linkage_word())));
}
[[noreturn]]static void post_stm_report_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_REPORT_REFUSAL kind="<<kind<<" stage="<<(post_stm_report?post_stm_report->stage():0u)
        <<" reason="<<(post_stm_report?post_stm_report->failure():0u)
        <<" visits="<<(post_stm_report?post_stm_report->visits():0u)
        <<" stores="<<(post_stm_report?post_stm_report->stores():0u)<<'\n';
    throw WitnessFailure{};
}
void post_stm_sc_report_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_report||!post_stm_report->before(c,pc,w,post_stm_report_held(c)))post_stm_report_refuse(2);
}
#endif
#ifdef UNDERCOVER_POST_STM_SC_VERSION
static bool post_stm_version_held(nw::CPUContext& c){
    return post_stm_version&&post_stm_objects&&post_stm_frame&&third_return_join&&
        post_stm_objects->objects_held(c,post_stm_frame->frame_held(c,
        third_return_join->post_resume_storage_held(c,third_return_storage(c),post_stm_version_msr)));
}
[[noreturn]]static void post_stm_version_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_VERSION_REFUSAL kind="<<kind<<" stage="<<(post_stm_version?post_stm_version->stage():0u)
        <<" reason="<<(post_stm_version?post_stm_version->failure():0u)
        <<" ordinal="<<(post_stm_version?post_stm_version->ordinal():0u)
        <<" visits="<<(post_stm_version?post_stm_version->visits():0u)<<'\n';
    throw WitnessFailure{};
}
void post_stm_sc_version_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_version||!post_stm_version->before(c,pc,w,post_stm_version_held(c)))post_stm_version_refuse(2);
}
#endif
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
static bool post_stm_restore_held(nw::CPUContext& c){
    return post_stm_restore&&post_stm_objects&&post_stm_frame&&third_return_join&&
        post_stm_objects->objects_held(c,post_stm_frame->frame_held(c,
        third_return_join->post_resume_storage_held(c,third_return_storage(c),post_stm_restore->expected_msr())));
}
[[noreturn]]static void post_stm_restore_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_RESTORE_REFUSAL kind="<<kind<<" stage="<<(post_stm_restore?post_stm_restore->stage():0u)
        <<" reason="<<(post_stm_restore?post_stm_restore->failure():0u)
        <<" ordinal="<<(post_stm_restore?post_stm_restore->ordinal():0u)
        <<" visits="<<(post_stm_restore?post_stm_restore->visits():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_POST_STM_SC_DECISION
static bool post_stm_decision_held(nw::CPUContext& c){
    return post_stm_decision&&post_stm_frame&&third_return_join&&
        post_stm_frame->frame_held(c,third_return_join->post_resume_storage_held(c,third_return_storage(c),
                                       post_stm_decision->expected_msr()));
}
[[noreturn]]static void post_stm_decision_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_DECISION_REFUSAL kind="<<kind<<" stage="<<(post_stm_decision?post_stm_decision->stage():0u)
        <<" reason="<<(post_stm_decision?post_stm_decision->failure():0u)
        <<" ordinal="<<(post_stm_decision?post_stm_decision->ordinal():0u)
        <<" visits="<<(post_stm_decision?post_stm_decision->visits():0u)
        <<" loads="<<(post_stm_decision?post_stm_decision->loads():0u)
        <<" stores="<<(post_stm_decision?post_stm_decision->stores():0u)<<'\n';
    throw WitnessFailure{};
}
void post_stm_sc_decision_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_decision||!post_stm_decision->before(c,pc,w,post_stm_decision_held(c)))post_stm_decision_refuse(2);
}
#endif
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
static bool post_stm_disable_held(nw::CPUContext& c){
    return post_stm_disable&&post_stm_frame&&third_return_join&&
        post_stm_frame->frame_held(c,third_return_join->post_resume_storage_held(c,third_return_storage(c),
                                       post_stm_disable->expected_msr()));
}
[[noreturn]]static void post_stm_disable_refuse(unsigned kind){
    std::cout<<"POST_STM_SC_DISABLE_REFUSAL kind="<<kind<<" stage="<<(post_stm_disable?post_stm_disable->stage():0u)
        <<" reason="<<(post_stm_disable?post_stm_disable->failure():0u)
        <<" visits="<<(post_stm_disable?post_stm_disable->visits():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
void post_stm_sc_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!post_stm_sc||!post_stm_sc->before(c,pc,w,post_stm_sc_held(c)))post_stm_sc_refuse(2);
}
#endif
void stm_final_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!stm_final||!stm_final->before(c,pc,w,stm_final_held(c)))stm_final_refuse(2);
}
#endif
[[noreturn]]static void third_resume_refuse(unsigned kind){
    std::cout<<"STM_RESUMED_RESTORE_REFUSAL kind="<<kind<<" stage="<<(third_resume?third_resume->stage():0u)
        <<" reason="<<(third_resume?third_resume->failure():0u)<<" visits="<<(third_resume?third_resume->visits():0u)
        <<" rfi="<<(third_return_route?third_return_route->stage():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
[[noreturn]]static void third_return_refuse(unsigned kind){
    std::cout<<"STM_DEFERRED_ACTIVE_RETURN_REFUSAL kind="<<kind
        <<" stage="<<(third_return_route?third_return_route->stage():0u)
        <<" reason="<<(third_return_route?third_return_route->failure():0u)
        <<" entry="<<(third_return_route?third_return_route->entry_refusal():0u)
        <<" join="<<(third_return_join?third_return_join->failure():0u)
        <<" detail="<<(third_return_join?third_return_join->detail():0u)
        <<" gqr="<<(third_return_join?third_return_join->gqr_mismatch_mask():0u)
        <<" visits="<<(third_return_route?third_return_route->visits():0u)
        <<" select="<<(third_return_route?third_return_route->select_state():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
[[noreturn]]static void third_ack_refuse(unsigned kind){
    std::cout<<"STM_DEFERRED_ACK_REFUSAL kind="<<kind<<" stage="<<(third_ack?third_ack->stage():0u)
             <<" reason="<<(third_ack?third_ack->failure():0u)<<" visits="<<(third_ack?third_ack->visits():0u)
             <<" ordinal="<<(third_ack?third_ack->ordinal():0u)<<" detail="<<(third_ack?third_ack->detail():0u)<<" reads="<<(third_ack?third_ack->reads():0u)
             <<" writes="<<(third_ack?third_ack->writes():0u)<<" memory="<<(third_memory?third_memory->failure():0u)
             <<" gate="<<(ioctl_event_gate?ioctl_event_gate->stage():0u)<<" gate_reason="<<(ioctl_event_gate?ioctl_event_gate->failure():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
[[noreturn]]static void third_dispatch_refuse(unsigned kind){
    std::cout<<"STM_DEFERRED_DISPATCH_REFUSAL kind="<<kind<<" stage="<<(third_dispatch?third_dispatch->stage():0u)
             <<" reason="<<(third_dispatch?third_dispatch->failure():0u)<<" detail="<<(third_dispatch?third_dispatch->detail():0u)
             <<" visits="<<(third_dispatch?third_dispatch->visits():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
[[noreturn]]static void third_vector_refuse(unsigned kind){
    std::cout<<"STM_DEFERRED_VECTOR_REFUSAL kind="<<kind<<" stage="<<(third_vector?third_vector->stage():0u)
             <<" reason="<<(third_vector?third_vector->failure():0u)
             <<" memory="<<(third_memory?third_memory->failure():0u)
             <<" detail="<<(third_memory?third_memory->detail():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
static bool stm_outer_pending(nw::CPUContext& c){
    return (c.msr&0x8000u)&&(cause.load()&mask.load())==H::PI_HOLLYWOOD;
}
[[noreturn]]static void stm_outer_refuse(unsigned kind){
    std::cout<<"STM_OUTER_RESTORE_REFUSAL kind="<<kind<<" stage="<<(stm_outer?stm_outer->stage():0u)
             <<" reason="<<(stm_outer?stm_outer->failure():0u)<<" visits="<<(stm_outer?stm_outer->visits():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
void stm_event_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(stm_event_return&&!stm_event_return->before(c,pc,w,async_held(c)))stm_event_refuse(2);
}
#endif
void async_wrapper_return(nw::CPUContext& c,uint32_t pc){
    if(!async_wrapper)return;
    if(!async_wrapper->returned(c,pc,async_held(c),ioctl_prefix->caller_abi(c)))async_wrapper_refuse(4);
    ++async_wrapper_count;
#ifdef UNDERCOVER_STM_EVENT_RETURN
    if(!async_wrapper->reached(c,async_held(c),ioctl_prefix->caller_abi(c)))stm_event_refuse(1);
    stm_event_return=std::make_unique<StmEventReturnWitness>(stm_event_return_private::expected);
    if(!stm_event_return->begin(c,async_held(c)))stm_event_refuse(1);
#else
    throw StmIoctlReached{};
#endif
}
#endif
void async_submit_return(nw::CPUContext& c,uint32_t pc){
    if(!async_return)return;
    if(!async_return->returned(c,pc,async_held(c),ioctl_submit_prefix->caller_abi(c)))async_refuse(4);
    ++async_return_count;
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
    if(!async_return->reached(c,async_held(c),ioctl_submit_prefix->caller_abi(c))||!ioctl_prefix)async_wrapper_refuse(1);
    async_wrapper=std::make_unique<AsyncWrapperReturnWitness>(async_wrapper_private::expected);
    if(!async_wrapper->begin(c,async_held(c),ioctl_prefix->caller_sp()))async_wrapper_refuse(1);
#else
    throw StmIoctlReached{};
#endif
}
#endif
void ipc_dispatch_return(nw::CPUContext& c,uint32_t pc){
    if(!ioctl_dispatch)return;
    if(!ioctl_dispatch->returned(c,pc,ioctl_dispatch_held(c)))ioctl_dispatch_refuse(3);
    if(ioctl_dispatch->stage()==2u){
        if(!ioctl_dispatch->reached(c,ioctl_dispatch_held(c))||ioctl_event_gate->stage()!=3u)ioctl_dispatch_refuse(3);
        ++ioctl_dispatch_count;
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
        const auto gp=c.gpr;const auto gqr=c.gqr;
        const auto pc0=c.pc,lr=c.lr,ctr=c.ctr,xer=c.xer,msr=c.msr,srr0=c.srr0,srr1=c.srr1;
        const auto ticks=c.inst_count;const auto cr=c.cr;
        if(!ioctl_event_gate->accept(c.msr,ioctl_dispatch_storage_held(c))||
           !async_held(c)||c.gpr!=gp||c.gqr!=gqr||c.pc!=pc0||c.lr!=lr||c.ctr!=ctr||c.xer!=xer||
           c.msr!=msr||c.srr0!=srr0||c.srr1!=srr1||c.inst_count!=ticks)async_refuse(1);
        for(unsigned i=0;i<8;++i)if(c.cr[i].lt!=cr[i].lt||c.cr[i].gt!=cr[i].gt||
            c.cr[i].eq!=cr[i].eq||c.cr[i].so!=cr[i].so)async_refuse(1);
        ++ioctl_deferred_count;
        async_return=std::make_unique<AsyncSubmitReturnWitness>(async_submit_private::expected);
        if(!async_return->begin(c,async_held(c),ioctl_submit_prefix->caller_sp()))async_refuse(1);
#else
        throw StmIoctlReached{};
#endif
    }
}
#endif
void ipc_profile_return(nw::CPUContext& c,uint32_t pc){
    if(!ioctl_profile)return;
    if(!ioctl_profile->returned(c,pc,ioctl_flush_held(c)))ioctl_profile_refuse(3);
    ++ioctl_profile_return_count;
#ifdef UNDERCOVER_IPC_DISPATCH
    if(!ioctl_profile->reached(c,ioctl_flush_held(c))||ioctl_dispatch||ioctl_event_gate||!ioctl_build||!ioctl_submit_prefix)
        ioctl_dispatch_refuse(1);
    const uint32_t req=ioctl_build->request(),sp=c.gpr[1],caller_sp=ioctl_submit_prefix->caller_sp();
    if(caller_sp<=sp||caller_sp-sp>512u)ioctl_dispatch_refuse(1);
    ioctl_dispatch_cpu=&c;
    ioctl_event_gate=std::make_unique<StmDeferredEventGate>();
    ioctl_dispatch=std::make_unique<IpcDispatchExecution>(ipc_dispatch_private::expected);
    if(!ioctl_event_gate->begin({req&0x3fffffffu,c.mmu.read32(req+8u),c.mmu.read32(req+16u),c.mmu.read32(req+20u),
                                c.mmu.read32(req+24u),c.mmu.read32(req+28u)},second_irq_kind,ioctl_dispatch_storage_held(c))||
       !ioctl_dispatch->begin(c,ioctl_dispatch_held(c),{req,ioctl_build->allocated_size()},{sp,caller_sp-sp+8u}))
        ioctl_dispatch_refuse(1);
#else
    throw StmIoctlReached{};
#endif
}
#endif
#endif
void v1404_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    // Shared queue initializer also executes in the two earlier Opens.
    if(ioctl_submit_prefix&&!ioctl_submit_prefix->before(c,pc,w,ioctl_submit_prefix_held(c)))ioctl_submit_prefix_refuse(2);
}
#endif
void v1392_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
    if(ioctl_tail){if(!ioctl_tail->before(c,pc,w,ioctl_flush_held(c)))ioctl_tail_refuse(2);return;}
#endif
    if(!ioctl_build||!ioctl_build->before(c,pc,w,ioctl_alloc_held(c)))ioctl_build_refuse(2);
}
#endif
[[noreturn]]static void ioctl_alloc_refuse(unsigned kind){
    std::cout<<"V1387_ALLOCATION_REFUSAL kind="<<kind<<" stage="<<ioctl_alloc->stage()<<" reason="<<ioctl_alloc->failure()
        <<" visits="<<ioctl_alloc->visits()<<" stores="<<ioctl_alloc->stores()<<" heap="<<ioctl_alloc->heap_stores()
        <<" metadata="<<ioctl_alloc->metadata_stores()<<" fence="<<ioctl_alloc->store_failure()<<" range="<<ioctl_alloc->range_failure()
        <<" ordinal="<<ioctl_alloc->store_ordinal()<<" control="<<ioctl_alloc->control()<<'\n';
    throw WitnessFailure{};
}
void v1387_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
    if(ioctl_build&&ioctl_build->stage()==2u){v1392_before(c,pc,w);return;}
#endif
    // Shared veneer/body hooks also execute in the two earlier Opens.
    if(!ioctl_alloc||ioctl_alloc->stage()!=1u)return;
    if(pc==v1387::expected.resume){
        if(!ioctl_alloc->inline_return(c,pc,w,ioctl_alloc_held(c)))ioctl_alloc_refuse(2);
        ++ioctl_alloc_count;throw StmIoctlReached{};
    }
    if(!ioctl_alloc->before(c,pc,w,ioctl_alloc_held(c)))ioctl_alloc_refuse(2);
}
#endif
[[noreturn]]static void ioctl_prefix_refuse(unsigned kind){
    std::cout<<"V1386_PREFIX_REFUSAL kind="<<kind<<" stage="<<(ioctl_prefix?ioctl_prefix->stage():0u)
             <<" reason="<<(ioctl_prefix?ioctl_prefix->failure():0u)<<" visits="<<(ioctl_prefix?ioctl_prefix->visits():0u)
             <<" stores="<<(ioctl_prefix?ioctl_prefix->stores():0u)<<" saved="<<(ioctl_prefix?ioctl_prefix->saved():0u)<<'\n';
    throw WitnessFailure{};
}
void v1386_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
    if(!ioctl_prefix||!ioctl_prefix->before(c,pc,w,stm_ioctl_held(c)))ioctl_prefix_refuse(2);
}
#endif
[[noreturn]]static void stm_ioctl_refuse(unsigned kind){
    std::cout<<"V1383_IOCTL_REFUSAL kind="<<kind<<" stage="<<(stm_ioctl?stm_ioctl->stage():0u)
             <<" reason="<<(stm_ioctl?stm_ioctl->failure():0u)<<" visits="<<(stm_ioctl?stm_ioctl->visits():0u)
             <<" stores="<<(stm_ioctl?stm_ioctl->stores():0u)<<'\n';throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1359_SECOND_OPEN
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
static bool second_request_held(nw::CPUContext& c){
    // Unlike the live reply lane, this proof begins after the first free.
    // Guest allocation can overwrite retired wire bytes and free-list head.
    return second_request&&selection_witness&&allocator_descriptor&&
        selection_witness->selected_after_release(c,raw_device_ok(c))&&
        B::is_open(0u,open_return_device);
}
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
static bool second_submit_held(nw::CPUContext& c){
    // At handoff the completed first transport was exact. Subsequent
    // transport changes are owned by PostAckSubmitJoin, not this guard.
    return second_submit&&second_submit_cpu==&c&&selection_witness&&allocator_descriptor&&
        selection_witness->selected_storage_after_release(c,raw_device_ok(c))&&
        allocator_descriptor->identity_after_release(c)&&B::is_open(0u,open_return_device);
}
[[noreturn]]static void second_submit_refuse(unsigned kind){
    std::cout<<"V1366_SUBMIT_REFUSAL kind="<<kind<<" stage="<<(second_submit?second_submit->stage():0u)
        <<" reason="<<(second_submit?second_submit->failure():0u)<<" write="<<(second_submit?second_submit->write_failure():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
[[noreturn]]static void second_request_refuse(unsigned kind){
    std::cout<<"V1364_REQUEST_REFUSAL kind="<<kind<<" stage="<<(second_request?second_request->stage():0u)
        <<" reason="<<(second_request?second_request->failure():0u)<<" request="<<(second_request?second_request->request_failure():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
[[noreturn]]static void second_open_refuse(unsigned kind){
    std::cout<<"V1359_SECOND_REFUSAL kind="<<kind<<" stage="<<second_open->stage()<<" reason="<<second_open->failure()<<" visits="<<second_open->visits()<<" stores="<<second_open->stores()<<'\n';throw WitnessFailure{};
}
#endif
[[noreturn]]static void open_return_refuse(unsigned kind){
    std::cout<<"V1358_OPEN_REFUSAL kind="<<kind<<" stage="<<(open_return?open_return->stage():0u)
        <<" reason="<<(open_return?open_return->failure():0u)<<" visits="<<(open_return?open_return->visits():0u)<<'\n';
    throw WitnessFailure{};
}
#endif
[[noreturn]]static void allocator_refuse(unsigned kind){
    std::cout<<"V1352_ALLOCATOR_REFUSAL kind="<<kind<<" stage="<<allocator_release->stage()
        <<" reason="<<allocator_release->failure()<<" store="<<allocator_release->store_failure()
        <<" visits="<<allocator_release->visits()<<" writes="<<allocator_release->stores()
        <<" heap="<<allocator_release->heap_stores()<<'\n';
    if(allocator_release->control_failure())
        std::cout<<"V1357_ALLOCATOR_CONTROL detail="<<allocator_release->control_failure()
            <<" owner="<<allocator_release->control_owner()<<'\n';
    if(allocator_release->store_range_failure())
        std::cout<<"V1354_ALLOCATOR_RANGE detail="<<allocator_release->store_range_failure()
            <<" base="<<allocator_release->store_base_class()
            <<" ordinal="<<allocator_release->store_site_ordinal()<<'\n';
    throw WitnessFailure{};
}
#endif
void v1344_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
    if(post_stm_disable){
        // The shared original disable leaf is owned by v1270_before.
        // This secondary installed hook may be before or after it.
        if(!third_return_storage(c)||std::count_if(post_stm_sc_disable_private::words.begin(),
             post_stm_sc_disable_private::words.end(),[&](auto x){return x.pc==pc&&x.word==w;})!=1)
            post_stm_disable_refuse(2);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
    if(third_return_route){
        // The shared original restore helper is already observed by
        // v1270_before. Never reactivate a retired submission witness.
        if(!third_return_storage(c)||std::count_if(v1270::words.begin(),v1270::words.end(),
            [&](auto x){return x.pc==pc&&x.word==w;})!=1)third_return_refuse(1);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACK
    if(third_ack){
        if(std::count_if(deferred_ack_private::words.begin(),deferred_ack_private::words.end(),
            [&](auto x){return x.pc==pc&&x.word==w;})!=1)third_ack_refuse(1);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
    // Shared interrupt leaves retain both installed hooks. The active
    // dispatcher owns these original labels via v1261_before; do not
    // send them to the retired asynchronous submission witness.
    if(third_dispatch){
        if(std::count_if(v1261::words.begin(),v1261::words.end(),
            [&](auto x){return x.pc==pc&&x.word==w;})!=1)third_dispatch_refuse(1);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_OUTER_RESTORE
    if(stm_outer){if(!stm_outer->before(c,pc,w,stm_outer_held(c)))stm_outer_refuse(2);return;}
#endif
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
    if(async_return){if(!async_return->before(c,pc,w,async_held(c)))async_refuse(2);return;}
#endif
#ifdef UNDERCOVER_IPC_DISPATCH
    if(ioctl_dispatch){ipc_dispatch_before(c,pc,w);return;}
#endif
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
    if(ioctl_submit_queue){
        if(!ioctl_submit_queue->before(c,pc,w,ioctl_flush_held(c)))ioctl_submit_queue_refuse(2);
        return;
    }
#endif
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
    if(ioctl_submit_prefix){v1404_before(c,pc,w);return;}
#endif
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
    if(ioctl_alloc&&ioctl_alloc->stage()==1u){v1387_before(c,pc,w);return;}
#endif
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
    if(stm_ioctl){if(!stm_ioctl->before(c,pc,w,stm_ioctl_held(c)))stm_ioctl_refuse(2);return;}
#endif
#ifdef UNDERCOVER_V1359_SECOND_OPEN
    if(second_open_active){if(!second_open->before(c,pc,w,open_return_held(c),open_descriptor(c)))second_open_refuse(2);return;}
#endif
#ifdef UNDERCOVER_V1358_OPEN_RETURN
    if(open_return_active){
        if(!open_return->before(c,pc,w,open_return_held(c),open_descriptor(c)))open_return_refuse(4);
        return;
    }
#endif
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
    if(allocator_active){
        if(pc==v1344::release_expected.resume){
            if(!allocator_release->inline_return(c,pc,w,allocator_held(c))||
               !allocator_release->returned(c,allocator_held(c)))allocator_refuse(1);
#ifdef UNDERCOVER_V1378_SECOND_FREE
            if(second_scheduler_lane){
                if(!allocator_descriptor||!allocator_descriptor->second_returned(c,allocator_release->metadata_stores())){
                    std::cout<<"V1378_DESCRIPTOR_REFUSAL stage=2\n";allocator_refuse(4);
                }
                ++second_allocator_count;
#ifdef UNDERCOVER_V1379_SECOND_RETURN
                if(!open_return||!open_return->begin_inline(c,*allocator_release,open_return_held(c),open_descriptor(c),1u))open_return_refuse(3);
                std::cout<<"V1379_FREE_HANDOFF n="<<last_trial<<" native_free=1 heap_shadow=1 metadata_shadow=1 caller_abi=1 inline_return=1 stores="<<allocator_release->stores()<<" heap="<<allocator_release->heap_stores()<<'\n';
                allocator_active=false;open_return_active=true;
                if(!open_return->before(c,pc,w,open_return_held(c),open_descriptor(c)))open_return_refuse(4);
                return;
#else
                throw AllocatorReturned{};
#endif
            }
#endif
            ++allocator_count;
#ifdef UNDERCOVER_V1358_OPEN_RETURN
            if(!open_return||!open_return->begin_inline(c,*allocator_release,open_return_held(c),open_descriptor(c),0u))open_return_refuse(3);
            std::cout<<"V1358_ALLOCATOR_HANDOFF n="<<last_trial<<" verified=1\n";
            allocator_active=false;open_return_active=true;
            if(!open_return->before(c,pc,w,open_return_held(c),open_descriptor(c)))open_return_refuse(4);
            return;
#else
            throw AllocatorReturned{};
#endif
        }
        if(!allocator_release->before(c,pc,w,allocator_held(c)))allocator_refuse(2);
        return;
    }
#endif
    if(submit_resume_active&&!submit_resume->before(c,pc,w,submit_held(c)))submit_resume_refuse(1);
}
#endif
void v1328_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
    if(exit_active){if(!sleep_exit->before(c,pc,w,load_held(c)))sleep_exit_refuse(1);return;}
#endif
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
    if(sleep_active){
        if(!sleep_resume->before(c,pc,w,load_held(c)))sleep_resume_refuse(1);
        return;
    }
#endif
    if(!selection_route)return;
    if(!selection_witness->boundary(c,device_ok(c))||!selection_route->before(c,pc,w,device_ok(c)))selection_refuse(1);
}
#endif
// The isolated caller and prior SI transaction are seeded, not original
// execution. Exercise actual native SI W1C and the same shared guard used
// by V1235. The subsequent IPC client and all its dependencies are original.
#ifdef UNDERCOVER_V1315_COOP_SAVE
[[noreturn]]static void coop_save_refuse(unsigned kind){
    std::cout<<"V1315_SAVE_REFUSAL kind="<<kind<<" stage="<<coop_save->stage()
        <<" reason="<<coop_save->failure()<<" abi="<<coop_save->abi_failure()
        <<" visits="<<coop_save->visits()<<'\n';
    throw WitnessFailure{};
}
void v1314_save_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
    if(sleep_active)return; // v1328 owns the resumed save-return label
#endif
    need(coop_save&&sched_join);
    if(!coop_save->before(c,pc,w,device_ok(c)))coop_save_refuse(1);
}
#endif
static void seed_completed_si(nw::CPUContext& c,SiController& ctl,SecondCompletionAck& ack){
    constexpr uint32_t A=0x80010000u,Base=0xcd006400u;
    constexpr uint32_t Load=(32u<<26)|(4u<<21)|(3u<<16)|0x34u;
    constexpr uint32_t Store=(36u<<26)|(4u<<21)|(3u<<16)|0x34u;
    constexpr uint32_t Nop=0x60000000u,cfg=SiController::TC_MASK|0x00010300u;
    const std::array<uint8_t,3> response{9,0,0};
    for(unsigned n=0;n<3;++n){
        ctl.write(SiController::Control,cfg|SiController::TSTART);
        ctl.complete(ctl.pending()->token,response);
        if(n!=2)ctl.write(SiController::Control,cfg|SiController::TC_INT);
    }
    c.mmu.write32(A,Load);c.mmu.write32(A+4,Store);c.mmu.write32(A+8,Nop);
    c.msr=0x32u;c.gpr[3]=Base;c.is_running=true;c.dispatch_saved_ctx=0;c.inst_count=0;
    need(ack.arm(ctl,cause,mask,c.inst_count,3,true));
    ++c.inst_count;need(ack.before(c,A,Load,true));
    uint32_t value=0;need(ack.read(ctl,SiController::Control,value));
    c.gpr[4]=value|SiController::TC_INT;++c.inst_count;
    need(ack.before(c,A+4,Store,true)&&ack.write(ctl,SiController::Control,c.gpr[4]));
    ++c.inst_count;need(ack.before(c,A+8,Nop,true)&&ack.resume_after_ack(c,A+8,Nop));
    need(ack.postack_held()&&device_ok(c)&&!(cause.load()&SiController::PI_SI));
}
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
static bool vector_held(nw::CPUContext& c){
    auto s=B::cold_snapshot();
    return vector_active&&s&&same_scheduler_ipc_snapshot(*s,vector_mail)&&device_ok(c);
}
static void vector_refuse(unsigned kind){
    std::cout<<"V1260_VECTOR_REFUSAL kind="<<kind<<" stage="<<ipc_vector.stage()
        <<" reason="<<ipc_vector.failure()<<" gpr="<<ipc_vector.gpr_mask()
        <<" special="<<ipc_vector.special_mask()<<'\n';
    throw WitnessFailure{};
}
void v1260_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_STM_DEFERRED_VECTOR
    if(third_vector){if(!third_vector->before(c,pc,w,cause.load(),mask.load(),third_irq_held(c)))third_vector_refuse(1);return;}
#endif
    if(!ipc_vector.before(c,pc,w,cause.load(),mask.load(),vector_held(c)))vector_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
static void dispatch_refuse(unsigned kind){
    std::cout<<"V1261_DISPATCH_REFUSAL kind="<<kind<<" stage="<<ipc_dispatch->stage()
        <<" reason="<<ipc_dispatch->failure()<<" reads="<<ipc_dispatch->cause_reads()+ipc_dispatch->mask_reads()
        <<" detail="<<ipc_dispatch->detail()<<" visits="<<ipc_dispatch->visits()<<'\n';
    throw WitnessFailure{};
}
void v1261_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
    if(third_dispatch){
        auto s=B::cold_snapshot();
        const bool guard=std::find(v1261::guard.begin(),v1261::guard.end(),pc)!=v1261::guard.end();
        if(!s||!third_dispatch->before(c,pc,w,guard,*s,third_irq_held(c)))third_dispatch_refuse(1);
        return;
    }
#endif
    if(!ipc_dispatch)return; // shared interrupt helpers run earlier
    auto s=B::cold_snapshot();
    const bool guard=std::find(v1261::guard.begin(),v1261::guard.end(),pc)!=v1261::guard.end();
    if(!s||!ipc_dispatch->before(c,pc,w,guard,*s,device_ok(c)))dispatch_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1292_NESTED_WAKE
[[noreturn]]static void nested_refuse(unsigned kind){
    std::cout<<"V1292_NESTED_REFUSAL kind="<<kind<<" stage="<<nested_wake->stage()
             <<" reason="<<nested_wake->failure()<<" visits="<<nested_wake->visits()<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1289_WAKE_READY
[[noreturn]]static void wake_refuse(unsigned kind){
    std::cout<<"V1289_WAKE_REFUSAL kind="<<kind<<" stage="<<wake_ready->stage()
             <<" reason="<<wake_ready->failure()<<" visits="<<wake_ready->visits()<<'\n';
    throw WitnessFailure{};
}
void v1289_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_V1292_NESTED_WAKE
    if(nested_wake){if(!nested_wake->before(c,pc,w,device_ok(c)))nested_refuse(1);return;}
#endif
    if(wake_ready&&!wake_ready->before(c,pc,w,device_ok(c)))wake_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
[[noreturn]]static void body_refuse(unsigned kind){
    std::cout<<"V1282_BODY_REFUSAL kind="<<kind<<" stage="<<reply_body->stage()
        <<" reason="<<reply_body->failure()<<" gate="<<reply_body->gate_failure()
        <<" visits="<<reply_body->visits()<<" reads="<<reply_body->arm_reads()
        <<" invalidations="<<reply_body->invalidations()<<'\n';
    std::cout<<"V1294_MMIO_REFUSAL reason="<<reply_body->mmio_reason()<<" owner="<<reply_body->mmio_owner()
             <<" form="<<reply_body->mmio_form()<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_V1300_REPLY_RETURN
[[noreturn]]static void return_refuse(unsigned kind){
    std::cout<<"V1300_RETURN_REFUSAL kind="<<kind<<" stage="<<reply_return->stage()
             <<" reason="<<reply_return->failure()<<" gate="<<reply_return->gate_failure()
             <<" visits="<<reply_return->visits()<<'\n';
    if(reply_return->failure()==3u)std::cout<<"V1318_RETURN_INSTRUCTION detail="<<reply_return->instruction_detail()
        <<" boundary="<<reply_return->instruction_boundary()<<" owner="<<reply_return->instruction_owner()
        <<" ticks="<<reply_return->instruction_ticks()<<'\n';
    if(reply_return->failure()==4u)std::cout<<"V1313_RETURN_CONTROL detail="<<reply_return->control_detail()
        <<" target="<<reply_return->control_target()<<" owner="<<reply_return->control_owner()
        <<" x2="<<reply_return->x2_writes()<<'\n';
    if(kind==5u)std::cout<<"V1302_RETURN_MMIO detail="<<reply_return->write_detail()
        <<" reg="<<reply_return->write_register()<<" ctrl="<<reply_return->write_control_bits()
        <<" value_class="<<reply_return->write_value_class()<<'\n';
    throw WitnessFailure{};
}
#endif
void v1316_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_V1316_REPLY_HELPER
    need(reply_return);
    if(!reply_return->before(c,pc,w,device_ok(c)))return_refuse(1);
#else
    (void)c;(void)pc;(void)w;throw WitnessFailure{};
#endif
}
void v1281_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_V1300_REPLY_RETURN
    if(reply_return){if(!reply_return->before(c,pc,w,device_ok(c)))return_refuse(1);return;}
#endif
    if(reply_body&&!reply_body->before(c,pc,w,device_ok(c)))body_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
[[noreturn]]static void reply_entry_refuse(unsigned kind){
    std::cout<<"V1275_REPLY_REFUSAL kind="<<kind<<" stage="<<reply_entry->stage()
        <<" reason="<<reply_entry->failure()<<" reads="<<reply_entry->reads()
        <<" visits="<<reply_entry->visits()<<'\n';
    throw WitnessFailure{};
}
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
static void joined_refuse(unsigned kind){
    std::cout<<"V1266_ACK_REFUSAL kind="<<kind<<" stage="<<joined_ack->stage()<<" reason="<<joined_ack->failure()
        <<" gate="<<joined_ack->gate_stage()<<" gate_reason="<<joined_ack->gate_failure()<<" visits="<<joined_ack->visits()<<'\n';
    throw WitnessFailure{};
}
void v1266_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_STM_DEFERRED_ACK
    if(third_ack){if(!third_ack->before(c,pc,w,third_ack_held(c)))third_ack_refuse(2);return;}
#endif
#ifdef UNDERCOVER_V1300_REPLY_RETURN
    if(reply_return){
        const auto i=std::find_if(v1299::words.begin(),v1299::words.end(),[&](auto x){return x.pc==pc;});
        if(i==v1299::words.end())return_refuse(1);
        // IPC leaves and processor entry have already been observed by v1281.
        if(i->owner==v1255::handler&&!reply_return->before(c,pc,w,device_ok(c)))return_refuse(1);
        return;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){
        const bool guard=pc==0x805190c0u||pc==0x8052a51cu||pc==v1255::returned;
        if(!reply_entry->before(c,pc,w,guard,device_ok(c)))reply_entry_refuse(1);
        return;
    }
#endif
    if(!joined_ack)return; // shared original leaves used earlier
    const bool guard=pc==0x805190c0u||pc==0x8052a51cu||pc==v1255::returned;
    if(!joined_ack->before(c,pc,w,guard,device_ok(c)))joined_refuse(1);
}
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
static bool reply_held(nw::CPUContext& c){
    const auto s=B::cold_snapshot();
    using Q=PostAckSchedulerJoin;
    const unsigned fd=
#ifdef UNDERCOVER_V1370_SECOND_REPLY
        second_scheduler_lane?OpenTransactionEpoch(second_irq_kind).result_fd():
#endif
        0u;
    return epilogue_host&&s&&same_scheduler_ipc_snapshot(*s,reply_mail)&&device_ok(c)&&
        c.is_running&&!c.in_callback&&!c.dispatch_saved_ctx&&
        c.mmu.read32(Q::Active)==Q::Idle&&c.mmu.read32(Q::Physical)==(Q::Idle&0x3fffffffu)&&
        c.mmu.read16(Q::Thread+712u)==4u&&c.mmu.read32(Q::Thread+732u)==reply_queue&&
        c.mmu.read32(reply_queue)==Q::Thread&&c.mmu.read32(reply_queue+4u)==Q::Thread&&
        epilogue_host->physical_ram().read32(reply_request)==StmIos::Reply&&
        epilogue_host->physical_ram().read32(reply_request+4u)==fd&&
        epilogue_host->physical_ram().read32(reply_request+8u)==StmIos::Open;
}
[[noreturn]]static void epilogue_refuse(unsigned kind){
    std::cout<<"V1271_EPILOGUE_REFUSAL kind="<<kind<<" stage="<<epilogue->stage()<<" reason="<<epilogue->failure()
        <<" entry="<<epilogue->entry_refusal()<<" visits="<<epilogue->visits()<<" select="<<epilogue->select_state()<<'\n';
    throw WitnessFailure{};
}
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
[[noreturn]]static void idle_return_refuse(unsigned kind){
    std::cout<<"V1305_IDLE_REFUSAL kind="<<kind<<" stage="<<idle_epilogue->stage()
        <<" reason="<<idle_epilogue->failure()<<" entry="<<idle_epilogue->entry_refusal()
        <<" join="<<ready_idle->failure()<<" visits="<<idle_epilogue->visits()
        <<" select="<<idle_epilogue->select_state()<<'\n';
    throw WitnessFailure{};
}
#endif
void v1270_before(nw::CPUContext& c,uint32_t pc,uint32_t w){
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
    if(post_stm_restore){
        if(!post_stm_restore->before(c,pc,w,post_stm_restore_held(c)))post_stm_restore_refuse(2);
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
    if(post_stm_disable){
        if(!post_stm_disable->before(c,pc,w,post_stm_disable_held(c)))post_stm_disable_refuse(2);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_RESUMED_RESTORE
    if(third_resume){
        const bool first=third_resume->visits()==0u;
        if(!third_resume_held(c)||(first&&!third_return_route->resume(c,pc,w,cause.load(),mask.load()))||
           !third_resume->before(c,pc,w,third_resume_held(c),first))third_resume_refuse(2);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
    if(third_return_route){
        if(!third_return_join->held(c,third_return_storage(c)))third_return_refuse(1);
        if(!third_return_route->stage()&&(pc!=v1255::returned||c.pc!=pc||
           c.inst_count-third_return_tick!=2u||
           !third_return_route->begin_cleared_select(c,*third_frame_ptr,cause.load(),mask.load())))third_return_refuse(2);
        if(!third_return_route->before(c,pc,w,cause.load(),mask.load()))third_return_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
    if(stm_ioctl){v1344_before(c,pc,w);return;}
#endif
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
    if(allocator_active){v1344_before(c,pc,w);return;}
#endif
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
    if(submit_resume_active){v1344_before(c,pc,w);return;}
#endif
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
    if(exit_active){if(!sleep_exit->before(c,pc,w,load_held(c)))sleep_exit_refuse(2);return;}
#endif
#ifdef UNDERCOVER_V1334_COOP_LOAD
    if(load_active){
        if(!coop_load->before(c,pc,w,load_held(c)))load_refuse(1);
        return;
    }
#endif
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
    if(ready_idle){
        if(!ready_idle->boundary(c,device_ok(c)))idle_return_refuse(1);
        if(!idle_epilogue->stage()&&(pc!=v1255::returned||c.pc!=pc||c.inst_count-idle_tick!=2u||
           !idle_epilogue->begin_cleared_select(c,irq_capture,cause.load(),mask.load())))idle_return_refuse(2);
        if(!idle_epilogue->before(c,pc,w,cause.load(),mask.load()))idle_return_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_V1292_NESTED_WAKE
    if(nested_wake){if(!nested_wake->before(c,pc,w,device_ok(c)))nested_refuse(1);return;}
#endif
    if(!epilogue)return; // shared IRQ leaves during earlier native execution
    if(!reply_held(c))epilogue_refuse(1);
    if(!epilogue->stage()){
        if(pc!=v1255::returned||c.pc!=pc||!epilogue->begin_pending(c,irq_capture,cause.load(),mask.load()))
            epilogue_refuse(2);
    }
    if(!epilogue->before(c,pc,w,cause.load(),mask.load()))epilogue_refuse(3);
}
#endif
static void submit_trace(uint32_t pc,nw::CPUContext& c){
    need(submit_join);
    const bool ok=submit_join->observe(c,pc,device_ok(c));
    last_stage=submit_join->stage();last_reason=submit_join->failure();
    if(!ok)throw WitnessFailure{};
    submit_stage=submit_join->stage();
    if(pc==OpenScRoute::Vector)++submit_vectors;
    if(submit_stage==8u){
        if(!submit_join->acknowledge(c,device_ok(c))){
            last_reason=submit_join->failure();throw WitnessFailure{};
        }
        need(submit_join->ack_at(c,device_ok(c)));
        ++submit_acks;submit_stage=9u;throw SubmitStop{};
    }
}
namespace nwii::runtime {
bool g_trace_calls=true;uint32_t g_watch_addr=0;
void trace_call(uint32_t pc,CPUContext& c){
    need(witness);
#ifdef UNDERCOVER_FORMATTER_NESTED
    if(formatter_nested){
        const bool held=formatter_nested_held(c);
#ifdef UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
        if(formatter_nested->stage()==28u){
            if(!formatter_nested->caller_next_entry_trace(c,pc,held))formatter_nested_refuse(3);
            return;
        }
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_ARRIVAL
        if(formatter_nested->stage()==7u){
            if(!formatter_nested->caller_arrival_entry(c,pc,held))formatter_nested_refuse(3);
            return;
        }
#endif
#ifdef UNDERCOVER_FORMATTER_ARRIVAL
        if(formatter_nested->stage()==3u){
            if(!formatter_nested->control_destination_entry(c,pc,held))formatter_nested_refuse(3);
#ifdef UNDERCOVER_FORMATTER_POST_CTR
            if(!formatter_nested->resume_control_path(c,formatter_post_ctr_private::expected,held))formatter_nested_refuse(3);
#endif
            return;
        }
#endif
        if(!formatter_nested->entry(c,pc,held))formatter_nested_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_FORMATTER_CONTINUATION
    if(formatter_continuation){
        if(!formatter_continuation->entry(c,pc,formatter_continuation_held(c)))formatter_continuation_refuse(3);
        if(formatter_continuation->stage()==2u){++formatter_continuation_count;throw FormatterContinuationStop{};}
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER_LEAF
    if(post_stm_formatter_leaf){
        if(!post_stm_formatter_leaf->entry(c,pc,post_stm_formatter_leaf_held(c)))post_stm_formatter_leaf_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
    if(post_stm_formatter){
        if(!post_stm_formatter->entry(c,pc,post_stm_formatter_held(c)))post_stm_formatter_refuse(3);
        if(post_stm_formatter->stage()==2u){++post_stm_formatter_count;throw PostStmFormatterStop{};}
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
    if(post_stm_resume){
        if(!post_stm_resume->entry(c,pc,post_stm_resume_held(c)))post_stm_resume_refuse(3);
        if(post_stm_resume->stage()==2u){++post_stm_resume_count;throw PostStmResumeStop{};}
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
    if(post_stm_dependency){
        if(!post_stm_dependency->entry(c,pc,post_stm_dependency_held(c)))post_stm_dependency_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
    if(post_stm_helper){
        if(!post_stm_helper->entry(c,pc,post_stm_helper_held(c)))post_stm_helper_refuse(3);
        if(post_stm_helper->stage()==2u){++post_stm_helper_count;throw PostStmHelperStop{};}
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT
    if(post_stm_report){
        if(!post_stm_report->entry(c,pc,post_stm_report_held(c)))post_stm_report_refuse(3);
        if(post_stm_report->stage()==2u){++post_stm_report_count;throw PostStmReportStop{};}
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_VERSION
    if(post_stm_version){
        if(!post_stm_version->entry(c,pc,post_stm_version_held(c)))post_stm_version_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
    if(post_stm_restore){
        if(!post_stm_restore->entry(c,pc,post_stm_restore_held(c)))post_stm_restore_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_DECISION
    if(post_stm_decision){
        if(!post_stm_decision->entry(c,pc,post_stm_decision_held(c)))post_stm_decision_refuse(3);
        if(post_stm_decision->stage()==2u){++post_stm_decision_count;throw PostStmDecisionStop{};}
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
    if(post_stm_disable){
        if(!post_stm_disable->entry(c,pc,post_stm_disable_held(c)))post_stm_disable_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
    if(post_stm_sc){
        if(!post_stm_sc->entry(c,pc,post_stm_sc_held(c)))post_stm_sc_refuse(3);
        if(post_stm_sc->stage()==2u){++post_stm_sc_count;throw PostStmScStop{};}
        return;
    }
#endif
#ifdef UNDERCOVER_STM_FINAL_RETURN
    if(stm_final){if(!stm_final->entry(c,pc,stm_final_held(c)))stm_final_refuse(3);return;}
#endif
#ifdef UNDERCOVER_STM_RESUMED_RESTORE
    if(third_resume){
        if(!third_resume->entry(c,pc,third_resume_held(c)))third_resume_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
    if(third_return_route){
        if(!third_return_join->held(c,third_return_storage(c))||
           !third_return_route->entry(c,pc,cause.load(),mask.load()))third_return_refuse(4);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACK
    if(third_ack){if(!third_ack->entry(c,pc,third_ack_held(c)))third_ack_refuse(3);return;}
#endif
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
    if(third_dispatch){
        auto s=B::cold_snapshot();
        if(!s)third_dispatch_refuse(2);
        if(!third_dispatch->stage()){
            if(!third_dispatch->begin_deferred(c,*third_frame_ptr,*s,third_wait,third_request,*ioctl_event_gate,third_irq_held(c)))
                third_dispatch_refuse(2);
        }else{
            if(!third_dispatch->observe(c,pc,*s,third_irq_held(c)))third_dispatch_refuse(3);
            if(third_dispatch->stage()==6u){++third_dispatch_count;throw DispatchStop{};}
        }
        return;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_VECTOR
    if(third_vector){
        if(!third_vector->stage()){
            if(pc!=ExternalVector||c.inst_count-third_vector_tick!=1u||
               !third_vector->begin_captured(c,*third_frame_ptr,cause.load(),mask.load(),third_irq_held(c)))third_vector_refuse(2);
        }else{
            if(!third_vector->entry(c,pc,cause.load(),mask.load(),third_irq_held(c)))third_vector_refuse(3);
            if(third_vector->stage()==3u){++third_vector_count;throw VectorStop{};}
        }
        return;
    }
#endif
#ifdef UNDERCOVER_STM_OUTER_RESTORE
    if(stm_outer)stm_outer_refuse(3);
#endif
#ifdef UNDERCOVER_STM_EVENT_RETURN
    if(stm_event_return){
        if(!stm_event_return->entry(c,pc,async_held(c)))stm_event_refuse(3);
        ++stm_event_return_count;
#ifdef UNDERCOVER_STM_OUTER_RESTORE
        if(!stm_event_return->reached(c,async_held(c)))stm_outer_refuse(1);
        stm_outer=std::make_unique<StmOuterRestoreWitness>(stm_outer_private::expected);
        if(!stm_outer->begin(c,stm_outer_held(c)))stm_outer_refuse(1);
        return;
#else
        throw StmIoctlReached{};
#endif
    }
#endif
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
    if(async_wrapper){if(!async_wrapper->entry(c,pc,async_held(c)))async_wrapper_refuse(3);return;}
#endif
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
    if(async_return){if(!async_return->entry(c,pc,async_held(c)))async_refuse(3);return;}
#endif
#ifdef UNDERCOVER_IPC_DISPATCH
    if(ioctl_dispatch){
        if(!ioctl_dispatch->entry(c,pc,ioctl_dispatch_held(c)))ioctl_dispatch_refuse(4);
        return;
    }
#endif
#ifdef UNDERCOVER_IPC_PROFILE
    if(ioctl_profile)ioctl_profile_refuse(3);
#endif
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
    if(ioctl_submit_queue){
        if(!ioctl_submit_queue->entry(c,pc,ioctl_flush_held(c)))ioctl_submit_queue_refuse(3);
        if(ioctl_submit_queue->stage()==2u){
            ++ioctl_queue_entry_count;
#ifdef UNDERCOVER_IPC_PROFILE
            if(!ioctl_submit_queue->reached(c,ioctl_flush_held(c))||ioctl_submit_queue->ring_stores()!=3u||
               ioctl_profile||!ioctl_build||!ioctl_submit_prefix)ioctl_profile_refuse(1);
            const uint32_t req=ioctl_build->request(),sp=c.gpr[1],caller_sp=ioctl_submit_prefix->caller_sp();
            if(caller_sp<=sp||caller_sp-sp>512u)ioctl_profile_refuse(1);
            ioctl_profile=std::make_unique<IpcProfileExecutionWitness>(ipc_profile::expected);
            if(!ioctl_profile->begin(c,ioctl_flush_held(c),{req,ioctl_build->allocated_size()},
                {sp,caller_sp-sp+8u},v1410::expected.ring,c.mmu.read32(req+8u)))ioctl_profile_refuse(1);
#else
            throw StmIoctlReached{};
#endif
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
    #ifdef UNDERCOVER_V1398_IOCTL_FLUSH
    if(ioctl_flush){
        if(!ioctl_flush->trace(c,pc,pc==OpenScRoute::Vector||ioctl_flush_held(c)))ioctl_flush_refuse(2);
        if(ioctl_flush->stage()==4u){
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
            if(!ioctl_flush->returned(c,ioctl_flush_held(c)))ioctl_flush_refuse(2);
#ifdef UNDERCOVER_V1407_IOCTL_HEADER
            if(ioctl_submit_prefix){
                if(pc!=OpenScRoute::SubmitCaller||!ioctl_flush->lines())ioctl_flush_refuse(2);
                ++ioctl_header_return_count;
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
                ioctl_header_lines=ioctl_flush->lines();
                ioctl_submit_queue=std::make_unique<IoctlSubmitQueueWitness>(v1410::expected);
                if(!ioctl_submit_queue->begin(c,ioctl_flush_held(c),ioctl_build->request(),
                        ioctl_build->allocated_size(),ioctl_submit_prefix->caller_sp()))ioctl_submit_queue_refuse(1);
                ioctl_flush.reset();return;
#else
                throw StmIoctlReached{};
#endif
            }
#endif
            if(!ioctl_tail){
                if(ioctl_build->flush_kind()!=1u)ioctl_tail_refuse(1);
                ++ioctl_flush_count;ioctl_input_lines=ioctl_flush->lines();
                ioctl_tail=std::make_unique<IoctlFlushTailWitness>(v1401::expected);
                if(!ioctl_tail->begin(c,ioctl_flush_held(c),ioctl_build->request(),ioctl_build->output(),ioctl_build->output_size()))ioctl_tail_refuse(1);
            }else{
                ++ioctl_output_count;ioctl_output_lines=ioctl_flush->lines();
                if(!ioctl_tail->output_return(c,ioctl_flush_held(c)))ioctl_tail_refuse(3);
            }
            ioctl_flush.reset();
#else
            ++ioctl_flush_count;throw StmIoctlReached{};
#endif
        }
        return;
    }
    #endif
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
    if(ioctl_submit_prefix){
        if(!ioctl_submit_prefix->entry(c,pc,ioctl_submit_prefix_held(c)))ioctl_submit_prefix_refuse(3);
        if(ioctl_submit_prefix->stage()==2u){
            ++ioctl_header_entry_count;
            if(ioctl_submit_prefix->queue_path()==1u)++ioctl_queue_init_count;
            else if(ioctl_submit_prefix->queue_path()==2u)++ioctl_queue_skip_count;
            else ioctl_submit_prefix_refuse(3);
#ifdef UNDERCOVER_V1407_IOCTL_HEADER
            if(!ioctl_submit_prefix->reached(c,ioctl_submit_prefix_held(c)))ioctl_submit_prefix_refuse(3);
            // V1344 privately audits the complete submit body, including
            // the already installed V651 return trace. Reuse its exact word.
            auto expected=v1398::expected;
            unsigned hits=0;
            for(const auto& row:v1344::words)
                if(row.owner==v1404::expected.submit.pc&&row.pc==OpenScRoute::SubmitCaller){
                    expected.submit_resume_word=row.word;++hits;
                }
            if(hits!=1u||v1404::expected.flush.lr!=OpenScRoute::SubmitCaller)ioctl_flush_refuse(1);
            ioctl_header_shadow.clear();
            for(unsigned i=0;i<ioctl_build->allocated_size();++i)
                ioctl_header_shadow.push_back(c.mmu.read8(ioctl_build->request()+i));
            ioctl_flush=std::make_unique<IoctlFirstFlushWitness>(expected,v626::vector,second_irq_kind,3u);
            if(!ioctl_flush->begin(c,ioctl_flush_held(c)))ioctl_flush_refuse(1);
#else
            throw StmIoctlReached{};
#endif
        }
        return;
    }
#endif
    if(ioctl_tail){
        if(!ioctl_tail->entry(c,pc,ioctl_flush_held(c)))ioctl_tail_refuse(4);
        if(ioctl_tail->stage()==2u){
            ioctl_flush=std::make_unique<IoctlFirstFlushWitness>(v1398::expected,v626::vector,second_irq_kind,2u);
            if(!ioctl_flush->begin(c,ioctl_flush_held(c)))ioctl_flush_refuse(1);
            return;
        }
        if(ioctl_tail->stage()==4u){
            ++ioctl_submit_count;
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
            if(!ioctl_tail->reached(c,ioctl_flush_held(c)))ioctl_tail_refuse(4);
            ioctl_submit_prefix=std::make_unique<IoctlSubmitPrefixWitness>(v1404::expected);
            if(!ioctl_submit_prefix->begin(c,ioctl_flush_held(c),ioctl_build->request(),ioctl_build->allocated_size(),ioctl_build->callback()))ioctl_submit_prefix_refuse(1);
            return;
#else
            throw StmIoctlReached{};
#endif
        }
        ioctl_tail_refuse(4);
    }
#endif
    if(ioctl_build&&ioctl_build->stage()==2u){
        if(!ioctl_build->entry(c,pc,ioctl_alloc_held(c)))ioctl_build_refuse(3);
        ++ioctl_build_count;
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
        ioctl_flush=std::make_unique<IoctlFirstFlushWitness>(v1398::expected,v626::vector,second_irq_kind,ioctl_build->flush_kind());
        if(!ioctl_build->reached(c,ioctl_alloc_held(c))||!ioctl_flush->begin(c,ioctl_flush_held(c)))ioctl_flush_refuse(1);
        return;
#else
        throw StmIoctlReached{};
#endif
    }
#endif
    if(ioctl_alloc&&ioctl_alloc->stage()==1u){
        if(!ioctl_alloc->entry(c,pc,ioctl_alloc_held(c)))ioctl_alloc_refuse(3);
        return;
    }
#endif
    if(ioctl_prefix&&ioctl_prefix->stage()==1u){
        if(!ioctl_prefix->entry(c,pc,stm_ioctl_held(c)))ioctl_prefix_refuse(3);
        if(ioctl_prefix->stage()==2u){
            ++ioctl_prefix_count;
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
            if(!ioctl_prefix->reached(c,stm_ioctl_held(c))||
               !allocator_descriptor->third_allocation_admitted(c,allocator_heap,c.gpr[3])||
               !ioctl_alloc->begin(c,ioctl_alloc_held(c),allocator_heap,allocator_descriptor->field(),allocator_descriptor->guard()))
                ioctl_alloc_refuse(1);
#else
            throw StmIoctlReached{};
#endif
        }
        return;
    }
#endif
    if(stm_ioctl){
        if(!stm_ioctl->entry(c,pc,stm_ioctl_held(c)))stm_ioctl_refuse(3);
        if(stm_ioctl->stage()==2u){
            ++stm_ioctl_count;
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
            if(!ioctl_build->capture(c,stm_ioctl_held(c),second_irq_kind))ioctl_build_refuse(1);
#endif
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
            if(!ioctl_prefix||!stm_ioctl->reached(c,stm_ioctl_held(c))||
               !ioctl_prefix->begin(c,stm_ioctl_held(c)))ioctl_prefix_refuse(1);
#else
            throw StmIoctlReached{};
#endif
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1359_SECOND_OPEN
    if(second_open_active){
        if(!second_open->entry(c,pc,open_return_held(c),open_descriptor(c)))second_open_refuse(3);
        ++second_open_count;
#ifdef UNDERCOVER_V1379_SECOND_RETURN
        if(!second_open_capture||!second_open_capture->capture_open(c,open_return_held(c)))open_return_refuse(1);
#endif
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
        if(!second_request||!second_request->begin_second(c,*second_open,second_request_held(c),
                open_return_held(c),open_descriptor(c),allocator_heap.size))second_request_refuse(1);
        std::cout<<"V1364_REQUEST_HANDOFF n="<<last_trial<<" first_release=1 second_entry=1 cache_rearmed=1\n";
        second_open_active=false;second_request_active=true;return;
#else
        throw SecondOpenReached{};
#endif
    }
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
    if(second_submit_active){
        if(!second_submit->observe(c,pc,second_submit_held(c)))second_submit_refuse(2);
        if(pc==OpenScRoute::Vector)++second_submit_vectors;
        if(second_submit->stage()==8u){
            if(!second_submit->acknowledge(c,second_submit_held(c))||
               !second_submit->ack_at(c,second_submit_held(c)))second_submit_refuse(3);
            ++second_submit_count;throw SecondSubmitAcked{};
        }
        return;
    }
#endif
    if(second_request_active){
        if(pc==OpenScRoute::Vector){
            if(!second_request->vector_trace(c,pc,second_request_held(c)))second_request_refuse(2);
            ++second_request_vectors;return;
        }
        if(!second_request->observe(c,pc,second_request_held(c)))second_request_refuse(3);
        if(second_request->stage()==9u){
            if(!second_request->submit_at(c,second_request_held(c))||
               !allocator_descriptor->identity_after_release(c))second_request_refuse(4);
            ++second_request_count;
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
            std::cout<<"V1364_REQUEST_TRIAL n="<<last_trial<<" request=1 opposite_path=1 native_rfi=1 first_fd_held=1 reused="<<(second_request->request()==allocator_request)<<"\n";
#ifdef UNDERCOVER_V1378_SECOND_FREE
            if(!second_resume_capture||!second_resume_capture->capture(c,second_request_held(c)))submit_resume_refuse(6);
#ifdef UNDERCOVER_V1379_SECOND_RETURN
            if(!second_open_capture||!second_open_capture->capture_submit(c,second_request_held(c)))open_return_refuse(2);
#endif
#endif
            if(!second_submit||!second_submit->begin(c,*second_request,second_request_held(c))||
               !second_submit->observe(c,pc,second_submit_held(c)))second_submit_refuse(1);
            second_request_active=false;second_submit_active=true;return;
#else
            throw SecondRequestReached{};
#endif
        }
        return;
    }
#endif
#endif
#ifdef UNDERCOVER_V1358_OPEN_RETURN
    if(open_return_active)open_return_refuse(5);
#endif
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
    if(allocator_active){
        if(!allocator_release->entry(c,pc,allocator_held(c)))allocator_refuse(3);
        return;
    }
#endif
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
    if(submit_resume_active){
        if(!submit_resume->entry(c,pc,submit_held(c)))submit_resume_refuse(2);
        if(submit_resume->stage()==3u){
            if(!submit_resume->release_at(c,submit_held(c)))submit_resume_refuse(2);
#ifdef UNDERCOVER_V1378_SECOND_FREE
            if(second_scheduler_lane)++second_release_count;else
#endif
            ++release_count;
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
            AllocatorRange meta{},guard{};
#ifdef UNDERCOVER_V1356_ALLOCATOR_METADATA
            if(!allocator_descriptor||
#ifdef UNDERCOVER_V1378_SECOND_FREE
               (second_scheduler_lane?!allocator_descriptor->second_release_entry(c,allocator_heap,c.gpr[3]):
#endif
               !allocator_descriptor->release_entry(c,allocator_heap,c.gpr[3])
#ifdef UNDERCOVER_V1378_SECOND_FREE
               )
#endif
               ){
                std::cout<<"V1356_DESCRIPTOR_REFUSAL stage=3\n";allocator_refuse(4);
            }
            meta=allocator_descriptor->field();guard=allocator_descriptor->guard();
#endif
            if(!allocator_release->begin(c,*submit_resume,submit_held(c),allocator_heap,allocator_request,meta,guard))allocator_refuse(4);
            submit_resume_active=false;allocator_active=true;return;
#else
            throw ReleaseReached{};
#endif
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
    if(exit_active)sleep_exit_refuse(3);
#endif
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
    if(sleep_active){
        if(!sleep_resume->entry(c,pc,load_held(c))||!sleep_resume->restored_sleep_at(c,load_held(c)))sleep_resume_refuse(2);
        
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)++second_resumed_sleep_count;else
#endif
            ++resumed_sleep_count;
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
        if(!sleep_exit->begin(c,*sleep_resume,load_held(c)))sleep_exit_refuse(4);
        sleep_active=false;exit_active=true;return;
#else
        throw SleepRestoreReached{};
#endif
    }
#endif
#ifdef UNDERCOVER_V1334_COOP_LOAD
    if(load_active)load_refuse(2);
#endif
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
    if(selection_route){
        if(!selection_route->entry(c,pc,device_ok(c))||!selection_witness->entry(c,pc,device_ok(c)))selection_refuse(2);
        if(selection_route->stage()==2u){
            if(!selection_route->loader_at(c,device_ok(c))||!selection_witness->loader_ready(c,device_ok(c)))selection_refuse(3);
            
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)++second_selection_count;else
#endif
            ++selection_count;
#ifdef UNDERCOVER_V1334_COOP_LOAD
            if(!coop_load->begin(c,*load_save,load_held(c)))load_refuse(3);
            selection_route=nullptr;load_active=true;return;
#else
            throw LoaderReached{};
#endif
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
    if(ready_idle){
        if(!ready_idle->boundary(c,device_ok(c))||!idle_epilogue->entry(c,pc,cause.load(),mask.load()))idle_return_refuse(4);
        return;
    }
#endif
#ifdef UNDERCOVER_V1300_REPLY_RETURN
    if(reply_return){if(!reply_return->entry(c,pc,device_ok(c)))return_refuse(2);return;}
#endif
#ifdef UNDERCOVER_V1292_NESTED_WAKE
    if(nested_wake){if(!nested_wake->entry(c,pc,device_ok(c)))nested_refuse(2);return;}
#endif
#ifdef UNDERCOVER_V1289_WAKE_READY
    if(wake_ready){
        if(!wake_ready->entry(c,pc,device_ok(c)))wake_refuse(2);
        if(wake_ready->stage()==2u){
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)++second_ready_count;else
#endif
            ++ready_count;throw ReadyReached{};}
        return;
    }
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    if(reply_body){
        if(!reply_body->entry(c,pc,device_ok(c)))body_refuse(2);
        if(reply_body->stage()==2u){
#ifdef UNDERCOVER_V1370_SECOND_REPLY
            if(second_scheduler_lane)++second_wake_entry_count;else
#endif
            ++wake_entry_count;throw WakeEntryReached{};}
        return;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){
        if(!reply_entry->entry(c,pc,device_ok(c)))reply_entry_refuse(2);
        if(reply_entry->stage()==2u){
#ifdef UNDERCOVER_V1370_SECOND_REPLY
            if(second_scheduler_lane)++second_reply_entry2_count;else
#endif
            ++reply_entry_count;throw ReplyProcessorReached{};}
        return;
    }
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
    if(epilogue){
        if(!reply_held(c)||!epilogue->entry(c,pc,cause.load(),mask.load()))epilogue_refuse(4);
        return;
    }
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
    if(joined_ack){
        if(!joined_ack->entry(c,pc,device_ok(c)))joined_refuse(2);
        return;
    }
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    if(ipc_dispatch){
        auto s=B::cold_snapshot();need(s.has_value());
        if(!ipc_dispatch->stage()){
            const bool begun=
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
                second_dispatch?ipc_dispatch->begin_reply(c,irq_capture,*s,dispatch_queue,reply_request,device_ok(c)):
#endif
                ipc_dispatch->begin(c,irq_capture,*s,dispatch_queue,device_ok(c));
            if(!begun)dispatch_refuse(2);
        }else{
            if(!ipc_dispatch->observe(c,pc,*s,device_ok(c)))dispatch_refuse(3);
            if(ipc_dispatch->stage()==6u){
#ifdef UNDERCOVER_V1370_SECOND_REPLY
                if(second_scheduler_lane){if(second_dispatch)++second_reply_dispatch2_count;else ++second_ack_dispatch_count;}else
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
                if(second_dispatch)++second_dispatch_count;else
#endif
                ++dispatch_count;
                throw DispatchStop{};
            }
        }
        return;
    }
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
    if(vector_active){
        if(!ipc_vector.stage()){
            if(pc!=ExternalVector||c.inst_count-vector_tick!=1u||
               !ipc_vector.begin_captured(c,irq_capture,cause.load(),mask.load(),vector_held(c)))vector_refuse(2);
        }else{
            if(!ipc_vector.entry(c,pc,cause.load(),mask.load(),vector_held(c)))vector_refuse(3);
            if(ipc_vector.stage()==3u){
#ifdef UNDERCOVER_V1370_SECOND_REPLY
                if(second_scheduler_lane){if(reply_vector)++second_reply_vector2_count;else ++second_ack_vector_count;}else
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
                if(reply_vector)++reply_vector_count;else
#endif
                ++vector_count;
                throw VectorStop{};
            }
        }
        return;
    }
#endif
    if(sched_join){
#ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
        if(second_scheduler_lane){
            const auto d=sched_join->boundary_detail(c,device_ok(c));
            if(d){std::cout<<"V1371_SCHED_BOUNDARY detail="<<d<<" stage="<<sched_join->stage()<<'\n';throw WitnessFailure{};}
        }
#endif
        if(!sched_join->observe(c,pc,device_ok(c))){
            last_stage=sched_join->stage();last_reason=sched_join->failure();throw WitnessFailure{};
        }
#ifdef UNDERCOVER_V1315_COOP_SAVE
        if(pc==PostAckSchedulerJoin::Save){
            need(coop_save);
            if(!coop_save->capture(c,device_ok(c)))coop_save_refuse(2);
        }
#endif
        return;
    }
    if(sleep_join){
        if(!sleep_join->observe(c,pc,device_ok(c))){last_stage=sleep_join->stage();last_reason=sleep_join->failure();throw WitnessFailure{};}
        if(sleep_join->stage()==4u){need(sleep_join->select_at(c,device_ok(c)));
#ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
            if(second_scheduler_lane)++second_sleep_count;else
#endif
            ++sleep_count;throw SleepStop{};}
        return;
    }
    if(submit_host){submit_trace(pc,c);last_stage=submit_stage;return;}
    if(open_witness&&open_witness->stage()){
        if(pc==OpenScRoute::Vector){
            need(open_witness->vector_trace(c,pc,device_ok(c)));++open_vectors;return;
        }
        const bool ok=open_witness->observe(c,pc,device_ok(c));
        last_stage=open_witness->stage();last_reason=open_witness->request_failure();
        if(!ok)throw WitnessFailure{};
        if(last_stage==9u){
            need(open_witness->submit_at(c,device_ok(c)));
            throw RequestReached{};
        }
        return;
    }
    if(stm_witness){
        const bool ok=stm_witness->observe(c,pc,device_ok(c));
        last_stage=stm_witness->stage();last_reason=stm_witness->stm_failure();
        if(!ok)throw WitnessFailure{};
        if(pc==StmPrefixWitness::Stm){++stm_entries;return;}
        if(pc==StmPrefixWitness::Open&&stm_witness->open_at(c)){
            need(open_witness);
            ++open_entries;
#ifdef UNDERCOVER_V1358_OPEN_RETURN
            if(!open_return||!open_return->capture_open(c,device_ok(c)))open_return_refuse(1);
#endif
            if(!open_witness->begin(c,*stm_witness,device_ok(c))){
                last_reason=open_witness->request_failure();throw WitnessFailure{};
            }
            last_stage=open_witness->stage();return;
        }
        throw WitnessFailure{};
    }
    const bool ok=witness->stage()==2u?witness->target_entry(c,pc,device_ok(c)):witness->continuation(c,pc,device_ok(c));
    last_stage=witness->client_stage();last_reason=witness->cold_failure()?witness->cold_failure():witness->failure();
    if(!ok)throw WitnessFailure{};
}
bool process_pending_callbacks(CPUContext& c){
#ifdef UNDERCOVER_FORMATTER_NESTED
    if(formatter_nested){
        const bool held=formatter_nested_held(c);
#ifdef UNDERCOVER_FORMATTER_RETURN
        if(formatter_nested->stage()==6u){
            if(!formatter_nested->native_return_poll(c,held))formatter_nested_refuse(4);
#ifdef UNDERCOVER_FORMATTER_CALLER_ARRIVAL
            return false; // allow original caller dispatcher and label to be entered
#else
            ++formatter_nested_count;throw FormatterNestedStop{}; // before caller dispatcher tick
#endif
        }
#endif
#ifdef UNDERCOVER_FORMATTER_ARRIVAL
        if(formatter_nested->stage()==2u){
            if(!formatter_nested->control_transfer_poll(c,held))formatter_nested_refuse(4);
            return false;
        }
#endif
        if(!formatter_nested->poll(c,held))formatter_nested_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_FORMATTER_CONTINUATION
    if(formatter_continuation){
        if(!formatter_continuation->poll(c,formatter_continuation_held(c)))formatter_continuation_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER_LEAF
    if(post_stm_formatter_leaf){
        if(!post_stm_formatter_leaf->poll(c,post_stm_formatter_leaf_held(c)))post_stm_formatter_leaf_refuse(4);
        if(post_stm_formatter_leaf->stage()==2u){++post_stm_formatter_leaf_count;throw PostStmFormatterLeafStop{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
    if(post_stm_formatter){
        if(!post_stm_formatter->poll(c,post_stm_formatter_held(c)))post_stm_formatter_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
    if(post_stm_resume){
        if(!post_stm_resume->poll(c,post_stm_resume_held(c)))post_stm_resume_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
    if(post_stm_dependency){
        if(!post_stm_dependency->poll(c,post_stm_dependency_held(c)))post_stm_dependency_refuse(4);
        if(post_stm_dependency->stage()==2u){++post_stm_dependency_count;throw PostStmDependencyStop{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
    if(post_stm_helper){
        if(!post_stm_helper->poll(c,post_stm_helper_held(c)))post_stm_helper_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT
    if(post_stm_report){
        if(!post_stm_report->poll(c,post_stm_report_held(c)))post_stm_report_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_VERSION
    if(post_stm_version){
        if(!post_stm_version->poll(c,post_stm_version_held(c)))post_stm_version_refuse(4);
        if(post_stm_version->stage()==2u){++post_stm_version_count;throw PostStmVersionStop{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
    if(post_stm_restore){
        const unsigned prior=post_stm_restore->stage();
        if(!post_stm_restore->poll(c,post_stm_restore_held(c)))post_stm_restore_refuse(4);
        if(prior==1u&&post_stm_restore->stage()==2u)throw PostStmRestoreEnableStop{};
        if(post_stm_restore->stage()==3u){++post_stm_restore_count;throw PostStmRestoreStop{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_DECISION
    if(post_stm_decision){if(!post_stm_decision->poll(c,post_stm_decision_held(c)))post_stm_decision_refuse(4);return false;}
#endif
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
    if(post_stm_disable){
        if(!post_stm_disable->poll(c,post_stm_disable_held(c)))post_stm_disable_refuse(4);
        if(post_stm_disable->stage()==2u){++post_stm_disable_count;throw PostStmDisableStop{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
    if(post_stm_sc){if(!post_stm_sc->poll(c,post_stm_sc_held(c)))post_stm_sc_refuse(4);return false;}
#endif
#ifdef UNDERCOVER_STM_FINAL_RETURN
    if(stm_final){
        if(!stm_final->poll(c,stm_final_held(c)))stm_final_refuse(4);
        if(stm_final->stage()==2u){++stm_final_count;throw StmFinalReturnStop{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_STM_RESUMED_RESTORE
    if(third_resume){
        if(!third_resume->poll(c,third_resume_held(c)))third_resume_refuse(4);
        if(third_resume->stage()==2u){++third_resume_count;throw StmResumedRestoreStop{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
    if(third_return_route){
        if(!third_return_join->held(c,third_return_storage(c)))third_return_refuse(5);
        if(!third_return_route->stage()){
            if(c.pc!=v1255::returned||c.inst_count!=third_return_tick)third_return_refuse(5);
            return false;
        }
        if(!third_return_route->poll(c,cause.load(),mask.load()))third_return_refuse(5);
        if(third_return_route->stage()==4u){
            if(!third_return_join->finish(c,third_return_storage(c)))third_return_refuse(6);
            ++third_return_count;throw DeferredActiveRfiStop{};
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACK
    if(third_ack){
        if(!third_ack->poll(c,third_ack_held(c)))third_ack_refuse(4);
        if(third_ack->stage()==2u){++third_ack_count;throw DeferredAckStop{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
    if(third_dispatch){
        auto s=B::cold_snapshot();
        if(!s)third_dispatch_refuse(4);
        if(!third_dispatch->stage()){
            if(c.pc!=v1260::dispatcher||!third_irq_held(c))third_dispatch_refuse(4);
        }else if(!third_dispatch->poll(c,*s,third_irq_held(c)))third_dispatch_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_VECTOR
    if(third_vector){
        if(!third_vector->stage()){
            if(c.pc!=ExternalVector||c.inst_count!=third_vector_tick||!third_irq_held(c))third_vector_refuse(4);
        }else if(!third_vector->poll(c,cause.load(),mask.load(),third_irq_held(c)))third_vector_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_STM_OUTER_RESTORE
    if(stm_outer){
        if(!stm_outer->poll(c,stm_outer_held(c),stm_outer_pending(c)))stm_outer_refuse(4);
        ++stm_outer_count;throw StmIoctlReached{};
    }
#endif
#ifdef UNDERCOVER_STM_EVENT_RETURN
    if(stm_event_return)stm_event_refuse(4);
#endif
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
    if(async_wrapper){if(!async_wrapper->poll(c,async_held(c),ioctl_prefix->caller_abi(c)))async_wrapper_refuse(5);return false;}
#endif
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
    if(async_return){if(!async_return->poll(c,async_held(c)))async_refuse(5);return false;}
#endif
#ifdef UNDERCOVER_IPC_DISPATCH
    if(ioctl_dispatch){
        if(!ioctl_dispatch->poll(c,ioctl_dispatch_held(c)))ioctl_dispatch_refuse(5);
        return false;
    }
#endif
#ifdef UNDERCOVER_IPC_PROFILE
    if(ioctl_profile){
        if(!ioctl_profile->poll(c,ioctl_flush_held(c)))ioctl_profile_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
    if(ioctl_submit_queue){
        if(!ioctl_submit_queue->poll(c,ioctl_flush_held(c)))ioctl_submit_queue_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
    if(ioctl_flush){if(!ioctl_flush->poll(c,ioctl_flush_held(c)))ioctl_flush_refuse(3);return false;}
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
    if(ioctl_submit_prefix)ioctl_submit_prefix_refuse(4);
#endif
    if(ioctl_tail)ioctl_tail_refuse(5);
#endif
#endif
    if(ioctl_build&&ioctl_build->stage()==2u){
        if(!ioctl_build->poll(c,ioctl_alloc_held(c)))ioctl_build_refuse(4);
        return false;
    }
#endif
    if(ioctl_alloc&&ioctl_alloc->stage()==1u){
        if(!ioctl_alloc->poll(c,ioctl_alloc_held(c)))ioctl_alloc_refuse(4);
        if(ioctl_alloc->stage()==2u){
            ++ioctl_alloc_count;
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
            if(!ioctl_alloc->returned(c,ioctl_alloc_held(c))||!allocator_descriptor->identity_after_release(c)||
               !ioctl_build->begin(c,ioctl_alloc_held(c),ioctl_alloc->request(),ioctl_alloc->allocated_size(),
                                  allocator_heap,allocator_descriptor->guard()))ioctl_build_refuse(1);
#else
            throw StmIoctlReached{};
#endif
        }
        return false;
    }
#endif
    if(ioctl_prefix&&ioctl_prefix->stage()==1u){if(!ioctl_prefix->poll(c,stm_ioctl_held(c)))ioctl_prefix_refuse(4);return false;}
#endif
    if(stm_ioctl){if(!stm_ioctl->poll(c,stm_ioctl_held(c)))stm_ioctl_refuse(4);return false;}
#endif
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
    if(second_submit_active){
        if(!second_submit->boundary(c,second_submit_held(c))||++second_submit_polls>8192u)second_submit_refuse(4);
        const auto stage=second_submit->stage();
        const bool allowed=(c.pc==OpenScRoute::Resume&&stage==4u&&(c.msr&0x8000u))||
            std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end();
        if(!allowed)second_submit_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
    if(second_request_active){
        if(!second_request->boundary(c,second_request_held(c))||++second_request_polls>8192u)second_request_refuse(5);
        const auto stage=second_request->stage();
        bool allowed=false;
        if(c.pc==OpenRequestWitness::Alloc)allowed=stage==2u&&c.lr==0x8051998cu;
        else if(c.pc==0x8051998cu)allowed=stage==5u&&c.lr==c.pc&&(c.msr&0x8000u);
        else if(c.pc==v626::restore_resume)allowed=stage==5u&&(c.msr&0x8000u);
        else if(c.pc==OpenScRoute::Resume)allowed=stage==7u&&(c.msr&0x8000u);
        else allowed=std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end();
        if(!allowed)second_request_refuse(5);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1359_SECOND_OPEN
    if(second_open_active){if(!second_open->poll(c,open_return_held(c),open_descriptor(c)))second_open_refuse(4);return false;}
#endif
#ifdef UNDERCOVER_V1358_OPEN_RETURN
    if(open_return_active){
        if(!open_return->poll(c,open_return_held(c),open_descriptor(c)))open_return_refuse(6);
        if(open_return->stage()==5u){
            if(!open_return->returned(c,open_return_held(c),open_descriptor(c)))open_return_refuse(6);
#ifdef UNDERCOVER_V1379_SECOND_RETURN
            if(second_scheduler_lane){++second_open_return_count;throw OpenReturned{};}
#endif
            ++open_return_count;
#ifdef UNDERCOVER_V1359_SECOND_OPEN
            if(!second_open->begin(c,*open_return,open_return_held(c),open_descriptor(c),open_return_device==StmIos::Device::Immediate?1u:2u))second_open_refuse(1);
            open_return_active=false;second_open_active=true;return false;
#else
            throw OpenReturned{};
#endif
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
    if(allocator_active){
        if(!allocator_release->poll(c,allocator_held(c))||allocator_release->stage()!=1u)allocator_refuse(5);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
    if(submit_resume_active){
#ifdef UNDERCOVER_V1378_SECOND_FREE
        if(second_scheduler_lane&&submit_resume->initial_dispatch_poll(c,submit_held(c)))return false;
#endif
        if(!submit_resume->poll(c,submit_held(c)))submit_resume_refuse(3);return false;
    }
#endif
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
    if(exit_active){
        if(!sleep_exit->poll(c,load_held(c)))sleep_exit_refuse(5);
        if(sleep_exit->stage()==3u){
            if(!sleep_exit->returned(c,load_held(c)))sleep_exit_refuse(5);
            
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)++second_sleep_exit_count;else
#endif
            ++sleep_exit_count;
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)throw SleepExited{};
#endif
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
            if(!submit_resume->begin(c,*sleep_exit,load_held(c)))submit_resume_refuse(4);
            exit_active=false;submit_resume_active=true;return false;
#else
            throw SleepExited{};
#endif
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
    if(sleep_active){if(!sleep_resume->poll(c,load_held(c)))sleep_resume_refuse(3);return false;}
#endif
#ifdef UNDERCOVER_V1334_COOP_LOAD
    if(load_active){
        if(!coop_load->poll(c,load_held(c)))load_refuse(4);
        if(coop_load->stage()==4u){
            if(!coop_load->restored(c,load_held(c)))load_refuse(5);
            
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)++second_load_count;else
#endif
            ++load_count;
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
            if(!sleep_resume->begin(c,*coop_load,load_held(c))||!sleep_resume->poll(c,load_held(c)))sleep_resume_refuse(4);
            load_active=false;sleep_active=true;return false;
#else
            throw CooperativeReturned{};
#endif
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
    if(selection_route){
        const auto detail=selection_witness->boundary_detail(c,device_ok(c));
        if(detail){std::cout<<"V1332_SELECTION_BOUNDARY detail="<<detail<<'\n';selection_refuse(4);}
        if(!selection_route->poll(c,device_ok(c)))selection_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
    if(ready_idle){
        if(!ready_idle->boundary(c,device_ok(c)))idle_return_refuse(5);
        if(!idle_epilogue->stage()){
            if(c.pc!=v1255::returned||c.inst_count!=idle_tick)idle_return_refuse(5);
            return false;
        }
        if(!idle_epilogue->poll(c,cause.load(),mask.load()))idle_return_refuse(5);
        if(idle_epilogue->stage()==4u){
            if(!ready_idle->finish(c,device_ok(c)))idle_return_refuse(6);
            
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)++second_idle_return_count;else
#endif
            ++idle_return_count;throw IdleRfiReturned{};
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_V1300_REPLY_RETURN
    if(reply_return){
        if(!reply_return->poll(c,device_ok(c)))return_refuse(3);
        if(reply_return->stage()==2u){
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)++second_return_count;else
#endif
            ++return_count;throw ReplyHandlerReturned{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_V1292_NESTED_WAKE
    if(nested_wake){
        if(!nested_wake->poll(c,device_ok(c)))nested_refuse(3);
        if(nested_wake->stage()==2u){
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
            if(second_scheduler_lane)++second_nested_count;else
#endif
            ++nested_count;throw NestedReturned{};}
        return false;
    }
#endif
#ifdef UNDERCOVER_V1289_WAKE_READY
    if(wake_ready){if(!wake_ready->poll(c,device_ok(c)))wake_refuse(3);return false;}
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    if(reply_body){
        if(!reply_body->poll(c,device_ok(c)))body_refuse(3);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){
        if(!reply_entry->poll(c,device_ok(c)))reply_entry_refuse(3);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
    if(epilogue){
        if(!reply_held(c))epilogue_refuse(5);
        if(!epilogue->stage()){
            if(c.pc!=v1255::returned||c.inst_count!=epilogue_tick)epilogue_refuse(5);
            return false;
        }
        if(epilogue->stage()==2u){
            if(!epilogue->pending_rfi_return(c,cause.load(),mask.load()))epilogue_refuse(6);
            if(!enter_scheduler_reply_irq(c,*epilogue_host,irq_capture,reply_capture,v1259::vector,reply_request
#ifdef UNDERCOVER_V1370_SECOND_REPLY
                ,second_scheduler_lane?second_irq_kind:0u
#endif
                ))
                epilogue_refuse(7);
            if(!reply_held(c)||c.pc!=ExternalVector)epilogue_refuse(7);
#ifdef UNDERCOVER_V1370_SECOND_REPLY
            if(second_scheduler_lane)++second_reply_rfi_count;else
#endif
            ++rfi_count;throw ReplyEntered{};
        }
        if(!epilogue->poll(c,cause.load(),mask.load()))epilogue_refuse(5);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
    if(joined_ack){
        if(!joined_ack->poll(c,device_ok(c)))joined_refuse(3);
        if(c.pc==v1255::returned){
            if(!joined_ack->finish(c,device_ok(c)))joined_refuse(4);
            throw AckReturned{};
        }
        return false;
    }
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    if(ipc_dispatch){
        auto s=B::cold_snapshot();need(s.has_value());
        if(!ipc_dispatch->stage()){
            if(c.pc!=v1260::dispatcher||!same_scheduler_ipc_snapshot(*s,vector_mail)||!device_ok(c))dispatch_refuse(4);
        }else if(!ipc_dispatch->poll(c,*s,device_ok(c)))dispatch_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
    if(vector_active){
        if(!ipc_vector.stage()){
            if(c.pc!=ExternalVector||c.inst_count!=vector_tick||!vector_held(c))vector_refuse(4);
        }else if(!ipc_vector.poll(c,cause.load(),mask.load(),vector_held(c)))vector_refuse(4);
        return false;
    }
#endif
    if(sched_join){
        if(c.pc==v1256::resume&&sched_join->stage()==6u){
            if(!sched_join->enabled_at(c,device_ok(c))){
                last_stage=sched_join->stage();last_reason=sched_join->failure();throw WitnessFailure{};
            }
#ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
            if(second_scheduler_lane)++second_scheduler_count;else
#endif
            ++scheduler_count;throw SchedulerStop{};
        }
#ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
        if(second_scheduler_lane){
            const auto d=sched_join->boundary_detail(c,device_ok(c));
            if(d){std::cout<<"V1371_SCHED_BOUNDARY detail="<<d<<" stage="<<sched_join->stage()<<'\n';throw WitnessFailure{};}
        }
#endif
        need(sched_join->boundary(c,device_ok(c)));
        const bool allowed=(c.pc==PostAckSchedulerJoin::Select&&sched_join->stage()==1u)||
            sched_join->indirect_poll(c)||
            std::find(v1256::polls.begin(),v1256::polls.end(),c.pc)!=v1256::polls.end();
        if(!allowed){
            last_stage=sched_join->stage();
            std::cout<<"V1256_SCHED_POLL_REFUSAL stage="<<last_stage
                     <<" category="<<(c.pc==PostAckSchedulerJoin::Callback?1:2)<<'\n';
            throw WitnessFailure{};
        }
        return false;
    }
    if(sleep_join){
        need(sleep_join->boundary(c,device_ok(c)));
        need(c.pc==PostAckSleepJoin::Sleep||std::find(v1252::polls.begin(),v1252::polls.end(),c.pc)!=v1252::polls.end());
        return false;
    }
    const auto s=B::cold_snapshot();need(s&&!(s->pi_cause&s->pi_mask)&&!s->queued&&!s->replies);
    if(submit_host){
        need(submit_join->boundary(c,device_ok(c))&&++submit_polls<=8192u);
        if(c.pc==OpenRequestWitness::Submit)need(submit_stage==1&&c.lr==0x80519a3cu);
        else if(c.pc==OpenScRoute::Resume)need(submit_stage==4&&(c.msr&0x8000u));
        else need(std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end());
        return false;
    }
    if(open_witness&&open_witness->stage()){
        need(open_witness->boundary(c,device_ok(c))&&++open_polls<=8192u);
        // Explicit native tail roots and dispatcher resumes, plus the
        // exact translated local loop and restore polling seams.
        if(c.pc==OpenRequestWitness::Alloc)need(open_witness->stage()==2u&&c.lr==0x8051998cu);
        else if(c.pc==0x8051998cu)need(open_witness->stage()==5u&&c.lr==c.pc&&(c.msr&0x8000u));
        else if(c.pc==v626::restore_resume)need(open_witness->stage()==5u&&(c.msr&0x8000u));
        else if(c.pc==OpenScRoute::Resume)need(open_witness->stage()==7u&&(c.msr&0x8000u));
        else need(std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end());
        return false;
    }
    if(stm_witness){need(stm_witness->boundary(c,device_ok(c)));return false;}
    need(c.is_running&&!c.dispatch_saved_ctx&&witness&&last_stage>=2&&last_stage<19);
    need(witness->boundary(c,device_ok(c)));
    if(c.pc==v626::restore_resume){
        need((c.msr&0x8000u)&&(last_stage==10u||last_stage==16u));++callbacks;
    }else{
        need(std::find(v626::backward_polls.begin(),v626::backward_polls.end(),c.pc)!=v626::backward_polls.end());
        need(++loop_polls<=8192u);
    }
    return false;
}
bool handle_syscall(CPUContext& c){
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
    if(post_stm_formatter)post_stm_formatter_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
    if(post_stm_resume)post_stm_resume_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
    if(post_stm_dependency)post_stm_dependency_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
    if(post_stm_helper)post_stm_helper_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT
    if(post_stm_report)post_stm_report_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_VERSION
    if(post_stm_version)post_stm_version_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
    if(post_stm_restore)post_stm_restore_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_DECISION
    if(post_stm_decision)post_stm_decision_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
    if(post_stm_disable)post_stm_disable_refuse(7);
#endif
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
    if(post_stm_sc)post_stm_sc_refuse(7);
#endif
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
    if(ioctl_submit_queue)ioctl_submit_queue_refuse(5);
#endif
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
    if(ioctl_submit_prefix&&!ioctl_flush)ioctl_submit_prefix_refuse(4);
#endif
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
    if(ioctl_flush){
        if(!ioctl_flush->dispatch(c,ioctl_flush_held(c),[](auto& cpu){func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }))ioctl_flush_refuse(4);
        return false;
    }
#endif
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
    if(second_submit_active){
        if(!second_submit->dispatch(c,second_submit_held(c),[](auto& cpu){func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }))second_submit_refuse(5);
        ++second_submit_returns;return false;
    }
#endif
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
    if(second_request_active){
        if(!second_request->dispatch(c,second_request_held(c),[](auto& cpu){func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }))second_request_refuse(6);
        ++second_request_returns;return false;
    }
#endif
    if(submit_host){
        need(submit_stage==4&&submit_join&&device_ok(c));
        need(submit_join->dispatch(c,device_ok(c),[](auto& cpu){func_80000C00(cpu);},
            [](auto& cpu,const auto& gp,uint32_t hid){
                for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
                return true;
            }));
        return false;
    }

    if(!open_witness||open_witness->stage()!=7u)throw std::runtime_error("V1256 unexpected syscall");
    need(open_witness->dispatch(c,device_ok(c),[](auto& cpu){func_80000C00(cpu);},
        [](auto& cpu,const auto& gp,uint32_t hid){
            for(unsigned i=0;i<32;++i)if(cpu.gpr[i]!=(i==9?hid:i==10?(hid|8u):gp[i]))return false;
            return true;
        }));
    ++open_returns;return false;
}
void interpret_step(CPUContext&){throw std::runtime_error("V1256 interpreter forbidden");}
void micro_interpret(CPUContext&,uint32_t,uint32_t){throw std::runtime_error("V1256 interpreter forbidden");}
void note_null_call(uint32_t,uint32_t){throw std::runtime_error("V1256 null branch");}
void watch_hit(uint32_t,uint32_t,int){}
void GX_WGPIPE_Write8(uint8_t){} void GX_WGPIPE_Write16(uint16_t){} void GX_WGPIPE_Write32(uint32_t){}
void GX_WGPIPE_WriteF32(float){} void GX_WGPIPE_WriteF64(double){}
uint16_t HW_Reg_Read16(uint32_t){throw std::runtime_error("V1256 unexpected MMIO16");}
void HW_Reg_Write16(uint32_t,uint16_t){throw std::runtime_error("V1256 unexpected MMIO16");}
uint32_t HW_Reg_Read32(uint32_t a){
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
    if(post_stm_formatter)post_stm_formatter_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
    if(post_stm_resume)post_stm_resume_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
    if(post_stm_dependency)post_stm_dependency_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
    if(post_stm_helper)post_stm_helper_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT
    if(post_stm_report)post_stm_report_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_VERSION
    if(post_stm_version)post_stm_version_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
    if(post_stm_restore)post_stm_restore_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_DECISION
    if(post_stm_decision)post_stm_decision_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
    if(post_stm_disable)post_stm_disable_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
    if(post_stm_sc)post_stm_sc_refuse(6);
#endif
#ifdef UNDERCOVER_STM_FINAL_RETURN
    if(stm_final)stm_final_refuse(6);
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACK
    if(third_ack){
        if(!ioctl_dispatch_cpu)third_ack_refuse(5);
        auto& c=*ioctl_dispatch_cpu;
        auto v=third_ack->read(c,a,third_ack_held(c));if(!v)third_ack_refuse(5);return *v;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
    if(third_dispatch){
        const auto p=a&0x3fffffffu;
        if(!ioctl_dispatch_cpu||!third_irq_held(*ioctl_dispatch_cpu)||(p!=IosBus::PI_CAUSE&&p!=IosBus::PI_MASK))
            third_dispatch_refuse(5);
        B::refresh_pi(a);const auto value=p==IosBus::PI_CAUSE?cause.load():mask.load();
        if(!third_dispatch->read(a,value)||!third_irq_held(*ioctl_dispatch_cpu))third_dispatch_refuse(5);
        return value;
    }
#endif
#ifdef UNDERCOVER_IPC_DISPATCH
    if(ioctl_dispatch){
        if(!ioctl_dispatch_cpu||!ioctl_dispatch->read_allowed(*ioctl_dispatch_cpu,a,ioctl_dispatch_held(*ioctl_dispatch_cpu)))
            ioctl_dispatch_refuse(6);
        auto& c=*ioctl_dispatch_cpu;
        auto v=ioctl_event_gate->read_submission_control(a,c.msr,ioctl_dispatch_storage_held(c));
        if(!v||!ioctl_dispatch->read_done(c,*v,ioctl_dispatch_held(c)))ioctl_dispatch_refuse(6);
        return *v;
    }
#endif
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
    if(ioctl_submit_queue)ioctl_submit_queue_refuse(6);
#endif
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
    if(stm_ioctl)stm_ioctl_refuse(5);
#endif
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
    if(second_submit_active){
        const auto phys=a&0x3fffffffu;
        if(!second_submit_cpu||second_submit->stage()!=7u||
           !second_submit->boundary(*second_submit_cpu,second_submit_held(*second_submit_cpu))||
           (phys!=IosBus::IPC+M::PPCCTRL&&phys!=IosBus::MIRROR+M::PPCCTRL))second_submit_refuse(6);
        const auto v=B::read32(a);
        if(!v||!second_submit->boundary(*second_submit_cpu,second_submit_held(*second_submit_cpu)))second_submit_refuse(6);
        return *v;
    }
#endif
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
    if(second_request_active)second_request_refuse(7);
#endif
#ifdef UNDERCOVER_V1359_SECOND_OPEN
    if(second_open_active)second_open_refuse(5);
#endif
#ifdef UNDERCOVER_V1358_OPEN_RETURN
    if(open_return_active)open_return_refuse(7);
#endif
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
    if(allocator_active)allocator_refuse(6);
#endif
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
    if(submit_resume_active)submit_resume_refuse(5);
#endif
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
    if(exit_active)sleep_exit_refuse(6);
#endif
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
    if(sleep_active)sleep_resume_refuse(5);
#endif
#ifdef UNDERCOVER_V1334_COOP_LOAD
    if(load_active)load_refuse(6);
#endif
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
    if(selection_route)selection_refuse(5);
#endif
    const auto p=a&0x3fffffffu;
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
    if(ready_idle)idle_return_refuse(7);
#endif
#ifdef UNDERCOVER_V1300_REPLY_RETURN
    if(reply_return){auto v=reply_return->read(*return_cpu,a,device_ok(*return_cpu));if(!v)return_refuse(4);return *v;}
#endif
#ifdef UNDERCOVER_V1292_NESTED_WAKE
    if(nested_wake){nested_wake->refuse_mmio();nested_refuse(4);}
#endif
#ifdef UNDERCOVER_V1289_WAKE_READY
    if(wake_ready){wake_ready->refuse_mmio();wake_refuse(4);}
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    if(reply_body){
        auto v=reply_body->read(*body_cpu,a,device_ok(*body_cpu));
        if(!v)body_refuse(4);
        return *v;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){
        const auto v=reply_entry->read(*reply_cpu,a,device_ok(*reply_cpu));
        if(!v)reply_entry_refuse(4);
        return *v;
    }
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
    if(epilogue)epilogue_refuse(8);
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
    if(joined_ack){
        auto v=joined_ack->read(*joined_cpu,a,device_ok(*joined_cpu));if(!v)joined_refuse(5);return *v;
    }
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    if(ipc_dispatch){
        if(p!=IosBus::PI_CAUSE&&p!=IosBus::PI_MASK)dispatch_refuse(5);
        B::refresh_pi(a);const auto v=p==IosBus::PI_CAUSE?cause.load():mask.load();
        if(!ipc_dispatch->read(a,v))dispatch_refuse(5);
        return v;
    }
#endif
    if(p==IosBus::PI_MASK)return mask.load();
    if(submit_host&&(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL)){auto v=B::read32(a);need(v.has_value());return *v;}
    if(p==IosBus::IPC+H::PPC_MASK||p==IosBus::MIRROR+H::PPC_MASK){
        auto v=B::read32(a);need(v.has_value());return *v;
    }
    throw std::runtime_error("V1256 unexpected MMIO read");
}
void HW_Reg_Write32(uint32_t a,uint32_t v){
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
    if(post_stm_formatter)post_stm_formatter_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
    if(post_stm_resume)post_stm_resume_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
    if(post_stm_dependency)post_stm_dependency_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
    if(post_stm_helper)post_stm_helper_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_REPORT
    if(post_stm_report)post_stm_report_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_VERSION
    if(post_stm_version)post_stm_version_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
    if(post_stm_restore)post_stm_restore_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_DECISION
    if(post_stm_decision)post_stm_decision_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
    if(post_stm_disable)post_stm_disable_refuse(6);
#endif
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
    if(post_stm_sc)post_stm_sc_refuse(6);
#endif
#ifdef UNDERCOVER_STM_FINAL_RETURN
    if(stm_final)stm_final_refuse(6);
#endif
#ifdef UNDERCOVER_STM_DEFERRED_ACK
    if(third_ack){
        if(!ioctl_dispatch_cpu||!third_ack->write(*ioctl_dispatch_cpu,a,v,third_ack_held(*ioctl_dispatch_cpu)))third_ack_refuse(6);
        return;
    }
#endif
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
    if(third_dispatch)third_dispatch_refuse(6);
#endif
#ifdef UNDERCOVER_IPC_DISPATCH
    if(ioctl_dispatch){
        if(!ioctl_dispatch_cpu||!ioctl_dispatch->write_allowed(*ioctl_dispatch_cpu,a,v,ioctl_dispatch_held(*ioctl_dispatch_cpu)))
            ioctl_dispatch_refuse(7);
        auto& c=*ioctl_dispatch_cpu;
        if(!ioctl_event_gate->submit_write(a,v,c.msr,ioctl_dispatch_storage_held(c))||
           !ioctl_dispatch->write_done(c,a,v,ioctl_dispatch_held(c)))ioctl_dispatch_refuse(7);
        return;
    }
#endif
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
    if(ioctl_submit_queue)ioctl_submit_queue_refuse(6);
#endif
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
    if(stm_ioctl)stm_ioctl_refuse(5);
#endif
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
    if(second_submit_active){
        if(!second_submit_cpu||!second_submit->write(*second_submit_cpu,a,v,second_submit_held(*second_submit_cpu)))second_submit_refuse(7);
        return;
    }
#endif
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
    if(second_request_active)second_request_refuse(7);
#endif
#ifdef UNDERCOVER_V1359_SECOND_OPEN
    if(second_open_active)second_open_refuse(5);
#endif
#ifdef UNDERCOVER_V1358_OPEN_RETURN
    if(open_return_active)open_return_refuse(7);
#endif
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
    if(allocator_active)allocator_refuse(6);
#endif
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
    if(submit_resume_active)submit_resume_refuse(5);
#endif
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
    if(exit_active)sleep_exit_refuse(6);
#endif
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
    if(sleep_active)sleep_resume_refuse(6);
#endif
#ifdef UNDERCOVER_V1334_COOP_LOAD
    if(load_active)load_refuse(7);
#endif
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
    if(selection_route)selection_refuse(6);
#endif
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
    if(ready_idle)idle_return_refuse(8);
#endif
#ifdef UNDERCOVER_V1300_REPLY_RETURN
    if(reply_return){if(!reply_return->write(*return_cpu,a,v,device_ok(*return_cpu)))return_refuse(5);return;}
#endif
#ifdef UNDERCOVER_V1292_NESTED_WAKE
    if(nested_wake){nested_wake->refuse_mmio();nested_refuse(5);}
#endif
#ifdef UNDERCOVER_V1289_WAKE_READY
    if(wake_ready){wake_ready->refuse_mmio();wake_refuse(5);}
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    if(reply_body){
        if(!reply_body->write(*body_cpu,a,v,device_ok(*body_cpu)))body_refuse(5);
        return;
    }
#endif
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    if(reply_entry){reply_entry->write_refused();reply_entry_refuse(5);}
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
    if(epilogue)epilogue_refuse(8);
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
    if(joined_ack){
        if(!joined_ack->write(*joined_cpu,a,v,device_ok(*joined_cpu)))joined_refuse(6);
        return;
    }
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    if(ipc_dispatch)dispatch_refuse(6);
#endif
    const auto p=a&0x3fffffffu;
    if(submit_host){
        // The guest CPU is available only in this isolated harness; keep
        // the witness on exactly the same context as the original call.
        need(submit_cpu&&submit_join);
        if(!submit_join->write(*submit_cpu,a,v,device_ok(*submit_cpu))){
            const auto s=B::cold_snapshot();
            const bool ctrl=p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL;
            std::cout<<"V1254_SUBMIT_MMIO_REFUSAL category="<<submit_join->write_failure()
                     <<" writes="<<submit_join->writes()<<" control="<<int(ctrl)
                     <<" low_bits="<<(ctrl?v&0x3fu:0u)<<" prior="<<(s?s->control&0x3fu:0u)<<'\n';
            last_reason=submit_join->failure();throw WitnessFailure{};
        }
        return;
    }
    if(p==IosBus::PI_MASK){mask.store(v);B::refresh_pi(a);return;}
    if(p==IosBus::IPC+H::PPC_MASK||p==IosBus::MIRROR+H::PPC_MASK){need(B::write32(a,v));return;}
    if(p==IosBus::IPC+M::PPCCTRL||p==IosBus::MIRROR+M::PPCCTRL){need(B::write32(a,v));++control_writes;return;}
    throw std::runtime_error("V1256 unexpected MMIO write");
}
}
extern "C" void run_game(nw::CPUContext&);
int main(int argc,char** argv)try{
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    need(argc==2);
    const auto initial_data=read_initialized_dol_input(argv[1]);
    std::cout<<"V1264_DOL_DATA verified=1 initialized_only=1 ranges="<<initialized_dol_ranges(initial_data).size()<<'\n';
#else
    (void)argv;need(argc==1);
#endif
    for(unsigned trial=0;trial<8;++trial){
        last_trial=trial;last_stage=last_reason=0;
        auto cpu=std::make_unique<nw::CPUContext>();auto& c=*cpu;
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
        // Match the verified V947 dispatcher setup. Load static initialized
        // data before all modeled OSInit postconditions and original IPC.
        seed_initialized_dol_data(c.mmu,initial_data);
#endif
        cause=0;mask=0xf0|SiController::PI_SI;
        NativeIosTransport host(c.mmu.mem1,c.mmu.mem2,cause,mask);B binding(host);
        SiController ctl(cause);SecondCompletionAck ack;si_ack=&ack;
        seed_completed_si(c,ctl,ack);
        need(B::write32(IosBus::IPC+H::PPC_MASK,H::IPC_PPC));
        for(auto w:v626::words)c.mmu.write32(w.pc,w.word);
        for(auto w:v626::submit_sda)c.mmu.write32(w.pc,w.word);
        for(auto w:v1243::words)c.mmu.write32(w.pc,w.word);
#ifdef UNDERCOVER_V1358_OPEN_RETURN
        for(auto w:v1358::stm_words)c.mmu.write32(w.pc,w.word);
#ifdef UNDERCOVER_V1379_SECOND_RETURN
        c.mmu.write32(v1379::expected.stm_resume,v1379::expected.stm_resume_word);
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
        for(auto w:v1383::words)c.mmu.write32(w.pc,w.word);
#ifdef UNDERCOVER_STM_FINAL_RETURN
        // Authenticated original caller word, used only as a stop guard.
        // The modeled OSInit bridge is not executed in this focused mode.
        need(stm_final_private::expected.caller==v629::expected_stm.stm.lr);
        c.mmu.write32(stm_final_private::expected.caller,stm_final_private::expected.caller_word);
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
        for(auto w:post_stm_sc_private::words)c.mmu.write32(w.pc,w.word);
        need(c.mmu.read32(post_stm_sc_private::expected.disable)==post_stm_sc_private::expected.disable_word);
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
        // Original continuation identity is only a stop guard in this
        // lane; the compiled SC prefix still has a nonreturning guard.
        c.mmu.write32(post_stm_sc_disable_private::expected.caller,post_stm_sc_disable_private::expected.caller_word);
#ifdef UNDERCOVER_POST_STM_SC_DECISION
        for(auto w:post_stm_sc_decision_private::words)c.mmu.write32(w.pc,w.word);
        need(c.mmu.read32(post_stm_sc_decision_private::expected.restore)==post_stm_sc_decision_private::expected.restore_word);
        // No SC data is seeded here. The cold flag must already be zero.
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
        // Original next instruction is a stop guard, not executed.
        c.mmu.write32(post_stm_sc_restore_private::expected.caller,post_stm_sc_restore_private::expected.caller_word);
#ifdef UNDERCOVER_POST_STM_SC_VERSION
        for(auto w:post_stm_sc_version_private::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(post_stm_sc_version_private::expected.report,post_stm_sc_version_private::expected.report_word);
#ifdef UNDERCOVER_POST_STM_SC_REPORT
        for(auto w:post_stm_sc_report_private::path)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(post_stm_sc_report_private::expected.target,post_stm_sc_report_private::expected.target_word);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
        for(auto w:post_stm_sc_report_helper_private::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(post_stm_sc_report_helper_private::expected.target,post_stm_sc_report_helper_private::expected.target_word);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
        for(auto w:post_stm_sc_report_dependency_private::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(post_stm_sc_report_dependency_private::expected.caller,post_stm_sc_report_dependency_private::expected.caller_word);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
        for(auto w:post_stm_sc_report_resume_private::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(post_stm_sc_report_resume_private::expected.call_target,post_stm_sc_report_resume_private::expected.call_word);
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
        for(auto w:post_stm_sc_formatter_private::path)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(post_stm_sc_formatter_private::expected.target,post_stm_sc_formatter_private::expected.target_word);
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER_LEAF
        for(auto w:post_stm_sc_formatter_leaf_private::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(post_stm_sc_formatter_leaf_private::expected.caller,post_stm_sc_formatter_leaf_private::expected.caller_word);
#ifdef UNDERCOVER_FORMATTER_CONTINUATION
        for(auto w:formatter_continuation_private::path)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(formatter_continuation_private::expected.target,formatter_continuation_private::expected.target_word);
#ifdef UNDERCOVER_FORMATTER_NESTED
        for(auto w:formatter_nested_private::path)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(formatter_nested_private::expected.target,formatter_nested_private::expected.target_word);
#ifdef UNDERCOVER_FORMATTER_CONTROL
        const auto control=formatter_nested_private::expected.control;
        c.mmu.write32(control.destination,control.word); // authenticated original fixture code, not guest data
#ifdef UNDERCOVER_FORMATTER_POST_CTR
        for(auto w:formatter_post_ctr_private::path)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(formatter_post_ctr_private::expected.target,formatter_post_ctr_private::expected.target_word);
#ifdef UNDERCOVER_FORMATTER_PARTIAL
        for(auto w:formatter_partial_private::path)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(formatter_partial_private::expected.target,formatter_partial_private::expected.target_word);
#ifdef UNDERCOVER_FORMATTER_SPECIAL
        c.mmu.write32(formatter_special_private::expected.target,formatter_special_private::expected.target_word);
#ifdef UNDERCOVER_FORMATTER_RELEASE
        c.mmu.write32(formatter_release_private::expected.target,formatter_release_private::expected.target_word);
#ifdef UNDERCOVER_FORMATTER_RETURN
#ifdef UNDERCOVER_FORMATTER_CALLER_ARRIVAL
        c.mmu.write32(formatter_caller_private::caller,formatter_caller_private::word); // authenticated original code
#ifdef UNDERCOVER_FORMATTER_CALLER_BYTE
        c.mmu.write32(formatter_caller_byte_private::next_pc,formatter_caller_byte_private::next_word);
#ifdef UNDERCOVER_FORMATTER_CALLER_INTEGERS
        for(auto step:formatter_caller_integer_private::path)c.mmu.write32(step.pc,step.word);
        c.mmu.write32(formatter_caller_integer_private::end_pc,formatter_caller_integer_private::end_word);
#ifdef UNDERCOVER_FORMATTER_CALLER_BRANCH
        c.mmu.write32(formatter_caller_branch_private::next_pc,formatter_caller_branch_private::next_word);
        c.mmu.write32(formatter_caller_branch_private::other_pc,0x44000002u);
#ifdef UNDERCOVER_FORMATTER_CALLER_SECOND_BRANCH
        c.mmu.write32(formatter_caller_second_branch_private::next_pc,formatter_caller_second_branch_private::next_word);
        c.mmu.write32(formatter_caller_second_branch_private::other_pc,0x44000002u);
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_INTEGERS
        for(auto step:formatter_caller_post_integer_private::path)c.mmu.write32(step.pc,step.word);
        c.mmu.write32(formatter_caller_post_integer_private::end_pc,formatter_caller_post_integer_private::end_word);
#ifdef UNDERCOVER_FORMATTER_CALLER_THIRD_BRANCH
        c.mmu.write32(formatter_caller_third_branch_private::next_pc,formatter_caller_third_branch_private::next_word);
        c.mmu.write32(formatter_caller_third_branch_private::other_pc,0x44000002u);
#ifdef UNDERCOVER_FORMATTER_CALLER_FOURTH_BRANCH
        c.mmu.write32(formatter_caller_fourth_branch_private::next_pc,formatter_caller_fourth_branch_private::next_word);
        c.mmu.write32(formatter_caller_fourth_branch_private::other_pc,0x44000002u);
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED
        for(auto s:formatter_caller_mixed_private::path){
            c.mmu.write32(s.pc,s.word);
            if(s.other_pc)c.mmu.write32(s.other_pc,0x44000002u);
        }
        c.mmu.write32(formatter_caller_mixed_private::end_pc,formatter_caller_mixed_private::end_word);
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE
        c.mmu.write32(formatter_caller_mixed_byte_private::next_pc,formatter_caller_mixed_byte_private::next_word);
        
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_MIXED
        for(auto s:formatter_caller_post_mixed_private::path){
            c.mmu.write32(s.pc,s.word);
            if(s.other_pc)c.mmu.write32(s.other_pc,0x44000002u);
        }
        c.mmu.write32(formatter_caller_post_mixed_private::end_pc,formatter_caller_post_mixed_private::end_word);
#ifdef UNDERCOVER_FORMATTER_CALLER_STACK_MOVE
        c.mmu.write32(formatter_caller_stack_move_private::next_pc,formatter_caller_stack_move_private::next_word);
#ifdef UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER
        c.mmu.write32(formatter_caller_final_integer_private::end_pc,formatter_caller_final_integer_private::end_word);
        c.mmu.write32(formatter_caller_final_integer_private::end_pc+4u,0x44000002u);
#ifdef UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
        c.mmu.write32(formatter_caller_next_entry_private::target,formatter_caller_next_entry_private::word);
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
        c.mmu.write32(formatter_caller_report_byte_private::next_pc,formatter_caller_report_byte_private::next_word);
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
        c.mmu.write32(formatter_report_compare_private::next_pc,formatter_report_compare_private::next_word);
        #ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
        c.mmu.write32(formatter_report_copy_private::next_pc,formatter_report_copy_private::next_word);
        c.mmu.write32(formatter_report_copy_private::next_pc+4u,0x44000002u);
#else
        c.mmu.write32(formatter_report_compare_private::next_pc+4u,0x44000002u);
#endif
#else
        c.mmu.write32(formatter_caller_report_byte_private::next_pc+4u,0x44000002u);
#endif
#else
        c.mmu.write32(formatter_caller_next_entry_private::target+4u,0x44000002u);
#endif
#endif // UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
#else
        c.mmu.write32(formatter_caller_stack_move_private::next_pc+4u,0x44000002u);
#endif
#endif
#else
        c.mmu.write32(formatter_caller_mixed_byte_private::next_pc+4u,0x44000002u);
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
#else
        // The private return contract authenticates this synthetic fixture guard.
        c.mmu.write32(formatter_return_private::caller,formatter_return_private::guard);
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
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#endif
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
        for(auto w:v1386::words)c.mmu.write32(w.pc,w.word);
#endif
#endif
#endif
#endif
        for(auto w:v1252::words)c.mmu.write32(w.pc,w.word);
        for(auto w:v1256::words)c.mmu.write32(w.pc,w.word);
        // Focused fixture: model the default thread previously initialized
        // by OSInitThread, before any original IPC execution.
        c.mmu.write32(PostAckSleepJoin::Current,PostAckSleepJoin::Thread);
        c.mmu.write16(PostAckSleepJoin::Thread+712u,2u);
        c.mmu.write16(PostAckSleepJoin::Thread+714u,1u);
        // Seed only the original V549 thread-init postcondition, before IPC.
        // Neither the saved context nor the idle selection is fabricated.
        using Q=PostAckSchedulerJoin;
        c.mmu.write32(Q::Active,Q::Thread);c.mmu.write32(Q::Physical,Q::Thread&0x3fffffffu);
        c.mmu.write32(0x800000dcu,Q::Thread);c.mmu.write32(0x800000e0u,Q::Thread);
        c.mmu.write32(Q::Thread+720u,16u);c.mmu.write32(Q::Thread+724u,16u);
        c.mmu.write32(Q::Thread+728u,0xffffffffu);
        c.mmu.write32(Q::Thread+772u,0x80751cb8u);c.mmu.write32(Q::Thread+776u,0x80711cb8u);
        c.mmu.write32(0x80711cb8u,0xdeadbabeu);c.mmu.write32(Q::CallbackPtr,Q::Callback);
        // Original initialized SDA/path data is privately seeded before
        // IPC. The actual original IPC code may mutate its own globals.
        for(auto b:v1243::data)c.mmu.write8(b.addr,b.value);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
        // Model original initialized data loading at fixture setup only.
        // Never repair live diagnostic state at admission.
        for(unsigned i=0;i<post_stm_sc_report_dependency_private::initial.size();++i){
            const auto a=post_stm_sc_report_dependency_private::object.base+i;
            const auto v=post_stm_sc_report_dependency_private::initial[i];
            need(c.mmu.get_ptr(a));const auto prior=c.mmu.read8(a);need(!prior||prior==v);
            if(!prior&&post_stm_sc_report_dependency_private::initial_kind==1u)c.mmu.write8(a,v);
        }
#endif
#ifdef UNDERCOVER_POST_STM_SC_VERSION
        // Model original initialized data loading before any guest code,
        // never repair a live pointer or string at the version boundary.
        for(auto b:post_stm_sc_version_private::data){
            need(c.mmu.get_ptr(b.addr));
            const auto prior=c.mmu.read8(b.addr);
            need(!prior||prior==b.value);
            if(!prior)c.mmu.write8(b.addr,b.value);
        }
#endif
        // The focused fixture seeds the previously installed vector;
        // original cache flush and exception return execute below.
        for(unsigned i=0;i<v626::vector.size();++i){
            c.mmu.write8(OpenScRoute::Source+i,v626::vector[i]);
            c.mmu.write8(OpenScRoute::Vector+i,v626::vector[i]);
        }
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
        // Seed the authenticated prior OSExceptionInit postcondition.
        for(unsigned i=0;i<v1259::vector.size();++i)c.mmu.write8(ExternalVector+i,v1259::vector[i]);
#endif
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
        for(unsigned i=0;i<v1260::trampoline_words.size();++i)c.mmu.write32(v1260::trampoline+4u*i,v1260::trampoline_words[i]);
        c.mmu.write32(v1260::dispatcher,v1260::dispatcher_word);
        // Previously installed OS exception-handler metadata, not guest context.
        c.mmu.write32(0x80000048u,0x004e5090u);
        c.mmu.write32(0x80003010u,v1260::trampoline);
#endif
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
        for(auto w:v1261::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(W::Sda+v1261::counter_disp,0u);
#endif
#ifdef UNDERCOVER_V1266_JOINED_ACK
        for(auto w:v1255::words)c.mmu.write32(w.pc,w.word);
        c.mmu.write32(v1255::returned,v1266::return_word);
#endif
#ifdef UNDERCOVER_V1271_IPC_RETURN
        for(auto w:v1270::words)c.mmu.write32(w.pc,w.word);
#endif
#ifdef UNDERCOVER_V1282_REPLY_WAKE
        for(auto w:v1281::words)c.mmu.write32(w.pc,w.word);
#endif
#ifdef UNDERCOVER_V1289_WAKE_READY
        for(auto w:v1289::words)c.mmu.write32(w.pc,w.word);
#endif
#ifdef UNDERCOVER_V1316_REPLY_HELPER
        // The old reply fixture only seeded the guard's entry word.
        // Populate the authenticated expanded body before execution,
        // not at the failing instruction boundary.
        const auto helper=v1299::expected(W::Sda+v1292::counter_disp).helper;
        need(seed_private_expansion(c.mmu,v1299::words,helper,31u));
        for(auto w:v1299::words)need(c.mmu.read32(w.pc)==w.word);
        std::cout<<"V1323_HELPER_RAM_TRIAL n="<<trial<<" seeded_words=31 verified_route_words="<<v1299::words.size()<<"\n";
#endif
        #ifdef UNDERCOVER_V1328_IDLE_SELECTION
        need(seed_private_expansion(c.mmu,v1321::ram_words,v1321::clear_root,9u));
        need(verify_private_words(c.mmu,v1321::ram_words));
        #endif
        c.guest_flush_count=18000;
        const uint32_t lo=0x93380000u+trial*0x1000u,hi=0x93400000u;
        c.mmu.write32(W::Lo,lo);c.mmu.write32(W::Hi,hi);
        c.mmu.write32(W::Sda-16336u,lo);c.mmu.write32(W::Sda-3352u,hi);
        c.mmu.write32(W::MaskA,0xf7fff7f0u);c.mmu.write32(W::MaskB,0);
        // OSInterruptInit established this pointer in the verified V69 route.
        c.mmu.write32(W::IrqGlobal,W::Table);
        for(unsigned i=0;i<32;++i)c.mmu.write32(W::Table+4*i,i==27?0:0x80005000u+4*i);
        for(unsigned i=0;i<W::HeapLimit+2u;++i)c.mmu.write8(lo-1u+i,uint8_t(0x6b+trial));
        for(unsigned i=0;i<32;++i)c.gpr[i]=0x12340000u+trial*32u+i;
        c.gpr[1]=W::Stack;c.gpr[2]=0x80715ee0u;c.gpr[3]=0;c.gpr[13]=W::Sda;
        c.pc=c.lr=W::Call;c.msr=0x8032u;c.is_running=true;c.dispatch_saved_ctx=0;
#if defined(UNDERCOVER_FORMATTER_NESTED) && !defined(UNDERCOVER_FORMATTER_CONTROL)
        InitializedCellObservation nested_cell;
        const auto cell=formatter_nested_private::expected.boundary;
        need(nested_cell.begin(c,initial_data,cell.address,cell.width));
#endif
        const auto e=v624::expected_client.edges[0];
        PostAckIpcJoin w(v624::expected_client,{W::Call,W::Root,e.branch_word,e.entry_word});witness=&w;
        const bool begun=w.pre_dispatch(c,W::Call,true,device_ok(c));
        last_stage=w.client_stage();last_reason=w.cold_failure()?w.cold_failure():w.failure();
        if(!begun)throw WitnessFailure{};
        // The caller BL is authenticated but its effects are modeled here.
        // Every instruction in the original callee/dependency graph is native.
        ++c.inst_count;
        need(w.before_call(c,W::Call,e.branch_word,true,device_ok(c)));
        c.pc=W::Root;c.lr=W::Return;
        const auto before_callbacks=callbacks,before_writes=control_writes;
#ifdef UNDERCOVER_V1356_ALLOCATOR_METADATA
        AllocatorDescriptorWitness descriptor;allocator_descriptor=&descriptor;
        if(!descriptor.before_create(c,v1356::tables)){std::cout<<"V1356_DESCRIPTOR_REFUSAL stage=1\n";throw WitnessFailure{};}
#endif
        func_805194C4(c);
        need(c.pc==W::Return&&c.lr==W::Return&&c.is_running);
        const bool returned=w.continuation(c,c.pc,device_ok(c));last_stage=w.client_stage();last_reason=w.cold_failure()?w.cold_failure():w.failure();
        if(!returned)throw WitnessFailure{};
        need(w.stage()==5u&&w.client_stage()==19u&&w.heap_size()>0&&host.serviced_steps()==0);
#ifdef UNDERCOVER_V1356_ALLOCATOR_METADATA
        if(!descriptor.after_create(c,{lo,w.heap_size()})){std::cout<<"V1356_DESCRIPTOR_REFUSAL stage=2\n";throw WitnessFailure{};}
        std::cout<<"V1356_DESCRIPTOR_CREATED n="<<trial<<" original_create=1 unique=1\n";
#endif
        need(device_ok(c)&&ctl.issued_tokens()==3u&&!ctl.pending());
        need(callbacks==before_callbacks+2&&control_writes==before_writes+1);
        PostAckStmJoin stm(v629::expected_stm);stm_witness=&stm;
        PostAckOpenJoin open(v639::expected_open,v626::vector);open_witness=&open;open_polls=0;
#ifdef UNDERCOVER_V1358_OPEN_RETURN
        OpenReturnWitness open_tail(v1358::expected);open_return=&open_tail;
#ifdef UNDERCOVER_V1359_SECOND_OPEN
        StmSecondWitness stm_second(v1359::expected);second_open=&stm_second;
#ifdef UNDERCOVER_V1379_SECOND_RETURN
        OpenReturnWitness open_tail2(v1379::expected);second_open_capture=&open_tail2;
#endif
#endif
#endif
        need(stm.begin(c,w,device_ok(c)));
#ifdef UNDERCOVER_STM_FINAL_RETURN
        const auto stm_caller_gp=c.gpr;
        const auto stm_caller_cr=StmFinalReturnWitness::abi_cr(c);
#endif
        // Focused proof: model the caller bridge after the verified IPC
        // return. Execute the original STM prefix, not a synthetic
        // pathname selection. Do not claim the OSInit bridge executed.
        c.inst_count+=7;c.pc=StmPrefixWitness::Stm;c.lr=v629::expected_stm.stm.lr;
        bool stopped=false;
        try{run_game(c);}catch(const RequestReached&){stopped=true;}
        need(stopped&&stm.stage()==3u&&open.stage()==9u&&open.submit_at(c,device_ok(c))&&host.serviced_steps()==0);
        need(open.request()&&open.path_kind()==stm.path_kind()&&open_vectors==trial+1u&&open_returns==trial+1u);
        std::cout<<"V1256_OPEN_TRIAL n="<<trial<<" path="<<open.path_kind()<<" request=1 native_rfi=1 serviced=0\n";
        // Continue from the authenticated native submit entry, without
        // resetting memory or creating a replacement guest request.
        const auto kind=open.path_kind();
#ifdef UNDERCOVER_V1358_OPEN_RETURN
        if(!open_tail.capture_submit(c,device_ok(c)))open_return_refuse(2);
        open_return_device=kind==1u?StmIos::Device::Immediate:StmIos::Device::Event;
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
        auto second_expect=v639::expected_open;
        const auto second_call=std::find_if(v1359::words.begin(),v1359::words.end(),[](auto w){return w.pc==v1359::expected.call;});
        need(second_call!=v1359::words.end());
        second_expect.entry={v1359::expected.open,v1359::expected.call+4u,second_call->word,v1359::expected.entry_word};
        PostAckOpenJoin second_build(second_expect,v626::vector,kind);
        second_request=&second_build;second_request_polls=0;
#endif
#endif
        std::array<VectorEdge,v626::submit_edges.size()> edges{};
        for(unsigned i=0;i<edges.size();++i){auto e=v626::submit_edges[i];edges[i]={e.pc,e.lr,e.branch,e.entry};}
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
        PostAckSubmitJoin second_submission(edges,v626::vector,kind);
        second_submit=&second_submission;second_submit_cpu=&c;second_submit_polls=0;
#ifdef UNDERCOVER_V1378_SECOND_FREE
        SubmitResumeWitness submit_cont2(v1344::expected,1u);second_resume_capture=&submit_cont2;
#endif
#ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
        IdleContextReuse idle_reuse;
#endif
#endif
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
        SubmitResumeWitness submit_cont(v1344::expected);
        submit_resume=&submit_cont;
        if(!submit_cont.capture(c,device_ok(c)))submit_resume_refuse(6);
#endif
        PostAckSubmitJoin next(edges,v626::vector);
        need(next.begin(c,open,device_ok(c)));
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
        AllocatorReleaseWitness allocator(v1344::release_expected);allocator_release=&allocator;
        allocator_heap={lo,w.heap_size()};allocator_request=next.request();
#endif
        open_witness=nullptr;stm_witness=nullptr;
        submit_host=&host;submit_join=&next;submit_cpu=&c;submit_stage=1;submit_polls=0;
        bool acked=false;
        try{run_game(c);}catch(const SubmitStop&){acked=true;}
        need(acked&&submit_stage==9&&submit_acks==trial+1&&submit_vectors==trial+1&&host.serviced_steps()==1&&device_ok(c));
        need(ctl.issued_tokens()==3u&&!ctl.pending());
        std::cout<<"V1256_SUBMIT_TRIAL n="<<trial<<" path="<<kind<<" ack=1 reply=0 si_quiescent=1\n";
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
        constexpr uint32_t SubmitResume=0x805197d8u;
        const auto submit_word=std::find_if(v626::words.begin(),v626::words.end(),[](auto w){return w.pc==SubmitResume;});
        need(submit_word!=v626::words.end());
        SleepExitWitness exited({PostAckSleepJoin::Sleep,SubmitResume,submit_word->word,v1252::edges[2],v1321::ram_words});
        sleep_exit=&exited;
        if(!exited.capture(c,device_ok(c)))sleep_exit_refuse(7);
#endif
        PostAckSleepJoin sleep(v1252::edges);
        need(sleep.begin(c,next,device_ok(c)));
        submit_host=nullptr;submit_join=nullptr;submit_cpu=nullptr;
        sleep_join=&sleep;bool waiting=false;
        try{run_game(c);}catch(const SleepStop&){waiting=true;}
        need(waiting&&sleep.stage()==4u&&sleep.select_at(c,device_ok(c))&&host.serviced_steps()==1u&&sleep_count==trial+1u);
        std::cout<<"V1252_SLEEP_TRIAL n="<<trial<<" waiting=1 queue=1 pending_ack=1 reply=0\n";
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
        SleepResumeWitness resumed({Q::Select,PostAckSleepJoin::Sleep,0x80529818u,0x8052a4fcu,v1252::edges[2],v1321::ram_words});
        sleep_resume=&resumed;
        if(!resumed.capture(c,device_ok(c)))sleep_resume_refuse(7);
#endif
        PostAckSchedulerJoin sched(v1256::edges,v1256::indirect,v1256::resume,v1256::resume_word);
        need(sched.begin(c,sleep,device_ok(c)));sleep_join=nullptr;sched_join=&sched;
#ifdef UNDERCOVER_V1315_COOP_SAVE
        CooperativeSaveLane save_lane(v1314::expected(Q::Thread));coop_save=&save_lane;
#endif
        bool enabled=false;
        try{run_game(c);}catch(const SchedulerStop&){enabled=true;}
        need(enabled&&sched.stage()==7u&&scheduler_count==trial+1u&&host.serviced_steps()==1u&&device_ok(c));
        need(host.exception_pending(c.msr)&&c.pc==v1256::resume&&(c.msr&0x8000u));
#ifdef UNDERCOVER_V1315_COOP_SAVE
        if(!save_lane.preserved(c,device_ok(c))||save_lane.visits()!=v1314::words.size())coop_save_refuse(3);
        ++coop_save_count;coop_save=nullptr;
#ifdef UNDERCOVER_V1320_SAVE_CONTINUITY
        coop_saved=&save_lane;
#endif
        std::cout<<"V1315_SAVE_TRIAL n="<<trial<<" native_save=1 original_return=1 saved_abi=1 gqr=1 idle_preserved=1\n";
#endif
        std::cout<<"V1256_SCHED_TRIAL n="<<trial<<" saved=1 idle=1 enabled=1 pending_ack=1 irq_entered=0\n";
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
        const auto before_irq=c.inst_count;
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
        irq_capture=ExternalReturnWitness{};ipc_vector=SecondVectorWitness(ipc_vector_expected);
        need(irq_capture.capture(c,cause.load(),mask.load(),H::PI_HOLLYWOOD));
        vector_mail=host.cold_ipc_snapshot();vector_tick=c.inst_count;
#endif
        need(enter_scheduler_ipc_irq(c,host,v1259::vector,next.request()&0x3fffffffu));
        need(c.pc==ExternalVector&&c.srr0==v1256::resume&&c.inst_count==before_irq&&
             c.mmu.read32(Q::Active)==Q::Idle&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep.queue())==Q::Thread&&c.mmu.read32(sleep.queue()+4u)==Q::Thread&&
             host.serviced_steps()==1u&&device_ok(c));
        ++irq_count;
        std::cout<<"V1259_IRQ_TRIAL n="<<trial<<" entered=1 srr=1 registers=1 pending_ack=1 vector_executed=0\n";
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
        vector_active=true;sched_join=nullptr;bool dispatched=false;
        try{run_game(c);}catch(const VectorStop&){dispatched=true;}
        need(dispatched&&ipc_vector.stage()==3u&&vector_count==trial+1u&&vector_held(c)&&
             c.pc==v1260::dispatcher&&irq_capture.saved_integer(c,Q::Idle).ok()&&
             c.mmu.read32(Q::Active)==Q::Idle&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep.queue())==Q::Thread&&c.mmu.read32(sleep.queue()+4u)==Q::Thread);
        vector_active=false;
        std::cout<<"V1260_VECTOR_TRIAL n="<<trial<<" saved_fields=38 original_vector=1 trampoline=1 pending_ack=1 dispatcher_executed=0\n";
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
        IpcDispatchWitness dispatch({v1261::code,v1261::handler,Q::Idle,Q::Thread,W::Table,W::IrqGlobal,W::Sda+v1261::counter_disp});
        ipc_dispatch=&dispatch;dispatch_queue=sleep.queue();bool handler_reached=false;
        try{run_game(c);}catch(const DispatchStop&){handler_reached=true;}
        need(handler_reached&&dispatch.stage()==6u&&dispatch_count==trial+1u&&
             dispatch.cause_reads()&&dispatch.mask_reads()&&c.pc==v1261::handler&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot())&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&device_ok(c));
        ipc_dispatch=nullptr;
        std::cout<<"V1261_DISPATCH_TRIAL n="<<trial<<" original_dispatcher=1 index=27 context=1 pi_reads=1 handler_entry=1 handler_executed=0\n";
#ifdef UNDERCOVER_V1266_JOINED_ACK
        JoinedIpcAck joined(v1255::handler,v1255::returned,v1266::return_word,v1266::final_blr,Q::Idle,Q::Thread,v1255::edges,v1255::polls);
        need(joined.begin(c,dispatch,irq_capture,sleep.queue(),next.request()&0x3fffffffu,kind,device_ok(c)));
        joined_ack=&joined;joined_cpu=&c;
        bool ack_returned=false;
        try{run_game(c);}catch(const AckReturned&){ack_returned=true;}
        need(ack_returned&&joined.stage()==2u&&host.serviced_steps()==1u);
        if(!joined.publish(c,device_ok(c)))joined_refuse(7);
        need(joined.stage()==3u&&host.serviced_steps()==2u&&c.pc==v1255::returned&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&c.mmu.read16(Q::Thread+712u)==4u);
        ++joined_count;joined_ack=nullptr;joined_cpu=nullptr;
        std::cout<<"V1266_ACK_TRIAL n="<<trial<<" handler_return=1 guest_w1c=1 native_reply=1 waiting=1 saved_fields=38\n";
#ifdef UNDERCOVER_V1271_IPC_RETURN
        // Preserve the live handler return and native reply. The original
        // dispatcher suffix executes with no host scheduler/context edits.
        LiveEpilogueWitness live(v1270::expected(Q::Idle));
        epilogue=&live;epilogue_host=&host;reply_mail=host.cold_ipc_snapshot();
        reply_request=next.request()&0x3fffffffu;reply_queue=sleep.queue();
        epilogue_tick=c.inst_count;reply_capture=ExternalReturnWitness{};
        bool reentered=false;
        try{run_game(c);}catch(const ReplyEntered&){reentered=true;}
        need(reentered&&live.stage()==3u&&rfi_count==trial+1u&&irq_capture.stage()==3u&&
             reply_capture.stage()==1u&&reply_held(c)&&host.serviced_steps()==2u);
        epilogue=nullptr;epilogue_host=nullptr;
        std::cout<<"V1271_RFI_TRIAL n="<<trial<<" original_scheduler=1 native_rfi=1 restored=1 reply_irq=1 waiting=1\n";
        // The second vector uses its own capture, not the previous saved
        // context as an artificial substitute for native vector stores.
        irq_capture=reply_capture;ipc_vector=SecondVectorWitness(ipc_vector_expected);
        vector_mail=host.cold_ipc_snapshot();vector_tick=c.inst_count;
        reply_vector=true;vector_active=true;bool reply_dispatched=false;
        try{run_game(c);}catch(const VectorStop&){reply_dispatched=true;}
        need(reply_dispatched&&ipc_vector.stage()==3u&&reply_vector_count==trial+1u&&
             vector_held(c)&&c.pc==v1260::dispatcher&&irq_capture.saved_integer(c,Q::Idle).ok()&&
             c.mmu.read16(Q::Thread+712u)==4u&&c.mmu.read32(sleep.queue())==Q::Thread&&
             c.mmu.read32(sleep.queue()+4u)==Q::Thread&&host.serviced_steps()==2u);
        vector_active=false;reply_vector=false;
        std::cout<<"V1271_REPLY_VECTOR_TRIAL n="<<trial<<" original_vector=1 trampoline=1 saved_fields=38 pending_reply=1 dispatcher_executed=0\n";
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
        IpcDispatchWitness second({v1261::code,v1261::handler,Q::Idle,Q::Thread,W::Table,W::IrqGlobal,W::Sda+v1261::counter_disp});
        need(c.mmu.read32(W::Sda+v1261::counter_disp)==0u);
        ipc_dispatch=&second;dispatch_queue=sleep.queue();second_dispatch=true;
        bool second_reached=false;
        try{run_game(c);}catch(const DispatchStop&){second_reached=true;}
        need(second_reached&&second.stage()==6u&&second.reply_mode()&&second_dispatch_count==trial+1u&&
             second.cause_reads()&&second.mask_reads()&&c.pc==v1261::handler&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot())&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&device_ok(c));
        ipc_dispatch=nullptr;second_dispatch=false;
        std::cout<<"V1275_REPLY_DISPATCH_TRIAL n="<<trial<<" dispatcher=1 index=27 handler_entry=1 pending_reply=1\n";
        constexpr uint32_t ReadLeaf=0x8051905cu,Reply=0x805190c0u,ReplyReturn=0x80519354u;
        auto match=[](const auto& e){return e.pc==Reply&&e.lr==ReplyReturn;};
        need(std::count_if(v1255::edges.begin(),v1255::edges.end(),match)==1);
        const auto reply_edge=*std::find_if(v1255::edges.begin(),v1255::edges.end(),match);
#ifdef UNDERCOVER_V1300_REPLY_RETURN
        const auto handler_abi=ReplyReturnAbi::capture(c);
#endif
        JoinedIpcReplyEntry entry(v1255::handler,ReadLeaf,reply_edge,Q::Idle,Q::Thread,v1255::edges,v1255::polls);
        need(entry.begin(c,second,irq_capture,sleep.queue(),reply_request,device_ok(c)));
        reply_entry=&entry;reply_cpu=&c;bool processor_reached=false;
        try{run_game(c);}catch(const ReplyProcessorReached&){processor_reached=true;}
        need(processor_reached&&entry.stage()==2u&&entry.reads()&&reply_entry_count==trial+1u&&
             c.pc==Reply&&c.lr==ReplyReturn&&host.serviced_steps()==2u&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot())&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep.queue())==Q::Thread&&c.mmu.read32(sleep.queue()+4u)==Q::Thread);
        reply_entry=nullptr;reply_cpu=nullptr;
        std::cout<<"V1275_REPLY_ENTRY_TRIAL n="<<trial<<" original_handler=1 reply_processor_entry=1 pending_reply=1 waiting=1\n";
#ifdef UNDERCOVER_V1282_REPLY_WAKE
        // Continue the live processor call. No scheduler registers,
        // request buffer or queue links are changed by the host.
#ifdef UNDERCOVER_V1300_REPLY_RETURN
        const auto processor_abi=ReplyReturnAbi::capture(c);
#endif
        ReplyProcessorWitness body(v1281::expected(Q::Idle,Q::Thread));
        reply_body=&body;body_cpu=&c;
        if(!body.begin(c,entry,irq_capture,sleep.queue(),reply_request,device_ok(c)))body_refuse(6);
        bool wake_reached=false;
        try{run_game(c);}catch(const WakeEntryReached&){wake_reached=true;}
        const auto consumed=host.cold_ipc_snapshot();
        need(wake_reached&&body.stage()==2u&&wake_entry_count==trial+1u&&body.arm_reads()&&body.invalidations()&&
             c.pc==0x8052a51cu&&c.lr==0x805192d4u&&c.gpr[3]==sleep.queue()&&
             !(consumed.control&(M::X1|M::Y1|M::Y2))&&consumed.steps==2u&&!consumed.replies&&
             consumed.ppc==reply_request&&consumed.arm==reply_request&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep.queue())==Q::Thread&&c.mmu.read32(sleep.queue()+4u)==Q::Thread&&
             device_ok(c));
        reply_body=nullptr;body_cpu=nullptr;
        std::cout<<"V1282_WAKE_ENTRY_TRIAL n="<<trial<<" original_processor=1 armmsg=1 native_dcbi=1 y1_w1c=1 queue=1 wake_executed=0\n";
#ifdef UNDERCOVER_V1289_WAKE_READY
        WakeReadyWitness ready(v1289::expected(Q::Idle,Q::Thread));wake_ready=&ready;
        if(!ready.begin(c,body,irq_capture,sleep.queue(),device_ok(c)))wake_refuse(6);
        bool selected=false;try{run_game(c);}catch(const ReadyReached&){selected=true;}
        need(selected&&ready.stage()==2u&&ready_count==trial+1u&&ready.ready_queue()&&
             c.pc==Q::Select&&c.lr==0x8052a5f0u&&c.gpr[3]==0u&&host.serviced_steps()==2u&&
             c.mmu.read16(Q::Thread+712u)==1u&&c.mmu.read32(sleep.queue())==0u&&
             c.mmu.read32(sleep.queue()+4u)==0u&&irq_capture.saved_integer(c,Q::Idle).ok()&&device_ok(c));
        wake_ready=nullptr;
        std::cout<<"V1289_READY_TRIAL n="<<trial<<" original_wake=1 nested_disable=1 drained=1 ready=1 enrolled=1 select_executed=0\n";
#ifdef UNDERCOVER_V1292_NESTED_WAKE
        const int64_t nested_counter=int64_t(c.gpr[13])+v1292::counter_disp;
        need(nested_counter>=0x80000000ll&&nested_counter<=0x817ffffcll);
        NestedWakeReturnWitness nested(v1292::expected(Q::Idle,uint32_t(nested_counter)));nested_wake=&nested;
        if(!nested.begin(c,ready,irq_capture,sleep.queue(),device_ok(c)))nested_refuse(6);
        bool wake_returned=false;try{run_game(c);}catch(const NestedReturned&){wake_returned=true;}
        need(wake_returned&&nested.stage()==2u&&nested_count==trial+1u&&c.pc==0x805192d4u&&
             c.lr==c.pc&&ready.ready_held(c,device_ok(c))&&host.serviced_steps()==2u);
        nested_wake=nullptr;
        std::cout<<"V1292_NESTED_TRIAL n="<<trial<<" original_select_return=1 original_restore=1 original_wake_return=1 ready=1\n";
#ifdef UNDERCOVER_V1300_REPLY_RETURN
        ReplyReturnWitness completed(v1299::expected(uint32_t(nested_counter)));
        reply_return=&completed;return_cpu=&c;
        if(!completed.begin(c,body,ready,nested,irq_capture,sleep.queue(),reply_request,handler_abi,processor_abi,device_ok(c)))return_refuse(6);
        bool handler_returned=false;try{run_game(c);}catch(const ReplyHandlerReturned&){handler_returned=true;}
        need(handler_returned&&completed.returned(c,device_ok(c))&&completed.x2_writes()==1u&&return_count==trial+1u&&
             c.pc==v1255::returned&&c.lr==c.pc&&host.serviced_steps()==2u&&
             !(cause.load()&mask.load())&&ready.ready_context_held(c,device_ok(c)));
#ifdef UNDERCOVER_V1316_REPLY_HELPER
        need(completed.helper_returns()==1u);
#endif
        reply_return=nullptr;return_cpu=nullptr;
        std::cout<<"V1300_RETURN_TRIAL n="<<trial<<" original_processor_return=1 original_handler_return=1 latch_clear=1 ready=1\n";
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
        ReadyIdleReturnJoin idle_join;LiveEpilogueWitness idle(v1270::expected(Q::Idle));
        ready_idle=&idle_join;idle_epilogue=&idle;idle_tick=c.inst_count;
        if(!idle_join.begin(c,completed,ready,irq_capture,device_ok(c)))idle_return_refuse(6);
        bool idle_returned=false;try{run_game(c);}catch(const IdleRfiReturned&){idle_returned=true;}
        need(idle_returned&&idle_join.resumed_idle(c,device_ok(c))&&idle.stage()==4u&&
             idle_return_count==trial+1u&&c.pc==v1256::resume&&(c.msr&0x8000u)&&
             host.serviced_steps()==2u&&!(cause.load()&mask.load()));
        ready_idle=nullptr;idle_epilogue=nullptr;
        std::cout<<"V1305_IDLE_TRIAL n="<<trial<<" original_epilogue=1 native_rfi=1 idle_restored=1 ready_preserved=1\n";
#ifdef UNDERCOVER_V1320_SAVE_CONTINUITY
        need(coop_saved==&save_lane&&save_lane.preserved(c,device_ok(c))&&coop_idle_count==trial);
        ++coop_idle_count;
        std::cout<<"V1320_IDLE_SAVE_TRIAL n="<<trial<<" native_save=1 complete_context=1 second_idle_rfi=1 ready=1\n";
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
        IdleSelectionWitness selection(v1321::selection(Q::Thread,Q::Idle,uint32_t(nested_counter)));
        IdleRouteWitness route({Q::Enable,v1256::resume,Q::Select,0x80529864u,v1321::direct[3].pc,
            v1321::ram_words,v1321::direct,v1321::callbacks});
        selection_witness=&selection;selection_route=&route;
        if(!selection.begin(c,idle_join,device_ok(c))||!route.begin(c,device_ok(c)))selection_refuse(7);
#ifdef UNDERCOVER_V1334_COOP_LOAD
        CooperativeLoadLane load(v1321::load());coop_load=&load;load_save=&save_lane;
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
        bool allocator_returned=false;
#ifdef UNDERCOVER_V1358_OPEN_RETURN
#ifdef UNDERCOVER_V1359_SECOND_OPEN
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
        try{run_game(c);}catch(const SecondSubmitAcked&){allocator_returned=true;}
        need(allocator_returned&&second_submission.ack_at(c,second_submit_held(c))&&second_submit_count==trial+1u&&
            second_submit_vectors==trial+1u&&second_submit_returns==trial+1u&&
            second_submission.writes()==2u&&second_request_count==trial+1u&&second_request_vectors==trial+1u&&
            second_request_returns==trial+1u&&second_open_count==trial+1u&&open_return_count==trial+1u&&host.serviced_steps()==3u&&
            host.exception_pending(0x8000u)&&!host.exception_pending(c.msr));
        std::cout<<"V1366_SUBMIT_TRIAL n="<<trial<<" submitted=1 ack=1 second_fd=1 first_fd_held=1 native_rfi=1 reply_pending=1\n";
        #ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
        if(!idle_reuse.capture(c,second_submission,second_submit_held(c))){std::cout<<"V1368_REUSE_REFUSAL stage=1\n";throw WitnessFailure{};}
        #endif
        second_submit_active=false;second_submit=nullptr;second_submit_cpu=nullptr;
#else
        try{run_game(c);}catch(const SecondRequestReached&){allocator_returned=true;}
        need(allocator_returned&&second_build.submit_at(c,second_request_held(c))&&
            descriptor.identity_after_release(c)&&second_request_count==trial+1u&&
            second_request_vectors==trial+1u&&second_request_returns==trial+1u&&
            second_open_count==trial+1u&&open_return_count==trial+1u&&host.serviced_steps()==2u);
        std::cout<<"V1364_REQUEST_TRIAL n="<<trial<<" request=1 opposite_path=1 native_rfi=1 first_fd_held=1 reused="<<(second_build.request()==open.request())<<"\n";
 #endif
        second_request_active=false;second_request=nullptr;
#else
        try{run_game(c);}catch(const SecondOpenReached&){allocator_returned=true;}
        need(allocator_returned&&stm_second.reached(c,open_return_held(c),open_descriptor(c))&&second_open_count==trial+1u&&open_return_count==trial+1u);
#endif
        std::cout<<"V1359_SECOND_TRIAL n="<<trial<<" second_entry=1 opposite_path=1 descriptor_store=1 first_fd_held=1\n";
        second_open_active=false;second_open=nullptr;
#else
        try{run_game(c);}catch(const OpenReturned&){allocator_returned=true;}
        need(allocator_returned&&open_tail.returned(c,open_return_held(c),open_descriptor(c))&&open_return_count==trial+1u);
#endif
        std::cout<<"V1358_OPEN_TRIAL n="<<trial<<" submit_return=1 open_return=1 stm_resume=1 descriptor=1\n";
        open_return_active=false;open_return=nullptr;open_return_device=StmIos::Device::None;
#else
        try{run_game(c);}catch(const AllocatorReturned&){allocator_returned=true;}
        need(allocator_returned&&allocator.returned(c,allocator_held(c)));
#endif
        need(selection_count==trial+1u&&
            load_count==trial+1u&&resumed_sleep_count==trial+1u&&sleep_exit_count==trial+1u&&release_count==trial+1u&&
            allocator_count==trial+1u);
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
        need(host.serviced_steps()==3u&&(cause.load()&mask.load())==H::PI_HOLLYWOOD);
#else
        need(host.serviced_steps()==2u&&!(cause.load()&mask.load()));
#endif
#ifdef UNDERCOVER_V1356_ALLOCATOR_METADATA
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
        // The completed descriptor and full heap shadow were verified
        // at the inline first return and again at second Open entry.
        if(!descriptor.identity_after_release(c)){std::cout<<"V1356_DESCRIPTOR_REFUSAL stage=4\n";throw WitnessFailure{};}
#else
        if(!descriptor.returned(c,allocator.metadata_stores())){std::cout<<"V1356_DESCRIPTOR_REFUSAL stage=4\n";throw WitnessFailure{};}
#endif
        std::cout<<"V1356_DESCRIPTOR_RETURN n="<<trial<<" exact_field=1 shadow=1 stores="<<allocator.metadata_stores()<<'\n';
        allocator_descriptor=nullptr;
#endif
        allocator_active=false;allocator_release=nullptr;
        std::cout<<"V1352_ALLOCATOR_TRIAL n="<<trial<<" native_free=1 heap_shadow=1 caller_abi=1 inline_return=1 stores="<<allocator.stores()<<" heap="<<allocator.heap_stores()<<'\n';
#else
        bool release_reached=false;try{run_game(c);}catch(const ReleaseReached&){release_reached=true;}
        need(release_reached&&submit_cont.release_at(c,submit_held(c))&&selection_count==trial+1u&&
            load_count==trial+1u&&resumed_sleep_count==trial+1u&&sleep_exit_count==trial+1u&&release_count==trial+1u&&
            host.serviced_steps()==2u&&!(cause.load()&mask.load()));
#endif
        submit_resume_active=false;submit_resume=nullptr;
        std::cout<<"V1344_SUBMIT_TRIAL n="<<trial<<" sleep_return=1 outer_restore=1 reply_held=1 free_entry=1\n";
#else
        bool sleep_exited=false;try{run_game(c);}catch(const SleepExited&){sleep_exited=true;}
        need(sleep_exited&&exited.returned(c,load_held(c))&&selection_count==trial+1u&&
            load_count==trial+1u&&resumed_sleep_count==trial+1u&&sleep_exit_count==trial+1u&&
            host.serviced_steps()==2u&&!(cause.load()&mask.load()));
#endif
        exit_active=false;sleep_exit=nullptr;
        std::cout<<"V1340_EXIT_TRIAL n="<<trial<<" nested_restore=1 sleep_return=1 submit_resume=1 caller_abi=1\n";
#else
        bool sleep_reached=false;try{run_game(c);}catch(const SleepRestoreReached&){sleep_reached=true;}
        need(sleep_reached&&resumed.restored_sleep_at(c,load_held(c))&&selection_count==trial+1u&&
            load_count==trial+1u&&resumed_sleep_count==trial+1u&&host.serviced_steps()==2u&&
            !(cause.load()&mask.load()));
#endif
        sleep_active=false;sleep_resume=nullptr;
        std::cout<<"V1336_SLEEP_TRIAL n="<<trial<<" native_rfi=1 select_return=1 sleep_stack=1 saved_abi=1 restore_entry=1\n";
#else
        bool cooperative_returned=false;try{run_game(c);}catch(const CooperativeReturned&){cooperative_returned=true;}
        need(cooperative_returned&&load.restored(c,load_held(c))&&selection_count==trial+1u&&
            load_count==trial+1u&&host.serviced_steps()==2u&&!(cause.load()&mask.load())&&
            c.pc==save_lane.expectation().geometry.save_return&&!(c.msr&0x8000u));
#endif
        load_active=false;coop_load=nullptr;load_save=nullptr;coop_saved=nullptr;
        std::cout<<"V1334_LOAD_TRIAL n="<<trial<<" original_loader=1 native_rfi=1 saved_abi=1 gqr=1 cooperative_return=1\n";
#else
        bool loader_reached=false;try{run_game(c);}catch(const LoaderReached&){loader_reached=true;}
        need(loader_reached&&route.loader_at(c,device_ok(c))&&selection.loader_ready(c,device_ok(c))&&
            selection_count==trial+1u&&save_lane.preserved(c,device_ok(c))&&host.serviced_steps()==2u&&
            !(cause.load()&mask.load()));
#endif
        selection_route=nullptr;selection_witness=nullptr;
        std::cout<<"V1328_SELECTION_TRIAL n="<<trial<<" original_clear=1 original_callback=1 original_set=1 loader_entry=1 preserved=1\n";
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
#ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
        // All first-transaction witnesses were checked at their own
        // frontiers. Retire them before the second save changes OSContext.
        second_scheduler_lane=true;coop_saved=nullptr;
        const OpenTransactionEpoch epoch(kind);
        const auto second_held=[&]{return raw_device_ok(c)&&epoch.acknowledged_descriptors(3u-kind)&&
            host.serviced_steps()==3u&&descriptor.identity_after_release(c);};
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
        SleepExitWitness exited2({PostAckSleepJoin::Sleep,SubmitResume,submit_word->word,v1252::edges[2],v1321::ram_words});
        sleep_exit=&exited2;
        if(!exited2.capture(c,second_held()))sleep_exit_refuse(7);
#endif
        PostAckSleepJoin sleep2(v1252::edges);
        if(!idle_reuse.preserved(c,second_held())||!sleep2.begin(c,second_submission,second_held())){
            std::cout<<"V1368_REUSE_REFUSAL stage=2\n";throw WitnessFailure{};
        }
        sleep_join=&sleep2;bool waiting2=false;
        try{run_game(c);}catch(const SleepStop&){waiting2=true;}
        need(waiting2&&sleep2.select_at(c,second_held())&&second_sleep_count==trial+1u);
        std::cout<<"V1368_SLEEP_TRIAL n="<<trial<<" waiting=1 queue=1 ack_held=1\n";
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
        SleepResumeWitness resumed2({Q::Select,PostAckSleepJoin::Sleep,0x80529818u,0x8052a4fcu,v1252::edges[2],v1321::ram_words});
        sleep_resume=&resumed2;
        if(!resumed2.capture(c,second_held()))sleep_resume_refuse(7);
#endif
        PostAckSchedulerJoin sched2(v1256::edges,v1256::indirect,v1256::resume,v1256::resume_word);
        if(!sched2.begin_reused(c,sleep2,idle_reuse,second_held())){
            std::cout<<"V1368_REUSE_REFUSAL stage=3\n";throw WitnessFailure{};
        }
        sleep_join=nullptr;sched_join=&sched2;
        CooperativeSaveLane save2(v1314::expected(Q::Thread));coop_save=&save2;
        bool enabled2=false;
        try{run_game(c);}catch(const SchedulerStop&){enabled2=true;}
        need(enabled2&&sched2.stage()==7u&&second_scheduler_count==trial+1u&&
            second_held()&&save2.preserved(c,second_held())&&save2.visits()==v1314::words.size()&&
            host.exception_pending(c.msr)&&c.pc==v1256::resume&&(c.msr&0x8000u));
        ++second_save_count;coop_save=nullptr;
        std::cout<<"V1368_SCHED_TRIAL n="<<trial<<" saved=1 idle_reused=1 enabled=1 pending_ack=1\n";
#ifdef UNDERCOVER_V1370_SECOND_REPLY
        second_irq_kind=kind;coop_saved=&save2;
        const auto irq_tick2=c.inst_count;
        irq_capture=ExternalReturnWitness{};ipc_vector=SecondVectorWitness(ipc_vector_expected);
        need(irq_capture.capture(c,cause.load(),mask.load(),H::PI_HOLLYWOOD));
        vector_mail=host.cold_ipc_snapshot();vector_tick=c.inst_count;
        const uint32_t req2=second_submission.request()&0x3fffffffu;
        need(enter_scheduler_ipc_irq(c,host,v1259::vector,req2,kind));
        need(c.pc==ExternalVector&&c.srr0==v1256::resume&&c.inst_count==irq_tick2&&
             c.mmu.read32(Q::Active)==Q::Idle&&c.mmu.read16(Q::Thread+712u)==4u&&
             c.mmu.read32(sleep2.queue())==Q::Thread&&c.mmu.read32(sleep2.queue()+4u)==Q::Thread&&
             host.serviced_steps()==3u&&device_ok(c));
        ++second_ack_irq_count;
        vector_active=true;sched_join=nullptr;
        bool ack_vector2=false;try{run_game(c);}catch(const VectorStop&){ack_vector2=true;}
        need(ack_vector2&&ipc_vector.stage()==3u&&second_ack_vector_count==trial+1u&&vector_held(c)&&
             c.pc==v1260::dispatcher&&irq_capture.saved_integer(c,Q::Idle).ok());
        vector_active=false;
        IpcDispatchWitness ack_dispatch2({v1261::code,v1261::handler,Q::Idle,Q::Thread,W::Table,W::IrqGlobal,W::Sda+v1261::counter_disp},kind);
        ipc_dispatch=&ack_dispatch2;dispatch_queue=sleep2.queue();second_dispatch=false;
        bool ack_handler2=false;try{run_game(c);}catch(const DispatchStop&){ack_handler2=true;}
        need(ack_handler2&&ack_dispatch2.stage()==6u&&second_ack_dispatch_count==trial+1u&&
             ack_dispatch2.cause_reads()&&ack_dispatch2.mask_reads()&&c.pc==v1261::handler&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot())&&device_ok(c));
        ipc_dispatch=nullptr;
        JoinedIpcAck ack_join2(v1255::handler,v1255::returned,v1266::return_word,v1266::final_blr,
            Q::Idle,Q::Thread,v1255::edges,v1255::polls,kind);
        need(ack_join2.begin(c,ack_dispatch2,irq_capture,sleep2.queue(),req2,3u-kind,device_ok(c)));
        joined_ack=&ack_join2;joined_cpu=&c;
        bool ack_ret2=false;try{run_game(c);}catch(const AckReturned&){ack_ret2=true;}
        need(ack_ret2&&ack_join2.stage()==2u&&host.serviced_steps()==3u);
        if(!ack_join2.publish(c,device_ok(c)))joined_refuse(7);
        need(ack_join2.stage()==3u&&host.serviced_steps()==4u&&c.pc==v1255::returned&&
             irq_capture.saved_integer(c,Q::Idle).ok()&&c.mmu.read16(Q::Thread+712u)==4u&&
             epoch.acknowledged_descriptors(3u-kind)&&host.physical_ram().read32(req2+4u)==1u);
        ++second_ack_return_count;joined_ack=nullptr;joined_cpu=nullptr;
        std::cout<<"V1370_ACK_TRIAL n="<<trial<<" original_vector=1 original_dispatch=1 original_ack_return=1 native_reply=1 fd=1\n";
        LiveEpilogueWitness live2(v1270::expected(Q::Idle));
        epilogue=&live2;epilogue_host=&host;reply_mail=host.cold_ipc_snapshot();
        reply_request=req2;reply_queue=sleep2.queue();epilogue_tick=c.inst_count;reply_capture=ExternalReturnWitness{};
        bool reply_entered2=false;try{run_game(c);}catch(const ReplyEntered&){reply_entered2=true;}
        need(reply_entered2&&live2.stage()==3u&&second_reply_rfi_count==trial+1u&&irq_capture.stage()==3u&&
             reply_capture.stage()==1u&&reply_held(c)&&host.serviced_steps()==4u);
        epilogue=nullptr;epilogue_host=nullptr;
        irq_capture=reply_capture;ipc_vector=SecondVectorWitness(ipc_vector_expected);
        vector_mail=host.cold_ipc_snapshot();vector_tick=c.inst_count;reply_vector=true;vector_active=true;
        bool reply_vec2=false;try{run_game(c);}catch(const VectorStop&){reply_vec2=true;}
        need(reply_vec2&&ipc_vector.stage()==3u&&second_reply_vector2_count==trial+1u&&
             vector_held(c)&&c.pc==v1260::dispatcher&&irq_capture.saved_integer(c,Q::Idle).ok()&&host.serviced_steps()==4u);
        vector_active=false;reply_vector=false;
        IpcDispatchWitness reply_dispatch2({v1261::code,v1261::handler,Q::Idle,Q::Thread,W::Table,W::IrqGlobal,W::Sda+v1261::counter_disp},kind);
        need(c.mmu.read32(W::Sda+v1261::counter_disp)==0u);
        ipc_dispatch=&reply_dispatch2;dispatch_queue=sleep2.queue();second_dispatch=true;
        bool reply_handler2=false;try{run_game(c);}catch(const DispatchStop&){reply_handler2=true;}
        need(reply_handler2&&reply_dispatch2.stage()==6u&&reply_dispatch2.reply_mode()&&second_reply_dispatch2_count==trial+1u&&
             reply_dispatch2.cause_reads()&&reply_dispatch2.mask_reads()&&c.pc==v1261::handler&&device_ok(c)&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot()));
        ipc_dispatch=nullptr;second_dispatch=false;
        constexpr uint32_t Read2=0x8051905cu,Reply2=0x805190c0u,Return2=0x80519354u;
        auto edge2=[](auto e){return e.pc==Reply2&&e.lr==Return2;};
        need(std::count_if(v1255::edges.begin(),v1255::edges.end(),edge2)==1);
        #ifdef UNDERCOVER_V1374_SECOND_RESTORE
        const auto handler_abi2=ReplyReturnAbi::capture(c);
        #endif
        JoinedIpcReplyEntry entry2(v1255::handler,Read2,*std::find_if(v1255::edges.begin(),v1255::edges.end(),edge2),
            Q::Idle,Q::Thread,v1255::edges,v1255::polls);
        need(entry2.begin(c,reply_dispatch2,irq_capture,sleep2.queue(),req2,device_ok(c)));
        reply_entry=&entry2;reply_cpu=&c;
        bool processor2=false;try{run_game(c);}catch(const ReplyProcessorReached&){processor2=true;}
        need(processor2&&entry2.stage()==2u&&entry2.reads()&&second_reply_entry2_count==trial+1u&&
             c.pc==Reply2&&c.lr==Return2&&host.serviced_steps()==4u&&
             same_scheduler_ipc_snapshot(vector_mail,host.cold_ipc_snapshot())&&device_ok(c));
        reply_entry=nullptr;reply_cpu=nullptr;
        #ifdef UNDERCOVER_V1374_SECOND_RESTORE
        const auto processor_abi2=ReplyReturnAbi::capture(c);
        #endif
        ReplyProcessorWitness body2(v1281::expected(Q::Idle,Q::Thread),kind);
        reply_body=&body2;body_cpu=&c;
        if(!body2.begin(c,entry2,irq_capture,sleep2.queue(),req2,device_ok(c)))body_refuse(6);
        bool wake2=false;try{run_game(c);}catch(const WakeEntryReached&){wake2=true;}
        const auto consumed2=host.cold_ipc_snapshot();
        need(wake2&&body2.stage()==2u&&second_wake_entry_count==trial+1u&&body2.arm_reads()&&body2.invalidations()&&
             c.pc==0x8052a51cu&&c.lr==0x805192d4u&&c.gpr[3]==sleep2.queue()&&
             !(consumed2.control&(M::X1|M::Y1|M::Y2))&&consumed2.steps==4u&&!consumed2.replies&&
             consumed2.ppc==req2&&consumed2.arm==req2&&irq_capture.saved_integer(c,Q::Idle).ok()&&
             c.mmu.read16(Q::Thread+712u)==4u&&c.mmu.read32(sleep2.queue())==Q::Thread&&
             c.mmu.read32(sleep2.queue()+4u)==Q::Thread&&epoch.acknowledged_descriptors(3u-kind)&&device_ok(c));
        reply_body=nullptr;body_cpu=nullptr;
        std::cout<<"V1370_REPLY_TRIAL n="<<trial<<" native_rfi=1 original_vector=1 original_dispatch=1 original_processor=1 native_dcbi=1 wake_entry=1 fd=1\n";
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
        WakeReadyWitness ready2(v1289::expected(Q::Idle,Q::Thread));wake_ready=&ready2;
        if(!ready2.begin(c,body2,irq_capture,sleep2.queue(),device_ok(c)))wake_refuse(6);
        bool selected2=false;try{run_game(c);}catch(const ReadyReached&){selected2=true;}
        need(selected2&&ready2.stage()==2u&&second_ready_count==trial+1u&&ready2.ready_queue()&&
             c.pc==Q::Select&&c.lr==0x8052a5f0u&&c.gpr[3]==0u&&host.serviced_steps()==4u&&
             c.mmu.read16(Q::Thread+712u)==1u&&c.mmu.read32(sleep2.queue())==0u&&
             c.mmu.read32(sleep2.queue()+4u)==0u&&irq_capture.saved_integer(c,Q::Idle).ok()&&device_ok(c));
        wake_ready=nullptr;
        const int64_t nested_counter2=int64_t(c.gpr[13])+v1292::counter_disp;
        need(nested_counter2>=0x80000000ll&&nested_counter2<=0x817ffffcll);
        NestedWakeReturnWitness nested2(v1292::expected(Q::Idle,uint32_t(nested_counter2)));nested_wake=&nested2;
        if(!nested2.begin(c,ready2,irq_capture,sleep2.queue(),device_ok(c)))nested_refuse(6);
        bool wake_return2=false;try{run_game(c);}catch(const NestedReturned&){wake_return2=true;}
        need(wake_return2&&nested2.stage()==2u&&second_nested_count==trial+1u&&c.pc==0x805192d4u&&
             c.lr==c.pc&&ready2.ready_held(c,device_ok(c))&&host.serviced_steps()==4u);
        nested_wake=nullptr;
        std::cout<<"V1374_WAKE_TRIAL n="<<trial<<" original_wake=1 ready=1 nested_return=1\n";
        ReplyReturnWitness completed2(v1299::expected(uint32_t(nested_counter2)));
        reply_return=&completed2;return_cpu=&c;
        if(!completed2.begin(c,body2,ready2,nested2,irq_capture,sleep2.queue(),req2,handler_abi2,processor_abi2,device_ok(c)))return_refuse(6);
        bool handler_ret2=false;try{run_game(c);}catch(const ReplyHandlerReturned&){handler_ret2=true;}
        need(handler_ret2&&completed2.returned(c,device_ok(c))&&completed2.x2_writes()==1u&&completed2.helper_returns()==1u&&
             second_return_count==trial+1u&&c.pc==v1255::returned&&c.lr==c.pc&&host.serviced_steps()==4u&&
             !(cause.load()&mask.load())&&ready2.ready_context_held(c,device_ok(c)));
        reply_return=nullptr;return_cpu=nullptr;
        ReadyIdleReturnJoin idle_join2;LiveEpilogueWitness idle2(v1270::expected(Q::Idle));
        ready_idle=&idle_join2;idle_epilogue=&idle2;idle_tick=c.inst_count;
        if(!idle_join2.begin(c,completed2,ready2,irq_capture,device_ok(c)))idle_return_refuse(6);
        bool idle_ret2=false;try{run_game(c);}catch(const IdleRfiReturned&){idle_ret2=true;}
        need(idle_ret2&&idle_join2.resumed_idle(c,device_ok(c))&&idle2.stage()==4u&&second_idle_return_count==trial+1u&&
             c.pc==v1256::resume&&(c.msr&0x8000u)&&host.serviced_steps()==4u&&!(cause.load()&mask.load())&&
             save2.preserved(c,device_ok(c)));
        ready_idle=nullptr;idle_epilogue=nullptr;
        std::cout<<"V1374_IDLE_TRIAL n="<<trial<<" handler_return=1 latch_clear=1 native_rfi=1 ready_preserved=1\n";
        IdleSelectionWitness selection2(v1321::selection(Q::Thread,Q::Idle,uint32_t(nested_counter2)));
        IdleRouteWitness route2({Q::Enable,v1256::resume,Q::Select,0x80529864u,v1321::direct[3].pc,
             v1321::ram_words,v1321::direct,v1321::callbacks});
        selection_witness=&selection2;selection_route=&route2;
        if(!selection2.begin(c,idle_join2,device_ok(c))||!route2.begin(c,device_ok(c)))selection_refuse(7);
        CooperativeLoadLane load2(v1321::load());coop_load=&load2;load_save=&save2;
        bool sleep_exit2=false;try{run_game(c);}catch(const SleepExited&){sleep_exit2=true;}
        need(sleep_exit2&&exited2.returned(c,load_held(c))&&second_selection_count==trial+1u&&
             second_load_count==trial+1u&&second_resumed_sleep_count==trial+1u&&second_sleep_exit_count==trial+1u&&
             host.serviced_steps()==4u&&!(cause.load()&mask.load())&&epoch.acknowledged_descriptors(3u-kind)&&
             host.physical_ram().read32(req2+4u)==1u&&descriptor.identity_after_release(c));
        std::cout<<"V1374_RESTORE_TRIAL n="<<trial<<" original_select=1 original_load=1 native_rfi=1 sleep_return=1 fd=1\n";
#ifdef UNDERCOVER_V1378_SECOND_FREE
        submit_resume=&submit_cont2;
        if(!submit_cont2.begin(c,exited2,load_held(c)))submit_resume_refuse(4);
        exit_active=false;submit_resume_active=true;
        AllocatorReleaseWitness allocator2(v1344::release_expected,1u);
        allocator_release=&allocator2;allocator_descriptor=&descriptor;allocator_request=second_submission.request();
#ifdef UNDERCOVER_V1379_SECOND_RETURN
        open_return=&open_tail2;
        bool opened2=false;try{run_game(c);}catch(const OpenReturned&){opened2=true;}
        need(opened2&&open_tail2.returned(c,open_return_held(c),open_descriptor(c))&&
             allocator2.storage_preserved(c,allocator_held(c))&&allocator2.inline_completed()&&second_open_return_count==trial+1u&&
             c.gpr[3]==1u&&c.pc==v1379::expected.stm_resume);
        std::cout<<"V1379_OPEN_TRIAL n="<<trial<<" submit_return=1 open_return=1 stm_resume=1 fd=1\n";
        open_return_active=false;
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
        StmIoctlEntryWitness ioctl_entry(v1383::expected);
        if(!ioctl_entry.begin(c,open_tail2,open_return_held(c),open_descriptor(c),kind)){
            stm_ioctl=&ioctl_entry;stm_ioctl_refuse(1);
        }
        stm_ioctl=&ioctl_entry;
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
        IoctlPrefixWitness prefix(v1386::expected);ioctl_prefix=&prefix;
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
        IoctlAllocationWitness alloc3(v1387::expected);ioctl_alloc=&alloc3;
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
        IoctlConstructionWitness build3(v1392::expected);ioctl_build=&build3;
#endif
#endif
#endif
        bool ioctl_reached=false;try{run_game(c);}catch(const StmIoctlReached&){ioctl_reached=true;}
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
#ifdef UNDERCOVER_V1407_IOCTL_HEADER
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
#ifdef UNDERCOVER_IPC_PROFILE
#ifdef UNDERCOVER_IPC_DISPATCH
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
#ifdef UNDERCOVER_STM_EVENT_RETURN
#ifdef UNDERCOVER_STM_OUTER_RESTORE
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u&&!ioctl_flush&&ioctl_submit_queue&&ioctl_submit_queue->stage()==2u&&ioctl_profile&&ioctl_profile->stage()==2u&&ioctl_dispatch&&async_return&&async_return->stage()==2u&&async_wrapper&&async_wrapper->stage()==2u&&stm_event_return&&stm_event_return->stage()==2u&&stm_outer&&stm_outer->reached(c,stm_outer_held(c),stm_outer_pending(c))&&stm_outer_count==trial+1u&&stm_event_return_count==trial+1u&&async_wrapper_count==trial+1u&&ioctl_event_gate->stage()==4u&&async_return_count==trial+1u&&ioctl_dispatch_count==trial+1u&&ioctl_profile_return_count==trial+1u&&ioctl_queue_entry_count==trial+1u&&ioctl_header_return_count==trial+1u&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#else
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u&&!ioctl_flush&&ioctl_submit_queue&&ioctl_submit_queue->stage()==2u&&ioctl_profile&&ioctl_profile->stage()==2u&&ioctl_dispatch&&async_return&&async_return->stage()==2u&&async_wrapper&&async_wrapper->stage()==2u&&stm_event_return&&stm_event_return->reached(c,async_held(c))&&stm_event_return_count==trial+1u&&async_wrapper_count==trial+1u&&ioctl_event_gate->stage()==4u&&async_return_count==trial+1u&&ioctl_dispatch_count==trial+1u&&ioctl_profile_return_count==trial+1u&&ioctl_queue_entry_count==trial+1u&&ioctl_header_return_count==trial+1u&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u&&!ioctl_flush&&ioctl_submit_queue&&ioctl_submit_queue->stage()==2u&&ioctl_profile&&ioctl_profile->stage()==2u&&ioctl_dispatch&&async_return&&async_return->stage()==2u&&async_wrapper&&async_wrapper->reached(c,async_held(c),ioctl_prefix->caller_abi(c))&&async_wrapper_count==trial+1u&&ioctl_event_gate->stage()==4u&&async_return_count==trial+1u&&ioctl_dispatch_count==trial+1u&&ioctl_profile_return_count==trial+1u&&ioctl_queue_entry_count==trial+1u&&ioctl_header_return_count==trial+1u&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u&&!ioctl_flush&&ioctl_submit_queue&&ioctl_submit_queue->stage()==2u&&ioctl_profile&&ioctl_profile->stage()==2u&&ioctl_dispatch&&async_return&&async_return->reached(c,async_held(c),ioctl_submit_prefix->caller_abi(c))&&ioctl_event_gate->stage()==4u&&async_return_count==trial+1u&&ioctl_dispatch_count==trial+1u&&ioctl_profile_return_count==trial+1u&&ioctl_queue_entry_count==trial+1u&&ioctl_header_return_count==trial+1u&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u&&!ioctl_flush&&ioctl_submit_queue&&ioctl_submit_queue->stage()==2u&&ioctl_profile&&ioctl_profile->stage()==2u&&ioctl_dispatch&&ioctl_dispatch->reached(c,ioctl_dispatch_held(c))&&ioctl_event_gate->stage()==3u&&ioctl_dispatch_count==trial+1u&&ioctl_profile_return_count==trial+1u&&ioctl_queue_entry_count==trial+1u&&ioctl_header_return_count==trial+1u&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u&&!ioctl_flush&&ioctl_submit_queue&&ioctl_submit_queue->stage()==2u&&ioctl_profile&&ioctl_profile->reached(c,ioctl_flush_held(c))&&ioctl_profile_return_count==trial+1u&&ioctl_queue_entry_count==trial+1u&&ioctl_header_return_count==trial+1u&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u&&!ioctl_flush&&ioctl_submit_queue&&ioctl_submit_queue->reached(c,ioctl_flush_held(c))&&ioctl_queue_entry_count==trial+1u&&ioctl_header_return_count==trial+1u&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->stage()==2u&&ioctl_flush&&ioctl_flush->returned(c,ioctl_flush_held(c))&&ioctl_header_return_count==trial+1u&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_submit_prefix&&ioctl_submit_prefix->reached(c,ioctl_submit_prefix_held(c))&&ioctl_header_entry_count==trial+1u&&ioctl_tail&&ioctl_tail->stage()==4u&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_tail&&ioctl_tail->reached(c,ioctl_flush_held(c))&&ioctl_output_count==trial+1u&&ioctl_submit_count==trial+1u&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&ioctl_flush&&ioctl_flush->returned(c,ioctl_flush_held(c))&&ioctl_flush_count==trial+1u&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&build3.reached(c,ioctl_alloc_held(c))&&alloc3.stage()==2u&&ioctl_build_count==trial+1u&&descriptor.identity_after_release(c)&&
#endif
#else
        need(ioctl_reached&&alloc3.returned(c,ioctl_alloc_held(c))&&descriptor.identity_after_release(c)&&
#endif
             ioctl_alloc_count==trial+1u&&ioctl_prefix_count==trial+1u&&
#else
        need(ioctl_reached&&prefix.reached(c,stm_ioctl_held(c))&&ioctl_prefix_count==trial+1u&&
#endif
#else
        need(ioctl_reached&&ioctl_entry.reached(c,stm_ioctl_held(c))&&
#endif
             stm_ioctl_count==trial+1u&&
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
             host.serviced_steps()==5u&&epoch.acknowledged_descriptors(3u-kind)&&(cause.load()&mask.load())==H::PI_HOLLYWOOD);
#else
             host.serviced_steps()==4u&&epoch.acknowledged_descriptors(3u-kind)&&!(cause.load()&mask.load()));
#endif
        std::cout<<"V1383_IOCTL_TRIAL n="<<trial<<" original_stm=1 native_disable=1 event_fd=1 buffers=1 callback=1 stores="<<ioctl_entry.stores()<<'\n';
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
        std::cout<<"V1386_PREFIX_TRIAL n="<<trial<<" original_prefix=1 save_return=1 allocator_entry=1 saved="<<prefix.saved()<<" stores="<<prefix.stores()<<'\n';
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
        std::cout<<"V1387_ALLOCATION_TRIAL n="<<trial<<" original_return=1 heap_shadow=1 metadata_shadow=1 masked=1 stores="
                 <<alloc3.stores()<<" heap="<<alloc3.heap_stores()<<" metadata="<<alloc3.metadata_stores()<<'\n';
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
        std::cout<<"V1392_CONSTRUCTION_TRIAL n="<<trial<<" original_request=1 callback=1 first_flush=1 flush_kind="<<build3.flush_kind()
                 <<" stores="<<build3.stores()<<" request="<<build3.request_stores()<<'\n';
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
        std::cout<<"V1398_FLUSH_TRIAL n="<<trial<<" original_flush=1 native_rfi=1 masked=1 lines="<<ioctl_input_lines<<" empty=0\n";
        std::cout<<"V1401_OUTPUT_TRIAL n="<<trial<<" second_flush=1 native_rfi=1 submit_entry=1 lines="<<ioctl_output_lines<<" visits="<<ioctl_tail->visits()<<'\n';
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
        std::cout<<"V1404_PREFIX_TRIAL n="<<trial<<" original_submit=1 queue_path="<<ioctl_submit_prefix->queue_path()<<" header_flush_entry=1 visits="<<ioctl_submit_prefix->visits()
                 <<" stores="<<ioctl_submit_prefix->stores()<<" queue="<<ioctl_submit_prefix->queue_stores()<<" request="<<ioctl_submit_prefix->request_stores()<<'\n';
#ifdef UNDERCOVER_V1407_IOCTL_HEADER
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
        std::cout<<"V1407_HEADER_TRIAL n="<<trial<<" original_flush=1 native_rfi=1 masked=1 request_preserved=1 lines="<<ioctl_header_lines<<'\n';
        std::cout<<"V1410_QUEUE_TRIAL n="<<trial<<" original_disable=1 masked=1 queue_entry=1 request_preserved=1 visits="<<ioctl_submit_queue->visits()
                 <<" stores="<<ioctl_submit_queue->stores()<<" polls="<<ioctl_submit_queue->polls()<<'\n';
#ifdef UNDERCOVER_IPC_PROFILE
        std::cout<<"IPC_PROFILE_TRIAL n="<<trial<<" original_return=1 masked=1 ring_preserved=1 request_preserved=1 visits="<<ioctl_profile->visits()
                 <<" stores="<<ioctl_profile->stores()<<" polls="<<ioctl_profile->polls()<<" slot="<<unsigned(ioctl_profile->slot_available())<<'\n';
#ifdef UNDERCOVER_IPC_DISPATCH
        std::cout<<"IPC_DISPATCH_TRIAL n="<<trial<<" original_return=1 masked=1 ring_dequeued=1 credit_consumed=1 message=1 control=1 queued=1 serviced=0 visits="
                 <<ioctl_dispatch->visits()<<" stores="<<ioctl_dispatch->stores()<<" calls="<<ioctl_dispatch->calls()
                 <<" writes="<<ioctl_dispatch->writes()<<" reads="<<ioctl_dispatch->reads()<<" polls="<<ioctl_dispatch->polls()<<'\n';
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
#ifdef UNDERCOVER_STM_EVENT_RETURN
#ifdef UNDERCOVER_STM_OUTER_RESTORE
        need(stm_outer->reached(c,stm_outer_held(c),host.exception_pending(c.msr))&&host.serviced_steps()==5u&&
             host.services().event_pending());
        std::cout<<"STM_OUTER_RESTORE_TRIAL n="<<trial<<" original_mtmsr=1 ee=1 pending_ack=1 deferred=1 visits="<<stm_outer->visits()<<'\n';
        ExternalReturnWitness third_frame;
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
        const auto third_gqr=c.gqr;
#endif
        const auto ex=stm_outer_private::expected;
        if(!enter_deferred_stm_irq(c,host,*ioctl_event_gate,third_frame,v1259::vector,
              ioctl_build->request()&0x3fffffffu,Q::Thread,ex.resume,ex.resume_word,stm_outer_held(c)))stm_outer_refuse(5);
        need(third_frame.stage()==1u&&c.pc==ExternalVector&&!(c.msr&0x8000u)&&
             third_frame.pending_source(c,cause.load(),mask.load())&&ioctl_event_gate->deferred_held(true)&&
             stm_event_return->flag_preserved(c)&&ioctl_dispatch->storage_preserved(c));
        ++stm_irq_entry_count;
        std::cout<<"STM_DEFERRED_IRQ_TRIAL n="<<trial<<" entered=1 active_thread=1 srr=1 deferred=1 pending_ack=1 vector_executed=0\n";
        stm_outer.reset();
#ifdef UNDERCOVER_STM_DEFERRED_VECTOR
        // At entry no original vector instruction has executed yet.
        // Transfer protected IPC memory to the independent ACK observer.
        IpcDeferredAckMemory ack_memory3;
        third_memory=&ack_memory3;
        const auto dx=ipc_dispatch_private::expected;
        const auto req3=ioctl_build->request();
        if(!ack_memory3.begin(c,dx.ring,dx.credit,dx.profile,{req3,ioctl_build->allocated_size()},
            {c.gpr[1]-512u,520u},dx.slots,c.mmu.read32(req3+8u),
            ioctl_event_gate->deferred_held(true)&&ioctl_profile->stage()==2u&&ioctl_profile->slot_available(),
            ioctl_profile->selected_slot()))third_vector_refuse(5);
        SecondVectorWitness vec3({v1260::trampoline,v1260::dispatcher,Q::Thread,
            v1260::dispatcher_word,v1260::vector_words,v1260::trampoline_words});
        third_context=Q::Thread;third_wait=sleep2.queue();
        for(unsigned i=0;i<third_thread_tail.size();++i)third_thread_tail[i]=c.mmu.read32(third_context+712u+4u*i);
        third_memory=&ack_memory3;third_frame_ptr=&third_frame;third_vector=&vec3;third_vector_tick=c.inst_count;
        bool vector3=false;try{run_game(c);}catch(const VectorStop&){vector3=true;}
        if(!vector3||vec3.stage()!=3u||third_vector_count!=trial+1u||!third_irq_held(c)||
           c.pc!=v1260::dispatcher||!third_frame.saved_integer(c,Q::Thread).ok()||host.serviced_steps()!=5u)third_vector_refuse(5);
        std::cout<<"STM_DEFERRED_VECTOR_TRIAL n="<<trial<<" original_vector=1 original_trampoline=1 active_context=1 saved_fields=38 deferred=1 pending_ack=1 dispatcher_executed=0 visits="<<vec3.vector_visits()+vec3.trampoline_visits()<<'\n';
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
        IpcDispatchWitness dispatch3({v1261::code,v1261::handler,Q::Thread,Q::Thread,W::Table,W::IrqGlobal,
                                     W::Sda+v1261::counter_disp},second_irq_kind);
        need(c.mmu.read32(W::Sda+v1261::counter_disp)==0u);
        third_dispatch=&dispatch3;third_request=req3&0x3fffffffu;
        bool dispatch_done=false;try{run_game(c);}catch(const DispatchStop&){dispatch_done=true;}
        const auto third_snap=host.cold_ipc_snapshot();
        if(!dispatch_done||!dispatch3.deferred_mode()||dispatch3.stage()!=6u||
           third_dispatch_count!=trial+1u||!dispatch3.handler_ready(c,third_frame,third_snap,third_wait,third_irq_held(c))||
           !dispatch3.cause_reads()||!dispatch3.mask_reads()||c.pc!=v1261::handler||host.serviced_steps()!=5u)third_dispatch_refuse(7);
        std::cout<<"STM_DEFERRED_DISPATCH_TRIAL n="<<trial<<" original_dispatch=1 handler_index=27 active_context=1 pending_ack=1 deferred=1 handler_executed=0 visits="
                 <<dispatch3.visits()<<" reads="<<dispatch3.cause_reads()+dispatch3.mask_reads()<<'\n';
        third_dispatch=nullptr;third_request=0;
#ifdef UNDERCOVER_STM_DEFERRED_ACK
        DeferredAckExecution ack3(deferred_ack_private::expected);
        third_ack=&ack3;
        if(!ack3.begin(c,*ioctl_event_gate,ack_memory3,third_ack_held(c)))third_ack_refuse(1);
        bool ack_done=false;try{run_game(c);}catch(const DeferredAckStop&){ack_done=true;}
        if(!ack_done||third_ack_count!=trial+1u||!ack3.reached(c,third_ack_held(c))||
           !ack_memory3.preserved(c)||!ioctl_event_gate->completed(true)||host.serviced_steps()!=5u||
           !host.services().event_pending()||(cause.load()&mask.load())||host.cold_ipc_snapshot().replies||
           !third_frame.saved_integer(c,Q::Thread).ok())third_ack_refuse(7);
        std::cout<<"STM_DEFERRED_ACK_TRIAL n="<<trial<<" original_return=1 guest_w1c=1 credit=1 unissued=1 deferred=1 reply=0 active_context=1 visits="
                 <<ack3.visits()<<" reads="<<ack3.reads()<<" writes="<<ack3.writes()<<" stack="<<ack3.stack_stores()<<" calls="<<ack3.calls()<<'\n';
        third_ack=nullptr;
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
        DeferredActiveReturnJoin active_join;
        LiveEpilogueWitness active_route(v1270::expected(Q::Thread));
        third_return_route=&active_route;third_return_join=&active_join;third_return_tick=c.inst_count;
        if(!active_join.begin(c,third_frame,*ioctl_event_gate,ack_memory3,Q::Thread,third_wait,
             W::Sda+v1261::counter_disp,third_gqr,third_return_storage(c)))third_return_refuse(6);
        bool active_returned=false;try{run_game(c);}catch(const DeferredActiveRfiStop&){active_returned=true;}
        if(!active_returned||third_return_count!=trial+1u||active_route.stage()!=4u||
           !active_join.resumed(c,third_return_storage(c))||c.pc!=ex.resume||!(c.msr&0x8000u)||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)third_return_refuse(7);
        std::cout<<"STM_DEFERRED_ACTIVE_RETURN_TRIAL n="<<trial
            <<" native_rfi=1 original_epilogue=1 active_context=1 deferred=1 reply=0 resume_instruction_executed=0 visits="
            <<active_route.visits()<<'\n';
#ifdef UNDERCOVER_STM_RESUMED_RESTORE
        StmResumedRestoreWitness resumed_restore(ex);
        third_resume=&resumed_restore;
        if(!resumed_restore.begin(c,active_join.resumed(c,third_return_storage(c))))third_resume_refuse(1);
        bool stm_resumed=false;try{run_game(c);}catch(const StmResumedRestoreStop&){stm_resumed=true;}
        if(!stm_resumed||third_resume_count!=trial+1u||active_route.stage()!=5u||
           !resumed_restore.reached(c,third_resume_held(c))||c.pc!=ex.caller||c.lr!=ex.caller||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)third_resume_refuse(5);
        std::cout<<"STM_RESUMED_RESTORE_TRIAL n="<<trial
            <<" native_resume=1 original_restore_return=1 stm_caller=1 deferred=1 reply=0 stm_instruction_executed=0 visits="
            <<resumed_restore.visits()<<'\n';
        third_resume=nullptr;
#ifdef UNDERCOVER_STM_FINAL_RETURN
        StmFinalReturnWitness final_stm(stm_final_private::expected);stm_final=&final_stm;
        if(!final_stm.begin(c,stm_caller_gp,stm_caller_cr,stm_final_held(c)))stm_final_refuse(1);
        bool stm_returned=false;try{run_game(c);}catch(const StmFinalReturnStop&){stm_returned=true;}
        if(!stm_returned||stm_final_count!=trial+1u||!final_stm.reached(c,stm_final_held(c))||
           c.pc!=stm_final_private::expected.caller||c.lr!=c.pc||final_stm.loads()!=3u||final_stm.stores()!=1u||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)stm_final_refuse(5);
        std::cout<<"STM_FINAL_RETURN_TRIAL n="<<trial
            <<" original_stm_return=1 state_store=1 caller_abi=1 deferred=1 reply=0 osinit_instruction_executed=0 visits="
            <<final_stm.visits()<<" loads="<<final_stm.loads()<<'\n';
        stm_final=nullptr;
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
        PostStmScEntryWitness sc_entry(post_stm_sc_private::expected);post_stm_sc=&sc_entry;
        if(!sc_entry.begin(c,post_stm_sc_held(c)))post_stm_sc_refuse(1);
        bool sc_entered=false;try{run_game(c);}catch(const PostStmScStop&){sc_entered=true;}
        if(!sc_entered||post_stm_sc_count!=trial+1u||!sc_entry.reached(c,post_stm_sc_held(c))||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)post_stm_sc_refuse(5);
        std::cout<<"POST_STM_SC_TRIAL n="<<trial
            <<" original_osinit_call=1 original_sc_prefix=1 stack_stores=3 disable_entry=1 deferred=1 reply=0 disable_executed=0 visits="
            <<sc_entry.visits()<<'\n';
        post_stm_sc=nullptr;
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
        PostStmScDisableWitness sc_disable(post_stm_sc_disable_private::expected);
        post_stm_frame=&sc_entry;
        if(!sc_disable.begin(c,sc_entry.reached(c,third_return_join->continuation_held(c,third_return_storage(c)))))
            post_stm_disable_refuse(1);
        post_stm_disable=&sc_disable;
        bool sc_disabled=false;try{run_game(c);}catch(const PostStmDisableStop&){sc_disabled=true;}
        if(!sc_disabled||post_stm_disable_count!=trial+1u||!sc_disable.reached(c,post_stm_disable_held(c))||
           (c.msr&0x8000u)||c.gpr[3]!=1u||host.serviced_steps()!=5u||!host.services().event_pending()||
           (cause.load()&mask.load())||host.cold_ipc_snapshot().replies)post_stm_disable_refuse(5);
        std::cout<<"POST_STM_SC_DISABLE_TRIAL n="<<trial
            <<" original_disable=1 native_msr=1 previous_ee=1 sc_return=1 deferred=1 reply=0 decision_executed=0 visits="
            <<sc_disable.visits()<<'\n';
        post_stm_disable=nullptr;
#ifdef UNDERCOVER_POST_STM_SC_DECISION
        ScDecisionWitness sc_decision(post_stm_sc_decision_private::expected);
        if(!sc_decision.begin(c,sc_disable.reached(c,sc_entry.frame_held(c,
             third_return_join->post_resume_storage_held(c,third_return_storage(c),sc_disable.expected_msr())))))
            post_stm_decision_refuse(1);
        post_stm_decision=&sc_decision;
        bool decision_done=false;try{run_game(c);}catch(const PostStmDecisionStop&){decision_done=true;}
        if(!decision_done||post_stm_decision_count!=trial+1u||!sc_decision.reached(c,post_stm_decision_held(c))||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)post_stm_decision_refuse(5);
        std::cout<<"POST_STM_SC_DECISION_TRIAL n="<<trial
            <<" cold_bss=1 original_branch=1 native_load=1 native_stores=2 restore_entry=1 deferred=1 reply=0 restore_executed=0 visits="
            <<sc_decision.visits()<<'\n';
        post_stm_decision=nullptr;
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
        ScQuietRestoreWitness sc_restore(post_stm_sc_restore_private::expected);
        post_stm_objects=&sc_decision;
        if(!sc_restore.begin(c,sc_decision.reached(c,sc_entry.frame_held(c,
             third_return_join->post_resume_storage_held(c,third_return_storage(c),sc_decision.expected_msr())))))
            post_stm_restore_refuse(1);
        post_stm_restore=&sc_restore;
        bool sc_enabled=false;try{run_game(c);}catch(const PostStmRestoreEnableStop&){sc_enabled=true;}
        if(!sc_enabled||!sc_restore.enabled(c,post_stm_restore_held(c))||(cause.load()&mask.load())||
           host.serviced_steps()!=5u||!host.services().event_pending()||host.cold_ipc_snapshot().replies)
            post_stm_restore_refuse(5);
        bool sc_restored=false;try{run_game(c);}catch(const PostStmRestoreStop&){sc_restored=true;}
        if(!sc_restored||post_stm_restore_count!=trial+1u||!sc_restore.reached(c,post_stm_restore_held(c))||
           !(c.msr&0x8000u)||host.serviced_steps()!=5u||!host.services().event_pending()||
           (cause.load()&mask.load())||host.cold_ipc_snapshot().replies)post_stm_restore_refuse(5);
        std::cout<<"POST_STM_SC_RESTORE_TRIAL n="<<trial
            <<" native_msr=1 quiet_poll=1 original_suffix=1 original_return=1 deferred=1 reply=0 version_executed=0 visits="
            <<sc_restore.visits()<<'\n';
        post_stm_restore=nullptr;
#ifdef UNDERCOVER_POST_STM_SC_VERSION
        ScVersionWitness sc_version(post_stm_sc_version_private::expected);
        post_stm_version_msr=sc_restore.expected_msr();
        if(!sc_version.begin(c,sc_restore.reached(c,sc_decision.objects_held(c,sc_entry.frame_held(c,
             third_return_join->post_resume_storage_held(c,third_return_storage(c),post_stm_version_msr))))))
            post_stm_version_refuse(1);
        post_stm_version=&sc_version;
        bool version_done=false;try{run_game(c);}catch(const PostStmVersionStop&){version_done=true;}
        if(!version_done||post_stm_version_count!=trial+1u||!sc_version.reached(c,post_stm_version_held(c))||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)post_stm_version_refuse(5);
        std::cout<<"POST_STM_SC_VERSION_TRIAL n="<<trial
            <<" original_pointer=1 original_thunk=1 diagnostic_abi=1 original_tail=1 deferred=1 reply=0 report_executed=0 visits="
            <<sc_version.visits()<<'\n';
        post_stm_version=nullptr;
#ifdef UNDERCOVER_POST_STM_SC_REPORT
        ScReportWitness sc_report(post_stm_sc_report_private::expected);
        post_stm_version_data=&sc_version;
        if(!sc_report.begin(c,sc_version.reached(c,sc_decision.objects_held(c,sc_entry.frame_held(c,
             third_return_join->post_resume_storage_held(c,third_return_storage(c),post_stm_version_msr))))))
            post_stm_report_refuse(1);
        post_stm_report=&sc_report;
        bool report_done=false;try{run_game(c);}catch(const PostStmReportStop&){report_done=true;}
        if(!report_done||post_stm_report_count!=trial+1u||!sc_report.reached(c,post_stm_report_held(c))||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)post_stm_report_refuse(5);
        std::cout<<"POST_STM_SC_REPORT_TRIAL n="<<trial
            <<" original_prologue=1 native_stores="<<sc_report.stores()
            <<" va_abi=1 original_helper_entry=1 deferred=1 reply=0 helper_executed=0 visits="
            <<sc_report.visits()<<'\n';
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
        ScReportHelperWitness sc_helper(post_stm_sc_report_helper_private::expected);
        if(!sc_helper.begin(c,sc_report.reached(c,post_stm_report_held(c))))post_stm_helper_refuse(1);
        post_stm_helper=&sc_helper;
        bool helper_done=false;try{run_game(c);}catch(const PostStmHelperStop&){helper_done=true;}
        if(!helper_done||post_stm_helper_count!=trial+1u||!sc_helper.reached(c,post_stm_helper_held(c))||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)post_stm_helper_refuse(5);
        std::cout<<"POST_STM_SC_REPORT_HELPER_TRIAL n="<<trial
            <<" original_prefix=1 native_stores="<<sc_helper.stores()
            <<" saved_nonvolatile=3 original_next_entry=1 deferred=1 reply=0 next_executed=0 visits="
            <<sc_helper.visits()<<'\n';
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
        ScLeafShadow sc_dependency(post_stm_sc_report_dependency_private::expected);
        if(!sc_helper.reached(c,post_stm_helper_held(c))||
           c.gpr[3]!=post_stm_sc_report_dependency_private::argument||
           c.gpr[4]!=post_stm_sc_report_dependency_private::selector)post_stm_dependency_refuse(1);
        for(unsigned i=0;i<post_stm_sc_report_dependency_private::initial.size();++i){
            const auto a=post_stm_sc_report_dependency_private::object.base+i;
            if(!c.mmu.get_ptr(a)||c.mmu.read8(a)!=post_stm_sc_report_dependency_private::initial[i])
                post_stm_dependency_refuse(1);
        }
        if(!sc_dependency.begin(c,post_stm_sc_report_dependency_private::object,
             sc_helper.frame_held(c,post_stm_helper_held(c))))post_stm_dependency_refuse(1);
        post_stm_dependency=&sc_dependency;
        bool dep_done=false;try{run_game(c);}catch(const PostStmDependencyStop&){dep_done=true;}
        if(!dep_done||post_stm_dependency_count!=trial+1u||!sc_dependency.reached(c,post_stm_dependency_held(c))||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)post_stm_dependency_refuse(5);
        if(sc_dependency.visits()!=20u||sc_dependency.loads()!=1u||sc_dependency.stores()!=1u||
           c.gpr[3]!=post_stm_sc_report_dependency_private::returned||
           !std::equal(sc_dependency.expected_bytes().begin(),sc_dependency.expected_bytes().end(),
                       post_stm_sc_report_dependency_private::final_bytes.begin(),
                       post_stm_sc_report_dependency_private::final_bytes.end()))post_stm_dependency_refuse(5);
        std::cout<<"POST_STM_SC_REPORT_DEPENDENCY_TRIAL n="<<trial
            <<" native_leaf=1 original_return=1 loads="<<sc_dependency.loads()<<" stores="<<sc_dependency.stores()
            <<" deferred=1 reply=0 caller_executed=0 visits="<<sc_dependency.visits()<<'\n';
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
        ScLeafShadow sc_resume(post_stm_sc_report_resume_private::expected);
        if(!sc_resume.begin(c,post_stm_sc_report_dependency_private::object,
             sc_dependency.reached(c,post_stm_dependency_held(c))))post_stm_resume_refuse(1);
        post_stm_resume=&sc_resume;
        bool resume_done=false;try{run_game(c);}catch(const PostStmResumeStop&){resume_done=true;}
        if(!resume_done||post_stm_resume_count!=trial+1u||!sc_resume.reached(c,post_stm_resume_held(c))||
           sc_resume.visits()!=8u||sc_resume.loads()||sc_resume.stores()||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)post_stm_resume_refuse(5);
        for(unsigned i=0;i<3u;++i)if(c.gpr[3u+i]!=post_stm_sc_report_resume_private::args[i])post_stm_resume_refuse(5);
        const auto va=uint32_t(int64_t(sc_report.incoming_gprs()[1])+post_stm_sc_report_resume_private::va_offset);
        if(c.gpr[6]!=va||c.mmu.read32(va)!=0x01000000u||
           c.mmu.read32(va+4u)!=sc_report.incoming_gprs()[1]+8u)post_stm_resume_refuse(5);
        std::cout<<"POST_STM_SC_REPORT_RESUME_TRIAL n="<<trial
            <<" original_resume=1 formatter_entry=1 arguments=4 deferred=1 reply=0 formatter_executed=0 visits=8\n";
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
        ScFormatterWitness sc_formatter(post_stm_sc_formatter_private::expected);
        if(!sc_formatter.begin(c,sc_resume.reached(c,post_stm_resume_held(c))))post_stm_formatter_refuse(1);
        post_stm_formatter=&sc_formatter;
        bool formatter_done=false;try{run_game(c);}catch(const PostStmFormatterStop&){formatter_done=true;}
        if(!formatter_done||post_stm_formatter_count!=trial+1u||!sc_formatter.reached(c,post_stm_formatter_held(c))||
           sc_formatter.visits()!=23u||sc_formatter.loads()!=1u||sc_formatter.stores()!=4u||
           host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
           host.cold_ipc_snapshot().replies)post_stm_formatter_refuse(5);
        std::cout<<"POST_STM_SC_FORMATTER_TRIAL n="<<trial
            <<" original_formatter=1 native_stores=4 native_loads=1 saved_nonvolatile=16 original_dependency_entry=1 deferred=1 reply=0 dependency_executed=0 visits=23\n";
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER_LEAF
        {
            namespace leaf=post_stm_sc_formatter_leaf_private;
            ScLeafShadow sc_leaf(leaf::expected);
            const uint64_t address=leaf::stack_relative?uint64_t(c.gpr[1])+leaf::address:leaf::address;
            if(address>0xffffffffull)post_stm_formatter_leaf_refuse(1);
            const AllocatorRange read{uint32_t(address),uint32_t(leaf::bytes.size())};
            if(!sc_leaf.begin(c,read,post_stm_formatter_leaf_held(c)))post_stm_formatter_leaf_refuse(1);
            if(!std::equal(leaf::bytes.begin(),leaf::bytes.end(),sc_leaf.expected_bytes().begin(),sc_leaf.expected_bytes().end()))
                post_stm_formatter_leaf_refuse(1);
            post_stm_formatter_leaf=&sc_leaf;
            bool leaf_done=false;try{run_game(c);}catch(const PostStmFormatterLeafStop&){leaf_done=true;}
            if(!leaf_done||post_stm_formatter_leaf_count!=trial+1u||!sc_leaf.reached(c,post_stm_formatter_leaf_held(c))||
               sc_leaf.visits()!=8u||sc_leaf.loads()!=1u||sc_leaf.stores()||sc_leaf.back_polls()!=leaf::backward_polls||
               host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
               host.cold_ipc_snapshot().replies)post_stm_formatter_leaf_refuse(5);
            std::cout<<"POST_STM_SC_FORMATTER_LEAF_TRIAL n="<<trial
                <<" native_leaf=1 original_return=1 exact_value=1 loads=1 stores=0 frame_held=1 deferred=1 reply=0 visits=8\n";
#ifdef UNDERCOVER_FORMATTER_CONTINUATION
            RegisterContinuationWitness continuation(formatter_continuation_private::expected);
            if(!continuation.begin(c,sc_leaf.reached(c,formatter_continuation_held(c))))formatter_continuation_refuse(1);
            formatter_continuation=&continuation;
            bool next_done=false;try{run_game(c);}catch(const FormatterContinuationStop&){next_done=true;}
            if(!next_done||formatter_continuation_count!=trial+1u||!continuation.reached(c,formatter_continuation_held(c))||
               continuation.visits()!=10u||host.serviced_steps()!=5u||!host.services().event_pending()||
               (cause.load()&mask.load())||host.cold_ipc_snapshot().replies)formatter_continuation_refuse(5);
            std::cout<<"FORMATTER_CONTINUATION_TRIAL n="<<trial
                <<" native_resume=1 next_entry=1 arguments=4 frame_held=1 deferred=1 reply=0 visits=10\n";
            formatter_continuation=nullptr;
#ifdef UNDERCOVER_FORMATTER_NESTED
            ScFormatterWitness nested(formatter_nested_private::expected);
            if(!nested.begin(c,continuation.reached(c,formatter_continuation_held(c))))formatter_nested_refuse(1);
            formatter_nested=&nested;
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
            formatter_report_byte.emplace();
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
            formatter_report_compare.emplace();
#endif
#endif
            bool nested_done=false;try{run_game(c);}catch(const FormatterNestedStop&){nested_done=true;}
            const bool nested_boundary_held=formatter_nested_held(c);
#if defined(UNDERCOVER_FORMATTER_CALLER_MIXED)
            const bool nested_reached=
#if defined(UNDERCOVER_FORMATTER_CALLER_POST_MIXED)
#if defined(UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE)
                formatter_report_byte&&formatter_report_byte->stage()==2u&&!formatter_report_byte->failed()&&
                formatter_report_compare&&formatter_report_compare->stage()==2u&&!formatter_report_compare->failed()&&
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
                nested.reached_caller_report_copy(c,nested_boundary_held)&&nested.caller_report_copy_visits()==1u&&
#else
                nested.reached_caller_report_compare(c,nested_boundary_held)&&
#endif
                nested.caller_report_compare_visits()==1u&&
                nested.caller_report_byte_visits()==1u&&nested.caller_next_entry_visits()==1u&&
                nested.caller_final_integer_visits()==1u&&nested.caller_stack_move_visits()==1u&&nested.caller_mixed_byte_visits()==1u&&
#elif defined(UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE)
                formatter_report_byte&&formatter_report_byte->stage()==2u&&!formatter_report_byte->failed()&&
                nested.reached_caller_report_byte(c,nested_boundary_held)&&nested.caller_report_byte_visits()==1u&&
                nested.caller_next_entry_visits()==1u&&nested.caller_final_integer_visits()==1u&&nested.caller_stack_move_visits()==1u&&nested.caller_mixed_byte_visits()==1u&&
#elif defined(UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY)
                nested.reached_caller_next_entry(c,nested_boundary_held)&&nested.caller_next_entry_visits()==1u&&nested.caller_final_integer_visits()==1u&&nested.caller_stack_move_visits()==1u&&nested.caller_mixed_byte_visits()==1u&&
#elif defined(UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER)
                nested.reached_caller_final_integer(c,nested_boundary_held)&&nested.caller_final_integer_visits()==1u&&nested.caller_stack_move_visits()==1u&&nested.caller_mixed_byte_visits()==1u&&
#elif defined(UNDERCOVER_FORMATTER_CALLER_STACK_MOVE)
                nested.reached_caller_stack_move(c,nested_boundary_held)&&nested.caller_stack_move_visits()==1u&&nested.caller_mixed_byte_visits()==1u&&
#else
                nested.reached_caller_post_mixed(c,nested_boundary_held)&&nested.caller_mixed_byte_visits()==1u&&
#endif
                nested.caller_post_mixed_visits()==2u&&nested.caller_post_mixed_integers()==1u&&
                nested.caller_post_mixed_taken()==1u&&nested.caller_post_mixed_fallthrough()==0u&&
#elif defined(UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE)
                nested.reached_caller_mixed_byte(c,nested_boundary_held)&&nested.caller_mixed_byte_visits()==1u&&
#else
                nested.reached_caller_mixed(c,nested_boundary_held)&&
#endif
                nested.caller_integer_visits()==formatter_caller_integer_private::path.size()&&
                nested.caller_branch_visits()==4u&&
                nested.caller_post_integer_visits()==formatter_caller_post_integer_private::path.size()&&
                nested.caller_mixed_visits()==formatter_caller_mixed_private::path.size()&&
                nested.caller_mixed_integers()==UNDERCOVER_EXPECTED_CALLER_MIXED_INTEGERS&&
                nested.caller_mixed_taken()==UNDERCOVER_EXPECTED_CALLER_MIXED_TAKEN&&
                nested.caller_mixed_fallthrough()==UNDERCOVER_EXPECTED_CALLER_MIXED_FALLTHROUGH;
#elif defined(UNDERCOVER_FORMATTER_CALLER_FOURTH_BRANCH)
            const bool nested_reached=nested.reached_caller_branch(c,nested_boundary_held)&&
                nested.caller_integer_visits()==formatter_caller_integer_private::path.size()&&
                nested.caller_branch_visits()==4u&&
                nested.caller_post_integer_visits()==formatter_caller_post_integer_private::path.size();
#elif defined(UNDERCOVER_FORMATTER_CALLER_THIRD_BRANCH)
            const bool nested_reached=nested.reached_caller_branch(c,nested_boundary_held)&&
                nested.caller_integer_visits()==formatter_caller_integer_private::path.size()&&
                nested.caller_branch_visits()==3u&&
                nested.caller_post_integer_visits()==formatter_caller_post_integer_private::path.size();
#elif defined(UNDERCOVER_FORMATTER_CALLER_POST_INTEGERS)
            const bool nested_reached=nested.reached_caller_post_integers(c,nested_boundary_held)&&
                nested.caller_integer_visits()==formatter_caller_integer_private::path.size()&&
                nested.caller_branch_visits()==2u&&
                nested.caller_post_integer_visits()==formatter_caller_post_integer_private::path.size();
#elif defined(UNDERCOVER_FORMATTER_CALLER_BRANCH)
            const bool nested_reached=nested.reached_caller_branch(c,nested_boundary_held)&&
                nested.caller_integer_visits()==formatter_caller_integer_private::path.size()&&
#ifdef UNDERCOVER_FORMATTER_CALLER_SECOND_BRANCH
                nested.caller_branch_visits()==2u;
#else
                nested.caller_branch_visits()==1u;
#endif
#elif defined(UNDERCOVER_FORMATTER_CALLER_INTEGERS)
            const bool nested_reached=nested.reached_caller_integers(c,nested_boundary_held)&&
                nested.caller_integer_visits()==formatter_caller_integer_private::path.size();
#elif defined(UNDERCOVER_FORMATTER_CALLER_BYTE)
            const bool nested_reached=nested.reached_caller_byte(c,nested_boundary_held);
#elif defined(UNDERCOVER_FORMATTER_CALLER_ARRIVAL)
            const bool nested_reached=nested.reached_caller_arrival(c,nested_boundary_held);
#elif defined(UNDERCOVER_FORMATTER_RETURN)
            const bool nested_reached=nested.reached_native_return(c,nested_boundary_held);
#elif defined(UNDERCOVER_FORMATTER_PARTIAL)
            const bool nested_reached=nested.reached_instruction_boundary(c,nested_boundary_held);
#elif defined(UNDERCOVER_FORMATTER_POST_CTR)
            const bool nested_reached=nested.reached_load_boundary(c,nested_boundary_held);
#elif defined(UNDERCOVER_FORMATTER_ARRIVAL)
            const bool nested_reached=nested.reached_control_destination(c,nested_boundary_held);
#else
            const bool nested_reached=formatter_nested_private::expected.control.destination?
                nested.reached_control_boundary(c,nested_boundary_held):nested.reached_load_boundary(c,nested_boundary_held);
#endif
            if(!nested_done||formatter_nested_count!=trial+1u||!nested_reached||
 #if defined(UNDERCOVER_FORMATTER_RETURN)
               nested.visits()!=98u||nested.loads()!=15u||nested.stores()!=17u||nested.authenticated_loads()!=5u||nested.caller_store_count()!=4u||!nested.frame_released()||c.gpr[1]!=post_stm_formatter->expected_sp()||
#ifdef UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
               c.lr!=formatter_caller_next_entry_private::return_pc||c.pc!=formatter_caller_next_entry_private::target||
#else
               c.lr!=formatter_return_private::caller||c.pc!=formatter_return_private::caller||
#endif
#elif defined(UNDERCOVER_FORMATTER_RELEASE)
               nested.visits()!=97u||nested.loads()!=15u||nested.stores()!=17u||nested.authenticated_loads()!=5u||nested.caller_store_count()!=4u||!nested.frame_released()||c.gpr[1]!=post_stm_formatter->expected_sp()||c.lr!=formatter_release_private::expected.entry_lr||
#elif defined(UNDERCOVER_FORMATTER_SPECIAL)
               nested.visits()!=96u||nested.loads()!=15u||nested.stores()!=17u||nested.authenticated_loads()!=5u||nested.caller_store_count()!=4u||c.lr!=formatter_special_private::expected.entry_lr||
#elif defined(UNDERCOVER_FORMATTER_PARTIAL)
               nested.visits()!=95u||nested.loads()!=15u||nested.stores()!=17u||nested.authenticated_loads()!=5u||nested.caller_store_count()!=4u||
#elif defined(UNDERCOVER_FORMATTER_POST_CTR)
               nested.visits()!=84u||nested.loads()!=8u||nested.authenticated_loads()!=post_ctr_authenticated||nested.stores()!=13u||
               nested.stack_boundary_written_mask(c,nested_boundary_held)!=post_ctr_written_mask||
#else
               nested.visits()!=nested_visits||nested.loads()!=nested_loads||nested.authenticated_loads()!=nested_authenticated||nested.stores()!=nested_stores||
#endif
               host.serviced_steps()!=5u||!host.services().event_pending()||(cause.load()&mask.load())||
               host.cold_ipc_snapshot().replies)formatter_nested_refuse(5);
#ifndef UNDERCOVER_FORMATTER_CONTROL
            const auto observed=nested_cell.finish(c,nested_reached);
            if(!observed)formatter_nested_refuse(6);
            nested_cold_match+=observed->pre_guest_matches_file;
            nested_live_match+=observed->boundary_matches_file;
            nested_sample_equal+=observed->sampled_values_equal;
            std::cout<<"FORMATTER_NESTED_CELL_TRIAL n="<<trial
                <<" cold_match="<<unsigned(observed->pre_guest_matches_file)
                <<" live_match="<<unsigned(observed->boundary_matches_file)
                <<" sample_equal="<<unsigned(observed->sampled_values_equal)<<" guest_load=0\n";
#endif
#if defined(UNDERCOVER_FORMATTER_CALLER_MIXED)
            std::cout<<
#if defined(UNDERCOVER_FORMATTER_CALLER_REPORT_COPY)
                "FORMATTER_CALLER_REPORT_COPY_TRIAL n="
#elif defined(UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE)
                "FORMATTER_CALLER_REPORT_COMPARE_TRIAL n="
#elif defined(UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE)
                "FORMATTER_CALLER_REPORT_BYTE_TRIAL n="
#elif defined(UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY)
                "FORMATTER_CALLER_NEXT_ENTRY_TRIAL n="
#elif defined(UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER)
                "FORMATTER_CALLER_FINAL_INTEGER_TRIAL n="
#elif defined(UNDERCOVER_FORMATTER_CALLER_STACK_MOVE)
                "FORMATTER_CALLER_STACK_MOVE_TRIAL n="
#elif defined(UNDERCOVER_FORMATTER_CALLER_POST_MIXED)
                "FORMATTER_CALLER_POST_MIXED_TRIAL n="
#elif defined(UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE)
                "FORMATTER_CALLER_MIXED_BYTE_TRIAL n="
#else
                "FORMATTER_CALLER_MIXED_TRIAL n="
#endif
                <<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers="<<nested.caller_integer_visits()
                <<" caller_branches="<<nested.caller_branch_visits()<<" post_integers="<<nested.caller_post_integer_visits()
                <<" mixed_integers="<<nested.caller_mixed_integers()<<" mixed_taken="<<nested.caller_mixed_taken()
                <<" mixed_fallthrough="<<nested.caller_mixed_fallthrough()
                
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE
                <<" mixed_byte_verified="<<nested.caller_mixed_byte_visits()
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_MIXED
                <<" post_mixed_integers="<<nested.caller_post_mixed_integers()<<" post_mixed_taken="<<nested.caller_post_mixed_taken()
                <<" post_mixed_fallthrough="<<nested.caller_post_mixed_fallthrough()
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_STACK_MOVE
                <<" stack_move_verified="<<nested.caller_stack_move_visits()
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER
                <<" final_integer_verified="<<nested.caller_final_integer_visits()
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
                <<" next_entry_verified="<<nested.caller_next_entry_visits()<<" callee_load_executed=1 report_byte_verified="<<nested.caller_report_byte_visits()
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
                <<" compare_verified="<<nested.caller_report_compare_visits()
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
                <<" copy_verified="<<nested.caller_report_copy_visits()
#endif
#endif
#elif defined(UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY)
                <<" next_entry_verified="<<nested.caller_next_entry_visits()<<" callee_load_executed=0"
#endif
                <<" next_label_stop=1 deferred=1 reply=0 visits=98 total_visits="<<99u+nested.caller_integer_visits()+nested.caller_branch_visits()+nested.caller_post_integer_visits()+nested.caller_mixed_visits()+nested.caller_mixed_byte_visits()+nested.caller_post_mixed_visits()+nested.caller_stack_move_visits()+nested.caller_final_integer_visits()+nested.caller_next_entry_visits()+nested.caller_report_byte_visits()+nested.caller_report_compare_visits()+nested.caller_report_copy_visits()<<'\n';
#elif defined(UNDERCOVER_FORMATTER_CALLER_FOURTH_BRANCH)
            std::cout<<"FORMATTER_CALLER_FOURTH_BRANCH_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers="<<nested.caller_integer_visits()
                <<" caller_branches="<<nested.caller_branch_visits()<<" post_integers="<<nested.caller_post_integer_visits()
                <<" fallthrough=3 taken=1 alternate_checks=4 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits="<<99u+nested.caller_integer_visits()+nested.caller_branch_visits()+nested.caller_post_integer_visits()<<'\n';
#elif defined(UNDERCOVER_FORMATTER_CALLER_THIRD_BRANCH)
            std::cout<<"FORMATTER_CALLER_FRAME_LEASE_TRIAL n="<<trial<<" parent_baseline="<<formatter_nested_parent_baseline
                <<" parent_age="<<formatter_nested_parent_age<<" parent_limit="<<formatter_nested_parent_limit
                <<" held_mask="<<formatter_nested_held_mask<<'\n';
            std::cout<<"FORMATTER_CALLER_THIRD_BRANCH_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers="<<nested.caller_integer_visits()
                <<" caller_branches="<<nested.caller_branch_visits()<<" post_integers="<<nested.caller_post_integer_visits()
                <<" fallthrough=2 taken=1 alternate_checks=3 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits="<<99u+nested.caller_integer_visits()+nested.caller_branch_visits()+nested.caller_post_integer_visits()<<'\n';
#elif defined(UNDERCOVER_FORMATTER_CALLER_POST_INTEGERS)
            std::cout<<"FORMATTER_CALLER_POST_INTEGERS_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers="<<nested.caller_integer_visits()
                <<" caller_branches="<<nested.caller_branch_visits()<<" post_integers="<<nested.caller_post_integer_visits()
                <<" fallthrough=1 taken=1 alternate_guards=2 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits="<<99u+nested.caller_integer_visits()+nested.caller_branch_visits()+nested.caller_post_integer_visits()<<'\n';
#elif defined(UNDERCOVER_FORMATTER_CALLER_SECOND_BRANCH)
            std::cout<<"FORMATTER_CALLER_SECOND_BRANCH_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers="<<nested.caller_integer_visits()
                <<" caller_branches="<<nested.caller_branch_visits()
                <<" fallthrough=1 taken=1 alternate_guards=2 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits="<<99u+nested.caller_integer_visits()+nested.caller_branch_visits()<<'\n';
#elif defined(UNDERCOVER_FORMATTER_CALLER_BRANCH)
            std::cout<<"FORMATTER_CALLER_BRANCH_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers="<<nested.caller_integer_visits()
                <<" caller_branch=1 fallthrough=1 alternate_guard=1 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits="<<100u+nested.caller_integer_visits()<<'\n';
#elif defined(UNDERCOVER_FORMATTER_CALLER_INTEGERS)
            std::cout<<"FORMATTER_CALLER_INTEGERS_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers="<<nested.caller_integer_visits()
                <<" next_label_stop=1 deferred=1 reply=0 visits=98 total_visits="<<99u+nested.caller_integer_visits()<<'\n';
#elif defined(UNDERCOVER_FORMATTER_CALLER_BYTE)
            std::cout<<"FORMATTER_CALLER_BYTE_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits=99\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_ARRIVAL)
            std::cout<<"FORMATTER_CALLER_ARRIVAL_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_label=1 caller_body=0 caller_guard=0 deferred=1 reply=0 visits=98\n";
#elif defined(UNDERCOVER_FORMATTER_RETURN)
            std::cout<<"FORMATTER_RETURN_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_arrival=1 caller_body=0 caller_guard=1 deferred=1 reply=0 visits=98\n";
#elif defined(UNDERCOVER_FORMATTER_RELEASE)
            std::cout<<"FORMATTER_RELEASE_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 return_stop=1 return_executed=0 deferred=1 reply=0 visits=97\n";
#elif defined(UNDERCOVER_FORMATTER_SPECIAL)
            std::cout<<"FORMATTER_SPECIAL_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 instruction_stop=1 deferred=1 reply=0 visits=96\n";
#elif defined(UNDERCOVER_FORMATTER_PARTIAL)
            std::cout<<"FORMATTER_PARTIAL_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 instruction_stop=1 deferred=1 reply=0 visits=95\n";
#elif defined(UNDERCOVER_FORMATTER_POST_CTR)
            std::cout<<"FORMATTER_POST_CTR_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=8 stores=13 nonvolatile=3 authenticated_loads="<<post_ctr_authenticated
                <<" local_transfer=1 stack_stop=1 unresolved_load=0 deferred=1 reply=0 visits=84\n";
            std::cout<<"FORMATTER_POST_CTR_STACK_PROVENANCE_TRIAL n="<<trial
                <<" written_bytes=2 unwritten_bytes=2 mask_match=1 guest_load=0\n";
#elif defined(UNDERCOVER_FORMATTER_ARRIVAL)
            std::cout<<"FORMATTER_ARRIVAL_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 transfer_executed=1 destination_arrival=1 destination_body=0 deferred=1 reply=0 visits=77\n";
#elif defined(UNDERCOVER_FORMATTER_CONTROL)
            std::cout<<"FORMATTER_CONTROL_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 pre_transfer_stop=1 transfer_executed=0 deferred=1 reply=0 visits=76\n";
#elif defined(UNDERCOVER_FORMATTER_THIRD)
            std::cout<<"FORMATTER_THIRD_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=5 stores=13 nonvolatile="<<nested_saved
                <<" authenticated_loads="<<nested.authenticated_loads()
                <<" conditional_loads=2 pre_load_stop=1 deferred=1 reply=0 visits=74\n";
#elif defined(UNDERCOVER_FORMATTER_SECOND)
            std::cout<<"FORMATTER_SECOND_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=2 stores=12 nonvolatile=3 conditional_load=1 pre_load_stop=1 deferred=1 reply=0 visits=44\n";
#else
            std::cout<<"FORMATTER_NESTED_TRIAL n="<<trial
                <<" native_prefix=1 frame=48 loads=1 stores=12 nonvolatile=3 pre_load_stop=1 deferred=1 reply=0 visits=35\n";
#endif
            formatter_nested=nullptr;
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
            formatter_report_byte.reset();
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
            formatter_report_compare.reset();
#endif
#endif
#endif
#endif
            post_stm_formatter_leaf=nullptr;
        }
#endif
        post_stm_formatter=nullptr;
#endif
        post_stm_resume=nullptr;
#endif
        post_stm_dependency=nullptr;
#endif
        post_stm_helper=nullptr;
#endif
        post_stm_report=nullptr;post_stm_version_data=nullptr;
#endif
        post_stm_version_msr=0;
#endif
        post_stm_objects=nullptr;
#endif
#endif
        post_stm_frame=nullptr;
#endif
#endif
#endif
#endif
        third_return_route=nullptr;third_return_join=nullptr;
#endif
#endif
#endif
        third_vector=nullptr;third_frame_ptr=nullptr;third_memory=nullptr;third_context=third_wait=0;
#endif
#else
        need(stm_event_return->reached(c,async_held(c))&&host.serviced_steps()==5u&&
             host.services().event_pending()&&!host.exception_pending(c.msr));
#endif
        std::cout<<"STM_EVENT_RETURN_TRIAL n="<<trial<<" original_flag=1 restore_entry=1 masked=1 deferred=1 visits="<<stm_event_return->visits()
                 <<" stores="<<stm_event_return->stores()<<'\n';
        stm_event_return.reset();
#else
        need(async_wrapper->reached(c,async_held(c),ioctl_prefix->caller_abi(c))&&host.serviced_steps()==5u&&
             host.services().event_pending()&&!host.exception_pending(c.msr));
#endif
        std::cout<<"ASYNC_WRAPPER_TRIAL n="<<trial<<" original_return=1 masked=1 abi=1 deferred=1 visits="<<async_wrapper->visits()
                 <<" loads="<<async_wrapper->loads()<<" restored="<<async_wrapper->restored()<<" polls="<<async_wrapper->polls()<<'\n';
        async_wrapper.reset();
#else
        need(async_return->reached(c,async_held(c),ioctl_submit_prefix->caller_abi(c))&&host.serviced_steps()==5u&&
             host.services().event_pending()&&!host.exception_pending(c.msr));
#endif
        std::cout<<"IPC_DEFERRED_TRIAL n="<<trial<<" original_boundary=1 deferred=1 pending_ack=1 masked=1 cpu_preserved=1 ring_preserved=1 request_preserved=1 reply=0 ios_steps=5\n";
        std::cout<<"ASYNC_SUBMIT_TRIAL n="<<trial<<" original_return=1 masked=1 abi=1 deferred=1 visits="<<async_return->visits()<<" polls="<<async_return->polls()<<'\n';
        async_return.reset();
#elif defined(UNDERCOVER_IPC_DEFERRED)
        // At this exact original local return, all preceding native
        // instructions and both actual mailbox writes have been proved.
        // Accept at the masked device boundary, not by synthesizing a
        // guest reply or invoking its callback.
        const auto pack_cr=[](const auto& cpu){uint32_t v=0;for(auto f:cpu.cr)
            v=(v<<4)|(unsigned(f.lt)<<3)|(unsigned(f.gt)<<2)|unsigned(f.eq)<<1|unsigned(f.so);return v;};
        const auto gp=c.gpr;const auto gqr=c.gqr;
        const auto pc=c.pc,lr=c.lr,ctr=c.ctr,xer=c.xer,msr=c.msr,srr0=c.srr0,srr1=c.srr1,cr=pack_cr(c);
        const auto ticks=c.inst_count;
        if(!ioctl_dispatch->reached(c,ioctl_dispatch_held(c))||ioctl_event_gate->stage()!=3u||
           !ioctl_event_gate->accept(c.msr,ioctl_dispatch_storage_held(c)))ioctl_dispatch_refuse(8);
        const auto pending=host.cold_ipc_snapshot();
        const bool held=ioctl_event_gate->deferred_held(ioctl_dispatch_storage_held(c,true));
        if(!held||!ioctl_dispatch->reached(c,held)||c.gpr!=gp||c.gqr!=gqr||c.pc!=pc||c.lr!=lr||
           c.ctr!=ctr||c.xer!=xer||c.msr!=msr||c.srr0!=srr0||c.srr1!=srr1||pack_cr(c)!=cr||
           c.inst_count!=ticks||host.exception_pending(c.msr)||pending.steps!=5u||pending.queued||
           !pending.event||pending.replies||!host.services().event_pending())ioctl_dispatch_refuse(8);
        ++ioctl_deferred_count;
        std::cout<<"IPC_DEFERRED_TRIAL n="<<trial<<" original_boundary=1 deferred=1 pending_ack=1 masked=1 cpu_preserved=1 ring_preserved=1 request_preserved=1 reply=0 ios_steps=5\n";
#endif
        ioctl_dispatch.reset();ioctl_event_gate.reset();ioctl_dispatch_cpu=nullptr;
#endif
        ioctl_profile.reset();
#endif
        ioctl_submit_queue.reset();ioctl_header_lines=0;
#else
        std::cout<<"V1407_HEADER_TRIAL n="<<trial<<" original_flush=1 native_rfi=1 masked=1 request_preserved=1 lines="<<ioctl_flush->lines()<<'\n';
        ioctl_flush.reset();
#endif
        ioctl_header_shadow.clear();
#endif
        ioctl_submit_prefix.reset();
#endif
        ioctl_tail.reset();
#else
        std::cout<<"V1398_FLUSH_TRIAL n="<<trial<<" original_flush=1 native_rfi=1 masked=1 lines="<<ioctl_flush->lines()<<" empty="<<ioctl_flush->zero()<<'\n';
        ioctl_flush.reset();
#endif
#endif
        ioctl_build=nullptr;
#endif
        ioctl_alloc=nullptr;
#endif
        ioctl_prefix=nullptr;
#endif
        stm_ioctl=nullptr;
#endif
        open_return=nullptr;second_open_capture=nullptr;
        need(
#else
        bool freed2=false;try{run_game(c);}catch(const AllocatorReturned&){freed2=true;}
        need(freed2&&allocator2.returned(c,allocator_held(c))&&allocator2.inline_completed()&&
#endif
             descriptor.second_completed()&&second_release_count==trial+1u&&second_allocator_count==trial+1u&&
#ifdef UNDERCOVER_IPC_DEFERRED
             host.serviced_steps()==5u&&epoch.acknowledged_descriptors(3u-kind)&&
#ifdef UNDERCOVER_STM_DEFERRED_ACK
             !(cause.load()&mask.load())&&third_ack_count==trial+1u&&
#else
             (cause.load()&mask.load())==H::PI_HOLLYWOOD&&
#endif
             host.services().event_pending()&&ioctl_deferred_count==trial+1u);
#else
             host.serviced_steps()==4u&&epoch.acknowledged_descriptors(3u-kind)&&!(cause.load()&mask.load()));
#endif
        std::cout<<"V1378_FREE_TRIAL n="<<trial<<" native_free=1 heap_shadow=1 metadata_shadow=1 caller_abi=1 inline_return=1 stores="<<allocator2.stores()<<" heap="<<allocator2.heap_stores()<<'\n';
        submit_resume_active=false;submit_resume=nullptr;second_resume_capture=nullptr;
        allocator_active=false;allocator_release=nullptr;allocator_descriptor=nullptr;
#endif
        selection_route=nullptr;selection_witness=nullptr;load_active=false;coop_load=nullptr;load_save=nullptr;
        sleep_active=false;sleep_resume=nullptr;exit_active=false;sleep_exit=nullptr;
#endif
        coop_saved=nullptr;second_irq_kind=0;
#endif
        second_scheduler_lane=false;
#endif
        sched_join=nullptr;witness=nullptr;si_ack=nullptr;
#ifdef UNDERCOVER_V1320_SAVE_CONTINUITY
        coop_saved=nullptr;
#endif
    }
    need(callbacks==16&&control_writes==8&&stm_entries==8&&open_entries==8);
#ifdef UNDERCOVER_V1315_COOP_SAVE
    need(coop_save_count==8u);
    std::cout<<"V1315_SAVE_NATIVE owner=1 trials=8 native_save=8 original_return=8 saved_abi=8 gqr=8 idle_preserved=8 fallback=0 thread_resumed=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1256_OPEN_POLLS restore=16 backward="<<loop_polls<<"\n";
    std::cout<<"V1256_SCHED_NATIVE owner=1 trials=8 submitted=8 ack=8 waiting=8 saved=8 idle=8 ee=8 pending_irq=8 irq_entered=0 reply=0 seeded_thread=1 synthetic_ack=1 synthetic_caller=1 synthetic_bridge=1 seeded_vector=1 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1259_IRQ_ENTRY
    need(irq_count==8u);
    std::cout<<"V1259_IRQ_NATIVE owner=1 trials=8 entered=8 saved=8 idle=8 pending_ack=8 vector_executed=0 reply=0 seeded_vector=1 fallback=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1260_IRQ_VECTOR
    need(vector_count==8u);
    std::cout<<"V1260_VECTOR_NATIVE owner=1 trials=8 original_vector=8 trampoline=8 saved_fields=38 dispatcher_entry=8 dispatcher_executed=0 pending_ack=8 reply=0 fallback=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1261_IPC_DISPATCH
    need(dispatch_count==8u);
    std::cout<<"V1261_DISPATCH_NATIVE owner=1 trials=8 dispatcher=8 ipc_index=27 handler_entry=8 handler_executed=0 pending_ack=8 reply=0 fallback=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1266_JOINED_ACK
    need(joined_count==8u);
    std::cout<<"V1266_ACK_NATIVE owner=1 trials=8 original_dispatch=8 original_handler_return=8 native_reply=8 waiting=8 saved_fields=38 modeled_dispatch=0 wakeup=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1271_IPC_RETURN
    need(rfi_count==8u&&reply_vector_count==8u);
    std::cout<<"V1271_REPLY_VECTOR_NATIVE owner=1 trials=8 first_rfi=8 restored=8 reply_irq=8 original_vector=8 trampoline=8 saved_fields=38 second_dispatch=0 wakeup=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1275_REPLY_ENTRY
    need(second_dispatch_count==8u&&reply_entry_count==8u);
    std::cout<<"V1275_REPLY_ENTRY_NATIVE owner=1 trials=8 original_second_dispatch=8 original_reply_handler=8 reply_processor_entry=8 waiting=8 ios_steps=2 wakeup=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1282_REPLY_WAKE
    need(wake_entry_count==8u);
    std::cout<<"V1282_REPLY_WAKE_NATIVE owner=1 trials=8 original_processor=8 armmsg=8 native_dcbi=8 y1_w1c=8 original_wake_entry=8 waiting=8 ios_steps=2 wake_executed=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1289_WAKE_READY
    need(ready_count==8u);
    std::cout<<"V1289_WAKE_READY_NATIVE owner=1 trials=8 original_wake=8 nested_disable=8 drained=8 ready=8 enrolled=8 select_executed=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1292_NESTED_WAKE
    need(nested_count==8u);
    std::cout<<"V1292_NESTED_NATIVE owner=1 trials=8 original_select_return=8 original_restore=8 original_wake_return=8 ready=8 thread_resumed=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1300_REPLY_RETURN
    need(return_count==8u);
    std::cout<<"V1300_REPLY_RETURN_NATIVE owner=1 trials=8 original_processor_return=8 original_handler_return=8 latch_clear=8 ready=8 ios_steps=2 thread_resumed=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1305_READY_IDLE_RETURN
    need(idle_return_count==8u);
    std::cout<<"V1305_READY_IDLE_NATIVE owner=1 trials=8 original_epilogue=8 native_rfi=8 idle_restored=8 ready_preserved=8 ios_steps=2 thread_resumed=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1320_SAVE_CONTINUITY
    need(coop_idle_count==8u);
    std::cout<<"V1320_IDLE_SAVE_NATIVE owner=1 trials=8 native_save=8 complete_context=8 second_idle_rfi=8 ready=8 ios_steps=2 thread_resumed=0 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1328_IDLE_SELECTION
    need(selection_count==8u);
    std::cout<<"V1328_SELECTION_NATIVE owner=1 trials=8 original_clear=8 original_callback=8 original_set=8 loader_entry=8 preserved=8 thread_resumed=0 ios_steps=2 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1334_COOP_LOAD
    need(load_count==8u);
    std::cout<<"V1334_COOPERATIVE_LOAD_NATIVE owner=1 trials=8 original_loader=8 native_rfi=8 saved_abi=8 gqr=8 cooperative_return=8 sleep_return=0 ios_steps=2 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1336_SLEEP_RESUME
    need(resumed_sleep_count==8u);
    std::cout<<"V1336_SLEEP_NATIVE owner=1 trials=8 native_rfi=8 select_return=8 sleep_stack=8 saved_abi=8 restore_entry=8 sleep_return=0 ios_steps=2 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1340_SLEEP_EXIT
    need(sleep_exit_count==8u);
    std::cout<<"V1340_SLEEP_EXIT_NATIVE owner=1 trials=8 nested_restore=8 sleep_return=8 submit_resume=8 caller_abi=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1344_SUBMIT_RESUME
    need(release_count==8u);
    std::cout<<"V1344_SUBMIT_NATIVE owner=1 trials=8 outer_restore=8 reply_held=8 free_entry=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1352_ALLOCATOR_RELEASE
    need(allocator_count==8u);
    std::cout<<"V1352_ALLOCATOR_NATIVE owner=1 trials=8 native_free=8 heap_shadow=8 caller_abi=8 inline_return=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0\n";
#ifdef UNDERCOVER_V1358_OPEN_RETURN
    need(open_return_count==8u);
#ifdef UNDERCOVER_V1359_SECOND_OPEN
    need(second_open_count==8u);
#ifdef UNDERCOVER_V1364_SECOND_REQUEST
    need(second_request_count==8u&&second_request_vectors==8u&&second_request_returns==8u);
#ifdef UNDERCOVER_V1366_SECOND_SUBMIT
    need(second_submit_count==8u&&second_submit_vectors==8u&&second_submit_returns==8u);
#ifdef UNDERCOVER_V1368_SECOND_SCHEDULER
    need(second_sleep_count==8u&&second_scheduler_count==8u&&second_save_count==8u);
#ifdef UNDERCOVER_V1370_SECOND_REPLY
#ifdef UNDERCOVER_V1374_SECOND_RESTORE
#ifdef UNDERCOVER_V1378_SECOND_FREE
    need(second_release_count==8u&&second_allocator_count==8u);
#ifdef UNDERCOVER_V1379_SECOND_RETURN
    need(second_open_return_count==8u);
#ifdef UNDERCOVER_V1383_STM_IOCTL_ENTRY
    need(stm_ioctl_count==8u);
#ifdef UNDERCOVER_V1386_IOCTL_PREFIX
    need(ioctl_prefix_count==8u);
#ifdef UNDERCOVER_V1387_IOCTL_ALLOCATION
    need(ioctl_alloc_count==8u);
#ifdef UNDERCOVER_V1392_IOCTL_CONSTRUCTION
    need(ioctl_build_count==8u);
#ifdef UNDERCOVER_V1398_IOCTL_FLUSH
    need(ioctl_flush_count==8u);
#ifdef UNDERCOVER_V1401_IOCTL_OUTPUT
    need(ioctl_output_count==8u&&ioctl_submit_count==8u);
#ifdef UNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX
    need(ioctl_header_entry_count==8u&&ioctl_queue_init_count+ioctl_queue_skip_count==8u);
#ifdef UNDERCOVER_V1407_IOCTL_HEADER
    need(ioctl_header_return_count==8u);
#ifdef UNDERCOVER_V1410_IOCTL_QUEUE
    need(ioctl_queue_entry_count==8u);
#ifdef UNDERCOVER_IPC_PROFILE
    need(ioctl_profile_return_count==8u);
#ifdef UNDERCOVER_IPC_DISPATCH
    need(ioctl_dispatch_count==8u);
#ifdef UNDERCOVER_IPC_DEFERRED
    need(ioctl_deferred_count==8u);
#ifdef UNDERCOVER_ASYNC_SUBMIT_RETURN
    need(async_return_count==8u);
#ifdef UNDERCOVER_ASYNC_WRAPPER_RETURN
    need(async_wrapper_count==8u);
#ifdef UNDERCOVER_STM_EVENT_RETURN
    need(stm_event_return_count==8u);
#ifdef UNDERCOVER_STM_OUTER_RESTORE
    need(stm_outer_count==8u&&stm_irq_entry_count==8u);
#ifdef UNDERCOVER_STM_DEFERRED_VECTOR
    need(third_vector_count==8u);
#ifdef UNDERCOVER_STM_DEFERRED_DISPATCH
    need(third_dispatch_count==8u);
#ifdef UNDERCOVER_STM_DEFERRED_ACK
    need(third_ack_count==8u);
#ifdef UNDERCOVER_STM_DEFERRED_ACTIVE_RETURN
    need(third_return_count==8u);
#ifdef UNDERCOVER_STM_RESUMED_RESTORE
    need(third_resume_count==8u);
#ifdef UNDERCOVER_STM_FINAL_RETURN
    need(stm_final_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_ENTRY
    need(post_stm_sc_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_DISABLE
    need(post_stm_disable_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_DECISION
    need(post_stm_decision_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_RESTORE
    need(post_stm_restore_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_VERSION
    need(post_stm_version_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_REPORT
    need(post_stm_report_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_HELPER
    need(post_stm_helper_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY
    need(post_stm_dependency_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_REPORT_RESUME
    need(post_stm_resume_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER
    need(post_stm_formatter_count==8u);
#ifdef UNDERCOVER_POST_STM_SC_FORMATTER_LEAF
    need(post_stm_formatter_leaf_count==8u);
#ifdef UNDERCOVER_FORMATTER_CONTINUATION
    need(formatter_continuation_count==8u);
#ifdef UNDERCOVER_FORMATTER_NESTED
    need(formatter_nested_count==8u);
#ifndef UNDERCOVER_FORMATTER_CONTROL
    std::cout<<"FORMATTER_NESTED_CELL_NATIVE owner=1 trials=8 cold_match="<<nested_cold_match
        <<" live_match="<<nested_live_match<<" sample_equal="<<nested_sample_equal
        <<" endpoint_only=1 guest_loads=0 guest_writes=0\n";
#endif
#if defined(UNDERCOVER_FORMATTER_CALLER_MIXED)
    std::cout<<
#if defined(UNDERCOVER_FORMATTER_CALLER_REPORT_COPY)
        "FORMATTER_CALLER_REPORT_COPY_NATIVE"
#elif defined(UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE)
        "FORMATTER_CALLER_REPORT_COMPARE_NATIVE"
#elif defined(UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE)
        "FORMATTER_CALLER_REPORT_BYTE_NATIVE"
#elif defined(UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY)
        "FORMATTER_CALLER_NEXT_ENTRY_NATIVE"
#elif defined(UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER)
        "FORMATTER_CALLER_FINAL_INTEGER_NATIVE"
#elif defined(UNDERCOVER_FORMATTER_CALLER_STACK_MOVE)
        "FORMATTER_CALLER_STACK_MOVE_NATIVE"
#elif defined(UNDERCOVER_FORMATTER_CALLER_POST_MIXED)
        "FORMATTER_CALLER_POST_MIXED_NATIVE"
#elif defined(UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE)
        "FORMATTER_CALLER_MIXED_BYTE_NATIVE"
#else
        "FORMATTER_CALLER_MIXED_NATIVE"
#endif
        " owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers="<<8u*formatter_caller_integer_private::path.size()
        <<" caller_branches=32 post_integers="<<8u*formatter_caller_post_integer_private::path.size()
        <<" mixed_integers="<<8u*UNDERCOVER_EXPECTED_CALLER_MIXED_INTEGERS<<" mixed_taken="<<8u*UNDERCOVER_EXPECTED_CALLER_MIXED_TAKEN
        <<" mixed_fallthrough="<<8u*UNDERCOVER_EXPECTED_CALLER_MIXED_FALLTHROUGH
        
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE
        <<" mixed_bytes_verified=8"
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_MIXED
        <<" post_mixed_integers=8 post_mixed_taken=8 post_mixed_fallthrough=0"
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_STACK_MOVE
        <<" stack_moves_verified=8"
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER
        <<" final_integers_verified=8"
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
        <<" next_entries_verified=8 callee_loads_executed=8 report_bytes_verified=8"
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
        <<" compares_verified=8"
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
        <<" copies_verified=8"
#endif
#endif
#elif defined(UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY)
        <<" next_entries_verified=8 callee_loads_executed=0"
#endif
        <<" next_label_stop=8 deferred=8 reply=0 visits=784 total_visits="<<824u+8u*(formatter_caller_integer_private::path.size()+formatter_caller_post_integer_private::path.size()+formatter_caller_mixed_private::path.size()
#ifdef UNDERCOVER_FORMATTER_CALLER_MIXED_BYTE
        +1u
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_POST_MIXED
        +formatter_caller_post_mixed_private::path.size()
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_STACK_MOVE
        +1u
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_FINAL_INTEGER
        +1u
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_NEXT_ENTRY
        +1u
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_BYTE
        +1u
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COMPARE
        +1u
#endif
#ifdef UNDERCOVER_FORMATTER_CALLER_REPORT_COPY
        +1u
#endif
        )
        <<" ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_FOURTH_BRANCH)
    std::cout<<"FORMATTER_CALLER_FOURTH_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers="<<8u*formatter_caller_integer_private::path.size()
        <<" caller_branches=32 post_integers="<<8u*formatter_caller_post_integer_private::path.size()
        <<" fallthrough=24 taken=8 alternate_checks=32 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits="<<824u+8u*(formatter_caller_integer_private::path.size()+formatter_caller_post_integer_private::path.size())
        <<" ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_THIRD_BRANCH)
    std::cout<<"FORMATTER_CALLER_THIRD_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers="<<8u*formatter_caller_integer_private::path.size()
        <<" caller_branches=24 post_integers="<<8u*formatter_caller_post_integer_private::path.size()
        <<" fallthrough=16 taken=8 alternate_checks=24 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits="<<816u+8u*(formatter_caller_integer_private::path.size()+formatter_caller_post_integer_private::path.size())
        <<" ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_POST_INTEGERS)
    std::cout<<"FORMATTER_CALLER_POST_INTEGERS_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers="<<8u*formatter_caller_integer_private::path.size()
        <<" caller_branches=16 post_integers="<<8u*formatter_caller_post_integer_private::path.size()
        <<" fallthrough=8 taken=8 alternate_guards=16 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits="<<808u+8u*(formatter_caller_integer_private::path.size()+formatter_caller_post_integer_private::path.size())
        <<" ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_SECOND_BRANCH)
    std::cout<<"FORMATTER_CALLER_SECOND_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers="<<8u*formatter_caller_integer_private::path.size()
        <<" caller_branches=16 fallthrough=8 taken=8 alternate_guards=16 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits="<<808u+8u*formatter_caller_integer_private::path.size()
        <<" ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_BRANCH)
    std::cout<<"FORMATTER_CALLER_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers="<<8u*formatter_caller_integer_private::path.size()
        <<" caller_branches=8 fallthrough=8 alternate_guard=8 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits="<<800u+8u*formatter_caller_integer_private::path.size()
        <<" ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_INTEGERS)
    std::cout<<"FORMATTER_CALLER_INTEGERS_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers="<<8u*formatter_caller_integer_private::path.size()
        <<" next_label_stop=8 deferred=8 reply=0 visits=784 total_visits="<<792u+8u*formatter_caller_integer_private::path.size()
        <<" ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_BYTE)
    std::cout<<"FORMATTER_CALLER_BYTE_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits=792 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CALLER_ARRIVAL)
    std::cout<<"FORMATTER_CALLER_ARRIVAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_label=8 caller_body=0 caller_guard=0 deferred=8 reply=0 visits=784 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_RETURN)
    std::cout<<"FORMATTER_RETURN_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_arrival=8 caller_body=0 caller_guard=8 deferred=8 reply=0 visits=784 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_RELEASE)
    std::cout<<"FORMATTER_RELEASE_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 return_stop=8 return_executed=0 deferred=8 reply=0 visits=776 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_SPECIAL)
    std::cout<<"FORMATTER_SPECIAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=24 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 instruction_stop=8 deferred=8 reply=0 visits=768 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_PARTIAL)
    std::cout<<"FORMATTER_PARTIAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=24 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 instruction_stop=8 deferred=8 reply=0 visits=760 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_POST_CTR)
    std::cout<<"FORMATTER_POST_CTR_NATIVE owner=1 trials=8 native_prefix=8 loads=64 stores=104 nonvolatile=24 authenticated_loads="<<8u*post_ctr_authenticated
        <<" local_transfer=8 stack_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=672 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_ARRIVAL)
    std::cout<<"FORMATTER_ARRIVAL_NATIVE owner=1 trials=8 native_prefix=8 loads=48 stores=104 nonvolatile=24 authenticated_loads=40 conditional_loads=24 ctr_match=8 destination_word=8 transfer_executed=8 destination_arrival=8 destination_body=0 deferred=8 reply=0 visits=616 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_CONTROL)
    std::cout<<"FORMATTER_CONTROL_NATIVE owner=1 trials=8 native_prefix=8 loads=48 stores=104 nonvolatile=24 authenticated_loads=40 conditional_loads=24 ctr_match=8 destination_word=8 pre_transfer_stop=8 transfer_executed=0 deferred=8 reply=0 visits=608 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_THIRD)
    std::cout<<"FORMATTER_THIRD_NATIVE owner=1 trials=8 native_prefix=8 loads=40 stores=104 nonvolatile="<<8u*nested_saved
        <<" authenticated_loads="<<8u*nested_authenticated
        <<" conditional_loads=16 pre_load_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=592 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#elif defined(UNDERCOVER_FORMATTER_SECOND)
    std::cout<<"FORMATTER_SECOND_NATIVE owner=1 trials=8 native_prefix=8 loads=16 stores=96 nonvolatile=24 conditional_loads=8 pre_load_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=352 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#else
    std::cout<<"FORMATTER_NESTED_NATIVE owner=1 trials=8 native_prefix=8 loads=8 stores=96 nonvolatile=24 pre_load_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=280 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
#endif
    std::cout<<"FORMATTER_CONTINUATION_NATIVE owner=1 trials=8 native_resume=8 next_entry=8 arguments=32 frame_held=8 deferred=8 reply=0 visits=80 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_FORMATTER_LEAF_NATIVE owner=1 trials=8 native_leaf=8 original_return=8 exact_value=8 loads=8 stores=0 frame_held=8 deferred=8 reply=0 visits=64 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_FORMATTER_NATIVE owner=1 trials=8 original_formatter=8 native_stores=32 native_loads=8 saved_nonvolatile=128 original_dependency_entry=8 deferred=8 reply=0 dependency_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_REPORT_RESUME_NATIVE owner=1 trials=8 original_resume=8 formatter_entry=8 arguments=32 deferred=8 reply=0 formatter_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_REPORT_DEPENDENCY_NATIVE owner=1 trials=8 native_leaf=8 original_return=8 deferred=8 reply=0 caller_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_REPORT_HELPER_NATIVE owner=1 trials=8 original_prefix=8 native_stores=40 saved_nonvolatile=24 original_next_entry=8 deferred=8 reply=0 next_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_REPORT_NATIVE owner=1 trials=8 original_prologue=8 native_stores=112 va_abi=8 original_helper_entry=8 deferred=8 reply=0 helper_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_VERSION_NATIVE owner=1 trials=8 original_pointer=8 original_thunk=8 diagnostic_abi=8 original_tail=8 deferred=8 reply=0 report_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_RESTORE_NATIVE owner=1 trials=8 native_msr=8 quiet_poll=8 original_suffix=8 original_return=8 deferred=8 reply=0 version_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_DECISION_NATIVE owner=1 trials=8 cold_bss=8 original_branch=8 native_load=8 native_stores=16 restore_entry=8 deferred=8 reply=0 restore_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_DISABLE_NATIVE owner=1 trials=8 original_disable=8 native_msr=8 previous_ee=8 sc_return=8 deferred=8 reply=0 decision_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"POST_STM_SC_NATIVE owner=1 trials=8 original_osinit_call=8 original_sc_prefix=8 disable_entry=8 deferred=8 reply=0 disable_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"STM_FINAL_RETURN_NATIVE owner=1 trials=8 original_stm_return=8 state_store=8 caller_abi=8 deferred=8 reply=0 osinit_instruction_executed=0 modeled_osinit_bridge=1 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"STM_RESUMED_RESTORE_NATIVE owner=1 trials=8 native_resume=8 original_restore_return=8 stm_caller=8 deferred=8 reply=0 stm_instruction_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"STM_DEFERRED_ACTIVE_RETURN_NATIVE owner=1 trials=8 native_rfi=8 original_epilogue=8 active_context=8 deferred=8 reply=0 resume_instruction_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"STM_DEFERRED_ACK_NATIVE owner=1 trials=8 original_return=8 guest_w1c=8 credit=8 unissued=8 deferred=8 reply=0 active_context=8 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"STM_DEFERRED_DISPATCH_NATIVE owner=1 trials=8 original_dispatch=8 handler_index=27 active_context=8 pending_ack=8 deferred=8 handler_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"STM_DEFERRED_VECTOR_NATIVE owner=1 trials=8 original_vector=8 original_trampoline=8 active_context=8 saved_fields=38 deferred=8 pending_ack=8 dispatcher_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"STM_DEFERRED_IRQ_NATIVE owner=1 trials=8 original_mtmsr=8 ee=8 entered=8 active_thread=8 pending_ack=8 deferred=8 ios_steps=5 vector_executed=0 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"STM_EVENT_RETURN_NATIVE owner=1 trials=8 original_flag=8 restore_entry=8 masked=8 deferred=8 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"ASYNC_WRAPPER_NATIVE owner=1 trials=8 original_return=8 masked=8 abi=8 deferred=8 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"ASYNC_SUBMIT_NATIVE owner=1 trials=8 original_return=8 masked=8 abi=8 deferred=8 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"IPC_DEFERRED_NATIVE owner=1 trials=8 original_boundary=8 deferred=8 pending_ack=8 cpu_preserved=8 request_preserved=8 reply=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"IPC_DISPATCH_NATIVE owner=1 trials=8 original_return=8 ring_dequeued=8 mailbox_submitted=8 queued=8 ios_steps=4 deferred=0 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"IPC_PROFILE_NATIVE owner=1 trials=8 profile_return=8 ring_preserved=8 request_preserved=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1410_QUEUE_NATIVE owner=1 trials=8 nested_disable=8 queue_entry=8 request_preserved=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1407_HEADER_NATIVE owner=1 trials=8 header_flush_return=8 native_rfi=8 request_preserved=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1406_QUEUE_PATH initialized="<<ioctl_queue_init_count<<" skipped="<<ioctl_queue_skip_count<<"\n";
    std::cout<<"V1404_PREFIX_NATIVE owner=1 trials=8 submit=8 queue_path_verified=8 header_flush_entry=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1401_OUTPUT_NATIVE owner=1 trials=8 second_flush_return=8 native_rfi=8 submit_entry=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1398_FLUSH_NATIVE owner=1 trials=8 first_flush_return=8 native_rfi=8 masked=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1392_CONSTRUCTION_NATIVE owner=1 trials=8 request=8 first_flush_entry=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1387_ALLOCATION_NATIVE owner=1 trials=8 allocation_return=8 heap_shadow=8 metadata_shadow=8 masked=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1386_PREFIX_NATIVE owner=1 trials=8 allocator_entry=8 original_save=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1383_IOCTL_NATIVE owner=1 trials=8 original_stm=8 native_disable=8 ioctl_entry=8 event_fd=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1379_OPEN_NATIVE owner=1 trials=8 second_submit_return=8 second_open_return=8 stm_resume=8 fd=1 ios_steps=4 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1378_FREE_NATIVE owner=1 trials=8 second_free=8 heap_shadow=8 metadata_shadow=8 abi=8 inline_return=8 ios_steps=4 fd=1 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    need(second_ready_count==8u&&second_nested_count==8u&&second_return_count==8u&&second_idle_return_count==8u&&
         second_selection_count==8u&&second_load_count==8u&&second_resumed_sleep_count==8u&&second_sleep_exit_count==8u);
    std::cout<<"V1374_RESTORE_NATIVE owner=1 trials=8 wake=8 handler_return=8 idle_rfi=8 selection=8 cooperative_rfi=8 sleep_return=8 ios_steps=4 fd=1 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    need(second_ack_irq_count==8u&&second_ack_vector_count==8u&&second_ack_dispatch_count==8u&&second_ack_return_count==8u&&
         second_reply_rfi_count==8u&&second_reply_vector2_count==8u&&second_reply_dispatch2_count==8u&&second_reply_entry2_count==8u&&second_wake_entry_count==8u);
    std::cout<<"V1370_REPLY_NATIVE owner=1 trials=8 ack_irq=8 original_ack_return=8 native_reply=8 native_rfi=8 reply_irq=8 original_processor=8 wake_entry=8 ios_steps=4 fd=1 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1368_SCHED_NATIVE owner=1 trials=8 second_sleep=8 second_save=8 idle_reused=8 ee=8 pending_ack=8 ios_steps=3 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1366_SUBMIT_NATIVE owner=1 trials=8 submitted=8 ack=8 second_fd=8 first_fd_held=8 native_rfi=8 ios_steps=3 second_reply=0 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1364_REQUEST_NATIVE owner=1 trials=8 request=8 opposite_path=8 native_rfi=8 first_fd_held=8 ios_steps=2 second_submitted=0 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1359_SECOND_NATIVE owner=1 trials=8 second_entry=8 opposite_path=8 descriptor_store=8 first_fd_held=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0\n";
#endif
    std::cout<<"V1358_OPEN_NATIVE owner=1 trials=8 submit_return=8 open_return=8 stm_resume=8 descriptor=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0\n";
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
#endif
#endif
#endif
#endif
#endif
#endif
}catch(const WitnessFailure&){
    std::cout<<"V1256_OPEN_FAILURE kind=witness trial="<<last_trial<<" stage="<<last_stage<<" reason="<<last_reason<<" line=0\n";return 1;
}catch(const HarnessFailure& e){
    std::cout<<"V1256_OPEN_FAILURE kind=assertion trial="<<last_trial<<" stage="<<last_stage<<" reason=0 line="<<e.line<<"\n";return 1;
}catch(const std::exception& e){
    const std::string_view msg=e.what();
    const char* kind="other";
    if(msg=="V1256 interpreter forbidden")kind="interpreter";
    else if(msg=="V1256 unexpected syscall")kind="syscall";
    else if(msg=="V1256 null branch")kind="null_branch";
    else if(msg=="V1256 unexpected MMIO16"||msg=="V1256 unexpected MMIO read"||msg=="V1256 unexpected MMIO write")kind="mmio";
    else if(msg=="unexpected cold IPC control write"||msg=="cold IPC proof already rejected")kind="mailbox";
    std::cout<<"V1256_OPEN_FAILURE kind="<<kind<<" trial="<<last_trial<<" stage="<<last_stage<<" reason=0 line=0\n";return 1;
}
