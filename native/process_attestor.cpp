// Read-only Win32 snapshot. Source only: no runtime deployment or automatic execution.
#define WIN32_LEAN_AND_MEAN
#include <winsock2.h>
#include <windows.h>
#include <iphlpapi.h>
#include <cstdio>
#include <cstdlib>
#include <cerrno>
#include <vector>
#include <string>
#pragma comment(lib, "iphlpapi.lib")
#pragma comment(lib, "ws2_32.lib")
static bool number(const wchar_t* s, unsigned long& n) {
    if (!s || !*s) return false;
    wchar_t* end = nullptr; errno = 0;
    n = wcstoul(s, &end, 10);
    return errno == 0 && end != s && *end == 0;
}
static std::string utf8(const wchar_t* src, int len) {
    int bytes = WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, src, len, nullptr, 0, nullptr, nullptr);
    if (bytes <= 0) return {};
    std::string out(bytes, '\0');
    if (WideCharToMultiByte(CP_UTF8, WC_ERR_INVALID_CHARS, src, len, out.data(), bytes, nullptr, nullptr) != bytes) return {};
    return out;
}
static std::string escape(const std::string& input) {
    std::string out;
    for (unsigned char c : input) {
        if (c == '"' || c == '\\') { out += '\\'; out += char(c); }
        else if (c < 32) { char b[7]; sprintf_s(b, "\\u%04x", c); out += b; }
        else out += char(c);
    }
    return out;
}
int wmain(int argc, wchar_t** argv) {
    unsigned long pid=0, port=0;
    if(argc!=3 || !number(argv[1],pid) || !number(argv[2],port) || pid==0 || port==0 || port>65535) return 2;
    DWORD sz=0;
    DWORD status=GetExtendedTcpTable(nullptr,&sz,FALSE,AF_INET,TCP_TABLE_OWNER_PID_LISTENER,0);
    if(status!=ERROR_INSUFFICIENT_BUFFER || sz==0 || sz>32*1024*1024) return 1;
    std::vector<BYTE> storage(sz);
    if(GetExtendedTcpTable(storage.data(),&sz,FALSE,AF_INET,TCP_TABLE_OWNER_PID_LISTENER,0)!=NO_ERROR) return 1;
    auto* table=reinterpret_cast<MIB_TCPTABLE_OWNER_PID*>(storage.data());
    DWORD matched=0;
    for(DWORD i=0;i<table->dwNumEntries;i++) {
        const auto& row=table->table[i];
        if(ntohs((u_short)row.dwLocalPort)==port &&
           row.dwLocalAddr==htonl(0x7f000001) && row.dwOwningPid==pid) matched++;
    }
    if(matched!=1) return 1;
    HANDLE process=OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION,FALSE,pid);
    if(!process) return 1;
    wchar_t path[32768]; DWORD len=32768;
    const BOOL image=QueryFullProcessImageNameW(process,0,path,&len);
    FILETIME created,exited,kernel,user;
    const BOOL times=GetProcessTimes(process,&created,&exited,&kernel,&user);
    CloseHandle(process);
    if(!image || !times) return 1;
    const std::string full=utf8(path,(int)len);
    if(full.empty()) return 1;
    ULARGE_INTEGER stamp; stamp.LowPart=created.dwLowDateTime; stamp.HighPart=created.dwHighDateTime;
    printf("{\"schema\":\"ezs.windows.attestation.v1\",\"verified\":true,\"pid\":%lu,\"port\":%lu,\"image_path\":\"%s\",\"creation_filetime\":\"%llu\",\"command_line_attested\":false,\"lifecycle_authorized\":false}\n",pid,port,escape(full).c_str(),stamp.QuadPart);
    return 0;
}
