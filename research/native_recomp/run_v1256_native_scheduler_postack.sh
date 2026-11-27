#!/usr/bin/env bash
set -euo pipefail
reply_entry_mode=0;reply_body_mode=0;wake_ready_mode=0;nested_wake_mode=0;reply_return_mode=0;ready_idle_mode=0;coop_save_mode=0;reply_helper_mode=0;save_continuity_mode=0;selection_mode=0;coop_load_mode=0;sleep_resume_mode=0;sleep_exit_mode=0;submit_resume_mode=0;allocator_release_mode=0;allocator_metadata_mode=0;open_return_mode=0;second_open_mode=0;second_request_mode=0;second_submit_mode=0;second_scheduler_mode=0;second_reply_mode=0;second_restore_mode=0;second_free_mode=0;second_return_mode=0;stm_ioctl_mode=0;ioctl_prefix_mode=0;ioctl_alloc_mode=0;ioctl_build_mode=0;ioctl_flush_mode=0;ioctl_output_mode=0;ioctl_submit_prefix_mode=0;ioctl_header_mode=0;ioctl_queue_mode=0;ipc_profile_mode=0;ipc_dispatch_mode=0;ipc_deferred_mode=0;async_return_mode=0;async_wrapper_mode=0;stm_event_return_mode=0;stm_outer_mode=0;stm_vector_mode=0;stm_dispatch_mode=0;stm_ack_mode=0;stm_active_return_mode=0;stm_resumed_restore_mode=0;stm_final_return_mode=0;post_stm_sc_mode=0;post_stm_disable_mode=0;post_stm_decision_mode=0;post_stm_restore_mode=0;post_stm_version_mode=0;post_stm_report_mode=0;post_stm_helper_mode=0;post_stm_dependency_mode=0;post_stm_resume_mode=0;post_stm_formatter_mode=0;post_stm_formatter_leaf_mode=0;formatter_continuation_mode=0;formatter_nested_mode=0;formatter_second_mode=0;formatter_third_mode=0;formatter_control_mode=0;formatter_arrival_mode=0;formatter_post_ctr_mode=0;formatter_partial_mode=0
if [[ $# == 4 && "$4" == --formatter-nested-partial ]];then
  formatter_partial_mode=1
  set -- "$1" "$2" "$3" --formatter-nested-post-ctr
fi
if [[ $# == 4 && "$4" == --formatter-nested-post-ctr ]];then
  formatter_post_ctr_mode=1
  set -- "$1" "$2" "$3" --formatter-nested-arrival
fi
if [[ $# == 4 && "$4" == --formatter-nested-arrival ]];then
  formatter_arrival_mode=1
  set -- "$1" "$2" "$3" --formatter-nested-control
fi
if [[ $# == 4 && "$4" == --formatter-nested-control ]];then
  formatter_control_mode=1
  set -- "$1" "$2" "$3" --formatter-nested
fi
if [[ $# == 4 && "$4" == --formatter-nested-third ]];then
  formatter_third_mode=1
  set -- "$1" "$2" "$3" --formatter-nested
fi
if [[ $# == 4 && "$4" == --formatter-nested-second ]];then
  formatter_second_mode=1
  set -- "$1" "$2" "$3" --formatter-nested
fi
if [[ $# == 4 && "$4" == --formatter-nested ]];then
  formatter_nested_mode=1
  set -- "$1" "$2" "$3" --formatter-continuation
fi
if [[ $# == 4 && "$4" == --formatter-continuation ]];then
  formatter_continuation_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-formatter-leaf
fi
if [[ $# == 4 && "$4" == --post-stm-sc-formatter-leaf ]];then
  post_stm_formatter_leaf_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-formatter
fi
if [[ $# == 4 && "$4" == --post-stm-sc-formatter ]];then
  post_stm_formatter_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-report-resume
fi
if [[ $# == 4 && "$4" == --post-stm-sc-report-resume ]];then
  post_stm_resume_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-report-dependency
fi
if [[ $# == 4 && "$4" == --post-stm-sc-report-dependency ]];then
  post_stm_dependency_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-report-helper
fi
if [[ $# == 4 && "$4" == --post-stm-sc-report-helper ]];then
  post_stm_helper_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-report
fi
if [[ $# == 4 && "$4" == --post-stm-sc-report ]];then
  post_stm_report_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-version
fi
if [[ $# == 4 && "$4" == --post-stm-sc-version ]];then
  post_stm_version_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-restore
fi
if [[ $# == 4 && "$4" == --post-stm-sc-restore ]];then
  post_stm_restore_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-decision
fi
if [[ $# == 4 && "$4" == --post-stm-sc-decision ]];then
  post_stm_decision_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-disable
fi
if [[ $# == 4 && "$4" == --post-stm-sc-disable ]];then
  post_stm_disable_mode=1
  set -- "$1" "$2" "$3" --post-stm-sc-entry
fi
if [[ $# == 4 && "$4" == --post-stm-sc-entry ]];then
  post_stm_sc_mode=1
  set -- "$1" "$2" "$3" --irq-stm-final-return
fi
if [[ $# == 4 && "$4" == --irq-stm-final-return ]];then
  stm_final_return_mode=1
  set -- "$1" "$2" "$3" --irq-stm-resumed-restore
fi
if [[ $# == 4 && "$4" == --irq-stm-resumed-restore ]];then
  stm_resumed_restore_mode=1
  set -- "$1" "$2" "$3" --irq-stm-deferred-active-return
fi
if [[ $# == 4 && "$4" == --irq-stm-deferred-active-return ]];then
  stm_active_return_mode=1
  set -- "$1" "$2" "$3" --irq-stm-deferred-ack
fi
if [[ $# == 4 && "$4" == --irq-stm-deferred-ack ]];then
  stm_ack_mode=1
  set -- "$1" "$2" "$3" --irq-stm-deferred-dispatch
fi
if [[ $# == 4 && "$4" == --irq-stm-deferred-dispatch ]];then
  stm_dispatch_mode=1
  set -- "$1" "$2" "$3" --irq-stm-deferred-vector
fi
if [[ $# == 4 && "$4" == --irq-stm-deferred-vector ]];then
  stm_vector_mode=1
  set -- "$1" "$2" "$3" --irq-stm-outer-restore
fi
if [[ $# == 4 && "$4" == --irq-stm-outer-restore ]];then
  stm_outer_mode=1
  set -- "$1" "$2" "$3" --irq-stm-event-return
fi
if [[ $# == 4 && "$4" == --irq-stm-event-return ]];then
  stm_event_return_mode=1
  set -- "$1" "$2" "$3" --irq-stm-wrapper-return
fi
if [[ $# == 4 && "$4" == --irq-stm-wrapper-return ]];then
  async_wrapper_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-return
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-return ]];then
  async_return_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-deferred
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-deferred ]];then
  ipc_deferred_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-dispatch
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-dispatch ]];then
  ipc_dispatch_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-profile
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-profile ]];then
  ipc_profile_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-submit-queue
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-submit-queue ]];then
  ioctl_queue_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-header
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-header ]];then
  ioctl_header_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-submit-prefix
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-submit-prefix ]];then
  ioctl_submit_prefix_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-output
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-output ]];then
  ioctl_output_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-first-flush
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-first-flush ]];then
  ioctl_flush_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-construction
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-construction ]];then
  ioctl_build_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-allocation
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-allocation ]];then
  ioctl_alloc_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-prefix
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-prefix ]];then
  ioctl_prefix_mode=1
  set -- "$1" "$2" "$3" --irq-stm-ioctl-entry
fi
if [[ $# == 4 && "$4" == --irq-stm-ioctl-entry ]];then
  stm_ioctl_mode=1
  set -- "$1" "$2" "$3" --irq-second-return
fi
if [[ $# == 4 && "$4" == --irq-second-return ]];then
  second_return_mode=1
  set -- "$1" "$2" "$3" --irq-second-free
fi
if [[ $# == 4 && "$4" == --irq-second-free ]];then
  second_free_mode=1
  set -- "$1" "$2" "$3" --irq-second-restore
fi
if [[ $# == 4 && "$4" == --irq-second-restore ]];then
  second_restore_mode=1
  set -- "$1" "$2" "$3" --irq-second-reply
fi
if [[ $# == 4 && "$4" == --irq-second-reply ]];then
  second_reply_mode=1
  set -- "$1" "$2" "$3" --irq-second-scheduler
fi
if [[ $# == 4 && "$4" == --irq-second-scheduler ]];then
  second_scheduler_mode=1
  set -- "$1" "$2" "$3" --irq-second-submit
fi
if [[ $# == 4 && "$4" == --irq-second-submit ]];then
  second_submit_mode=1
  set -- "$1" "$2" "$3" --irq-second-request
fi
if [[ $# == 4 && "$4" == --irq-second-request ]];then
  second_request_mode=1
  set -- "$1" "$2" "$3" --irq-second-open
fi
if [[ $# == 4 && "$4" == --irq-second-open ]];then
  second_open_mode=1
  set -- "$1" "$2" "$3" --irq-open-return
fi
if [[ $# == 4 && "$4" == --irq-open-return ]];then
  open_return_mode=1
  set -- "$1" "$2" "$3" --irq-allocator-metadata
fi
if [[ $# == 4 && "$4" == --irq-allocator-metadata ]];then
  allocator_metadata_mode=1
  set -- "$1" "$2" "$3" --irq-allocator-release
fi
if [[ $# == 4 && "$4" == --irq-allocator-release ]];then
  allocator_release_mode=1
  set -- "$1" "$2" "$3" --irq-submit-resume
fi
if [[ $# == 4 && "$4" == --irq-submit-resume ]];then
  submit_resume_mode=1
  set -- "$1" "$2" "$3" --irq-sleep-exit
fi
if [[ $# == 4 && "$4" == --irq-sleep-exit ]];then
  sleep_exit_mode=1
  set -- "$1" "$2" "$3" --irq-sleep-resume
fi
if [[ $# == 4 && "$4" == --irq-sleep-resume ]];then
  sleep_resume_mode=1
  set -- "$1" "$2" "$3" --irq-coop-load
fi
if [[ $# == 4 && "$4" == --irq-coop-load ]];then
  coop_load_mode=1
  set -- "$1" "$2" "$3" --irq-coop-selection
fi
if [[ $# == 4 && "$4" == --irq-coop-selection ]];then
  selection_mode=1
  set -- "$1" "$2" "$3" --irq-ready-idle-save-helper
fi
if [[ $# == 4 && "$4" == --irq-ready-idle-save-helper ]];then
  reply_helper_mode=1
  save_continuity_mode=1
  set -- "$1" "$2" "$3" --irq-ready-idle-save
fi
if [[ $# == 4 && "$4" == --irq-reply-handler-helper ]];then
  reply_helper_mode=1
  set -- "$1" "$2" "$3" --irq-reply-handler-return
fi
if [[ $# == 4 && "$4" == --coop-save ]];then
  coop_save_mode=1
  set -- "$1" "$2" "$3"
fi
if [[ $# == 4 && "$4" == --irq-ready-idle-save ]];then
  coop_save_mode=1
  set -- "$1" "$2" "$3" --irq-ready-idle-return
fi
if [[ $# == 4 && "$4" == --irq-ready-idle-return ]];then
  ready_idle_mode=1
  set -- "$1" "$2" "$3" --irq-reply-handler-return
fi
if [[ $# == 4 && "$4" == --irq-reply-handler-return ]];then
  reply_return_mode=1
  set -- "$1" "$2" "$3" --irq-nested-wake-return
fi
if [[ $# == 4 && "$4" == --irq-nested-wake-return ]];then
  nested_wake_mode=1
  set -- "$1" "$2" "$3" --irq-wake-ready
fi
if [[ $# == 4 && "$4" == --irq-wake-ready ]];then
  wake_ready_mode=1
  set -- "$1" "$2" "$3" --irq-reply-wake-entry
fi
if [[ $# == 4 && "$4" == --irq-reply-wake-entry ]];then
  reply_body_mode=1
  set -- "$1" "$2" "$3" --irq-reply-entry
fi
if [[ $# == 4 && "$4" == --irq-reply-entry ]];then
  reply_entry_mode=1
  set -- "$1" "$2" "$3" --irq-return
fi
[[ $# == 3 || ( $# == 4 && ( "$4" == --irq-entry || "$4" == --irq-vector || "$4" == --irq-dispatch || "$4" == --irq-ack || "$4" == --irq-return ) ) ]] || exit 2
extra=();overlays=()
if [[ $# == 4 ]];then extra=(-DUNDERCOVER_V1259_IRQ_ENTRY);fi
if [[ "${4-}" == --irq-vector || "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then extra+=(-DUNDERCOVER_V1260_IRQ_VECTOR);overlays+=(--native-external-overlay-preflight);fi
if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then extra+=(-DUNDERCOVER_V1261_IPC_DISPATCH);fi
if [[ "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then extra+=(-DUNDERCOVER_V1266_JOINED_ACK);fi
if [[ "${4-}" == --irq-return ]];then extra+=(-DUNDERCOVER_V1271_IPC_RETURN);fi
if [[ "$reply_entry_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1275_REPLY_ENTRY);fi
if [[ "$reply_body_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1282_REPLY_WAKE);fi
if [[ "$wake_ready_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1289_WAKE_READY);fi
if [[ "$nested_wake_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1292_NESTED_WAKE);fi
if [[ "$reply_return_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1300_REPLY_RETURN);fi
if [[ "$ready_idle_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1305_READY_IDLE_RETURN);fi
if [[ "$coop_save_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1315_COOP_SAVE);fi
if [[ "$save_continuity_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1320_SAVE_CONTINUITY);fi
if [[ "$selection_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1328_IDLE_SELECTION);fi
if [[ "$coop_load_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1334_COOP_LOAD);fi
sleep_args=()
if [[ "$sleep_resume_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1336_SLEEP_RESUME);sleep_args=(--sleep-resume);fi
if [[ "$sleep_exit_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1340_SLEEP_EXIT);fi
if [[ "$submit_resume_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1344_SUBMIT_RESUME);fi
allocator_args=()
if [[ "$allocator_release_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1352_ALLOCATOR_RELEASE);allocator_args=(--allocator);fi
if [[ "$allocator_metadata_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1356_ALLOCATOR_METADATA);fi
if [[ "$open_return_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1358_OPEN_RETURN);fi
if [[ "$second_open_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1359_SECOND_OPEN);fi
if [[ "$second_request_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1364_SECOND_REQUEST);fi
if [[ "$second_submit_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1366_SECOND_SUBMIT);fi
if [[ "$second_scheduler_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1368_SECOND_SCHEDULER);fi
if [[ "$second_reply_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1370_SECOND_REPLY);fi
if [[ "$second_restore_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1374_SECOND_RESTORE);fi
if [[ "$second_free_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1378_SECOND_FREE);fi
if [[ "$second_return_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1379_SECOND_RETURN);fi
if [[ "$stm_ioctl_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1383_STM_IOCTL_ENTRY);fi
if [[ "$ioctl_prefix_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1386_IOCTL_PREFIX);fi
if [[ "$ioctl_alloc_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1387_IOCTL_ALLOCATION);fi
if [[ "$ioctl_build_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1392_IOCTL_CONSTRUCTION);fi
if [[ "$ioctl_flush_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1398_IOCTL_FLUSH);fi
if [[ "$ioctl_output_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1401_IOCTL_OUTPUT);fi
if [[ "$ioctl_submit_prefix_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1404_IOCTL_SUBMIT_PREFIX);fi
if [[ "$ioctl_header_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1407_IOCTL_HEADER);fi
if [[ "$ioctl_queue_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1410_IOCTL_QUEUE);fi
if [[ "$ipc_profile_mode" == 1 ]];then extra+=(-DUNDERCOVER_IPC_PROFILE);fi
if [[ "$ipc_dispatch_mode" == 1 ]];then extra+=(-DUNDERCOVER_IPC_DISPATCH);fi
if [[ "$ipc_deferred_mode" == 1 ]];then extra+=(-DUNDERCOVER_IPC_DEFERRED);fi
if [[ "$async_return_mode" == 1 ]];then extra+=(-DUNDERCOVER_ASYNC_SUBMIT_RETURN);fi
if [[ "$async_wrapper_mode" == 1 ]];then extra+=(-DUNDERCOVER_ASYNC_WRAPPER_RETURN);fi
if [[ "$stm_event_return_mode" == 1 ]];then extra+=(-DUNDERCOVER_STM_EVENT_RETURN);fi
if [[ "$stm_outer_mode" == 1 ]];then extra+=(-DUNDERCOVER_STM_OUTER_RESTORE);fi
if [[ "$stm_vector_mode" == 1 ]];then extra+=(-DUNDERCOVER_STM_DEFERRED_VECTOR);fi
if [[ "$stm_dispatch_mode" == 1 ]];then extra+=(-DUNDERCOVER_STM_DEFERRED_DISPATCH);fi
if [[ "$stm_ack_mode" == 1 ]];then extra+=(-DUNDERCOVER_STM_DEFERRED_ACK);fi
if [[ "$stm_active_return_mode" == 1 ]];then extra+=(-DUNDERCOVER_STM_DEFERRED_ACTIVE_RETURN);fi
if [[ "$stm_resumed_restore_mode" == 1 ]];then extra+=(-DUNDERCOVER_STM_RESUMED_RESTORE);fi
if [[ "$stm_final_return_mode" == 1 ]];then extra+=(-DUNDERCOVER_STM_FINAL_RETURN);fi
if [[ "$post_stm_sc_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_ENTRY);fi
if [[ "$post_stm_disable_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_DISABLE);fi
if [[ "$post_stm_decision_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_DECISION);fi
if [[ "$post_stm_restore_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_RESTORE);fi
if [[ "$post_stm_version_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_VERSION);fi
if [[ "$post_stm_report_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_REPORT);fi
if [[ "$post_stm_helper_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_REPORT_HELPER);fi
if [[ "$post_stm_dependency_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_REPORT_DEPENDENCY);fi
if [[ "$post_stm_resume_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_REPORT_RESUME);fi
if [[ "$post_stm_formatter_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_FORMATTER);fi
if [[ "$post_stm_formatter_leaf_mode" == 1 ]];then extra+=(-DUNDERCOVER_POST_STM_SC_FORMATTER_LEAF);fi
if [[ "$formatter_continuation_mode" == 1 ]];then extra+=(-DUNDERCOVER_FORMATTER_CONTINUATION);fi
if [[ "$formatter_nested_mode" == 1 ]];then extra+=(-DUNDERCOVER_FORMATTER_NESTED);fi
nested_args=()
if [[ "$formatter_second_mode" == 1 ]];then extra+=(-DUNDERCOVER_FORMATTER_SECOND);nested_args=(--second);fi
if [[ "$formatter_third_mode" == 1 ]];then extra+=(-DUNDERCOVER_FORMATTER_THIRD);nested_args=(--third);fi
if [[ "$formatter_control_mode" == 1 ]];then extra+=(-DUNDERCOVER_FORMATTER_CONTROL);nested_args=(--control);fi
if [[ "$formatter_arrival_mode" == 1 ]];then extra+=(-DUNDERCOVER_FORMATTER_ARRIVAL);nested_args=(--arrival);fi
if [[ "$formatter_post_ctr_mode" == 1 ]];then extra+=(-DUNDERCOVER_FORMATTER_POST_CTR);nested_args=(--post-ctr);fi
if [[ "$formatter_partial_mode" == 1 ]];then extra+=(-DUNDERCOVER_FORMATTER_PARTIAL);nested_args=(--partial);fi
helper_args=()
if [[ "$reply_helper_mode" == 1 ]];then extra+=(-DUNDERCOVER_V1316_REPLY_HELPER);helper_args=(--helper);fi
root="$(realpath "$1")";here="$(cd "$(dirname "$0")" && pwd)"
work="$(mktemp -d)";trap 'rm -rf -- "$work"' EXIT;umask 077;ulimit -c 0
[[ "$(git -C "$root" rev-parse HEAD)" == 595f176f1d24cc54ff2e8389feed12d7fb553cc2 ]]
for p in apply_verified_elf_spans_v6 apply_function_root_v443 apply_exact_dispatch_v445 apply_native_tick_v438 apply_mtmsr_resume_v74 apply_hollywood_mmio_v62 apply_native_lowmem_v63 apply_hid_state_v18 apply_syscall_pc_v26 apply_cache_events_v561 apply_syscall_transfer_v461;do
  python3 "$here/$p.py" "$root" > "$work/patch.log" 2>&1 || { echo "V1256 source patch failed: $p";exit 1; }
done
if [[ "$reply_body_mode" == 1 ]];then python3 "$here/apply_isolated_dcbi_v1276.py" "$root";fi
python3 "$here/make_v1256_scheduler_fixture.py" "$2" "$3" "$work/input"
if [[ $# == 4 ]];then python3 "$here/prepare_v1259_scheduler_vector.py" "$2" "$3" "$work/input/v1259_private_vector.h";fi
if [[ "${4-}" == --irq-vector || "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then
  python3 "$here/apply_exception_sprg.py" "$root" > "$work/patch.log" 2>&1 || { echo 'V1260 SPRG patch failed';exit 1; }
  python3 "$here/prepare_v1260_scheduler_vector.py" "$2" "$3" "$work/input"
fi
if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1261_ipc_dispatch.py" "$2" "$3" "$work/input";fi
if [[ "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1266_joined_ack.py" "$2" "$3" "$work/input";fi
if [[ "${4-}" == --irq-return ]];then python3 "$here/prepare_v1270_ipc_epilogue.py" "$2" "$3" "$work/input";fi
if [[ "$reply_body_mode" == 1 ]];then python3 "$here/prepare_v1281_reply_fixture.py" "$2" "$3" "$work/input";fi
if [[ "$wake_ready_mode" == 1 ]];then python3 "$here/prepare_v1289_wake_fixture.py" "$2" "$3" "$work/input";fi
if [[ "$nested_wake_mode" == 1 ]];then python3 "$here/prepare_v1292_nested_wake.py" "$2" "$3" "$work/input";fi
if [[ "$reply_helper_mode" == 1 ]];then python3 "$here/prepare_v1316_reply_helper.py" "$2" "$3" "$work/input";fi
if [[ "$reply_return_mode" == 1 ]];then python3 "$here/prepare_v1299_reply_return.py" "$2" "$3" "$work/input" "${helper_args[@]}";fi
if [[ "$coop_save_mode" == 1 ]];then python3 "$here/prepare_v1314_save_lane.py" "$2" "$3" "$work/input";fi
if [[ "$selection_mode" == 1 ]];then python3 "$here/prepare_v1321_combined_resume.py" "$2" "$3" "$work/input";fi
if [[ "$open_return_mode" == 1 ]];then python3 "$here/prepare_v1358_open_return.py" "$2" "$3" "$work/input";fi
if [[ "$second_return_mode" == 1 ]];then python3 "$here/prepare_v1379_second_return.py" "$2" "$3" "$work/input";fi
if [[ "$stm_ioctl_mode" == 1 ]];then python3 "$here/prepare_v1383_stm_ioctl_entry.py" "$2" "$3" "$work/input";fi
if [[ "$ioctl_prefix_mode" == 1 ]];then python3 "$here/prepare_v1386_ioctl_prefix.py" "$2" "$3" "$work/input";fi
if [[ "$ioctl_alloc_mode" == 1 ]];then python3 "$here/prepare_v1387_ioctl_allocation.py" "$2" "$3" "$work/input";fi
if [[ "$ioctl_build_mode" == 1 ]];then python3 "$here/prepare_v1392_ioctl_construction.py" "$2" "$3" "$work/input";fi
if [[ "$ioctl_flush_mode" == 1 ]];then python3 "$here/prepare_v1398_ioctl_flush.py" "$2" "$3" "$work/input";fi
if [[ "$ioctl_output_mode" == 1 ]];then python3 "$here/prepare_v1401_ioctl_output.py" "$2" "$3" "$work/input";fi
if [[ "$ioctl_submit_prefix_mode" == 1 ]];then python3 "$here/prepare_v1404_ioctl_submit.py" "$2" "$3" "$work/input";fi
if [[ "$ioctl_queue_mode" == 1 ]];then python3 "$here/prepare_v1410_ioctl_queue.py" "$2" "$3" "$work/input";fi
if [[ "$ipc_profile_mode" == 1 ]];then python3 "$here/prepare_ipc_profile_native.py" "$2" "$3" "$work/input";fi
if [[ "$ipc_dispatch_mode" == 1 ]];then python3 "$here/prepare_ipc_dispatch_native.py" "$2" "$3" "$work/input";fi
if [[ "$stm_ack_mode" == 1 ]];then python3 "$here/prepare_ipc_deferred_ack_geometry.py" "$2" "$3" --out "$work/input";fi
if [[ "$async_return_mode" == 1 ]];then python3 "$here/prepare_async_submit_return.py" "$2" "$3" "$work/input";fi
if [[ "$async_wrapper_mode" == 1 ]];then python3 "$here/prepare_async_wrapper_return.py" "$2" "$3" --out "$work/input";fi
if [[ "$stm_event_return_mode" == 1 ]];then python3 "$here/prepare_stm_event_return_geometry.py" "$2" "$3" --out "$work/input";fi
if [[ "$stm_outer_mode" == 1 ]];then python3 "$here/prepare_stm_outer_restore.py" "$2" "$3" "$work/input";fi
if [[ "$stm_final_return_mode" == 1 ]];then python3 "$here/prepare_stm_final_return.py" "$2" "$3" --out "$work/input";fi
if [[ "$post_stm_sc_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_join.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$post_stm_disable_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_disable.py" "$2" "$3" --out "$work/input";fi
if [[ "$post_stm_decision_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_decision.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$post_stm_restore_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_restore.py" "$2" "$3" --out "$work/input";fi
if [[ "$post_stm_version_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_version_fixture.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$post_stm_report_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_fixture.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$post_stm_helper_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_helper_fixture.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$post_stm_dependency_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_dependency_fixture.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$post_stm_resume_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_helper_resume_fixture.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$post_stm_formatter_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_formatter_fixture.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$post_stm_formatter_leaf_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_formatter_leaf_fixture.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$formatter_continuation_mode" == 1 ]];then python3 "$here/prepare_formatter_continuation_fixture.py" "$2" "$3" --fixture "$work/input";fi
if [[ "$formatter_nested_mode" == 1 ]];then python3 "$here/prepare_formatter_nested_fixture.py" "$2" "$3" --fixture "$work/input" "${nested_args[@]}";fi
python3 "$here/apply_open_roots_v645.py" "$root" "$2" "$3"
if [[ "${4-}" != --irq-return ]];then python3 "$here/make_v1256_scheduler_fixture.py" "$2" "$3" "$work/input" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp";fi
if [[ "${4-}" == --irq-vector ]];then python3 "$here/prepare_v1260_scheduler_vector.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer;fi
if [[ "${4-}" == --irq-dispatch ]];then python3 "$here/prepare_v1261_ipc_dispatch.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer;fi
if [[ "${4-}" == --irq-ack ]];then python3 "$here/prepare_v1266_joined_ack.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer;fi
if [[ "$formatter_nested_mode" == 1 ]];then
  python3 "$here/prepare_formatter_nested_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv" "${nested_args[@]}"
elif [[ "$formatter_continuation_mode" == 1 ]];then
  python3 "$here/prepare_formatter_continuation_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_formatter_leaf_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_formatter_leaf_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_formatter_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_report_formatter_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_resume_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_report_helper_resume_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_dependency_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_report_dependency_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_helper_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_report_helper_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_report_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_report_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_version_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_version_fixture.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_decision_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_decision.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$post_stm_sc_mode" == 1 ]];then
  python3 "$here/prepare_post_stm_sc_join.py" "$2" "$3" --analyzer "$root/nWiiAnalyzer/src/analyzer.cpp" --symbols "$work/input/symbols.csv"
elif [[ "$ioctl_prefix_mode" == 1 ]];then
  python3 "$here/prepare_v1386_ioctl_prefix.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "$stm_ioctl_mode" == 1 ]];then
  python3 "$here/prepare_v1383_stm_ioctl_entry.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "$second_return_mode" == 1 ]];then
  python3 "$here/prepare_v1379_second_return.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "$open_return_mode" == 1 ]];then
  python3 "$here/prepare_v1358_open_return.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "$selection_mode" == 1 ]];then
  python3 "$here/prepare_v1321_combined_resume.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "$reply_helper_mode" == 1 ]];then
  python3 "$here/prepare_v1316_reply_helper.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "$wake_ready_mode" == 1 ]];then
  python3 "$here/prepare_v1289_wake_fixture.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "$reply_body_mode" == 1 ]];then
  python3 "$here/prepare_v1281_reply_fixture.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer --symbols "$work/input/symbols.csv"
elif [[ "${4-}" == --irq-return ]];then
  python3 "$here/prepare_v1270_ipc_epilogue.py" "$2" "$3" "$root/nWiiAnalyzer/src/analyzer.cpp" --analyzer
fi
python3 "$here/apply_explicit_tail_roots_v71.py" "$root" --strict-native
python3 "$here/apply_isolated_open_cache_v651.py" "$root"
g++ -std=c++20 -O2 -DUNDERCOVER_NATIVE_SC_OVERLAY -I"$root/nWiiRuntime/include" -I"$root/nWiiAnalyzer/include" -I"$root/nWiiRecomp/include" \
  "$here/offline_recompiler_driver_v6.cpp" "$root/nWiiRuntime/src/core/loader.cpp" "$root/nWiiAnalyzer/src/analyzer.cpp" \
  "$root/nWiiAnalyzer/src/dolphin_sigdb.cpp" "$root/nWiiAnalyzer/src/signature_scanner.cpp" "$root/nWiiRecomp/src/recompiler.cpp" "$root/nWiiRecomp/src/symbols.cpp" \
  -o "$work/driver" > "$work/build.log" 2>&1 || { echo 'V1256 driver failed';exit 1; }
mkdir "$work/generated"
"$work/driver" "$work/input/fixture.dol" "$work/input/symbols.csv" "$work/generated" --strict-symbol-spans --native-sc-overlay "${overlays[@]}" --generate "$root/nWiiRuntime" > "$work/generate.log" 2>&1 || { echo 'V1256 translation failed';exit 1; }
python3 "$here/make_v651_open_fixture.py" "$2" "$3" "$work/generated" --trace
PYTHONPATH="$here" python3 - "$work/input/fixture.dol" "$work/generated" <<'PY'
import sys
from pathlib import Path
from prepare_v625_ipc_client import audit_native
from make_v624_ipc_geometry import SPANS
from prepare_v629_stm_open import STM
from make_v1252_sleep_fixture import SLEEP,SELECT,SIZE
from make_v1256_scheduler_fixture import ALLOWED,FORBIDDEN
from prepare_v680_si_helper import verify_direct
from make_start_to_select_thread_v74 import EDGES
from prepare_v419_full_start import words_at
d=Path(sys.argv[1]).read_bytes();root=Path(sys.argv[2])
expected={pc+4*i:(pc,w) for pc,n in SPANS for i,w in enumerate(words_at(d,pc,n//4))}
expected.update({STM+4*i:(STM,w) for i,w in enumerate(words_at(d,STM,23))})
expected.update({SLEEP+4*i:(SLEEP,w) for i,w in enumerate(words_at(d,SLEEP,SIZE//4))})
sizes={int(a,16):int(n) for _,a,n in (row.split(',') for row in (root.parent/'input/symbols.csv').read_text().splitlines()[1:])}
for pc in (*ALLOWED,*FORBIDDEN):
    expected.update({pc+4*i:(pc,w) for i,w in enumerate(words_at(d,pc,1 if pc in FORBIDDEN else sizes[pc]//4))})
shards=[p.read_text() for p in root.glob('output_*.cpp')]
for site,target in EDGES:
    owners=[s for s in shards if f'loc_{site:X}: ;' in s]
    if len(owners)!=1:sys.exit('V1256 scheduler direct owner refused')
    try:verify_direct(owners[0],site,target)
    except ValueError:sys.exit('V1256 scheduler direct edge refused')
try:n=audit_native((p.read_text() for p in root.glob('output_*.cpp')),(root/'main_output.cpp').read_text(),expected)
except ValueError:print('V1256_IPC_STM_TRANSLATION verified=0');sys.exit(1)
print(f'V1256_IPC_STM_TRANSLATION verified=1 native_words={n}')
PY
if [[ "${4-}" == --irq-vector || "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1260_scheduler_vector.py" "$2" "$3" "$work/generated" --install;fi
if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1261_ipc_dispatch.py" "$2" "$3" "$work/generated" --install;fi
if [[ "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then python3 "$here/prepare_v1266_joined_ack.py" "$2" "$3" "$work/generated" --install;fi
if [[ "${4-}" == --irq-return ]];then python3 "$here/prepare_v1270_ipc_epilogue.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$reply_body_mode" == 1 ]];then python3 "$here/prepare_v1281_reply_fixture.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$wake_ready_mode" == 1 ]];then python3 "$here/prepare_v1289_wake_fixture.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$nested_wake_mode" == 1 ]];then python3 "$here/prepare_v1292_nested_wake.py" "$2" "$3" "$work/generated" --audit;fi
if [[ "$reply_helper_mode" == 1 ]];then python3 "$here/prepare_v1316_reply_helper.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$reply_return_mode" == 1 ]];then python3 "$here/prepare_v1299_reply_return.py" "$2" "$3" "$work/generated" --audit "${helper_args[@]}";fi
if [[ "$coop_save_mode" == 1 ]];then python3 "$here/prepare_v1314_save_lane.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$selection_mode" == 1 ]];then python3 "$here/prepare_v1328_idle_route.py" "$2" "$3" "$work/generated" "${sleep_args[@]}";fi
if [[ "$submit_resume_mode" == 1 ]];then python3 "$here/prepare_v1337_open_completion.py" "$2" "$3" "$work/generated" --submit-install "${allocator_args[@]}";fi
if [[ "$allocator_metadata_mode" == 1 ]];then python3 "$here/derive_allocator_descriptor_v1356.py" "$3" "$work/input/v1356_private_descriptor.h";fi
if [[ "$open_return_mode" == 1 ]];then python3 "$here/prepare_v1358_open_return.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$second_open_mode" == 1 ]];then python3 "$here/prepare_v1359_second_open.py" "$2" "$3" "$work/generated";fi
if [[ "$second_return_mode" == 1 ]];then python3 "$here/prepare_v1379_second_return.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$stm_ioctl_mode" == 1 ]];then python3 "$here/prepare_v1383_stm_ioctl_entry.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$ioctl_prefix_mode" == 1 ]];then python3 "$here/prepare_v1386_ioctl_prefix.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$ioctl_alloc_mode" == 1 ]];then python3 "$here/prepare_v1387_ioctl_allocation.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$ioctl_build_mode" == 1 ]];then python3 "$here/prepare_v1392_ioctl_construction.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$ioctl_flush_mode" == 1 ]];then python3 "$here/prepare_v1398_ioctl_flush.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$ioctl_output_mode" == 1 ]];then python3 "$here/prepare_v1401_ioctl_output.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$ioctl_submit_prefix_mode" == 1 ]];then python3 "$here/prepare_v1404_ioctl_submit.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$ioctl_queue_mode" == 1 ]];then python3 "$here/prepare_v1410_ioctl_queue.py" "$2" "$3" "$work/generated" --audit;fi
if [[ "$ipc_profile_mode" == 1 ]];then python3 "$here/prepare_ipc_profile_native.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$ipc_dispatch_mode" == 1 ]];then python3 "$here/prepare_ipc_dispatch_native.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$stm_ack_mode" == 1 ]];then python3 "$here/prepare_ipc_deferred_ack_geometry.py" "$2" "$3" --audit "$work/generated";fi
if [[ "$async_return_mode" == 1 ]];then python3 "$here/prepare_async_submit_return.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$async_wrapper_mode" == 1 ]];then python3 "$here/prepare_async_wrapper_return.py" "$2" "$3" --install "$work/generated";fi
if [[ "$stm_event_return_mode" == 1 ]];then python3 "$here/prepare_stm_event_return_geometry.py" "$2" "$3" --install "$work/generated";fi
if [[ "$stm_outer_mode" == 1 ]];then python3 "$here/prepare_stm_outer_restore.py" "$2" "$3" "$work/generated" --install;fi
if [[ "$stm_active_return_mode" == 1 ]];then python3 "$here/prepare_deferred_active_resume.py" "$2" "$3" --install "$work/generated";fi
if [[ "$stm_final_return_mode" == 1 ]];then python3 "$here/prepare_stm_final_return.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_sc_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_join.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_disable_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_disable.py" "$2" "$3" --audit "$work/generated";fi
if [[ "$post_stm_decision_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_decision.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_restore_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_restore.py" "$2" "$3" --audit "$work/generated";fi
if [[ "$post_stm_version_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_version_fixture.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_report_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_fixture.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_helper_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_helper_fixture.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_dependency_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_dependency_fixture.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_resume_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_helper_resume_fixture.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_formatter_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_report_formatter_fixture.py" "$2" "$3" --install "$work/generated";fi
if [[ "$post_stm_formatter_leaf_mode" == 1 ]];then python3 "$here/prepare_post_stm_sc_formatter_leaf_fixture.py" "$2" "$3" --install "$work/generated";fi
if [[ "$formatter_continuation_mode" == 1 ]];then python3 "$here/prepare_formatter_continuation_fixture.py" "$2" "$3" --install "$work/generated";fi
if [[ "$formatter_nested_mode" == 1 ]];then python3 "$here/prepare_formatter_nested_fixture.py" "$2" "$3" --install "$work/generated" "${nested_args[@]}";fi
python3 "$here/patch_sc_trace_v570.py" "$work/generated"
python3 "$here/patch_sc_trace_v640.py" "$work/generated"
python3 "$here/apply_sc_dispatch_gate_v572.py" "$work/generated" --vector "$work/input/vector.bin"
g++ -std=c++20 -O1 "${extra[@]}" -fsanitize=address,undefined -fno-pie -no-pie -I"$here" -I"$work/input" -I"$work/generated" -I"$work/generated/nWiiRuntime/include" \
  "$here/test_native_scheduler_postack_v1256.cpp" "$work/generated"/*.cpp -o "$work/native" > "$work/compile.log" 2>&1 || { python3 "$here/classify_open_compile_v654.py" "$work/compile.log";python3 "$here/classify_reply_compile_v1290.py" "$work/compile.log";echo 'V1256 compile failed';exit 1; }
rc=0;native_args=()
if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then native_args=("$2");fi
ASAN_OPTIONS=abort_on_error=1 UBSAN_OPTIONS=halt_on_error=1 timeout 30s "$work/native" "${native_args[@]}" > "$work/run.log" 2>&1 || rc=$?
grep -Ex 'STM_DEFERRED_ACK_REFUSAL kind=[1-7] stage=[0-2] reason=[0-8] visits=[0-9]{1,4} ordinal=[0-9]{1,3} detail=([0-9]|10) reads=[0-9]{1,2} writes=[0-2] memory=[0-6] gate=[0-6] gate_reason=[0-6]|STM_DEFERRED_ACK_TRIAL n=[0-7] original_return=1 guest_w1c=1 credit=1 unissued=1 deferred=1 reply=0 active_context=1 visits=[0-9]{1,4} reads=[0-9]{1,2} writes=2 stack=[0-9]{1,2} calls=[0-9]{1,2}|STM_DEFERRED_DISPATCH_REFUSAL kind=[1-7] stage=[0-6] reason=[0-6] detail=([0-9]|10) visits=[0-9]{1,4}|STM_DEFERRED_DISPATCH_TRIAL n=[0-7] original_dispatch=1 handler_index=27 active_context=1 pending_ack=1 deferred=1 handler_executed=0 visits=[0-9]{1,4} reads=[0-9]{1,2}|STM_DEFERRED_VECTOR_REFUSAL kind=[1-5] stage=[0-3] reason=[0-6] memory=[0-6] detail=([0-9]|10)|STM_DEFERRED_VECTOR_TRIAL n=[0-7] original_vector=1 original_trampoline=1 active_context=1 saved_fields=38 deferred=1 pending_ack=1 dispatcher_executed=0 visits=[0-9]{1,3}|STM_OUTER_RESTORE_REFUSAL kind=[1-5] stage=[0-2] reason=[0-4] visits=[0-9]{1,2}|STM_OUTER_RESTORE_TRIAL n=[0-7] original_mtmsr=1 ee=1 pending_ack=1 deferred=1 visits=[0-9]{1,2}|STM_DEFERRED_IRQ_TRIAL n=[0-7] entered=1 active_thread=1 srr=1 deferred=1 pending_ack=1 vector_executed=0|STM_EVENT_RETURN_REFUSAL kind=[1-4] stage=[0-2] reason=[0-5] visits=[0-9]{1,2} stores=[01] ordinal=[0-9]{1,3}|STM_EVENT_RETURN_TRIAL n=[0-7] original_flag=1 restore_entry=1 masked=1 deferred=1 visits=[0-9]{1,2} stores=1|ASYNC_WRAPPER_REFUSAL kind=[1-5] stage=[0-2] reason=[0-7] visits=[0-9]{1,3} loads=[0-9]{1,2} restored=[0-9]{1,2} ordinal=[0-9]{1,3} detail=[0-5]|ASYNC_WRAPPER_TRIAL n=[0-7] original_return=1 masked=1 abi=1 deferred=1 visits=[0-9]{1,3} loads=[0-9]{1,2} restored=[0-9]{1,2} polls=[01]|ASYNC_SUBMIT_REFUSAL kind=[1-5] stage=[0-2] reason=[0-8] visits=[0-9]{1,3} polls=[0-9]{1,2} ordinal=[0-9]{1,3}|ASYNC_SUBMIT_TRIAL n=[0-7] original_return=1 masked=1 abi=1 deferred=1 visits=[0-9]{1,3} polls=[0-9]{1,2}|IPC_DEFERRED_TRIAL n=[0-7] original_boundary=1 deferred=1 pending_ack=1 masked=1 cpu_preserved=1 ring_preserved=1 request_preserved=1 reply=0 ios_steps=5|IPC_DISPATCH_REFUSAL kind=[1-8] stage=[0-2] reason=[0-8] memory=[0-6] gate=[0-5] gate_stage=[0-6] visits=[0-9]{1,3} stores=[0-3] calls=[0-3] writes=[0-2] reads=[01] ordinal=[0-9]{1,3} detail=[0-3]|IPC_DISPATCH_TRIAL n=[0-7] original_return=1 masked=1 ring_dequeued=1 credit_consumed=1 message=1 control=1 queued=1 serviced=0 visits=[0-9]{1,3} stores=3 calls=3 writes=2 reads=1 polls=[0-9]{1,3}|IPC_PROFILE_REFUSAL kind=[1-4] stage=[0-2] reason=[0-7] memory=[0-3] visits=[0-9]{1,4} stores=[0-4] polls=[0-9]{1,3} ordinal=[0-9]{1,3}|IPC_PROFILE_TRIAL n=[0-7] original_return=1 masked=1 ring_preserved=1 request_preserved=1 visits=[0-9]{1,4} stores=[24] polls=[0-9]{1,3} slot=[01]|V1410_QUEUE_REFUSAL kind=[1-6] stage=[0-2] reason=[0-7] visits=[0-9]{1,3} stores=[0-9]{1,4} polls=[0-9]{1,3} ordinal=[0-9]{1,3} fence=[0-6] range=[0-9] base=[0-3] dest=[0-8] value=[0-7] form=[0-5] ring=[0-4] ring_stores=[0-3]|V1410_QUEUE_TRIAL n=[0-7] original_disable=1 masked=1 queue_entry=1 request_preserved=1 visits=[0-9]{1,3} stores=[0-9]{1,4} polls=[0-9]{1,3}|V1407_HEADER_TRIAL n=[0-7] original_flush=1 native_rfi=1 masked=1 request_preserved=1 lines=[0-9]{1,3}|V1404_PREFIX_REFUSAL kind=[1-4] stage=[0-2] reason=[0-7] visits=[0-9]{1,3} stores=[0-9]{1,4} queue=[0-2] fence=[0-6] range=[0-9] ordinal=[0-9]{1,3} detail=[0-6] queue_path=[0-2] queue_class=[0-5]|V1404_PREFIX_TRIAL n=[0-7] original_submit=1 queue_path=[12] header_flush_entry=1 visits=[0-9]{1,3} stores=[0-9]{1,4} queue=[02] request=[0-9]{1,4}|V1406_QUEUE_PATH initialized=[0-8] skipped=[0-8]|V1401_TAIL_REFUSAL kind=[1-5] stage=[0-4] reason=[0-8] visits=[0-9]{1,3}|V1401_OUTPUT_TRIAL n=[0-7] second_flush=1 native_rfi=1 submit_entry=1 lines=[0-9]{1,3} visits=[0-9]{1,3}|V1398_FLUSH_REFUSAL kind=[1-4] stage=[0-4] reason=[0-5] lines=[0-9]{1,3} polls=[0-9]{1,3} empty=[01]|V1398_FLUSH_TRIAL n=[0-7] original_flush=1 native_rfi=1 masked=1 lines=[0-9]{1,3} empty=[01]|V1392_CONSTRUCTION_REFUSAL kind=[1-5] stage=[0-3] reason=[0-7] visits=[0-9]{1,3} stores=[0-9]{1,4} request=[0-9]{1,4} fence=[0-6] range=[0-9] base_class=[0-3] ordinal=[0-9]{1,3} wire=[0-8] control=[0-8]|V1392_CONSTRUCTION_TRIAL n=[0-7] original_request=1 callback=1 first_flush=1 flush_kind=[12] stores=[0-9]{1,4} request=[0-9]{1,4}|V1387_ALLOCATION_REFUSAL kind=[1-5] stage=[0-2] reason=[0-8] visits=[0-9]{1,4} stores=[0-9]{1,4} heap=[0-9]{1,4} metadata=[0-9]{1,4} fence=[0-6] range=[0-9] ordinal=[0-9]{1,4} control=[0-8]|V1387_ALLOCATION_TRIAL n=[0-7] original_return=1 heap_shadow=1 metadata_shadow=1 masked=1 stores=[0-9]{1,4} heap=[0-9]{1,4} metadata=[0-9]{1,4}|V1386_PREFIX_REFUSAL kind=[1-5] stage=[0-2] reason=[0-6] visits=[0-9]{1,3} stores=[0-9]{1,2} saved=[0-9]{1,2}|V1386_PREFIX_TRIAL n=[0-7] original_prefix=1 save_return=1 allocator_entry=1 saved=9 stores=[0-9]{1,2}|V1383_IOCTL_REFUSAL kind=[1-5] stage=[0-2] reason=[0-6] visits=[0-9]{1,3} stores=[0-8]|V1383_IOCTL_TRIAL n=[0-7] original_stm=1 native_disable=1 event_fd=1 buffers=1 callback=1 stores=[1-8]|V1379_FREE_HANDOFF n=[0-7] native_free=1 heap_shadow=1 metadata_shadow=1 caller_abi=1 inline_return=1 stores=[0-9]{1,4} heap=[0-9]{1,4}|V1379_OPEN_TRIAL n=[0-7] submit_return=1 open_return=1 stm_resume=1 fd=1|V1378_DESCRIPTOR_REFUSAL stage=2|V1378_FREE_TRIAL n=[0-7] native_free=1 heap_shadow=1 metadata_shadow=1 caller_abi=1 inline_return=1 stores=[0-9]{1,4} heap=[0-9]{1,4}|V1374_WAKE_TRIAL n=[0-7] original_wake=1 ready=1 nested_return=1|V1374_IDLE_TRIAL n=[0-7] handler_return=1 latch_clear=1 native_rfi=1 ready_preserved=1|V1374_RESTORE_TRIAL n=[0-7] original_select=1 original_load=1 native_rfi=1 sleep_return=1 fd=1|V1371_SCHED_BOUNDARY detail=[1-9] stage=[1-6]|V1370_ACK_TRIAL n=[0-7] original_vector=1 original_dispatch=1 original_ack_return=1 native_reply=1 fd=1|V1370_REPLY_TRIAL n=[0-7] native_rfi=1 original_vector=1 original_dispatch=1 original_processor=1 native_dcbi=1 wake_entry=1 fd=1|V1368_REUSE_REFUSAL stage=[1-3]|V1368_SLEEP_TRIAL n=[0-7] waiting=1 queue=1 ack_held=1|V1368_SCHED_TRIAL n=[0-7] saved=1 idle_reused=1 enabled=1 pending_ack=1|V1366_SUBMIT_REFUSAL kind=[1-7] stage=[0-9] reason=[0-5] write=[0-5]|V1366_SUBMIT_TRIAL n=[0-7] submitted=1 ack=1 second_fd=1 first_fd_held=1 native_rfi=1 reply_pending=1|V1364_REQUEST_REFUSAL kind=[1-7] stage=[0-9] reason=[0-3] request=[0-6]|V1364_REQUEST_HANDOFF n=[0-7] first_release=1 second_entry=1 cache_rearmed=1|V1364_REQUEST_TRIAL n=[0-7] request=1 opposite_path=1 native_rfi=1 first_fd_held=1 reused=[01]|V1359_SECOND_REFUSAL kind=[1-5] stage=[0-2] reason=[0-6] visits=[0-9]{1,2} stores=[0-9]|V1359_SECOND_TRIAL n=[0-7] second_entry=1 opposite_path=1 descriptor_store=1 first_fd_held=1|V1358_OPEN_REFUSAL kind=[1-7] stage=[0-5] reason=[0-6] visits=[0-9]{1,3}|V1358_ALLOCATOR_HANDOFF n=[0-7] verified=1|V1358_OPEN_TRIAL n=[0-7] submit_return=1 open_return=1 stm_resume=1 descriptor=1|V1357_ALLOCATOR_CONTROL detail=[1-8] owner=[0-3]|V1356_DESCRIPTOR_REFUSAL stage=[1-4]|V1356_DESCRIPTOR_CREATED n=[0-7] original_create=1 unique=1|V1356_DESCRIPTOR_RETURN n=[0-7] exact_field=1 shadow=1 stores=[0-9]{1,4}|V1354_ALLOCATOR_RANGE detail=[1-9] base=[0-3] ordinal=[0-9]{1,3}|V1352_ALLOCATOR_REFUSAL kind=[1-6] stage=[0-2] reason=[0-8] store=[0-6] visits=[0-9]{1,3} writes=[0-9]{1,4} heap=[0-9]{1,4}|V1352_ALLOCATOR_TRIAL n=[0-7] native_free=1 heap_shadow=1 caller_abi=1 inline_return=1 stores=[0-9]{1,4} heap=[0-9]{1,4}|V1344_SUBMIT_REFUSAL kind=[1-6] stage=[0-3] reason=[0-6] visits=[0-9]{1,3}|V1344_SUBMIT_TRIAL n=[0-7] sleep_return=1 outer_restore=1 reply_held=1 free_entry=1|V1340_EXIT_REFUSAL kind=[1-7] stage=[0-3] reason=[0-6] visits=[0-9]{1,3}|V1340_EXIT_TRIAL n=[0-7] nested_restore=1 sleep_return=1 submit_resume=1 caller_abi=1|V1336_SLEEP_REFUSAL kind=[1-7] stage=[0-3] reason=[0-7] visits=[0-9]{1,3}|V1336_SLEEP_TRIAL n=[0-7] native_rfi=1 select_return=1 sleep_stack=1 saved_abi=1 restore_entry=1|V1334_LOAD_REFUSAL kind=[1-7] stage=[0-4] reason=[0-6] abi=[0-5] visits=[0-9]{1,3}|V1334_LOAD_TRIAL n=[0-7] original_loader=1 native_rfi=1 saved_abi=1 gqr=1 cooperative_return=1|V1332_SELECTION_BOUNDARY detail=([1-9]|10)|V1328_SELECTION_REFUSAL kind=[1-7] stage=[0-6] reason=[0-3] route=[0-2] route_reason=[0-5] visits=[0-9]{1,4}|V1328_SELECTION_TRIAL n=[0-7] original_clear=1 original_callback=1 original_set=1 loader_entry=1 preserved=1|V1323_HELPER_RAM_TRIAL n=[0-7] seeded_words=31 verified_route_words=296|V1320_IDLE_SAVE_TRIAL n=[0-7] native_save=1 complete_context=1 second_idle_rfi=1 ready=1|V1318_RETURN_INSTRUCTION detail=[1-9] boundary=[0-9] owner=[0-5] ticks=[0-9]|V1315_SAVE_REFUSAL kind=[1-3] stage=[0-2] reason=[0-5] abi=[0-5] visits=[0-9]{1,3}|V1315_SAVE_TRIAL n=[0-7] native_save=1 original_return=1 saved_abi=1 gqr=1 idle_preserved=1|V1313_RETURN_CONTROL detail=([1-9]|1[0-5]) target=([0-9]|1[0-2]) owner=[0-5] x2=[01]|V1305_IDLE_REFUSAL kind=[1-8] stage=[0-4] reason=[0-9] entry=[0-9]{1,3} join=[0-2] visits=[0-9]{1,3} select=[0-6]|V1305_IDLE_TRIAL n=[0-7] original_epilogue=1 native_rfi=1 idle_restored=1 ready_preserved=1|V1302_RETURN_MMIO detail=[0-8] reg=[0-5] ctrl=[0-9]{1,2} value_class=[0-6]|V1300_RETURN_REFUSAL kind=[1-6] stage=[0-2] reason=[0-7] gate=[0-3] visits=[0-9]{1,4}|V1300_RETURN_TRIAL n=[0-7] original_processor_return=1 original_handler_return=1 latch_clear=1 ready=1|V1294_MMIO_REFUSAL reason=([0-9]|10) owner=[0-4] form=[0-4]|V1292_NESTED_TRIAL n=[0-7] original_select_return=1 original_restore=1 original_wake_return=1 ready=1|V1292_NESTED_REFUSAL kind=[1-6] stage=[0-2] reason=[0-8] visits=[0-9]{1,4}|V1289_READY_TRIAL n=[0-7] original_wake=1 nested_disable=1 drained=1 ready=1 enrolled=1 select_executed=0|V1289_WAKE_REFUSAL kind=[1-6] stage=[0-2] reason=[0-8] visits=[0-9]{1,4}|V1282_WAKE_ENTRY_TRIAL n=[0-7] original_processor=1 armmsg=1 native_dcbi=1 y1_w1c=1 queue=1 wake_executed=0|V1282_BODY_REFUSAL kind=[1-6] stage=[0-2] reason=[0-8] gate=[0-6] visits=[0-9]{1,4} reads=[0-9]{1,2} invalidations=[0-9]{1,3}|V1275_REPLY_DISPATCH_TRIAL n=[0-7] dispatcher=1 index=27 handler_entry=1 pending_reply=1|V1275_REPLY_ENTRY_TRIAL n=[0-7] original_handler=1 reply_processor_entry=1 pending_reply=1 waiting=1|V1275_REPLY_REFUSAL kind=[1-5] stage=[0-2] reason=[0-7] reads=[0-9]{1,2} visits=[0-9]{1,4}|V1271_RFI_TRIAL n=[0-7] original_scheduler=1 native_rfi=1 restored=1 reply_irq=1 waiting=1|V1271_REPLY_VECTOR_TRIAL n=[0-7] original_vector=1 trampoline=1 saved_fields=38 pending_reply=1 dispatcher_executed=0|V1271_EPILOGUE_REFUSAL kind=[1-8] stage=[0-5] reason=[0-9] entry=[0-9]{1,3} visits=[0-9]{1,3} select=[0-6]|V1266_ACK_TRIAL n=[0-7] handler_return=1 guest_w1c=1 native_reply=1 waiting=1 saved_fields=38|V1266_ACK_REFUSAL kind=[1-7] stage=[0-3] reason=[0-8] gate=[0-4] gate_reason=[0-3] visits=[0-9]{1,4}|V1261_DISPATCH_TRIAL n=[0-7] original_dispatcher=1 index=27 context=1 pi_reads=1 handler_entry=1 handler_executed=0|V1264_DOL_DATA verified=1 initialized_only=1 ranges=([1-9]|1[01])|V1261_DISPATCH_REFUSAL kind=[1-6] stage=[0-6] reason=[0-6] reads=[0-9]{1,2} detail=([0-9]|10) visits=[0-9]{1,4}|V1260_VECTOR_TRIAL n=[0-7] saved_fields=38 original_vector=1 trampoline=1 pending_ack=1 dispatcher_executed=0|V1260_VECTOR_REFUSAL kind=[1-4] stage=[0-3] reason=[0-6] gpr=[0-9]{1,10} special=[0-9]{1,2}|V1259_IRQ_TRIAL n=[0-7] entered=1 srr=1 registers=1 pending_ack=1 vector_executed=0|V1256_SCHED_POLL_REFUSAL stage=[1-6] category=[12]|V1254_SUBMIT_MMIO_REFUSAL category=[1-5] writes=[0-2] control=[01] low_bits=[0-9]{1,2} prior=[0-9]{1,2}|V1256_SCHED_TRIAL n=[0-7] saved=1 idle=1 enabled=1 pending_ack=1 irq_entered=0|V1252_SLEEP_TRIAL n=[0-7] waiting=1 queue=1 pending_ack=1 reply=0|V1256_OPEN_TRIAL n=[0-7] path=[12] request=1 native_rfi=1 serviced=0|V1256_SUBMIT_TRIAL n=[0-7] path=[12] ack=1 reply=0 si_quiescent=1|V1256_OPEN_FAILURE kind=(witness|assertion|interpreter|syscall|null_branch|mmio|mailbox|other) trial=[0-7] stage=[0-9]{1,2} reason=[0-7] line=[0-9]{1,4}' "$work/run.log" || true
grep -Ex 'STM_DEFERRED_ACTIVE_RETURN_REFUSAL kind=[1-7] stage=[0-5] reason=[0-9] entry=[0-9]{1,3} join=[0-2] detail=([0-9]|1[0-3]) gqr=[0-9]{1,3} visits=[0-9]{1,3} select=[0-6]|STM_DEFERRED_ACTIVE_RETURN_TRIAL n=[0-7] native_rfi=1 original_epilogue=1 active_context=1 deferred=1 reply=0 resume_instruction_executed=0 visits=[0-9]{1,3}' "$work/run.log" || true
grep -Ex 'STM_RESUMED_RESTORE_REFUSAL kind=[1-5] stage=[0-2] reason=[0-4] visits=[0-9] rfi=[0-5]|STM_RESUMED_RESTORE_TRIAL n=[0-7] native_resume=1 original_restore_return=1 stm_caller=1 deferred=1 reply=0 stm_instruction_executed=0 visits=[0-9]' "$work/run.log" || true
grep -Ex 'STM_FINAL_RETURN_REFUSAL kind=[1-6] stage=[0-2] reason=[0-6] visits=[0-9]{1,2} loads=[0-9]{1,2} stores=[0-1]|STM_FINAL_RETURN_TRIAL n=[0-7] original_stm_return=1 state_store=1 caller_abi=1 deferred=1 reply=0 osinit_instruction_executed=0 visits=[0-9]{1,2} loads=[0-9]{1,2}' "$work/run.log" || true
grep -Ex 'POST_STM_SC_REFUSAL kind=[1-7] stage=[0-2] reason=[0-6] visits=[0-6] stores=[0-3]|POST_STM_SC_TRIAL n=[0-7] original_osinit_call=1 original_sc_prefix=1 stack_stores=3 disable_entry=1 deferred=1 reply=0 disable_executed=0 visits=6' "$work/run.log" || true
grep -Ex 'POST_STM_SC_DISABLE_REFUSAL kind=[1-7] stage=[0-2] reason=[0-4] visits=[0-9]{1,2}|POST_STM_SC_DISABLE_TRIAL n=[0-7] original_disable=1 native_msr=1 previous_ee=1 sc_return=1 deferred=1 reply=0 decision_executed=0 visits=[0-9]{1,2}' "$work/run.log" || true
grep -Ex 'POST_STM_SC_DECISION_REFUSAL kind=[1-7] stage=[0-2] reason=[0-6] ordinal=[0-9]{1,2} visits=[0-8] loads=[0-1] stores=[0-2]|POST_STM_SC_DECISION_TRIAL n=[0-7] cold_bss=1 original_branch=1 native_load=1 native_stores=2 restore_entry=1 deferred=1 reply=0 restore_executed=0 visits=[1-8]' "$work/run.log" || true
grep -Ex 'POST_STM_SC_RESTORE_REFUSAL kind=[1-7] stage=[0-3] reason=[0-5] ordinal=[0-9]{1,2} visits=[0-9]{1,2}|POST_STM_SC_RESTORE_TRIAL n=[0-7] native_msr=1 quiet_poll=1 original_suffix=1 original_return=1 deferred=1 reply=0 version_executed=0 visits=[0-9]{1,2}' "$work/run.log" || true
grep -Ex 'POST_STM_SC_VERSION_REFUSAL kind=[1-7] stage=[0-2] reason=[0-5] ordinal=[0-9]{1,2} visits=[0-9]{1,2}|POST_STM_SC_VERSION_TRIAL n=[0-7] original_pointer=1 original_thunk=1 diagnostic_abi=1 original_tail=1 deferred=1 reply=0 report_executed=0 visits=[0-9]{1,2}' "$work/run.log" || true
grep -Ex 'POST_STM_SC_REPORT_REFUSAL kind=[1-7] stage=[0-2] reason=[0-6] visits=[0-9]{1,2} stores=[0-9]{1,2}|POST_STM_SC_REPORT_TRIAL n=[0-7] original_prologue=1 native_stores=14 va_abi=1 original_helper_entry=1 deferred=1 reply=0 helper_executed=0 visits=22' "$work/run.log" || true
grep -Ex 'POST_STM_SC_REPORT_HELPER_REFUSAL kind=[1-7] stage=[0-2] reason=[0-6] visits=[0-9]{1,2} stores=[0-9]{1,2}|POST_STM_SC_REPORT_HELPER_TRIAL n=[0-7] original_prefix=1 native_stores=5 saved_nonvolatile=3 original_next_entry=1 deferred=1 reply=0 next_executed=0 visits=13' "$work/run.log" || true
grep -Ex 'POST_STM_SC_REPORT_DEPENDENCY_REFUSAL kind=[1-7] stage=[0-2] reason=[0-6] visits=[0-9]{1,2} loads=[0-9] stores=[0-9]|POST_STM_SC_REPORT_DEPENDENCY_TRIAL n=[0-7] native_leaf=1 original_return=1 loads=[01] stores=[0-2] deferred=1 reply=0 caller_executed=0 visits=[0-9]{1,2}' "$work/run.log" || true
grep -Ex 'POST_STM_SC_REPORT_RESUME_REFUSAL kind=[1-7] stage=[0-2] reason=[0-6] visits=[0-9]{1,2}|POST_STM_SC_REPORT_RESUME_TRIAL n=[0-7] original_resume=1 formatter_entry=1 arguments=4 deferred=1 reply=0 formatter_executed=0 visits=8' "$work/run.log" || true
grep -Ex 'POST_STM_SC_FORMATTER_REFUSAL kind=[1-7] stage=[0-2] reason=[0-6] visits=[0-9]{1,2} loads=[0-9] stores=[0-9]|POST_STM_SC_FORMATTER_TRIAL n=[0-7] original_formatter=1 native_stores=4 native_loads=1 saved_nonvolatile=16 original_dependency_entry=1 deferred=1 reply=0 dependency_executed=0 visits=23' "$work/run.log" || true
grep -Ex 'POST_STM_SC_FORMATTER_LEAF_REFUSAL kind=[1-7] stage=[0-2] reason=[0-6] visits=[0-9]{1,2} loads=[0-9] stores=[0-9]|POST_STM_SC_FORMATTER_LEAF_TRIAL n=[0-7] native_leaf=1 original_return=1 exact_value=1 loads=1 stores=0 frame_held=1 deferred=1 reply=0 visits=8' "$work/run.log" || true
grep -Ex 'FORMATTER_CONTINUATION_REFUSAL kind=[1-7] stage=[0-2] reason=[0-5] visits=[0-9]{1,2}|FORMATTER_CONTINUATION_TRIAL n=[0-7] native_resume=1 next_entry=1 arguments=4 frame_held=1 deferred=1 reply=0 visits=10' "$work/run.log" || true
grep -Ex 'FORMATTER_NESTED_REFUSAL kind=[1-7] stage=[0-5] reason=[0-6] visits=[0-9]{1,2} loads=[0-9]{1,2} stores=[0-9]{1,2}|FORMATTER_NESTED_TRIAL n=[0-7] native_prefix=1 frame=48 loads=1 stores=12 nonvolatile=3 pre_load_stop=1 deferred=1 reply=0 visits=35' "$work/run.log" || true
grep -Ex 'FORMATTER_NESTED_CELL_TRIAL n=[0-7] cold_match=[01] live_match=[01] sample_equal=[01] guest_load=0' "$work/run.log" || true
grep -Ex 'FORMATTER_SECOND_TRIAL n=[0-7] native_prefix=1 frame=48 loads=2 stores=12 nonvolatile=3 conditional_load=1 pre_load_stop=1 deferred=1 reply=0 visits=44' "$work/run.log" || true
grep -Ex 'FORMATTER_THIRD_TRIAL n=[0-7] native_prefix=1 frame=48 loads=5 stores=13 nonvolatile=([3-9]|1[0-8]) authenticated_loads=[3-5] conditional_loads=2 pre_load_stop=1 deferred=1 reply=0 visits=74' "$work/run.log" || true
grep -Ex 'FORMATTER_CONTROL_TRIAL n=[0-7] native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 pre_transfer_stop=1 transfer_executed=0 deferred=1 reply=0 visits=76' "$work/run.log" || true
grep -Ex 'FORMATTER_ARRIVAL_TRIAL n=[0-7] native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 transfer_executed=1 destination_arrival=1 destination_body=0 deferred=1 reply=0 visits=77' "$work/run.log" || true
grep -Ex 'FORMATTER_POST_CTR_TRIAL n=[0-7] native_prefix=1 frame=48 loads=8 stores=13 nonvolatile=3 authenticated_loads=5 local_transfer=1 stack_stop=1 unresolved_load=0 deferred=1 reply=0 visits=84' "$work/run.log" || true
if [[ "$formatter_post_ctr_mode" == 1 && "$formatter_partial_mode" == 0 ]];then
  for i in {0..7};do
    marker="FORMATTER_POST_CTR_STACK_PROVENANCE_TRIAL n=$i written_bytes=2 unwritten_bytes=2 mask_match=1 guest_load=0"
    [[ "$(grep -Fxc "$marker" "$work/run.log" || true)" == 1 ]] || { echo "FORMATTER_POST_CTR_STACK_PROVENANCE verified=0";exit 1; }
  done
  echo 'FORMATTER_POST_CTR_STACK_PROVENANCE verified=1 trials=8 written_bytes=16 unwritten_bytes=16 guest_loads=0'
fi
grep -Ex 'FORMATTER_PARTIAL_TRIAL n=[0-7] native_prefix=1 frame=48 loads=9 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 instruction_stop=1 deferred=1 reply=0 visits=95' "$work/run.log" || true
[[ "$rc" == 0 ]] || { echo "V1256 execution failed rc=$rc";exit 1; }
grep -Fx 'V1256_SCHED_NATIVE owner=1 trials=8 submitted=8 ack=8 waiting=8 saved=8 idle=8 ee=8 pending_irq=8 irq_entered=0 reply=0 seeded_thread=1 synthetic_ack=1 synthetic_caller=1 synthetic_bridge=1 seeded_vector=1 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"

if [[ $# == 4 ]];then
  grep -Fx 'V1259_IRQ_NATIVE owner=1 trials=8 entered=8 saved=8 idle=8 pending_ack=8 vector_executed=0 reply=0 seeded_vector=1 fallback=0 boot_verified=0' "$work/run.log"
fi

if [[ "${4-}" == --irq-vector || "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then
  grep -Fx 'V1260_VECTOR_NATIVE owner=1 trials=8 original_vector=8 trampoline=8 saved_fields=38 dispatcher_entry=8 dispatcher_executed=0 pending_ack=8 reply=0 fallback=0 boot_verified=0' "$work/run.log"
fi

if [[ "${4-}" == --irq-dispatch || "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then
  grep -Fx 'V1261_DISPATCH_NATIVE owner=1 trials=8 dispatcher=8 ipc_index=27 handler_entry=8 handler_executed=0 pending_ack=8 reply=0 fallback=0 boot_verified=0' "$work/run.log"
fi

if [[ "${4-}" == --irq-ack || "${4-}" == --irq-return ]];then
  grep -Fx 'V1266_ACK_NATIVE owner=1 trials=8 original_dispatch=8 original_handler_return=8 native_reply=8 waiting=8 saved_fields=38 modeled_dispatch=0 wakeup=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "${4-}" == --irq-return ]];then
  grep -Fx 'V1271_REPLY_VECTOR_NATIVE owner=1 trials=8 first_rfi=8 restored=8 reply_irq=8 original_vector=8 trampoline=8 saved_fields=38 second_dispatch=0 wakeup=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$reply_entry_mode" == 1 ]];then
  grep -Fx 'V1275_REPLY_ENTRY_NATIVE owner=1 trials=8 original_second_dispatch=8 original_reply_handler=8 reply_processor_entry=8 waiting=8 ios_steps=2 wakeup=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$reply_body_mode" == 1 ]];then
  grep -Fx 'V1282_REPLY_WAKE_NATIVE owner=1 trials=8 original_processor=8 armmsg=8 native_dcbi=8 y1_w1c=8 original_wake_entry=8 waiting=8 ios_steps=2 wake_executed=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$wake_ready_mode" == 1 ]];then
  grep -Fx 'V1289_WAKE_READY_NATIVE owner=1 trials=8 original_wake=8 nested_disable=8 drained=8 ready=8 enrolled=8 select_executed=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$nested_wake_mode" == 1 ]];then
  grep -Fx 'V1292_NESTED_NATIVE owner=1 trials=8 original_select_return=8 original_restore=8 original_wake_return=8 ready=8 thread_resumed=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$reply_return_mode" == 1 ]];then
  grep -Fx 'V1300_REPLY_RETURN_NATIVE owner=1 trials=8 original_processor_return=8 original_handler_return=8 latch_clear=8 ready=8 ios_steps=2 thread_resumed=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ready_idle_mode" == 1 ]];then
  grep -Fx 'V1305_READY_IDLE_NATIVE owner=1 trials=8 original_epilogue=8 native_rfi=8 idle_restored=8 ready_preserved=8 ios_steps=2 thread_resumed=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$coop_save_mode" == 1 ]];then
  grep -Fx 'V1315_SAVE_NATIVE owner=1 trials=8 native_save=8 original_return=8 saved_abi=8 gqr=8 idle_preserved=8 fallback=0 thread_resumed=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$save_continuity_mode" == 1 ]];then
  grep -Fx 'V1320_IDLE_SAVE_NATIVE owner=1 trials=8 native_save=8 complete_context=8 second_idle_rfi=8 ready=8 ios_steps=2 thread_resumed=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$selection_mode" == 1 ]];then
  grep -Fx 'V1328_SELECTION_NATIVE owner=1 trials=8 original_clear=8 original_callback=8 original_set=8 loader_entry=8 preserved=8 thread_resumed=0 ios_steps=2 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$coop_load_mode" == 1 ]];then
  grep -Fx 'V1334_COOPERATIVE_LOAD_NATIVE owner=1 trials=8 original_loader=8 native_rfi=8 saved_abi=8 gqr=8 cooperative_return=8 sleep_return=0 ios_steps=2 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$sleep_resume_mode" == 1 ]];then
  grep -Fx 'V1336_SLEEP_NATIVE owner=1 trials=8 native_rfi=8 select_return=8 sleep_stack=8 saved_abi=8 restore_entry=8 sleep_return=0 ios_steps=2 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$sleep_exit_mode" == 1 ]];then
  grep -Fx 'V1340_SLEEP_EXIT_NATIVE owner=1 trials=8 nested_restore=8 sleep_return=8 submit_resume=8 caller_abi=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$submit_resume_mode" == 1 ]];then
  grep -Fx 'V1344_SUBMIT_NATIVE owner=1 trials=8 outer_restore=8 reply_held=8 free_entry=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$allocator_release_mode" == 1 ]];then
  grep -Fx 'V1352_ALLOCATOR_NATIVE owner=1 trials=8 native_free=8 heap_shadow=8 caller_abi=8 inline_return=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$allocator_metadata_mode" == 1 ]];then
  [[ "$(grep -Ec '^V1356_DESCRIPTOR_RETURN n=[0-7] exact_field=1 shadow=1 stores=[1-9][0-9]{0,3}$' "$work/run.log")" == 8 ]]
fi

if [[ "$open_return_mode" == 1 ]];then
  grep -Fx 'V1358_OPEN_NATIVE owner=1 trials=8 submit_return=8 open_return=8 stm_resume=8 descriptor=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$second_open_mode" == 1 ]];then
  grep -Fx 'V1359_SECOND_NATIVE owner=1 trials=8 second_entry=8 opposite_path=8 descriptor_store=8 first_fd_held=8 ios_steps=2 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$second_request_mode" == 1 ]];then
  grep -Fx 'V1364_REQUEST_NATIVE owner=1 trials=8 request=8 opposite_path=8 native_rfi=8 first_fd_held=8 ios_steps=2 second_submitted=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$second_submit_mode" == 1 ]];then
  grep -Fx 'V1366_SUBMIT_NATIVE owner=1 trials=8 submitted=8 ack=8 second_fd=8 first_fd_held=8 native_rfi=8 ios_steps=3 second_reply=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$second_scheduler_mode" == 1 ]];then
  grep -Fx 'V1368_SCHED_NATIVE owner=1 trials=8 second_sleep=8 second_save=8 idle_reused=8 ee=8 pending_ack=8 ios_steps=3 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$second_reply_mode" == 1 ]];then
  grep -Fx 'V1370_REPLY_NATIVE owner=1 trials=8 ack_irq=8 original_ack_return=8 native_reply=8 native_rfi=8 reply_irq=8 original_processor=8 wake_entry=8 ios_steps=4 fd=1 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$second_restore_mode" == 1 ]];then
  grep -Fx 'V1374_RESTORE_NATIVE owner=1 trials=8 wake=8 handler_return=8 idle_rfi=8 selection=8 cooperative_rfi=8 sleep_return=8 ios_steps=4 fd=1 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$second_free_mode" == 1 ]];then
  grep -Fx 'V1378_FREE_NATIVE owner=1 trials=8 second_free=8 heap_shadow=8 metadata_shadow=8 abi=8 inline_return=8 ios_steps=4 fd=1 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$second_return_mode" == 1 ]];then
  grep -Fx 'V1379_OPEN_NATIVE owner=1 trials=8 second_submit_return=8 second_open_return=8 stm_resume=8 fd=1 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_ioctl_mode" == 1 ]];then
  grep -Fx 'V1383_IOCTL_NATIVE owner=1 trials=8 original_stm=8 native_disable=8 ioctl_entry=8 event_fd=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ioctl_prefix_mode" == 1 ]];then
  grep -Fx 'V1386_PREFIX_NATIVE owner=1 trials=8 allocator_entry=8 original_save=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ioctl_alloc_mode" == 1 ]];then
  grep -Fx 'V1387_ALLOCATION_NATIVE owner=1 trials=8 allocation_return=8 heap_shadow=8 metadata_shadow=8 masked=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ioctl_build_mode" == 1 ]];then
  grep -Fx 'V1392_CONSTRUCTION_NATIVE owner=1 trials=8 request=8 first_flush_entry=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ioctl_flush_mode" == 1 ]];then
  grep -Fx 'V1398_FLUSH_NATIVE owner=1 trials=8 first_flush_return=8 native_rfi=8 masked=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ioctl_output_mode" == 1 ]];then
  grep -Fx 'V1401_OUTPUT_NATIVE owner=1 trials=8 second_flush_return=8 native_rfi=8 submit_entry=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ioctl_submit_prefix_mode" == 1 ]];then
  grep -Fx 'V1404_PREFIX_NATIVE owner=1 trials=8 submit=8 queue_path_verified=8 header_flush_entry=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ioctl_header_mode" == 1 ]];then
  [[ "$(grep -Ec '^V1407_HEADER_TRIAL n=[0-7] original_flush=1 native_rfi=1 masked=1 request_preserved=1 lines=[1-9][0-9]{0,2}$' "$work/run.log")" == 8 ]]
  grep -Fx 'V1407_HEADER_NATIVE owner=1 trials=8 header_flush_return=8 native_rfi=8 request_preserved=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ioctl_queue_mode" == 1 ]];then
  [[ "$(grep -Ec '^V1410_QUEUE_TRIAL n=[0-7] original_disable=1 masked=1 queue_entry=1 request_preserved=1 visits=[1-9][0-9]{0,2} stores=[0-9]{1,4} polls=[0-9]{1,3}$' "$work/run.log")" == 8 ]]
  grep -Fx 'V1410_QUEUE_NATIVE owner=1 trials=8 nested_disable=8 queue_entry=8 request_preserved=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ipc_profile_mode" == 1 ]];then
  [[ "$(grep -Ec '^IPC_PROFILE_TRIAL n=[0-7] original_return=1 masked=1 ring_preserved=1 request_preserved=1 visits=[1-9][0-9]{0,3} stores=[24] polls=[0-9]{1,3} slot=[01]$' "$work/run.log")" == 8 ]]
  grep -Fx 'IPC_PROFILE_NATIVE owner=1 trials=8 profile_return=8 ring_preserved=8 request_preserved=8 ios_steps=4 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ipc_dispatch_mode" == 1 ]];then
  [[ "$(grep -Ec '^IPC_DISPATCH_TRIAL n=[0-7] original_return=1 masked=1 ring_dequeued=1 credit_consumed=1 message=1 control=1 queued=1 serviced=0 visits=[1-9][0-9]{0,2} stores=3 calls=3 writes=2 reads=1 polls=[0-9]{1,3}$' "$work/run.log")" == 8 ]]
  grep -Fx 'IPC_DISPATCH_NATIVE owner=1 trials=8 original_return=8 ring_dequeued=8 mailbox_submitted=8 queued=8 ios_steps=4 deferred=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$ipc_deferred_mode" == 1 ]];then
  [[ "$(grep -Ec '^IPC_DEFERRED_TRIAL n=[0-7] original_boundary=1 deferred=1 pending_ack=1 masked=1 cpu_preserved=1 ring_preserved=1 request_preserved=1 reply=0 ios_steps=5$' "$work/run.log")" == 8 ]]
  grep -Fx 'IPC_DEFERRED_NATIVE owner=1 trials=8 original_boundary=8 deferred=8 pending_ack=8 cpu_preserved=8 request_preserved=8 reply=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$async_return_mode" == 1 ]];then
  [[ "$(grep -Ec '^ASYNC_SUBMIT_TRIAL n=[0-7] original_return=1 masked=1 abi=1 deferred=1 visits=[1-9][0-9]{0,2} polls=[0-9]{1,2}$' "$work/run.log")" == 8 ]]
  grep -Fx 'ASYNC_SUBMIT_NATIVE owner=1 trials=8 original_return=8 masked=8 abi=8 deferred=8 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$async_wrapper_mode" == 1 ]];then
  [[ "$(grep -Ec '^ASYNC_WRAPPER_TRIAL n=[0-7] original_return=1 masked=1 abi=1 deferred=1 visits=[1-9][0-9]{0,2} loads=[1-9][0-9]? restored=[1-9][0-9]? polls=[01]$' "$work/run.log")" == 8 ]]
  grep -Fx 'ASYNC_WRAPPER_NATIVE owner=1 trials=8 original_return=8 masked=8 abi=8 deferred=8 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_event_return_mode" == 1 ]];then
  [[ "$(grep -Ec '^STM_EVENT_RETURN_TRIAL n=[0-7] original_flag=1 restore_entry=1 masked=1 deferred=1 visits=[1-9][0-9]? stores=1$' "$work/run.log")" == 8 ]]
  grep -Fx 'STM_EVENT_RETURN_NATIVE owner=1 trials=8 original_flag=8 restore_entry=8 masked=8 deferred=8 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_outer_mode" == 1 ]];then
  [[ "$(grep -Ec '^STM_OUTER_RESTORE_TRIAL n=[0-7] original_mtmsr=1 ee=1 pending_ack=1 deferred=1 visits=[1-9][0-9]?$' "$work/run.log")" == 8 ]]
  [[ "$(grep -Ec '^STM_DEFERRED_IRQ_TRIAL n=[0-7] entered=1 active_thread=1 srr=1 deferred=1 pending_ack=1 vector_executed=0$' "$work/run.log")" == 8 ]]
  grep -Fx 'STM_DEFERRED_IRQ_NATIVE owner=1 trials=8 original_mtmsr=8 ee=8 entered=8 active_thread=8 pending_ack=8 deferred=8 ios_steps=5 vector_executed=0 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_vector_mode" == 1 ]];then
  [[ "$(grep -Ec '^STM_DEFERRED_VECTOR_TRIAL n=[0-7] original_vector=1 original_trampoline=1 active_context=1 saved_fields=38 deferred=1 pending_ack=1 dispatcher_executed=0 visits=[1-9][0-9]{0,2}$' "$work/run.log")" == 8 ]]
  grep -Fx 'STM_DEFERRED_VECTOR_NATIVE owner=1 trials=8 original_vector=8 original_trampoline=8 active_context=8 saved_fields=38 deferred=8 pending_ack=8 dispatcher_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_dispatch_mode" == 1 ]];then
  [[ "$(grep -Ec '^STM_DEFERRED_DISPATCH_TRIAL n=[0-7] original_dispatch=1 handler_index=27 active_context=1 pending_ack=1 deferred=1 handler_executed=0 visits=[1-9][0-9]{0,3} reads=[1-9][0-9]?$' "$work/run.log")" == 8 ]]
  grep -Fx 'STM_DEFERRED_DISPATCH_NATIVE owner=1 trials=8 original_dispatch=8 handler_index=27 active_context=8 pending_ack=8 deferred=8 handler_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_ack_mode" == 1 ]];then
  [[ "$(grep -Ec '^STM_DEFERRED_ACK_TRIAL n=[0-7] original_return=1 guest_w1c=1 credit=1 unissued=1 deferred=1 reply=0 active_context=1 visits=[1-9][0-9]{0,3} reads=[1-9][0-9]? writes=2 stack=[1-9][0-9]? calls=[1-9][0-9]?$' "$work/run.log")" == 8 ]]
  grep -Fx 'STM_DEFERRED_ACK_NATIVE owner=1 trials=8 original_return=8 guest_w1c=8 credit=8 unissued=8 deferred=8 reply=0 active_context=8 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_active_return_mode" == 1 ]];then
  [[ "$(grep -Ec '^STM_DEFERRED_ACTIVE_RETURN_TRIAL n=[0-7] native_rfi=1 original_epilogue=1 active_context=1 deferred=1 reply=0 resume_instruction_executed=0 visits=[1-9][0-9]{0,2}$' "$work/run.log")" == 8 ]]
  grep -Fx 'STM_DEFERRED_ACTIVE_RETURN_NATIVE owner=1 trials=8 native_rfi=8 original_epilogue=8 active_context=8 deferred=8 reply=0 resume_instruction_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_resumed_restore_mode" == 1 ]];then
  [[ "$(grep -Ec '^STM_RESUMED_RESTORE_TRIAL n=[0-7] native_resume=1 original_restore_return=1 stm_caller=1 deferred=1 reply=0 stm_instruction_executed=0 visits=[1-8]$' "$work/run.log")" == 8 ]]
  grep -Fx 'STM_RESUMED_RESTORE_NATIVE owner=1 trials=8 native_resume=8 original_restore_return=8 stm_caller=8 deferred=8 reply=0 stm_instruction_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$stm_final_return_mode" == 1 ]];then
  [[ "$(grep -Ec '^STM_FINAL_RETURN_TRIAL n=[0-7] original_stm_return=1 state_store=1 caller_abi=1 deferred=1 reply=0 osinit_instruction_executed=0 visits=9 loads=3$' "$work/run.log")" == 8 ]]
  grep -Fx 'STM_FINAL_RETURN_NATIVE owner=1 trials=8 original_stm_return=8 state_store=8 caller_abi=8 deferred=8 reply=0 osinit_instruction_executed=0 modeled_osinit_bridge=1 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_sc_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_TRIAL n=[0-7] original_osinit_call=1 original_sc_prefix=1 stack_stores=3 disable_entry=1 deferred=1 reply=0 disable_executed=0 visits=6$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_NATIVE owner=1 trials=8 original_osinit_call=8 original_sc_prefix=8 disable_entry=8 deferred=8 reply=0 disable_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_disable_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_DISABLE_TRIAL n=[0-7] original_disable=1 native_msr=1 previous_ee=1 sc_return=1 deferred=1 reply=0 decision_executed=0 visits=([3-9]|1[0-2])$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_DISABLE_NATIVE owner=1 trials=8 original_disable=8 native_msr=8 previous_ee=8 sc_return=8 deferred=8 reply=0 decision_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_decision_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_DECISION_TRIAL n=[0-7] cold_bss=1 original_branch=1 native_load=1 native_stores=2 restore_entry=1 deferred=1 reply=0 restore_executed=0 visits=[1-8]$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_DECISION_NATIVE owner=1 trials=8 cold_bss=8 original_branch=8 native_load=8 native_stores=16 restore_entry=8 deferred=8 reply=0 restore_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_restore_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_RESTORE_TRIAL n=[0-7] native_msr=1 quiet_poll=1 original_suffix=1 original_return=1 deferred=1 reply=0 version_executed=0 visits=([4-9]|1[0-6])$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_RESTORE_NATIVE owner=1 trials=8 native_msr=8 quiet_poll=8 original_suffix=8 original_return=8 deferred=8 reply=0 version_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_version_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_VERSION_TRIAL n=[0-7] original_pointer=1 original_thunk=1 diagnostic_abi=1 original_tail=1 deferred=1 reply=0 report_executed=0 visits=6$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_VERSION_NATIVE owner=1 trials=8 original_pointer=8 original_thunk=8 diagnostic_abi=8 original_tail=8 deferred=8 reply=0 report_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_report_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_REPORT_TRIAL n=[0-7] original_prologue=1 native_stores=14 va_abi=1 original_helper_entry=1 deferred=1 reply=0 helper_executed=0 visits=22$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_REPORT_NATIVE owner=1 trials=8 original_prologue=8 native_stores=112 va_abi=8 original_helper_entry=8 deferred=8 reply=0 helper_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_helper_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_REPORT_HELPER_TRIAL n=[0-7] original_prefix=1 native_stores=5 saved_nonvolatile=3 original_next_entry=1 deferred=1 reply=0 next_executed=0 visits=13$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_REPORT_HELPER_NATIVE owner=1 trials=8 original_prefix=8 native_stores=40 saved_nonvolatile=24 original_next_entry=8 deferred=8 reply=0 next_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_dependency_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_REPORT_DEPENDENCY_TRIAL n=[0-7] native_leaf=1 original_return=1 loads=1 stores=1 deferred=1 reply=0 caller_executed=0 visits=20$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_REPORT_DEPENDENCY_NATIVE owner=1 trials=8 native_leaf=8 original_return=8 deferred=8 reply=0 caller_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_resume_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_REPORT_RESUME_TRIAL n=[0-7] original_resume=1 formatter_entry=1 arguments=4 deferred=1 reply=0 formatter_executed=0 visits=8$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_REPORT_RESUME_NATIVE owner=1 trials=8 original_resume=8 formatter_entry=8 arguments=32 deferred=8 reply=0 formatter_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_formatter_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_FORMATTER_TRIAL n=[0-7] original_formatter=1 native_stores=4 native_loads=1 saved_nonvolatile=16 original_dependency_entry=1 deferred=1 reply=0 dependency_executed=0 visits=23$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_FORMATTER_NATIVE owner=1 trials=8 original_formatter=8 native_stores=32 native_loads=8 saved_nonvolatile=128 original_dependency_entry=8 deferred=8 reply=0 dependency_executed=0 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$post_stm_formatter_leaf_mode" == 1 ]];then
  [[ "$(grep -Ec '^POST_STM_SC_FORMATTER_LEAF_TRIAL n=[0-7] native_leaf=1 original_return=1 exact_value=1 loads=1 stores=0 frame_held=1 deferred=1 reply=0 visits=8$' "$work/run.log")" == 8 ]]
  grep -Fx 'POST_STM_SC_FORMATTER_LEAF_NATIVE owner=1 trials=8 native_leaf=8 original_return=8 exact_value=8 loads=8 stores=0 frame_held=8 deferred=8 reply=0 visits=64 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$formatter_continuation_mode" == 1 ]];then
  [[ "$(grep -Ec '^FORMATTER_CONTINUATION_TRIAL n=[0-7] native_resume=1 next_entry=1 arguments=4 frame_held=1 deferred=1 reply=0 visits=10$' "$work/run.log")" == 8 ]]
  grep -Fx 'FORMATTER_CONTINUATION_NATIVE owner=1 trials=8 native_resume=8 next_entry=8 arguments=32 frame_held=8 deferred=8 reply=0 visits=80 ios_steps=5 fallback=0 complete_image=0 boot_verified=0' "$work/run.log"
fi

if [[ "$formatter_nested_mode" == 1 ]];then
  python3 "$here/validate_formatter_nested_log.py" "$work/run.log" "${nested_args[@]}"
fi
