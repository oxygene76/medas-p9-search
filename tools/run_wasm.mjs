// SPDX-License-Identifier: GPL-3.0-or-later
// Runs the WebAssembly build of p9sim (WASI preview 1) in Node:
//   node tools/run_wasm.mjs build/zig-wasm32-O3/p9sim <p9sim arguments>
// The whole file system is visible to it ("/" preopened), so paths work as
// for the native build; nothing else (no network, no environment).
import { readFile } from "node:fs/promises";
import { resolve } from "node:path";
import { WASI } from "node:wasi";

// WASI has no current directory (relative paths start at "/"): file arguments
// are made absolute here, numbers and commands stay as they are.
const isPath = (a) => a.includes("/") || /\.(sa|state|txt)$/.test(a);
const [wasmPath, ...rest] = process.argv.slice(2);
const args = rest.map((a) => (isPath(a) && !a.startsWith("/") ? resolve(a) : a));
const wasi = new WASI({ version: "preview1", args: ["p9sim", ...args], env: {}, preopens: { "/": "/" }, returnOnExit: true });
const module = await WebAssembly.compile(await readFile(wasmPath));
const instance = await WebAssembly.instantiate(module, wasi.getImportObject());
process.exitCode = wasi.start(instance);
