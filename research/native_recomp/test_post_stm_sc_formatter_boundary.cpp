#include "wii_post_stm_sc_formatter.h"
#include <cassert>
#include <iostream>
using namespace undercover::wii;
constexpr uint32_t B=0x80000000u,R=B+0x100u,L=B+0x400u,A=B+0x500u,SP=B+0xc00u;
constexpr uint32_t ins(unsigned op,unsigned r,unsigned a,int n){return (op<<26)|(r<<21)|(a<<16)|(uint32_t(n)&0xffffu);}
struct Mem{
    std::array<uint8_t,4096> ram{};unsigned data_reads=0;
    uint8_t* get_ptr(uint32_t a){return a>=B&&a-B<ram.size()?ram.data()+a-B:nullptr;}
    uint8_t read8(uint32_t a){if(a>=A&&a<A+4)++data_reads;auto p=get_ptr(a);assert(p);return *p;}
    uint32_t read32(uint32_t a){uint32_t v=0;for(unsigned i=0;i<4;++i)v=(v<<8)|read8(a+i);return v;}
    void write32(uint32_t a,uint32_t v){for(unsigned i=0;i<4;++i)*get_ptr(a+i)=uint8_t(v>>(24-8*i));}
};
struct Cr{bool lt=false,gt=false,eq=false,so=false;};
struct Cpu{
    Mem mmu;std::array<uint32_t,32> gpr{};std::array<uint32_t,8> gqr{};std::array<Cr,8> cr{};
    uint32_t pc=R,lr=L,ctr=0,xer=0,msr=0x8032,srr0=R,srr1=0x8032,dispatch_saved_ctx=0;
    uint64_t inst_count=100;bool is_running=true,in_callback=false;
};
static void trial(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.gpr[31]=0x1234;
    c.mmu.write32(A,0xdeadbeefu);
    constexpr uint32_t target=R+16,load=ins(32,4,3,0);
    const std::array<IpcDispatchWord,4> path{{{R,R,ins(37,1,1,-48)},{R,R+4,0x7c0802a6},
        {R,R+8,ins(36,0,1,52)},{R,R+12,ins(36,31,1,44)}}};
    const std::array<ScFormatterAccess,3> access{{{R,4,-48,true,true},{R+8,4,4,true,true},{R+12,4,-4,true,true}}};
    const std::array<StmFinalSlot,2> slots{{{4,32},{-4,31}}};
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(target,load);
    ScFormatterWitness w({R,L,target,load,48,path,access,slots,{fault==1?A+1:fault==2?A+4:A,fault==3?2u:4u}});
    bool ok=w.begin(c,true);
    if(fault==1||fault==3){assert(!ok);return;}assert(ok);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    for(auto x:path){
        ++c.inst_count;assert(w.before(c,x.pc,x.word,true));
        if(x.pc==R){c.gpr[1]=SP-48;c.mmu.write32(SP-48,SP);}
        if(x.pc==R+4)c.gpr[0]=L;
        if(x.pc==R+8)c.mmu.write32(SP+4,L);
        if(x.pc==R+12)c.mmu.write32(SP-4,c.gpr[31]);
    }
    if(fault==4)c.mmu.write32(SP-4,0);
    if(fault==5)c.gpr[4]=0xdeadbeefu;
    if(fault==6)c.mmu.write32(target,ins(34,4,3,0));
    if(fault!=7)++c.inst_count;
    ok=w.stop_before_load(c,target,load,fault!=8);
    if(fault){assert(!ok);return;}
    assert(ok&&w.reached_load_boundary(c,true)&&!w.reached(c,true));
    assert(w.visits()==4&&w.stores()==3&&w.loads()==0&&w.authenticated_loads()==0&&c.gpr[4]==0&&c.mmu.data_reads==0);
    ++c.inst_count;assert(!w.reached_load_boundary(c,true));
}
static void many_accesses(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.gpr[5]=0x55;c.mmu.write32(A+8,0x12345678);
    std::vector<IpcDispatchWord> path{{R,R,ins(37,1,1,-48)},{R,R+4,0x7c0802a6},{R,R+8,ins(36,0,1,52)}};
    std::vector<ScFormatterAccess> access{{R,4,-48,true,true},{R+8,4,4,true,true}};
    for(unsigned i=0;i<10;++i){
        const auto pc=R+12+i*4;path.push_back({R,pc,ins(38,5,1,8+i)});
        access.push_back({pc,1,int64_t(i)-40,true,true});
    }
    const auto rd=R+52,target=R+60;
    path.push_back({R,rd,ins(32,6,3,8)});
    path.push_back({R,rd+4,ins(32,7,3,12)});
    access.push_back({rd,4,A+8,false,false,fault==1?0u:0x12345678u});
    access.push_back({rd+4,4,A+12,false,false,fault==3?1u:0u});
    if(fault==2)access.back().write=true;
    if(fault==4)access.back().expected_value.reset();
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    const auto load=ins(32,4,3,0);c.mmu.write32(target,load);
    const std::array<StmFinalSlot,1> slots{{{4,32}}};
    ScFormatterWitness w({R,L,target,load,48,path,access,slots,{A,4}});
    const bool started=w.begin(c,true);
    if(fault==2){assert(!started);return;}assert(started);
    assert(w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    for(auto x:path){
        ++c.inst_count;const bool ok=w.before(c,x.pc,x.word,true);
        if(fault==1&&x.pc==rd){assert(!ok&&w.authenticated_loads()==0);return;}
        if(fault==3&&x.pc==rd+4){assert(!ok&&w.authenticated_loads()==1);return;}assert(ok);
        if(x.pc==R){c.gpr[1]=SP-48;c.mmu.write32(SP-48,SP);}
        else if(x.pc==R+4)c.gpr[0]=L;
        else if(x.pc==R+8)c.mmu.write32(SP+4,L);
        else if(x.pc==rd)c.gpr[6]=0x12345678;
        else if(x.pc==rd+4)c.gpr[7]=0;
        else *c.mmu.get_ptr(SP-40+(x.pc-R-12)/4)=0x55;
    }
    ++c.inst_count;
    assert(w.stop_before_load(c,target,load,true)&&w.reached_load_boundary(c,true));
    assert(w.loads()==2&&w.authenticated_loads()==(fault==4?1u:2u)&&w.stores()==12&&c.mmu.data_reads==0);
}
constexpr uint32_t xload(unsigned xo,unsigned rt,unsigned ra,unsigned rb,unsigned rc=0){return (31u<<26)|(rt<<21)|(ra<<16)|(rb<<11)|(xo<<1)|rc;}
static void indexed(unsigned xo,unsigned n,uint32_t value,unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A+4;c.gpr[5]=uint32_t(-4);c.gpr[8]=A+16;
    c.mmu.write32(A,0x81ff1234u);
    const auto rd=R+12,target=R+16;
    const auto word=xload(xo,4,3,5),stop=xload(23,7,0,8);
    const std::array<IpcDispatchWord,4> path{{{R,R,ins(37,1,1,-48)},{R,R+4,0x7c0802a6},
        {R,R+8,ins(36,0,1,52)},{R,rd,word}}};
    const uint32_t raw=n==4?0x81ff1234u:n==2?0x81ffu:0x81u;
    const std::array<ScFormatterAccess,3> access{{{R,4,-48,true,true},{R+8,4,4,true,true},
        {rd,n,fault==1?A+4:A,false,false,fault==2?raw^1u:raw}}};
    const std::array<StmFinalSlot,1> slots{{{4,32}}};
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(target,stop);
    ScFormatterWitness w({R,L,target,stop,48,path,access,slots,{fault==3?A+20:A+16,4}});
    assert(w.begin(c,true)&&w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    for(auto x:path){
        ++c.inst_count;const bool ok=w.before(c,x.pc,x.word,true);
        if(x.pc==rd&&(fault==1||fault==2)){assert(!ok&&w.authenticated_loads()==0);return;}
        assert(ok);
        if(x.pc==R){c.gpr[1]=SP-48;c.mmu.write32(SP-48,SP);}
        else if(x.pc==R+4)c.gpr[0]=L;
        else if(x.pc==R+8)c.mmu.write32(SP+4,L);
        else {c.gpr[4]=fault==4?value^1u:value;if(xo==55||xo==119||xo==311||xo==375)c.gpr[3]=A;}
    }
    ++c.inst_count;const bool ok=w.stop_before_load(c,target,stop,true);
    if(fault>=3){assert(!ok);return;}
    assert(ok&&w.reached_load_boundary(c,true)&&w.authenticated_loads()==1&&w.loads()==1&&c.gpr[7]==0);
}
static void long_prefix(unsigned count,unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;
    std::vector<IpcDispatchWord> path{{R,R,ins(37,1,1,-48)},{R,R+4,0x7c0802a6},{R,R+8,ins(36,0,1,52)}};
    const std::array<ScFormatterAccess,2> accesses{{{R,4,-48,true,true},{R+8,4,4,true,true}}};
    const std::array<StmFinalSlot,1> slots{{{4,32}}};
    for(unsigned i=3;i<count;++i)path.push_back({R,R+4*i,ins(14,6,6,1)});
    const auto target=R+4*count,load=ins(32,7,3,0);
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(target,load);
    ScFormatterWitness w({R,L,target,load,48,path,accesses,slots,fault==1?ScFormatterBoundary{}:ScFormatterBoundary{A,4}});
    const bool ok=w.begin(c,true);
    if(count>128||fault==1){assert(!ok);return;}
    assert(ok&&w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    for(auto x:path){
        ++c.inst_count;assert(w.before(c,x.pc,x.word,true));
        if(x.pc==R){c.gpr[1]=SP-48;c.mmu.write32(SP-48,SP);}
        else if(x.pc==R+4)c.gpr[0]=L;
        else if(x.pc==R+8)c.mmu.write32(SP+4,L);
        else ++c.gpr[6];
    }
    if(fault==2)++c.gpr[6];
    ++c.inst_count;const bool stopped=w.stop_before_load(c,target,load,true);
    if(fault==2){assert(!stopped);return;}
    assert(stopped&&w.reached_load_boundary(c,true)&&w.visits()==count&&c.gpr[6]==count-3&&c.mmu.data_reads==0);
}
// Model the third contract's exact access census with original-free words.
// Every completed load is compared by the next hook; the final load is not read.
static void mixed_third(unsigned fault){
    Cpu c;c.gpr[1]=SP;c.gpr[3]=A;c.gpr[5]=0x55;c.gpr[14]=0x14;c.gpr[15]=0x15;c.gpr[16]=0x16;
    std::vector<IpcDispatchWord> path;std::vector<ScFormatterAccess> access;
    auto emit=[&](uint32_t w){const auto pc=R+4u*uint32_t(path.size());path.push_back({R,pc,w});return pc;};
    auto store=[&](unsigned op,unsigned reg,int off,unsigned n){
        const auto pc=emit(ins(op,reg,1,off));access.push_back({pc,n,off-48,true,true});
    };
    store(37,1,-48,4);access.back().address=-48;
    emit(0x7c0802a6);store(36,0,52,4);
    store(36,14,44,4);store(36,15,40,4);store(36,16,36,4);
    for(unsigned i=0;i<8;++i)store(38,5,8+int(i),1);
    const auto stack_pc=emit(ins(32,7,1,8));access.push_back({stack_pc,4,-40,true,false});
    std::array<uint32_t,4> read_pc{};
    for(unsigned i=0;i<4;++i){
        c.mmu.write32(A+8+4*i,0x10203040u+i);
        read_pc[i]=emit(ins(32,8,3,8+4*int(i)));
        access.push_back({read_pc[i],4,A+8+4*i,false,false,0x10203040u+i});
    }
    while(path.size()<74u)emit(ins(14,6,6,1));
    const auto target=R+4u*uint32_t(path.size()),load=ins(32,9,3,0);
    for(auto x:path)c.mmu.write32(x.pc,x.word);
    c.mmu.write32(target,load);
    const std::array<StmFinalSlot,4> slots{{{4,32},{-4,14},{-8,15},{-12,16}}};
    ScFormatterWitness w({R,L,target,load,48,path,access,slots,{A,4}});
    assert(w.begin(c,true)&&w.poll(c,true));++c.inst_count;assert(w.entry(c,R,true));
    for(auto x:path){
        if(fault==1&&x.pc==stack_pc)*c.mmu.get_ptr(SP-40)=0x66;
        if(fault==2&&x.pc==read_pc[2])c.mmu.write32(A+16,0);
        ++c.inst_count;const bool ok=w.before(c,x.pc,x.word,true);
        if((fault==1&&x.pc==stack_pc)||(fault==2&&x.pc==read_pc[2])){assert(!ok);return;}
        if(fault==3&&x.pc==read_pc[1]){assert(!ok);return;}
        assert(ok);
        const unsigned op=x.word>>26,rt=(x.word>>21)&31;
        const int off=int((x.word&0xffffu)^0x8000u)-0x8000;
        if(x.pc==R){c.gpr[1]=SP-48;c.mmu.write32(SP-48,SP);}
        else if(x.word==0x7c0802a6)c.gpr[0]=L;
        else if(op==36)c.mmu.write32(c.gpr[1]+uint32_t(off),c.gpr[rt]);
        else if(op==38)*c.mmu.get_ptr(c.gpr[1]+uint32_t(off))=uint8_t(c.gpr[rt]);
        else if(x.pc==stack_pc)c.gpr[7]=c.mmu.read32(SP-40);
        else if(op==32){
            c.gpr[8]=c.mmu.read32(A+uint32_t(off));
            if(fault==3&&x.pc==read_pc[0])c.gpr[8]^=1u;
        }else ++c.gpr[6];
    }
    if(fault==4)c.mmu.write32(SP-4,0);
    ++c.inst_count;const bool stopped=w.stop_before_load(c,target,load,true);
    if(fault==4){assert(!stopped);return;}
    assert(stopped&&w.reached_load_boundary(c,true)&&w.visits()==74&&w.loads()==5&&
           w.stores()==13&&w.authenticated_loads()==4&&c.gpr[7]==0x55555555u&&c.gpr[9]==0&&c.mmu.data_reads==0);
}
int main(){for(unsigned i=0;i<=8;++i)trial(i);for(unsigned i=0;i<=4;++i)many_accesses(i);
    for(auto xo:{23u,55u,87u,119u,279u,311u,343u,375u}){
        const unsigned n=xo<=55?4:xo<=119?1:2;
        const uint32_t v=n==4?0x81ff1234u:n==1?0x81u:xo>=343?0xffff81ffu:0x81ffu;
        indexed(xo,n,v,0);
    }
    for(unsigned i=1;i<=4;++i)indexed(23,4,0x81ff1234u,i);
    long_prefix(74,0);long_prefix(128,0);long_prefix(129,0);long_prefix(74,1);long_prefix(74,2);
    for(unsigned i=0;i<=4;++i)mixed_third(i);
    std::cout<<"FORMATTER_BOUNDARY_TEST cases=36 original_execution=0\n";}
