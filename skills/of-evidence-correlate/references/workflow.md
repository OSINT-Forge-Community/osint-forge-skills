# Correlate case evidence notes

The helper compares normalized UTC instants and exact URLs. URLs require `url_exact: true`; regenerate legacy browser outputs whose URLs may have been clipped. Skipped URL fields are counted explicitly. It validates input evidence metadata against the case, but derived files can still be edited to mislead. Reproduce analyses before relying on them.

Matching URLs may arise from public resources, synchronization, automation or copied evidence. Matching times can result from rounding or common settings. Neither proves identity, intent or causation.

Redirects and different parameter strings require separate evidence before semantic equivalence can be assumed. Do not strip meaningful URL distinctions silently.

Keep source-origin groups distinct from candidate entities. A repeated name does not prove both documents identify the same individual. No bulk profiling or deanonymization is implied.

## Explain each candidate link

State the exact comparison key, original record indices, date windows and
possible alternative explanations for a shared time or URL. A match can be
coincidental or share an upstream origin. Use explicit premise dependencies
when one conclusion actually supports another. Record what would falsify the
relationship and inspect review warnings after any premise is corrected.
