# Fix report

**Root cause:** `fastembed==0.5.0` pins `mmh3>=4.1.0,<5.0.0`. `mmh3` 4.1.0 has no prebuilt wheel for
Python 3.13 on Windows, so pip tried to compile it and failed (no MSVC). Forcing `mmh3==5.3.1` only
hid the conflict.

**Fix:** `fastembed==0.7.4` officially allows `mmh3<6`, and `mmh3==5.3.1` ships cp312/cp313 Windows wheels.
Python 3.13 can stay. Verified: `pip download --platform win_amd64 --only-binary=:all:` resolves every
package (incl. transitive) for both cp313 and cp312 with zero source builds.

| Package | Old | New | Why |
|---|---|---|---|
| fastembed | 0.5.0 | 0.7.4 | allows mmh3 5.x; wheels for 3.13 |
| pypdf | 4.3.1 | 6.1.3 | old 4.x line has published security advisories (infinite-loop/RAM DoS on crafted PDFs) |
| google-genai | 0.3.0 | 1.38.0 | very old pre-1.0 SDK; code verified against new API (no API changes needed) |
| faiss-cpu | 1.9.0.post1 | 1.12.0 | cp313 Windows wheel |

## Changed files (server/)
- requirements.txt (above); requirements-dev.txt (new, adds pytest)
- app/main.py: deprecated `@app.on_event("startup")` -> lifespan handler
- app/core/config.py: `.env` now resolved relative to `server/` (not the current directory); optional `FASTEMBED_CACHE_DIR`
- app/services/vector_store.py: FAISS index saved/loaded via pathlib bytes (faiss C++ file I/O is fragile with non-ASCII/OneDrive paths; on-disk format unchanged, existing indexes still load); optional cache dir
- app/services/gemini_service.py: clear error instead of crash when Gemini returns empty text
- .env.example (placeholders only), .gitignore (+.pytest_cache)
- tests/ (new, 16 tests); README.md + docs/README.md (Windows/PowerShell steps)
- `.env` was NOT modified. Frontend untouched (API contract verified to match).

## Not verified here
- Real Gemini calls (no API key) and real fastembed model download (Hugging Face unreachable from the sandbox) were stubbed in tests.
- Actual Windows install was verified by wheel resolution for win_amd64, not by running on Windows.

## Rollback
Keep your original zip / `.venv`. To revert: restore the old files from the original zip, or use
`git checkout -- .` if the project is under git. Create the new venv separately (`.venv313`) so `.venv` stays intact.
