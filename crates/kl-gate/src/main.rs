//! kl-gate — hook entry point for the kl-skills plugin.
//!
//! Claude Code runs this once per hook event, passing the gate name as argv[1]
//! and the event payload as JSON on stdin.
//!
//! Exit codes (Claude Code contract):
//!   0 = allow; stdout is handed to the model as context
//!   2 = block; stderr is shown to the model
//! A gate that cannot decide exits 0. Erroring out on an unexpected payload
//! would break every session that triggers the event, which is a far worse
//! outcome than a rule going unenforced once.

use std::io::Read;
use std::path::{Path, PathBuf};

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
                "KL-SKILLS GATES v{VERSION} — loaded, 3 rules enforced \
                 (wiki-index-check, wiki-graph, prose-check)"
            );
        }
        "wiki-index-check" => wiki_index_check(&payload),
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

fn wiki_index_check(payload: &str) {
    let Some(root) = wiki_root() else { return };
    let Ok(v) = serde_json::from_str::<serde_json::Value>(payload) else { return };
    let Some(file_path) = v["tool_input"]["file_path"].as_str() else { return };
    let Some((topic, page)) = wiki_page(file_path, &root) else { return };

    let index = root.join(&topic).join("wiki").join("index.md");
    // No index at all is a different problem, and new-topic.sh is the fix for it.
    let Ok(text) = std::fs::read_to_string(&index) else {
        println!(
            "! {topic}/wiki/index.md is missing, so nothing written here can be found.\n  \
             refill it:  sh \"{}\" {topic}",
            script("new-topic.sh")
        );
        return;
    };

    if indexed(&text, &page) {
        return;
    }

    println!(
        "! {page} is not listed in {topic}/wiki/index.md — a page missing from the \
         index is a page nobody finds.\n  add it:  python3 \"{}\" {topic} {page} \
         <category> \"one line on what it holds\"",
        script("index-add.py")
    );
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

#[cfg(test)]
mod tests {
    use super::*;

    fn root() -> PathBuf {
        PathBuf::from("/home/u/llm-wiki-docs")
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
