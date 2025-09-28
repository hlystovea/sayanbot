FROM ghcr.io/astral-sh/uv:python3.11-alpine

WORKDIR /sayanbot

COPY pyproject.toml uv.lock ./

RUN uv sync --locked

COPY . .
