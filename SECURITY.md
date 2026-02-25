# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 1.x     | Yes       |

## Reporting a Vulnerability

Please report security vulnerabilities through one of these channels:

1. **GitHub Security Advisory** (preferred): [Open a private advisory](https://github.com/merlijntishauser/unifi-topology/security/advisories/new)
2. **Email**: Contact the maintainer directly

Do **not** open a public issue for security vulnerabilities.

## Response Timeline

- **Acknowledgement**: Within 7 days
- **Initial assessment**: Within 14 days
- **Fix release**: Depends on severity (critical: ASAP, high: within 30 days)

## Scope

This library connects to UniFi controllers on local networks. Security concerns include:

- SSL/TLS handling (self-signed certificate support)
- Credential handling in configuration
- Cache file permissions
- SVG output sanitization (XSS prevention)
- Environment variable validation

See `docs/roadmap.md` for known security items being tracked.
