#include "guest_disc_paths_v8.h"
#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <stdexcept>
#include <string>

namespace fs=std::filesystem;
using nwii::runtime::resolve_guest_disc_path;
static int checks=0;
static void check(bool yes, const char* why) {
    if (!yes) throw std::runtime_error(why);
    ++checks;
}
static void touch(const fs::path& filename) {
    fs::create_directories(filename.parent_path());
    std::ofstream f(filename,std::ios::binary); f << "fixture";
}
static bool resolves(const fs::path& root, std::string_view name, const fs::path& expected) {
    auto p=resolve_guest_disc_path(root,name);
    return p && fs::equivalent(*p,expected);
}
int main(int argc,char** argv) {
    if (argc!=2) return 2;
    auto root=fs::path(argv[1]);
    fs::remove_all(root); fs::create_directories(root);
    try {
        touch(root / "files" / "nfs" / "zdir.bin");
        touch(root / "files" / "global" / "gameplay.bin");
        touch(root / "files" / "Frontend" / "FrontB1.Bun");
        touch(root / "files" / "MOVIES" / "WIDESCREEN" / "NFS09_FMV3_ENGLISH_NTSC.VP6");
        touch(root / "GLOBAL" / "attributes.bin");
        touch(root / "ExtractSOUND" / "Speech" / "TEST.BIG");
        check(resolves(root,"NFS\\ZDIR.BIN", root/"files/nfs/zdir.bin"), "Wii backslash & fold");
        check(resolves(root,"/nfs/zdir.bin", root/"files/nfs/zdir.bin"), "disc-root slash");
        check(resolves(root,"GLOBAL/GAMEPLAY.BIN", root/"files/global/gameplay.bin"), "cross case");
        check(resolves(root,"FRONTEND\\FRONTB1.BUN",root/"files/Frontend/FrontB1.Bun"),"BUN asset");
        check(resolves(root,"MOVIES\\WIDESCREEN\\NFS09_FMV3_ENGLISH_NTSC.VP6",root/"files/MOVIES/WIDESCREEN/NFS09_FMV3_ENGLISH_NTSC.VP6"),"VP6 asset");
        check(resolves(root,"GLOBAL\\ATTRIBUTES.BIN",root/"GLOBAL/attributes.bin"),"flattened root fallback");
        check(resolves(root,"sound\\speech\\test.big",root/"ExtractSOUND/Speech/TEST.BIG"),"Extract prefix compatibility");
        check(!resolve_guest_disc_path(root,"MISSING\\FILE.BIN"),"absent files");
        check(!resolve_guest_disc_path(root,"../etc/passwd"),"parent traversal");
        check(!resolve_guest_disc_path(root,"NFS\\..\\GLOBAL\\GAMEPLAY.BIN"),"internal traversal");
        check(!resolve_guest_disc_path(root,"C:\\WINDOWS\\SYSTEM32"),"DOS absolute");
        check(!resolve_guest_disc_path(root,"\\\\server\\share"),"UNC absolute");
        check(!resolve_guest_disc_path(root,"GLOBAL//GAMEPLAY.BIN"),"empty segment");
        check(!resolve_guest_disc_path(root,"."),"dot segment");
        check(!resolve_guest_disc_path(root,"GLOBAL/"),"directory path");
        check(!resolve_guest_disc_path(root,std::string_view("NFS\0ZDIR.BIN",12)),"nul byte");
        check(!resolve_guest_disc_path(root,"/"),"disc root not file");
        check(!resolve_guest_disc_path(root,""),"empty name");
        check(!resolve_guest_disc_path(root,"NFS\\ZDIR.BIN\n"),"control char");
        check(!resolve_guest_disc_path(root,"////GLOBAL/GAMEPLAY.BIN"),"double rooted path");
        // Prefer files/ content when a duplicate exists in the root.
        touch(root/"NFS/ZDIR.BIN");
        check(resolves(root,"NFS/ZDIR.BIN",root/"files/nfs/zdir.bin"),"files dir precedence");
        // Exact match wins, but ambiguous folded-only matches are rejected.
        touch(root/"files/dupe/A.BIN");touch(root/"files/dupe/a.BIN");
        check(resolves(root,"dupe/A.BIN",root/"files/dupe/A.BIN"),"exact case precedence");
        check(!resolve_guest_disc_path(root,"dupe/a.Bin"),"ambiguous case-fold collision");
        // Symlink traversal never allowed. Skip on Windows hosts lacking privilege.
        std::error_code ec;
        fs::create_symlink(root/"files/nfs/zdir.bin",root/"files/nfs/ALIAS.BIN",ec);
        if (!ec) check(!resolve_guest_disc_path(root,"NFS/ALIAS.BIN"),"symlink rejected");
        fs::create_directory_symlink(root/"files/global",root/"files/LINKED",ec);
        if (!ec) check(!resolve_guest_disc_path(root,"LINKED/GAMEPLAY.BIN"),"symlink directory rejected");
        fs::create_directory_symlink(root/"files/global",root/"ExtractLINKED",ec);
        if (!ec) check(!resolve_guest_disc_path(root,"LINKED/GAMEPLAY.BIN"),"Extract prefix symlink rejected");
        std::cout << "PASS: " << checks << " original-free Wii host disc path tests\n";
        fs::remove_all(root);
    } catch(...) {fs::remove_all(root);throw;}
}
