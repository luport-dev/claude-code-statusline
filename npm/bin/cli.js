#!/usr/bin/env node
/**
 * Wrapper that launches the Python TUI (settings.py) shipped with this package.
 * Tries `python3` first, then `python`. Forwards exit code.
 *
 * Exit code 75 from the TUI signals a user-requested self-update: the wrapper
 * detects the install mode (global vs. npx cache), runs the matching
 * npm/npx command, and re-spawns the TUI.
 */
"use strict";

const { spawnSync } = require("child_process");
const path = require("path");
const fs = require("fs");

const PAYLOAD = path.join(__dirname, "..", "payload");
const SETTINGS_PY = path.join(PAYLOAD, "settings.py");
const PACKAGE_NAME = "@luport-dev/claude-code-statusline";
const UPDATE_EXIT_CODE = 75;

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

function ensureWindowsCurses(python) {
  // Windows Python ships without the _curses C extension. Probe first; only
  // shell out to pip if the import actually fails, so we don't slow down the
  // normal path.
  const probe = spawnSync(python, ["-c", "import _curses"], { stdio: "ignore" });
  if (probe.status === 0) return true;

  console.error("Installing windows-curses (one-time setup)...");
  const install = spawnSync(
    python,
    ["-m", "pip", "install", "--quiet", "--disable-pip-version-check", "windows-curses"],
    { stdio: "inherit" },
  );
  if (install.status !== 0) {
    console.error("");
    console.error("Failed to install windows-curses automatically.");
    console.error("Run this manually, then re-run the installer:");
    console.error("  " + python + " -m pip install windows-curses");
    return false;
  }
  return true;
}

function npmCmd() {
  // On Windows the npm executable is npm.cmd.
  return process.platform === "win32" ? "npm.cmd" : "npm";
}

function npxCmd() {
  return process.platform === "win32" ? "npx.cmd" : "npx";
}

function detectInstallMode() {
  // Resolve the package root (one level up from bin/) and compare against
  // `npm root -g` and `npm config get cache`. Anything inside `_npx/` (npm's
  // npx cache) counts as npx mode; anything under the global node_modules
  // counts as global mode. Otherwise we fall back to npx, which is the safest
  // generic path (it always pulls the latest published version).
  const pkgRoot = path.resolve(__dirname, "..");

  if (pkgRoot.includes(path.sep + "_npx" + path.sep)) return "npx";

  const globalRoot = spawnSync(npmCmd(), ["root", "-g"], { encoding: "utf8" });
  if (globalRoot.status === 0) {
    const root = path.resolve(globalRoot.stdout.trim());
    if (root && pkgRoot.startsWith(root + path.sep)) return "global";
  }

  const cache = spawnSync(npmCmd(), ["config", "get", "cache"], { encoding: "utf8" });
  if (cache.status === 0) {
    const cacheDir = path.resolve(cache.stdout.trim());
    if (cacheDir && pkgRoot.startsWith(cacheDir + path.sep)) return "npx";
  }

  return "npx";
}

function runSelfUpdate() {
  const mode = detectInstallMode();
  const target = `${PACKAGE_NAME}@latest`;

  if (mode === "global") {
    console.log(`\nUpdating ${PACKAGE_NAME} globally…\n`);
    const install = spawnSync(npmCmd(), ["install", "-g", target], { stdio: "inherit" });
    if (install.status !== 0) {
      console.error(`\nUpdate failed. Try manually: npm i -g ${target}`);
      return 1;
    }
    console.log("\nUpdate complete. Re-launching settings…\n");
    // Re-exec the freshly installed wrapper via npm's global bin. We resolve
    // the bin name through `npm bin -g` to avoid hard-coding the path.
    const binDir = spawnSync(npmCmd(), ["bin", "-g"], { encoding: "utf8" });
    let entry = process.argv[1];
    if (binDir.status === 0) {
      const dir = path.resolve(binDir.stdout.trim());
      const candidate = path.join(dir, process.platform === "win32" ? "claude-code-statusline.cmd" : "claude-code-statusline");
      if (fs.existsSync(candidate)) entry = candidate;
    }
    const relaunch = spawnSync(entry, process.argv.slice(2), { stdio: "inherit" });
    return relaunch.status === null ? 1 : relaunch.status;
  }

  // npx mode (and fallback): a fresh `npx -y …@latest` pulls the newest
  // version into the cache and runs it. From the user's perspective the TUI
  // just reopens at the new version.
  console.log(`\nRelaunching with latest version via npx…\n`);
  const relaunch = spawnSync(npxCmd(), ["-y", target, ...process.argv.slice(2)], { stdio: "inherit" });
  if (relaunch.status === null) {
    console.error(`\nRelaunch failed. Run manually: npx -y ${target}`);
    return 1;
  }
  return relaunch.status;
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

  if (process.platform === "win32" && !ensureWindowsCurses(python)) {
    process.exit(1);
  }

  // Force UTF-8 so the TUI's box-drawing chars and emojis render instead of
  // tofu (◇◇) — Windows Python otherwise starts on the legacy cp1252 codec.
  const r = spawnSync(python, [SETTINGS_PY, ...process.argv.slice(2)], {
    stdio: "inherit",
    env: { ...process.env, PYTHONIOENCODING: "utf-8", PYTHONUTF8: "1" },
  });

  const status = r.status === null ? 1 : r.status;
  if (status === UPDATE_EXIT_CODE) {
    process.exit(runSelfUpdate());
  }
  process.exit(status);
}

main();
