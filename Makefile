# Builds p9sim with REBOUND (third_party/rebound-<version>, see third_party/README.md).
#
#   make                       gcc -O3 into build/gcc-O3/p9sim
#   make CC=clang OPT=-O2      clang -O2 into build/clang-O2/p9sim
#   make VARIANT=name CC=... CFLAGS_EXTRA=... LDFLAGS_EXTRA=...
#
# Never -ffast-math (it allows reassociation and other value-changing
# rewrites); -ffp-contract=off forbids fused multiply-add, which some targets
# (ARM64, WebAssembly with relaxed SIMD, x86 with -march=native) would
# otherwise use and which rounds differently. -fno-math-errno and friends are
# not needed: integration uses only + - * / and sqrt.

REBOUND_VERSION := 5.2.2
REBOUND := third_party/rebound-$(REBOUND_VERSION)
ifeq ($(origin CC),default)
CC := gcc
endif
OPT ?= -O3
CCNAME := $(notdir $(firstword $(CC)))
VARIANT ?= $(CCNAME)$(OPT)
OUT := build/$(VARIANT)

# REBOUND sources: everything but the OpenGL loader, MPI, the web server and
# WHFast512 (AVX-512 assembly; replaced by src/whfast512_stub.c). display.c is
# needed for its settings; its OpenGL part is off without -DOPENGL.
REB_SRC := $(filter-out %/glad.c %/communication_mpi.c %/server.c %/integrator_whfast512.c,$(wildcard $(REBOUND)/src/*.c))
SRC := src/p9sim.c src/sha256.c src/whfast512_stub.c

CFLAGS := -std=c99 -fno-fast-math $(OPT) -ffp-contract=off -D_GNU_SOURCE -DLIBREBOUND -I$(REBOUND)/src -Isrc -w $(CFLAGS_EXTRA)
LDLIBS := -lm $(LDFLAGS_EXTRA)

$(OUT)/p9sim: $(SRC) $(REB_SRC) Makefile
	@mkdir -p $(OUT)
	$(CC) $(CFLAGS) -o $@ $(SRC) $(REB_SRC) $(LDLIBS)
	@echo "$(VARIANT): $(CC) $(CFLAGS)" > $(OUT)/BUILD-FLAGS

.PHONY: clean
clean:
	rm -rf build/gcc* build/clang* build/zig*

# Cross builds with zig (https://ziglang.org, 0.16.0: clang 21 with musl and WASI libcs).
ZIG ?= zig
.PHONY: aarch64 wasm
aarch64:   # static ARM64 binary (musl); run with qemu-aarch64 on x86
	$(MAKE) VARIANT=zig-aarch64$(OPT) CC="$(ZIG) cc -target aarch64-linux-musl -static"
wasm:      # WebAssembly (WASI preview 1); run with: node tools/run_wasm.mjs build/zig-wasm32$(OPT)/p9sim ...
	$(MAKE) VARIANT=zig-wasm32$(OPT) CC="$(ZIG) cc -target wasm32-wasi" \
	  CFLAGS_EXTRA="-D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS" \
	  LDFLAGS_EXTRA="-lwasi-emulated-signal -lwasi-emulated-process-clocks"

# Counter-examples for the reproducibility check (never for real runs):
# fused multiply-add and -ffast-math change the rounding, so the hash changes.
.PHONY: counterexamples
counterexamples:
	$(MAKE) VARIANT=gcc-O3-fma CC=gcc OPT="-O3 -march=x86-64-v3" CFLAGS_EXTRA="-ffp-contract=fast"
	$(MAKE) VARIANT=gcc-O3-fastmath CC=gcc OPT="-O3 -ffast-math"
