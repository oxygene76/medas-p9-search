# medas-p9-search

Orbit integrations for a search for Planet Nine. **Pilot, local only**: no
distribution to clients, no chain entries, never on production systems.

- `src/p9sim.c` – the integration program on REBOUND 5.2.2 (WHFast, democratic
  heliocentric coordinates): `init`, `run`, `last`, `state`, `dump`.
- `tools/make_ic.py` – start values of the test case after Brown & Batygin (2021).
- `tools/p9job.py` – work packages: description, hashes, run, check.
- `third_party/README.md` – REBOUND version, checksum and licence.

```sh
scripts/fetch-rebound.sh
make                                  # gcc -O3 -> build/gcc-O3/p9sim
make CC=clang OPT=-O2                 # other compilers and levels
python3 -m venv build/venv && build/venv/bin/pip install -r tools/requirements.txt
build/venv/bin/python tools/p9job.py make --out runs/demo --t-end 10000 --snapshots 4 --tp-to 100
build/venv/bin/python tools/p9job.py run runs/demo
```

Licence: GPL-3.0-or-later (REBOUND is GPL-3.0-or-later; see `LICENSE`).
