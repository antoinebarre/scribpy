# ADR-002 — Generer la table des matieres dans Scribpy

## Context

La cle `build.toc` est reconnue par le manifeste racine mais n'est pas
implementee dans le pipeline d'assemblage. Un utilisateur qui pose `toc: true`
dans son `scribpy.yml` n'obtient aucun effet et aucun avertissement.

MkForge dispose d'une generation de TOC via `Report(toc=True)`, mais ce
mecanisme s'applique a son propre modele de document (`Report` > `Chapter` >
`Section`). Scribpy travaille avec du Markdown assemble a plat, issu de la
concatenation de fichiers `.md` independants. MkForge ne peut pas lire ce
Markdown brut et en deduire un TOC ; il ne peut generer un TOC que depuis ses
propres objets internes.

Le pipeline Scribpy applique deja le heading numbering (etape 1) avant la
reecriture des liens (etape 2). Les slugs d'ancrage du TOC doivent etre
calcules apres ces deux etapes pour pointer vers les titres effectivement
publies.

## Decision

La generation du TOC sera implementee dans Scribpy comme une etape dediee du
pipeline d'assemblage, apres la reecriture des liens internes.

Scribpy extraira les titres ATX (`#` a `######`) du Markdown assemble, les
convertira en entrees de liste Markdown avec des liens ancrés en utilisant
`slugify_heading()` (deja present dans `assembly/slug.py`), et inserera le TOC
apres le premier titre H1 du document.

### Contrat YAML

```yaml
build:
  toc: true
```

`build.toc` est optionnel. Lorsqu'il est absent ou `false`, aucun TOC n'est
genere. Lorsqu'il vaut `true`, le TOC est insere apres le H1 du document
assemble.

Les valeurs valides :

| Cle | Type | Defaut | Description |
|-----|------|--------|-------------|
| `build.toc` | boolean | `false` | Active la generation d'une table des matieres. |

Scribpy levera `InvalidScribpyManifestError` si `build.toc` n'est pas un
booleen.

### Format du TOC genere

Le TOC est une liste Markdown non ordonnee, indentee par profondeur de titre.
Le H1 du document (titre de la collection) est exclu du TOC. Les entrees
commencent au premier H2.

Exemple pour un document avec les titres suivants :

```markdown
# Guide utilisateur
## Installation
### Prerequis
### Etapes
## Configuration
## Reference API
```

TOC genere :

```markdown
- [Installation](#installation)
  - [Prerequis](#prerequis)
  - [Etapes](#etapes)
- [Configuration](#configuration)
- [Reference API](#reference-api)
```

Le TOC est insere directement apres la ligne du H1, separe par une ligne
vide avant et apres.

Si le document assemble ne contient pas de H1, le TOC est insere en tete du
document.

Si le document ne contient aucun heading apres le H1, aucun TOC n'est insere
meme si `toc: true`.

### Position dans le pipeline

Le transform TOC est insere apres la reecriture des liens et avant le rendu
des diagrammes :

1. Numbering des titres via MkForge, si active ;
2. Reecriture des liens internes ;
3. **Generation du TOC, si activee ;**
4. Rendu PlantUML ;
5. Rendu Mermaid ;
6. Collecte des images.

Cette position garantit que les slugs du TOC sont calcules depuis les titres
tels qu'ils apparaissent dans le document final. Si le numbering est actif,
`generate_toc()` lira `## 1. Installation` et produira `#1-installation`,
ce qui correspond exactement a l'ancre que le renderer Markdown generera pour
ce titre. La coherence est structurelle : le TOC lit le meme contenu que le
renderer, aucune reconciliation n'est necessaire.

### Module cible

La logique de generation sera portee par un nouveau module
`src/scribpy/core/assembly/toc.py` avec une interface publique reduite a une
fonction :

```python
def generate_toc(content: str) -> str:
    """Inserer un TOC apres le premier H1 du Markdown assemble."""
```

`concatenate()` dans `concatenate.py` instanciera le `TransformFn` TOC de
la meme facon que les autres etapes, en le conditionnant a
`manifest.build.get("toc") is True`.

`slugify_heading()` de `assembly/slug.py` sera reutilisee sans modification
pour produire les ancres du TOC, garantissant la coherence avec celles de la
reecriture des liens.

### Validation du manifeste

`_validate_build_settings()` dans `manifest.py` sera etendue d'une fonction
`_validate_toc()` qui verifie que `build.toc` est un booleen lorsqu'il est
present. Le manifest loader leve `InvalidScribpyManifestError` en cas de
valeur invalide.

## Consequences

`slugify_heading()` devient une fonction partagee entre la reecriture des
liens et la generation du TOC. La coherence des ancres est garantie par cette
reutilisation.

Le contrat YAML reste minimal. Aucune option de profondeur maximale, de style
ou de titre du bloc TOC n'est exposee tant que le besoin produit n'est pas
etabli.

Les tests devront couvrir : l'insertion correcte apres le H1, l'absence de TOC
quand il n'y a pas de headings post-H1, le cas sans H1, la validation YAML
(`toc` non booleen), et l'integration end-to-end dans le pipeline complet.

## Alternatives rejected

### Deleguer a MkForge

Rejete. MkForge genere un TOC depuis son propre modele objet (`Report` >
`Chapter` > `Section`). Il ne dispose pas d'API pour extraire un TOC depuis du
Markdown brut. Utiliser MkForge ici imposerait de parser le Markdown assemble
en objets MkForge, ce qui sort du perimetre de MkForge et introduirait un
couplage injustifie.

### Inserer le TOC avant le H1

Rejete. Le H1 est le titre du document. Un TOC avant le titre rompt la
structure logique attendue par les renderers Markdown aval (MkDocs, Pandoc,
GitHub).

### Inclure le H1 dans le TOC

Rejete. Le H1 est le titre de la page entiere. L'inclure dans le TOC creerait
une entree qui pointe vers le debut du document, redondante avec le titre
lui-meme.

### Exposer une option de profondeur maximale des maintenant

Rejete. Le besoin exprime est l'activation du TOC. Ajouter `toc_depth` avant
d'observer l'usage reel augmenterait le contrat public sans benefice immediat.

### Implementer le TOC comme diagnostic plutot que transform

Rejete. Le TOC modifie le contenu du document assemble. Les diagnostics sont
des verificateurs read-only sur la collection source ; ils n'ont pas vocation a
produire du contenu.
