FROM mcr.microsoft.com/devcontainers/python:1-3.12-bookworm

# System packages useful for AI / audio / media workflows.
# Base image ships a yarn apt source with a rotated/missing GPG key; drop it
# before apt-get update (Node feature installs yarn without that apt repo).
# Electron/Chromium runtime for apps/desktop (GUI via desktop-lite or xvfb).
RUN rm -f /etc/apt/sources.list.d/yarn.list \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
        ffmpeg \
        libsndfile1 \
        curl \
        jq \
        libnss3 \
        libatk-bridge2.0-0 \
        libgtk-3-0 \
        libgbm1 \
        libasound2 \
        libx11-xcb1 \
        libxss1 \
        libxtst6 \
        libdrm2 \
        libxcomposite1 \
        libxdamage1 \
        libxrandr2 \
        libxkbcommon0 \
        fonts-liberation \
        dbus-x11 \
        xvfb \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Keep pip/tooling current inside the image
RUN python -m pip install --upgrade pip setuptools wheel
