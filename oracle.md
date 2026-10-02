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
| 1 | SELECT / WHERE / NULL / CASE | ✅ | ✅ (E1-E5, 02/10) | — |
| 2 | GROUP BY / HAVING | ☐ | ☐ | ☐ S06 |
| 3 | JOIN | ☐ | ☐ | ☐ S07, S09 |
| 4 | Sous-requêtes, EXISTS | ☐ | ☐ | ☐ S04, S05 |
| 5 | CTE (WITH) | ☐ | ☐ | ☐ S10 |
| 6 | Fenêtrage | ☐ | ☐ | ☐ S08 |

---

## Notion 1 — SELECT / FROM / WHERE / ORDER BY, NULL, CASE

### 1.1 La structure d'une requête

```sql
SELECT   account_number, status, open_date      -- 3. quelles COLONNES je veux voir
FROM     account                                -- 1. dans quelle TABLE
WHERE    status = 'ACTIVE'                      -- 2. quelles LIGNES je garde
ORDER BY open_date DESC                         -- 4. dans quel ORDRE je les affiche
FETCH FIRST 10 ROWS ONLY;                       -- 5. combien j'en affiche au maximum
```

On l'**écrit** dans l'ordre `SELECT → FROM → WHERE → ORDER BY`, mais Oracle l'**exécute** dans l'ordre des numéros :

1. `FROM` : je prends la table.
2. `WHERE` : je filtre les lignes.
3. `SELECT` : je choisis et calcule les colonnes.
4. `ORDER BY` : je trie.
5. `FETCH FIRST` : je coupe.

Conséquence pratique : un **alias** défini dans le `SELECT` (`... AS tranche`) est utilisable dans `ORDER BY` (exécuté après) mais **pas dans `WHERE`** (exécuté avant).

Comparaison Python :
```python
[(a.number, a.status, a.open_date)                 # SELECT
 for a in accounts                                 # FROM
 if a.status == "ACTIVE"]                          # WHERE
# puis sorted(..., reverse=True)[:10]              # ORDER BY + FETCH FIRST
```

Résultat réel sur `CBS_LAB` (`SELECT ... FROM account ORDER BY account_id FETCH FIRST 5 ROWS ONLY`) :

| ACCOUNT_NUMBER | PRODUCT_ID | STATUS | OPEN_DATE | CLOSE_DATE | CURRENCY |
| --- | ---: | --- | --- | --- | --- |
| 002-040007 | 1 | ACTIVE | 2024-01-15 | | XOF |
| 004-040007 | 1 | ACTIVE | 2024-08-30 | | XOF |
| 002-040014 | 5 | ACTIVE | 2026-03-23 | | XOF |
| 002-040021 | 1 | ACTIVE | 2024-07-15 | | XOF |
| 002-040028 | 1 | CLOSED | 2026-03-20 | 2026-09-04 | XOF |

Outil de vérification utilisé dans les exercices : `SELECT COUNT(*) FROM ... WHERE ...` compte les lignes au lieu de les afficher (détaillé en notion 2).

⚠️ Le nombre de lignes affiché par SQL Developer après un `SELECT *` (ex. « 200 ») est seulement le **premier paquet chargé**, pas le total. Pour connaître le nombre de résultats : `COUNT(*)`.

### 1.2 WHERE : les opérateurs

| Opérateur | Exemple sur CBS_LAB | Sens |
| --- | --- | --- |
| `=`, `<>` | `status = 'ACTIVE'` | égal, différent |
| `<`, `<=`, `>`, `>=` | `amount_xof >= 1000000` | comparaisons |
| `IN (...)` | `product_id IN (1, 2)` | une valeur de la liste |
| `BETWEEN a AND b` | `amount BETWEEN 10000 AND 50000` | entre a et b, **bornes incluses** |
| `LIKE` | `full_name LIKE 'Ets %'` | `%` = n'importe quelle suite de caractères, `_` = un caractère |
| `IS NULL`, `IS NOT NULL` | `close_date IS NULL` | valeur absente / présente |
| `AND`, `OR`, `NOT` | | combiner des conditions |

Exemple : comptes courants (produits 1 et 2) ouverts en 2025 → **158 comptes**.

```sql
SELECT account_number, open_date
FROM   account
WHERE  product_id IN (1, 2)
AND    open_date >= DATE '2025-01-01'
AND    open_date <  DATE '2026-01-01';
```

`DATE '2025-01-01'` est un **littéral de date** : toujours au format `AAAA-MM-JJ`, indépendant des réglages d'affichage. C'est la seule écriture de date à utiliser.

### 1.3 Piège : `AND` passe avant `OR`

