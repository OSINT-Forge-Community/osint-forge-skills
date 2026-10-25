# Review geolocation hypotheses notes

A plausible facade is a candidate, not a match. Look for geometry, road layout, sign position and skyline constraints that can fail the candidate. Keep original-image observations separate from later overlays.

Metadata does not establish local solar time. Camera clocks, missing timezone, editing and transcoding can undermine sun-based precision. Preserve intervals and assumptions.

Reverse-image search transmits image bytes. Do not upload local images automatically: use supplied results or an explicitly authorized qualified provider. The utility does not geolocate or identify people.

Explain supported public-place results. For sensitive private locations retain methodology and an appropriate coarse result rather than exact whereabouts.

## Candidate ledger

For each genuine candidate keep a short record of visible observations, their
E references and locators, interpretation, candidate-specific matches,
contradictions, assumptions, predicted features and the next discriminating
check. Keep rejected hypotheses with the reason they failed. Do not invent a
fixed number of candidates or hide an equally plausible competitor.

Separate generic resemblance from a feature that the nearest competitor would
not explain. Test the strongest plausible competitor, image mirroring and
camera-side/viewpoint geometry where observable. If a candidate was suggested
only by a prior unrelated image or conversation, set it aside until current
image evidence independently supports it.

A missing feature is negative evidence only when it should have been visible,
within the capture's resolution, field of view and date. Use schema 4 hypothesis/test records from the [recipes](recipes.md#hypotheses-and-tests).
Keep the test state planned, blocked, completed or inconclusive separate from
its supports, contradicts or undetermined outcome. Cite the actual observation
and capture for completed tests. These are review states, not probability scores. Do not
promote an exact public location while a material contradiction or equally
plausible competitor remains. Return the supported region or indeterminate.

Select the next check for its ability to distinguish the remaining candidates,
its cost and its authorized data flow. A clearer sign may be more useful than
many generic architecture matches. Preserve literal sign text and OCR
uncertainty; misleading labels do not override incompatible scene geometry.
