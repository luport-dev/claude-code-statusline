# AGENTS.md — claude-code-statusline (Cerebro)

This repo belongs to **Cerebro**, a second-brain knowledge system.
Cerebro vault: `/home/luport-dev/Dropbox/cerebro` · Project note: `40-projects/claude-code-statusline/claude-code-statusline.md`

Cerebro note: `40-projects/claude-code-statusline/claude-code-statusline.md`

## 🔹 Project
- ID: claude-code-statusline · Stack: Python 3 + Node.js wrapper · Version: 0.1.15

## ⚖️ Binding rules (stable, always follow)
- **SemVer:** maintain MAJOR.MINOR.PATCH correctly.
- **Changelog:** document every version in `CHANGELOG.md` (+ vault `log.md`).
- **TDD where possible:** test first, then code, then refactor.
- **Capture knowledge:** document new decisions/insights/rules.
- **Focused & atomic:** concise, one purpose per note, link.

### Project-specific (see vault `rules/`)
- **Windows UTF-8:** force UTF-8 console encoding at every Python and Node entrypoint.
- **Payload sync:** edit Python sources, never `npm/payload/`; `prepack` regenerates it.
- **Self-update:** TUI exit code 75 ↔ Node wrapper relaunch — keep both halves in sync.
- **Visual checks:** validate rendering with `scripts/preview.py` (no automated asserts).

## 💼 Vault usage (if reachable)
If you can read the Cerebro vault at `/home/luport-dev/Dropbox/cerebro`:
1. Read `00-kernel/cerebro.md` and `20-rules/` for the complete rules.
2. Read the project notes under `40-projects/claude-code-statusline/`.
3. Capture new knowledge there (see protocol).
If not reachable: follow the rules above.