```sql
-- FAUX : 410 lignes
WHERE status = 'ACTIVE' AND product_id = 1 OR product_id = 2
-- Oracle lit : (ACTIVE et produit 1) OU (produit 2, quel que soit le statut)

-- JUSTE : 395 lignes
WHERE status = 'ACTIVE' AND (product_id = 1 OR product_id = 2)
```

Les 15 lignes en trop sont des comptes produit 2 **non actifs**. La requête fausse ne produit **aucune erreur**. Règle : dès qu'un `OR` apparaît, je mets des parenthèses (ou j'utilise `IN`).

### 1.4 Piège : une DATE Oracle contient une heure

`TXN.txn_date` contient l'heure de l'opération (ex. `2026-09-30 14:32:07`). `DATE '2026-09-30'` veut dire `2026-09-30 00:00:00`.

| Requête | Résultat | Pourquoi |
| --- | ---: | --- |
| `WHERE txn_date = DATE '2026-09-30'` | **0** | aucune opération à minuit pile |
| `WHERE txn_date >= DATE '2026-09-30' AND txn_date < DATE '2026-10-01'` | **837** | toute la journée |
| `WHERE txn_date BETWEEN DATE '2026-09-01' AND DATE '2026-09-30'` | **2 093** | s'arrête le 30/09 à 00:00:00 : la journée du 30 est perdue |
| `WHERE txn_date >= DATE '2026-09-01' AND txn_date < DATE '2026-10-01'` | **2 930** | tout septembre |

Règle : pour une période, toujours un **intervalle semi-ouvert** `>= début AND < lendemain de la fin`. Il est juste avec ou sans heure, et il utilise les index.

### 1.5 NULL : l'absence de valeur

`NULL` ne veut pas dire 0 ni chaîne vide : il veut dire **inconnu / sans objet**. Dans `CBS_LAB` :

| Colonne | NULL signifie |
| --- | --- |
| `ACCOUNT.close_date` | compte non clôturé (694 comptes) |
| `CUSTOMER.birth_date` | client entreprise (69 clients) |
| `TXN.user_id` | opération sans agent : batch, carte, Mobile Money, virement (39 110 transactions) |
| `TXN.partner_code` | opération qui n'est pas du Mobile Money |
| `GL_ENTRY.account_id` | écriture sur un compte interne de la banque |

**Règle 1 : on ne compare jamais avec `= NULL`.** Toute comparaison avec NULL donne « inconnu », et `WHERE` ne garde que ce qui est « vrai ».

| Requête | Résultat |
| --- | ---: |
| `WHERE close_date = NULL` | **0** (toujours, sans erreur) |
| `WHERE close_date IS NULL` | **694** |
| `WHERE close_date IS NOT NULL` | **106** |

**Règle 2 : `<>` ignore aussi les NULL.**

