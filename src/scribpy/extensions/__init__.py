"""Plugin architecture for scribpy.

Extensions are registered as callables in an ExtensionRegistry.
Registry updates return new registry instances (immutable pattern).

Data types:
    ExtensionRegistry — mapping of lint rules, transforms,
                        builders, and renderers by name

Main functions:
    create_default_registry()                          -> ExtensionRegistry
    register_lint_rule(registry, name, rule)           -> ExtensionRegistry
    register_transform(registry, name, transform)      -> ExtensionRegistry
    register_builder(registry, name, builder)          -> ExtensionRegistry
    load_extensions(config, registry)
        -> tuple[ExtensionRegistry, list[Diagnostic]]
"""
