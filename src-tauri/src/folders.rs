// Native folder bridge.
// Folders are chosen in the system's own folder window, so the program knows each folder's real
// location on disk (needed by the desktop-only features). On Windows the page then receives a
// genuine browser folder handle for that location, created by WebView2, so FledgeView reads,
// moves and writes files exactly as it does in a browser, at the same speed.

use std::path::{Path, PathBuf};
use tauri::{AppHandle, Manager, WebviewWindow};

/// Where the folder window starts: a known folder path, a remembered one, or a named place
/// such as "pictures".
fn start_dir(app: &AppHandle, start: Option<String>) -> Option<PathBuf> {
    let s = start?;
    let p = app.path();
    let named = match s.as_str() {
        "pictures" => p.picture_dir().ok(),
        "desktop" => p.desktop_dir().ok(),
        "documents" => p.document_dir().ok(),
        "downloads" => p.download_dir().ok(),
        "music" => p.audio_dir().ok(),
        "videos" => p.video_dir().ok(),
        _ => None,
    };
    named.or_else(|| Some(PathBuf::from(&s))).filter(|d| d.is_dir())
}

/// Shows the folder window. Returns the chosen folder's path, or nothing if cancelled.
#[tauri::command]
pub async fn fv_pick_folder(
    app: AppHandle,
    window: WebviewWindow,
    start: Option<String>,
) -> Result<Option<String>, String> {
    // Automated tests (debug builds only) can skip the window.
    #[cfg(debug_assertions)]
    if let Ok(t) = std::env::var("FV_TEST_PICK") {
        return Ok(if t.is_empty() { None } else { Some(t) });
    }
    let start = start_dir(&app, start);
    // The window is shown on a worker thread (it waits for the person), attached to FledgeView's window.
    tauri::async_runtime::spawn_blocking(move || {
        let mut dialog = rfd::FileDialog::new()
            .set_title("Choose a photo folder")
            .set_parent(&window);
        if let Some(dir) = start {
            dialog = dialog.set_directory(dir);
        }
        dialog.pick_folder().map(|p| p.to_string_lossy().into_owned())
    })
    .await
    .map_err(|e| e.to_string())
}

/// Gives the page a real folder handle for `path` (Windows). The page receives it as a web
/// message tagged with `id`. Other systems answer "unsupported" until their bridge exists.
#[tauri::command]
pub async fn fv_send_dir_handle(window: WebviewWindow, path: String, id: String) -> Result<(), String> {
    if !Path::new(&path).is_dir() {
        return Err(format!("not a folder: {path}"));
    }
    #[cfg(windows)]
    {
        let json = serde_json::json!({ "fvHandle": id, "path": path }).to_string();
        let (tx, rx) = std::sync::mpsc::channel();
        window
            .with_webview(move |pv| {
                let r = win::post_dir_handle(&pv.environment(), &pv.controller(), &path, &json)
                    .map_err(|e| e.to_string());
                let _ = tx.send(r);
            })
            .map_err(|e| e.to_string())?;
        rx.recv_timeout(std::time::Duration::from_secs(10))
            .map_err(|_| "the folder handle took too long".to_string())?
    }
    #[cfg(not(windows))]
    {
        let _ = (window, id);
        Err("unsupported".into())
    }
}

#[cfg(windows)]
mod win {
    use webview2_com::Microsoft::Web::WebView2::Win32::*;
    use windows_core::{IUnknown, Interface, HRESULT, HSTRING};

    /// Creates a read-write browser folder handle for `path` and posts it to the page with `json`.
    pub fn post_dir_handle(
        env: &ICoreWebView2Environment,
        ctl: &ICoreWebView2Controller,
        path: &str,
        json: &str,
    ) -> windows_core::Result<()> {
        unsafe {
            let env14: ICoreWebView2Environment14 = env.cast()?;
            let handle = env14.CreateWebFileSystemDirectoryHandle(
                &HSTRING::from(path),
                COREWEBVIEW2_FILE_SYSTEM_HANDLE_PERMISSION_READ_WRITE,
            )?;
            let mut items: [Option<IUnknown>; 1] = [Some(handle.cast::<IUnknown>()?)];
            let mut coll: Option<ICoreWebView2ObjectCollection> = None;
            env14.CreateObjectCollection(1, items.as_mut_ptr(), &mut coll)?;
            let coll = coll
                .ok_or_else(|| windows_core::Error::from_hresult(HRESULT(0x8000_4003_u32 as i32)))?;
            let webview: ICoreWebView2_23 = ctl.CoreWebView2()?.cast()?;
            webview.PostWebMessageAsJsonWithAdditionalObjects(&HSTRING::from(json), &coll)?;
        }
        Ok(())
    }
}
