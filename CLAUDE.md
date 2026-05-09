# Neteye — Claude Code Instructions

## Branching

Always create a feature branch before making any code changes.
Direct commits to `master` are prohibited.

Branch naming conventions:
- Bug fixes: `fix/<description>`
- New features: `feature/<description>`
- Refactoring: `refactor/<description>`
- Documentation: `docs/<description>`

After completing work, open a PR and merge into `master`.

## Commit Messages

- Do not include Co-Authored-By
- Before committing, always show a summary of changes and `git diff`, and wait for user confirmation

## Proposing Recommendations

When proposing alternatives or recommendations, always evaluate from the following three perspectives, then state the recommended option with reasoning.

1. **Network Engineer perspective**: Network operations and design (observability, incident response, operational conventions)
2. **Software Engineer perspective**: Code quality, maintainability, and security (naming conventions, design patterns, standards)
3. **Critical perspective**: Weaknesses, trade-offs, and overlooked risks of the above two options

→ **Recommendation**: `<option name>` — `<1–2 sentence rationale>`
