# Triage media evidence notes

The built-in triage recognizes PNG/JPEG signatures and PNG IHDR dimensions. Optional adapters invoke separately installed ExifTool, ffprobe and Tesseract as described in [tool workflows](tool-workflows.md). No third-party binary is bundled. These adapters do not extract video frames, validate pixels or classify synthetic media. Never claim an absent analysis ran.

EXIF can be edited, copied or stripped. Messaging and social systems resize and transcode files. Editing-software traces do not prove malicious alteration or original device identity.

Record exact frames or intervals supporting a video observation. Compression, reflections, perspective and motion can explain discontinuities. Check adjacent frames rather than cherry-picking.

Keep originals local. Uploads to another service are a separate data flow. Public accessibility does not grant a redistribution license.

## Frame derivation and sequence limits

Request only the frames that could distinguish the proposed interpretation.
Keep source media ID/hash, exporter/version, extraction options, frame position
and time-base assumptions with each selected export. A model description is a
lead and a supplied frame is a derived view. Do not infer persistence from one
sample or treat a matching OCR excerpt as verification of the original scene.
The bundled ffprobe adapter does not extract frames.
