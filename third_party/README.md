# Third-party code

## REBOUND 5.2.2

- N-body integrator by Hanno Rein and contributors, https://github.com/hannorein/rebound
- Version: tag 5.2.2 (released 2026-10-05)
- Source: https://codeload.github.com/hannorein/rebound/tar.gz/refs/tags/5.2.2
- sha256 of that archive: `86038080c4392c8c19c4df2004d1804b30ca2aebd3c0329bfd1b02afc41d6eda`
- Licence: GNU GPL version 3 or (at your option) any later version (`LICENSE` in the
  archive; header of `src/rebound.h`). This repository is therefore GPL-3.0-or-later as a whole.
- Fetched and checked by `scripts/fetch-rebound.sh`; not committed.
- Used unmodified. Not compiled: `glad.c` (OpenGL loader), `communication_mpi.c` (MPI),
  `server.c` (web server), `integrator_whfast512.c` (AVX-512 assembly; replaced by
  `src/whfast512_stub.c`, which can not be selected).

Citation for results: Rein & Liu 2012, A&A 537, A128 (REBOUND); Rein & Tamayo 2015,
MNRAS 452, 376 (WHFast).
