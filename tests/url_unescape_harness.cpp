#include <algorithm>
#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <dlfcn.h>
#include <iconv.h>
#include <limits.h>
#include <stdexcept>
#include <string>
#include <type_traits>

using WCHAR = char16_t;
using UINT = unsigned int;
using NTSTATUS = int32_t;
static_assert(sizeof(WCHAR) == 2, "Wine WCHAR is UTF-16");
static constexpr NTSTATUS STATUS_NO_SUCH_FILE = static_cast<NTSTATUS>(0xc000000f);
static constexpr int FILE_OPEN_IF = 3;
static int allocations, fail_allocation, utf8_calls, lookup_calls;
static std::u16string last_lookup;
static void *native_ntdll;
static NTSTATUS (*native_utf8)(WCHAR *, uint32_t, uint32_t *, const char *, uint32_t);

static void require(bool condition, const char *message)
{
    if (!condition) throw std::runtime_error(message);
}

static void *test_malloc(size_t bytes)
{
    ++allocations;
    if (allocations == fail_allocation) return nullptr;
    return std::malloc(bytes);
}

// Real libc conversion for valid test inputs; not a replacement for Wine error semantics.
static size_t convert(const char *to, const char *from, const void *src, size_t bytes,
                      void *dst, size_t capacity)
{
    iconv_t cd = iconv_open(to, from);
    require(cd != reinterpret_cast<iconv_t>(-1), "iconv_open failed");
    char *in = const_cast<char *>(static_cast<const char *>(src));
    char *out = static_cast<char *>(dst);
    size_t left = capacity;
    size_t result = iconv(cd, &in, &bytes, &out, &left);
    iconv_close(cd);
    require(result != static_cast<size_t>(-1), "iconv conversion failed (outside valid-input adapter)");
    return capacity - left;
}

static NTSTATUS RtlUTF8ToUnicodeN(WCHAR *dst, uint32_t capacity, uint32_t *written,
                                 const char *src, uint32_t bytes)
{
    ++utf8_calls;
    if (native_utf8) return native_utf8(dst, capacity, written, src, bytes);
    *written = convert("UTF-16LE", "UTF-8", src, bytes, dst, capacity);
    return 0;
}

// Stub Wine's locale-dependent multibyte entry point with explicit UTF-8 conversion.
static uint32_t ntdll_umbstowcs(const char *src, uint32_t bytes, WCHAR *dst, uint32_t capacity)
{
    return convert("UTF-16LE", "UTF-8", src, bytes, dst, capacity * sizeof(WCHAR)) / sizeof(WCHAR);
}

// Stub filesystem/drive mapping: capture the actual collapsed NT path, map Z: to /.
static NTSTATUS ntdll_get_unix_file_name(const WCHAR *path, char **buffer, int disposition)
{
    require(disposition == FILE_OPEN_IF, "unexpected lookup disposition");
    ++lookup_calls;
    last_lookup = path;
    require(last_lookup.substr(0, 7) == u"\\??\\Z:\\", "lookup expected NT Z: path");
    std::u16string suffix = last_lookup.substr(6);
    std::replace(suffix.begin(), suffix.end(), u'\\', u'/');
    char converted[4096];
    convert("UTF-8", "UTF-16LE", suffix.c_str(), (suffix.size() + 1) * sizeof(WCHAR),
            converted, sizeof(converted));
    *buffer = static_cast<char *>(std::malloc(std::strlen(converted) + 1));
    require(*buffer != nullptr, "lookup test double allocation failed");
    std::strcpy(*buffer, converted);
    return 0;
}

static void lstrcpynA(char *dst, const char *src, size_t capacity)
{
    if (!capacity) return;
    size_t length = std::min(std::strlen(src), capacity - 1);
    std::memcpy(dst, src, length);
    dst[length] = 0;
}

#define TRACE(...) ((void)0)
#define ERR(...) ((void)0)
#define wcslen(s) std::char_traits<WCHAR>::length(s)
#define malloc test_malloc
#include "path_functions.inc"
#undef malloc
#undef wcslen

// The old void decoder is considered successful so RED runs execute, not compile-fail.
template<typename F> static bool decode(F function, WCHAR *buffer)
{
    if constexpr (std::is_void_v<decltype(function(buffer))>)
    {
        function(buffer);
        return true;
    }
    else return function(buffer);
}

static void decoder_oom()
{
    WCHAR input[] = u"abc%41tail";
    const std::u16string original = input;
    fail_allocation = 1;
    require(!decode(url_unescape, input), "decoder must report allocation failure");
    require(std::u16string(input) == original, "allocation failure changed input");
    require(allocations == 1 && utf8_calls == 0, "OOM must stop before UTF conversion");
}

static void caller_oom()
{
    fail_allocation = 1;
    char *result = steamclient_dos_to_unix_path("file:///Z:/abc%41tail", 1);
    bool failed = result == nullptr;
    std::free(result);
    require(failed, "caller must return NULL on decoder allocation failure");
    require(allocations == 1, "caller continued allocating after decoder failure");
    require(utf8_calls == 0 && lookup_calls == 0, "caller converted or looked up an undecoded path");
}

static void expect_decoded(const char16_t *src, const char16_t *expected)
{
    std::u16string input = src;
    require(decode(url_unescape, input.data()), "decoder unexpectedly failed");
    require(std::u16string(input.c_str()) == expected, "decoded output mismatch");
}

static void final_triplets()
{
    expect_decoded(u"%41", u"A");
}

static void trailing_triplets()
{
    expect_decoded(u"abc%41", u"abcA");
    expect_decoded(u"%41%42", u"AB");
    expect_decoded(u"abc%2f", u"abc/");
}

