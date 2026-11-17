#pragma once
// Original-free narrow EXI immediate transaction test device. No claim of
// complete Wii hardware emulation. Reject every out-of-order operation.
#include <cstdint>
#include <stdexcept>

struct ExiIdTestDevice {
    static constexpr uint32_t CSR=0x0d006800u, CR=0x0d00680cu,
        DATA=0x0d006810u, HWREV=0x0d006024u;
    uint32_t response=0, csr=0, control=0, pending=0;
    unsigned write_busy=0, read_busy=0, polls=0, revision_reads=0;
    enum class Phase { idle, ready, selected, command, writing, written,
                       reading, received, data_read, done };
    Phase phase=Phase::idle;

    static void need(bool ok,const char*msg){
        if(!ok)throw std::runtime_error(msg);
    }
    void reset(uint32_t id,unsigned wb,unsigned rb){
        *this=ExiIdTestDevice{};
        response=id;write_busy=wb;read_busy=rb;
    }
    void begin(uint32_t initial_csr){
        need(phase==Phase::idle && initial_csr==0x2000u,
             "EXI ID device was not initialized by authentic startup");
        csr=initial_csr;phase=Phase::ready;
    }
    bool active() const {return phase!=Phase::idle;}
    bool complete() const {return phase==Phase::done && revision_reads==2u;}
    uint32_t read(uint32_t addr){
        if(addr==CSR){
            need(phase==Phase::ready||phase==Phase::data_read,
                 "unexpected EXI CSR read during immediate transaction");
            return csr;
        }
        if(addr==CR){
            need(phase==Phase::writing||phase==Phase::reading,
                 "EXI control polled without an active transfer");
            need(++polls<=32u,"unbounded EXI immediate status polling");
            if(pending){--pending;return control;}
            const bool writing=phase==Phase::writing;
            phase=writing?Phase::written:Phase::received;
            return control&~1u;
        }
        if(addr==HWREV){
            need((phase==Phase::written&&revision_reads==0u)||
                 (phase==Phase::data_read&&revision_reads==1u),
                 "unexpected hardware-revision read");
            ++revision_reads;return 1u; // Explicit synthetic non-0xff revision.
        }
        if(addr==DATA){
            need(phase==Phase::received,"EXI ID register read before completed read transfer");
            phase=Phase::data_read;return response;
        }
        throw std::runtime_error("unrecognized EXI device read");
    }
    void write(uint32_t addr,uint32_t value){
        if(addr==CSR){
            if(phase==Phase::ready){
                need(value==0x200u,"EXI selected unexpected device or frequency");
                csr=value;phase=Phase::selected;return;
            }
            need(phase==Phase::data_read&&revision_reads==2u&&value==0u,
                 "EXI deselected before completed ID response");
            csr=value;phase=Phase::done;return;
        }
        if(addr==DATA){
            need(phase==Phase::selected&&value==0u,"EXI ID requires two-byte zero command");
            phase=Phase::command;return;
        }
        if(addr==CR){
            if(phase==Phase::command){
                need(value==0x15u,"EXI ID command must be two-byte immediate write");
                control=value;pending=write_busy;phase=Phase::writing;return;
            }
            need(phase==Phase::written&&revision_reads==1u&&value==0x31u,
                 "EXI ID response must be four-byte immediate read after command sync");
            control=value;pending=read_busy;phase=Phase::reading;return;
        }
        throw std::runtime_error("unrecognized EXI device write");
    }
};
