//! kl-gate — hook entry point for the kl-skills plugin.
//!
//! Claude Code runs this once per hook event, passing the gate name as argv[1]
//! and the event payload as JSON on stdin.
//!
//! Exit codes (Claude Code contract):
//!   0 = allow. Plain stdout reaches the model only on SessionStart; on
//!       PostToolUse and Stop it goes to the debug log. Use `model_note` for text
//!       the model must see.
//!   2 = block; stderr is shown to the model
//! A gate that cannot decide exits 0. Erroring out on an unexpected payload
//! would break every session that triggers the event, which is a far worse
//! outcome than a rule going unenforced once.

use std::fs;
use std::io::{Read, Write};
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::time::SystemTime;

const VERSION: &str = env!("CARGO_PKG_VERSION");

fn main() {
    let mut payload = String::new();
    let _ = std::io::stdin().read_to_string(&mut payload);

    let gate = std::env::args().nth(1).unwrap_or_default();

    match gate.as_str() {
        "session-start" => {
            // The count and the names are written out by hand, because this binary cannot
            // see hooks.json and the Python gates are not in this crate at all. That makes
            // the line drift the moment a gate is added, which is exactly what happened
            // when wiki-graph and prose-check arrived. tests/selftest-banner.sh compares
            // this string against hooks.json so the drift fails a test instead of shipping.
            println!(
                "KL-SKILLS GATES v{VERSION} — loaded, 9 rules enforced \
                 (wiki-index-check, wiki-graph, prose-check, code-check, plan-drift, \
                  after-bash, wiki-sync, answer-check, wiki-recall)"
            );
        }
        "wiki-index-check" => wiki_index_check(&payload),
        // "wiki-touch" 는 예전 이름이다. 설치된 hooks.json 이 아직 그 이름을 부를 수 있다.
        "wiki-touch" | "after-bash" => after_bash(&payload),
        // Unknown or not-yet-implemented gate: allow, say nothing.
        _ => {}
    }
}

/// Where the wikis live. Mirrors scripts/_wiki.py so the two cannot disagree.
fn wiki_root() -> Option<PathBuf> {
    if let Ok(r) = std::env::var("LLM_WIKI_ROOT") {
        if !r.trim().is_empty() {
            return Some(PathBuf::from(r));
        }
    }
    std::env::var("HOME").ok().map(|h| Path::new(&h).join("llm-wiki-docs"))
}

/// A page written into a wiki, as (topic, page path relative to wiki/).
///
/// Returns None for anything outside `<root>/<topic>/wiki/`, and for index.md
/// and log.md, which are the machinery rather than pages to be indexed.
fn wiki_page(file_path: &str, root: &Path) -> Option<(String, String)> {
    let rest = Path::new(file_path).strip_prefix(root).ok()?;
    let mut parts = rest.components();
    let topic = parts.next()?.as_os_str().to_str()?.to_string();
    if parts.next()?.as_os_str().to_str()? != "wiki" {
        return None;
    }
    // Joined with '/' deliberately, never with the platform separator: this string
    // is compared against an index entry written by index-add.py, which always
    // uses '/'. On Windows a collected PathBuf would give "sub\\deep.md" and never
    // match, so every page in a subfolder would be reported as unindexed forever.
    let mut page_parts = Vec::new();
    for c in parts {
        page_parts.push(c.as_os_str().to_str()?);
    }
    let page = page_parts.join("/");
    if page.is_empty() || !page.ends_with(".md") || page == "index.md" || page == "log.md" {
        return None;
    }
    Some((topic, page))
}

/// Does index.md already list this page? Entries carry the file in `(...)`, so
/// that is what we look for — matching the bare name would also hit prose.
fn indexed(index_text: &str, page: &str) -> bool {
    let needle = format!("({page})");
    index_text.lines().any(|l| l.trim_start().starts_with("- ") && l.contains(&needle))
}

