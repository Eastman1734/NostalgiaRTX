// NostalgiaRTX integration of NVIDIA RTX Video SDK 1.1.
// This software contains source code provided by NVIDIA Corporation.
// NVIDIA SDK components remain governed by NVIDIA_RTX_Video_SDK_License.pdf.
#define WIN32_LEAN_AND_MEAN
#define NOMINMAX
#include <windows.h>
#include <d3d11.h>
#include <dxgi1_2.h>
#include <cstdio>
#include <cstring>
#include <new>
#include "nvsdk_ngx_helpers_vsr.h"

#define EXPORT extern "C" __declspec(dllexport)
static thread_local char error_text[1024] = "";
template <class T> static void release(T*& p) { if (p) { p->Release(); p = nullptr; } }
static bool hr_ok(HRESULT hr, const char* action) {
    if (SUCCEEDED(hr)) return true;
    snprintf(error_text, sizeof(error_text), "%s: HRESULT 0x%08lX", action, (unsigned long)hr);
    return false;
}
static bool ngx_ok(NVSDK_NGX_Result code, const char* action) {
    if (NVSDK_NGX_SUCCEED(code)) return true;
    snprintf(error_text, sizeof(error_text), "%s: NGX 0x%08X. Check the NVIDIA driver and nvngx_vsr.dll.", action, (unsigned)code);
    return false;
}

struct Engine {
    ID3D11Device* device = nullptr;
    ID3D11DeviceContext* context = nullptr;
    ID3D11Texture2D *input = nullptr, *output = nullptr, *readback = nullptr;
    NVSDK_NGX_Parameter* params = nullptr;
    NVSDK_NGX_Handle* feature = nullptr;
    unsigned w = 0, h = 0, ow = 0, oh = 0, quality = 3;
    bool initialized = false;
    ~Engine() {
        if (context) context->ClearState();
        if (feature) NVSDK_NGX_D3D11_ReleaseFeature(feature);
        if (params) NVSDK_NGX_D3D11_DestroyParameters(params);
        if (initialized) NVSDK_NGX_D3D11_Shutdown1(device);
        release(readback); release(output); release(input);
        release(context); release(device);
    }
};

EXPORT const char* nr_error() { return error_text; }
EXPORT void nr_destroy(void* pointer) { delete static_cast<Engine*>(pointer); }
EXPORT unsigned nr_abi_version() { return 1; }

