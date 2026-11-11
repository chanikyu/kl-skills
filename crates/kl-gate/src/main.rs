//! kl-gate — hook entry point for the kl-skills plugin.
//!
//! Claude Code runs this once per hook event, passing the event name as argv[1]
//! and the event payload as JSON on stdin.
//!
//! No rules are enforced yet. This build only proves the install path works:
//! plugin install -> hooks.json -> run.sh/run.ps1 -> correct binary -> here.
//!
//! Exit codes a hook may return (Claude Code contract):
//!   0 = allow, stdout becomes added context
//!   2 = block, stderr is shown to the model
//! Anything a gate cannot decide must exit 0. A hook that errors out on an
//! unexpected payload would break every session that triggers it.

use std::io::Read;

const VERSION: &str = env!("CARGO_PKG_VERSION");

fn main() {
    // Always drain stdin. Leaving the pipe unread can make the caller see a
    // broken pipe instead of a clean exit.
    let mut payload = String::new();
    let _ = std::io::stdin().read_to_string(&mut payload);

    let event = std::env::args().nth(1).unwrap_or_default();

    match event.as_str() {
        "session-start" => {
            println!("KL-SKILLS GATES v{VERSION} — loaded, 0 rules enforced");
        }
        // Unknown or not-yet-implemented event: allow, say nothing.
        _ => {}
    }
}
