#!/usr/bin/env sh
set -eu

ollama pull "${OLLAMA_MODEL:-qwen2.5-coder:7b}"
