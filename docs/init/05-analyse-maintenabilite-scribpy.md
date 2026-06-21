---
type: analyse
status: draft
date: 2026-06-21
tags: [architecture, maintenabilite, scribpy]
---

# Analyse de maintenabilité — Scribpy

Évaluation de l'architecture proposée (document de conception du 2026-06-21) sur les quatre critères de jugement : simplicité, testabilité, maintenabilité, évolutivité. Arbitrage explicite quand ils sont en tension.

## Simplicité

Un développeur découvrant le projet suit un flux linéaire : `cli.py` → `pipeline.py` (parse → résout images → rend diagrammes) → `export_targets.py` (sélectionne le renderer) → un module de `render/`. Aucun saut dans une hiérarchie de classes à plusieurs niveaux ; chaque étape du pipeline est une fonction nommée explicitement par ce qu'elle fait. Le seul point d'indirection (le dictionnaire `export_targets`) est volontairement plat — une clé, une fonction, pas de registre dynamique ni de découverte par introspection qui obligerait à chercher où une implémentation est enregistrée.

Point de vigilance : `pdf_tree_renderer.py` et `html_site_renderer.py` partagent une logique de parcours d'arbre (`NavNode`) qui pourrait, par réflexe, être dupliquée entre les deux modules. À surveiller au Lot 7/8 (plan de bataille) : si la duplication dépasse une fonction de parcours générique simple, l'extraire dans `tree/nav_model.py` plutôt que de la laisser se répéter — sans pour autant créer une abstraction "moteur de rendu générique" prématurée qui anticiperait des formats non demandés.

## Testabilité

Conçu pour que la logique métier (parsing, résolution d'images, choix de rendu) soit testable sans écriture disque ni réseau, conformément à REQ-021 :

- `markdown_parser.parse` prend une chaîne, retourne une dataclass — testable avec de simples assertions sur la structure.
- `image_resolver.resolve` peut être testé avec un `Path` factice (`tmp_path` de pytest) sans dépendance à un vrai projet Markdown.
- `diagram_renderer` est testé via le `Protocol` : un faux renderer (callable de test ne faisant qu'enregistrer son appel) suffit pour tester le dispatch à clé composite `(engine, mode)`, sans invoquer aucune des quatre implémentations concrètes dans la suite de tests par défaut (cf. Lot 2, plan de bataille).
- `plantuml_web` et `mermaid_web` sont le seul point du projet où un mock réseau est nécessaire (succès et échec simulé de l'appel `httpx`) — accepté comme exception ciblée et isolée à ces deux modules, pas une caractéristique généralisée du projet. Le reste du pipeline (parsing, résolution d'images, dispatch) reste testable sans aucun mock réseau.
- Les renderers de sortie (`html_renderer`, `pdf_renderer`) sont les seuls points qui touchent réellement le disque ou une lib de rendu lourde (`markdown-pdf`) — ils sont testés en intégration, pas en unitaire, ce qui est le bon niveau (pas la peine de mocker `markdown-pdf` pour vérifier qu'un PDF est produit : un test d'intégration léger sur un fichier de quelques lignes suffit et reste rapide).

Aucun mock lourd n'est nécessaire pour la majorité du pipeline ; seuls les adaptateurs externes (subprocess Java, `mmdc`, écriture PDF) sortent du périmètre unitaire pur, ce qui est attendu et borné.

## Maintenabilité

Une modification localisée reste localisée :

- Corriger une règle de parsing Markdown → un seul fichier (`markdown_parser.py`), aucun impact sur les renderers de sortie qui consomment une structure déjà stabilisée (`ParsedDocument`).
- Ajuster le CSS appliqué en PDF → `pdf_renderer.py` uniquement ; `html_renderer.py` n'est pas concerné (chaque format a son propre point d'application CSS, pas de logique CSS partagée et donc pas de risque de régression croisée).
- Corriger un bug de détection d'image manquante → `image_resolver.py` uniquement, propagé à tous les formats de sortie sans dupliquer le correctif (un seul point de vérification d'existence, en amont du pipeline).

Point de tension identifié : si demain le CSS doit être validé (syntaxe, propriétés autorisées) plutôt que simplement appliqué, cette règle devra être dupliquée entre `html_renderer` et `pdf_renderer` à moins d'être extraite dans un module `core/css_validator.py` partagé — non fait aujourd'hui car non demandé (REQ-002/REQ-010 ne demandent que l'application, pas la validation), conformément à la règle de ne pas anticiper un besoin non exprimé. À surveiller si la demande émerge.

## Évolutivité

Ajouter une variante prévisible (nouveau format de sortie, ex. EPUB) demande d'**ajouter** du code (une nouvelle entrée dans `export_targets`, un nouveau module `render/epub_renderer.py`), pas de modifier l'existant — conforme à l'open/closed principle, obtenu ici par dictionnaire de callables plutôt que par interface abstraite lourde. Idem pour un nouveau moteur de diagramme (ex. support futur de Graphviz) ou un troisième mode de rendu (ex. un serveur auto-hébergé en plus de web/hors-ligne) : une entrée supplémentaire dans le dictionnaire à clé composite `(engine, mode)` de `diagram_renderer`, sans toucher aux quatre implémentations existantes ni à la logique de dispatch elle-même.

Évolution plus coûteuse, assumée comme telle : changer la convention d'ordre de l'arborescence (REQ-015, actuellement alphabétique par défaut) après que des utilisateurs aient déjà constitué leurs projets selon cette convention impliquerait une migration de comportement, pas seulement un ajout de code — raison pour laquelle ce point est explicitement remonté comme jalon de décision avant le Lot 6 du plan de bataille, plutôt que tranché silencieusement.

## Arbitrage global

Simplicité et testabilité ont primé sur une évolutivité anticipée plus large (ex. : pas d'architecture de plugins externes, pas d'interface abstraite pour de futurs formats hypothétiques non demandés). Le point réellement variable identifié dans le besoin actuel (format de sortie, moteur de diagramme) est couvert par un point d'extension ciblé (dictionnaires de callables) ; tout le reste reste une chaîne de fonctions simples, conformément à la règle d'arbitrage par défaut du skill d'architecture.
