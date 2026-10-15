# Review Windows artifact exports

Input is a selected CSV export, not EVTX, hive, MFT or Prefetch binary data. For example, map an operator-confirmed `TimeCreated` to time and `Description` to event. Other columns remain in the original evidence; the helper reports them as unmapped. Validate important rows against the supplied parser output or a separately approved independent parser.

The helper never launches Zimmerman tools, mounts images, enumerates a workstation, or installs a parser. State whether the export was filtered and whether timezone, event IDs, artifact paths and record completeness are known. A missing event in a filtered export is not evidence that it never occurred.

## Select an export profile

Use the shared source/export profiles to ask for parser version, options,
artifact family, source hash, encoding, filters and clock interpretation. Column
names vary by parser version: inspect rather than guessing a universal mapping.
Preserve unmapped fields and the original zero-based row index. State which
artifact semantics support execution, logon, inventory or file activity. Record
missing exports as coverage gaps and test normalized CSV in a named destination
before claiming that integration is qualified.
