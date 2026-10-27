# Wikipod Web Launcher (unofficial)

This repository deploys the **original Rust/WebAssembly** ArtCraft Launcher interface with a small Rust source patch: Wikipod branding and direct **Open in browser** actions for each Craft app. The app binaries are official upstream web releases, or (where possible) native Rust source-to-WASM builds on GitHub Actions.

Website: https://bongoer.github.io/artcraft-wblaunch/

All thirteen apps, no placeholder pages:

| App | URL |
| --- | --- |
| PhotoCraft | /apps/photocraft/ |
| LightCraft | /apps/lightcraft/ |
| FilmCraft | /apps/filmcraft/ |
| DesignCraft | /apps/designcraft/ |
| VectorCraft | /apps/vectorcraft/ |
| PdfCraft | /apps/pdfcraft/ |
| EffectCraft | /apps/effectcraft/ |
| WordCraft | /apps/wordcraft/ |
| DeckCraft | /apps/deckcraft/ |
| GridCraft | /apps/gridcraft/ |
| CADCraft | /apps/cadcraft/ |
| SoundCraft | /apps/soundcraft/ |
| FigCraft | /apps/figcraft/ |

## Updates

- Scheduled every six hours; workflow can also be manually dispatched.
- Initial manual run uses official release WASM assets for fast/reliable deployment.
- Scheduled runs attempt to build latest Rust main when it is newer than the latest official web release.
- A failed upstream source build falls back to the last official web release (rather than shipping a broken application).
- If an app has no release ZIP and a source build fails, deployment fails instead of publishing a placeholder.
- Source WASM ZIPs are cached using the upstream commit and release tag.
- All 13 releases had published web ZIPs on October 25, 2026.

GitHub Actions builds the launcher. **No Rust toolchain, massive Node installation or large ZIP download on the user's phone.** The website is published as a Pages Actions artifact, not committed binaries.

## Sources and copyright

Original work: https://github.com/storytold/craft-launcher and individual `https://github.com/storytold/<app>` repositories. This website is independently maintained. The modified launcher removes the ArtCraft trademark header mark and replaces it with the user's original Wikipod symbol. Licenses and acknowledgements included with the original release assets are preserved; this site is not affiliated with ArtCraft.
