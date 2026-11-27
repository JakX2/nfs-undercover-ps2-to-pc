#!/usr/bin/env python3
import unittest
from validate_formatter_nested_log import verify,markers

def log(second=False):
    tag,_,total=markers(second);visits,loads=(44,2) if second else (35,1)
    conditional=' conditional_load=1' if second else ''
    rows=[]
    for i in range(8):
        rows.append(f'{tag}_TRIAL n={i} native_prefix=1 frame=48 loads={loads} stores=12 nonvolatile=3{conditional} pre_load_stop=1 deferred=1 reply=0 visits={visits}')
        rows.append(f'FORMATTER_NESTED_CELL_TRIAL n={i} cold_match=1 live_match={int(i!=0)} sample_equal={int(i!=0)} guest_load=0')
    return rows+['FORMATTER_NESTED_CELL_NATIVE owner=1 trials=8 cold_match=8 live_match=7 sample_equal=7 endpoint_only=1 guest_loads=0 guest_writes=0',total]
class Test(unittest.TestCase):
    def test_exact(self):
        for mode in (False,True):self.assertEqual(verify(log(mode),second=mode),tuple(log(mode)[-2:]))
    def test_duplicate(self):
        x=log();x[2]=x[0]
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x)
        x=log();x[3]=x[1]
        with self.assertRaisesRegex(ValueError,'cell trial'):verify(x)
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(log()[2:])
    def test_false_total(self):
        x=log();x[-2]=x[-2].replace('live_match=7','live_match=8')
        with self.assertRaisesRegex(ValueError,'totals'):verify(x)
    def test_false_equality(self):
        x=log();x[1]=x[1].replace('sample_equal=0','sample_equal=1')
        with self.assertRaisesRegex(ValueError,'consistency'):verify(x)
    def test_native_refusal(self):
        with self.assertRaisesRegex(ValueError,'refusal'):verify(log()+['FORMATTER_NESTED_REFUSAL kind=2'])
    def test_cross_mode(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(log(True))
def third_log():
    rows=log()
    for i in range(8):
        rows[2*i]=f'FORMATTER_THIRD_TRIAL n={i} native_prefix=1 frame=48 loads=5 stores=13 nonvolatile=3 authenticated_loads=4 conditional_loads=2 pre_load_stop=1 deferred=1 reply=0 visits=74'
    rows[-1]='FORMATTER_THIRD_NATIVE owner=1 trials=8 native_prefix=8 loads=40 stores=104 nonvolatile=24 authenticated_loads=32 conditional_loads=16 pre_load_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=592 ios_steps=5 fallback=0 complete_image=0 boot_verified=0'
    return rows
class Third(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(third_log(),third=True),tuple(third_log()[-2:]))
    def test_details(self):
        x=third_log();x[2]=x[2].replace('authenticated_loads=4','authenticated_loads=3')
        with self.assertRaisesRegex(ValueError,'details'):verify(x,third=True)
    def test_totals(self):
        x=third_log();x[-1]=x[-1].replace('authenticated_loads=32','authenticated_loads=24')
        with self.assertRaisesRegex(ValueError,'native totals'):verify(x,third=True)
    def test_counts(self):
        x=third_log();x[0]=x[0].replace('authenticated_loads=4','authenticated_loads=2')
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x,third=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(third_log(),second=True)
        with self.assertRaisesRegex(ValueError,'mode'):verify(third_log(),second=True,third=True)
def control_log():
    rows=[f'FORMATTER_CONTROL_TRIAL n={i} native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 pre_transfer_stop=1 transfer_executed=0 deferred=1 reply=0 visits=76' for i in range(8)]
    return rows+['FORMATTER_CONTROL_NATIVE owner=1 trials=8 native_prefix=8 loads=48 stores=104 nonvolatile=24 authenticated_loads=40 conditional_loads=24 ctr_match=8 destination_word=8 pre_transfer_stop=8 transfer_executed=0 deferred=8 reply=0 visits=608 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
class Control(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(control_log(),control=True),tuple(control_log()[-1:]))
    def test_target(self):
        x=control_log();x[0]=x[0].replace('ctr_match=1','ctr_match=0')
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x,control=True)
    def test_transfer(self):
        x=control_log();x[-1]=x[-1].replace('transfer_executed=0','transfer_executed=1')
        with self.assertRaisesRegex(ValueError,'native aggregate'):verify(x,control=True)
    def test_cell(self):
        with self.assertRaisesRegex(ValueError,'unexpected cell'):verify(control_log()+[log()[1]],control=True)
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(control_log()[1:],control=True)
    def test_mixed(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(control_log(),control=True,third=True)
def arrival_log():
    return [f'FORMATTER_ARRIVAL_TRIAL n={i} native_prefix=1 frame=48 loads=6 stores=13 nonvolatile=3 authenticated_loads=5 conditional_loads=3 ctr_match=1 destination_word=1 transfer_executed=1 destination_arrival=1 destination_body=0 deferred=1 reply=0 visits=77' for i in range(8)]+['FORMATTER_ARRIVAL_NATIVE owner=1 trials=8 native_prefix=8 loads=48 stores=104 nonvolatile=24 authenticated_loads=40 conditional_loads=24 ctr_match=8 destination_word=8 transfer_executed=8 destination_arrival=8 destination_body=0 deferred=8 reply=0 visits=616 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
class Arrival(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(arrival_log(),arrival=True),tuple(arrival_log()[-1:]))
    def test_transfer(self):
        x=arrival_log();x[0]=x[0].replace('transfer_executed=1','transfer_executed=0')
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x,arrival=True)
    def test_body(self):
        x=arrival_log();x[-1]=x[-1].replace('destination_body=0','destination_body=8')
        with self.assertRaisesRegex(ValueError,'native aggregate'):verify(x,arrival=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(arrival_log(),arrival=True,control=True)
        with self.assertRaisesRegex(ValueError,'coverage'):verify(control_log(),arrival=True)
def post_ctr_log():
    return [f'FORMATTER_POST_CTR_TRIAL n={i} native_prefix=1 frame=48 loads=8 stores=13 nonvolatile=3 authenticated_loads=5 local_transfer=1 stack_stop=1 unresolved_load=0 deferred=1 reply=0 visits=84' for i in range(8)]+['FORMATTER_POST_CTR_NATIVE owner=1 trials=8 native_prefix=8 loads=64 stores=104 nonvolatile=24 authenticated_loads=40 local_transfer=8 stack_stop=8 unresolved_loads=0 deferred=8 reply=0 visits=672 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
class PostCtr(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(post_ctr_log(),post_ctr=True),tuple(post_ctr_log()[-1:]))
    def test_count(self):
        x=post_ctr_log();x[-1]=x[-1].replace('authenticated_loads=40','authenticated_loads=48')
        with self.assertRaisesRegex(ValueError,'native totals'):verify(x,post_ctr=True)
    def test_details(self):
        x=post_ctr_log();x[1]=x[1].replace('authenticated_loads=5','authenticated_loads=6')
        with self.assertRaisesRegex(ValueError,'native trial'):verify(x,post_ctr=True)
    def test_unresolved(self):
        x=post_ctr_log();x[0]=x[0].replace('unresolved_load=0','unresolved_load=1')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,post_ctr=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(post_ctr_log(),post_ctr=True,arrival=True)
        with self.assertRaisesRegex(ValueError,'coverage'):verify(arrival_log(),post_ctr=True)
def partial_log():
    return [f'FORMATTER_PARTIAL_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 instruction_stop=1 deferred=1 reply=0 visits=95' for i in range(8)]+['FORMATTER_PARTIAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=24 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 instruction_stop=8 deferred=8 reply=0 visits=760 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
class Partial(unittest.TestCase):
    def test_exact(self):self.assertEqual(verify(partial_log(),partial=True),tuple(partial_log()[-1:]))
    def test_reject_stale_load_totals(self):
        x=partial_log();x[0]=x[0].replace('loads=15','loads=9')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,partial=True)
        x=partial_log();x[-1]=x[-1].replace('loads=120','loads=72')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,partial=True)
    def test_parent(self):
        x=partial_log();x[1]=x[1].replace('parent_overlay=1','parent_overlay=0')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,partial=True)
    def test_total(self):
        x=partial_log();x[-1]=x[-1].replace('caller_stores=32','caller_stores=24')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,partial=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(partial_log(),partial=True,post_ctr=True)
        with self.assertRaisesRegex(ValueError,'coverage'):verify(post_ctr_log(),partial=True)
    def test_missing_and_duplicate(self):
        for x in (partial_log()[1:],partial_log()+[partial_log()[0]]):
            with self.assertRaises(ValueError):verify(x,partial=True)
class Special(unittest.TestCase):
    def logs(self):
        return [f'FORMATTER_SPECIAL_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=3 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 instruction_stop=1 deferred=1 reply=0 visits=96' for i in range(8)]+['FORMATTER_SPECIAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=24 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 instruction_stop=8 deferred=8 reply=0 visits=768 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,special=True),(x[-1],))
    def test_lr(self):
        x=self.logs();x[0]=x[0].replace('lr_restored=1','lr_restored=0')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,special=True)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('visits=768','visits=760')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,special=True)
    def test_previous_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(partial_log(),special=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),special=True,partial=True)
