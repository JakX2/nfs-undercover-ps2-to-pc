from apply_native_lowmem_v63 import OLD_H,NEW_H,OLD_E,NEW_E,rewrite
if __name__=="__main__":
    assert rewrite(OLD_H,OLD_E)==(NEW_H,NEW_E)
    assert rewrite(NEW_H,NEW_E)==(NEW_H,NEW_E)
    for h,e in ((NEW_H,OLD_E),(OLD_H,NEW_E),("",OLD_E),(OLD_H,OLD_E+OLD_E)):
        try:rewrite(h,e)
        except ValueError:continue
        raise AssertionError("unsafe low-memory opt-in patch accepted")
    print("PASS: low-memory opt-in guarded and idempotent")
