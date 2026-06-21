---
type: srs
status: draft
date: 2026-06-21
tags: [architecture, srs, exigences, scribpy]
---

# SRS — Scribpy

## 1. Objectif et périmètre

Scribpy convertit des fichiers Markdown (unitaires ou organisés en arborescence) en livrables exploitables par des personnes non techniques, au format HTML (page unique ou site multi-pages destiné à GitLab/GitHub Pages) ou PDF (document unique ou agrégé depuis une arborescence). Scribpy ne fait pas d'édition de contenu Markdown, pas de serveur de prévisualisation, pas de gestion de version de contenu : il transforme une source Markdown statique en sortie statique.

## 2. Exigences fonctionnelles

| ID | Exigence | Critère de vérification |
|---|---|---|
| REQ-001 | Le système doit convertir un fichier Markdown unique en un fichier HTML autonome. | Un fichier `.md` donné produit un fichier `.html` valide (parsable par un parseur HTML standard), sans erreur. |
| REQ-002 | Le système doit permettre d'appliquer une feuille de style CSS fournie par l'utilisateur à la sortie HTML. | Un CSS fourni en entrée est présent (lié ou injecté) dans le HTML produit, et son contenu est appliqué visuellement aux éléments correspondants. |
| REQ-003 | Le système doit permettre de générer, en option, une table des matières interactive accessible via un menu de type "hamburger" en JavaScript. | Quand l'option est activée, le HTML produit contient un menu déclenchable listant les titres du document et permettant la navigation vers chaque section ; absent quand l'option est désactivée. |
| REQ-004 | Le système doit résoudre les références d'images du Markdown et vérifier leur existence avant génération. | Pour chaque image référencée, le système confirme l'existence du fichier source ; une image manquante est signalée nommément (chemin) sans interrompre silencieusement la génération des autres images valides. |
| REQ-005 | Le système doit transformer les blocs de code PlantUML présents dans le Markdown en diagrammes intégrés à la sortie, selon un mode de rendu sélectionné par l'utilisateur (service web ou rendu hors-ligne). | Un bloc identifié comme PlantUML dans le Markdown source est remplacé dans la sortie par une image ou un SVG représentant le diagramme rendu, produit par le mode actif au moment de l'exécution. |
| REQ-006 | Le système doit transformer les blocs de code Mermaid présents dans le Markdown en diagrammes intégrés à la sortie, selon un mode de rendu sélectionné par l'utilisateur (service web ou rendu hors-ligne). | Un bloc identifié comme Mermaid dans le Markdown source est remplacé dans la sortie par une image ou un rendu représentant le diagramme, produit par le mode actif au moment de l'exécution. |
| REQ-024 | Le système doit permettre à l'utilisateur de choisir, via un réglage unique applicable à l'ensemble du document, entre un mode de rendu de diagrammes "web" (service PlantUML public et mermaid.ink) et un mode "hors-ligne" (rendu local sans appel réseau), pour PlantUML et Mermaid conjointement. | Le réglage actif au moment de l'exécution déterminé sans ambiguïté (un seul mode actif par exécution) ; changer le réglage change le comportement de rendu pour tous les blocs PlantUML et Mermaid du document, sans réglage distinct par moteur ni par bloc. |
| REQ-025 | En mode "web", si l'appel au service de rendu échoue (réseau, proxy, indisponibilité du service), le système doit interrompre la génération du diagramme concerné avec une erreur explicite, sans basculer automatiquement vers le mode hors-ligne. | Une simulation d'échec réseau (ex. service inaccessible) en mode web produit une erreur nommant le bloc de diagramme concerné et le mode actif, et n'aboutit pas à une sortie produite par un autre mode. |
| REQ-007 | Le système doit permettre à l'utilisateur de spécifier le répertoire de destination de l'export HTML et de ses fichiers associés (CSS, images, assets JS). | Après exécution, le répertoire choisi par l'utilisateur contient le HTML et tous les fichiers associés nécessaires à son fonctionnement hors ligne (aucune dépendance non livrée). |
| REQ-008 | Le système doit produire une structure de sortie HTML directement publiable sur GitLab Pages ou GitHub Pages sans transformation supplémentaire. | La structure générée respecte les conventions attendues par ces plateformes (ex. point d'entrée `index.html`, chemins relatifs corrects) ; un déploiement manuel sur l'une des deux plateformes affiche le contenu correctement. |
| REQ-009 | Le système doit convertir un fichier Markdown unique en un fichier PDF, sans nécessiter d'installation système lourde (dépendances natives type navigateur complet, moteur de rendu GTK/Pango/Cairo, binaire externe non gérable via le gestionnaire de paquets Python). | L'installation du package via `uv`/`pip` seul (sans étape d'installation système manuelle, sans droits administrateur) permet de produire un PDF à partir d'un Markdown. |
| REQ-010 | Le système doit permettre d'appliquer une feuille de style CSS fournie par l'utilisateur à la sortie PDF. | Le PDF produit reflète visuellement les règles du CSS fourni (polices, couleurs, mise en page). |
| REQ-011 | Le système doit générer un sommaire/marque-page dans le PDF reflétant la structure des titres du document. | Le PDF produit contient des marque-pages (bookmarks PDF) ou un sommaire en première page, dont les entrées correspondent aux titres du Markdown et pointent vers la bonne page. |
| REQ-012 | Le système doit construire un site HTML multi-pages à partir d'une arborescence de fichiers Markdown organisée par l'utilisateur. | Une arborescence de répertoires/fichiers `.md` fournie en entrée produit une arborescence HTML correspondante, avec navigation entre les pages reflétant la structure source. |
| REQ-013 | Le système doit permettre d'appliquer une feuille de style CSS commune à l'ensemble des pages d'un site généré depuis une arborescence. | Toutes les pages HTML générées depuis l'arborescence référencent ou intègrent le même CSS fourni. |
| REQ-014 | Le système doit produire, pour un site multi-pages, une structure directement publiable sur GitLab Pages ou GitHub Pages. | Identique à REQ-008, appliqué à la sortie multi-pages. |
| REQ-015 | Le système doit agréger une arborescence de fichiers Markdown en un unique document PDF. | Une arborescence `.md` fournie en entrée produit un seul fichier PDF contenant l'ensemble du contenu, dans un ordre déterministe reflétant l'organisation de l'arborescence (ex. ordre alphabétique ou ordre explicite défini par l'utilisateur). |

## 3. Exigences non-fonctionnelles

| ID | Catégorie | Exigence | Critère de vérification |
|---|---|---|---|
| REQ-016 | Contraintes d'environnement | Le système doit fonctionner sans droits administrateur sur un poste Windows, en n'utilisant que des paquets installables via `pip`/`uv`. | Une installation `uv add scribpy` (ou équivalent) sur un compte utilisateur Windows standard, sans étape d'installation système, aboutit à un package fonctionnel. |
| REQ-017 | Contraintes d'environnement | Le système doit fonctionner derrière un proxy d'entreprise avec interception SSL (certificat non standard) en mode hors-ligne, sans aucune dépendance réseau. En mode web (REQ-024), l'appel au service de rendu est un appel réseau explicitement documenté et choisi par l'utilisateur, pas un effet de bord caché. | En mode hors-ligne, aucune opération du package n'effectue d'appel réseau. En mode web, le seul appel réseau effectué est celui, documenté, vers le service PlantUML/mermaid.ink configuré. |
| REQ-018 | Fiabilité | Une erreur sur un élément isolé (une image manquante, un bloc de diagramme malformé, un fichier Markdown invalide dans une arborescence) ne doit pas interrompre le traitement des autres éléments valides du même lot. | Sur un lot contenant un élément en erreur et N éléments valides, les N éléments valides sont produits et l'élément en erreur est signalé avec son identifiant (chemin/nom). |
| REQ-019 | Performance | Le système doit convertir un fichier Markdown de moins de 50 Ko (hors diagrammes) en HTML en moins de 2 secondes sur un poste de travail standard. | Mesure du temps d'exécution sur un fichier de test de taille de référence. |
| REQ-020 | Maintenabilité | Chaque format de sortie (HTML, PDF) et chaque mode (page unique, arborescence) doit pouvoir évoluer indépendamment sans modification du code traitant les autres formats/modes. | Ajout ou modification d'un format de sortie : revue de code confirmant qu'aucun fichier propre à un autre format n'a été modifié. |
| REQ-021 | Testabilité | La logique de transformation Markdown → structure intermédiaire doit être testable unitairement sans écriture sur disque ni dépendance réseau. | Suite de tests `pytest` couvrant cette logique sans fixture de fichiers temporaires ni mock réseau pour les cas nominaux. |
| REQ-022 | Compatibilité | Le système doit fonctionner avec Python 3.13 ou supérieur. | Exécution de la suite de tests sous Python 3.13 sans erreur de compatibilité. |
| REQ-023 | Sécurité | Le système ne doit pas exécuter de code arbitraire issu du contenu Markdown traité (ex. scripts embarqués non liés au rendu des diagrammes/TOC prévus). | Revue de code confirmant l'absence d'`eval`/`exec` sur du contenu issu du fichier source, et limitation du HTML généré aux éléments explicitement prévus (TOC, diagrammes). |

## 4. Contraintes et hypothèses

- Le contenu Markdown source est supposé encodé en UTF-8 — à confirmer si des sources legacy (ex. export Word, fichiers Windows historiques) sont à supporter.
- Le rendu PlantUML/Mermaid (REQ-005, REQ-006) est désormais piloté par un réglage explicite (REQ-024) entre mode web (services officiels PlantUML/mermaid.ink) et mode hors-ligne (rendu local) — ce point, initialement tranché par défaut vers le seul mode hors-ligne, a été révisé suite à la demande explicite de double mode réglable. La cohérence avec REQ-016/REQ-017 est désormais conditionnelle au mode actif plutôt qu'absolue.
- L'utilisateur final du PDF/HTML produit est non technique : aucune exigence d'accessibilité spécifique (WCAG, lecteurs d'écran) n'a été formulée — à signaler comme hors périmètre explicite plutôt qu'omis silencieusement (cf. section 5), sauf demande contraire.
- La notion d'"arborescence de markdowns" (F3/F4) suppose une convention de structuration (ex. fichier d'index, ordre de tri) qui n'est pas encore définie par l'utilisateur — REQ-015 pose une hypothèse par défaut (ordre alphabétique) à confirmer.

## 5. Hors périmètre

- Édition ou validation de contenu Markdown (couvert par un autre outil de l'utilisateur : validateur Markdown existant).
- Hébergement, déploiement automatisé ou intégration CI/CD vers GitLab/GitHub Pages (Scribpy produit une structure publiable ; le déploiement effectif — `git push`, pipeline CI — reste hors périmètre).
- Authentification, gestion multi-utilisateurs, ou toute notion de collaboration temps réel.
- Accessibilité avancée (WCAG) — non demandée, à réévaluer si le public cible évolue.
- Conversion dans le sens inverse (HTML/PDF → Markdown).
- Prévisualisation live / serveur de développement (type `mkdocs serve`) — non demandé explicitement ; à confirmer si souhaité, car cela changerait la nature du package (passage d'un convertisseur batch à un outil avec composant serveur).

## 6. Point de clarification sur l'énoncé fourni

L'énoncé contient deux exigences numérotées "F1.4" (PlantUML/Mermaid, et choix du répertoire d'export). Pour la traçabilité, elles sont distinguées ici : F1.4 → REQ-005/REQ-006 (diagrammes), F1.5 (répertoire d'export, ex-F1.4 doublon) → REQ-007, F1.6 (export Pages, ex-F1.5) → REQ-008. Aucune perte de contenu, seule la numérotation est clarifiée.
