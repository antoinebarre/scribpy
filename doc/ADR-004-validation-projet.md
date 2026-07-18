# ADR-004 — Orchestrer la validation de projet dans Scribpy

## Contexte

Scribpy connaît les manifests, l'arborescence et les relations entre fichiers,
tandis que Mkforge 0.5 produit des diagnostics structurés sur la conformité
d'un document Markdown isolé. Une API publique doit agréger ces contrôles,
afficher un résultat console et retourner un booléen.

## Décision

Ajouter un moteur `validate_project` qui produit un rapport immuable. Il
exécute des règles de manifest propres à Scribpy, construit la collection,
adapte les diagnostics Mkforge de chaque fichier et ajoute les diagnostics de
collection existants. Une façade `valid_report` transmet ce rapport à un
présentateur Rich et retourne `report.is_valid`.

Le cœur ne dépend pas de la console. Mkforge reste propriétaire des règles de
conformité internes à un document ; Scribpy reste propriétaire de la structure
du projet et des références nécessitant plusieurs fichiers.

## Conséquences

- Les consommateurs peuvent utiliser le rapport sans produire de sortie.
- Les identifiants Mkforge restent visibles et exploitables.
- Une erreur de manifest empêche la découverte sûre de la collection, mais les
  erreurs de tous les manifests accessibles sont d'abord collectées.
- Rich devient une dépendance directe limitée à la couche de présentation.
- Certaines règles historiques de collection peuvent recouper une règle
  Mkforge ; leur retrait éventuel fera l'objet d'une décision distincte.

## Alternatives rejetées

- Faire retourner directement un booléen au moteur : les causes d'échec
  deviendraient inexploitables par les clients.
- Ajouter la connaissance de `scribpy.yml` à Mkforge : cela couplerait la
  bibliothèque Markdown à un format de projet particulier.
- Imprimer depuis chaque règle : cela mélangerait validation et présentation
  et rendrait les tests ainsi que les intégrations difficiles.

