# Apprendre SQL Oracle pas à pas

> Plan d'apprentissage des notions SQL, appliquées directement à la banque fictive `CBS_LAB`.
> Une notion à la fois : on ne passe à la suivante que lorsque la case « Contrôle écrit » est cochée.

## 1. Apprendre sur mes tables plutôt que de mettre le projet en pause

LiveSQL fait travailler sur des tables de démonstration (`EMP`, `DEPT`, `HR`…). Or j'ai déjà une base bancaire chargée sur ma machine. Pour chaque notion, je fais dans cet ordre :

1. **Lire** la notion : un tutoriel, ou Claude.
2. **Pratiquer** sur `CBS_LAB` dans SQL Developer.
3. **Écrire le contrôle S0x** qui utilise cette notion.

J'apprends autant, et chaque notion fait avancer le projet. Les deux pistes ne s'opposent pas.

## 2. Bien choisir la ressource

| Ressource | Usage |
| --- | --- |
| [docs.oracle.com … /sqlrf/](https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/) | C'est un **manuel de référence**, comme un dictionnaire : très complet, mais on y **cherche** une syntaxe précise, on n'y apprend pas. À garder pour plus tard. |
| [LiveSQL](https://livesql.oracle.com/) | Bien pour tester sans installation. J'ai déjà Oracle chez moi : il me sert donc surtout pour ses tutoriels. |
| **Oracle Dev Gym**, cours *« Databases for Developers: Foundations »* | Un vrai cours gratuit, progressif, avec des exercices. C'est le meilleur point de départ parmi les ressources Oracle. |

## 3. L'ordre des notions et ce que chacune débloque

| # | Notion | Débloque dans le projet |
| --- | --- | --- |
| 1 | `SELECT / FROM / WHERE / ORDER BY`, `NULL`, `CASE` | Explorer les tables |
| 2 | `GROUP BY / HAVING`, `COUNT / SUM` | S01, puis S02 (je la comprendrai) et **S06** |
| 3 | `JOIN` (INNER, LEFT) | **S07, S09** |
| 4 | Sous-requêtes, **`EXISTS / NOT EXISTS`** | **S04, S05** |
| 5 | CTE (`WITH ... AS`) | **S10**, puis S03 (je la comprendrai) |
| 6 | Fenêtrage (`ROW_NUMBER`, `LEAD`…) | **S08** |

Les jointures passent avant les sous-requêtes : c'est plus naturel, et `NOT EXISTS` se comprend mieux une fois qu'on maîtrise les jointures. `RIGHT JOIN` est très rare en pratique ; on écrit presque toujours un `LEFT JOIN` en inversant les tables.

## 4. Ma progression

| # | Notion | Lu | Pratiqué | Contrôle écrit |
| --- | --- | :---: | :---: | :---: |
| 1 | SELECT / WHERE / NULL / CASE | ☐ | ☐ | — |
| 2 | GROUP BY / HAVING | ☐ | ☐ | ☐ S06 |
| 3 | JOIN | ☐ | ☐ | ☐ S07, S09 |
| 4 | Sous-requêtes, EXISTS | ☐ | ☐ | ☐ S04, S05 |
| 5 | CTE (WITH) | ☐ | ☐ | ☐ S10 |
| 6 | Fenêtrage | ☐ | ☐ | ☐ S08 |

---

## Notion 1 — SELECT / FROM / WHERE / ORDER BY, NULL, CASE

*À compléter quand on l'aborde : explication, exemples sur CBS_LAB, exercices, pièges.*

## Notion 2 — GROUP BY / HAVING, COUNT / SUM

*À compléter.*

## Notion 3 — JOIN (INNER, LEFT)

*À compléter.*

## Notion 4 — Sous-requêtes, EXISTS / NOT EXISTS

*À compléter.*

## Notion 5 — CTE (WITH ... AS)

*À compléter.*

## Notion 6 — Fonctions de fenêtrage

*À compléter.*
