# Triage documents and files notes

The helper performs signatures, PNG dimensions, ZIP directory statistics and bounded header-only email parsing. PE/ELF are candidate families, not malware verdicts. No attachment or active code executes.

Archive directories describe claimed names and sizes, not validated decompressed content. Unsafe paths, duplicate names or symlink entries require an isolated qualified review, never extraction on the workstation.

Email headers can contain personal data and forged assertions. Authentication results require evidence of which trusted receiver added them and what they cover.

PDF signature recognition is not text extraction, signature verification or authenticity validation. The optional `pdftotext` adapter extracts a selected page range; `exiftool` reads metadata and `tesseract` handles selected PNG/JPEG images. Follow [tool workflows](tool-workflows.md) for execution and provenance. These executables are not bundled. No adapter decrypts documents, bypasses permissions or extracts embedded attachments.

## Excerpt and receiver context

Use `check-citations` for qualified UTF-8 or explicitly mapped records and retain
page/OCR limitations. Page excerpts from a qualified pdftotext analysis can
be checked against original page numbering and analysis hashes. OCR matches
still establish derived text only, never the truth of the photographed scene. An exact excerpt confirms its location, not
its implication. For mail, identify which receiver's logs and authentication
results are trusted before interpreting earlier untrusted headers. A sender
field, forwarded header or displayed authentication result alone does not
establish origin or delivery.
