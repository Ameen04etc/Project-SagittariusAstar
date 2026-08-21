#include "TerminalSession.h"

#include <utility>
#include <cstdint>
#include <vector>

TerminalSession::TerminalSession() {}

void TerminalSession::Resize(short Columns, short Rows)
{
    if (Console)
    {
        COORD NewSize{};
        NewSize.X = Columns;
        NewSize.Y = Rows;
        ResizePseudoConsole(Console, NewSize);
    }
}

TerminalSession::~TerminalSession()
{
    Stop();
}

bool TerminalSession::Start()
{
    if (Running)
        return true;

    HANDLE InputRead = nullptr;
    HANDLE OutputWrite = nullptr;

    if (!CreatePipe(&InputRead, &InputWrite, nullptr, 0))
        return false;

    if (!CreatePipe(&OutputRead, &OutputWrite, nullptr, 0))
    {
        CloseHandle(InputRead);
        CloseHandle(InputWrite);
        InputRead = nullptr;
        InputWrite = nullptr;
        return false;
    }

    COORD ConsoleSize{};
    ConsoleSize.X = 120;
    ConsoleSize.Y = 30;

    HRESULT Result = CreatePseudoConsole(
        ConsoleSize,
        InputRead,
        OutputWrite,
        0,
        &Console
    );

    if (FAILED(Result))
    {
        CloseHandle(InputRead);
        CloseHandle(InputWrite);
        CloseHandle(OutputRead);
        CloseHandle(OutputWrite);
        InputRead = nullptr;
        InputWrite = nullptr;
        OutputRead = nullptr;
        OutputWrite = nullptr;
        return false;
    }

    // These are the ConPTY-side handles. Our application keeps
    // InputWrite and OutputRead.
    CloseHandle(InputRead);
    CloseHandle(OutputWrite);

    SIZE_T AttributeListSize = 0;

    InitializeProcThreadAttributeList(
        nullptr,
        1,
        0,
        &AttributeListSize
    );

    auto AttributeList =
        reinterpret_cast<LPPROC_THREAD_ATTRIBUTE_LIST>(
            HeapAlloc(GetProcessHeap(), 0, AttributeListSize)
        );

    if (!AttributeList)
    {
        Stop();
        return false;
    }

    if (!InitializeProcThreadAttributeList(
            AttributeList,
            1,
            0,
            &AttributeListSize))
    {
        HeapFree(GetProcessHeap(), 0, AttributeList);
        Stop();
        return false;
    }

    if (!UpdateProcThreadAttribute(
            AttributeList,
            0,
            PROC_THREAD_ATTRIBUTE_PSEUDOCONSOLE,
            Console,
            sizeof(HPCON),
            nullptr,
            nullptr))
    {
        DeleteProcThreadAttributeList(AttributeList);
        HeapFree(GetProcessHeap(), 0, AttributeList);
        Stop();
        return false;
    }

    STARTUPINFOEXW StartupInfo{};
    StartupInfo.StartupInfo.cb = sizeof(STARTUPINFOEXW);
    StartupInfo.lpAttributeList = AttributeList;

    PROCESS_INFORMATION ProcessInfo{};

    wchar_t CommandLine[] = L"powershell.exe -NoLogo";

    BOOL Success = CreateProcessW(
        nullptr,
        CommandLine,
        nullptr,
        nullptr,
        FALSE,
        EXTENDED_STARTUPINFO_PRESENT,
        nullptr,
        nullptr,
        &StartupInfo.StartupInfo,
        &ProcessInfo
    );

    DeleteProcThreadAttributeList(AttributeList);
    HeapFree(GetProcessHeap(), 0, AttributeList);

    if (!Success)
    {
        Stop();
        return false;
    }

    ProcessHandle = ProcessInfo.hProcess;
    ThreadHandle = ProcessInfo.hThread;

    Running = true;

    ReaderThread = std::thread(
        &TerminalSession::ReaderLoop,
        this
    );

    return true;
}