EXPORT void* nr_create(unsigned w, unsigned h, unsigned scale, unsigned quality,
                       unsigned nvidia_index, const wchar_t* cache) {
    error_text[0] = 0;
    if (!w || !h || w > 8192 || h > 8192 || (scale != 2 && scale != 4) || quality < 1 || quality > 4
        || w * scale > 8192 || h * scale > 8192) {
        snprintf(error_text, sizeof(error_text), "Unsupported dimensions, scale, or quality."); return nullptr;
    }
    Engine* e = new (std::nothrow) Engine();
    if (!e) return nullptr;
    e->w = w; e->h = h; e->ow = w * scale; e->oh = h * scale; e->quality = quality;
    IDXGIFactory1* factory = nullptr;
    IDXGIAdapter1* adapter = nullptr;
    if (!hr_ok(CreateDXGIFactory1(__uuidof(IDXGIFactory1), (void**)&factory), "CreateDXGIFactory1")) { delete e; return nullptr; }
    unsigned found = 0;
    for (unsigned i = 0; factory->EnumAdapters1(i, &adapter) != DXGI_ERROR_NOT_FOUND; ++i) {
        DXGI_ADAPTER_DESC1 desc = {};
        adapter->GetDesc1(&desc);
        if (desc.VendorId == 0x10de && !(desc.Flags & DXGI_ADAPTER_FLAG_SOFTWARE)) {
            if (found++ == nvidia_index) break;
        }
        release(adapter);
    }
    release(factory);
    if (!adapter) { snprintf(error_text, sizeof(error_text), "NVIDIA GPU #%u not found.", nvidia_index); delete e; return nullptr; }
    D3D_FEATURE_LEVEL levels[] = { D3D_FEATURE_LEVEL_11_0 };
    HRESULT hr = D3D11CreateDevice(adapter, D3D_DRIVER_TYPE_UNKNOWN, nullptr, D3D11_CREATE_DEVICE_BGRA_SUPPORT,
                                 levels, 1, D3D11_SDK_VERSION, &e->device, nullptr, &e->context);
    release(adapter);
    if (!hr_ok(hr, "D3D11CreateDevice")) { delete e; return nullptr; }
    // Use a private SDK search path, not the current working directory.
    wchar_t dll_folder[32768] = {};
    HMODULE module = nullptr;
    GetModuleHandleExW(GET_MODULE_HANDLE_EX_FLAG_FROM_ADDRESS | GET_MODULE_HANDLE_EX_FLAG_UNCHANGED_REFCOUNT,
                       reinterpret_cast<LPCWSTR>(&nr_create), &module);
    GetModuleFileNameW(module, dll_folder, 32768);
    wchar_t* slash = wcsrchr(dll_folder, L'\\');
    if (slash) *slash = 0;
    const wchar_t* paths[] = {dll_folder};
    NVSDK_NGX_FeatureCommonInfo common = {};
    common.PathListInfo.Path = paths;
    common.PathListInfo.Length = 1;
    if (!ngx_ok(NVSDK_NGX_D3D11_Init(0, cache, e->device, &common), "NGX Init")) { delete e; return nullptr; }
    e->initialized = true;
    if (!ngx_ok(NVSDK_NGX_D3D11_GetCapabilityParameters(&e->params), "NGX capability parameters")) { delete e; return nullptr; }
    int available = 0;
    e->params->Get(NVSDK_NGX_Parameter_VSR_Available, &available);
    if (!available) {
        int needs_driver = 0;
        e->params->Get(NVSDK_NGX_Parameter_VSR_NeedsUpdatedDriver, &needs_driver);
        snprintf(error_text, sizeof(error_text), "RTX Video VSR is unavailable%s. An RTX GPU and a compatible NVIDIA driver are required.",
                 needs_driver ? ": update the driver" : ""); delete e; return nullptr;
    }
    NVSDK_NGX_Feature_Create_Params create = {};
    if (!ngx_ok(NGX_D3D11_CREATE_VSR_EXT(e->context, &e->feature, e->params, &create), "Create VSR")) { delete e; return nullptr; }
    D3D11_TEXTURE2D_DESC td = {};
    td.Width = e->w; td.Height = e->h; td.MipLevels = td.ArraySize = 1;
    td.Format = DXGI_FORMAT_B8G8R8A8_UNORM; td.SampleDesc.Count = 1;
    td.Usage = D3D11_USAGE_DEFAULT; td.BindFlags = D3D11_BIND_SHADER_RESOURCE;
    if (!hr_ok(e->device->CreateTexture2D(&td, nullptr, &e->input), "Create input texture")) { delete e; return nullptr; }
    // RGBA output supports typed UAV on D3D11. Input may be BGRA per SDK.
    td.Width = e->ow; td.Height = e->oh; td.Format = DXGI_FORMAT_R8G8B8A8_UNORM;
    td.BindFlags = D3D11_BIND_UNORDERED_ACCESS | D3D11_BIND_SHADER_RESOURCE;
    if (!hr_ok(e->device->CreateTexture2D(&td, nullptr, &e->output), "Create output texture")) { delete e; return nullptr; }
    td.Usage = D3D11_USAGE_STAGING; td.BindFlags = 0; td.CPUAccessFlags = D3D11_CPU_ACCESS_READ;
    if (!hr_ok(e->device->CreateTexture2D(&td, nullptr, &e->readback), "Create staging texture")) { delete e; return nullptr; }
    return e;
}

EXPORT int nr_process(void* pointer, const unsigned char* bgra, unsigned long long input_size,
                      unsigned char* rgba, unsigned long long output_size) {
    Engine* e = static_cast<Engine*>(pointer);
    if (!e || !bgra || !rgba || input_size != (unsigned long long)e->w*e->h*4
        || output_size != (unsigned long long)e->ow*e->oh*4) {
        snprintf(error_text, sizeof(error_text), "Incorrect frame buffer size."); return 0;
    }
    e->context->UpdateSubresource(e->input, 0, nullptr, bgra, e->w * 4, 0);
    NVSDK_NGX_D3D11_VSR_Eval_Params p = {};
    p.pInput = e->input; p.pOutput = e->output;
    p.InputSubrectSize.Width = e->w; p.InputSubrectSize.Height = e->h;
    p.OutputSubrectSize.Width = e->ow; p.OutputSubrectSize.Height = e->oh;
    p.QualityLevel = static_cast<NVSDK_NGX_VSR_QualityLevel>(e->quality);
    if (!ngx_ok(NGX_D3D11_EVALUATE_VSR_EXT(e->context, e->feature, e->params, &p), "Evaluate VSR")) return 0;
    e->context->CopyResource(e->readback, e->output);
    D3D11_MAPPED_SUBRESOURCE mapped = {};
    if (!hr_ok(e->context->Map(e->readback, 0, D3D11_MAP_READ, 0, &mapped), "Read VSR result")) return 0;
    for (unsigned y = 0; y < e->oh; ++y)
        memcpy(rgba + (size_t)y*e->ow*4, static_cast<unsigned char*>(mapped.pData) + (size_t)y*mapped.RowPitch, e->ow*4);
    e->context->Unmap(e->readback, 0);
    return 1;
}