class Release(unittest.TestCase):
    def logs(self):
        return [f'FORMATTER_RELEASE_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 return_stop=1 return_executed=0 deferred=1 reply=0 visits=97' for i in range(8)]+['FORMATTER_RELEASE_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 return_stop=8 return_executed=0 deferred=8 reply=0 visits=776 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,release=True),(x[-1],))
    def test_return_not_executed(self):
        x=self.logs();x[0]=x[0].replace('return_executed=0','return_executed=1')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,release=True)
    def test_registers(self):
        x=self.logs();x[-1]=x[-1].replace('nonvolatile=144','nonvolatile=24')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,release=True)
    def test_previous_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(Special().logs(),release=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),release=True,special=True)
class Return(unittest.TestCase):
    def logs(self):
        return [f'FORMATTER_RETURN_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_arrival=1 caller_body=0 caller_guard=1 deferred=1 reply=0 visits=98' for i in range(8)]+['FORMATTER_RETURN_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_arrival=8 caller_body=0 caller_guard=8 deferred=8 reply=0 visits=784 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,return_mode=True),(x[-1],))
    def test_caller_body(self):
        x=self.logs();x[0]=x[0].replace('caller_body=0','caller_body=1')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,return_mode=True)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('visits=784','visits=776')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,return_mode=True)
    def test_previous_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(Release().logs(),return_mode=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),return_mode=True,release=True)
