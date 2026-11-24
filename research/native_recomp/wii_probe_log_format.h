#pragma once
#include <ios>

namespace undercover::wii {
// The upstream runtime prints guest PCs with std::hex on the same stream.
// Witness numbers must not inherit those formatting flags. Restore the
// caller's formatting when the bounded observer returns normally.
class ScopedProbeDecimal {
    std::ios_base& stream_;
    std::ios_base::fmtflags flags_;
    std::streamsize width_;
public:
    explicit ScopedProbeDecimal(std::ios_base& s):stream_(s),flags_(s.flags()),width_(s.width()){
        stream_.setf(std::ios_base::dec,std::ios_base::basefield);
        stream_.unsetf(std::ios_base::showbase|std::ios_base::showpos);
        stream_.width(0);
    }
    ~ScopedProbeDecimal(){stream_.flags(flags_);stream_.width(width_);}
    ScopedProbeDecimal(const ScopedProbeDecimal&)=delete;
    ScopedProbeDecimal& operator=(const ScopedProbeDecimal&)=delete;
};
}
