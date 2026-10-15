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
