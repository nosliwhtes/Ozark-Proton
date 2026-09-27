/* Build stub.
 *
 * patches/lsteamclient/0010-lsteamclient-maintain-wayland-overlay-controller-focus.patch
 * includes this header and calls overlay_focus::sync() from unixlib.cpp, and
 * overlay_bridge/tests/steam-focus-investigation.md says the header is
 * "maintained directly in the repository". Upstream GE-Proton master never
 * committed it (verified absent on origin/master at 74177a0 and in the fork).
 *
 * Shipping a no-op keeps the build identical to released GE-Proton behavior:
 * the Wayland overlay controller-focus recovery is not implemented anywhere,
 * so this adds no new behavior. Replace this file with the real adapter when
 * that implementation lands.
 */
#pragma once

#include <stdint.h>

namespace overlay_focus
{
static inline void sync( int32_t /*pipe*/ ) {}
}
