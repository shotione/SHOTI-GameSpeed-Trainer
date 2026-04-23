/*
 * winmm_proxy.c  —  DL1 Speed Trainer  (proxy DLL)
 *
 * Build:
 *   cl /nologo /LD /O2 /MD /wd4273 winmm_proxy.c /Fe:winmm.dll /link /DEF:winmm.def kernel32.lib
 *
 * Do NOT #include <mmsystem.h> — the Win10 SDK 26100 headers declare
 * several MCI/driver functions with incompatible linkage specs (C2375).
 * We define the minimum types ourselves and let the .def file handle exports.
 */

#define WIN32_LEAN_AND_MEAN
#include <windows.h>

/* ─── Suppress C4273 "inconsistent dll linkage" for timing funcs
       that windows.h pulls in via timeapi.h ─────────────────────── */
#pragma warning(disable: 4273)

/* ═══════════════════════════════════════════════════════════════════
   Minimal mm type definitions  (no mmsystem.h)
   All struct/caps pointer params use VP (void*) — stubs just forward
   them; exact struct layout doesn't matter here.
   ═══════════════════════════════════════════════════════════════════ */
typedef UINT      MMRESULT;
typedef DWORD     FOURCC;
typedef DWORD     MCIERROR;
typedef UINT      MCIDEVICEID;

typedef HANDLE    HWAVEOUT,  *LPHWAVEOUT;
typedef HANDLE    HWAVEIN,   *LPHWAVEIN;
typedef HANDLE    HMIDI;
typedef HANDLE    HMIDIOUT,  *LPHMIDIOUT;
typedef HANDLE    HMIDIIN,   *LPHMIDIIN;
typedef HANDLE    HMIDISTRM, *LPHMIDISTRM;
typedef HANDLE    HMIXER,    *LPHMIXER;
typedef HANDLE    HMIXEROBJ;
typedef HANDLE    HMMIO;
typedef HANDLE    HDRVR;

#define VP void*   /* opaque struct/caps pointer — type doesn't matter in stubs */

/* ═══════════════════════════════════════════════════════════════════
   Stub macros
   No __declspec(dllexport) — exports are listed in winmm.def
   ═══════════════════════════════════════════════════════════════════ */
