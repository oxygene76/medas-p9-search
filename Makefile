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
SRC := src/p9sim.c src/p9state.c src/p9encounter.c src/sha256.c src/whfast512_stub.c
# Version compiled into the programs (printed with every result): the VERSION
# file of a package, else git describe.
P9_VERSION ?= $(shell cat VERSION 2>/dev/null || git describe --always --dirty 2>/dev/null || echo unknown)
.DEFAULT_GOAL := $(OUT)/p9sim
# A new version rebuilds every program (the version is compiled in).
VERSION_STAMP := build/.version-$(P9_VERSION)
$(VERSION_STAMP):
	@mkdir -p build && rm -f build/.version-* && touch $@

CFLAGS := -std=c99 -fno-fast-math $(OPT) -ffp-contract=off -D_GNU_SOURCE -DLIBREBOUND -DP9_VERSION='"$(P9_VERSION)"' -I$(REBOUND)/src -Isrc -w $(CFLAGS_EXTRA)
LDLIBS := -lm $(LDFLAGS_EXTRA)

$(OUT)/p9sim: $(SRC) $(REB_SRC) Makefile $(VERSION_STAMP)
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

# ------------------------------------------------------------------ p9gpu (test particles on the GPU)
# CUDA from NVIDIA's pip packages works without root:
#   python3 -m venv build/cuda-venv && build/cuda-venv/bin/pip install nvidia-cuda-nvcc==13.4.92 nvidia-cuda-runtime==13.4.92
# --fmad=false: no fused multiply-add on the GPU (division and sqrt are
# correctly rounded by default); the host part is built with the same flags
# as p9sim. PTX for compute_75 is embedded so that other GPUs can JIT it.
CUDA ?= build/cuda-venv/lib/python3.14/site-packages/nvidia/cu13
NVCC ?= $(CUDA)/bin/nvcc
CUDA_LIB ?= $(CUDA)/lib
# For binaries that run on other systems (the GPU check package): GPU_LINK=g++ GPU_STDCXX=
# GPU_LDFLAGS="-static-libstdc++ -static-libgcc" (g++ then links libstdc++ statically itself;
# an explicit -lstdc++ would bind it dynamically)
GPU_LDFLAGS ?=
GPU_LINK ?= gcc
GPU_STDCXX ?= -lstdc++
GPU_ARCH ?= -gencode arch=compute_120,code=sm_120 -gencode arch=compute_75,code=compute_75
GPU_SRC := gpu/p9gpu.c src/p9state.c src/p9encounter.c src/sha256.c src/whfast512_stub.c
GPU_HDR := gpu/whdh.h gpu/whdh_t.h gpu/df64.h gpu/p9gpu_api.h gpu/p9gpu_real.h
CXX ?= g++
# the templated integrator on the CPU (gpu/cpu_t.cpp): same flags as the C code
GPU_CXXFLAGS := -std=c++17 -fno-fast-math -O3 -ffp-contract=off -Isrc -Igpu -w
GPU_CFLAGS := -std=c99 -fno-fast-math -O3 -ffp-contract=off -D_GNU_SOURCE -DLIBREBOUND -DP9_VERSION='"$(P9_VERSION)"' -I$(REBOUND)/src -Isrc -Igpu -w

.PHONY: gpu gpu-cpu
# GPU_DIR=build/gpu-dev builds elsewhere (e.g. while runs use build/gpu/p9gpu)
GPU_DIR ?= build/gpu
gpu: $(GPU_DIR)/p9gpu
$(GPU_DIR)/p9gpu: gpu/kernel.cu gpu/cpu_t.cpp $(GPU_HDR) $(GPU_SRC) $(REB_SRC) Makefile $(VERSION_STAMP)
	@mkdir -p $(GPU_DIR)
	$(NVCC) -O3 --fmad=false -prec-div=true -prec-sqrt=true $(GPU_ARCH) -Isrc -Igpu -Xcompiler -ffp-contract=off -c gpu/kernel.cu -o $(GPU_DIR)/kernel.o
	$(CXX) $(GPU_CXXFLAGS) -c gpu/cpu_t.cpp -o $(GPU_DIR)/cpu_t.o
	$(GPU_LINK) $(GPU_CFLAGS) -o $@ $(GPU_SRC) $(REB_SRC) $(GPU_DIR)/kernel.o $(GPU_DIR)/cpu_t.o -L$(CUDA_LIB) $(GPU_LDFLAGS) -lcudart_static $(GPU_STDCXX) -ldl -lpthread -lrt -lm
	@echo "gpu: $(NVCC) --fmad=false $(GPU_ARCH); host gcc $(GPU_CFLAGS)" > $(GPU_DIR)/BUILD-FLAGS

