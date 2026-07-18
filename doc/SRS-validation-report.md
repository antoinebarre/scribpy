# SRS — Validation d'un projet Scribpy

## Exigences

- **REQ-VALIDATION-01** — Scribpy SHALL valider tous les manifests `scribpy.yml` accessibles depuis la racine du projet.
  - Critère d'acceptation : un YAML invalide ou un schéma invalide produit un diagnostic bloquant associé au manifest.
- **REQ-VALIDATION-02** — Scribpy SHALL vérifier que chaque fichier ou dossier déclaré dans une clé `order` existe comme enfant direct.
  - Critère d'acceptation : chaque entrée absente produit un diagnostic bloquant contenant son nom et le chemin du manifest.
- **REQ-VALIDATION-03** — Scribpy SHALL signaler comme bloquante toute entrée `order` déclarée plusieurs fois dans un même manifest.
  - Critère d'acceptation : le rapport identifie chaque nom dupliqué.
- **REQ-VALIDATION-04** — Scribpy SHALL déléguer la conformité de chaque fichier Markdown à Mkforge 0.5 ou ultérieur.
  - Critère d'acceptation : les diagnostics Mkforge conservent leur identifiant, leur message, leur ligne et leur colonne dans le rapport Scribpy.
- **REQ-VALIDATION-05** — Scribpy SHALL exécuter ses diagnostics de collection pour les contraintes nécessitant le contexte du projet.
  - Critère d'acceptation : les liens interdocuments invalides et les ressources sortant de la racine figurent dans le rapport.
- **REQ-VALIDATION-06** — L'API `validate_project` SHALL retourner un rapport structuré sans écrire dans la console.
  - Critère d'acceptation : le rapport expose les diagnostics et une propriété booléenne `is_valid`.
- **REQ-VALIDATION-07** — L'API `valid_report` SHALL afficher un rapport lisible et retourner uniquement la validité du projet sous forme de booléen.
  - Critère d'acceptation : un projet valide retourne `True`, un projet contenant au moins une erreur retourne `False`.
- **REQ-VALIDATION-08** — L'affichage console SHOULD distinguer visuellement succès, avertissements et erreurs.
  - Critère d'acceptation : le résumé et chaque diagnostic sont rendus avec Rich, sans modifier le résultat métier.

