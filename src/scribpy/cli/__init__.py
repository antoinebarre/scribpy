"""Command-line interface for scribpy.

Exposes the main CLI entry point and sub-commands:
    scribpy init
    scribpy lint
    scribpy build [markdown|html|pdf]
    scribpy format <path>
    scribpy rewrite-links <path>
    scribpy toc
    scribpy index [show|check|generate|add]
    scribpy clean

The CLI delegates all business logic to application services
defined in scribpy.core and the pipeline packages.
"""
