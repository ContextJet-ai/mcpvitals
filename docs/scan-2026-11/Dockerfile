FROM node:22-bookworm
COPY --from=ghcr.io/astral-sh/uv:0.8.4 /uv /uvx /usr/local/bin/
RUN uv tool install --refresh mcpvitals==0.3.0
ENV PATH="/root/.local/bin:$PATH"
WORKDIR /scan