class CallerArrival(unittest.TestCase):
    def logs(self):
        return [f'FORMATTER_CALLER_ARRIVAL_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_label=1 caller_body=0 caller_guard=0 deferred=1 reply=0 visits=98' for i in range(8)]+['FORMATTER_CALLER_ARRIVAL_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_label=8 caller_body=0 caller_guard=0 deferred=8 reply=0 visits=784 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,caller_arrival=True),(x[-1],))
    def test_caller_body(self):
        x=self.logs();x[0]=x[0].replace('caller_body=0','caller_body=1')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,caller_arrival=True)
    def test_caller_label(self):
        x=self.logs();x[-1]=x[-1].replace('caller_label=8','caller_label=7')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,caller_arrival=True)
    def test_previous_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(Return().logs(),caller_arrival=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),caller_arrival=True,return_mode=True)
class CallerByte(unittest.TestCase):
    def logs(self):
        return [f'FORMATTER_CALLER_BYTE_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits=99' for i in range(8)]+['FORMATTER_CALLER_BYTE_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits=792 ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,caller_byte=True),(x[-1],))
    def test_byte(self):
        x=self.logs();x[0]=x[0].replace('caller_byte_verified=1','caller_byte_verified=0')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,caller_byte=True)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=792','total_visits=784')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,caller_byte=True)
    def test_previous_not_accepted(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(CallerArrival().logs(),caller_byte=True)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),caller_byte=True,caller_arrival=True)
class CallerIntegers(unittest.TestCase):
    def logs(self,count=2):
        return [f'FORMATTER_CALLER_INTEGERS_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={99+count}' for i in range(8)]+[f'FORMATTER_CALLER_INTEGERS_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={792+8*count} ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        for count in range(1,9):
            x=self.logs(count);self.assertEqual(verify(x,caller_integers=True,integer_count=count),(x[-1],))
    def test_wrong_count(self):
        with self.assertRaisesRegex(ValueError,'trial'):verify(self.logs(),caller_integers=True,integer_count=3)
    def test_count_required(self):
        for count in (None,0,9,True):
            with self.assertRaisesRegex(ValueError,'count'):verify(self.logs(),caller_integers=True,integer_count=count)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=808','total_visits=792')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,caller_integers=True,integer_count=2)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),caller_byte=True,integer_count=2)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(CallerByte().logs(),caller_integers=True,integer_count=2)
class CallerBranch(unittest.TestCase):
    def logs(self,count=2):
        return [f'FORMATTER_CALLER_BRANCH_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branch=1 fallthrough=1 alternate_guard=1 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={100+count}' for i in range(8)]+[f'FORMATTER_CALLER_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=8 fallthrough=8 alternate_guard=8 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={800+8*count} ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,caller_branch=True,integer_count=2),(x[-1],))
    def test_alternate(self):
        x=self.logs();x[0]=x[0].replace('alternate_guard=1','alternate_guard=0')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,caller_branch=True,integer_count=2)
    def test_outcome(self):
        x=self.logs();x[0]=x[0].replace('fallthrough=1','fallthrough=0')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,caller_branch=True,integer_count=2)
    def test_count(self):
        with self.assertRaisesRegex(ValueError,'trial'):verify(self.logs(),caller_branch=True,integer_count=1)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=816','total_visits=808')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,caller_branch=True,integer_count=2)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),caller_branch=True,caller_integers=True,integer_count=2)
class CallerSecondBranch(unittest.TestCase):
    def logs(self,count=2):
        return [f'FORMATTER_CALLER_SECOND_BRANCH_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=2 fallthrough=1 taken=1 alternate_guards=2 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={101+count}' for i in range(8)]+[f'FORMATTER_CALLER_SECOND_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=16 fallthrough=8 taken=8 alternate_guards=16 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={808+8*count} ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,caller_second_branch=True,integer_count=2),(x[-1],))
    def test_alternate(self):
        x=self.logs();x[0]=x[0].replace('alternate_guards=2','alternate_guards=1')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,caller_second_branch=True,integer_count=2)
    def test_outcome(self):
        x=self.logs();x[0]=x[0].replace('taken=1','taken=0')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,caller_second_branch=True,integer_count=2)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=824','total_visits=816')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,caller_second_branch=True,integer_count=2)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(CallerBranch().logs(),caller_second_branch=True,integer_count=2)
