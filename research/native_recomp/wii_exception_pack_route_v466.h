#pragma once
#include "wii_exception_pack_v462.h"
#include "wii_exception_vector_witness_v457.h"

namespace undercover::wii {
struct ExceptionPackRouteExpectations {
    ExceptionPackExpectations image;
    std::array<VectorEdge,32> exception_edges,syscall_edges;
    unsigned exception_count,syscall_count;
    VectorEdge syscall_entry,alarm_entry;
    uint32_t vector_return_word;
};
class ExceptionPackRoute {
public:
    explicit ExceptionPackRoute(const ExceptionPackRouteExpectations& e):e_(e),pack_(e.image){}
    unsigned phase()const{return pack_.phase();}
    unsigned failure()const{return error_?error_:pack_.failure();}
    unsigned vectors()const{return vectors_;}
    unsigned calls()const{return calls_;}
    template<class Cpu> bool begin(Cpu& c){
        if(e_.exception_count==0||e_.exception_count>e_.exception_edges.size()||
           e_.syscall_count==0||e_.syscall_count>e_.syscall_edges.size())return fail(11);
        if(!pack_.begin(c))return false;
        last_=c.inst_count;return true;
    }
    template<class Cpu> bool first_copy(Cpu& c){
        if(!valid(c,0x80004338u)||!edge(c,e_.exception_edges,e_.exception_count))return fail(12);
        if(!pack_.first_copy(c))return false;
        index_=0;step_=1;last_=c.inst_count;return true;
    }
    // Called only for the next three already-authenticated V457 events.
    template<class Cpu> bool first_vector_event(uint32_t addr,Cpu& c,unsigned stage){
        if(pack_.phase()!=2||stage!=step_+1||stage<2||stage>4)return fail(12);
        return vector_event(addr,c);
    }
    template<class Cpu> bool observe(uint32_t addr,Cpu& c){
        if(error_||pack_.failure()||!valid(c,addr)||++calls_>128)return fail(13);
        if(pack_.phase()==2){
            if(addr==0x805290c8u){
                if(vectors_!=15||step_!=0||!matches(c,e_.syscall_entry))return fail(14);
                if(!pack_.syscall_entry(c))return false;
            }else if(addr==0x80004338u&&c.lr==0x80520d9cu){
                if(vectors_>=15||step_!=0||c.gpr[29]!=vectors_||!edge(c,e_.exception_edges,e_.exception_count)||
                   c.gpr[3]!=0x80000000u+e_.image.offsets[vectors_]||c.gpr[4]!=0x80520ec0u||c.gpr[5]!=152u)return fail(15);
                index_=vectors_;step_=1;
            }else if(addr==0x80522320u||addr==0x80522378u||addr==0x80520db8u){
                return vector_event(addr,c);
            }else if(step_||!edge(c,e_.exception_edges,e_.exception_count))return fail(16);
        }else if(pack_.phase()==3){
            if(addr==0x805210ccu){
                if(sys_step_!=3||!matches(c,e_.alarm_entry))return fail(17);
                if(!pack_.alarm_entry(c))return false;
            }else{
                if(!edge(c,e_.syscall_edges,e_.syscall_count))return fail(17);
                if(sys_step_==0&&addr==0x80004338u&&c.gpr[3]==0x80000c00u&&c.gpr[4]==0x805290a8u&&c.gpr[5]==28u)++sys_step_;
                else if(sys_step_==1&&addr==0x80522320u&&c.gpr[3]==0x80000c00u&&c.gpr[4]==256u)++sys_step_;
                else if(sys_step_==2&&addr==0x80522378u&&c.gpr[3]==0x80000c00u&&c.gpr[4]==256u)++sys_step_;
                else return fail(17);
            }
        }else return fail(13);
        last_=c.inst_count;return true;
    }
private:
    ExceptionPackRouteExpectations e_;
    ExceptionPackWitness pack_;
    unsigned error_=0,vectors_=0,index_=0,step_=0,sys_step_=0,calls_=0;
    uint64_t last_=0;
    bool fail(unsigned n){if(!error_)error_=n;return false;}
    template<class Cpu> bool valid(Cpu& c,uint32_t addr) const{return c.is_running&&c.pc==addr&&c.inst_count>last_;}
    template<class Cpu> static bool word(Cpu& c,uint32_t a,uint32_t w){
        return a>=0x80000000u&&a<=0x817ffffcu&&!(a&3u)&&c.mmu.get_ptr(a)&&c.mmu.get_ptr(a+3)&&c.mmu.read32(a)==w;
    }
    template<class Cpu> static bool matches(Cpu& c,const VectorEdge& x){
        return c.pc==x.pc&&c.lr==x.lr&&word(c,x.pc,x.entry_word)&&word(c,x.lr-4u,x.branch_word);
    }
    template<class Cpu> static bool edge(Cpu& c,const std::array<VectorEdge,32>& edges,unsigned n){
        for(unsigned i=0;i<n;++i)if(matches(c,edges[i]))return true;
        return false;
    }
    template<class Cpu> bool vector_event(uint32_t addr,Cpu& c){
        if(!valid(c,addr)||index_!=vectors_||vectors_>=15)return fail(15);
        const uint32_t dest=0x80000000u+e_.image.offsets[index_];
        if(step_==1&&addr==0x80522320u&&c.lr==0x80520da8u&&c.gpr[3]==dest&&c.gpr[4]==152u&&edge(c,e_.exception_edges,e_.exception_count))step_=2;
        else if(step_==2&&addr==0x80522378u&&c.lr==0x80520db8u&&c.gpr[3]==dest&&c.gpr[4]==152u&&edge(c,e_.exception_edges,e_.exception_count))step_=3;
        else if(step_==3&&addr==0x80520db8u&&c.lr==addr&&word(c,addr,e_.vector_return_word)){step_=0;++vectors_;}
        else return fail(15);
        last_=c.inst_count;return true;
    }
};
}
