#include <cstdint>
#include <wiixlaunch.hpp>
#include <wiixlaunch/botw/game/pouch.hpp>
#include <stddef.h>

extern "C" void* memset(void* destination, int value, size_t count)
{
    unsigned char* bytes = static_cast<unsigned char*>(destination);

    for (size_t i = 0; i < count; ++i)
    {
        bytes[i] = static_cast<unsigned char>(value);
    }

    return destination;
}

using namespace WiiXLaunch::BotW;
static uint32_t LocalStringLength(const char* text) {
    uint32_t length = 0;
    if (!text) return 0;
    while (text[length] != '\0') {
        ++length;
    }
    return length;
}

extern "C" {
    extern void wiixl_import__wiixl_core__Log(const char* text);
    extern uint32_t wiixl_import__wiixl_core__RegisterTick(
        void (*fn)()
    );

    extern uint32_t wiixl_import__wiixl_net__Available(void);
    extern uint32_t wiixl_import__wiixl_net__Open(
        uint32_t* outHandle
    );
    extern uint32_t wiixl_import__wiixl_net__SetNonBlocking(
        uint32_t handle
    );
    extern uint32_t wiixl_import__wiixl_net__SetReuseAddr(
        uint32_t handle
    );
    extern uint32_t wiixl_import__wiixl_net__Bind(
        uint32_t handle,
        uint32_t port
    );
    extern uint32_t wiixl_import__wiixl_net__Listen(
        uint32_t handle,
        uint32_t backlog
    );
    extern uint32_t wiixl_import__wiixl_net__Accept(
        uint32_t listener,
        uint32_t* outHandle
    );
    extern int32_t wiixl_import__wiixl_net__Recv(
        uint32_t handle,
        void* buffer,
        uint32_t maxSize
    );
    extern int32_t wiixl_import__wiixl_net__Send(
        uint32_t handle,
        const void* buffer,
        uint32_t size
    );
    extern uint32_t wiixl_import__wiixl_net__Shutdown(
        uint32_t handle,
        uint32_t how
    );
    extern uint32_t wiixl_import__wiixl_net__Close(
        uint32_t handle
    );
}

using U32Fn = uint32_t (*)(void);
using OpenFn = uint32_t (*)(uint32_t*);
using HandleFn = uint32_t (*)(uint32_t);
using BindFn = uint32_t (*)(uint32_t, uint32_t);
using AcceptFn = uint32_t (*)(uint32_t, uint32_t*);
using RecvFn = int32_t (*)(uint32_t, void*, uint32_t);
using SendFn = int32_t (*)(uint32_t, const void*, uint32_t);
using ShutdownFn = uint32_t (*)(uint32_t, uint32_t);
using LogFn = void (*)(const char*);
using TickRegFn = uint32_t (*)(void (*)());

static U32Fn volatile g_Available =
    &wiixl_import__wiixl_net__Available;
static OpenFn volatile g_Open =
    &wiixl_import__wiixl_net__Open;
static HandleFn volatile g_NonBlocking =
    &wiixl_import__wiixl_net__SetNonBlocking;
static HandleFn volatile g_ReuseAddr =
    &wiixl_import__wiixl_net__SetReuseAddr;
static BindFn volatile g_Bind =
    &wiixl_import__wiixl_net__Bind;
static BindFn volatile g_Listen =
    &wiixl_import__wiixl_net__Listen;
static AcceptFn volatile g_Accept =
    &wiixl_import__wiixl_net__Accept;
static RecvFn volatile g_Recv =
    &wiixl_import__wiixl_net__Recv;
static SendFn volatile g_Send =
    &wiixl_import__wiixl_net__Send;
static ShutdownFn volatile g_Shutdown =
    &wiixl_import__wiixl_net__Shutdown;
static HandleFn volatile g_Close =
    &wiixl_import__wiixl_net__Close;
static LogFn volatile g_Log =
    &wiixl_import__wiixl_core__Log;
static TickRegFn volatile g_RegisterTick =
    &wiixl_import__wiixl_core__RegisterTick;

