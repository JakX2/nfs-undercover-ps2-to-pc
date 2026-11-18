from apply_dcbz_v67 import OLD_CTX,NEW_CTX,OLD_EMIT,NEW_EMIT,OLD_INCLUDE,NEW_INCLUDE,rewrite
if __name__=="__main__":
    c=OLD_INCLUDE+"\n"+OLD_CTX;nc=NEW_INCLUDE+"\n"+NEW_CTX
    assert rewrite(c,OLD_EMIT)==(nc,NEW_EMIT,False)
    assert rewrite(nc,NEW_EMIT)==(nc,NEW_EMIT,True)
    for a,b in ((c,NEW_EMIT),(nc,OLD_EMIT),("",OLD_EMIT),(c,OLD_EMIT*2)):
        try:rewrite(a,b)
        except ValueError:continue
        raise AssertionError("invalid mixed dcbz patch accepted")
    print("PASS: dcbz patch idempotency and fail-closed guards")
