# SunoLlamaIndex

This repository owns `llama-index-tools-suno-acedatacloud`, a standalone LlamaIndex BaseToolSpec integration. It is maintained by Ace Data Cloud and is not an official Suno or LlamaIndex product.

- `llama_index/tools/suno_acedatacloud/` owns the native tool adapter; reuse the published `acedatacloud` SDK. Do not copy or modify shared SDK/MCP implementations here.
- Keep sync and async native tool signatures aligned. Generation sends once with retries disabled. Query the same task ID; pending preview URLs are not final media.
- Do not expose credentials in tool schemas, output, docs, screenshots, or commits. No `.env` files.
- Models are explicit inputs; do not add default model fallbacks or prices.
- Install `.[dev]`, then run `ruff check .`, `ruff format --check .`, `pytest`, `python -m build`, and install the wheel in a separate consumer environment.
- Tests use mock HTTP only. Never run a billable generation as an automatic test.
- Follow the parent Index worktree and bot-PR rules. Do not merge without current explicit authorization.
