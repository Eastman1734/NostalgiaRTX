#define UNICODE
#define _UNICODE
#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <wchar.h>

int WINAPI wWinMain(HINSTANCE instance, HINSTANCE previous, PWSTR args, int show) {
    wchar_t folder[32768], python[32768], script[32768], cmd[65536];
    GetModuleFileNameW(NULL, folder, 32768);
    wchar_t* slash = wcsrchr(folder, L'\\');
    if (!slash) return 1;
    *slash = 0;
    swprintf(python, 32768, L"%ls\\.runtime\\pythonw.exe", folder);
    swprintf(script, 32768, L"%ls\\main.py", folder);
    if (GetFileAttributesW(python) == INVALID_FILE_ATTRIBUTES) {
        int answer = MessageBoxW(NULL,
            L"First launch needs the Python/Qt runtime and FFmpeg (downloaded from official sources).\n\nRun local setup now?",
            L"Nostalgia RTX - first launch", MB_OKCANCEL | MB_ICONINFORMATION);
        if (answer != IDOK) return 0;
        swprintf(script, 32768, L"%ls\\INSTALL.cmd", folder);
        if ((INT_PTR)ShellExecuteW(NULL, L"open", script, NULL, folder, SW_SHOWNORMAL) <= 32)
            MessageBoxW(NULL, L"Run INSTALL.cmd from the application folder.", L"Setup could not start", MB_OK | MB_ICONERROR);
        return 0;
    }
    swprintf(cmd, 65536, L"\"%ls\" \"%ls\"", python, script);
    STARTUPINFOW startup = {sizeof(startup)};
    PROCESS_INFORMATION process = {0};
    if (!CreateProcessW(python, cmd, NULL, NULL, FALSE, 0, NULL, folder, &startup, &process)) {
        MessageBoxW(NULL, L"Unable to start Python. Run INSTALL.cmd again or use START.cmd to see the error.",
                    L"Nostalgia RTX", MB_OK | MB_ICONERROR);
        return 1;
    }
    CloseHandle(process.hThread); CloseHandle(process.hProcess);
    return 0;
}