/// The JSON a hook must print for its text to reach the model.
///
/// On PostToolUse, plain stdout only lands in Claude Code's debug log; the model
/// never sees it. The documented route is `hookSpecificOutput.additionalContext`,
/// which is attached next to the tool result. Until 2026-11-11 these gates printed
/// plain text, so their warnings were recorded and read by nobody. Kept pure so the
/// shape is tested rather than assumed.
fn model_note(event: &str, text: &str) -> String {
    serde_json::json!({
        "hookSpecificOutput": {
            "hookEventName": event,
            "additionalContext": text,
        }
    })
    .to_string()
}

fn tell_model(text: &str) {
    println!("{}", model_note("PostToolUse", text));
}

fn wiki_index_check(payload: &str) {
    let Some(root) = wiki_root() else { return };
    let Ok(v) = serde_json::from_str::<serde_json::Value>(payload) else { return };
    let Some(file_path) = v["tool_input"]["file_path"].as_str() else { return };
    let Some((topic, page)) = wiki_page(file_path, &root) else { return };

    let index = root.join(&topic).join("wiki").join("index.md");
    // No index at all is a different problem, and new-topic.sh is the fix for it.
    let Ok(text) = std::fs::read_to_string(&index) else {
        tell_model(&format!(
            "! {topic}/wiki/index.md is missing, so nothing written here can be found.\n  \
             refill it:  sh \"{}\" {topic}",
            script("new-topic.sh")
        ));
        return;
    };

    if indexed(&text, &page) {
        return;
    }

    tell_model(&format!(
        "! {page} is not listed in {topic}/wiki/index.md — a page missing from the \
         index is a page nobody finds.\n  add it:  python3 \"{}\" {topic} {page} \
         <category> \"one line on what it holds\"",
        script("index-add.py")
    ));
}

/// Path to one of the skill's scripts, taken from the environment rather than
/// assumed, since the plugin lives in a different place on every machine.
fn script(name: &str) -> String {
    let base = std::env::var("CLAUDE_PLUGIN_ROOT").unwrap_or_else(|_| ".".into());
    Path::new(&base)
        .join("skills/llm-wiki-docs/scripts")
        .join(name)
        .to_string_lossy()
        .into_owned()
}

/// Has a wiki page been written since the graph was last built?
///
/// Pure on purpose: the two timestamps come from the caller, so the decision is
/// testable without touching a disk.
fn stale(newest_page: Option<SystemTime>, graph: Option<SystemTime>) -> bool {
    match (newest_page, graph) {
        // No pages: nothing to keep in sync.
        (None, _) => false,
        // Pages but no graph yet: the first build is owed.
        (Some(_), None) => true,
        (Some(page), Some(graph)) => page > graph,
    }
}

/// The newest mtime among `<root>/<topic>/wiki/**/*.md`.
///
/// index.md and log.md are left out deliberately. They change on every filing,
/// and filing is not what the graph or the prose check care about.
fn newest_page_mtime(root: &Path) -> Option<SystemTime> {
    let mut newest: Option<SystemTime> = None;
    if let Ok(entries) = fs::read_dir(root) {
        for topic in entries.flatten() {
            let name = topic.file_name();
            if name.to_string_lossy().starts_with('.') {
                continue;
            }
            let wiki = topic.path().join("wiki");
            if wiki.is_dir() {
                walk_pages(&wiki, &mut newest, 0);
            }
        }
    }
    newest
}

fn walk_pages(dir: &Path, newest: &mut Option<SystemTime>, depth: usize) {
    // A wiki is a few levels deep at most. The cap stops a symlink loop from
    // turning a 4 ms gate into a hung session.
    if depth > 6 {
        return;
    }
    let entries = match fs::read_dir(dir) {
        Ok(e) => e,
        Err(_) => return,
    };
    for entry in entries.flatten() {
        let path = entry.path();
        let name = match path.file_name().and_then(|n| n.to_str()) {
            Some(n) => n.to_string(),
            None => continue,
        };
        if name.starts_with('.') {
            continue;
        }
        if path.is_dir() {
            walk_pages(&path, newest, depth + 1);
            continue;
        }
        if !name.ends_with(".md") || name == "index.md" || name == "log.md" {
            continue;
        }
        if let Ok(modified) = entry.metadata().and_then(|m| m.modified()) {
            if newest.map_or(true, |n| modified > n) {
                *newest = Some(modified);
            }
        }
    }
}

