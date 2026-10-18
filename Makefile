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

CFLAGS := -std=c99 $(OPT) -fno-fast-math -ffp-contract=off -D_GNU_SOURCE -DLIBREBOUND -I$(REBOUND)/src -Isrc -w $(CFLAGS_EXTRA)
LDLIBS := -lm $(LDFLAGS_EXTRA)

$(OUT)/p9sim: $(SRC) $(REB_SRC) Makefile
	@mkdir -p $(OUT)
	$(CC) $(CFLAGS) -o $@ $(SRC) $(REB_SRC) $(LDLIBS)
	@echo "$(VARIANT): $(CC) $(CFLAGS)" > $(OUT)/BUILD-FLAGS

.PHONY: clean
clean:
	rm -rf build/gcc* build/clang* build/zig*