static void utf8_triplets()
{
    expect_decoded(u"%C3%A9", u"\u00e9");
    expect_decoded(u"name%E2%82%AC", u"name\u20ac");
    expect_decoded(u"%F0%9F%98%80", u"\U0001f600");
}

static void short_no_allocation()
{
    fail_allocation = 1;
    expect_decoded(u"", u"");
    expect_decoded(u"a", u"a");
    expect_decoded(u"ab", u"ab");
    expect_decoded(u"%", u"%");
    expect_decoded(u"%4", u"%4");
    require(allocations == 0 && utf8_calls == 0, "short input allocated or converted");
}

static void ordinary_decoder()
{
    expect_decoded(u"abc", u"abc");
    expect_decoded(u"Z:/Games/ordinary file.txt", u"Z:/Games/ordinary file.txt");
    expect_decoded(u"a+b", u"a+b");
    expect_decoded(u"%41tail", u"Atail");
}

static void malformed_semantics()
{
    // Characterizations: retain the pre-existing percent dropping / NUL truncation policy.
    expect_decoded(u"abc%", u"abc%");
    expect_decoded(u"abc%4", u"abc%4");
    expect_decoded(u"%G1tail", u"G1tail");
    expect_decoded(u"%4Gtail", u"4Gtail");
    expect_decoded(u"%00tail", u"");
}

static void expect_path(const char *src, int is_url, const char *expected)
{
    char *result = steamclient_dos_to_unix_path(src, is_url);
    bool matches = result && std::strcmp(result, expected) == 0;
    std::free(result);
    require(matches, "caller output mismatch");
}

static void caller_paths()
{
    require(steamclient_dos_to_unix_path(nullptr, 0) == nullptr, "NULL input changed");
    expect_path("", 0, "");
    expect_path("relative\\plain.txt", 0, "relative/plain.txt");
    expect_path("relative\\abc%41", 0, "relative/abc%41");
    expect_path("Z:\\Games\\plain.txt", 0, "/Games/plain.txt");
    expect_path("Z:\\Games\\abc%41", 0, "/Games/abc%41");
    expect_path("https://example.test/abc%41", 1, "https://example.test/abc%41");
    require(utf8_calls == 0 && lookup_calls == 2, "non-file input reached URL decoder");
}

static void caller_file_urls()
{
    expect_path("file:///Z:/abc%41", 1, "file:///abcA");
    expect_path("file:///Z:/%C3%A9", 1, "file:///\xc3\xa9");
    expect_path("file:///Z:/%E2%82%AC", 1, "file:///\xe2\x82\xac");
    expect_path("file:///Z:/%F0%9F%98%80", 1, "file:///\xf0\x9f\x98\x80");
    expect_path("file:///Z:/Game%20Files/plain.txt", 1, "file:///Game Files/plain.txt");
    expect_path("file:///Z:/abc%41?query=%42#frag", 1, "file:///abcA?query=%42#frag");
    expect_path("file:///Z:/Games/../plain.txt", 1, "file:///plain.txt");
    require(utf8_calls == 7 && lookup_calls == 7, "expected decoder and lookup per file URL");
    require(last_lookup == u"\\??\\Z:\\plain.txt", "actual collapse_path was not exercised");
}

static void caller_result_oom()
{
    fail_allocation = 2;
    char *result = steamclient_dos_to_unix_path("file:///Z:/abc%41", 1);
    bool failed = result == nullptr;
    std::free(result);
    require(failed, "caller output allocation failure must return NULL");
    require(allocations == 2 && utf8_calls == 1 && lookup_calls == 1,
            "output allocation failure did not exercise successful decode/lookup first");
}

static void existing_unicode_narrowing()
{
    // Adjacent defect, deliberately NOT fixed: U+0100 narrows to an embedded zero byte.
    expect_decoded(u"abc\u0100def", u"abc");
    std::puts("KNOWN ADJACENT DEFECT: abc U+0100 def decodes to abc (WCHAR-to-char narrowing)");
}

int main(int argc, char **argv)
{
    try
    {
        require(argc == 2, "one test case required");
        if (const char *library = std::getenv("OZARK_TEST_NTDLL"))
        {
            native_ntdll = dlopen(library, RTLD_NOW | RTLD_LOCAL);
            require(native_ntdll != nullptr, "native ntdll dlopen failed");
            native_utf8 = reinterpret_cast<decltype(native_utf8)>(dlsym(native_ntdll, "RtlUTF8ToUnicodeN"));
            require(native_utf8 != nullptr, "native RtlUTF8ToUnicodeN symbol not found");
            std::printf("Backend: native Wine RtlUTF8ToUnicodeN (%s)\n", library);
        }
        else std::puts("Backend: libc iconv adapter (not Wine Rtl)");
        std::string test = argv[1];
        if (test == "decoder_oom") decoder_oom();
        else if (test == "caller_oom") caller_oom();
        else if (test == "final_triplets") final_triplets();
        else if (test == "trailing_triplets") trailing_triplets();
        else if (test == "utf8_triplets") utf8_triplets();
        else if (test == "short_no_allocation") short_no_allocation();
        else if (test == "ordinary_decoder") ordinary_decoder();
        else if (test == "malformed_semantics") malformed_semantics();
        else if (test == "caller_paths") caller_paths();
        else if (test == "caller_file_urls") caller_file_urls();
        else if (test == "caller_result_oom") caller_result_oom();
        else if (test == "existing_unicode_narrowing") existing_unicode_narrowing();
        else throw std::runtime_error("unknown case");
        std::printf("PASS %s\n", argv[1]);
        if (native_ntdll) dlclose(native_ntdll);
        return 0;
    }
    catch (const std::exception &error)
    {
        std::fprintf(stderr, "FAIL: %s\n", error.what());
        if (native_ntdll) dlclose(native_ntdll);
        return 1;
    }
}
