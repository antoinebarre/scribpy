# Project Status Report

# Executive Summary

This report summarises the current state of the project.

> All major milestones are on track.
> No critical blockers identified.

# Technical Details

## Architecture

The system follows a layered architecture.

### Parser Layer

Handles ingestion of Markdown source files.

#### Adapters

Concrete adapters: markdown-it-py, mistune.

### Exporter Layer

Renders the document tree to target formats.

## Code Sample

```python
from scribpy.report import Report, Chapter

report = Report(title='My Report')
report.add(Chapter(title='Intro'))
report.save('output/report.md')
```

## Metrics Table

| Module | Coverage | Complexity |
| --- | --- | --- |
| report/nodes.py | 100% | < 5 |
| report/renderer.py | 99% | < 5 |
| report/toc.py | 100% | < 5 |

# Formatting Showcase

Normal **bold text**, *italic text*, `inline_code()`, ~~~~struck~~~~.

## Lists

- Alpha
- Beta
- Gamma

1. First step
2. Second step
3. Third step

## Media

![scribpy logo](assets/logo.png "scribpy")

---

End of media section.