class CallerPostIntegers(unittest.TestCase):
    def logs(self,count=2,post=1):
        return [f'FORMATTER_CALLER_POST_INTEGERS_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=2 post_integers={post} fallthrough=1 taken=1 alternate_guards=2 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={101+count+post}' for i in range(8)]+[f'FORMATTER_CALLER_POST_INTEGERS_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=16 post_integers={8*post} fallthrough=8 taken=8 alternate_guards=16 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={808+8*(count+post)} ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        for post in range(1,9):
            x=self.logs(post=post);self.assertEqual(verify(x,caller_post_integers=True,integer_count=2,post_integer_count=post),(x[-1],))
    def test_count(self):
        with self.assertRaisesRegex(ValueError,'trial'):verify(self.logs(),caller_post_integers=True,integer_count=2,post_integer_count=2)
    def test_missing(self):
        with self.assertRaisesRegex(ValueError,'count'):verify(self.logs(),caller_post_integers=True,integer_count=2)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=832','total_visits=824')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,caller_post_integers=True,integer_count=2,post_integer_count=1)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(CallerSecondBranch().logs(),caller_post_integers=True,integer_count=2,post_integer_count=1)
    def test_mode(self):
        with self.assertRaisesRegex(ValueError,'mode'):verify(self.logs(),caller_second_branch=True,integer_count=2,post_integer_count=1)
class CallerThirdBranch(unittest.TestCase):
    def logs(self,count=2,post=1):
        return [f'FORMATTER_CALLER_THIRD_BRANCH_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=3 post_integers={post} fallthrough=2 taken=1 alternate_checks=3 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={102+count+post}' for i in range(8)]+[f'FORMATTER_CALLER_THIRD_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=24 post_integers={8*post} fallthrough=16 taken=8 alternate_checks=24 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={816+8*(count+post)} ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,caller_third_branch=True,integer_count=2,post_integer_count=1),(x[-1],))
    def test_alternate(self):
        x=self.logs();x[0]=x[0].replace('alternate_checks=3','alternate_checks=2')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,caller_third_branch=True,integer_count=2,post_integer_count=1)
    def test_count(self):
        with self.assertRaisesRegex(ValueError,'trial'):verify(self.logs(),caller_third_branch=True,integer_count=2,post_integer_count=2)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=840','total_visits=832')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,caller_third_branch=True,integer_count=2,post_integer_count=1)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(CallerPostIntegers().logs(),caller_third_branch=True,integer_count=2,post_integer_count=1)
class CallerFourthBranch(unittest.TestCase):
    def logs(self,count=2,post=1):
        return [f'FORMATTER_CALLER_FOURTH_BRANCH_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=4 post_integers={post} fallthrough=3 taken=1 alternate_checks=4 next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={103+count+post}' for i in range(8)]+[f'FORMATTER_CALLER_FOURTH_BRANCH_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=32 post_integers={8*post} fallthrough=24 taken=8 alternate_checks=32 next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={824+8*(count+post)} ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def test_exact(self):
        x=self.logs();self.assertEqual(verify(x,caller_fourth_branch=True,integer_count=2,post_integer_count=1),(x[-1],))
    def test_alternate(self):
        x=self.logs();x[0]=x[0].replace('alternate_checks=4','alternate_checks=3')
        with self.assertRaisesRegex(ValueError,'trial'):verify(x,caller_fourth_branch=True,integer_count=2,post_integer_count=1)
    def test_count(self):
        with self.assertRaisesRegex(ValueError,'trial'):verify(self.logs(),caller_fourth_branch=True,integer_count=2,post_integer_count=2)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=848','total_visits=840')
        with self.assertRaisesRegex(ValueError,'aggregate'):verify(x,caller_fourth_branch=True,integer_count=2,post_integer_count=1)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):verify(CallerThirdBranch().logs(),caller_fourth_branch=True,integer_count=2,post_integer_count=1)
class CallerMixed(unittest.TestCase):
    def logs(self,count=2,post=1,integers=2,taken=1,fallthrough=0):
        return [f'FORMATTER_CALLER_MIXED_TRIAL n={i} native_prefix=1 frame=48 loads=15 stores=17 nonvolatile=18 authenticated_loads=5 conditional_stack_load=1 caller_stores=4 parent_overlay=1 lr_restored=1 frame_release=1 original_return=1 caller_dispatch=1 caller_load=1 caller_byte_verified=1 caller_integers={count} caller_branches=4 post_integers={post} mixed_integers={integers} mixed_taken={taken} mixed_fallthrough={fallthrough} next_label_stop=1 deferred=1 reply=0 visits=98 total_visits={103+count+post+integers+taken+fallthrough}' for i in range(8)]+[f'FORMATTER_CALLER_MIXED_NATIVE owner=1 trials=8 native_prefix=8 loads=120 stores=136 nonvolatile=144 authenticated_loads=40 conditional_stack_loads=8 caller_stores=32 parent_overlay=8 lr_restored=8 frame_release=8 original_return=8 caller_dispatch=8 caller_loads=8 caller_bytes_verified=8 caller_integers={8*count} caller_branches=32 post_integers={8*post} mixed_integers={8*integers} mixed_taken={8*taken} mixed_fallthrough={8*fallthrough} next_label_stop=8 deferred=8 reply=0 visits=784 total_visits={824+8*(count+post+integers+taken+fallthrough)} ios_steps=5 fallback=0 complete_image=0 boot_verified=0']
    def probe(self,logs,integers=2,taken=1,fallthrough=0):
        return verify(logs,caller_mixed=True,integer_count=2,post_integer_count=1,mixed_integers=integers,mixed_taken=taken,mixed_fallthrough=fallthrough)
    def test_exact(self):
        for a,b,c in ((2,1,0),(0,0,1),(16,0,0),(0,8,8)):
            x=self.logs(integers=a,taken=b,fallthrough=c);self.assertEqual(self.probe(x,a,b,c),(x[-1],))
    def test_count(self):
        for counts in ((0,0,0),(16,1,0),(None,1,0),(True,1,0)):
            with self.assertRaisesRegex(ValueError,'mixed count'):self.probe(self.logs(),*counts)
    def test_outcome(self):
        with self.assertRaisesRegex(ValueError,'trial'):self.probe(self.logs(),2,0,1)
    def test_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=872','total_visits=848')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(x)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):self.probe(CallerFourthBranch().logs())
class CallerMixedByte(unittest.TestCase):
    def logs(self):
        rows=CallerMixed().logs(integers=2,taken=2,fallthrough=1)
        return [s.replace('FORMATTER_CALLER_MIXED_TRIAL','FORMATTER_CALLER_MIXED_BYTE_TRIAL').replace(' next_label_stop=1',' mixed_byte_verified=1 next_label_stop=1').replace('total_visits=111','total_visits=112') for s in rows[:-1]]+[rows[-1].replace('FORMATTER_CALLER_MIXED_NATIVE','FORMATTER_CALLER_MIXED_BYTE_NATIVE').replace(' next_label_stop=8',' mixed_bytes_verified=8 next_label_stop=8').replace('total_visits=888','total_visits=896')]
    def probe(self,rows,**kw):
        return verify(rows,caller_mixed_byte=True,integer_count=2,post_integer_count=1,mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)
    def test_exact(self):
        x=self.logs();self.assertEqual(self.probe(x),(x[-1],))
    def test_missing_load(self):
        x=self.logs();x[0]=x[0].replace(' mixed_byte_verified=1','')
        with self.assertRaisesRegex(ValueError,'trial'):self.probe(x)
    def test_old_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=896','total_visits=888')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(x)
    def test_missing_aggregate(self):
        x=self.logs();x[-1]=x[-1].replace(' mixed_bytes_verified=8','')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(x)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):self.probe(CallerMixed().logs(integers=2,taken=2,fallthrough=1))
    def test_modes(self):
        with self.assertRaisesRegex(ValueError,'mode'):self.probe(self.logs(),caller_mixed=True)
