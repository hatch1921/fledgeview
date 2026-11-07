// LibRaw: develops camera raw files. Compiled into the program (see build.rs).
// Stage 1: confirm it's built in and working (version shown by Ctrl+Shift+D).

use std::ffi::CStr;
use std::os::raw::c_char;

extern "C" {
    fn libraw_version() -> *const c_char;
    fn libraw_cameraCount() -> i32;
}

/// LibRaw's version and how many camera models it knows (shown by Ctrl+Shift+D).
#[tauri::command]
pub fn fv_libraw_version() -> String {
    unsafe {
        let v = CStr::from_ptr(libraw_version()).to_string_lossy().into_owned();
        format!("{v}, {} cameras", libraw_cameraCount())
    }
}
