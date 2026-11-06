FROM ubuntu:26.04@sha256:6a06111c3b0a8600feadb270aec771dc239bf407b25625f93f44ab00e11f4d3c
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    squashfs-tools xorriso python3 python3-pil python3-yaml rsync \
    ca-certificates curl file cpio xz-utils zstd binutils \
    imagemagick sbsigntool gnupg kmod \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /work
