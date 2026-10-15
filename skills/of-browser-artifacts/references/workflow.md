# Analyze browser history copies notes

Chromium visit times use microseconds since 1601-01-01 UTC; Firefox uses microseconds since the Unix epoch. Clock accuracy, synchronization and connection to a person remain unverified.

The helper uses fixed SQL queries in a private temporary database with immutable/query-only mode and query bounds. Unsupported schemas fail visibly. At most 5,000 events return; truncation remains material.

SQLite values/rows are limited to 32 KiB, exact URLs to 16 KiB and accepted titles to 8 KiB of UTF-8. Oversize fields and cumulative output are rejected, without saving a partial analysis. A title displayed over 1,000 characters is clipped with `title_truncated: true`. Preserve and safely escape the exact `url`; never automatically open it.

A delivered copy without its WAL can omit recent rows. An omitted WAL cannot be reliably detected, so snapshot completeness always remains unverified.

An empty history does not prove no browsing. Retention, private browsing, multiple profiles, sync and acquisition coverage may matter. Do not collect adjacent profiles as a workaround.

## Coverage and reproducible references

Preserve the supplied backup method, source browser/exporter version, time
window, filters and completeness limitations. A missing visit may reflect
retention or a partial copy. Cite the original record index in derived event
analyses, including index zero; a sorted display position is not that index.
Correlate only decision-relevant exact URLs or times and keep identity and
interaction hypotheses separate from the literal history observation.