class CallerPostMixed(unittest.TestCase):
    def logs(self):
        rows=CallerMixedByte().logs()
        return [s.replace('FORMATTER_CALLER_MIXED_BYTE_TRIAL','FORMATTER_CALLER_POST_MIXED_TRIAL').replace(' next_label_stop=1',' post_mixed_integers=1 post_mixed_taken=1 post_mixed_fallthrough=0 next_label_stop=1').replace('total_visits=112','total_visits=114') for s in rows[:-1]]+[rows[-1].replace('FORMATTER_CALLER_MIXED_BYTE_NATIVE','FORMATTER_CALLER_POST_MIXED_NATIVE').replace(' next_label_stop=8',' post_mixed_integers=8 post_mixed_taken=8 post_mixed_fallthrough=0 next_label_stop=8').replace('total_visits=896','total_visits=912')]
    def probe(self,rows,**kw):
        return verify(rows,caller_post_mixed=True,integer_count=2,post_integer_count=1,mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)
    def test_exact(self):
        x=self.logs();self.assertEqual(self.probe(x),(x[-1],))
    def test_branch_outcome(self):
        x=self.logs();x[0]=x[0].replace('post_mixed_taken=1','post_mixed_taken=0')
        with self.assertRaisesRegex(ValueError,'trial'):self.probe(x)
    def test_old_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=912','total_visits=896')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(x)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):self.probe(CallerMixedByte().logs())
    def test_modes(self):
        with self.assertRaisesRegex(ValueError,'mode'):self.probe(self.logs(),caller_mixed_byte=True)
