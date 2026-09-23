# Pending patch ledger

This ledger records upstream refs found in patch headers. "unverified" means the upstream page was not fetched or did not prove the fix landed. Do not drop a patch based on this file.

| file | applied by protonprep | upstream ref | claims | landing |
| ---- | --------------------- | ------------ | ------ | ------- |
| 0001-decouple-wineopenxr-from-steamvr-and-integrate-it-in.patch | explicit | none in header | decouple wineopenxr from steamvr, integrate into wine | no-upstream-ref |
| 0001-server-Dynamically-relocate-.exes-by-default-too.patch | explicit | none in header | dynamically relocate .exes by default too | no-upstream-ref |
| 0002-ntdll-allow-disabling-executable-ASLR.patch | explicit | none in header | allow disabling executable ASLR per process | no-upstream-ref |
| 0009-HACK-kernel32-Spoof-GetProcAddress-of-KiUserApcDispa.patch | explicit | none in header | spoof GetProcAddress of KiUserApcDispatcher/KiUserCallbackDispatcher | no-upstream-ref |
| crypt32-pfx-record-machine-keyset-in-prov-info.patch | explicit | none in header | record machine keyset in PFX provider info | no-upstream-ref |
| crypt32-pfx-use-the-container-key-spec.patch | explicit | none in header | use the container's actual key spec | no-upstream-ref |
| crypt32-reject-ncrypt-only-private-keys.patch | explicit | none in header | reject unsupported NCrypt-only private-key requests | no-upstream-ref |
| crypt32-wc3-accept-legacy-chain-engine-config.patch | explicit | https://bugs.winehq.org/show_bug.cgi?id=59600 | accept CERT_CHAIN_ENGINE_CONFIG without dwExclusiveFlags | unverified |
| crypt32-wc3-check-exclusive-flags-size.patch | explicit | none in header | check size before accessing dwExclusiveFlags | no-upstream-ref |
| crypt32-wc3-modern-chain-engine-config.patch | explicit | https://bugs.winehq.org/show_bug.cgi?id=59531 | update CERT_CHAIN_ENGINE_CONFIG definition | unverified |
| crypt32-wc3-preserve-exclusive-root-and-test-layouts.patch | explicit | none in header | preserve legacy exclusive roots, test chain config layouts | no-upstream-ref |
| crypt32-wc3-trace-chain-engine-config.patch | explicit | none in header | trace CERT_CHAIN_ENGINE_CONFIG fields | no-upstream-ref |
| icuuc-icuin-forwarder-dlls.patch | explicit | none in header | add icuuc/icuin forwarder DLLs | no-upstream-ref |
| kernel32-refresh-power-status-asynchronously.patch | explicit | none in header | refresh system power status asynchronously | no-upstream-ref |
| NCryptDecrypt_implementation.patch | explicit | none in header | implement NCryptDecrypt | no-upstream-ref |
| ntdll-keep-builtin-amd-ags-ahead-of-version-heuristic.patch | explicit | Wine commit e87e9626a64893481fd45b875360c41717452f0b | keep builtin amd_ags_x64 ahead of version heuristic | unverified |
| ntdll-prefer-native-version-resource-heuristics.patch | explicit | Wine commit a31ec8da9572672e04ae46792a398da942649875 | prefer native DLLs via version-resource heuristics | unverified |
| ntdll-remove-redundant-packed-split-lock.patch | explicit | none in header | remove redundant packed-code split lock | no-upstream-ref |
| ntdll-reserve-top-down-space-for-large-address-aware-wow64.patch | explicit | https://bugs.winehq.org/show_bug.cgi?id=58698 | reserve top-down space for large-address-aware WoW64 | unverified |
| ntdll-retry-native-view-allocation-with-effective-range.patch | explicit | none in header | retry native-view allocation with effective range | no-upstream-ref |
| ole32-clipboard-stale-handle-1-tests.patch | explicit | https://bugs.winehq.org/show_bug.cgi?id=59519 | test OLE clipboard reuse across STA threads | unverified |
| ole32-clipboard-stale-handle-2-fix.patch | explicit | https://bugs.winehq.org/show_bug.cgi?id=59519 | validate cached clipboard window handle | unverified |
| registry_RRF_RT_REG_SZ-RRF_RT_REG_EXPAND_SZ.patch | explicit | none in header | fix RegGetValueW dwFlags validation | no-upstream-ref |
| secur32-fallback-without-no-shuffle-extensions.patch | explicit | none in header | fall back when GnuTLS lacks NO_SHUFFLE_EXTENSIONS | no-upstream-ref |
| unity_crash_hotfix.patch | explicit | none in header | Unity crash hotfix (DXGI debug interface) | no-upstream-ref |
| urlmon-pump-thread-user-messages-during-synchronous-bind.patch | explicit | none in header | pump thread user messages during synchronous binds | no-upstream-ref |
| version-GetFileVersionInfoByHandle-stub.patch | explicit | none in header | add GetFileVersionInfoByHandle stub | no-upstream-ref |
| win32u-limit-extra-swapchain-image-to-doom.patch | explicit | none in header | limit extra swapchain image workaround to DOOM | no-upstream-ref |
| win32u-share-selected-cursors-across-processes.patch | explicit | none in header | share selected cursor images across processes | no-upstream-ref |
| win32u-use-three-image-present-modes-for-hades-wayland.patch | explicit | https://gitlab.freedesktop.org/mesa/mesa/-/blob/mesa-26.2.1/src/vulkan/wsi/wsi_common_wayland.c | per-present-mode image limits for Hades on Wayland | unverified |
| win32u-use-three-image-present-modes-for-path-of-exile.patch | explicit | none in header | three-image present modes for Path of Exile on Wayland | no-upstream-ref |
| wineboot-create-sqm-machine-id.patch | explicit | https://learn.microsoft.com/en-us/openspecs/windows_protocols/ms-sqmcs2/0442f736-8670-4ae4-8651-5732f3ba18dd | initialize SQM client machine identifier | unverified |
| winebus-diablo-iv-dualsense-edge-identity.patch | explicit | https://github.com/torvalds/linux/blob/master/drivers/hid/hid-playstation.c | expose DualSense Edge as DualSense for Diablo IV | unverified |
| winebus-switch-pro-xinput-identity.patch | explicit | none in header | give mapped Switch Pro controllers an XInput identity | no-upstream-ref |
| wined3d-preserve-runtime-opengl-gpu-description.patch | explicit | none in header | preserve runtime OpenGL GPU description | no-upstream-ref |
| winex11-keep-forza-background-windows-unmapped-on-wlroots.patch | explicit | Wine commit 0dabe4b3e9c | keep Forza backing windows unmapped on wlroots | unverified |
| winex11-use-x11-drawables-for-steam-opengl-overlay.patch | explicit | none in header | use X11 drawables with Steam OpenGL overlay | no-upstream-ref |
| ws2_32-validate-connect-address.patch | explicit | none in header | validate Winsock connect address arguments | no-upstream-ref |
