// FledgeView desktop program: opens the FledgeView page in a native window.
// Folders open through the system folder window (see folders.rs).
#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

mod exif;
mod folders;
mod raw;

use std::path::{Path, PathBuf};
use tauri::webview::DownloadEvent;
use tauri::{Manager, WebviewUrl, WebviewWindowBuilder};

/// Picks a file name in `dir` that doesn't exist yet ("photo.jpg", then "photo (2).jpg", ...),
/// so a save never overwrites anything.
fn unique_path(dir: &Path, name: &str) -> PathBuf {
    let first = dir.join(name);
    if !first.exists() {
        return first;
    }
    let p = Path::new(name);
    let stem = p.file_stem().and_then(|s| s.to_str()).unwrap_or("FledgeView export");
    let ext = p.extension().and_then(|s| s.to_str());
    (2..10_000)
        .map(|i| match ext {
            Some(e) => dir.join(format!("{stem} ({i}).{e}")),
            None => dir.join(format!("{stem} ({i})")),
        })
        .find(|c| !c.exists())
        .unwrap_or(first)
}

fn main() {
    tauri::Builder::default()
        .plugin(tauri_plugin_opener::init())
        // Remembers the window's size, position, and maximized state between launches.
        .plugin(tauri_plugin_window_state::Builder::default().build())
        .invoke_handler(tauri::generate_handler![folders::fv_pick_folder, folders::fv_send_dir_handle, exif::fv_read_tags, exif::fv_exiftool_version, raw::fv_libraw_version])
        .setup(|app| {
            // The Downloads folder; if the system doesn't name one, a Downloads folder in the
            // home folder (never the program's own folder).
            let downloads = app.path().download_dir().ok().or_else(|| {
                let d = app.path().home_dir().ok()?.join("Downloads");
                std::fs::create_dir_all(&d).ok()?;
                Some(d)
            });
            WebviewWindowBuilder::new(app, "main", WebviewUrl::default())
                .title("FledgeView")
                .inner_size(1440.0, 900.0)
                .min_inner_size(1000.0, 640.0)
                .center()
                // Let the page handle dropped photos and folders itself, as it does in a browser.
                .disable_drag_drop_handler()
                // Saves the page starts (single exports, web gallery ZIPs) go to the Downloads folder.
                .on_download(move |_webview, event| {
                    if let DownloadEvent::Requested { destination, .. } = event {
                        if let Some(dir) = &downloads {
                            let name = destination
                                .file_name()
                                .and_then(|n| n.to_str())
                                .unwrap_or("FledgeView export")
                                .to_string();
                            *destination = unique_path(dir, &name);
                        }
                    }
                    true
                })
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("FledgeView could not start");
}
