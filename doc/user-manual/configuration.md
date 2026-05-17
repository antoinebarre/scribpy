# Configuration

Minimal project:

```toml
[project]
name = "Example manual"

[paths]
source = "doc"

[index]
mode = "filesystem"

[document.toc]
enabled = true
max_level = 3
style = "bullet"

[document.numbering]
enabled = true
max_level = 3
style = "decimal"

[builders.html]
mode = "single-page"
```

## Supported choices

| Setting | Choices |
| --- | --- |
| `index.mode` | `filesystem`, `explicit`, `hybrid` |
| `document.toc.style` | `bullet`, `numbered` |
| `document.numbering.style` | `decimal`, `alpha`, `roman` |
| `builders.html.mode` | `single-page`, `site` |

## HTML builder settings

```toml
[builders.html]
mode = "site"
site_name = "Engineering Handbook"
theme = "readthedocs"
output_dir = "build/site"
css_files = ["theme/custom.css"]
```

`output_dir` configures the default HTML build location. A CLI `--output-dir`
or Python `output_dir=` argument overrides it for one run, which is usually the
cleaner option in CI/CD.