/// PostToolUse(Bash) gate: two cheap questions after every shell command.
///
/// 1. Was a wiki page changed by the shell rather than by Write/Edit? (mtime check)
/// 2. Was this a commit? If so, does the work still follow the plan?
///
/// Bash is the most-used tool, so this runs hundreds of times a session. Both
/// questions are answered here without spawning anything in the usual case; only
/// a real change pays for the Python work. They share one gate so the launcher
/// cost (about 20 ms, measured) is paid once per Bash call, not twice.
///
/// Whatever both checks found leaves as **one** JSON object. Two objects on stdout
/// cannot be parsed, and Claude Code then drops the lot.
fn after_bash(payload: &str) {
    let mut notes: Vec<String> = Vec::new();
    if let Some(text) = wiki_touch() {
        notes.push(text);
    }
    if made_a_commit(payload) {
        // ponytail: 실패한 커밋(바뀐 것 없음)에서도 돈다. 그때는 직전 커밋을 다시 본다 — 같은
        // 알림이 한 번 더 나올 뿐이라 놔둔다. 거슬리면 tool_response 의 실패 여부를 본다.
        if let Some(text) = run_python("plan-drift.py", &["--plain"], payload) {
            notes.push(text);
        }
    }
    if !notes.is_empty() {
        tell_model(&notes.join("\n\n"));
    }
}

/// A wiki page newer than the graph means the wiki changed outside Write/Edit.
fn wiki_touch() -> Option<String> {
    let root = wiki_root()?;
    if !root.is_dir() {
        return None;
    }
    let graph = fs::metadata(root.join(".graph").join("graph.json"))
        .and_then(|m| m.modified())
        .ok();
    if !stale(newest_page_mtime(&root), graph) {
        return None;
    }
    run_python("wiki-sync.py", &[], "")
}

/// Did this Bash call run a commit? Read from the payload, never guessed.
fn made_a_commit(payload: &str) -> bool {
    serde_json::from_str::<serde_json::Value>(payload)
        .ok()
        .and_then(|event| event["tool_input"]["command"].as_str().map(runs_a_commit))
        .unwrap_or(false)
}

/// Does this shell command run `git ... commit`?
///
/// Looking for the literal text "git commit" missed `git -C <dir> commit`,
/// which is how commits into another folder are usually written (2026-11-11). So
/// each command segment is read word by word: optional `NAME=value` assignments,
/// then `git`, then any global options (`-C dir`, `-c key=value`, `--flag`),
/// then `commit`. `git` has to start the segment, so `echo git commit` is not one.
fn runs_a_commit(command: &str) -> bool {
    command
        .split(|separator| matches!(separator, ';' | '&' | '|' | '\n'))
        .any(|segment| {
            let words: Vec<&str> = segment.split_whitespace().collect();
            let mut index = 0;
            // GIT_AUTHOR_DATE=... 같은 환경 변수 지정은 명령 앞에 올 수 있다.
            while index < words.len() && words[index].contains('=') && !words[index].starts_with('-') {
                index += 1;
            }
            if words.get(index) != Some(&"git") {
                return false;
            }
            index += 1;
            while let Some(word) = words.get(index) {
                match *word {
                    "-C" | "-c" => index += 2,
                    flag if flag.starts_with("--") => index += 1,
                    _ => break,
                }
            }
            words.get(index) == Some(&"commit")
        })
}