class CallerStackMove(unittest.TestCase):
    def logs(self):
        rows=CallerPostMixed().logs()
        return [s.replace('FORMATTER_CALLER_POST_MIXED_TRIAL','FORMATTER_CALLER_STACK_MOVE_TRIAL').replace(' next_label_stop=1',' stack_move_verified=1 next_label_stop=1').replace('total_visits=114','total_visits=115') for s in rows[:-1]]+[rows[-1].replace('FORMATTER_CALLER_POST_MIXED_NATIVE','FORMATTER_CALLER_STACK_MOVE_NATIVE').replace(' next_label_stop=8',' stack_moves_verified=8 next_label_stop=8').replace('total_visits=912','total_visits=920')]
    def probe(self,rows,**kw):
        return verify(rows,caller_stack_move=True,integer_count=2,post_integer_count=1,mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)
    def test_exact(self):
        x=self.logs();self.assertEqual(self.probe(x),(x[-1],))
    def test_missing_copy(self):
        x=self.logs();x[0]=x[0].replace('stack_move_verified=1','stack_move_verified=0')
        with self.assertRaisesRegex(ValueError,'trial'):self.probe(x)
    def test_old_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=920','total_visits=912')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(x)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):self.probe(CallerPostMixed().logs())
    def test_modes(self):
        with self.assertRaisesRegex(ValueError,'mode'):self.probe(self.logs(),caller_post_mixed=True)
class CallerFinalInteger(unittest.TestCase):
    def logs(self):
        rows=CallerStackMove().logs()
        return [s.replace('FORMATTER_CALLER_STACK_MOVE_TRIAL','FORMATTER_CALLER_FINAL_INTEGER_TRIAL').replace(' next_label_stop=1',' final_integer_verified=1 next_label_stop=1').replace('total_visits=115','total_visits=116') for s in rows[:-1]]+[rows[-1].replace('FORMATTER_CALLER_STACK_MOVE_NATIVE','FORMATTER_CALLER_FINAL_INTEGER_NATIVE').replace(' next_label_stop=8',' final_integers_verified=8 next_label_stop=8').replace('total_visits=920','total_visits=928')]
    def probe(self,rows,**kw):
        return verify(rows,caller_final_integer=True,integer_count=2,post_integer_count=1,mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)
    def test_exact(self):
        x=self.logs();self.assertEqual(self.probe(x),(x[-1],))
    def test_missing_integer(self):
        x=self.logs();x[0]=x[0].replace('final_integer_verified=1','final_integer_verified=0')
        with self.assertRaisesRegex(ValueError,'trial'):self.probe(x)
    def test_old_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=928','total_visits=920')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(x)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):self.probe(CallerStackMove().logs())
    def test_modes(self):
        with self.assertRaisesRegex(ValueError,'mode'):self.probe(self.logs(),caller_stack_move=True)
class CallerNextEntry(unittest.TestCase):
    def logs(self):
        rows=CallerFinalInteger().logs()
        return [s.replace('FORMATTER_CALLER_FINAL_INTEGER_TRIAL','FORMATTER_CALLER_NEXT_ENTRY_TRIAL').replace(' next_label_stop=1',' next_entry_verified=1 callee_load_executed=0 next_label_stop=1').replace('total_visits=116','total_visits=117') for s in rows[:-1]]+[rows[-1].replace('FORMATTER_CALLER_FINAL_INTEGER_NATIVE','FORMATTER_CALLER_NEXT_ENTRY_NATIVE').replace(' next_label_stop=8',' next_entries_verified=8 callee_loads_executed=0 next_label_stop=8').replace('total_visits=928','total_visits=936')]
    def probe(self,rows,**kw):
        return verify(rows,caller_next_entry=True,integer_count=2,post_integer_count=1,mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)
    def test_exact(self):
        x=self.logs();self.assertEqual(self.probe(x),(x[-1],))
    def test_executed_load(self):
        x=self.logs();x[0]=x[0].replace('callee_load_executed=0','callee_load_executed=1')
        with self.assertRaisesRegex(ValueError,'trial'):self.probe(x)
    def test_old_total(self):
        x=self.logs();x[-1]=x[-1].replace('total_visits=936','total_visits=928')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(x)
    def test_prior(self):
        with self.assertRaisesRegex(ValueError,'coverage'):self.probe(CallerFinalInteger().logs())
    def test_modes(self):
        with self.assertRaisesRegex(ValueError,'mode'):self.probe(self.logs(),caller_final_integer=True)
