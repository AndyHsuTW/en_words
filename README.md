SpellVid (en_words)
=====================

Small CLI to compose short 1080p teaching videos for English words.

Quick start
-----------

1. Create and activate the project virtual environment (PowerShell):

   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   pip install -r requirements-dev.txt
   ```

2. Run the test suite inside the venv. Use the provided helper script to ensure
   tests run inside the project's venv:

   ```powershell
   .\scripts\run_tests.ps1
   ```

3. Render a single item (dry-run to validate assets):

   ```powershell
   python -m spellvid.cli make --letters "I i" --word-en Ice --word-zh 冰 \
     --image assets/ice.png --music assets/ice.mp3 --out out/Ice.mp4 --dry-run
   ```

Notes
-----
- The project prefers running tests and CLI inside the repository `.venv`.
- If `ffmpeg` isn't available on your PATH, the repo contains `FFmpeg/ffmpeg.exe` which will be used by default.

If you want CI integration or a GitHub Actions job that runs tests automatically, tell me and I can add an example workflow.