static constexpr uint32_t kOk = 0;
static constexpr uint32_t kNoConnection = 0;
static constexpr uint32_t kPort = 8080;

static uint32_t g_Listener = 0;
static uint32_t g_Client = kNoConnection;
static uint32_t g_TicksWaiting = 0;

static char g_Command[128];
static uint32_t g_CommandLength = 0;

static void CloseClient() {
    if (g_Client == kNoConnection) {
        return;
    }

    g_Shutdown(g_Client, 1);
    g_Close(g_Client);

    g_Client = kNoConnection;
    g_TicksWaiting = 0;
    g_CommandLength = 0;
}

static void Reply(const char* message) {
    if (g_Client == kNoConnection) {
        return;
    }

    g_Send(
        g_Client,
        message,
        LocalStringLength(message)
    );

    CloseClient();
}

static const char* g_Result = "ERR invalid command or item\n";

// Expected command:
// GIVE Item_Fruit_D 1
//
// This deliberately accepts only a restricted actor-name format.
// The client connection is local to your PC; do not expose this port
//  to the internet.
static bool ParseSignedInt32(const char* text, int32_t* out)
{
    if (!text || !*text || !out)
        return false;

    bool negative = false;

    if (*text == '-' || *text == '+')
    {
        negative = (*text == '-');
        ++text;
    }

    if (!*text)
        return false;

    int64_t value = 0;

    while (*text)
    {
        if (*text < '0' || *text > '9')
            return false;

        value = value * 10 + (*text - '0');

        if (value > 2147483648LL)
            return false;

        ++text;
    }

    if (negative)
        value = -value;

    if (value < INT32_MIN || value > INT32_MAX)
        return false;

    *out = static_cast<int32_t>(value);
    return true;
}

static bool ParseUnsigned32(const char* text, uint32_t* out)
{
    if (!text || !*text || !out)
        return false;

    uint64_t value = 0;

    while (*text)
    {
        if (*text < '0' || *text > '9')
            return false;

        value = value * 10 + (*text - '0');

        if (value > UINT32_MAX)
            return false;

        ++text;
    }

    *out = static_cast<uint32_t>(value);
    return true;
}

static bool ParseAndGrant()
{
    char* tokens[5] = {};
    int tokenCount = 0;
    char* p = g_Command;

    while (*p == ' ' || *p == '\t')
        ++p;

    while (*p && *p != '\r' && *p != '\n')
    {
        if (tokenCount >= 5)
            return false;

        tokens[tokenCount++] = p;

        while (*p && *p != ' ' && *p != '\t' &&
               *p != '\r' && *p != '\n')
        {
            ++p;
        }

        if (*p == ' ' || *p == '\t')
        {
            *p++ = '\0';

            while (*p == ' ' || *p == '\t')
                ++p;
        }
        else
        {
            if (*p)
                *p++ = '\0';

            break;
        }
    }

    if (tokenCount < 2 || tokenCount > 5)
        return false;

    if (LocalStringLength(tokens[0]) != 4 ||
        tokens[0][0] != 'G' ||
        tokens[0][1] != 'I' ||
        tokens[0][2] != 'V' ||
        tokens[0][3] != 'E')
    {
        return false;
    }

    const char* actor = tokens[1];

    if (!actor || !*actor)
        return false;

    int32_t requestedValue = 1;
    const bool hasValue = (tokenCount >= 3);

    if (hasValue &&
        !ParseSignedInt32(tokens[2], &requestedValue))
    {
        return false;
    }

    const bool hasModifier = (tokenCount == 5);

    uint32_t modifierFlags = 0;
    int32_t modifierMagnitude = 0;

    if (hasModifier)
    {
        if (!ParseUnsigned32(tokens[3], &modifierFlags) ||
            !ParseSignedInt32(tokens[4], &modifierMagnitude))
        {
            return false;
        }
    }

    int32_t storedValue = requestedValue;

    // Pouch item types:
    // 0 = melee weapon, 1 = bow, 2 = arrow, 3 = shield.
    // The CLI's requested weapon durability is in ordinary game units;
    // the pouch API expects the stored durability value.
    const int itemType = WiiXLaunch::BotW::Pouch::GetTypeForName(actor);

    if (hasValue &&
        (itemType == 0 || itemType == 1 || itemType == 3))
    {
        if (requestedValue > INT32_MAX / 100 ||
            requestedValue < INT32_MIN / 100)
        {
            return false;
        }

        storedValue = requestedValue * 100;
    }

    bool added = false;

    if (hasValue)
        added = WiiXLaunch::BotW::Pouch::AddItem(actor, storedValue);
    else
        added = WiiXLaunch::BotW::Pouch::AddItem(actor);

    if (!added)
    {
        g_Result = "ERR item rejected\n";
        return false;
    }

    if (hasModifier)
    {
        // Weapon modifiers are supported only for melee weapons,
        // bows, and shields.
        if (itemType != 0 && itemType != 1 && itemType != 3)
        {
            g_Result = "ERR item added; modifiers unsupported for this item type\n";
            return false;
        }

        const uintptr_t newest =
            WiiXLaunch::BotW::Pouch::FindNewestItem(actor);

        if (!newest ||
            !WiiXLaunch::BotW::Pouch::SetModifierAt(
                newest, modifierFlags, modifierMagnitude))
        {
            g_Result = "ERR item added but modifier application failed\n";
            return false;
        }
    }

    g_Result = "OK\n";
    return true;
}

