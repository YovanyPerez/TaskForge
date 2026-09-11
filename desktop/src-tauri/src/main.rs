#![cfg_attr(not(debug_assertions), windows_subsystem = "windows")]

use std::net::{TcpStream, ToSocketAddrs};
use std::path::PathBuf;
use std::time::Duration;

use tauri::{Url, WebviewUrl, WebviewWindowBuilder};

// Real deployment URLs are injected at build time (not committed):
//   TASKFORGE_SERVER_URLS="https://<machine>.<tailnet>.ts.net,http://<server-host>:8000"
const COMPILED_SERVER_URLS: Option<&str> = option_env!("TASKFORGE_SERVER_URLS");
const PLACEHOLDER_SERVER_URLS: &str = "https://taskforge.example.ts.net";
const CONFIG_FILE_NAME: &str = "taskforge.json";
const CONNECT_TIMEOUT: Duration = Duration::from_secs(2);

#[derive(serde::Deserialize)]
struct ClientConfig {
    #[serde(default)]
    server_urls: Vec<String>,
}

fn config_path() -> Option<PathBuf> {
    std::env::current_exe()
        .ok()?
        .parent()
        .map(|dir| dir.join(CONFIG_FILE_NAME))
}

fn parse_urls(raw: &str) -> Vec<String> {
    raw.split(',')
        .map(|url| url.trim().to_string())
        .filter(|url| !url.is_empty())
        .collect()
}

fn default_urls() -> Vec<String> {
    parse_urls(COMPILED_SERVER_URLS.unwrap_or(PLACEHOLDER_SERVER_URLS))
}

fn candidate_urls() -> Vec<String> {
    if let Ok(url) = std::env::var("TASKFORGE_SERVER_URL") {
        let url = url.trim();
        if !url.is_empty() {
            return vec![url.to_string()];
        }
    }
    if let Some(path) = config_path() {
        if let Ok(raw) = std::fs::read_to_string(path) {
            if let Ok(config) = serde_json::from_str::<ClientConfig>(&raw) {
                let urls: Vec<String> = config
                    .server_urls
                    .into_iter()
                    .map(|url| url.trim().to_string())
                    .filter(|url| !url.is_empty())
                    .collect();
                if !urls.is_empty() {
                    return urls;
                }
            }
        }
    }
    default_urls()
}

fn is_reachable(url: &str) -> bool {
    let Ok(parsed) = Url::parse(url) else {
        return false;
    };
    let Some(host) = parsed.host_str() else {
        return false;
    };
    let Some(port) = parsed.port_or_known_default() else {
        return false;
    };
    let Ok(addresses) = (host, port).to_socket_addrs() else {
        return false;
    };
    addresses
        .into_iter()
        .any(|addr| TcpStream::connect_timeout(&addr, CONNECT_TIMEOUT).is_ok())
}

fn first_reachable(urls: &[String]) -> Option<String> {
    urls.iter().find(|url| is_reachable(url)).cloned()
}

#[tauri::command]
fn get_server_urls() -> Vec<String> {
    candidate_urls()
}

#[tauri::command]
fn find_server(urls: Vec<String>) -> Option<String> {
    first_reachable(&urls)
}

#[tauri::command]
fn open_server(window: tauri::WebviewWindow, url: String) -> Result<(), String> {
    let parsed = Url::parse(&url).map_err(|error| error.to_string())?;
    window.navigate(parsed).map_err(|error| error.to_string())
}

fn main() {
    tauri::Builder::default()
        .invoke_handler(tauri::generate_handler![
            get_server_urls,
            find_server,
            open_server
        ])
        .setup(|app| {
            let (url, size) = match first_reachable(&candidate_urls()) {
                Some(server) => (WebviewUrl::External(server.parse()?), (1280.0, 800.0)),
                None => (WebviewUrl::App("offline.html".into()), (720.0, 540.0)),
            };
            WebviewWindowBuilder::new(app, "main", url)
                .title("TaskForge")
                .inner_size(size.0, size.1)
                .min_inner_size(720.0, 480.0)
                .build()?;
            Ok(())
        })
        .run(tauri::generate_context!())
        .expect("error while running tauri application");
}

#[cfg(test)]
mod tests {
    use super::{default_urls, parse_urls};
    use tauri::Url;

    #[test]
    fn parses_url_lists() {
        assert_eq!(
            parse_urls(" https://a.ts.net , http://b:8000 ,, "),
            vec!["https://a.ts.net", "http://b:8000"]
        );
        assert!(parse_urls("").is_empty());
    }

    #[test]
    fn default_urls_are_valid() {
        let urls = default_urls();
        assert!(!urls.is_empty());
        for url in urls {
            assert!(Url::parse(&url).is_ok(), "invalid URL: {url}");
        }
    }
}
