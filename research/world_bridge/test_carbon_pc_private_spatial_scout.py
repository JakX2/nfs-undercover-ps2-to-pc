#!/usr/bin/env python3
"""Synthetic-only regression tests for private spatial scout."""
import csv
import io
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_carbon_pc_dxt5_spatial_smoke_target import args
from carbon_pc_private_spatial_scout import (
    scout_components, scout_original_pc_section, _safe_export_destination,
    export_private_csv, analyze_original_files,
)


def sample():
    return scout_components(*args(),slot=0,cluster_distance=12.)


class SourcePlanTests(unittest.TestCase):
    def test_counts(self):
        public,rows=sample()
        self.assertEqual(public['source_primary_scenery_instances'],4)
        self.assertEqual(len(rows),4)
    def test_two_groups(self):
        _,rows=sample()
        self.assertEqual([r['experimental_group'] for r in rows],[1,1,2,2])
    def test_each_group_size(self):
        _,rows=sample()
        self.assertEqual([r['group_size'] for r in rows],[2,2,2,2])
    def test_stable_instance_ordinals(self):
        _,rows=sample()
        self.assertEqual([r['source_instance_ordinal'] for r in rows],[0,1,2,3])
    def test_first_group_center(self):
        _,rows=sample()
        self.assertEqual(rows[0]['group_center_x'],2)
    def test_second_group_center(self):
        _,rows=sample()
        self.assertEqual(rows[2]['group_center_x'],41.5)
    def test_instance_aabb_min(self):
        _,rows=sample()
        self.assertEqual(rows[0]['instance_min_x'],1.)
    def test_instance_aabb_max(self):
        _,rows=sample()
        self.assertEqual(rows[3]['instance_max_x'],43.)
    def test_group_extent(self):
        _,rows=sample()
        self.assertEqual(rows[0]['group_min_x'],1.)
        self.assertEqual(rows[0]['group_max_x'],3.)
    def test_public_no_original_xyz_values(self):
        report,_=sample()
        self.assertNotIn('group_center_x',report)
        self.assertNotIn('source_instance_ordinal',report)
    def test_other_slot_may_fail_when_unreferenced(self):
        a=list(args());a[2]=[111,111,111,111]
        with self.assertRaises(ValueError):scout_components(*a,slot=0)
    def test_bad_slot(self):
        with self.assertRaises(ValueError):scout_components(*args(),slot=99)
    def test_bad_threshold_zero(self):
        with self.assertRaises(ValueError):scout_components(*args(),slot=0,cluster_distance=0)
    def test_bad_threshold_nan(self):
        with self.assertRaises(ValueError):scout_components(*args(),slot=0,cluster_distance=float('nan'))
    def test_wrong_tree(self):
        a=list(args());a[4]=a[4][:-3]
        with self.assertRaises(ValueError):scout_components(*a,slot=0)
    def test_bad_instance_model_links(self):
        a=list(args());a[2]=a[2][:-1]
        with self.assertRaises(ValueError):scout_components(*a,slot=0)
    def test_repeated_model_occurrence_not_repeated_instance(self):
        a=list(args());a[1]=a[1]+[(101,a[1][0][1])]
        _,rows=scout_components(*a,slot=0)
        self.assertEqual(len(rows),4)
    def test_private_rows_consistent_with_public_clusters(self):
        p,rows=sample()
        self.assertEqual(sorted({r['experimental_group'] for r in rows}),[1,2])
        self.assertEqual(sorted(p['proximity_cluster_sizes']),[2,2])
    def test_source_only_original_gate_refuses_wrong_bytes(self):
        with self.assertRaises(ValueError):scout_original_pc_section(b'bad')


class ExportSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.good=Path(self.tmp.name)/'PRIVATE_scout.csv'
    def test_valid_destination(self):
        self.assertEqual(_safe_export_destination(self.good),self.good)
    def test_private_csv_roundtrip(self):
        _,rows=sample()
        report=export_private_csv(self.good,rows)
        self.assertTrue(report['private_csv_created'])
        self.assertFalse(report['source_positions_printed'])
        with self.good.open(newline='') as fp:
            loaded=list(csv.DictReader(fp))
        self.assertEqual(len(loaded),4)
        self.assertEqual(loaded[0]['source_instance_ordinal'],'0')
    def test_private_mode_unix(self):
        _,rows=sample();export_private_csv(self.good,rows)
        if os.name=='posix':
            self.assertEqual(self.good.stat().st_mode & 0o777,0o600)
    def test_existing_destination_fail_closed(self):
        self.good.write_text('original')
        with self.assertRaises(ValueError):export_private_csv(self.good,sample()[1])
        self.assertEqual(self.good.read_text(),'original')
    def test_wrong_prefix(self):
        with self.assertRaises(ValueError):export_private_csv(self.good.with_name('public.csv'),sample()[1])
    def test_wrong_extension(self):
        with self.assertRaises(ValueError):export_private_csv(self.good.with_suffix('.json'),sample()[1])
    def test_malformed_rows(self):
        with self.assertRaises(ValueError):export_private_csv(self.good,[{'x':1}])
    def test_empty_rows(self):
        with self.assertRaises(ValueError):export_private_csv(self.good,[])
    def test_invalid_nonfinite(self):
        _,rows=sample();bad=dict(rows[0]);bad['instance_min_x']=float('inf')
        with self.assertRaises(ValueError):export_private_csv(self.good,[bad])
    def test_symlink_destination(self):
        target=Path(self.tmp.name)/'target.csv';target.write_text('x')
        link=self.good
        try:link.symlink_to(target)
        except OSError:self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError):export_private_csv(link,sample()[1])
        self.assertEqual(target.read_text(),'x')
    def test_symlink_parent(self):
        real=Path(self.tmp.name)/'actual';real.mkdir()
        alias=Path(self.tmp.name)/'alias'
        try:alias.symlink_to(real,target_is_directory=True)
        except OSError:self.skipTest('symlinks unavailable')
        with self.assertRaises(ValueError):export_private_csv(alias/'PRIVATE_x.csv',sample()[1])
    def test_nonexistent_parent(self):
        with self.assertRaises(ValueError):export_private_csv(self.good.parent/'missing'/'PRIVATE_x.csv',sample()[1])
    def test_game_tracks_directory(self):
        t=self.good.parent/'TRACKS';t.mkdir()
        with self.assertRaises(ValueError):export_private_csv(t/'PRIVATE_x.csv',sample()[1])
    def test_repository_path(self):
        t=self.good.parent/'research';t.mkdir()
        with self.assertRaises(ValueError):export_private_csv(t/'PRIVATE_x.csv',sample()[1])
    def test_source_path_overlap(self):
        with self.assertRaises(ValueError):_safe_export_destination(self.good,sources=(self.good,))
    def test_valid_sources_elsewhere(self):
        other=self.good.parent/'bun.bun';other.write_bytes(b'x')
        self.assertEqual(_safe_export_destination(self.good,sources=(other,)),self.good)
    def test_does_not_write_unless_export_called(self):
        _,rows=sample()
        self.assertFalse(self.good.exists())
        self.assertEqual(len(rows),4)
    def test_false_schema_does_not_create(self):
        rows=[dict(sample()[1][0])];rows[0].pop('instance_max_z')
        with self.assertRaises(ValueError):export_private_csv(self.good,rows)
        self.assertFalse(self.good.exists())
    def test_bad_input_paths(self):
        with self.assertRaises(ValueError):analyze_original_files(self.good,self.good)


if __name__=='__main__': unittest.main()

class AdditionalSafetyTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.good=Path(self.tmp.name)/'PRIVATE_safe.csv'
    def test_duplicate_instance_ordinal_fails(self):
        _,rows=sample();bad=[dict(r) for r in rows];bad[1]['source_instance_ordinal']=0
        with self.assertRaises(ValueError):export_private_csv(self.good,bad)
    def test_instance_ordinal_bool_fails(self):
        _,rows=sample();bad=[dict(rows[0])];bad[0]['source_instance_ordinal']=True
        with self.assertRaises(ValueError):export_private_csv(self.good,bad)
    def test_unexpected_field_rejected(self):
        _,rows=sample();bad=[dict(rows[0])];bad[0]['source_model_hash']=0xdeadbeef
        with self.assertRaises(ValueError):export_private_csv(self.good,bad)
    def test_reordered_fields_fail_closed(self):
        _,rows=sample();bad=[dict(reversed(list(rows[0].items())))]
        with self.assertRaises(ValueError):export_private_csv(self.good,bad)
    def test_missing_field_rejected(self):
        _,rows=sample();bad=[dict(rows[0])];bad[0].pop('group_center_x')
        with self.assertRaises(ValueError):export_private_csv(self.good,bad)
    def test_source_private_positions_never_in_report(self):
        public,rows=sample()
        for key in ('group_center_x','instance_min_x','instance_max_z','source_instance_ordinal'):
            self.assertNotIn(key,public)
    def test_no_file_creation_from_computation(self):
        sample()
        self.assertFalse(self.good.exists())
    def test_no_file_created_on_duplicate(self):
        _,rows=sample();bad=[dict(r) for r in rows];bad[0]['source_instance_ordinal']=bad[1]['source_instance_ordinal']
        with self.assertRaises(ValueError):export_private_csv(self.good,bad)
        self.assertFalse(self.good.exists())
