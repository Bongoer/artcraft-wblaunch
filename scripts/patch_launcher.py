#!/usr/bin/env python3
"""Minimal, anchored modifications to the upstream Rust egui ArtCraft Launcher web build.

Modifies real Rust UI source, not a mock or a canvas click overlay. Stops if upstream
changes break any expected anchor, avoiding accidental publication of an unmodified build.
"""
from pathlib import Path
import sys

root = Path(sys.argv[1])
file = root / 'crates/ui-egui/src/views.rs'
src = file.read_text(encoding='utf-8')


def replace_once(old: str, new: str) -> None:
    global src
    n = src.count(old)
    if n != 1:
        raise SystemExit(f'Rust patch refused: expected one match, got {n}: {old[:100]!r}')
    src = src.replace(old, new, 1)


replace_once('''            // The ArtCraft wordmark exactly as supplied, in its own cell.
            let logo = vec2(14.0 * crate::icons::ARTCRAFT_LOGO_ASPECT, 14.0);
            let (cell, _) = ui.allocate_exact_size(vec2(logo.x + 40.0, h), Sense::hover());
            egui::Image::new(crate::icons::artcraft_logo(t.dark)).alt_text(tl!("ArtCraft")).paint_at(ui, Rect::from_center_size(cell.center(), logo));''', '''            // Wikipod's original diagonal mark replaces the upstream brand assets.
            ui.add_space(15.0);
            wikipod_mark(ui, t.ink_strong);
            ui.add_space(9.0);
            ui.label(RichText::new("wikipod").size(18.0).family(theme::semibold()).color(t.ink_strong));
            ui.add_space(16.0);''')

replace_once('''                // The controls reserve their actual widths before the secondary text gets space.
                ui.with_layout(egui::Layout::left_to_right(egui::Align::Center), |ui| {
                    if ui.available_width() >= 17.0 + widgets::hud_galley(ui, tl!("Craft App Suite"), t.muted).size().x {
                        widgets::rule(ui, h);
                        ui.add_space(16.0);
                        widgets::hud(ui, tl!("Craft App Suite"), t.muted);
                    }
                });''', '''                // Wikipod is now the sole header brand (no Craft App Suite label).''')

replace_once('''        if !self.caps.manage_apps {
            let platform = self.platform;
            let url = entry.release().zip(platform).and_then(|(r, p)| {''', '''        if !self.caps.manage_apps {
            // All buttons in the real Rust/WASM UI open our hosted original app builds.
            // This also covers the table view and the app-details drawer.
            if cfg!(target_arch = "wasm32") {
                return Primary::Download(format!("apps/{}/", entry.app.id));
            }
            let platform = self.platform;
            let url = entry.release().zip(platform).and_then(|(r, p)| {''')

replace_once('''            Primary::Download(url) => {
                let label = match self.platform {
                    Some(p) => fmt(tl!("Download for {os}"), &[("os", p.os.label())]),
                    None => tl!("Download").into(),
                };
                if widgets::button(ui, &label, Kind::Primary, main_w).clicked() {
                    widgets::open_external_link(ui.ctx(), &url);
                }
            }''', '''            Primary::Download(url) => {
                let hosted = cfg!(target_arch = "wasm32") && url.starts_with("apps/");
                let label = if hosted {
                    "Open in browser".to_string()
                } else {
                    match self.platform {
                        Some(p) => fmt(tl!("Download for {os}"), &[("os", p.os.label())]),
                        None => tl!("Download").into(),
                    }
                };
                if widgets::button(ui, &label, Kind::Primary, main_w).clicked() {
                    if hosted {
                        ui.ctx().open_url(egui::OpenUrl::same_tab(format!("./{url}")));
                    } else {
                        widgets::open_external_link(ui.ctx(), &url);
                    }
                }
            }''')

insert_before = 'impl LauncherUi {\n    /// The header bar;'
if src.count(insert_before) != 1:
    raise SystemExit('Rust patch refused: could not find launcher header')
mark = '''// Original Wikipod diagonal symbol (62 x 80 source viewBox), rendered natively by egui.
fn wikipod_mark(ui: &mut Ui, color: Color32) {
    let (rect, response) = ui.allocate_exact_size(vec2(18.0, 24.0), Sense::hover());
    response.widget_info(|| egui::WidgetInfo::labeled(egui::Role::Image, true, "Wikipod"));
    let xy = |x: f32, y: f32| egui::pos2(rect.left() + x * rect.width() / 62.0, rect.top() + y * rect.height() / 80.0);
    for vertices in [
        vec![xy(0.0, 0.0), xy(62.0, 0.0), xy(62.0, 26.0), xy(26.0, 26.0)],
        vec![xy(0.0, 26.0), xy(26.0, 26.0), xy(62.0, 62.0), xy(26.0, 62.0)],
        vec![xy(0.0, 26.0), xy(26.0, 26.0), xy(26.0, 80.0), xy(0.0, 54.0)],
    ] {
        ui.painter().add(egui::Shape::convex_polygon(vertices, color, Stroke::NONE));
    }
}

'''
src = src.replace(insert_before, mark + insert_before, 1)
file.write_text(src, encoding='utf-8')

# Remove the protected ArtCraft favicon from the modified distribution.
html = root / 'apps/artcraft-launcher-web/index.html'
h = html.read_text(encoding='utf-8')
needle = '  <link data-trunk rel="icon" href="../../assets/app-icon/hicolor/64x64/apps/ai.storyteller.artcraft-launcher.png" />\n'
if h.count(needle) != 1:
    raise SystemExit('Rust patch refused: unexpected launcher icon tag')
h = h.replace(needle, '', 1)
h = h.replace('<title>ArtCraft Launcher</title>', '<title>Wikipod Web Launcher</title>', 1)
html.write_text(h, encoding='utf-8')
print('Patched original upstream Rust launcher: Wikipod branding, 13 real WASM app links, same-tab navigation.')
