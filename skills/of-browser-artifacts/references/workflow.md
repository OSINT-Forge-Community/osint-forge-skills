# Analyze browser history copies notes

Chromium visit times use microseconds since 1601-01-01 UTC; Firefox uses microseconds since the Unix epoch. Clock accuracy, synchronization and connection to a person remain unverified.

The helper uses fixed SQL queries in a private temporary database with immutable/query-only mode and query bounds. Unsupported schemas fail visibly. At most 5,000 events return; truncation remains material.

A delivered copy without its WAL can omit recent rows. An omitted WAL cannot be reliably detected, so snapshot completeness always remains unverified.

An empty history does not prove no browsing. Retention, private browsing, multiple profiles, sync and acquisition coverage may matter. Do not collect adjacent profiles as a workaround.
