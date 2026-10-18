# Release and official discovery

Source implementation is merged. Version: **0.1.0**.

- GitHub release (wheel + sdist): https://github.com/AceDataCloud/SunoLlamaIndex/releases/tag/v0.1.0
- Installable wheel: https://github.com/AceDataCloud/SunoLlamaIndex/releases/download/v0.1.0/llama_index_tools_suno_acedatacloud-0.1.0-py3-none-any.whl
- Package: `llama-index-tools-suno-acedatacloud`.

The existing authorized organization `PYPI_TOKEN` is available; no new account or
Trusted Publisher setup is required for the chosen token publication path. PyPI
new-project creation is temporarily limited for both the account and source IP.
The observed shared reset is 2026-10-20 03:23:23 Asia/Shanghai; publication should
resume only after the reset and a registry readback. No identity or IP workaround.

A published GitHub release builds and attaches the wheel/sdist independently.
The maintainer then uses workflow_dispatch on `publish.yml` with the existing
tag `v0.1.0` to publish the same source after registry quota is available.
Read the registry version/digests first; never replace immutable release files.

Official discovery contribution: https://github.com/run-llama/llama_index/pull/23574 .
It is not accepted or merged yet. New integration packages stay independent under
https://github.com/run-llama/llama_index/blob/main/CONTRIBUTING.md .
GitHub installation, PyPI publication, official listing, native real-task validation
and billing/acquisition are separate stages. The release is not official endorsement.
No paid test, new account, terms acceptance or permission expansion is part of this workflow.
