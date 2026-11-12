#!/usr/bin/env python3
"""Joint original-free Carbon external file-access and A/B/A visual evidence.

Combines V17 three-run calibrated ProcMon file access with the established
strict RGB/RGBA PNG target/anchor/restore comparison. This is a post-capture,
read-only *co-occurrence* gate. It cannot prove ASI execution, causality,
resource registration, original-game scene ownership, or rendering of the
specific Undercover model. No paths, images, coordinates, IDs or PIDs appear
in the JSON output.
"""
import argparse
import json
import os
from pathlib import Path

from carbon_pc_external_aba_capture_gate import audit_owner_aba_files
from carbon_pc_original_loader_control_chain import _stamp
from carbon_pc_private_visual_evidence_gate import (
    MAX_PNG_BYTES, MAX_ROI_BYTES, _owner_file, compare_png_evidence,
)


VISUAL_CANDIDATE = (
    'reversible_localized_screen_difference_candidate_not_rendering_proof'
)
READ_CANDIDATE = 'ISOLATED_EXTERNAL_FILE_READ_OBSERVED_NOT_REGISTRATION'


def join_carbon_aba_io_and_visual(file_report, visual_report):
    """Combine reports from established gates, without promoting evidence.

    The original input reports come from independent original-free
    filesystem and PNG analysis. The aggregate report only contains
    selected non-private scalars and explicit negative runtime claims.
    """
    if type(file_report) is not dict or type(visual_report) is not dict:
        raise ValueError('Expected two independently produced evidence reports')
    if file_report.get('scope') != 'OWNER_CAPTURED_CARBON_A_B_A_FILE_IO_NOT_RUNTIME_LOADING':
        raise ValueError('Wrong source scope for three-run Carbon file audit')
    if visual_report.get('scope') != 'PRIVATE_SCREENSHOT_PIXEL_COMPARISON_NOT_RENDERING_PROOF':
        raise ValueError('Wrong source scope for three-run Carbon visual audit')
    required_file = ('all_captures_calibrated',
                     'external_access_isolated_to_control_capture',
                     'control_external_and_sentinel_same_pid',
                     'control_same_pid_open_read_observed',
                     'control_full_external_file_read_observed')
    for key in required_file:
        if type(file_report.get(key)) is not bool:
            raise ValueError('Missing or malformed Carbon file evidence flag')
    required_visual = ('same_dimensions', 'background_anchor_stability_passed',
                       'restoration_control_performed',
                       'restoration_visual_match_to_baseline')
    for key in required_visual:
        if type(visual_report.get(key)) is not bool:
            raise ValueError('Missing or malformed PNG evidence flag')

    io = (file_report.get('evidence_level') == READ_CANDIDATE and
          file_report['all_captures_calibrated'] and
          file_report['external_access_isolated_to_control_capture'] and
          file_report['control_external_and_sentinel_same_pid'] and
          file_report['control_same_pid_open_read_observed'])
    visual = (
        visual_report.get('verdict') == VISUAL_CANDIDATE and
        visual_report['same_dimensions'] and
        visual_report['background_anchor_stability_passed'] and
        visual_report['restoration_control_performed'] and
        visual_report['restoration_visual_match_to_baseline']
    )
    if io and visual:
        level = 'CORRELATED_FILE_READ_AND_REVERSIBLE_SCREEN_CANDIDATE_NOT_REGISTRATION'
    elif io:
        level = 'ISOLATED_FILE_READ_WITHOUT_REVERSIBLE_VISUAL_CANDIDATE'
    elif visual:
        level = 'REVERSIBLE_VISUAL_CANDIDATE_WITHOUT_ISOLATED_FILE_READ'
    else:
        level = 'NO_CORRELATED_FILE_AND_REVERSIBLE_SCREEN_EVIDENCE'

    return {
        'scope': 'CARBON_PC_PRIVATE_A_B_A_JOINT_IO_VISUAL_CANDIDATE_ONLY',
        'all_file_captures_calibrated': file_report['all_captures_calibrated'],
        'external_read_isolated_to_control': io,
        'external_full_file_read_observed': (
            bool(io and file_report['control_full_external_file_read_observed'])
        ),
        'baseline_control_restore_screenshots_compared': (
            visual_report['restoration_control_performed']
        ),
        'background_anchors_stable': (
            visual_report['background_anchor_stability_passed']
        ),
        'screen_target_reverted_to_baseline': (
            visual_report['restoration_visual_match_to_baseline']
        ),
        'reversible_localized_screen_change_candidate': visual,
        'joint_evidence_level': level,
        'test_run_order_verified': False,
        'snapshot_to_procmon_time_alignment_verified': False,
        'loader_asi_executed_verified': False,
        'engine_resource_registration_verified': False,
        'specific_undercover_asset_rendering_verified': False,
        'carbon_gameplay_port_verified': False,
        'private_paths_images_roi_ids_pids_disclosed': False,
        'files_modified': False,
        'limitations': (
            'Co-occurrence of file access and a localized reversible visual '
            'change is not evidence that the file caused the changed pixels. '
            'The control may have other changes; capture timing, actual ASI '
            'execution, loaded resource identity, resource-manager registration '
            'and visibility are not independently attested. Static screenshots '
            'can be affected by camera alignment, motion and rendering state.'
        ),
    }


