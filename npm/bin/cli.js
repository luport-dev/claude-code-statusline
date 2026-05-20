#!/usr/bin/env node
/**
 * Wrapper that launches the Python TUI (settings.py) shipped with this package.
 * Tries `python3` first, then `python`. Forwards exit code.
 */
"use strict";

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const PAYLOAD = path.join(__dirname, "..", "payload");
const SETTINGS_PY = path.join(PAYLOAD, "settings.py");

function findPython() {
  const candidates = process.platform === "win32"
    ? ["python", "python3", "py"]
    : ["python3", "python"];
  for (const cmd of candidates) {
    const r = spawnSync(cmd, ["--version"], { stdio: "ignore" });
    if (r.status === 0) return cmd;
  }
  return null;
}

function main() {
  if (!fs.existsSync(SETTINGS_PY)) {
    console.error("Error: settings.py not found in package payload.");
    console.error("Expected: " + SETTINGS_PY);
    process.exit(1);
  }

  const python = findPython();
  if (!python) {
    console.error("Error: Python 3 not found in PATH.");
    console.error("Install Python 3 from https://www.python.org/ and try again.");
    if (process.platform === "win32") {
      console.error("Also install: pip install windows-curses");
    }
    process.exit(1);
  }

  // Force UTF-8 so the TUI's box-drawing chars and emojis render instead of
  // tofu (◇◇) — Windows Python otherwise starts on the legacy cp1252 codec.
  const r = spawnSync(python, [SETTINGS_PY, ...process.argv.slice(2)], {
    stdio: "inherit",
    env: { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1" },
  });
  process.exit(r.status === null ? 1 : r.status);
}

main();
