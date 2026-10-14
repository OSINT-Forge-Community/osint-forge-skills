# Security model and reporting

Threat impact: medium. Selected files, databases, event text and model-facing
documents can be hostile. Helpers reject symlinks and special files, bound
size/record counts, separate raw/derived IO, neutralize output controls, use
fixed read-only SQLite queries, and never run samples or make network calls.

These controls are not a sandbox or protection against a compromised OS/client.
Keep case parents, executables and install receipts under operator control.
Concurrent hostile directory replacement and privileged local attackers are
outside the utility's trust boundary. Enforce host permissions independently.

Private cases and exports contain original content. Heuristic masking is not
anonymization. Human review must cover names, locations, identifiers, sensitive
context and unrecognized credentials before approving the exact public view.
Do not provide credentials or real sensitive samples with a report.

Sovereignty impact: autonomous local content and utilities. Interoperability
adapters are files, with no model API, provider SDK or background collection.
A chosen cloud client retains its external control plane and data policy; the
project does not classify it as sovereign or approve its use for private data.

No public issue tracker or security mailbox has been provisioned. Until a
maintainer publishes a verified private contact, report a fixed error code and
minimal synthetic reproduction through your established maintainer channel.
Do not create a public ticket containing real evidence, secrets or vulnerability
details that unnecessarily expose an affected operator.