class CallerReportByte(unittest.TestCase):
    def logs(self):
        rows=CallerNextEntry().logs()
        return [s.replace('FORMATTER_CALLER_NEXT_ENTRY_TRIAL','FORMATTER_CALLER_REPORT_BYTE_TRIAL')
                 .replace('callee_load_executed=0','callee_load_executed=1 report_byte_verified=1')
                 .replace('total_visits=117','total_visits=118') for s in rows[:-1]]+[
            rows[-1].replace('FORMATTER_CALLER_NEXT_ENTRY_NATIVE','FORMATTER_CALLER_REPORT_BYTE_NATIVE')
            .replace('callee_loads_executed=0','callee_loads_executed=8 report_bytes_verified=8')
            .replace('total_visits=936','total_visits=944')]
    def probe(self,rows,**kw):
        return verify(rows,caller_report_byte=True,integer_count=2,post_integer_count=1,
                      mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)
    def test_exact(self):
        rows=self.logs();self.assertEqual(self.probe(rows),(rows[-1],))
    def test_prior_entry_not_load(self):
        with self.assertRaisesRegex(ValueError,'coverage'):self.probe(CallerNextEntry().logs())
    def test_missing_byte(self):
        rows=self.logs();rows[0]=rows[0].replace('report_byte_verified=1','report_byte_verified=0')
        with self.assertRaisesRegex(ValueError,'trial'):self.probe(rows)
    def test_aggregate_count(self):
        rows=self.logs();rows[-1]=rows[-1].replace('report_bytes_verified=8','report_bytes_verified=7')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(rows)
    def test_prior_total(self):
        rows=self.logs();rows[-1]=rows[-1].replace('total_visits=944','total_visits=936')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(rows)
    def test_modes(self):
        with self.assertRaisesRegex(ValueError,'mode'):self.probe(self.logs(),caller_next_entry=True)
class CallerReportCompare(unittest.TestCase):
    def logs(self):
        rows=CallerReportByte().logs()
        return [line.replace('FORMATTER_CALLER_REPORT_BYTE_TRIAL','FORMATTER_CALLER_REPORT_COMPARE_TRIAL')
                    .replace(' report_byte_verified=1',' report_byte_verified=1 compare_verified=1')
                    .replace('total_visits=118','total_visits=119') for line in rows[:-1]]+[
            rows[-1].replace('FORMATTER_CALLER_REPORT_BYTE_NATIVE','FORMATTER_CALLER_REPORT_COMPARE_NATIVE')
                .replace(' report_bytes_verified=8',' report_bytes_verified=8 compares_verified=8')
                .replace('total_visits=944','total_visits=952')]
    def probe(self,rows,**kw):
        return verify(rows,caller_report_compare=True,integer_count=2,post_integer_count=1,
                      mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)
    def test_exact(self):
        rows=self.logs()
        self.assertEqual(self.probe(rows),(rows[-1],))
    def test_missing_compare(self):
        rows=self.logs()
        rows[0]=rows[0].replace('compare_verified=1','compare_verified=0')
        with self.assertRaisesRegex(ValueError,'trial'):self.probe(rows)
    def test_aggregate_compare(self):
        rows=self.logs()
        rows[-1]=rows[-1].replace('compares_verified=8','compares_verified=7')
        with self.assertRaisesRegex(ValueError,'aggregate'):self.probe(rows)
    def test_old_118_rejected(self):
        with self.assertRaisesRegex(ValueError,'coverage'):
            self.probe(CallerReportByte().logs())
    def test_mode_conflict(self):
        with self.assertRaisesRegex(ValueError,'mode'):
            self.probe(self.logs(),caller_report_byte=True)
    def test_trial_accounting_and_duplicate(self):
        rows=self.logs()
        with self.assertRaisesRegex(ValueError,'coverage'):
            self.probe(rows[1:])
        duplicate=rows[:]
        duplicate.insert(1,rows[0])
        with self.assertRaisesRegex(ValueError,'trial'):
            self.probe(duplicate)
    def test_native_aggregate_required(self):
        rows=self.logs()
        with self.assertRaisesRegex(ValueError,'coverage'):
            self.probe(rows[:-1])
    def test_no_synthetic_fallback_claim(self):
        rows=self.logs()
        rows[-1]=rows[-1].replace('fallback=0','fallback=1')
        with self.assertRaisesRegex(ValueError,'aggregate'):
            self.probe(rows)
    def test_incomplete_guard_or_corrupted_visit(self):
        rows=self.logs()
        rows[0]=rows[0].replace('next_label_stop=1','next_label_stop=0')
        with self.assertRaisesRegex(ValueError,'trial'):
            self.probe(rows)
        rows=self.logs()
        rows[-1]=rows[-1].replace('total_visits=952','total_visits=944')
        with self.assertRaisesRegex(ValueError,'aggregate'):
            self.probe(rows)

