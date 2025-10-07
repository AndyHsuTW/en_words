<!--
Sync Impact Report:
Version change: [TEMPLATE] → v1.0.0
Modified principles: All principles defined from existing CONSTITUTION.md
Added sections: 5 core principles + testing strategy + security requirements + governance
Removed sections: None (template filled)
Templates requiring updates: ✅ Updated constitution from detailed project guidelines
Follow-up TODOs: None - all placeholders filled
-->

# SpellVid Project Constitution

## Core Principles

### I. Test-First Development (NON-NEGOTIABLE)
TDD mandatory: Tests written → User approved → Tests fail → Then implement; Red-Green-Refactor cycle strictly enforced; All new features require corresponding unit tests; Integration tests for multi-module functionality; Minimum 80% test coverage required; Tests must be independent, deterministic, and headless-compatible for CI/CD environments.

### II. Code Quality & Style Consistency
Follow PEP 8 with 4-space indentation and snake_case naming; Use type hints for all public functions; Document public APIs with clear docstrings; Internal helpers prefixed with underscore may be imported by tests; Maintain compatibility with existing architecture patterns; Error handling must be explicit and informative.

### III. Backward Compatibility
All changes must maintain compatibility with existing single video processing mode; CLI interface changes require deprecation warnings; Asset path resolution order must remain consistent; FFmpeg integration must support existing environment variable configuration; Configuration schema changes require migration path documentation.

### IV. Security & Input Validation  
All external inputs validated through JSON schema; File paths must be normalized and validated against traversal attacks; Use parameterized subprocess calls to prevent injection; Sensitive data must never be committed to git; Environment variables for sensitive configuration; Regular dependency vulnerability scanning with safety tool.

### V. Asset & Environment Management
Virtual environment isolation mandatory for all development; FFmpeg detection follows priority: env vars → repo-local → imageio-ffmpeg; Asset validation through check_assets() before processing; Headless rendering support for CI/CD; Resource cleanup with proper context managers and temporary directory handling.

## Testing Strategy Requirements

Pytest framework with pytest-cov for coverage reporting; Visual validation using opencv-python for pixel-level boundary checks; Audio validation using pydub for waveform analysis; Integration tests for complete render pipeline; Contract tests for function signatures and behavior; Conditional test skipping when optional dependencies unavailable; Test assets stored in tests/assets/ directory.

## Development Workflow Standards

Feature Branch Workflow with PR review requirements; Conventional Commits format for all commit messages; Branch protection on main requiring CI success and review approval; PowerShell script compatibility for Windows development environment; Documentation updates required for API changes; Agent context files updated automatically via update-agent-context.sh script.

## Governance

Constitution supersedes all other development practices; All PRs must verify compliance with these principles; Complexity deviations require explicit justification and documentation; Version control follows semantic versioning for constitution updates; Quarterly review cycle for principle relevance and effectiveness; Amendment process requires team consensus and impact analysis.

**Version**: v1.0.0 | **Ratified**: 2025-10-07 | **Last Amended**: 2025-10-07