# Review Windows artifact exports

Input is a selected CSV export, not EVTX, hive, MFT or Prefetch binary data. For example, map an operator-confirmed `TimeCreated` to time and `Description` to event. Other columns remain in the original evidence; the helper reports them as unmapped. Validate important rows against the supplied parser output or a separately approved independent parser.

The helper never launches Zimmerman tools, mounts images, enumerates a workstation, or installs a parser. State whether the export was filtered and whether timezone, event IDs, artifact paths and record completeness are known. A missing event in a filtered export is not evidence that it never occurred.
