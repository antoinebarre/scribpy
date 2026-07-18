# ADR-005 — Sélectionner le fournisseur de rendu PlantUML

## Context

Le backend PlantUML `web` désigne actuellement Kroki sans rendre ce choix
explicite. Scribpy doit aussi pouvoir utiliser le serveur PlantUML officiel ou
une instance PlantUML Server auto-hébergée, sans modifier le pipeline commun de
rendu des blocs.

Kroki et PlantUML Server exposent tous deux du PNG par HTTP, mais leurs chemins
et encodages diffèrent. L'encodeur Kroki existant utilise zlib et base64url.
PlantUML Server accepte officiellement une source UTF-8 encodée en hexadécimal
et préfixée par `~h` sur l'endpoint `/png/ENCODED`.

## Decision

Conserver `PlantUmlRenderer` comme interface stable et ajouter
`PlantUmlServerRenderer` comme adaptateur HTTP autonome. Il reçoit une URL de
base validée, encode la source en `~h<hex-utf8>` et appelle
`<base>/png/<encoded>`.

Le champ `build.plantuml_backend` accepte les stratégies suivantes :

- `kroki` pour le service Kroki explicite ;
- `plantuml_server` pour un serveur PlantUML et comme valeur par défaut ;
- `local` pour le placeholder existant ;
- `web` comme alias rétrocompatible de `kroki`.

Le nouveau champ `build.plantuml_server_url` vaut par défaut
`https://www.plantuml.com/plantuml`. Seules les URL HTTP ou HTTPS absolues sont
acceptées. La factory `make_renderer` devient un registre de fonctions de
construction afin que les renderers avec et sans configuration restent
interchangeables.

`render_diagram_blocks()` continue de recevoir `BuildSettings` et transmet
l'URL à la factory PlantUML. Le merge et l'export MkDocs conservent donc le
même point d'entrée et le même comportement de sélection YAML.

## Consequences

- PlantUML Server devient le fournisseur par défaut ; `web` et `kroki`
  restent disponibles explicitement.
- Le site officiel et les installations auto-hébergées utilisent le même
  renderer configurable.
- Aucun package Python supplémentaire n'est ajouté.
- L'encodage hexadécimal produit des URL plus longues que Deflate ; les limites
  pratiques du serveur ou du proxy restent applicables aux grands diagrammes.
- Les erreurs HTTP et réseau restent exposées comme `PlantUmlRenderError`.

## Alternatives rejected

| Alternative | Raison du rejet |
|---|---|
| Remplacer Kroki par le serveur officiel | Casse le comportement existant et retire un fournisseur fonctionnel |
| Faire de l'URL une nouvelle valeur de `plantuml_backend` | Mélange identité de stratégie et configuration d'instance |
| Réutiliser l'encodage Kroki | Le protocole d'encodage PlantUML Server est différent |
| Implémenter l'encodage Deflate PlantUML personnalisé | Plus complexe que l'encodage hexadécimal officiellement supporté |
| Créer un backend distinct pour chaque serveur auto-hébergé | L'URL configurable couvre ces instances sans multiplier les classes |
