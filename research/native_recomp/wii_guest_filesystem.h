#pragma once
#include <cstdint>
#include <limits>
#include <map>
#include <memory>
#include <string>
#include <string_view>
#include <utility>
#include <vector>

// Independent, read-only guest filesystem namespace for native Wii IOS.
// The platform explicitly mounts bytes it owns. No host filesystem calls.
// Public protocol: https://wiibrew.org/wiki//dev/fs and
// https://wiibrew.org/wiki/IOS/resource_request
namespace undercover::wii {
class GuestFiles {
public:
    using Bytes=std::vector<uint8_t>;
    using Blob=std::shared_ptr<const Bytes>;
    static bool valid_path(std::string_view p) noexcept {
        if(p.size()<2u||p.size()>63u||p.front()!='/'||p.back()=='/'||
           p=="/dev"||p.starts_with("/dev/"))return false;
        unsigned parts=0;size_t begin=1;
        while(begin<p.size()){
            const auto end=p.find('/',begin);
            const auto part=p.substr(begin,end==p.npos?p.size()-begin:end-begin);
            if(part.empty()||part=="."||part==".."||++parts>8u)return false;
            for(unsigned char x:part)if(x<0x20u||x>=0x7fu||x=='\\'||x==':')return false;
            if(end==p.npos)break;
            begin=end+1u;
        }
        return true;
    }
    bool add(std::string path,Bytes bytes){
        if(!valid_path(path)||bytes.size()>uint32_t(std::numeric_limits<int32_t>::max())||
           files_.contains(path))return false;
        files_.emplace(std::move(path),std::make_shared<const Bytes>(std::move(bytes)));
        return true;
    }
    Blob find(std::string_view path) const {
        if(!valid_path(path))return {};
        const auto it=files_.find(path);
        return it==files_.end()?Blob{}:it->second;
    }
private:
    std::map<std::string,Blob,std::less<>> files_;
};
}
