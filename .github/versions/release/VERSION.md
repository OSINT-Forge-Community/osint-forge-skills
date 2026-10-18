# Release platform history

These four-part delivery versions track source changes independently of the
package SemVer in `VERSION` and the plugin manifests. This history begins with
the platform convention; earlier three-part commit titles are not rewritten.
The first entry advances the existing 0.2.0 product baseline for compatible
features. Recording an entry does not publish a package or authorize a push.

## 0.3.0.0 - 2026-10-18

Summary: Add prioritized case review and a count-only MCP summary, refresh the
private HTML review dashboard, and index event citations for faster selection.
Introduce platform delivery histories and the signed commit convention.

Threat impact: Keep review read-only, restrict MCP output to aggregate counters,
detect persistent journal changes, and preserve bounded parsing, escaping and CSP.

Sovereignty impact: Keep the standard-library runtime offline and all evidence
and generated reports local; add no provider, telemetry or external dependency.

Validation: 192 local tests passed; generated skills and archives were checked.
Local commit status: `verification-pending` until complete pre-push checks pass.
