# Reproducibility of p9sim

Goal: the same job gives the same `result_sha256` on every machine, compiler,
optimisation level and target. Checked on 2026-10-18 on one machine (Intel Core
Ultra 9 275HX, WSL2, Ubuntu 26.04) with `tools/repro_matrix.sh` and the check
package (`tools/make_check_package.sh`).

## What is hashed

`result_sha256` is SHA-256 over the canonical states of all snapshots of a run:
per snapshot "P9STATE2", t, N, then per particle id, m, x, y, z, vx, vy, vz as
little-endian IEEE-754 binary64 (see `src/p9sim.c`). Not the SimulationArchive
file: REBOUND writes wall times, a random seed and platform-dependent fields into
it (the WebAssembly output of the same run is 21 bytes shorter than the native
one, with identical states).

## Rules that make it work

- The start state is computed once (`tools/make_ic.py`: DE440s, rotations, elements
  to states with numpy) and handed over as exact decimals (`p9sim init`) and then as
  a binary SimulationArchive. No machine converts elements itself, so libm
  differences (sin, cos, atan2, …) never enter.
- The integration (WHFast, democratic heliocentric, fixed step) uses only + − × ÷
  and sqrt, all correctly rounded in IEEE-754. This holds for WHFast and for p9gpu
  with its CPU twin. It does **not** hold for MERCURIUS (see the correction below).
- Build without `-ffast-math` and with `-ffp-contract=off` (no fused
  multiply-add). The Makefile sets both for every variant.
- Particles are identified by an integer id (stored in the radius field), not by
  name (see "Deviations").
- Removal of test particles happens at fixed step counts (every 1000 steps), the
  same on every machine; restarts from a snapshot continue bit-identically
  (checked: one run of 10,000 years against two of 5,000 years).

## Correction of 2026-11-11: MERCURIUS and the libm function cbrt

The matrix below used a WHFast job only. The ARM64 study of 2026-11-11 (`docs/arm64-repro-study.md` on the branch
feat/arm64-repro) found the following.
- **The cause:** REBOUND's MERCURIUS computes the planets' critical radii with `cbrt` (`integrator_mercurius.c`),
  which comes from the system's libm. glibc's `cbrt` is not correctly rounded; musl's (and zig's) is.
  - On the masses of Uranus and Planet Nine they differ by 1 ulp.
  - glibc on aarch64 builds the same code with FMA and differs from glibc on x86-64 on about 20 % of all arguments.
- **Bit-identical on every platform:** WHFast, and p9gpu with its CPU twin (no transcendental libm call).
- **MERCURIUS (p9sim) so far bit-identical only with glibc on x86-64.**
  - With zig/musl, 4 of the 38 MERCURIUS check cases of p9pair-merc differ, on x86-64 and on ARM64 alike.
  - gcc + glibc on ARM64 passes the 38 cases only because the six job masses happen to agree.
  - The WebAssembly build presumably behaves like musl (not run end to end).
- **The MERCURIUS runs so far** (equivalence group M, long runs 110–112, paired tests) ran on x86-64 with glibc. They
  passed the package checks there, so their results stand.
- **The fix:** from a new p9sim binary on, p9sim has its own `cbrt`, which reproduces glibc's generic algorithm bit for
  bit on every platform. It is for future packages only. The running and registered packages and their binaries stay
  unchanged.
- The text above as of 2026-10-18 stays in the history unchanged, as it was notarised.

## Matrix (job 0667d88a…, 100 test particles, 1 Myr, 2,000,000 steps, 10 snapshots)

| Build | Compiler / runtime | result_sha256 | Wall time |
|---|---|---|---|
| gcc -O3 (twice) | gcc 15.2.0, glibc, x86-64 | fcabef5a219907ac… | 34.4 s, 35.9 s |
| gcc -O2 | gcc 15.2.0 | fcabef5a219907ac… | 39.2 s |
| clang -O3 / -O2 | clang 21.1.8 (Ubuntu) | fcabef5a219907ac… | 38.9 s / 39.1 s |
| WebAssembly -O3 / -O2 | zig 0.16.0 (clang 21.1.0), wasm32-wasi, Node 22.22.1 | fcabef5a219907ac… | 34.3 s / 34.2 s |
| ARM64 -O3 / -O2 | zig 0.16.0, aarch64-linux-musl static, qemu-aarch64 10.2.1 | fcabef5a219907ac… | 373 s / 372 s (emulated) |
| Debian container | gcc 14.2.0 (Debian trixie), glibc | fcabef5a219907ac… | 35.6 s |
| Debian container, ARM64 | gcc 14.2.0, Docker's arm64 emulation | df6e8803… (control job) = expected | 12.4 s (control) |
| **counter-example** FMA | gcc -O3 -march=x86-64-v3 -ffp-contract=fast | a9f6a07e… (differs) | 30.4 s |
| **counter-example** fast-math | gcc -O3 -ffast-math | 22c774c8… (differs) | 33.9 s |
| **counter-example** ARM64 FMA | zig ARM64 -ffp-contract=fast | 35d65b86… (differs) | 359 s |

Full hash of the matrix: `fcabef5a219907aca435aee0d820122db7d63a67ae37da93c6292978368d7d80`.
WebAssembly in Node runs as fast as native code here.

## Deviations found, causes, remedies

1. **WebAssembly: particle names garbled** (first hash differed although every
   number was identical: "iter" instead of "Jupiter"). Cause: REBOUND 5.2.2 stores
   the particle name list in the SimulationArchive together with the original
   `char*` pointers (`binarydata.c`, `REB_CHARP_LIST`; the source says "This pointer
   arithmetic will fail on 32 bit architectures") and reads it back with the
   reader's pointer size, 4 bytes on wasm32. Remedy: the canonical state uses
   numeric ids stored in the particle radius `r` (unused by WHFast without
   collisions), not names. Names stay for reading. A report to REBOUND upstream
   would make sense (not done).
2. **FMA (fused multiply-add)** changes the rounding of a·b+c. x86 with
   `-march=x86-64-v3` and ARM64 by default contract such expressions when allowed.
   Remedy: `-ffp-contract=off`, set in the Makefile for every build.
3. **-ffast-math** allows reassociation and other value-changing rewrites. Remedy:
   never use it; the Makefile puts `-fno-fast-math` first.

How large such differences become: after 1 Myr the planets of the counter-examples
differ by 10⁻⁷ au, but test particles with close encounters by up to 1,000 au.
The orbits are chaotic; any rounding difference grows exponentially. Statistics
over many particles stay comparable, single trajectories do not; that is why
results are compared bit for bit.

## Not yet checked

- A real second machine (the check package is ready: `build/p9check-<commit>.tar.gz`).
- macOS (clang, libSystem), Windows, a real ARM CPU (only emulated so far), and
  WebAssembly in a browser engine other than Node's V8.
