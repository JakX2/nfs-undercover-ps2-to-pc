#pragma once
// Original-free host path bridge for Wii/GC DVD filenames.
// This is an opt-in HLE helper, not a substitute for FST/DI emulation.
#include <cctype>
#include <filesystem>
#include <optional>
#include <string>
#include <string_view>
#include <vector>

namespace nwii::runtime {
namespace guest_disc_detail {
namespace fs = std::filesystem;

inline char ascii_fold(char c) {
    unsigned char b = static_cast<unsigned char>(c);
    return (b >= 'A' && b <= 'Z') ? static_cast<char>(b + 32) : c;
}
inline bool case_equal(std::string_view a, std::string_view b) {
    if (a.size() != b.size()) return false;
    for (size_t i=0; i<a.size(); ++i)
        if (ascii_fold(a[i]) != ascii_fold(b[i])) return false;
    return true;
}

inline std::optional<std::vector<std::string>> parse_guest_path(std::string_view raw) {
    if (raw.empty() || raw.size() > 4096) return std::nullopt;
    std::string s;
    s.reserve(raw.size());
    for (const char ch : raw) {
        const unsigned char c = static_cast<unsigned char>(ch);
        if (c == 0 || c < 32 || c == 127 || ch == ':') return std::nullopt;
        s.push_back(ch == '\\' ? '/' : ch);
    }
    // A single root slash is Wii-disc-relative, not a host absolute path.
    // UNC and double-slash prefixes are rejected.
    if (s.rfind("//", 0) == 0) return std::nullopt;
    if (s[0] == '/') s.erase(0, 1);
    if (s.empty() || s.back() == '/') return std::nullopt;
    std::vector<std::string> parts;
    size_t start=0;
    while (start < s.size()) {
        const size_t delim=s.find('/', start);
        const std::string part=s.substr(start, delim==std::string::npos ? std::string::npos : delim-start);
        if (part.empty() || part == "." || part == "..") return std::nullopt;
        parts.push_back(part);
        if (delim==std::string::npos) break;
        start=delim+1;
    }
    return parts;
}

inline std::optional<fs::path> try_root(const fs::path& root,
                                       const std::vector<std::string>& parts,
                                       bool allow_extract_prefix = false) {
    std::error_code ec;
    if (fs::is_symlink(fs::symlink_status(root, ec)) || ec) return std::nullopt;
    if (!fs::is_directory(root, ec)) return std::nullopt;
    fs::path current = root;
    for (size_t i = 0; i < parts.size(); ++i) {
        // Exact match takes precedence; ambiguous case-insensitive names fail closed.
        std::optional<fs::path> exact, folded, prefixed;
        bool ambiguous=false, prefixed_ambiguous=false;
        for (fs::directory_iterator it(current, fs::directory_options::skip_permission_denied, ec), end;
             !ec && it != end; it.increment(ec)) {
            const std::string name = it->path().filename().string();
            if (name == parts[i]) exact = it->path();
            else if (case_equal(name, parts[i])) {
                if (folded) ambiguous=true;
                else folded = it->path();
            } else if (allow_extract_prefix && i == 0 &&
                       case_equal(name, std::string("Extract") + parts[i])) {
                if (prefixed) prefixed_ambiguous=true;
                else prefixed = it->path();
            }
        }
        if (ec) return std::nullopt;
        if (!exact && ambiguous) return std::nullopt;
        if (!exact && !folded && prefixed_ambiguous) return std::nullopt;
        const auto found = exact ? exact : (folded ? folded : prefixed);
        if (!found) return std::nullopt;
        // Never traverse symlinks (including a symlinked final file).
        if (fs::is_symlink(fs::symlink_status(*found, ec)) || ec) return std::nullopt;
        if (i + 1 < parts.size() && !fs::is_directory(*found, ec)) return std::nullopt;
        current=*found;
    }
    return fs::is_regular_file(current, ec) && !ec ? std::optional<fs::path>(current) : std::nullopt;
}
} // namespace guest_disc_detail

// The unmodified NWiiRuntime expects a Dolphin/wit-style game root with
// sys/{boot.bin,fst.bin} and files/*. The owner may alternatively point at
// the flattened, unpacked asset directory. Try the canonical files/ first.
inline std::optional<std::filesystem::path> resolve_guest_disc_path(
    const std::filesystem::path& game_dir, std::string_view guest_filename) {
    using namespace guest_disc_detail;
    const auto parts=parse_guest_path(guest_filename);
    if (!parts) return std::nullopt;
    if (auto p=try_root(game_dir / "files", *parts)) return p;
    return try_root(game_dir, *parts, true);
}
} // namespace nwii::runtime
