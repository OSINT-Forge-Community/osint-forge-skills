# Triage documents and files notes

The helper performs signatures, PNG dimensions, ZIP directory statistics and bounded header-only email parsing. PE/ELF are candidate families, not malware verdicts. No attachment or active code executes.

Archive directories describe claimed names and sizes, not validated decompressed content. Unsafe paths, duplicate names or symlink entries require an isolated qualified review, never extraction on the workstation.

Email headers can contain personal data and forged assertions. Authentication results require evidence of which trusted receiver added them and what they cover.

PDF signature recognition is not text extraction, signature verification or authenticity validation. Use an already approved parser or an operator export.
