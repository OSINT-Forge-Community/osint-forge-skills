# Export or resume a case notes

Private packages carry originals, records and derived files. Public packages carry only the approved view and export metadata and cannot restore a complete case.

ZIP_STORED archives use fixed member times. Verification rejects traversal paths, duplicates, symlink modes, size violations and hash mismatches without extracting. Restore stages a verified private case in a new directory.

Internal hashes are not signatures: an attacker can replace an archive and its manifest together. Retain independent digests where that matters. There is no trusted timestamp.

Masking misses names, precise locations, identifiers, sensitive deductions and unfamiliar secrets. The approved digest is an operator assertion, not authenticated proof of human review. Export never uploads to another service.
