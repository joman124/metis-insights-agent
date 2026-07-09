# Voice reference samples

Drop real Metis-voice writing samples here, **one sample per `.txt` file**
(for example `01-exit-interviews.txt`, `02-ai-readiness.txt`). Plain text,
UTF-8 is fine here (only the `.py` files must stay ASCII).

`voice_profile._load_reference_passages()` picks up every `.txt` file in this
folder automatically and uses them as the reference set the voice judge scores
drafts against. When one or more real samples exist, they **replace** the
placeholder passages that are otherwise drawn from the metis-website marketing
copy (`voice_profile._PLACEHOLDER_PASSAGES`).

Good samples are short-to-medium excerpts that clearly show the target voice:
published essays, strong LinkedIn posts, whitepaper passages, talk
transcripts, or coaching-memo prose. Five to eight strong samples are plenty.

Until samples land here, the Streamlit sidebar shows a note that the voice bar
is provisional (`USING_PLACEHOLDER_REFERENCES`).
