#!/usr/bin/env python3
"""Synthetic field encodings and idempotent patch guards; no game data."""
from apply_jump_table_v58 import OLD_SPR,NEW_SPR,OLD_BCTR,NEW_BCTR,OLD_ROOTS,NEW_ROOTS,OLD_PARAM,NEW_PARAM,rewrite

def rejects(s):
    try:rewrite(s)
    except ValueError:return
    raise AssertionError("unexpected patch accepted")
def spr_field(spr):
    return ((spr&31)<<5)|(spr>>5)
def decode(word):
    field=(word>>11)&1023
    return ((field&31)<<5)|(field>>5)

if __name__=="__main__":
    for spr in range(1024):
        ins=(31<<26)|(7<<21)|(spr_field(spr)<<11)|(467<<1)
        assert decode(ins)==spr
    bctr=(19<<26)|(20<<21)|(528<<1)
    assert ((bctr>>1)&1023)==528 and (bctr&1023)!=528
    old="\n".join((OLD_SPR,OLD_BCTR,OLD_ROOTS,OLD_PARAM))
    new="\n".join((NEW_SPR,NEW_BCTR,NEW_ROOTS,NEW_PARAM))
    assert rewrite(old)==new and rewrite(new)==new
    rejects(OLD_SPR);rejects(OLD_BCTR);rejects(old+"\n"+OLD_BCTR)
    print("PASS: all 1024 PPC SPR encodings and jump-table patch fail-closed guards")
