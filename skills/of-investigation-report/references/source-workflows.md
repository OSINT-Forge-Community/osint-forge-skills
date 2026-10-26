# Dated source cards and supplied exports

`sources --category organization --jurisdiction FR` filters the bundled static
cards. Other categories are domain, archive and imagery; omit filters to see all
nine cards. Commands do not visit the listed pages. Every card records publisher,
jurisdiction, languages, accepted selectors, coverage, time limits, interpretation
limits, access considerations and potential outbound data. Documentation was
reviewed on 15 October 2026; APIs and actual research queries were not tested.

## Choose a source for the question

| Card | Reference | Use and interpretation limit |
| --- | --- | --- |
| `inpi-rne` | [DATA INPI](https://data.inpi.fr/) | RNE records and filings; distinguish a legal entity, its brands and dated roles. |
| `bodacc` | [BODACC](https://www.bodacc.fr/) | Published civil/commercial announcements; publication is not implementation. |
| `gleif` | [GLEIF data](https://www.gleif.org/en/lei-data/gleif-golden-copy/download-the-golden-copy) | LEIs and accounting parent records; reporting exceptions prevent a complete ownership inference. |
| `companies-house` | [Companies House](https://find-and-update.company-information.service.gov.uk/) | UK company records; filed information is not independently verified by registration. |
| `ted` | [TED search documentation](https://docs.ted.europa.eu/api/latest/search.html) | Procurement notices; distinguish planned procurement, award and actual implementation. |
| `rdap` | [ICANN RDAP](https://www.icann.org/rdap) | Find authoritative registration sources; distinguish registrant, registrar and hosting roles. |
| `wayback` | [Wayback guidance](https://help.archive.org/help/using-the-wayback-machine/) | Available historical captures; missing snapshots do not prove absence. |
| `copernicus` | [Copernicus Browser](https://documentation.dataspace.copernicus.eu/Applications/Browser.html) | Dated imagery; resolution, clouds and viewing geometry constrain comparison. |
| `nominatim` | [Nominatim policy](https://operations.osmfoundation.org/policies/nominatim/) | Public-place candidates; geocoding is not scene verification and service restrictions apply. |

Select the primary record that could distinguish the hypotheses. Use the
source's original language and record any translated query separately. Retain
exact legal identifiers, effective dates, publication dates and acquisition
context. Do not grade a claim by the number of portals repeating one filing.

Before client research, check the provider's current documentation, access
requirements and terms. The query identifies interests to that provider;
following target links can contact the target. Uploading a local file or asking
an archive to publish a new capture is a separate transmission. No card grants
permission, supplies an API endpoint, installs a provider or recommends an account.

For example, a synthetic Harbor Example Ltd name match leads to a registry
identifier and jurisdiction check. It does not establish a relationship. If the
record is unavailable, log that state and ask for the smallest useful extract.

## Supplied public exports and timed transcripts

Register the selected original with `add` before parsing it. The three commands
below read registered bytes and write a new analysis under the case. They never
contact a provider, fetch a capture, transcribe media or install another MCP.
Each output retains the evidence ID and SHA-256, source record indexes and
explicit coverage limits. An empty selection describes only the supplied export.

| Command | Accepted input | Interpretation |
| --- | --- | --- |
| `wayback-index` | CDX JSON table with a header row including `original` and `timestamp`, or `[]` | Select an exact URL and optional inclusive capture-date window. Sort captures by their declared UTC timestamp. Preserve redirects, duplicates and other CDX columns. |
| `bodacc-history` | Flat BODACC JSON object array, or Explore API v2 `results` with optional `total_count` | Select an exact nine-digit SIREN in `registre` and order by `dateparution`. Preserve each selected notice and its ID. A provider total larger than the export is marked partial. |
| `transcript` | UTF-8 SRT or a bounded WebVTT cue subset | Preserve cue text, source line ranges and millisecond start/end offsets. Declare the transcription method and translation status without claiming verification. |

For CDX, `record_index` starts at zero after the header. `source_row` is the
zero-based position in the original JSON table including its header. Do not
infer page contents from the index. Acquire any selected capture separately,
register it, use `capture` for supplied HTML and `compare` for its derived text.
Document how the supplied capture maps to the selected index entry.

BODACC rows use `id`, `registre` and `dateparution`. `registre` accepts one
string or an array of nine-digit strings, optionally containing ordinary or
nonbreaking spaces. Missing registers are counted as unmatchable. Other formats,
including legacy v1 wrappers, CSV and nested/XML notices, need an explicit
separate conversion with its provenance. No company is matched by name.
An optional `--event-date-field` reads a named top-level ISO date independently
of publication. Nested act/judgment dates are not inferred. This is a chronology
of supplied publications, not a complete corporate history or ownership verdict.

SRT cues require numeric identifiers, `HH:MM:SS,mmm` times and blank separators.
WebVTT requires a `WEBVTT` header, a blank separator and `MM:SS.mmm` or
`HH:MM:SS.mmm` times. Cue IDs and settings are retained, not interpreted.
NOTE/STYLE/REGION blocks are counted and skipped. Header metadata is not
interpreted. Cue markup remains inert verbatim text, including speaker labels
and inline timestamps. No word-level timing or speaker identity is derived.
Overlapping and out-of-order cues remain in source order. Empty transcripts,
invalid intervals and unsupported structures fail explicitly.

Use `--method unknown|manual|automatic`, `--translation unknown|original|translated`
and optional `--language` for analyst declarations. Defaults are unknown.
Compare a cited passage with the actual media before asserting what was said.

All inputs are limited to 4 MiB and 5,000 records/cues, with derived JSON limited
to 4 MiB. Cue payloads have at most 4,000 characters and hour fields at most
9,999 hours. Oversized or malformed input is refused without partial output.
Original files stay unchanged. A hash checks bytes, not authenticity.

Source documentation: [CDX JSON](https://github.com/internetarchive/wayback/blob/master/wayback-cdx-server/README.md),
[DILA BODACC](https://www.bodacc.fr/pages/api-bodacc/),
[BODACC dataset](https://bodacc-datadila.opendatasoft.com/explore/dataset/annonces-commerciales/api/)
and [WebVTT](https://www.w3.org/TR/webvtt1/). Documentation was consulted on
26 October 2026. Local synthetic tests do not qualify a provider or a live API.

## Forensic export profiles

Profiles describe selected exports, not native parsers or proof that a particular
binary/version is qualified. Preserve the supplied parser/version and options
as a separate piece. Inspect headers before choosing a mapping. The generic
`import-events` command maps exactly two chosen columns and preserves other
columns in the original. Record version-specific differences, omitted rows and
the original clock context; never infer a timezone from the workstation.

| Supplied export family | Candidate columns to inspect | Key interpretation question |
| --- | --- | --- |
| EVTX CSV | Timestamp, event description, channel, record ID, event ID | Is this event a logon, execution indication or another recorded event, and what was filtered? |
| Prefetch CSV | Execution-time fields, program, volume information | Which fields actually support execution, and are several timestamps packed into one cell? |
| Registry / Amcache CSV | Key path, value, last-write or inventory time | Is the time a key change, inventory observation or actual execution evidence? |
| MFT / USN CSV | Timestamp family, record reference, path, reason flags | Which filesystem event does each timestamp represent, and are paths or records reused? |
| Browser CSV | Visit time, URL, transition/context, source row | Is the recorded event an actual visit, and is user interaction independently supported? |

No universal column names are assumed. A parser manifest should state artifact
family, parser name/version, command options, source hash, export encoding,
filtering, clock interpretation and known omissions. Keep claims limited to the
semantics of that artifact. An empty or absent export is a coverage gap.

## Exchange qualification

GraphML preserves IDs, relation states, evidence lists, premise links, review
status and optional identity/time metadata. Structured values are JSON strings
in GraphML data fields. Timesketch CSV includes datetime, message,
timestamp_desc, evidence_id, original record_index and analysis_sha256.
Uncertain times are omitted with counts; annotations and other fields remain
in the original case. Formula-like messages receive a leading apostrophe.

Use a selected synthetic case to import into a named destination/version and
inspect identifiers, accents, uncertain times, row zero and metadata after
import. Record losses and any transformations. Format parsing or a library
round trip is distinct from an import into Timesketch, Maltego, Aleph or OGI.
No destination service, connector or automatic installation is required.
