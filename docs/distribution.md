# Release and official discovery handoff

- Standard package: `llama-index-tools-suno-acedatacloud`.
- Native namespace: `llama_index.tools.suno_acedatacloud.SunoToolSpec`.
- Service title: **Suno by Ace Data Cloud**; keywords only Suno, LlamaIndex, music/audio, Ace Data Cloud.
- Scope: music submission plus same-task retrieval. No bundled unrelated services, LLM provider or fallback.
- License: MIT. Maintainer: Ace Data Cloud. Not an official Suno/LlamaIndex product.

## Publication gates

1. Review and merge the source PR only with explicit authorization.
2. An authorized existing PyPI owner configures a new or pending Trusted Publisher for this package:
   owner `AceDataCloud`, repo `SunoLlamaIndex`, workflow `publish.yml`, environment `pypi`.
   No new identity, protocol acceptance or credential is created by this PR.
3. Review release contents and publish tag `v0.1.0`; verify PyPI wheel bytes and install into a new environment.
4. Independent PyPI publication is not an official LlamaIndex directory listing.

## Official docs contribution packet

Official policy: https://github.com/run-llama/llama_index/blob/main/CONTRIBUTING.md
New integration packages must live outside the monorepo. Do not add `pyproject.toml` there.
LlamaHub is archived and its site now points to the current integration docs.

A docs-only draft has been submitted to the externally maintained Tool Specs
subsection of the official tools guide: https://github.com/run-llama/llama_index/pull/23574 .
It clearly links the source/release status rather than claiming a PyPI installation
already works. Keep it draft until source/release gates and maintainer review are satisfied.
The factual entry is:

> **Suno by Ace Data Cloud**: independently maintained LlamaIndex ToolSpec for music
> generation and retrieval of the same asynchronous task. Install
> `llama-index-tools-suno-acedatacloud`, set an Ace application token, and use
> `SunoToolSpec().to_tool_list()`. Generation may consume credits; pending preview
> URLs are not final results. Source and bilingual onboarding:
> https://github.com/AceDataCloud/SunoLlamaIndex

The draft is submitted, not approved or merged. Do not claim a PyPI install
works or a directory listing exists before verifying it. No unsolicited marketing
or review-reminder messages are part of publication.
