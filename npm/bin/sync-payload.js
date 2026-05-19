#!/usr/bin/env node
/**
 * Copy the Python sources from the repo into payload/ so they ship in the npm tarball.
 * Run automatically via `npm pack` / `npm publish` (prepack hook).
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const NPM_DIR = path.join(__dirname, "..");
const PAYLOAD = path.join(NPM_DIR, "payload");

const PAYLOAD_FILES = [
  ["setup/settings.py", "settings.py"],
  ["scripts/statusline.py", "statusline.py"],
];

const ROOT_FILES = [
  ["README.md", "README.md"],
  ["LICENSE", "LICENSE"],
];

fs.mkdirSync(PAYLOAD, { recursive: true });

for (const [src, dest] of PAYLOAD_FILES) {
  const srcAbs = path.join(ROOT, src);
  const destAbs = path.join(PAYLOAD, dest);
  if (!fs.existsSync(srcAbs)) {
    console.error("missing: " + srcAbs);
    process.exit(1);
  }
  fs.copyFileSync(srcAbs, destAbs);
  console.log("copied: " + src + " -> payload/" + dest);
}

for (const [src, dest] of ROOT_FILES) {
  const srcAbs = path.join(ROOT, src);
  const destAbs = path.join(NPM_DIR, dest);
  if (!fs.existsSync(srcAbs)) {
    console.error("missing: " + srcAbs);
    process.exit(1);
  }
  fs.copyFileSync(srcAbs, destAbs);
  console.log("copied: " + src + " -> " + dest);
}