#define STUB(ret, name, sig, call) \
    typedef ret (WINAPI *pfn_##name) sig; \
    static pfn_##name g_##name; \
    ret WINAPI name sig { return g_##name ? g_##name call : (ret)0; }

#define STUB_V(name, sig, call) \
    typedef void (WINAPI *pfn_##name) sig; \
    static pfn_##name g_##name; \
    void WINAPI name sig { if (g_##name) g_##name call; }

/* Real winmm handle + GetProcAddress helper */
static HMODULE g_real = NULL;
#define GP(n)  g_##n = (pfn_##n)GetProcAddress(g_real, #n)


/* ═══════════════════════════════════════════════════════════════════
   TIMING STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT, timeGetDevCaps,    (VP a, UINT b),                                              (a,b))
STUB(MMRESULT, timeBeginPeriod,   (UINT a),                                                    (a))
STUB(MMRESULT, timeEndPeriod,     (UINT a),                                                    (a))
STUB(MMRESULT, timeGetSystemTime, (VP a, UINT b),                                              (a,b))
STUB(MMRESULT, timeKillEvent,     (UINT a),                                                    (a))
STUB(MMRESULT, timeSetEvent,      (UINT a, UINT b, DWORD_PTR c, DWORD_PTR d, UINT e),          (a,b,c,d,e))

/* ═══════════════════════════════════════════════════════════════════
   MMIO STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT,  mmioAdvance,         (HMMIO a, VP b, UINT c),                                  (a,b,c))
STUB(MMRESULT,  mmioAscend,          (HMMIO a, VP b, UINT c),                                  (a,b,c))
STUB(MMRESULT,  mmioClose,           (HMMIO a, UINT b),                                        (a,b))
STUB(MMRESULT,  mmioCreateChunk,     (HMMIO a, VP b, UINT c),                                  (a,b,c))
STUB(MMRESULT,  mmioDescend,         (HMMIO a, VP b, VP c, UINT d),                            (a,b,c,d))
STUB(MMRESULT,  mmioFlush,           (HMMIO a, UINT b),                                        (a,b))
STUB(MMRESULT,  mmioGetInfo,         (HMMIO a, VP b, UINT c),                                  (a,b,c))
STUB(DWORD_PTR, mmioInstallIOProcA,  (FOURCC a, DWORD_PTR b, DWORD c),                         (a,b,c))
STUB(DWORD_PTR, mmioInstallIOProcW,  (FOURCC a, DWORD_PTR b, DWORD c),                         (a,b,c))
STUB(HMMIO,     mmioOpenA,           (LPSTR a, VP b, DWORD c),                                 (a,b,c))
STUB(HMMIO,     mmioOpenW,           (LPWSTR a, VP b, DWORD c),                                (a,b,c))
STUB(LONG,      mmioRead,            (HMMIO a, char* b, LONG c),                               (a,b,c))
STUB(MMRESULT,  mmioRenameA,         (LPCSTR a, LPCSTR b, VP c, DWORD d),                      (a,b,c,d))
STUB(MMRESULT,  mmioRenameW,         (LPCWSTR a, LPCWSTR b, VP c, DWORD d),                    (a,b,c,d))
STUB(LONG,      mmioSeek,            (HMMIO a, LONG b, int c),                                 (a,b,c))
STUB(LRESULT,   mmioSendMessage,     (HMMIO a, UINT b, LPARAM c, LPARAM d),                    (a,b,c,d))
STUB(MMRESULT,  mmioSetBuffer,       (HMMIO a, char* b, LONG c, UINT d),                       (a,b,c,d))
STUB(MMRESULT,  mmioSetInfo,         (HMMIO a, VP b, UINT c),                                  (a,b,c))
STUB(FOURCC,    mmioStringToFOURCCA, (LPCSTR a, UINT b),                                       (a,b))
STUB(FOURCC,    mmioStringToFOURCCW, (LPCWSTR a, UINT b),                                      (a,b))
STUB(LONG,      mmioWrite,           (HMMIO a, const char* b, LONG c),                         (a,b,c))

/* ═══════════════════════════════════════════════════════════════════
   WAVE OUT STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT, waveOutPause,           (HWAVEOUT a),                                                          (a))
STUB(MMRESULT, waveOutBreakLoop,       (HWAVEOUT a),                                                          (a))
STUB(MMRESULT, waveOutClose,           (HWAVEOUT a),                                                          (a))
STUB(MMRESULT, waveOutGetDevCapsA,     (UINT_PTR a, VP b, UINT c),                                            (a,b,c))
STUB(MMRESULT, waveOutGetDevCapsW,     (UINT_PTR a, VP b, UINT c),                                            (a,b,c))
STUB(MMRESULT, waveOutGetErrorTextA,   (MMRESULT a, LPSTR b, UINT c),                                        (a,b,c))
STUB(MMRESULT, waveOutGetErrorTextW,   (MMRESULT a, LPWSTR b, UINT c),                                       (a,b,c))
STUB(MMRESULT, waveOutGetID,           (HWAVEOUT a, UINT* b),                                                 (a,b))
STUB(UINT,     waveOutGetNumDevs,      (void),                                                                ())
STUB(MMRESULT, waveOutGetPitch,        (HWAVEOUT a, DWORD* b),                                                (a,b))
STUB(MMRESULT, waveOutGetPlaybackRate, (HWAVEOUT a, DWORD* b),                                                (a,b))
STUB(MMRESULT, waveOutGetPosition,     (HWAVEOUT a, VP b, UINT c),                                            (a,b,c))
STUB(MMRESULT, waveOutGetVolume,       (HWAVEOUT a, DWORD* b),                                                (a,b))
STUB(MMRESULT, waveOutMessage,         (HWAVEOUT a, UINT b, DWORD_PTR c, DWORD_PTR d),                        (a,b,c,d))
STUB(MMRESULT, waveOutOpen,            (LPHWAVEOUT a, UINT_PTR b, VP c, DWORD_PTR d, DWORD_PTR e, DWORD f),   (a,b,c,d,e,f))
STUB(MMRESULT, waveOutPrepareHeader,   (HWAVEOUT a, VP b, UINT c),                                            (a,b,c))
STUB(MMRESULT, waveOutReset,           (HWAVEOUT a),                                                          (a))
STUB(MMRESULT, waveOutRestart,         (HWAVEOUT a),                                                          (a))
STUB(MMRESULT, waveOutSetPitch,        (HWAVEOUT a, DWORD b),                                                 (a,b))
STUB(MMRESULT, waveOutSetPlaybackRate, (HWAVEOUT a, DWORD b),                                                 (a,b))
STUB(MMRESULT, waveOutSetVolume,       (HWAVEOUT a, DWORD b),                                                 (a,b))
STUB(MMRESULT, waveOutUnprepareHeader, (HWAVEOUT a, VP b, UINT c),                                            (a,b,c))
STUB(MMRESULT, waveOutWrite,           (HWAVEOUT a, VP b, UINT c),                                            (a,b,c))

/* ═══════════════════════════════════════════════════════════════════
   WAVE IN STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT, waveInAddBuffer,       (HWAVEIN a, VP b, UINT c),                                              (a,b,c))
STUB(MMRESULT, waveInClose,           (HWAVEIN a),                                                            (a))
STUB(MMRESULT, waveInGetDevCapsA,     (UINT_PTR a, VP b, UINT c),                                             (a,b,c))
STUB(MMRESULT, waveInGetDevCapsW,     (UINT_PTR a, VP b, UINT c),                                             (a,b,c))
STUB(MMRESULT, waveInGetErrorTextA,   (MMRESULT a, LPSTR b, UINT c),                                         (a,b,c))
STUB(MMRESULT, waveInGetErrorTextW,   (MMRESULT a, LPWSTR b, UINT c),                                        (a,b,c))
STUB(MMRESULT, waveInGetID,           (HWAVEIN a, UINT* b),                                                   (a,b))
STUB(UINT,     waveInGetNumDevs,      (void),                                                                 ())
STUB(MMRESULT, waveInGetPosition,     (HWAVEIN a, VP b, UINT c),                                              (a,b,c))
STUB(MMRESULT, waveInMessage,         (HWAVEIN a, UINT b, DWORD_PTR c, DWORD_PTR d),                          (a,b,c,d))
STUB(MMRESULT, waveInOpen,            (LPHWAVEIN a, UINT_PTR b, VP c, DWORD_PTR d, DWORD_PTR e, DWORD f),     (a,b,c,d,e,f))
STUB(MMRESULT, waveInPrepareHeader,   (HWAVEIN a, VP b, UINT c),                                              (a,b,c))
STUB(MMRESULT, waveInReset,           (HWAVEIN a),                                                            (a))
STUB(MMRESULT, waveInStart,           (HWAVEIN a),                                                            (a))
STUB(MMRESULT, waveInStop,            (HWAVEIN a),                                                            (a))
STUB(MMRESULT, waveInUnprepareHeader, (HWAVEIN a, VP b, UINT c),                                              (a,b,c))

/* ═══════════════════════════════════════════════════════════════════
   MIDI OUT STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT, midiOutCacheDrumPatches, (HMIDIOUT a, UINT b, WORD* c, UINT d),                  (a,b,c,d))
STUB(MMRESULT, midiOutCachePatches,     (HMIDIOUT a, UINT b, WORD* c, UINT d),                  (a,b,c,d))
STUB(MMRESULT, midiOutClose,            (HMIDIOUT a),                                            (a))
STUB(MMRESULT, midiOutGetDevCapsA,      (UINT_PTR a, VP b, UINT c),                             (a,b,c))
STUB(MMRESULT, midiOutGetDevCapsW,      (UINT_PTR a, VP b, UINT c),                             (a,b,c))
STUB(MMRESULT, midiOutGetErrorTextA,    (MMRESULT a, LPSTR b, UINT c),                          (a,b,c))
STUB(MMRESULT, midiOutGetErrorTextW,    (MMRESULT a, LPWSTR b, UINT c),                         (a,b,c))
STUB(MMRESULT, midiOutGetID,            (HMIDIOUT a, UINT* b),                                  (a,b))
STUB(UINT,     midiOutGetNumDevs,       (void),                                                  ())
STUB(MMRESULT, midiOutGetVolume,        (HMIDIOUT a, DWORD* b),                                 (a,b))
STUB(MMRESULT, midiOutLongMsg,          (HMIDIOUT a, VP b, UINT c),                             (a,b,c))
STUB(MMRESULT, midiOutMessage,          (HMIDIOUT a, UINT b, DWORD_PTR c, DWORD_PTR d),         (a,b,c,d))
STUB(MMRESULT, midiOutOpen,             (LPHMIDIOUT a, UINT_PTR b, DWORD_PTR c, DWORD_PTR d, DWORD e),(a,b,c,d,e))
STUB(MMRESULT, midiOutPrepareHeader,    (HMIDIOUT a, VP b, UINT c),                             (a,b,c))
STUB(MMRESULT, midiOutReset,            (HMIDIOUT a),                                            (a))
STUB(MMRESULT, midiOutSetVolume,        (HMIDIOUT a, DWORD b),                                  (a,b))
STUB(MMRESULT, midiOutShortMsg,         (HMIDIOUT a, DWORD b),                                  (a,b))
STUB(MMRESULT, midiOutUnprepareHeader,  (HMIDIOUT a, VP b, UINT c),                             (a,b,c))

/* ═══════════════════════════════════════════════════════════════════
   MIDI IN STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT, midiInAddBuffer,       (HMIDIIN a, VP b, UINT c),                                (a,b,c))
STUB(MMRESULT, midiInClose,           (HMIDIIN a),                                               (a))
STUB(MMRESULT, midiInGetDevCapsA,     (UINT_PTR a, VP b, UINT c),                               (a,b,c))
STUB(MMRESULT, midiInGetDevCapsW,     (UINT_PTR a, VP b, UINT c),                               (a,b,c))
STUB(MMRESULT, midiInGetErrorTextA,   (MMRESULT a, LPSTR b, UINT c),                            (a,b,c))
STUB(MMRESULT, midiInGetErrorTextW,   (MMRESULT a, LPWSTR b, UINT c),                           (a,b,c))
STUB(MMRESULT, midiInGetID,           (HMIDIIN a, UINT* b),                                     (a,b))
STUB(UINT,     midiInGetNumDevs,      (void),                                                    ())
STUB(MMRESULT, midiInMessage,         (HMIDIIN a, UINT b, DWORD_PTR c, DWORD_PTR d),             (a,b,c,d))
STUB(MMRESULT, midiInOpen,            (LPHMIDIIN a, UINT_PTR b, DWORD_PTR c, DWORD_PTR d, DWORD e),(a,b,c,d,e))
STUB(MMRESULT, midiInPrepareHeader,   (HMIDIIN a, VP b, UINT c),                                (a,b,c))
STUB(MMRESULT, midiInReset,           (HMIDIIN a),                                               (a))
STUB(MMRESULT, midiInStart,           (HMIDIIN a),                                               (a))
STUB(MMRESULT, midiInStop,            (HMIDIIN a),                                               (a))
STUB(MMRESULT, midiInUnprepareHeader, (HMIDIIN a, VP b, UINT c),                                (a,b,c))

/* ═══════════════════════════════════════════════════════════════════
   MIDI STREAM / CONNECT STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT, midiConnect,        (HMIDI a, HMIDIOUT b, VP c),                                              (a,b,c))
STUB(MMRESULT, midiDisconnect,     (HMIDI a, HMIDIOUT b, VP c),                                              (a,b,c))
STUB(MMRESULT, midiStreamClose,    (HMIDISTRM a),                                                             (a))
STUB(MMRESULT, midiStreamOpen,     (LPHMIDISTRM a, UINT* b, DWORD c, DWORD_PTR d, DWORD_PTR e, DWORD f),     (a,b,c,d,e,f))
STUB(MMRESULT, midiStreamOut,      (HMIDISTRM a, VP b, UINT c),                                              (a,b,c))
STUB(MMRESULT, midiStreamPause,    (HMIDISTRM a),                                                             (a))
STUB(MMRESULT, midiStreamPosition, (HMIDISTRM a, VP b, UINT c),                                              (a,b,c))
STUB(MMRESULT, midiStreamProperty, (HMIDISTRM a, BYTE* b, DWORD c),                                          (a,b,c))
STUB(MMRESULT, midiStreamRestart,  (HMIDISTRM a),                                                             (a))
STUB(MMRESULT, midiStreamStop,     (HMIDISTRM a),                                                             (a))

/* ═══════════════════════════════════════════════════════════════════
   MIXER STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT, mixerClose,             (HMIXER a),                                                            (a))
STUB(MMRESULT, mixerGetControlDetailsA,(HMIXEROBJ a, VP b, DWORD c),                                         (a,b,c))
STUB(MMRESULT, mixerGetControlDetailsW,(HMIXEROBJ a, VP b, DWORD c),                                         (a,b,c))
STUB(MMRESULT, mixerGetDevCapsA,       (UINT_PTR a, VP b, UINT c),                                           (a,b,c))
STUB(MMRESULT, mixerGetDevCapsW,       (UINT_PTR a, VP b, UINT c),                                           (a,b,c))
STUB(MMRESULT, mixerGetID,             (HMIXEROBJ a, UINT* b, DWORD c),                                      (a,b,c))
STUB(MMRESULT, mixerGetLineControlsA,  (HMIXEROBJ a, VP b, DWORD c),                                         (a,b,c))
STUB(MMRESULT, mixerGetLineControlsW,  (HMIXEROBJ a, VP b, DWORD c),                                         (a,b,c))
STUB(MMRESULT, mixerGetLineInfoA,      (HMIXEROBJ a, VP b, DWORD c),                                         (a,b,c))
STUB(MMRESULT, mixerGetLineInfoW,      (HMIXEROBJ a, VP b, DWORD c),                                         (a,b,c))
STUB(UINT,     mixerGetNumDevs,        (void),                                                                ())
STUB(DWORD,    mixerMessage,           (HMIXER a, UINT b, DWORD_PTR c, DWORD_PTR d),                         (a,b,c,d))
STUB(MMRESULT, mixerOpen,              (LPHMIXER a, UINT b, DWORD_PTR c, DWORD_PTR d, DWORD e),               (a,b,c,d,e))
STUB(MMRESULT, mixerSetControlDetails, (HMIXEROBJ a, VP b, DWORD c),                                         (a,b,c))

/* ═══════════════════════════════════════════════════════════════════
   MCI STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(BOOL,       mciDriverNotify,             (HWND a, MCIDEVICEID b, UINT c),                               (a,b,c))
STUB(UINT,       mciDriverYield,              (MCIDEVICEID a),                                                (a))
STUB(BOOL,       mciExecute,                  (LPCSTR a),                                                     (a))
STUB(BOOL,       mciFreeCommandResource,       (UINT a),                                                      (a))
STUB(HANDLE,     mciGetCreatorTask,            (MCIDEVICEID a),                                               (a))
STUB(MCIDEVICEID,mciGetDeviceIDA,              (LPCSTR a),                                                    (a))
STUB(MCIDEVICEID,mciGetDeviceIDFromElementIDA, (DWORD a, LPCSTR b),                                          (a,b))
STUB(MCIDEVICEID,mciGetDeviceIDFromElementIDW, (DWORD a, LPCWSTR b),                                         (a,b))
STUB(MCIDEVICEID,mciGetDeviceIDW,              (LPCWSTR a),                                                   (a))
STUB(DWORD_PTR,  mciGetDriverData,             (MCIDEVICEID a),                                               (a))
STUB(BOOL,       mciGetErrorStringA,           (MCIERROR a, LPSTR b, UINT c),                                 (a,b,c))
STUB(BOOL,       mciGetErrorStringW,           (MCIERROR a, LPWSTR b, UINT c),                                (a,b,c))
STUB(DWORD_PTR,  mciGetYieldProc,              (MCIDEVICEID a, DWORD* b),                                     (a,b))
STUB(UINT,       mciLoadCommandResource,        (HINSTANCE a, LPCWSTR b, UINT c),                             (a,b,c))
STUB(MCIERROR,   mciSendCommandA,              (MCIDEVICEID a, UINT b, DWORD_PTR c, DWORD_PTR d),             (a,b,c,d))
STUB(MCIERROR,   mciSendCommandW,              (MCIDEVICEID a, UINT b, DWORD_PTR c, DWORD_PTR d),             (a,b,c,d))
STUB(MCIERROR,   mciSendStringA,               (LPCSTR a, LPSTR b, UINT c, HWND d),                           (a,b,c,d))
STUB(MCIERROR,   mciSendStringW,               (LPCWSTR a, LPWSTR b, UINT c, HWND d),                         (a,b,c,d))
STUB(BOOL,       mciSetDriverData,             (MCIDEVICEID a, DWORD_PTR b),                                  (a,b))
STUB(BOOL,       mciSetYieldProc,              (MCIDEVICEID a, DWORD_PTR b, DWORD c),                         (a,b,c))

/* ═══════════════════════════════════════════════════════════════════
   AUX / JOYSTICK STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(MMRESULT, auxGetDevCapsA,    (UINT_PTR a, VP b, UINT c),        (a,b,c))
STUB(MMRESULT, auxGetDevCapsW,    (UINT_PTR a, VP b, UINT c),        (a,b,c))
STUB(UINT,     auxGetNumDevs,     (void),                             ())
STUB(MMRESULT, auxGetVolume,      (UINT a, DWORD* b),                 (a,b))
STUB(MMRESULT, auxOutMessage,     (UINT a, UINT b, DWORD_PTR c, DWORD_PTR d),(a,b,c,d))
STUB(MMRESULT, auxSetVolume,      (UINT a, DWORD b),                  (a,b))
STUB(MMRESULT, joyConfigChanged,  (DWORD a),                          (a))
STUB(MMRESULT, joyGetDevCapsA,    (UINT_PTR a, VP b, UINT c),        (a,b,c))
STUB(MMRESULT, joyGetDevCapsW,    (UINT_PTR a, VP b, UINT c),        (a,b,c))
STUB(UINT,     joyGetNumDevs,     (void),                             ())
STUB(MMRESULT, joyGetPos,         (UINT a, VP b),                     (a,b))
STUB(MMRESULT, joyGetPosEx,       (UINT a, VP b),                     (a,b))
STUB(MMRESULT, joyGetThreshold,   (UINT a, UINT* b),                  (a,b))
STUB(MMRESULT, joyReleaseCapture, (UINT a),                           (a))
STUB(MMRESULT, joySetCapture,     (HWND a, UINT b, UINT c, BOOL d),   (a,b,c,d))
STUB(MMRESULT, joySetThreshold,   (UINT a, UINT b),                   (a,b))

/* ═══════════════════════════════════════════════════════════════════
   DRIVER / SOUND / MISC STUBS
   ═══════════════════════════════════════════════════════════════════ */
STUB(LRESULT, CloseDriver,         (HDRVR a, LPARAM b, LPARAM c),                                    (a,b,c))
STUB(LRESULT, DefDriverProc,       (DWORD_PTR a, HDRVR b, UINT c, LPARAM d, LPARAM e),               (a,b,c,d,e))
STUB(BOOL,    DriverCallback,      (DWORD_PTR a, DWORD b, HDRVR c, DWORD d, DWORD_PTR e, DWORD_PTR f, DWORD_PTR g),(a,b,c,d,e,f,g))
STUB(HMODULE, DrvGetModuleHandle,  (HDRVR a),                                                         (a))
STUB(HMODULE, GetDriverModuleHandle,(HDRVR a),                                                        (a))
STUB(HDRVR,   OpenDriver,          (LPCWSTR a, LPCWSTR b, LPARAM c),                                  (a,b,c))
STUB(BOOL,    PlaySound,           (LPCSTR a, HMODULE b, DWORD c),                                    (a,b,c))
STUB(BOOL,    PlaySoundA,          (LPCSTR a, HMODULE b, DWORD c),                                    (a,b,c))
STUB(BOOL,    PlaySoundW,          (LPCWSTR a, HMODULE b, DWORD c),                                   (a,b,c))
STUB(LRESULT, SendDriverMessage,   (HDRVR a, UINT b, LPARAM c, LPARAM d),                             (a,b,c,d))
STUB(BOOL,    sndPlaySoundA,       (LPCSTR a, UINT b),                                                (a,b))
STUB(BOOL,    sndPlaySoundW,       (LPCWSTR a, UINT b),                                               (a,b))
STUB(UINT,    mmsystemGetVersion,  (void),                                                             ())
STUB(BOOL,    NotifyCallbackData,  (DWORD_PTR a, DWORD b, HDRVR c, DWORD d, DWORD_PTR e, DWORD_PTR f, DWORD_PTR g),(a,b,c,d,e,f,g))
STUB(DWORD,   mmGetCurrentTask,    (void),                                                             ())
STUB(UINT,    mmTaskCreate,        (DWORD_PTR a, HANDLE* b, DWORD_PTR c),                             (a,b,c))
STUB(BOOL,    mmTaskSignal,        (DWORD a),                                                          (a))
STUB_V(       mmTaskBlock,         (DWORD a),                                                          (a))
STUB_V(       mmTaskYield,         (void),                                                             ())


/* ═══════════════════════════════════════════════════════════════════
   SHARED MEMORY  (Python trainer writes speed float here)
   ═══════════════════════════════════════════════════════════════════ */
#define SHM_NAME  L"DL1Hook_v3"
#define SHM_SIZE  16

static HANDLE  g_shm         = NULL;
static float  *g_pSpeed      = NULL;
static float   g_local_speed = 1.0f;

/* ═══════════════════════════════════════════════════════════════════
   OUR timeGetTime  —  the speed hook
   ═══════════════════════════════════════════════════════════════════ */
typedef DWORD (WINAPI *pfn_timeGetTime)(void);
static  pfn_timeGetTime g_timeGetTime = NULL;

static DWORD s_last  = 0;
static DWORD s_accum = 0;
static float s_frac  = 0.0f;

DWORD WINAPI timeGetTime(void)
{
    if (!g_timeGetTime) return 0;

    DWORD real = g_timeGetTime();
    float spd  = g_pSpeed ? *g_pSpeed : g_local_speed;

    /* At 1.0x: pass through real time and re-sync accumulator */
    if (spd == 1.0f) {
        s_last  = real;
        s_accum = real;
        s_frac  = 0.0f;
        return real;
    }

    /* First call at non-1x */
    if (s_last == 0) {
        s_last  = real;
        s_accum = real;
        s_frac  = 0.0f;
        return real;
    }

    /* Fractional accumulator fixes precision loss when engine calls
       timeGetTime every 1ms. Without this, at spd=0.25 and delta=1ms:
       (DWORD)(1 * 0.25) = 0 -> time never advances below 1.0x.
       The fraction carries the sub-ms remainder into the next call. */
    float scaled = (float)(real - s_last) * spd + s_frac;
    DWORD add    = (DWORD)scaled;
    s_frac       = scaled - (float)add;

    s_last   = real;
    s_accum += add;
    return s_accum;
}

/* ═══════════════════════════════════════════════════════════════════
   SetSpeed  —  Python can call this directly (alternative to SHM)
   ═══════════════════════════════════════════════════════════════════ */
void WINAPI SetSpeed(float spd)
{
    if (g_pSpeed) *g_pSpeed    = spd;
    else           g_local_speed = spd;
}

/* ═══════════════════════════════════════════════════════════════════
   DllMain
   ═══════════════════════════════════════════════════════════════════ */
BOOL WINAPI DllMain(HINSTANCE hInst, DWORD reason, LPVOID reserved)
{
    (void)reserved;

    if (reason == DLL_PROCESS_ATTACH)
    {
        DisableThreadLibraryCalls(hInst);

        g_real = LoadLibraryA("winmm_real.dll");
        if (!g_real) {
            MessageBoxA(NULL,
                "DL1 Speed Trainer:\n\nwinmm_real.dll not found in game folder!\n"
                "Re-run build_proxy.bat.",
                "Speed Trainer", MB_ICONERROR | MB_TOPMOST);
            return FALSE;
        }

        /* ── Resolve all function pointers ── */
        GP(timeGetTime); GP(timeGetDevCaps); GP(timeBeginPeriod);
        GP(timeEndPeriod); GP(timeGetSystemTime); GP(timeKillEvent); GP(timeSetEvent);

        GP(mmioAdvance); GP(mmioAscend); GP(mmioClose); GP(mmioCreateChunk);
        GP(mmioDescend); GP(mmioFlush); GP(mmioGetInfo); GP(mmioInstallIOProcA);
        GP(mmioInstallIOProcW); GP(mmioOpenA); GP(mmioOpenW); GP(mmioRead);
        GP(mmioRenameA); GP(mmioRenameW); GP(mmioSeek); GP(mmioSendMessage);
        GP(mmioSetBuffer); GP(mmioSetInfo); GP(mmioStringToFOURCCA);
        GP(mmioStringToFOURCCW); GP(mmioWrite);

        GP(waveOutPause); GP(waveOutBreakLoop); GP(waveOutClose); GP(waveOutGetDevCapsA);
        GP(waveOutGetDevCapsW); GP(waveOutGetErrorTextA); GP(waveOutGetErrorTextW);
        GP(waveOutGetID); GP(waveOutGetNumDevs); GP(waveOutGetPitch);
        GP(waveOutGetPlaybackRate); GP(waveOutGetPosition); GP(waveOutGetVolume);
        GP(waveOutMessage); GP(waveOutOpen); GP(waveOutPrepareHeader);
        GP(waveOutReset); GP(waveOutRestart); GP(waveOutSetPitch);
        GP(waveOutSetPlaybackRate); GP(waveOutSetVolume); GP(waveOutUnprepareHeader);
        GP(waveOutWrite);

        GP(waveInAddBuffer); GP(waveInClose); GP(waveInGetDevCapsA);
        GP(waveInGetDevCapsW); GP(waveInGetErrorTextA); GP(waveInGetErrorTextW);
        GP(waveInGetID); GP(waveInGetNumDevs); GP(waveInGetPosition);
        GP(waveInMessage); GP(waveInOpen); GP(waveInPrepareHeader);
        GP(waveInReset); GP(waveInStart); GP(waveInStop); GP(waveInUnprepareHeader);

        GP(midiOutCacheDrumPatches); GP(midiOutCachePatches); GP(midiOutClose);
        GP(midiOutGetDevCapsA); GP(midiOutGetDevCapsW); GP(midiOutGetErrorTextA);
        GP(midiOutGetErrorTextW); GP(midiOutGetID); GP(midiOutGetNumDevs);
        GP(midiOutGetVolume); GP(midiOutLongMsg); GP(midiOutMessage);
        GP(midiOutOpen); GP(midiOutPrepareHeader); GP(midiOutReset);
        GP(midiOutSetVolume); GP(midiOutShortMsg); GP(midiOutUnprepareHeader);

        GP(midiInAddBuffer); GP(midiInClose); GP(midiInGetDevCapsA);
        GP(midiInGetDevCapsW); GP(midiInGetErrorTextA); GP(midiInGetErrorTextW);
        GP(midiInGetID); GP(midiInGetNumDevs); GP(midiInMessage); GP(midiInOpen);
        GP(midiInPrepareHeader); GP(midiInReset); GP(midiInStart); GP(midiInStop);
        GP(midiInUnprepareHeader);

        GP(midiConnect); GP(midiDisconnect); GP(midiStreamClose); GP(midiStreamOpen);
        GP(midiStreamOut); GP(midiStreamPause); GP(midiStreamPosition);
        GP(midiStreamProperty); GP(midiStreamRestart); GP(midiStreamStop);

        GP(mixerClose); GP(mixerGetControlDetailsA); GP(mixerGetControlDetailsW);
        GP(mixerGetDevCapsA); GP(mixerGetDevCapsW); GP(mixerGetID);
        GP(mixerGetLineControlsA); GP(mixerGetLineControlsW);
        GP(mixerGetLineInfoA); GP(mixerGetLineInfoW); GP(mixerGetNumDevs);
        GP(mixerMessage); GP(mixerOpen); GP(mixerSetControlDetails);

        GP(mciDriverNotify); GP(mciDriverYield); GP(mciExecute);
        GP(mciFreeCommandResource); GP(mciGetCreatorTask); GP(mciGetDeviceIDA);
        GP(mciGetDeviceIDFromElementIDA); GP(mciGetDeviceIDFromElementIDW);
        GP(mciGetDeviceIDW); GP(mciGetDriverData); GP(mciGetErrorStringA);
        GP(mciGetErrorStringW); GP(mciGetYieldProc); GP(mciLoadCommandResource);
        GP(mciSendCommandA); GP(mciSendCommandW); GP(mciSendStringA);
        GP(mciSendStringW); GP(mciSetDriverData); GP(mciSetYieldProc);

        GP(auxGetDevCapsA); GP(auxGetDevCapsW); GP(auxGetNumDevs);
        GP(auxGetVolume); GP(auxOutMessage); GP(auxSetVolume);
        GP(joyConfigChanged); GP(joyGetDevCapsA); GP(joyGetDevCapsW);
        GP(joyGetNumDevs); GP(joyGetPos); GP(joyGetPosEx); GP(joyGetThreshold);
        GP(joyReleaseCapture); GP(joySetCapture); GP(joySetThreshold);

        GP(CloseDriver); GP(DefDriverProc); GP(DriverCallback);
        GP(DrvGetModuleHandle); GP(GetDriverModuleHandle); GP(OpenDriver);
        GP(PlaySound); GP(PlaySoundA); GP(PlaySoundW); GP(SendDriverMessage);
        GP(sndPlaySoundA); GP(sndPlaySoundW); GP(mmsystemGetVersion);
        GP(NotifyCallbackData); GP(mmGetCurrentTask);
        GP(mmTaskCreate); GP(mmTaskSignal); GP(mmTaskBlock); GP(mmTaskYield);

        /* ── Shared memory (Python trainer writes speed here) ── */
        g_shm = CreateFileMappingW(INVALID_HANDLE_VALUE, NULL,
                                   PAGE_READWRITE, 0, SHM_SIZE, SHM_NAME);
        if (g_shm) {
            g_pSpeed = (float*)MapViewOfFile(g_shm, FILE_MAP_ALL_ACCESS, 0, 0, SHM_SIZE);
            if (g_pSpeed) *g_pSpeed = 1.0f;
        }
    }
    else if (reason == DLL_PROCESS_DETACH)
    {
        if (g_pSpeed) { UnmapViewOfFile(g_pSpeed); g_pSpeed = NULL; }
        if (g_shm)    { CloseHandle(g_shm);         g_shm    = NULL; }
        if (g_real)   { FreeLibrary(g_real);         g_real   = NULL; }
    }

    return TRUE;
}