| Requête | Résultat |
| --- | ---: |
| `WHERE partner_code <> 'MM01'` | **8 341** (seulement les Mobile Money d'un autre partenaire) |
| `WHERE partner_code <> 'MM01' OR partner_code IS NULL` | **58 203** (tout sauf MM01) |

Pour « tout sauf X » sur une colonne qui peut être NULL, il faut ajouter `OR col IS NULL`.

**Règle 3 : NULL contamine les calculs.** `100 + NULL` = NULL. On remplace par une valeur par défaut avec `NVL` :

```sql
SELECT account_number, NVL(TO_CHAR(close_date, 'DD/MM/YYYY'), 'Ouvert') AS cloture
FROM   account;
```

**Nuance : « 0 » ou « aucune ligne » ?**

| Requête | Résultat |
| --- | --- |
| `SELECT COUNT(*) FROM customer WHERE birth_date = NULL;` | 1 ligne : `0` (sans `GROUP BY`, il y a toujours un paquet, même vide) |
| `SELECT customer_type, COUNT(*) FROM customer WHERE birth_date = NULL GROUP BY customer_type;` | **aucune ligne** (aucune catégorie trouvée, donc aucun paquet) |

**Règle 4 (spécifique Oracle) : `''` = NULL.** Une chaîne vide est stockée comme NULL ; `WHERE col = ''` ne renvoie donc jamais rien.

### 1.6 CASE : le « if / elif / else » du SQL

```sql
SELECT account_id, ledger_balance,
       CASE
         WHEN ledger_balance < 0       THEN 'Négatif'
         WHEN ledger_balance < 100000  THEN '0 - 100 000'
         WHEN ledger_balance < 1000000 THEN '100 000 - 1 M'
         ELSE                               '> 1 M'
       END AS tranche
FROM   daily_balance
WHERE  balance_date = DATE '2026-09-30'
ORDER  BY ledger_balance DESC;
```

- Les `WHEN` sont testés **dans l'ordre** ; le premier vrai l'emporte. Ici, `< 100000` n'a pas besoin de `>= 0` : les négatifs ont déjà été pris.
- Sans `ELSE`, une ligne qui ne correspond à aucun cas reçoit NULL.
- Toutes les branches doivent renvoyer le même type (ici du texte).
- `balance_date = DATE '2026-09-30'` est juste ici : `balance_date` ne contient pas d'heure (photo de fin de journée).

Répartition réelle au 30/09/2026 : 110 négatifs, 46 entre 0 et 100 000, 182 entre 100 000 et 1 M, 356 au-dessus de 1 M. Sur les 110 négatifs, **74 sont des prêts** : dans ce modèle, le décaissement d'un prêt débite le compte de prêt. Un solde négatif n'a donc pas le même sens selon le produit. C'est une **question de définition métier**, pas de SQL.

`CASE` peut aussi transformer des codes en libellés (`CASE status WHEN 'ACTIVE' THEN 'Actif' ... END`) : très utile sur `CBS_BLACKBOX`, où les statuts sont codés `01/02/09`.

### 1.7 ORDER BY

```sql
ORDER BY branch_id, open_date DESC      -- par agence, puis du plus récent au plus ancien
ORDER BY close_date NULLS LAST          -- les NULL à la fin (par défaut en ASC, ils sont à la fin ; en DESC, au début)
```

Sans `ORDER BY`, Oracle ne garantit **aucun ordre** : le même `SELECT` peut renvoyer les lignes dans un ordre différent d'une fois sur l'autre.

### 1.8 Style et casse

```sql
-- E1 : clients entreprises de l'agence Plateau, triés par nom
SELECT full_name, segment, created_at
FROM   customer
WHERE  customer_type = 'COMPANY'
AND    branch_id = 1
ORDER  BY full_name;
```

- Convention : **mots-clés SQL en MAJUSCULES**, **tables et colonnes en minuscules**. Oracle s'en moque (`select` = `SELECT`) ; c'est pour la lisibilité.
- **Les valeurs entre apostrophes sont sensibles à la casse** : `'COMPANY'` → 12 lignes, `'company'` → 0 ligne, sans erreur.
- Commentaires : `-- une ligne` ou `/* plusieurs lignes */`. Ils servent à expliquer, pas à garder des requêtes désactivées.
- Colonnes de contrôle (ex. `customer_type`) : utiles pendant le développement, retirées à la livraison.

### 1.9 Exercices

À faire dans SQL Developer sur `CBS_LAB`. Le résultat attendu permet de vérifier sans voir la solution.

| # | Énoncé | Résultat attendu |
| --- | --- | --- |
| E1 | Les clients **entreprises** de l'agence **Plateau** (`branch_id = 1`), triés par nom. Afficher nom, segment, date de création. | 12 lignes — ✅ validé le 02/10 |
| E2 | Le nombre de transactions de **septembre 2026** (colonne `txn_date`). | 2 930 (si vous trouvez 2 093 : relire 1.4) — ✅ validé le 02/10 |
| E3 | Les comptes **clôturés en 2026**, avec numéro, produit et date de clôture, du plus récent au plus ancien. | 56 lignes — ✅ validé le 02/10 |
| E4 | Les transactions Mobile Money **rejetées**, avec une colonne `sens` qui vaut `'Wallet → compte'` pour un `DEPOSIT` et `'Compte → wallet'` pour un `WITHDRAWAL` (`CASE`). | À compter vous-même ; expliquer pourquoi un seul des deux sens apparaît (indice : `generate.py`, lignes 448-453) — ✅ validé le 02/10 : 580 rejets, tous « Compte → wallet » |
| E5 | Les clients **sans** date de naissance. Écrire d'abord la version fausse avec `= NULL`, puis la version juste. | 0, puis 69 — ✅ validé le 02/10 : 69 entreprises, aucun particulier sans date de naissance |

### 1.10 À retenir

- Ordre d'exécution : `FROM → WHERE → SELECT → ORDER BY`.
- Dates : littéral `DATE 'AAAA-MM-JJ'` et intervalle semi-ouvert `>= début AND < fin + 1`.
- `AND` passe avant `OR` : parenthèses obligatoires.
- `IS NULL`, jamais `= NULL` ; `<>` ignore les NULL ; `NVL` pour une valeur par défaut ; `''` = NULL.
- `CASE` : premier `WHEN` vrai l'emporte, toujours prévoir le `ELSE`.
- Une requête fausse ne fait pas d'erreur : elle donne juste un mauvais chiffre. D'où l'habitude de **vérifier le nombre de lignes**.
- Ne jamais déduire le sens d'une colonne de son nom : `CUSTOMER.created_at` = entrée en relation avec la banque, **pas** la date de création de l'entreprise.
- Comprendre **pourquoi** une colonne est NULL dit **comment** la traiter (ex. exclure les entreprises d'une analyse par âge).

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
