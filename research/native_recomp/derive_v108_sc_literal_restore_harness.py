#!/usr/bin/env python3
"""V108 restore precisely authenticated original SC initialized data at its actual guest pointer."""
import argparse
from pathlib import Path
from derive_v107_sc_source_probe_harness import derive as previous
EDITS = [(
    '                  <<" original_literal="<<owner_match<<std::endl;\n         }',
    '''                  <<" original_literal="<<owner_match<<std::endl;
         const bool span=open71_ram(s,unsigned(public_sc.size()+1u));
         std::cout<<"V108_SC_GATE owner="<<owner_match<<" empty="<<guest_empty
                  <<" span="<<span<<std::endl;
         check(owner_match&&guest_empty&&span,
               "V108 SC literal provenance is not an omitted initialized data span");
         check(seed_stm_data(ctx,s,unsigned(public_sc.size()+1u)),
               "V108 SC authenticated original data restoration failed");
         bool exact=true;
         for(unsigned i=0;i<public_sc.size();++i)
           exact&=ctx.mmu.read8(s+i)==uint8_t(public_sc[i]);
         exact&=ctx.mmu.read8(s+public_sc.size())==0u;
         std::cout<<"V108_SC_RESTORE owner="<<owner_match<<" empty_before="<<guest_empty
                  <<" exact="<<exact<<std::endl;
         check(exact,"V108 restored initialized SC bytes differ from owner literal");
         }'''
)]
def derive(source):
    source=previous(source)
    for old,new in EDITS:
        if source.count(old)!=1:raise ValueError("V108 original SC input provenance anchor missing")
        source=source.replace(old,new,1)
    return source

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("source",type=Path);p.add_argument("output",type=Path)
    a=p.parse_args()
    with a.output.open("x",encoding="utf-8") as out:
        out.write(derive(a.source.read_text(encoding="utf-8")))
if __name__=="__main__":main()
