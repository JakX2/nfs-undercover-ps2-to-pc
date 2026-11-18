from apply_mtmsr_resume_v74 import OLD,NEW,rewrite
if __name__=="__main__":
    src=OLD+"\n"+OLD
    assert rewrite(src)==NEW+"\n"+NEW
    assert rewrite(rewrite(src))==rewrite(src)
    for bad in (OLD,NEW+"\n"+OLD,src+"\n"+OLD,""):
        try:rewrite(bad)
        except ValueError:continue
        raise AssertionError("unsafe partial resume patch accepted")
    print("PASS: dual dispatcher resume patch guards")
