# Build an evidence timeline notes

JSON accepts an event array or an object with events. JSONL uses one object per line. CSV needs event and timestamp columns. Missing timestamps remain explicitly uncertain; no timezone default applies.

Rows retain the piece ID and zero-based source-record index. Known UTC rows sort first; unknown rows retain source order and must not be interpreted as later events.

An ambiguous daylight-saving local time needs an offset or clock-context export. A minute-resolution timestamp cannot justify second-level sequencing.

CSV escapes spreadsheet formula prefixes while JSON retains original timestamps. Vendor binary logs, raw EVTX and arbitrary text formats need a trusted structured export. Parse failure is a gap, not an empty timeline.
