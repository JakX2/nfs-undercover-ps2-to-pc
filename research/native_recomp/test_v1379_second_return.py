import unittest
from prepare_v1379_second_return import extend,scope,STM,BLR
class Tests(unittest.TestCase):
    def test_extend(self):
        old=tuple(range(33));body=tuple(range(70))
        self.assertEqual(extend({STM:old+(BLR,)},old,body)[STM],body[:34]+(BLR,))
        self.assertEqual(dict(scope({STM:96}))[STM],140)
    def test_refusals(self):
        old=tuple(range(33));body=tuple(range(70))
        for blocks,prefix,full in [({STM:old},old,body),({STM:old+(BLR,)},old,body[:34]),({STM:old+(BLR,)},old,(99,)+body[1:]),({STM:old+(BLR,),STM+136:(0,)},old,body)]:
            with self.assertRaises(ValueError):extend(blocks,prefix,full)
        for prior in ({STM:136},{STM+136:4}):
            with self.assertRaises(ValueError):scope(prior)
if __name__=='__main__':unittest.main()
