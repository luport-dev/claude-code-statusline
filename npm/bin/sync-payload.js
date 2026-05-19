#!/usr/bin/env node
/**
 * Copy the Python sources from the repo into payload/ so they ship in the npm tarball.
 * Run automatically via `npm pack` / `npm publish` (prepack hook).
 */
"use strict";

const fs = require("fs");
const path = require("path");

const ROOT = path.join(__dirname, "..", "..");
const PAYLOAD = path.join(__dirname, "..", "payload");

const FILES = [
  ["setup/settings.py", "settings.py"],
  ["scripts/statusline.py", "statusline.py"],
];

fs.mkdirSync(PAYLOAD, { recursive: true });

for (const [src, dest] of FILES) {
  const srcAbs = path.join(ROOT, src);
  const destAbs = path.join(PAYLOAD, dest);
  if (!fs.existsSync(srcAbs)) {
    console.error("missing: " + srcAbs);
    process.exit(1);
  }
  fs.copyFileSync(srcAbs, destAbs);
  console.log("copied: " + src + " -> payload/" + dest);
}
