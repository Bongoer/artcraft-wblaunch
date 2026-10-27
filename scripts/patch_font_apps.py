#!/usr/bin/env python3
"""Apply narrowly-scoped Rust font fallback corrections during GitHub Actions builds."""
from pathlib import Path
import sys

app, dirname = sys.argv[1:3]
root = Path(dirname)


def replace_exact(path: str, needle: str, replacement: str):
    file = root / path
    source = file.read_text(encoding="utf-8")
    if source.count(needle) != 1:
        raise SystemExit(f"{app}: cannot find unique patch anchor in {path}: {needle[:110]!r}; source may have changed")
    file.write_text(source.replace(needle, replacement, 1), encoding="utf-8")


if app == 'deckcraft':
    replace_exact('crates/ui-egui/src/theme.rs',
        '    add_fallback_faces(&mut defs, extra);',
        '''    // Preserve the original Inter UI style on wasm; Ubuntu was only a last resort.
    if cfg!(target_arch = "wasm32") {
        let inter = names.iter().any(|(family, style, _)| *family == "Inter" && *style == "Regular");
        assert!(inter, "DeckCraft web must embed Inter from craft-fonts");
        for chain in defs.families.values_mut() {
            chain.retain(|name| name != "Ubuntu-Light");
        }
    }
    add_fallback_faces(&mut defs, extra);''')
elif app == 'wordcraft':
    replace_exact('crates/ui-egui/src/theme.rs',
        '    // Symbols and emoji fall back to egui\'s defaults (kept in the families).',
        '''    // Web builds already embed Inter; don't fall through to Ubuntu-Light for Latin UI.
    if cfg!(target_arch = "wasm32") {
        for chain in fonts.families.values_mut() {
            chain.retain(|name| name != "Ubuntu-Light");
        }
    }
    // Symbols and emoji still fall back to egui's other built-in faces.''')
elif app == 'gridcraft':
    replace_exact('crates/ui-egui/src/craft_fonts_policy.rs',
        'pub const WEB_ALLOWED: &[(&str, &str)] = &[\n',
        '''pub const WEB_ALLOWED: &[(&str, &str)] = &[
    // Small OFL Latin faces from the shared manifest: the UI must not render in Ubuntu.
    ("Inter", "Regular"),
    ("Inter", "Bold"),
    ("Carlito", "Regular"),
    ("Carlito", "Bold"),
    ("Carlito", "Italic"),
    ("Carlito", "Bold Italic"),
''')
    replace_exact('crates/ui-egui/build.rs',
        '    let chinese = if wasm { Vec::new() } else { chinese_font_rows(dir, required)? };',
        '''    let chinese = if wasm { Vec::new() } else { chinese_font_rows(dir, required)? };
    // Explicitly opt in to the licensed Latin manifest for web builds.
    let latin = if wasm {
        let text = std::fs::read_to_string(dir.join("fonts/latin-manifest.txt"))
            .map_err(|e| format!("Latin font manifest: {e}"))?;
        let rows = craft_fonts_policy::parse_manifest(&text)?;
        if required {
            for (family, style) in [("Inter", "Regular"), ("Inter", "Bold"),
                ("Carlito", "Regular"), ("Carlito", "Bold"), ("Carlito", "Italic"), ("Carlito", "Bold Italic")] {
                if !rows.iter().any(|r| r.family == family && r.style == style) {
                    return Err(format!("Missing {family} {style} in Latin font manifest"));
                }
            }
        }
        rows
    } else { Vec::new() };''')
    replace_exact('crates/ui-egui/build.rs',
        '    for row in rows.iter().chain(&chinese) {',
        '    for row in rows.iter().chain(&chinese).chain(&latin) {')
    replace_exact('crates/ui-egui/build.rs',
        '    for row in craft_fonts_policy::embeddable(&rows, wasm).into_iter().chain(craft_fonts_policy::embeddable(&chinese, wasm)) {',
        '    for row in craft_fonts_policy::embeddable(&rows, wasm).into_iter().chain(craft_fonts_policy::embeddable(&chinese, wasm)).chain(craft_fonts_policy::embeddable(&latin, wasm)) {')
    replace_exact('crates/ui-egui/src/theme/font_setup.rs',
        '''    append_craft_faces(&mut fonts);
    drop_unparseable_fonts(&mut fonts);''',
        '''    append_craft_faces(&mut fonts);
    // In a browser, system font discovery cannot work. Put embedded Inter first for
    // the interface and Carlito first for cell roles; preserve script fallback after.
    if cfg!(target_arch = "wasm32") {
        for (role, family, style) in [
            (UI, "Inter", "Regular"),
            (UI_BOLD, "Inter", "Bold"),
            (CELL, "Carlito", "Regular"),
            (CELL_BOLD, "Carlito", "Bold"),
            (CELL_ITALIC, "Carlito", "Italic"),
            (CELL_BOLD_ITALIC, "Carlito", "Bold Italic"),
        ] {
            let suffix = format!("-{family}-{style}");
            let preferred = fonts.font_data.keys().find(|key| key.ends_with(&suffix)).cloned()
                .unwrap_or_else(|| panic!("Missing embedded {family} {style} web font"));
            if let Some(chain) = fonts.families.get_mut(&FontFamily::Name(role.into())) {
                chain.retain(|key| key != &preferred && key != "Ubuntu-Light");
                chain.insert(0, preferred);
            }
        }
        if let Some(chain) = fonts.families.get(&FontFamily::Name(UI.into())).cloned() {
            fonts.families.insert(FontFamily::Proportional, chain);
        }
    }
    drop_unparseable_fonts(&mut fonts);''')
else:
    raise SystemExit(f'no font modifications for {app}')

print(f'{app}: patched native Rust font definitions for the web')