class CallerReportCopy(unittest.TestCase):
    def logs(self):
        rows=CallerReportCompare().logs()
        return [line.replace('FORMATTER_CALLER_REPORT_COMPARE_TRIAL',
                             'FORMATTER_CALLER_REPORT_COPY_TRIAL')
                    .replace(' compare_verified=1',
                             ' compare_verified=1 copy_verified=1')
                    .replace('total_visits=119','total_visits=120') for line in rows[:-1]]+[
            rows[-1].replace('FORMATTER_CALLER_REPORT_COMPARE_NATIVE',
                             'FORMATTER_CALLER_REPORT_COPY_NATIVE')
                .replace(' compares_verified=8',
                         ' compares_verified=8 copies_verified=8')
                .replace('total_visits=952','total_visits=960')]

    def probe(self,rows,**kw):
        return verify(rows,caller_report_copy=True,integer_count=2,post_integer_count=1,
                      mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)

    def test_exact(self):
        rows=self.logs()
        self.assertEqual(self.probe(rows),(rows[-1],))

    def test_old_119_rejected(self):
        with self.assertRaisesRegex(ValueError,'coverage'):
            self.probe(CallerReportCompare().logs())

    def test_missing_copy(self):
        rows=self.logs()
        rows[0]=rows[0].replace('copy_verified=1','copy_verified=0')
        with self.assertRaisesRegex(ValueError,'trial'):
            self.probe(rows)

    def test_missing_native_visit(self):
        rows=self.logs()
        rows[-1]=rows[-1].replace('copies_verified=8','copies_verified=7')
        with self.assertRaisesRegex(ValueError,'aggregate'):
            self.probe(rows)

    def test_guard_and_fallback_refusals(self):
        for old,new in (('next_label_stop=1','next_label_stop=0'),
                        ('copy_verified=1','copy_verified=0')):
            rows=self.logs()
            rows[0]=rows[0].replace(old,new)
            with self.assertRaisesRegex(ValueError,'trial'):
                self.probe(rows)
        rows=self.logs()
        rows[-1]=rows[-1].replace('fallback=0','fallback=1')
        with self.assertRaisesRegex(ValueError,'aggregate'):
            self.probe(rows)

    def test_conflicting_modes(self):
        with self.assertRaisesRegex(ValueError,'mode'):
            self.probe(self.logs(),caller_report_compare=True)


class CallerReportImmediate(unittest.TestCase):
    def logs(self):
        rows=CallerReportCopy().logs()
        return [line.replace('FORMATTER_CALLER_REPORT_COPY_TRIAL',
                             'FORMATTER_CALLER_REPORT_IMMEDIATE_TRIAL')
                    .replace(' copy_verified=1',
                             ' copy_verified=1 immediate_verified=1')
                    .replace('total_visits=120','total_visits=121')
                for line in rows[:-1]]+[
            rows[-1].replace('FORMATTER_CALLER_REPORT_COPY_NATIVE',
                             'FORMATTER_CALLER_REPORT_IMMEDIATE_NATIVE')
                .replace(' copies_verified=8',
                         ' copies_verified=8 immediates_verified=8')
                .replace('total_visits=960','total_visits=968')]

    def probe(self,rows,**kw):
        return verify(rows,caller_report_immediate=True,
                      integer_count=2,post_integer_count=1,
                      mixed_integers=2,mixed_taken=2,mixed_fallthrough=1,**kw)

    def test_exact(self):
        rows=self.logs()
        self.assertEqual(self.probe(rows),(rows[-1],))

    def test_missing_121_or_120(self):
        with self.assertRaisesRegex(ValueError,'coverage'):
            self.probe(CallerReportCopy().logs())
        rows=self.logs()
        rows[1]=rows[1].replace(' immediate_verified=1','')
        with self.assertRaisesRegex(ValueError,'trial'):
            self.probe(rows)

    def test_corrupted_121_result(self):
        for old,new in (('immediate_verified=1','immediate_verified=0'),
                        ('copy_verified=1','copy_verified=0'),
                        ('next_label_stop=1','next_label_stop=0'),
                        ('total_visits=121','total_visits=120')):
            rows=self.logs()
            rows[0]=rows[0].replace(old,new)
            with self.subTest(old=old):
                with self.assertRaisesRegex(ValueError,'trial'):
                    self.probe(rows)

    def test_aggregate_and_fallback(self):
        for old,new in (('immediates_verified=8','immediates_verified=7'),
                        ('total_visits=968','total_visits=960'),
                        ('fallback=0','fallback=1')):
            rows=self.logs()
            rows[-1]=rows[-1].replace(old,new)
            with self.subTest(old=old):
                with self.assertRaisesRegex(ValueError,'aggregate'):
                    self.probe(rows)

    def test_mode_conflict_and_coverage(self):
        with self.assertRaisesRegex(ValueError,'mode'):
            self.probe(self.logs(),caller_report_copy=True)
        with self.assertRaisesRegex(ValueError,'coverage'):
            self.probe(self.logs()[:-1])

if __name__=='__main__':unittest.main(verbosity=2)
