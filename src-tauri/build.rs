// Build step: compiles LibRaw (camera raw decoding) into the program, then runs Tauri's own build step.
// The LibRaw source is put in vendor/libraw by fetch_libraw.py (run by build_desktop.py), checked against a
// pinned fingerprint. The list of files to compile is read from LibRaw's own Makefile.am, so updating
// LibRaw to a new version needs no change here.

use std::path::Path;

fn libraw() {
    let dir = Path::new("vendor/libraw");
    let makefile = dir.join("Makefile.am");
    println!("cargo:rerun-if-changed=vendor/libraw/.fledgeview-libraw");
    let text = std::fs::read_to_string(&makefile).unwrap_or_else(|_| {
        panic!("LibRaw source is missing (src-tauri/vendor/libraw). Run: python build_desktop.py")
    });
    // The static library's sources: "lib_libraw_a_SOURCES = a.cpp b.cpp \ ..." (continued lines)
    let start = text.find("lib_libraw_a_SOURCES").expect("LibRaw Makefile.am has no source list");
    let mut sources = Vec::new();
    for line in text[start..].lines() {
        let body = line.split('=').last().unwrap_or("");
        for word in body.split_whitespace() {
            if word.ends_with(".cpp") {
                sources.push(word.to_string());
            }
        }
        if !line.trim_end().ends_with('\\') {
            break;
        }
    }
    assert!(sources.len() > 40, "LibRaw source list looks incomplete ({} files)", sources.len());

    let mut build = cc::Build::new();
    build
        .cpp(true)
        .include(dir)
        .define("LIBRAW_NODLL", None) // built in, not a separate DLL
        .define("LIBRAW_BUILDLIB", None)
        .warnings(false)
        .opt_level(2);
    if build.get_compiler().is_like_msvc() {
        build.flag("/EHsc").define("WIN32", None).define("_CRT_SECURE_NO_WARNINGS", None);
    } else {
        build.flag_if_supported("-w").flag_if_supported("-std=c++11");
    }
    for s in &sources {
        build.file(dir.join(s));
    }
    build.compile("raw_fledgeview");
    if std::env::var("CARGO_CFG_WINDOWS").is_ok() {
        println!("cargo:rustc-link-lib=ws2_32"); // LibRaw uses Windows sockets helpers (byte order)
    }
}

fn main() {
    libraw();
    tauri_build::build()
}