def audit_owner_aba_joint_files(
        game_directory, manifest_path, original_resource_path,
        sentinel_game_file, baseline_csv, control_csv, restore_csv, kind,
        baseline_png, control_png, restore_png, roi_json, *,
        windows_root_override_for_tests=None):
    """Run both already-tested owner-local audits with consistent files.

    All paths are only READ. PNG and ROI files must be separate from
    the other private file/capture inputs, must not be hardlinks, and
    must remain unchanged across the check. All reports are redacted.
    """
    image_paths = tuple(_owner_file(p, MAX_ROI_BYTES if i == 3 else MAX_PNG_BYTES)
                        for i, p in enumerate(
                            (baseline_png, control_png, restore_png, roi_json)))
    other_paths = tuple(Path(p).absolute() for p in (
        manifest_path, original_resource_path, sentinel_game_file,
        baseline_csv, control_csv, restore_csv))
    all_paths = image_paths + other_paths
    if len(set(all_paths)) != len(all_paths):
        raise ValueError('Cannot reuse a private image/ROI/control file path')
    # Both hardlink aliases and symlinks can alias one source to another.
    if any(os.path.samefile(p, q) for i, p in enumerate(all_paths)
           for q in all_paths[i+1:]):
        raise ValueError('Private image, game and trace inputs must be distinct')
    before = tuple(_stamp(p) for p in image_paths)

    file_report = audit_owner_aba_files(
        game_directory, manifest_path, original_resource_path,
        sentinel_game_file, baseline_csv, control_csv, restore_csv, kind,
        windows_root_override_for_tests=windows_root_override_for_tests)
    visual_report = compare_png_evidence(
        baseline_png, control_png, roi_json, restore_png)

    if before != tuple(_stamp(p) for p in image_paths):
        raise ValueError('Private PNG/ROI inputs changed during read-only audit')
    return join_carbon_aba_io_and_visual(file_report, visual_report)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--carbon-game-dir', required=True)
    parser.add_argument('--xnfs-manifest', required=True)
    parser.add_argument('--original-carbon-bun', required=True)
    parser.add_argument('--stock-sentinel-bun', required=True)
    parser.add_argument('--baseline-csv', required=True)
    parser.add_argument('--control-csv', required=True)
    parser.add_argument('--restore-csv', required=True)
    parser.add_argument('--kind', required=True, choices=('geometry', 'texture'))
    parser.add_argument('--baseline-png', required=True)
    parser.add_argument('--control-png', required=True)
    parser.add_argument('--restore-png', required=True)
    parser.add_argument('--roi-json', required=True)
    args = parser.parse_args()
    result = audit_owner_aba_joint_files(
        args.carbon_game_dir, args.xnfs_manifest, args.original_carbon_bun,
        args.stock_sentinel_bun, args.baseline_csv, args.control_csv,
        args.restore_csv, args.kind, args.baseline_png, args.control_png,
        args.restore_png, args.roi_json)
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
