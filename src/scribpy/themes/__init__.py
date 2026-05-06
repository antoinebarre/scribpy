"""Theme and template management for scribpy.

Manages HTML and PDF rendering templates and CSS stylesheets.

Data types:
    Theme — name, template paths, and CSS file paths

Main functions:
    load_theme(name, theme_paths)       -> Theme
    resolve_css_files(config, target)   -> tuple[Path, ...]
    render_template(template, context)  -> str
"""
