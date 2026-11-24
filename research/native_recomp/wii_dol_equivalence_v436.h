#pragma once
#include <cstdint>
#include <cstddef>

namespace undercover::wii {
// Compare complete loaded images, not just aggregate checksums or sizes.
// This intentionally preserves original section order and BSS semantics.
enum class DolMismatch : unsigned { None, Entry, Count, Geometry, Flags, Payload };
template<class Sections>
DolMismatch compare_dol(uint32_t original_entry,const Sections& original,
                        uint32_t strict_entry,const Sections& strict){
    if(original_entry!=strict_entry)return DolMismatch::Entry;
    if(original.size()!=strict.size())return DolMismatch::Count;
    for(std::size_t i=0;i<original.size();++i){
        const auto& a=original[i];const auto& b=strict[i];
        if(a.address!=b.address||a.size!=b.size)return DolMismatch::Geometry;
        if(a.is_text!=b.is_text||a.is_bss!=b.is_bss)return DolMismatch::Flags;
        if(a.data!=b.data)return DolMismatch::Payload;
    }
    return DolMismatch::None;
}
}
