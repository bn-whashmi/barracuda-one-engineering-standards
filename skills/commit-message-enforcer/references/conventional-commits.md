# Conventional Commits Baseline

Conventional Commits defines this structure:

```text
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Key requirements:

- Commits must have a type followed by a colon and space.
- `feat` represents a feature and maps to a minor SemVer change.
- `fix` represents a bug fix and maps to a patch SemVer change.
- Breaking changes are marked with `!` after type or scope, or with a `BREAKING CHANGE:` footer.
- A body starts one blank line after the description.
- Footers start one blank line after the body and follow git trailer-style formatting.

Source: https://www.conventionalcommits.org/en/v1.0.0/
