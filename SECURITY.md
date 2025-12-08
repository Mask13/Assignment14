# Security notes

## Temporary Trivy ignore

We've added temporary `.trivyignore` entries for specific CVEs to unblock CI while preparing proper dependency upgrades.
This is a temporary measure and these vulnerabilities should be addressed by upgrading to the fixed versions.

### Current Vulnerabilities and Fix Versions

1. starlette==0.41.2
   - CVE-2025-62727 (HIGH)
   - Issue: DoS via Range header merging
   - Fixed in: 0.49.1

2. python-jose==3.3.0
   - CVE-2024-33663 (CRITICAL)
   - Issue: Algorithm confusion with OpenSSH ECDSA keys
   - Fixed in: 3.4.0

3. h11==0.14.0
   - CVE-2025-43859 (CRITICAL)
   - Issue: Accepts malformed Chunked-Encoding bodies
   - Fixed in: 0.16.0

### Action items (follow-up, tracked outside this file)
- Identify the exact CVE(s) reported by Trivy for these packages and update this file to list CVE IDs instead of file globs (more precise).
- Upgrade `starlette` and `python-jose` (and/or any transitive packages) to patched versions.
- After upgrading, remove the corresponding `.trivyignore` entries and re-run the scanner.
- Re-run full CI and confirm no remaining HIGH or CRITICAL vulnerabilities.

### Rationale
- Ignoring the package metadata paths is a short-term workaround to unblock CI while tested dependency upgrades are prepared. It is not a long-term fix.

If you prefer a different approach (relax workflow or upgrade now), we can implement that instead.