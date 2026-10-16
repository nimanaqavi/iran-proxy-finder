# AI AGENTS PROTOCOL & REPO STANDARDS
# Lead Architects: Hermes Agent & Claude Code
# Cloud Sandbox / Worker: Google Jules

## 1. Architectural Hierarchy
- **Senior Architects (Hermes & Claude Code):** Own 100% of system design, complex multi-file logic, intricate debugging, security-critical implementations, and final PR code reviews.
- **Cloud Worker (Google Jules):** Used strictly as an asynchronous cloud sandbox for:
  - Mechanical migrations and repetitive pattern-based refactors.
  - Exhaustive test suite execution and test coverage expansion.
  - Parallel cloud sandbox benchmarking (`--parallel 2-3`).
  - Isolated low-risk bug fixes.

## 2. Engineering Standards
- **YAGNI & Simplicity:** Do not introduce unrequested abstractions, extra files, or speculative boilerplate. Standard library and native platform features over external packages.
- **Type Safety:** Strict types, explicit interface boundaries, zero `any` types.
- **Verification:** Every change must include a runnable verification check or test suite.
- **Review Gate:** Every Jules cloud PR requires senior review by Claude/Hermes before merging into `main`.

## 3. Environment Constraints
- Tooling Base: `D:\AITools\jules` (No C: drive clutter).
- API Base: `https://jules.googleapis.com/v1alpha`
