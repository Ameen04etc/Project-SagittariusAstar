#pragma once

#include <windows.h>
#include <wincon.h>

#include <thread>
#include <atomic>
#include <functional>
#include <cstddef>

class TerminalSession
{
public:
    using OutputCallback = std::function<void(const char*, std::size_t)>;

    TerminalSession();
    ~TerminalSession();

    bool Start();
    void Stop();
    bool Send(const char* Data, std::size_t Size);
    void SetOutputCallback(OutputCallback Callback);
    bool IsRunning() const;
    void Resize(short Columns, short Rows);

private:
    void ReaderLoop();

private:
    HPCON Console = nullptr;

    HANDLE InputWrite = nullptr;
    HANDLE OutputRead = nullptr;

    HANDLE ProcessHandle = nullptr;
    HANDLE ThreadHandle = nullptr;

    std::thread ReaderThread;
    std::atomic<bool> Running = false;

    OutputCallback OnOutput;
};