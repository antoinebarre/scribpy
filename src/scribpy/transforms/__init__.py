"""Document transformation engine for scribpy.

A transform is a plain callable:
    Transform = Callable[[TransformContext], TransformResult]

Transforms receive the full document map and return a new map plus
diagnostics. They are applied in explicit order by apply_transforms.

Built-in transforms:
    resolve_includes          — expand !include directives
    resolve_cross_references  — resolve [[ref]] cross-references
    apply_section_numbering   — prefix headings with section numbers
    render_diagrams           — render Mermaid / PlantUML blocks
    rewrite_links_for_target  — adapt links for markdown/html/pdf output
    generate_toc_transform    — inject table of contents

Main functions:
    apply_transforms(context, transforms) -> TransformResult
"""