void TerminalSession::ReaderLoop(){
    char Buffer[4096];

    // Maximum amount of output to send in one callback.
    // We do NOT wait for this many bytes.
    constexpr std::size_t MaxBatchSize = 16 * 1024;

    std::vector<char> Pending;
    Pending.reserve(MaxBatchSize);

    while (Running)
    {
        DWORD BytesRead = 0;

        // Blocking read: if there is no output, this thread waits here
        // until ConPTY produces some data.
        BOOL Success = ReadFile(
            OutputRead,
            Buffer,
            sizeof(Buffer),
            &BytesRead,
            nullptr
        );

        if (!Success)
            break;

        if (BytesRead == 0)
            continue;

        Pending.insert(
            Pending.end(),
            Buffer,
            Buffer + BytesRead
        );

        // Drain data that is ALREADY waiting in the pipe.
        // PeekNamedPipe() does not consume data; it only tells us how much
        // data can currently be read without waiting.
        while (Running && Pending.size() < MaxBatchSize)
        {
            DWORD Available = 0;

            BOOL PeekSuccess = PeekNamedPipe(
                OutputRead,
                nullptr,
                0,
                nullptr,
                &Available,
                nullptr
            );

            if (!PeekSuccess || Available == 0)
                break;

            DWORD Remaining = static_cast<DWORD>(
                MaxBatchSize - Pending.size()
            );

            DWORD ToRead = (Available < Remaining)
                ? Available
                : Remaining;

            DWORD ExtraBytesRead = 0;

            BOOL ReadSuccess = ReadFile(
                OutputRead,
                Buffer,
                ToRead,
                &ExtraBytesRead,
                nullptr
            );

            if (!ReadSuccess || ExtraBytesRead == 0)
                break;

            Pending.insert(
                Pending.end(),
                Buffer,
                Buffer + ExtraBytesRead
            );
        }

        // Deliver one callback for the whole currently available burst.
        if (OnOutput && !Pending.empty())
        {
            OnOutput(
                Pending.data(),
                Pending.size()
            );
        }

        Pending.clear();
    }
}

bool TerminalSession::Send(const char* Data, std::size_t Size)
{
    if (!Running || !InputWrite || !Data)
        return false;

    DWORD BytesWritten = 0;

    BOOL Success = WriteFile(
        InputWrite,
        Data,
        static_cast<DWORD>(Size),
        &BytesWritten,
        nullptr
    );

    return Success && BytesWritten == Size;
}

void TerminalSession::SetOutputCallback(OutputCallback Callback)
{
    OnOutput = std::move(Callback);
}

bool TerminalSession::IsRunning() const
{
    return Running.load();
}

void TerminalSession::Stop()
{
    if (!Running)
        return;

    Running = false;

    // ReadFile() may be blocked in ReaderLoop(). Cancel the synchronous
    // I/O from this thread before joining the reader.
    if (ReaderThread.joinable())
    {
        CancelSynchronousIo(ReaderThread.native_handle());
    }

    // Temporary/simple shutdown for this first version.
    // We will make shutdown graceful later.
    if (ProcessHandle)
    {
        TerminateProcess(ProcessHandle, 0);
    }

    if (ReaderThread.joinable())
    {
        ReaderThread.join();
    }

    if (ThreadHandle)
    {
        CloseHandle(ThreadHandle);
        ThreadHandle = nullptr;
    }

    if (ProcessHandle)
    {
        CloseHandle(ProcessHandle);
        ProcessHandle = nullptr;
    }

    if (InputWrite)
    {
        CloseHandle(InputWrite);
        InputWrite = nullptr;
    }

    if (OutputRead)
    {
        CloseHandle(OutputRead);
        OutputRead = nullptr;
    }

    if (Console)
    {
        ClosePseudoConsole(Console);
        Console = nullptr;
    }

    OnOutput = nullptr;
}

