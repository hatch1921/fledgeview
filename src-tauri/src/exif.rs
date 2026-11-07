// ExifTool, bundled with the program, reads camera data such as where each photo was focused.
// It is started once and kept running ("-stay_open"), so asking about hundreds of photos is fast.
// Windows uses the bundled exiftool.exe (with its exiftool_files folder); other systems run the
// bundled Perl version with the system's perl.

use std::io::{BufRead, BufReader, Write};
use std::path::PathBuf;
use std::process::{Child, ChildStdin, ChildStdout, Command, Stdio};
use std::sync::Mutex;
use tauri::{AppHandle, Manager};

struct ExifTool {
    child: Child,
    stdin: ChildStdin,
    stdout: BufReader<ChildStdout>,
    seq: u64,
}

impl Drop for ExifTool {
    fn drop(&mut self) {
        let _ = self.stdin.write_all(b"-stay_open\nFalse\n");
        let _ = self.stdin.flush();
        let _ = self.child.wait();
    }
}

static EXIFTOOL: Mutex<Option<ExifTool>> = Mutex::new(None);

fn exiftool_dir(app: &AppHandle) -> Result<PathBuf, String> {
    let dir = app
        .path()
        .resource_dir()
        .map_err(|e| e.to_string())?
        .join("exiftool");
    if dir.is_dir() {
        Ok(dir)
    } else {
        Err(format!("ExifTool is missing from the program folder ({})", dir.display()))
    }
}

fn start(app: &AppHandle) -> Result<ExifTool, String> {
    let dir = exiftool_dir(app)?;
    #[cfg(windows)]
    let mut cmd = {
        use std::os::windows::process::CommandExt;
        let mut c = Command::new(dir.join("exiftool.exe"));
        c.creation_flags(0x0800_0000); // CREATE_NO_WINDOW: no console window flashing up
        c
    };
    #[cfg(not(windows))]
    let mut cmd = {
        let mut c = Command::new("perl");
        c.arg(dir.join("exiftool"));
        c
    };
    let mut child = cmd
        .args(["-stay_open", "True", "-@", "-"])
        .current_dir(&dir)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|e| format!("couldn't start ExifTool: {e}"))?;
    let stdin = child.stdin.take().ok_or("no ExifTool input")?;
    let stdout = BufReader::new(child.stdout.take().ok_or("no ExifTool output")?);
    Ok(ExifTool { child, stdin, stdout, seq: 0 })
}

impl ExifTool {
    /// Sends one command (one argument per line) and returns everything ExifTool printed for it.
    fn run(&mut self, args: &[String]) -> Result<String, String> {
        self.seq += 1;
        let mut msg = String::new();
        for a in args {
            if a.contains('\n') || a.contains('\r') {
                return Err("file names can't contain line breaks".into());
            }
            msg.push_str(a);
            msg.push('\n');
        }
        msg.push_str(&format!("-execute{}\n", self.seq));
        self.stdin.write_all(msg.as_bytes()).map_err(|e| e.to_string())?;
        self.stdin.flush().map_err(|e| e.to_string())?;
        let done = format!("{{ready{}}}", self.seq);
        let mut out = String::new();
        loop {
            let mut line = String::new();
            let n = self.stdout.read_line(&mut line).map_err(|e| e.to_string())?;
            if n == 0 {
                return Err("ExifTool stopped unexpectedly".into());
            }
            if line.trim_end() == done {
                break;
            }
            out.push_str(&line);
        }
        Ok(out)
    }
}

/// Runs one command, starting ExifTool if needed and restarting it once if it has stopped.
fn with_exiftool(app: &AppHandle, args: &[String]) -> Result<String, String> {
    let mut guard = EXIFTOOL.lock().map_err(|_| "ExifTool is busy".to_string())?;
    for attempt in 0..2 {
        if guard.is_none() {
            *guard = Some(start(app)?);
        }
        match guard.as_mut().unwrap().run(args) {
            Ok(out) => return Ok(out),
            Err(e) => {
                *guard = None; // drop it; try once more with a fresh one
                if attempt == 1 {
                    return Err(e);
                }
            }
        }
    }
    unreachable!()
}

/// Reads the given tags from the given files (absolute paths). Returns ExifTool's JSON:
/// one record per readable file, numbers as numbers (-n), lists as space-separated text.
#[tauri::command]
pub async fn fv_read_tags(app: AppHandle, paths: Vec<String>, tags: Vec<String>) -> Result<serde_json::Value, String> {
    if paths.is_empty() {
        return Ok(serde_json::Value::Array(vec![]));
    }
    for t in &tags {
        if t.is_empty() || !t.chars().all(|c| c.is_ascii_alphanumeric() || c == '_' || c == ':' || c == '*' || c == '#') {
            return Err(format!("not a tag name: {t}"));
        }
    }
    tauri::async_runtime::spawn_blocking(move || {
        let mut args: Vec<String> = ["-j", "-n", "-q", "-q", "-charset", "filename=utf8"].iter().map(|s| s.to_string()).collect();
        args.extend(tags.iter().map(|t| format!("-{t}")));
        // File names must be full paths, so none can be mistaken for an ExifTool option.
        // ("--" can't be used here: in stay-open mode it would swallow the -execute that ends a request.)
        for p in &paths {
            if !std::path::Path::new(p).is_absolute() || p.starts_with('-') {
                return Err(format!("not a full path: {p}"));
            }
        }
        args.extend(paths);
        let out = with_exiftool(&app, &args)?;
        if out.trim().is_empty() {
            return Ok(serde_json::Value::Array(vec![]));
        }
        serde_json::from_str(&out).map_err(|e| format!("unexpected ExifTool output: {e}"))
    })
    .await
    .map_err(|e| e.to_string())?
}

/// The bundled ExifTool's version, to confirm it's present and working (shown by Ctrl+Shift+D).
#[tauri::command]
pub async fn fv_exiftool_version(app: AppHandle) -> Result<String, String> {
    tauri::async_runtime::spawn_blocking(move || with_exiftool(&app, &["-ver".to_string()]).map(|v| v.trim().to_string()))
        .await
        .map_err(|e| e.to_string())?
}
