# Release and Pipeline Memo — Scribpy

**Version:** 0.1.0-draft  
**Date:** 2026-05-06  
**Scope:** commandes de développement, CI locale, build, PyPI et Git

---

## 1. Objectif

Ce mémo regroupe les commandes utiles pour exécuter les pipelines locaux,
construire les distributions Python, vérifier les artefacts, publier sur
TestPyPI ou PyPI, et piloter le flux Git autour d'une release.

Il complète `doc/DEVELOPMENT_CHECKS.md`, qui détaille les contrôles qualité.

---

## 2. Boucle de Développement

Installer ou synchroniser l'environnement :

```bash
uv sync --dev
uv pip install -e .
```

Lancer le contrôle local complet :

```bash
make check
```

Ce pipeline local exécute :

```text
format -> lint -> docstrings -> typecheck -> test
```

Commandes ciblées :

```bash
make format        # formate src/ et tests/
make format-check  # vérifie le format sans modifier
make lint          # ruff check src/ tests/
make docstrings    # règles pydocstyle Google sur src/
make typecheck     # mypy strict sur src/
make test          # pytest + coverage
```

Tester le CLI de la phase 2 :

```bash
scribpy demo create /tmp/scribpy-demo
scribpy index check --root /tmp/scribpy-demo
```

Si le venv macOS ignore le package editable :

```bash
chflags -R nohidden .venv
```

---

## 3. Pipeline CI Local

Lancer la CI locale consolidée :

```bash
make ci
```

Cette cible appelle :

```bash
bash scripts/ci.sh
```

Différence avec `make check` :

- `make check` s'arrête au premier échec ;
- `make ci` collecte les résultats dans `work/*.log` et affiche un résumé.

Logs produits :

| Fichier | Contenu |
|---------|---------|
| `work/format.log` | Résultat du format-check |
| `work/lint.log` | Résultat Ruff |
| `work/typecheck.log` | Résultat mypy |
| `work/test.log` | Résultat pytest + coverage |
| `work/junit.xml` | Rapport JUnit |
| `work/coverage.xml` | Rapport coverage XML |
| `work/htmlcov/` | Rapport coverage HTML |

---

## 4. Préparer une Branche

Créer une branche de travail :

```bash
git status
git switch -c feat/phase-2-index-check
```

Voir les modifications :

```bash
git status --short
git diff
git diff --stat
```

Ajouter les fichiers :

```bash
git add src tests doc demo demo1.py Makefile pyproject.toml
```

Faire un commit :

```bash
git commit -m "Add project context index check workflow"
```

Pousser la branche :

```bash
git push -u origin feat/phase-2-index-check
```

---

## 5. Build des Distributions

Nettoyer et construire :

```bash
make build
```

Cette cible exécute :

```bash
rm -rf dist
uv build
```

Artefacts attendus :

```text
dist/*.tar.gz
dist/*.whl
```

Vérifier le contenu de `dist/` :

```bash
ls -lh dist
```

---

## 6. Vérifier les Distributions

Contrôle Twine :

```bash
make check-dist
```

Cette cible exécute :

```bash
make build
uv run --with twine twine check dist/*
```

Objectif :

- vérifier les métadonnées du package ;
- détecter les problèmes de description longue ;
- éviter une publication PyPI rejetée.

---

## 7. Publier sur TestPyPI

Pré-requis :

- compte TestPyPI ;
- token configuré pour Twine ;
- `make check` vert ;
- `make check-dist` vert.

Publier sur TestPyPI :

```bash
make publish-test
```

Cette cible exécute :

```bash
make check-dist
uv run --with twine twine upload --repository testpypi dist/*
```

Tester l'installation depuis TestPyPI dans un environnement temporaire :

```bash
cd /tmp
uv venv scribpy-testpypi
source scribpy-testpypi/bin/activate
uv pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ scribpy
scribpy --help
scribpy demo create /tmp/scribpy-test-demo
scribpy index check --root /tmp/scribpy-test-demo
```

---

## 8. Publier sur PyPI

Pré-requis recommandés :

```bash
git status --short
make check
make ci
make check-dist
```

Publier sur PyPI :

```bash
make publish
```

Cette cible exécute :

```bash
make check-dist
uv run --with twine twine upload dist/*
```

Tester l'installation depuis PyPI :

```bash
cd /tmp
uv venv scribpy-pypi
source scribpy-pypi/bin/activate
uv pip install scribpy
scribpy --help
scribpy demo create /tmp/scribpy-pypi-demo
scribpy index check --root /tmp/scribpy-pypi-demo
```

---

## 9. Version et Tags Git

La version est dynamique :

```toml
[tool.hatch.version]
source = "vcs"
tag-pattern = "^v(?P<version>.+)$"
fallback-version = "0.0.0"
```

Cela signifie que la version du package est dérivée des tags Git.

Créer un tag de release :

```bash
git status
make check
git tag v0.0.2b
git push origin v0.0.2b
```

Voir les tags :

```bash
git tag --list
git describe --tags --dirty --always
```

Supprimer un tag local en cas d'erreur :

```bash
git tag -d v0.0.2b
```

Supprimer un tag distant en cas d'erreur :

```bash
git push origin :refs/tags/v0.0.2b
```

À faire avec prudence : supprimer un tag publié peut perturber les workflows
des autres contributeurs.

---

## 10. Flux de Release Recommandé

Checklist :

1. Vérifier l'état Git.
2. Lancer les checks locaux.
3. Lancer la CI locale consolidée.
4. Construire et vérifier la distribution.
5. Publier sur TestPyPI.
6. Tester l'installation TestPyPI.
7. Créer et pousser le tag Git.
8. Publier sur PyPI.
9. Tester l'installation PyPI.

Commandes :

```bash
git status --short
make check
make ci
make check-dist
make publish-test

git tag v0.0.2b
git push origin v0.0.2b

make publish
```

Après publication :

```bash
git status --short
git log --oneline --decorate -5
git describe --tags --dirty --always
```

---

## 11. Commandes Git Utiles

Inspecter l'historique :

```bash
git log --oneline --decorate --graph -20
```

Voir les fichiers modifiés :

```bash
git status --short
git diff --stat
```

Voir le dernier commit :

```bash
git show --stat
```

Créer un commit de release :

```bash
git add .
git commit -m "Prepare release v0.0.2b"
```

Pousser la branche courante :

```bash
git push
```

Pousser une nouvelle branche :

```bash
git push -u origin HEAD
```

---

## 12. Règles de Prudence

- Ne publie pas sur PyPI avant d'avoir testé TestPyPI.
- Ne crée pas de tag avant que `make check` et `make check-dist` soient verts.
- Ne mets pas de logique métier dans `__init__.py` ou `__main__.py`; ces fichiers
  sont des façades ou points d'entrée.
- Vérifie `git status --short` avant chaque build ou publication.
- Garde `dist/` comme sortie générée : reconstruis avec `make build` plutôt que
  d'éditer les artefacts.
- En cas de doute sur l'environnement local, recrée le venv :

```bash
rm -rf .venv
uv sync --dev
uv pip install -e .
```
