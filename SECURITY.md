# Security Policy

## Supported branch

Security fixes are applied to the current `main` branch and to later tagged releases when a release is affected.

## Reporting a vulnerability

Do not open a public issue containing credentials, exploitable secrets, or a working exploit against production infrastructure.

Use GitHub's private vulnerability reporting for this repository when available. Include:

- the affected Asset Forge command or module;
- the smallest reproducible input;
- the expected and observed behavior;
- the security impact;
- whether generated files, external tools, paths, URLs, or credentials are involved.

Never include live API keys, access tokens, private keys, or other production credentials in a report.

## Security boundaries

Asset Forge treats generated content and external tool output as untrusted input. Production paths are expected to remain inside the configured job output directory. Generated assets must pass their format/profile validation before they are considered production-ready.

External tools such as Pollinations, Blender, Godot, Pillow/libwebp, glTF validators, and optimizers are separate trust boundaries. Their availability does not by itself mark an asset as valid.

## Secrets

Secrets must be supplied through the execution environment or the provider's credential store. They must not be committed to this repository, embedded in asset manifests, or persisted in production reports.
