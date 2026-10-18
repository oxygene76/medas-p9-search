// SPDX-License-Identifier: GPL-3.0-or-later
// SHA-256 (FIPS 180-4), small and portable: also for the WebAssembly build.
#ifndef P9_SHA256_H
#define P9_SHA256_H
#include <stddef.h>
#include <stdint.h>
struct sha256_ctx {
    uint32_t h[8];
    uint64_t len;
    uint8_t buf[64];
    size_t n;
};
void sha256_init(struct sha256_ctx* c);
void sha256_update(struct sha256_ctx* c, const uint8_t* data, size_t len);
void sha256_final(struct sha256_ctx* c, uint8_t out[32]);
#endif
