# Milestone 4 design mocks (8 Oct 2026)

A visual direction for the three screens, to be approved before the product is built. Not the product.

```bash
python -m http.server 8765 --directory docs/superpowers/specs/m4-mocks
```

Then open `http://localhost:8765`. Add `?theme=dark` or `?theme=light` to fix the theme and `?reveal=1` to start
with the sensor revealed, for example `http://localhost:8765/?theme=dark&reveal=1#patient`.

- **Every patient value is synthetic**, generated in `mock.js` from a fixed seed. Rows in the clinic list other
  than Mrs. R. are placeholders.
- **Evidence figures are real**: each is quoted from its decision record (`docs/decisions/`).
- Boxes with a dashed outline that begin "Design note" are the mock talking and are not part of the product.
- `fonts/` is not committed. The page falls back to system fonts without it. To see the intended type, copy
  `SourceSansVF-Upright`, `SourceSerifVariable-Roman` and `SourceCodeVF-Upright` (woff2, SIL Open Font License)
  from `.venv/Lib/site-packages/streamlit/static/static/media/` into `fonts/` as `SourceSans3VF-Upright.woff2`,
  `SourceSerif4VF-Roman.woff2` and `SourceCodeVF-Upright.woff2`. The build vendors them with their licence.
