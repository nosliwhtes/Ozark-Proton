"""Offline behavioral checks for overlay patch 0075 against the pinned Wine source.

Run with OZARK_WINE_SOURCE pointing to an existing Wine Git object database.
Only temporary fixture files are changed; no Wine/Proton build is performed.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]

def function(source, name):
    pos = source.index(name + '(')
    start = source.rfind('\n', 0, pos) + 1
    opening = source.index('{', pos)
    depth = 1
    end = opening + 1
    while depth:
        depth += (source[end] == '{') - (source[end] == '}')
        end += 1
    return source[start:end]

PREFIX = r'''
#include <assert.h>
#include <limits.h>
#include <stddef.h>
#include <stdio.h>
#include <string.h>
typedef long long LONGLONG;
typedef int HRESULT; typedef int BOOL; typedef int LONG; typedef unsigned DWORD;
typedef unsigned UINT; typedef int HWND;
typedef struct { LONG left, top, right, bottom; } RECT;
#define TRUE 1
#define FALSE 0
#define DD_OK 0
#define DDERR_INVALIDPARAMS -2
#define MINLONG INT_MIN
#define MAXLONG INT_MAX
#define DDSCAPS_PRIMARYSURFACE 1
#define DDOVER_HIDE 2
#define DDOVER_SHOW 4
#define DDSCL_EXCLUSIVE 8
#define WINAPI
#define TRACE(...) ((void)0)
#define SUCCEEDED(hr) ((hr) >= 0)
struct ddraw_surface;
struct ddraw {
    struct ddraw_surface *overlay, *overlay_dst;
    RECT overlay_src_rect, overlay_dst_rect;
    void *wined3d_swapchain;
    DWORD cooperative_level;
    HWND d3d_window, dest_window;
};
struct ddraw_surface {
    struct ddraw *ddraw;
    struct { struct { DWORD dwCaps; } ddsCaps; DWORD dwWidth, dwHeight; } surface_desc;
    void *clipper, *wined3d_texture;
    unsigned sub_resource_idx;
};
typedef struct ddraw_surface IDirectDrawSurface7;
static struct ddraw_surface *impl_from_IDirectDrawSurface7(IDirectDrawSurface7 *p) { return p; }
static int redraws, restores, setter_result, hidden_redraws, setter_calls;
static RECT regions[16];
static HRESULT ddraw_surface_update_frontbuffer(struct ddraw_surface *s, const RECT *r, BOOL a, int b) {
    assert(redraws < 16); regions[redraws++] = *r;
    if (!s->ddraw->overlay) hidden_redraws++;
    return DD_OK;
}
static void wined3d_swapchain_set_window(void *swapchain, HWND window) { if (window == 10) restores++; }
static void ddraw_set_swapchain_window(struct ddraw *d, HWND window) {}
static HWND ddraw_find_overlay_window(struct ddraw *d) { return 20; }
static void wined3d_mutex_lock(void) {}
static void wined3d_mutex_unlock(void) {}
static HRESULT wined3d_texture_set_overlay_position(void *t, unsigned i, LONG x, LONG y) { setter_calls++; return setter_result; }
static void SetRect(RECT *r, LONG l, LONG t, LONG right, LONG b) { *r = (RECT){l,t,right,b}; }
static void OffsetRect(RECT *r, LONG x, LONG y) { r->left += x; r->right += x; r->top += y; r->bottom += y; }
'''
MAIN = r'''
static struct ddraw d;
static struct ddraw_surface overlay, dst, other;
static RECT src = {0,0,10,10}, a = {1,2,11,12}, b = {30,40,40,50};
static void reset(void) {
    d = (struct ddraw){.wined3d_swapchain=(void *)1,.d3d_window=10,.dest_window=20};
    overlay = (struct ddraw_surface){.ddraw=&d};
    dst = (struct ddraw_surface){.ddraw=&d,.surface_desc.ddsCaps.dwCaps=DDSCAPS_PRIMARYSURFACE};
    other = dst; redraws = restores = hidden_redraws = setter_result = setter_calls = 0;
    ddraw_surface_set_visible_overlay(&overlay,&src,&dst,&a,DDOVER_SHOW);
    redraws = restores = hidden_redraws = 0;
}
int main(int argc, char **argv) {
    reset();
    if (!strcmp(argv[1],"position") || !strcmp(argv[1],"overlap")) {
        int x = !strcmp(argv[1],"position") ? 30 : 5;
        int y = !strcmp(argv[1],"position") ? 40 : 5;
        assert(ddraw_surface7_SetOverlayPosition(&overlay,x,y) == DD_OK);
        assert(d.overlay_dst_rect.left == x && d.overlay_dst_rect.top == y);
        assert(d.overlay_dst_rect.right == x+10 && d.overlay_dst_rect.bottom == y+10);
        assert(hidden_redraws == 1 && redraws == 2);
        assert(regions[0].left == a.left && regions[1].left == x);
        assert(restores == 0);
    } else if (!strcmp(argv[1],"extreme-x") || !strcmp(argv[1],"extreme-y")) {
        int axis_x = !strcmp(argv[1],"extreme-x");
        RECT old = axis_x ? (RECT){INT_MIN,2,INT_MIN+10,12} : (RECT){1,INT_MIN,11,INT_MIN+10};
        d.overlay_dst_rect = old;
        int x = axis_x ? 0 : 1, y = axis_x ? 2 : 0;
        assert(ddraw_surface7_SetOverlayPosition(&overlay,x,y) == DD_OK);
        assert(d.overlay_dst_rect.left == x && d.overlay_dst_rect.top == y);
        assert(d.overlay_dst_rect.right == x+10 && d.overlay_dst_rect.bottom == y+10);
        assert(hidden_redraws == 1 && redraws == 2 && restores == 0);
        assert(!memcmp(&regions[0], &old, sizeof(old)));
        assert(!memcmp(&regions[1], &d.overlay_dst_rect, sizeof(old)));
    } else if (!strcmp(argv[1],"large-negative-delta")) {
        d.overlay_dst_rect = (RECT){INT_MAX-10,INT_MAX-10,INT_MAX,INT_MAX};
        assert(ddraw_surface7_SetOverlayPosition(&overlay,-100,-200) == DD_OK);
        assert(d.overlay_dst_rect.left == -100 && d.overlay_dst_rect.top == -200);
        assert(d.overlay_dst_rect.right == -90 && d.overlay_dst_rect.bottom == -190);
        assert(hidden_redraws == 1 && redraws == 2 && restores == 0);
    } else if (!strcmp(argv[1],"overflow-endpoint") || !strcmp(argv[1],"overflow-width")) {
        if (!strcmp(argv[1],"overflow-width")) d.overlay_dst_rect = (RECT){INT_MIN,0,INT_MAX,10};
        RECT old = d.overlay_dst_rect;
        int x = !strcmp(argv[1],"overflow-width") ? INT_MIN : INT_MAX;
        int y = !strcmp(argv[1],"overflow-width") ? 0 : INT_MAX;
        assert(ddraw_surface7_SetOverlayPosition(&overlay,x,y) == DDERR_INVALIDPARAMS);
        assert(setter_calls == 0);
        assert(!memcmp(&d.overlay_dst_rect,&old,sizeof(old)) && redraws == 0);
    } else if (!strcmp(argv[1],"failed-position")) {
        setter_result = -1; assert(ddraw_surface7_SetOverlayPosition(&overlay,30,40) == -1);
        assert(d.overlay_dst_rect.left == a.left && redraws == 0);
    } else if (!strcmp(argv[1],"update")) {
        ddraw_surface_set_visible_overlay(&overlay,&src,&dst,&b,0);
        assert(hidden_redraws == 1 && redraws == 2);
        assert(regions[0].left == a.left && regions[1].left == b.left);
        assert(restores == 0);
    } else if (!strcmp(argv[1],"replace")) {
        ddraw_surface_set_visible_overlay(&overlay,&src,&other,&b,DDOVER_SHOW);
        assert(hidden_redraws == 1 && redraws == 2 && restores == 1 && d.overlay_dst == &other);
    } else if (!strcmp(argv[1],"hide")) {
        ddraw_surface_set_visible_overlay(&overlay,NULL,NULL,NULL,DDOVER_HIDE);
        assert(!d.overlay && !d.overlay_dst && hidden_redraws == 1 && restores == 1);
    } else if (!strcmp(argv[1],"destroy-overlay") || !strcmp(argv[1],"destroy-destination")) {
        ddraw_surface_cleanup(!strcmp(argv[1],"destroy-overlay") ? &overlay : &dst);
        assert(!d.overlay && !d.overlay_dst && hidden_redraws == 1 && restores == 1);
    } else if (!strcmp(argv[1],"destroy-unrelated")) {
        ddraw_surface_cleanup(&other);
        assert(d.overlay == &overlay && redraws == 0 && restores == 0);
    } else return 2;
    return 0;
}
'''

class OverlayPatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        wine = os.environ.get('OZARK_WINE_SOURCE')
        if not wine:
            raise unittest.SkipTest('set OZARK_WINE_SOURCE to an existing pinned Wine Git object database')
        cls.tmp = tempfile.TemporaryDirectory()
        cls.addClassCleanup(cls.tmp.cleanup)
        directory = Path(cls.tmp.name)
        sha = subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD:wine'], text=True).strip()
        for name in ['surface.c','ddraw.c','ddraw_private.h']:
            target = directory/'dlls/ddraw'/name
            target.parent.mkdir(parents=True,exist_ok=True)
            target.write_bytes(subprocess.check_output(['git','-C',wine,'show',f'{sha}:dlls/ddraw/{name}']))
        patch = ROOT/'patches/ge-video-rework/0075-ddraw-emulate-one-visible-overlay.patch'
        subprocess.run(['patch','--batch','-p1','-i',str(patch)],cwd=directory,check=True,capture_output=True)
        source = (directory/'dlls/ddraw/surface.c').read_text()
        functions = function(source,'ddraw_surface_update_overlay_dst') + '\n'
        if 'static void ddraw_surface_clear_overlay(' in source:
            functions += function(source,'ddraw_surface_clear_overlay') + '\n'
        functions += function(source,'ddraw_surface_set_visible_overlay') + '\n'
        functions += function(source,'ddraw_surface7_SetOverlayPosition') + '\n'
        # Exercise the actual cleanup entry before its unrelated resource teardown.
        cleanup = function(source,'ddraw_surface_cleanup')
        functions += cleanup[:cleanup.index('    /* The refcount test')] + '}\n'
        harness = directory/'overlay.c';harness.write_text(PREFIX+functions+MAIN)
        cls.binary = directory/'overlay'
        subprocess.run(['cc','-std=c99','-O1','-fsanitize=undefined','-fno-sanitize-recover=undefined',str(harness),'-o',str(cls.binary)],check=True,capture_output=True)

    def test_overlay_lifecycle(self):
        for case in ['position','overlap','extreme-x','extreme-y','large-negative-delta','overflow-endpoint','overflow-width','failed-position','update','replace','hide','destroy-overlay','destroy-destination','destroy-unrelated']:
            with self.subTest(case=case):
                result=subprocess.run([str(self.binary),case],capture_output=True,text=True)
                self.assertEqual(result.returncode,0,result.stderr)

if __name__ == '__main__':
    unittest.main()