/// Run one of the plugin's Python scripts and return what it printed, if anything.
/// `stdin_text` is handed over as the script's input — the hook payload, usually.
fn run_python(script_name: &str, args: &[&str], stdin_text: &str) -> Option<String> {
    let base = std::env::var("CLAUDE_PLUGIN_ROOT").unwrap_or_else(|_| ".".into());
    let path = Path::new(&base).join("hooks").join("py").join(script_name);
    if !path.is_file() {
        return None;
    }
    for interpreter in ["python3", "python"] {
        let spawned = Command::new(interpreter)
            .arg(&path)
            .args(args)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::null())
            .spawn();
        let mut child = match spawned {
            Ok(child) => child,
            // 이 이름의 인터프리터가 없으면 다음 이름으로 넘어간다.
            Err(_) => continue,
        };
        if let Some(mut input) = child.stdin.take() {
            // 쓰기가 실패해도 스크립트는 빈 입력으로 돌 수 있다. 여기서 멈추지 않는다.
            let _ = input.write_all(stdin_text.as_bytes());
        }
        let finished = child.wait_with_output().ok()?;
        let text = String::from_utf8_lossy(&finished.stdout).trim_end().to_string();
        return if text.is_empty() { None } else { Some(text) };
    }
    None
}

#[cfg(test)]
mod tests {
    use super::*;

    fn root() -> PathBuf {
        PathBuf::from("/home/u/llm-wiki-docs")
    }

    #[test]
    fn a_commit_into_another_folder_is_still_a_commit() {
        assert!(runs_a_commit("git -C /some/repo commit -q -m x"));
        assert!(runs_a_commit("git -c user.name=t commit -m x"));
        assert!(runs_a_commit("A=1 B=2 git -C \"/a b\" commit -m y"));
        assert!(runs_a_commit("cd repo && git add -A && git commit -m z"));
        // 낱말이 들어 있을 뿐인 명령은 커밋이 아니다.
        assert!(!runs_a_commit("echo git commit is a command"));
        assert!(!runs_a_commit("git log --format=%s | grep commit"));
    }

