# The check in a container: a different compiler (Debian's gcc) and libc than
# the reference machine. Build and run:
#   docker build -t p9check . && docker run --rm p9check
# For ARM64 (with emulation or on an ARM machine): docker build --platform linux/arm64 ...
FROM debian:trixie-slim
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev make && rm -rf /var/lib/apt/lists/*
WORKDIR /p9check
COPY . .
CMD ["sh", "run-check.sh"]
