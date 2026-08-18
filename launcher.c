#define WIN32_LEAN_AND_MEAN
#include <windows.h>
#include <shellapi.h>
#include <stdio.h>
#include <stdlib.h>

int file_exists(const char *path) {
    DWORD dwAttrib = GetFileAttributesA(path);
    return (dwAttrib != INVALID_FILE_ATTRIBUTES && !(dwAttrib & FILE_ATTRIBUTE_DIRECTORY));
}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {
    char exeDir[MAX_PATH];
    GetModuleFileNameA(NULL, exeDir, MAX_PATH);
    char *lastSlash = strrchr(exeDir, '\\');
    if (lastSlash) *lastSlash = '\0';
    SetCurrentDirectoryA(exeDir);

    char pythonPath[MAX_PATH] = {0};

    // 1. Check python_path.txt configured by setup wizard
    char cfgPath[MAX_PATH];
    snprintf(cfgPath, MAX_PATH, "%s\\python_path.txt", exeDir);
    FILE *f = fopen(cfgPath, "r");
    if (f) {
        if (fgets(pythonPath, MAX_PATH, f)) {
            char *nl = strchr(pythonPath, '\r');
            if (nl) *nl = '\0';
            nl = strchr(pythonPath, '\n');
            if (nl) *nl = '\0';
        }
        fclose(f);
    }

    // 2. Fallbacks if not found or invalid
    if (pythonPath[0] == '\0' || !file_exists(pythonPath)) {
        // Check standard locations
        const char *candidates[] = {
            "C:\\Users\\Bikram\\PycharmProjects\\PythonProject2\\.venv\\Scripts\\pythonw.exe",
            "C:\\Users\\Bikram\\PycharmProjects\\PythonProject2\\.venv\\Scripts\\python.exe",
            ".venv\\Scripts\\pythonw.exe",
            ".venv\\Scripts\\python.exe",
            "pythonw.exe",
            "python.exe"
        };
        for (int i = 0; i < 6; i++) {
            if (file_exists(candidates[i]) || i >= 4) {
                strncpy(pythonPath, candidates[i], MAX_PATH);
                break;
            }
        }
    }

    // Prepare command line: "pythonPath" main.py
    char cmd[1024];
    snprintf(cmd, sizeof(cmd), "\"%s\" main.py", pythonPath);

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    ZeroMemory(&pi, sizeof(pi));

    // Try CreateProcess without console window
    if (!CreateProcessA(NULL, cmd, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, exeDir, &si, &pi)) {
        // Fallback: ShellExecute
        HINSTANCE hRes = ShellExecuteA(NULL, "open", pythonPath, "main.py", exeDir, SW_SHOWNORMAL);
        if ((INT_PTR)hRes <= 32) {
            MessageBoxA(NULL, "Unable to launch Crazyy Simulation.\nPlease ensure Python and Pygame are installed.", "Crazyy Simulation - Error", MB_OK | MB_ICONERROR);
            return 1;
        }
    } else {
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }

    return 0;
}
