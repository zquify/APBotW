#include <wiixlaunch.hpp>
#include <wiixlaunch/loader/load_point.hpp>
#include <wiixlaunch/game_version.hpp>
#include <wiixlaunch/loader/core_surface.hpp>
#include <wiixlaunch/loader/net_surface.hpp>
#include <wiixlaunch/loader/base_surfaces.hpp>

// Game module registration, if present in the tree.
#if __has_include(<wiixlaunch/module.hpp>)
#include <wiixlaunch/module.hpp>
#define WIIXL_HAVE_GAME_MODULE 1
#endif

// Optional graphics backend for BotW.
#if __has_include(<wiixlaunch/botw/botw.hpp>) && !defined(WIIXL_NO_DEMO)
#include <wiixlaunch/botw/botw.hpp>
#define WIIXL_BOTW_DEMO 1
using namespace WiiXLaunch::BotW;
#endif

// Entry point called once at plugin/module load. Install your hooks here.
extern "C" void WiiXLaunch_Init() {
    static bool initialized = false;
    if (initialized) return;
    initialized = true;

#if WIIXL_WIIU
    if (!WiiXLaunch::Backend::InitWiiUBackend()) return;
#elif WIIXL_CEMU
    if (!WiiXLaunch::Backend::InitCemuBackend()) return;
#endif

    WIIXL_LOG("WiiXLaunch: init OK");

    // Detect running game version before installing hooks or patches.
    WiiXLaunch::GameVersion::Detect();

    // Register surfaces: core, networking, and base services.
    WiiXLaunch::Core::Register();
    WiiXLaunch::NetSurface::Register();
    WiiXLaunch::BaseSurfaces::RegisterAll();

#if WIIXL_HAVE_GAME_MODULE
    WIIXL_LOG("WiiXLaunch: game module '%s'", WiiXLaunch::GameModule::kName);
    WiiXLaunch::GameModule::Register();
#else
    WIIXL_LOG("WiiXLaunch: no game module in this build - base surfaces only.");
#endif

    WiiXLaunch::Surface::LogRegistered();

    // Probe filesystem availability at the entry hook.
    WiiXLaunch::LoadPoint::Probe("entry-hook");

    // System clock check.
    char clock[20];
    WiiXLaunch::Time::FormatNow(clock, sizeof(clock));
    WIIXL_LOG("WiiXLaunch: system clock %s", clock);

#if WIIXL_BOTW_DEMO
#if WIIXL_SWITCH
    NVN::Init();
#elif WIIXL_CEMU
    GX2::Init();
#endif
#endif // WIIXL_BOTW_DEMO
}
