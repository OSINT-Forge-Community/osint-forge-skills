# Investigate organizations

Use supplied synthetic registry CSV/JSON or selected public filings. Record an entity with `record --input entity.json`, then a relation whose source and target reference existing R entity IDs. A relation describes an analyst assertion, never an automatic merge. Use `graph` to export the evidence-linked relations. Entity records require at least one registered piece.

Jurisdiction-specific identifiers and filing dates are stronger discriminators than labels. Do not infer an ultimate owner through missing links, a shared address, or a registry search with no result. Record each missing link as a research limitation. This workflow produces investigative observations, not a sanctions, legal or credit clearance.

## Jurisdiction and temporal identity

Preserve registry identifiers as scheme/value pairs with jurisdiction. Shared
names and addresses may justify a candidate group but never an automatic merge.
State a relation's matching criteria and validity period; distinguish filing,
publication, acquisition and availability dates. Consult selected source cards
for the relevant jurisdiction, then verify the actual record. Missing ownership
records or reporting exceptions remain gaps rather than a clean result.

## Correct a documented relationship

Schema 4 permits complete superseding entity and relation records. Preserve
the old assertion, supporting pieces and reason for correction. An explicit
retirement withdraws the assertion from the current graph without deleting
its historical links. Reassess conclusions whose argument used the withdrawn
relationship. A recorded correction is not verification of the replacement.