extern "C" __attribute__((used)) void WiiXLaunch_ModTick() {
    if (g_Listener == 0) {
        return;
    }

    if (g_Client == kNoConnection) {
        uint32_t client = 0;

        if (g_Accept(g_Listener, &client) == kOk) {
            g_Client = client;
            g_TicksWaiting = 0;
            g_CommandLength = 0;
        }

        return;
    }

    ++g_TicksWaiting;

    // Don't leave a client connected indefinitely.
    if (g_TicksWaiting > 300) {
        Reply("ERR timeout\n");
        return;
    }

    char incoming[32];

    const int32_t received = g_Recv(
        g_Client,
        incoming,
        sizeof(incoming)
    );

    if (received == 0) {
        CloseClient();
        return;
    }

    if (received < 0) {
        return;
    }

    for (int32_t i = 0; i < received; ++i) {
        const char c = incoming[i];

        if (g_CommandLength >= sizeof(g_Command) - 1) {
            Reply("ERR command too long\n");
            return;
        }

        g_Command[g_CommandLength++] = c;

        if (c == '\n') {
            ParseAndGrant();
            Reply(g_Result);
            return;
        }
    }
}

extern "C" __attribute__((used)) void WiiXLaunch_ModEntry() {
    if (!g_Log || !g_Available || !g_Open ||
        !g_RegisterTick) {
        return;
    }

    g_Log("BotW AP bridge: starting");

    if (!g_Available()) {
        g_Log("BotW AP bridge: network API unavailable");
        return;
    }

    if (g_Open(&g_Listener) != kOk) {
        g_Log("BotW AP bridge: socket open failed");
        g_Listener = 0;
        return;
    }

    if (g_ReuseAddr) {
        g_ReuseAddr(g_Listener);
    }

    if (g_NonBlocking(g_Listener) != kOk) {
        g_Log("BotW AP bridge: nonblocking setup failed");
        g_Close(g_Listener);
        g_Listener = 0;
        return;
    }

    if (g_Bind(g_Listener, kPort) != kOk) {
        g_Log("BotW AP bridge: port 8080 bind failed");
        g_Close(g_Listener);
        g_Listener = 0;
        return;
    }

    if (g_Listen(g_Listener, 1) != kOk) {
        g_Log("BotW AP bridge: listen failed");
        g_Close(g_Listener);
        g_Listener = 0;
        return;
    }

    g_RegisterTick(&WiiXLaunch_ModTick);

    g_Log("BotW AP bridge: listening on port 8080");
}