    #[test]
    fn a_commit_is_read_from_the_command_not_guessed() {
        assert!(made_a_commit(r#"{"tool_input":{"command":"git commit -m x"}}"#));
        assert!(made_a_commit(r#"{"tool_input":{"command":"cd a && git commit -q -m y"}}"#));
        assert!(!made_a_commit(r#"{"tool_input":{"command":"git status"}}"#));
        // 명령이 없는 사건, 깨진 입력은 커밋이 아니다. 터지지도 않는다.
        assert!(!made_a_commit(r#"{"tool_input":{}}"#));
        assert!(!made_a_commit("not json"));
    }

    #[test]
    fn model_note_has_the_shape_claude_code_reads() {
        let note = model_note("PostToolUse", "줄 하나\n줄 둘 \"따옴표\"");
        let parsed: serde_json::Value = serde_json::from_str(&note).expect("JSON 이어야 한다");
        assert_eq!(parsed["hookSpecificOutput"]["hookEventName"], "PostToolUse");
        // 줄바꿈과 따옴표가 섞여도 원문 그대로 돌아와야 한다. 깨지면 모델이 받는 글이 달라진다.
        assert_eq!(
            parsed["hookSpecificOutput"]["additionalContext"],
            "줄 하나\n줄 둘 \"따옴표\""
        );
        // 출력은 JSON 한 줄뿐이어야 한다. 앞뒤에 다른 글이 섞이면 통째로 버려진다.
        assert!(!note.contains('\n'), "JSON 이 여러 줄로 찍혔다");
    }

    #[test]
    fn stale_only_when_a_page_is_newer_than_the_graph() {
        let early = SystemTime::UNIX_EPOCH;
        let late = early + std::time::Duration::from_secs(10);
        // 페이지가 없으면 맞출 것이 없다
        assert!(!stale(None, None));
        assert!(!stale(None, Some(early)));
        // 그래프가 아직 없으면 첫 빌드가 밀려 있다
        assert!(stale(Some(early), None));
        assert!(stale(Some(late), Some(early)));
        assert!(!stale(Some(early), Some(late)));
        // 같은 시각이면 이미 맞춰진 것으로 본다. 아니면 매번 다시 돈다.
        assert!(!stale(Some(early), Some(early)));
    }

    #[test]
    fn newest_page_ignores_the_index_and_the_log() {
        let dir = std::env::temp_dir().join(format!("kl-gate-test-{}", std::process::id()));
        let wiki = dir.join("t").join("wiki");
        fs::create_dir_all(&wiki).unwrap();
        fs::write(wiki.join("page.md"), "# p").unwrap();
        let with_page = newest_page_mtime(&dir);
        assert!(with_page.is_some(), "페이지를 못 찾았다");

        // 목차와 기록을 나중에 써도 '가장 새 페이지'는 변하지 않아야 한다
        std::thread::sleep(std::time::Duration::from_millis(20));
        fs::write(wiki.join("index.md"), "# i").unwrap();
        fs::write(wiki.join("log.md"), "# l").unwrap();
        assert_eq!(with_page, newest_page_mtime(&dir), "목차·기록을 페이지로 셌다");

        // wiki/ 가 없는 디렉토리는 토픽이 아니다
        fs::create_dir_all(dir.join("not-a-topic")).unwrap();
        fs::write(dir.join("not-a-topic").join("loose.md"), "# x").unwrap();
        assert_eq!(with_page, newest_page_mtime(&dir), "wiki 밖 파일을 셌다");

        fs::remove_dir_all(&dir).ok();
    }

    #[test]
    fn page_inside_a_wiki_is_recognised() {
        assert_eq!(
            wiki_page("/home/u/llm-wiki-docs/a/wiki/pathway.md", &root()),
            Some(("a".into(), "pathway.md".into()))
        );
    }

    /// Regression: this asserted the platform separator and so failed on Windows,
    /// where the gate would then never match a subfolder page against its index
    /// entry. The '/' is part of the contract with index-add.py, not a detail.
    #[test]
    fn subfolders_keep_their_path_so_the_index_entry_matches() {
        assert_eq!(
            wiki_page("/home/u/llm-wiki-docs/a/wiki/sub/deep.md", &root()),
            Some(("a".into(), "sub/deep.md".into()))
        );
    }

    #[test]
    fn machinery_and_outsiders_are_ignored() {
        for p in [
            "/home/u/llm-wiki-docs/a/wiki/index.md",   // the index itself
            "/home/u/llm-wiki-docs/a/wiki/log.md",     // the log
            "/home/u/llm-wiki-docs/a/raw/paper.md",    // raw sources are never indexed
            "/home/u/llm-wiki-docs/a/README.md",       // the schema doc
            "/home/u/llm-wiki-docs/a/wiki/notes.txt",  // not a page
            "/home/u/projects/code/main.md",           // nothing to do with the wiki
            "relative/a/wiki/p.md",                    // no absolute path to match
        ] {
            assert_eq!(wiki_page(p, &root()), None, "should ignore {p}");
        }
    }

    #[test]
    fn indexed_matches_the_entry_format_only() {
        let idx = "## Concepts\n\n- [pathway](pathway.md) — what gating is\n";
        assert!(indexed(idx, "pathway.md"));
        assert!(!indexed(idx, "other.md"));
        // Prose naming the file is not an index entry.
        assert!(!indexed("see pathway.md for details\n", "pathway.md"));
        // A near-miss name must not count as listed.
        assert!(!indexed(idx, "way.md"));
    }

    #[test]
    fn subfolder_entries_match_on_their_full_relative_path() {
        let idx = "- [deep](sub/deep.md) — nested\n";
        assert!(indexed(idx, "sub/deep.md"));
        assert!(!indexed(idx, "deep.md"));
    }
}
