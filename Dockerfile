# Multi-stage Dockerfile for building and testing lilvlib
# Usage:
#   docker build -t lilvlib-build .
#   docker run --rm -v $(pwd)/dist:/dist lilvlib-build
#
# To run only the build stage (skip tests):
#   docker build --target builder -t lilvlib-builder .

# =============================================================================
# Stage 1: Builder - compile python3-lilv and build wheel
# =============================================================================
FROM ubuntu:22.04 AS builder

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates \
    curl \
    debhelper \
    devscripts \
    dpkg-dev \
    git \
    libpcre3-dev \
    meson \
    pkg-config \
    python3-all-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    && rm -rf /var/lib/apt/lists/*

# Ubuntu 22.04's meson (0.61.2) is incompatible with the build
RUN curl -sLO https://launchpad.net/~kxstudio-debian/+archive/ubuntu/toolchain/+files/meson_1.9.1-1kxstudio2_all.deb \
    && dpkg -i meson_1.9.1-1kxstudio2_all.deb \
    && rm meson_1.9.1-1kxstudio2_all.deb

WORKDIR /src
COPY . .

ENV DIST_DIR=/artifacts
RUN ./scripts/build.sh

# =============================================================================
# Stage 2: Tester - validate artifacts in a clean environment
# =============================================================================
FROM ubuntu:22.04 AS tester

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /src
COPY --from=builder /artifacts /artifacts
COPY --from=builder /src/test.py /src/
COPY --from=builder /src/lilvlib /src/lilvlib
COPY --from=builder /src/scripts /src/scripts

ENV DIST_DIR=/artifacts
RUN apt-get update && ./scripts/test.sh && rm -rf /var/lib/apt/lists/*

# =============================================================================
# Final Stage: Artifacts - extract build outputs (runs after tests pass)
# =============================================================================
FROM ubuntu:22.04

WORKDIR /artifacts
COPY --from=tester /artifacts /artifacts

CMD ["sh", "-c", "cp -v /artifacts/* /dist/ 2>/dev/null || echo 'Mount a volume to /dist to extract artifacts: docker run --rm -v $(pwd)/dist:/dist <image>'"]
