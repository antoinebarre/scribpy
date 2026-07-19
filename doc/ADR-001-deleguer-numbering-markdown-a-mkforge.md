# ADR-001 - Deleguer le numbering Markdown a MkForge

## Context

MkForge 0.3.0 fournit des fonctionnalites de numbering pour les titres
Markdown. Scribpy assemble deja des collections Markdown en un document unique,
normalise les niveaux de titres pendant la concatenation, puis applique un
pipeline de transforms.

Les fonctions metier Markdown doivent rester dans MkForge. Scribpy ne doit pas
reimplementer d'algorithme de numbering, de parcours syntaxique Markdown ou de
reecriture metier des titres. Scribpy doit seulement lire le `scribpy.yml`,
valider le contrat de configuration et appeler l'API MkForge adaptee.

Le `scribpy.yml` racine est le seul manifeste riche du projet. Les manifests de
dossier restent limites a `title` et `order`.

## Decision

Scribpy deleguera le numbering des titres Markdown a MkForge 0.3.0. La
configuration sera portee par le bloc `build.heading_numbering` du
`scribpy.yml` racine.

Scribpy introduira un adapter fin dans le pipeline d'assemblage. Cet adapter
aura une responsabilite unique : convertir la configuration validee en appel
MkForge et retourner le contenu Markdown produit par MkForge.

Scribpy ne developpera pas de logique metier Markdown pour le numbering. En
particulier, Scribpy ne calculera pas les compteurs de sections, ne detectera
pas les titres numerotables lui-meme et ne modifiera pas les titres selon ses
propres regles de numbering.

### Contrat YAML

Le contrat canonique est le suivant :

```yaml
project:
  title: Guide utilisateur

build:
  heading_numbering:
    enabled: true
```

`build.heading_numbering` est optionnel. Lorsqu'il est absent, le numbering est
desactive.

`build.heading_numbering.enabled` est optionnel. Lorsqu'il est absent dans un
bloc `heading_numbering` present, sa valeur par defaut est `true`.

Les valeurs valides sont :

| Cle | Type | Defaut | Description |
|-----|------|--------|-------------|
| `build.heading_numbering` | mapping | absent | Configure le numbering des titres Markdown. |
| `build.heading_numbering.enabled` | boolean | `true` si le bloc existe, sinon `false` | Active ou desactive le transform MkForge de numbering. |

Exemples valides :

```yaml
build:
  heading_numbering:
    enabled: true
```

```yaml
build:
  heading_numbering:
    enabled: false
```

```yaml
build:
  heading_numbering: {}
```

Exemples invalides :

```yaml
build:
  heading_numbering: true
```

```yaml
build:
  heading_numbering:
    enabled: "yes"
```

```yaml
build:
  heading_numbering:
    style: decimal
```

Scribpy levera `InvalidScribpyManifestError` quand
`build.heading_numbering` n'est pas un mapping, quand `enabled` n'est pas un
booleen ou quand une cle non supportee est presente dans
`build.heading_numbering`.

### Compatibilite avec `renumber_headings`

`build.renumber_headings` est un ancien nom accepte temporairement comme alias
de `build.heading_numbering.enabled`.

Exemple compatible :

```yaml
build:
  renumber_headings: true
```

`build.renumber_headings` doit etre un booleen. Toute autre valeur leve
`InvalidScribpyManifestError`.

Si `build.heading_numbering` et `build.renumber_headings` sont presents dans le
meme manifeste, `build.heading_numbering` est prioritaire. Scribpy emettra un
`ScribpyManifestWarning` pour signaler que `renumber_headings` est ignore.

`renumber_headings` pourra etre retire dans une version future apres une
periode de migration documentee.

### Position dans le pipeline

Le transform de numbering sera applique apres la concatenation et avant les
transforms qui dependent du contenu final des titres.

L'ordre cible du pipeline devient :

1. numbering des titres via MkForge, si active ;
2. reecriture des liens internes ;
3. rendu PlantUML ;
4. rendu Mermaid ;
5. collecte des images.

Cette position garantit que les slugs et liens internes sont calcules a partir
des titres effectivement publies apres numbering.

## Consequences

Scribpy conserve une responsabilite claire : assembler les fichiers, porter la
configuration et orchestrer les transforms.

MkForge devient la source de verite pour le comportement metier Markdown du
numbering. Les evolutions de format ou de regles de numbering doivent etre
prises en charge par MkForge, puis exposees dans Scribpy seulement par extension
du contrat YAML.

Le contrat YAML reste volontairement minimal. Aucune option de style, de
profondeur, de prefixe ou de politique d'exclusion n'est exposee tant que le
besoin produit n'est pas etabli.

Les tests Scribpy devront verifier la validation du YAML, l'activation ou la
desactivation du transform et l'appel a MkForge. Ils ne devront pas tester en
detail l'algorithme de numbering, qui appartient a MkForge.

## Alternatives rejected

### Implementer le numbering dans Scribpy

Rejete. Cela dupliquerait une fonctionnalite metier Markdown deja fournie par
MkForge 0.3.0 et creerait deux sources de verite.

### Ajouter des options de style des maintenant

Rejete. Le besoin exprime porte sur l'activation pilotee par YAML. Exposer des
options avant de stabiliser l'usage augmenterait le contrat public sans
benefice immediat.

### Autoriser `heading_numbering: true`

Rejete. Le champ canonique est un mapping afin de rester extensible sans casser
le schema YAML. Le booleen court rendrait les futures options ambigues.

### Configurer le numbering dans les manifests de dossier

Rejete. Les manifests de dossier gardent une responsabilite locale limitee a
`title` et `order`. Le numbering est une politique de build globale.
