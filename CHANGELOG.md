# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- pytest test suite with token tracker smoke tests
- GitHub Actions CI workflow (Python 3.11 + 3.12 matrix)
- Ruff linting in CI
- Badges in README (CI, Python, license, MiMo-powered)
- CONTRIBUTING.md with PR workflow

## [0.1.0] - 2026-05-26

### Added
- Initial scaffold with FastAPI gateway
- 4-agent fan-out: translator, summarizer, extractor, synthesizer
- Token tracker with per-agent breakdown
- 3-pass translation pipeline (literal → idiomatic → review)
- OpenClaw skill manifest in `skill/SKILL.md`
- Real-run example in `docs/EXAMPLE_RUN.md` (12,271 tokens, ZH→ID Alibaba OSS)
- Architecture diagram in `docs/ARCHITECTURE.md`
- MiMo Orbit 100T application draft in `docs/MIMO_APPLICATION.md`
- Dockerfile for production deploy
- Sample inputs in `examples/`
