# Voice reference samples

Drop real Metis-voice writing samples here, **one sample per file**. Both
`.txt` and `.docx` are supported (for example `01-exit-interviews.docx`,
`02-ai-readiness.txt`). Old-format `.doc` (binary Word) is **not** supported --
open it in Word and Save As `.docx`, or paste into a `.txt`.

`voice_profile._load_reference_passages()` picks up every `.txt` and `.docx`
file in this folder automatically and uses them as the reference set the voice
judge scores drafts against. This `README.md` and any file whose name starts
with `_` or `.` are skipped, so they are never mistaken for a sample. When one or more real samples exist, they **replace** the
placeholder passages that are otherwise drawn from the metis-website marketing
copy (`voice_profile._PLACEHOLDER_PASSAGES`).

Good samples are short-to-medium excerpts that clearly show the target voice:
published essays, strong LinkedIn posts, whitepaper passages, talk
transcripts, or coaching-memo prose. Five to eight strong samples are plenty.

Until samples land here, the Streamlit sidebar shows a note that the voice bar
is provisional (`USING_PLACEHOLDER_REFERENCES`).
