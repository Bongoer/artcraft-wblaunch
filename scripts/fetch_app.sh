#!/usr/bin/env bash
set -Eeuo pipefail
app="${1:?expected app slug}"
case "$app" in
  photocraft|vectorcraft|filmcraft|lightcraft|pdfcraft|effectcraft|designcraft|figcraft|wordcraft|soundcraft|deckcraft|cadcraft|gridcraft) ;;
  *) echo "Invalid app: $app" >&2; exit 2 ;;
esac

mkdir -p "${GITHUB_WORKSPACE}/_apps/${app}"
output="${GITHUB_WORKSPACE}/_apps/${app}"
work="${RUNNER_TEMP}/craft_${app}"
mkdir -p "$work/release" "$work/extracted"
cache_dir="${RUNNER_TEMP}/craft_cached/${app}"
if compgen -G "$cache_dir/*.zip" > /dev/null; then
  cp "$cache_dir"/*.zip "$work/release/"
  echo "${app}: using cached WASM release/source ZIP"
fi
release_json="$(gh api "repos/storytold/${app}/releases/latest" --jq '{tag: .tag_name, published: .published_at, web: [.assets[].name | select(test("-web-.*\\.zip$"))]}' 2>/dev/null || true)"
tag="$(jq -r '.tag // empty' <<< "$release_json" 2>/dev/null || true)"
release_date="$(jq -r '.published // empty' <<< "$release_json" 2>/dev/null || true)"
webasset="$(jq -r '.web[0] // empty' <<< "$release_json" 2>/dev/null || true)"

# If the main branch is ahead of the release, try rebuilding real Rust/WASM
# from the latest source. Any failure falls back to the official stable build.
new_source=false
if [[ -n "$tag" && -n "$release_date" ]]; then
  main_date="$(gh api "repos/storytold/${app}/commits/main" --jq '.commit.committer.date' 2>/dev/null || true)"
  if [[ -n "$main_date" && "$main_date" > "$release_date" ]]; then
    new_source=true
  fi
fi
# DeckCraft can embed permitted open-source UI fonts from craft-fonts when built from
# source. The published WASM may omit those optional faces, leaving egui's Ubuntu fallback.
font_build=false
if [[ "$app" == deckcraft && "${EMBED_DECKCRAFT_FONTS:-false}" == true ]]; then
  font_build=true
fi
if ! compgen -G "$work/release/*.zip" > /dev/null && { [[ "$font_build" == true ]] || [[ -z "$webasset" ]] || { [[ "$new_source" == true && "${UPDATE_FROM_SOURCE:-false}" == true ]]; }; }; then
  echo "${app}: checking source build (newer source: ${new_source}; released browser ZIP: ${webasset:-none})"
  if git clone -q --depth 1 "https://github.com/storytold/${app}.git" "$work/source" \
     && (if [[ "$font_build" == true ]]; then
           git clone -q --depth 1 https://github.com/storytold/craft-fonts.git "$work/craft-fonts"
           export CRAFT_FONTS_DIR="$work/craft-fonts" CRAFT_FONTS_REQUIRED=1
         fi
         cd "$work/source" && CI=1 bash packaging/web/package.sh); then
    built="$(find "$work/source/dist" -maxdepth 1 -type f -name "${app}-web-*.zip" | head -n 1 || true)"
    if [[ -n "$built" ]]; then
      cp "$built" "$work/release/"
      echo "${app}: using current Rust source WebAssembly build"
    fi
  else
    echo "WARNING: ${app} could not build from current Rust source; falling back to published WebAssembly release" >&2
  fi
fi

if ! find "$work/release" -maxdepth 1 -name '*.zip' -print -quit | grep -q .; then
  if [[ -z "$webasset" || -z "$tag" ]]; then
    echo "ERROR: ${app} has neither a working source build nor a release WebAssembly ZIP" >&2
    exit 1
  fi
  gh release download "$tag" -R "storytold/${app}" -p "$webasset" -D "$work/release" --clobber
  echo "${app}: using published WebAssembly release ${tag}"
fi
zip="$(find "$work/release" -maxdepth 1 -name '*.zip' -print -quit)"
mkdir -p "$cache_dir"
cp "$zip" "$cache_dir/"
unzip -q "$zip" -d "$work/extracted"
mapfile -t indexes < <(find "$work/extracted" -type f -name index.html)
if [[ ${#indexes[@]} != 1 ]]; then
  echo "ERROR: ${app} has ${#indexes[@]} index.html files in WebAssembly package" >&2
  exit 1
fi
site="$(dirname "${indexes[0]}")"
cp -a "$site/." "$output/"
test -s "$output/index.html"
find "$output" -type f \( -name '*.wasm' -o -name '*.part-aa' \) -print -quit | grep -q . || { echo "ERROR: ${app} browser package has no WebAssembly" >&2; exit 1; }
echo "Ready: /apps/${app}/"

# Copy official suite icon and present a consistent startup screen while native WASM loads.
curl -fLsS --retry 3 \
  "https://raw.githubusercontent.com/storytold/craft-launcher/main/assets/app-icons/${app}.png" \
  -o "$output/wikipod-app-icon.png"
python3 "$GITHUB_WORKSPACE/scripts/inject_loader.py" "$output" "$app"