# The same integrator without CUDA (P9GPU_MODE=cpu only): reference and CPU speed.
gpu-cpu: build/gpu-cpu/p9gpu
build/gpu-cpu/p9gpu: gpu/cpu_t.cpp $(GPU_HDR) $(GPU_SRC) $(REB_SRC) Makefile $(VERSION_STAMP)
	@mkdir -p build/gpu-cpu
	$(CXX) $(GPU_CXXFLAGS) -c gpu/cpu_t.cpp -o build/gpu-cpu/cpu_t.o
	$(CC) $(GPU_CFLAGS) -DP9_NO_CUDA -o $@ $(GPU_SRC) $(REB_SRC) build/gpu-cpu/cpu_t.o -lstdc++ -lm
	@echo "gpu-cpu: $(CC) $(GPU_CFLAGS) -DP9_NO_CUDA" > build/gpu-cpu/BUILD-FLAGS

# p9gpu's integrator without CUDA as WebAssembly (WASI): the same bits as on the GPU.
.PHONY: gpu-wasm
gpu-wasm: build/gpu-wasm/p9gpu
build/gpu-wasm/p9gpu: gpu/whdh.h $(GPU_SRC) $(REB_SRC) Makefile $(VERSION_STAMP)
	@mkdir -p build/gpu-wasm
	$(ZIG) cc -target wasm32-wasi $(GPU_CFLAGS) -DP9_NO_CUDA -DP9_NO_REAL_T -D_WASI_EMULATED_SIGNAL -D_WASI_EMULATED_PROCESS_CLOCKS \
	  -o $@ $(GPU_SRC) $(REB_SRC) -lwasi-emulated-signal -lwasi-emulated-process-clocks

# ------------------------------------------------------------------ tests
# The encounter radii parser (C) and tools/p9job.py, end to end with p9sim and
# the CPU build of p9gpu (no GPU needed). Builds into build/test and
# build/gpu-cpu; leaves the other builds alone.
PY ?= build/venv/bin/python
.PHONY: test
test: build/test/test_encounter build/test/test_j2 build/test/test_step_encounter gpu-cpu
	$(MAKE) VARIANT=test
	build/test/test_encounter
	build/test/test_j2
	build/test/test_step_encounter
	P9TEST_P9SIM=build/test/p9sim P9TEST_P9GPU=build/gpu-cpu/p9gpu $(PY) -I tests/test_p9job.py -v
	P9TEST_P9SIM=build/test/p9sim P9TEST_P9GPU=build/gpu-cpu/p9gpu $(PY) -I tests/test_flyby.py -v
	P9TEST_P9SIM=build/test/p9sim P9TEST_P9GPU=build/gpu-cpu/p9gpu $(PY) -I tests/test_flyby_regression.py
.PHONY: test-resume
test-resume:
	$(MAKE) VARIANT=test
	P9SIM=build/test/p9sim PY=$(PY) sh tests/test_campaign_resume.sh
build/test/test_step_encounter: tests/test_step_encounter.c gpu/whdh.h
	@mkdir -p build/test
	$(CC) -std=c99 -O2 -Wall -Wextra -ffp-contract=off -Igpu -o $@ tests/test_step_encounter.c -lm
build/test/test_j2: tests/test_j2.c gpu/whdh.h
	@mkdir -p build/test
	$(CC) -std=c99 -O2 -Wall -Wextra -ffp-contract=off -Igpu -o $@ tests/test_j2.c -lm
build/test/test_encounter: tests/test_encounter.c src/p9encounter.c src/p9encounter.h
	@mkdir -p build/test
	$(CC) -std=c99 -O2 -Wall -Wextra -Isrc -o $@ tests/test_encounter.c src/p9encounter.c

# ------------------------------------------------------------------ GPU probes (docs/gpu-performance.md)
.PHONY: gpu-probe
gpu-probe: build/probe/count_ops build/probe/peak
build/probe/count_ops: gpu/probe/count_ops.cpp $(GPU_HDR)
	@mkdir -p build/probe
	$(CXX) $(GPU_CXXFLAGS) -o $@ gpu/probe/count_ops.cpp
build/probe/peak: gpu/probe/peak.cu
	@mkdir -p build/probe
	$(NVCC) -O3 --fmad=false -prec-div=true -prec-sqrt=true $(GPU_ARCH) -o $@ gpu/probe/peak.cu
