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
| 2 | GROUP BY / HAVING | ✅ | ✅ (E6-E11, 05/10) | ✅ S06 (06/10) |
| 3 | JOIN | ✅ | ✅ (E12-E16, 14/10) | ☐ S07, S09 |
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
| E2 | Le nombre de transactions de **septembre 2026** (colonne `txn_date`). | 2 930 (si je trouve 2 093 : relire 1.4) — ✅ validé le 02/10 |
| E3 | Les comptes **clôturés en 2026**, avec numéro, produit et date de clôture, du plus récent au plus ancien. | 56 lignes — ✅ validé le 02/10 |
| E4 | Les transactions Mobile Money **rejetées**, avec une colonne `sens` qui vaut `'Wallet → compte'` pour un `DEPOSIT` et `'Compte → wallet'` pour un `WITHDRAWAL` (`CASE`). | À compter moi-même ; expliquer pourquoi un seul des deux sens apparaît (indice : `generate.py`, lignes 448-453) — ✅ validé le 02/10 : 580 rejets, tous « Compte → wallet » |
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

### 2.1 Les fonctions d'agrégat : résumer plusieurs lignes en une

| Fonction | Rôle | Sur `CUSTOMER` (500 clients) |
| --- | --- | --- |
| `COUNT(*)` | nombre de **lignes** | 500 |
| `COUNT(col)` | nombre de valeurs **non NULL** | `COUNT(birth_date)` = 431 |
| `COUNT(DISTINCT col)` | nombre de valeurs **différentes** | `COUNT(DISTINCT segment)` = 4 |
| `SUM(col)` | somme | |
| `AVG(col)` | moyenne | |
| `MIN(col)` / `MAX(col)` | plus petite / plus grande valeur | `MIN(created_at)` = 02/01/2015 |

```sql
SELECT COUNT(*), COUNT(birth_date), COUNT(DISTINCT segment), MIN(created_at), MAX(created_at)
FROM   customer;
```

Sans `GROUP BY`, un agrégat résume **toute la table** (après le `WHERE`) en **une seule ligne**.

**Toutes les fonctions d'agrégat ignorent les NULL**, sauf `COUNT(*)`. `COUNT(*)` = 500 mais `COUNT(birth_date)` = 431 : les 69 entreprises ne sont pas comptées.

### 2.2 GROUP BY : un résultat par catégorie

`GROUP BY` range les lignes **en paquets** (un par valeur différente), puis l'agrégat est calculé **par paquet**.

```sql
SELECT   status, COUNT(*) AS nb
FROM     account
GROUP BY status
ORDER BY nb DESC;
```

| STATUS | NB |
| --- | ---: |
| ACTIVE | 626 |
| CLOSED | 106 |
| BLOCKED | 39 |
| DORMANT | 29 |

Recoupement : 626 + 106 + 39 + 29 = **800** = nombre total de comptes. La somme des paquets doit toujours redonner le total.

Comparaison Python :
```python
from collections import Counter
Counter(a.status for a in accounts)      # {'ACTIVE': 626, 'CLOSED': 106, ...}
```

**Plusieurs colonnes** : un paquet par **combinaison** de valeurs.

```sql
SELECT   branch_id, segment, COUNT(*) AS nb
FROM     customer
GROUP BY branch_id, segment
ORDER BY branch_id, segment;
```

| BRANCH_ID | SEGMENT | NB |
| ---: | --- | ---: |
| 1 | CORPORATE | 4 |
| 1 | PREMIUM | 11 |
| 1 | RETAIL | 68 |
| 1 | SME | 8 |
| 2 | PREMIUM | 6 |
| … | … | … |

31 combinaisons au total. Une combinaison absente (l'agence 2 n'a aucun client CORPORATE) **n'apparaît pas** : `GROUP BY` ne crée pas de ligne à 0.

### 2.3 La règle d'or du GROUP BY

**Chaque colonne du `SELECT` est soit dans le `GROUP BY`, soit dans une fonction d'agrégat.**

```sql
-- FAUX : ORA-00979: not a GROUP BY expression
SELECT branch_id, segment, COUNT(*)
FROM   customer
GROUP  BY branch_id;
```

Pourquoi : l'agence 1 contient 4 segments différents. Oracle ne sait pas **lequel** afficher sur la ligne unique de l'agence 1. Il refuse plutôt que de choisir au hasard.

Et inversement (vu en E5) : **une colonne du `GROUP BY` doit être affichée**, sinon on obtient des chiffres sans savoir à quelle catégorie ils correspondent.

**Analogie des boîtes.** `GROUP BY branch_id` = ranger les 500 fiches clients dans 8 boîtes fermées, une par agence. Sur le rapport, pour chaque boîte, on ne peut écrire que :
- **l'étiquette** de la boîte (« Agence 1 ») → colonne du `GROUP BY` ;
- **un résumé** du contenu (« 91 fiches », « la plus ancienne date de 2015 ») → fonction d'agrégat.

Impossible d'écrire « le segment de la boîte 1 » : elle en contient 4. Comme un directeur qui ne peut pas écrire **un** prénom pour **toute** une classe de 30 élèves.

**Corriger selon la question posée :**

| Je veux… | Correction | Requête |
| --- | --- | --- |
| le détail par agence **et** par segment | faire de `segment` une **étiquette** | `GROUP BY branch_id, segment` |
| une ligne par agence, avec un résumé des segments | **résumer** `segment` | `COUNT(DISTINCT segment)` avec `GROUP BY branch_id` |

**Méthode** : pour chaque colonne du `SELECT`, se demander « **étiquette ou résumé ?** ». Étiquette → `GROUP BY`. Résumé → agrégat. Ni l'un ni l'autre → la question est mal posée.

### 2.4 SUM, AVG : des montants par catégorie

Activité par canal (transactions postées, toute la période) :

```sql
SELECT   channel,
         COUNT(*)               AS nb,
         SUM(amount_xof)        AS total_xof,
         ROUND(AVG(amount_xof)) AS moyenne_xof
FROM     txn
WHERE    status = 'POSTED'
GROUP BY channel
ORDER BY total_xof DESC;
```

| CHANNEL | NB | TOTAL_XOF | MOYENNE_XOF |
| --- | ---: | ---: | ---: |
| BRANCH | 23 314 | 4 073 699 023 | 174 732 |
| TRANSFER | 5 340 | 2 345 982 292 | 439 323 |
| MOBILE_MONEY | 11 982 | 388 342 000 | 32 410 |
| CARD | 6 589 | 278 238 922 | 42 228 |
| BATCH | 13 671 | 59 456 733 | 4 349 |

Lecture métier : le Mobile Money fait **presque 2 fois plus d'opérations** que la carte, mais avec des montants moyens faibles (32 000 XOF) ; les virements sont peu nombreux mais pèsent lourd (439 000 XOF en moyenne). **Compter et sommer racontent deux histoires différentes** : il faut souvent les deux.

### 2.5 HAVING : filtrer les paquets

```sql
-- Clients titulaires de plus de 3 comptes
SELECT   customer_id, COUNT(*) AS nb_comptes
FROM     account_holder
GROUP BY customer_id
HAVING   COUNT(*) > 3
ORDER BY nb_comptes DESC;
```

→ 16 clients ; le premier (client 126) détient 7 comptes.

**`WHERE` ou `HAVING` ?**

| | `WHERE` | `HAVING` |
| --- | --- | --- |
| Filtre | des **lignes** | des **paquets** |
| Quand | **avant** le regroupement | **après** le regroupement |
| Peut contenir un agrégat ? | **non** (`WHERE COUNT(*) > 3` → erreur) | **oui** |
| Exemple | `WHERE status = 'POSTED'` | `HAVING COUNT(*) > 3` |

Ordre d'exécution complet :

```text
1. FROM      → je prends la table
2. WHERE     → je garde certaines LIGNES
3. GROUP BY  → je fais les paquets
4. HAVING    → je garde certains PAQUETS
5. SELECT    → je calcule les colonnes
6. ORDER BY  → je trie
```

Règle pratique : tout ce qui peut être filtré **avant** (une condition sur une ligne) va dans `WHERE`. C'est plus juste et plus rapide : moins de lignes à regrouper.

### 2.6 L'agrégation conditionnelle : COUNT(CASE WHEN …) et SUM(CASE WHEN …)

Le `CASE` de la notion 1, **à l'intérieur** d'un agrégat : plusieurs comptages dans **une seule ligne** par paquet.

```sql
SELECT   branch_id,
         COUNT(*)                                     AS nb_comptes,
         COUNT(CASE WHEN status = 'ACTIVE' THEN 1 END) AS actifs,
         COUNT(CASE WHEN status = 'CLOSED' THEN 1 END) AS clotures
FROM     account
GROUP BY branch_id
ORDER BY branch_id;
```

| BRANCH_ID | NB_COMPTES | ACTIFS | CLOTURES |
| ---: | ---: | ---: | ---: |
| 1 | 153 | 119 | 20 |
| 2 | 112 | 83 | 20 |
| … | … | … | … |

Comment ça marche : pour un compte actif, le `CASE` renvoie 1 ; sinon, sans `ELSE`, il renvoie **NULL**, et `COUNT` ignore les NULL. On ne compte donc que les comptes actifs.

C'est **exactement** la technique de la requête S02 du contrôle technique :

```sql
SELECT   txn_id
FROM     gl_entry
GROUP BY txn_id                                                                -- 1 paquet par transaction
HAVING   SUM(CASE dc_flag WHEN 'D' THEN amount_xof ELSE -amount_xof END) <> 0; -- débits − crédits ≠ 0
```

Débit compté en `+`, crédit en `−`, par transaction. Si la transaction est équilibrée, la somme vaut 0 ; `HAVING <> 0` ne garde que les **paquets déséquilibrés**. S02 est maintenant lisible.

### 2.7 Pièges

| Piège | Exemple réel | Parade |
| --- | --- | --- |
| `SUM` de rien = **NULL**, pas 0 | `SUM(amount_xof)` sur un canal inexistant → NULL ; `COUNT(*)` → 0 | `NVL(SUM(...), 0)` |
| `AVG` dépend de la population | découvert moyen : `AVG(overdraft_limit)` = **86 000** sur tous les comptes, mais **494 964** sur les seuls comptes qui ont un découvert | Définir **sur quelle population** on fait la moyenne |
| `COUNT(*)` ≠ `COUNT(DISTINCT …)` | `ACCOUNT_HOLDER` : 847 lignes, mais 487 clients différents | `COUNT(DISTINCT customer_id)` pour compter des clients |
| Un agrégat dans `WHERE` | `WHERE COUNT(*) > 3` → erreur | `HAVING` |
| Filtrer dans `WHERE` ce qu'on veut **compter** | `WHERE role <> 'PRIMARY'` supprime les lignes PRIMARY : impossible ensuite de les compter, et un compte à 0 PRIMARY disparaît du résultat | Garder toutes les lignes et compter avec `COUNT(CASE WHEN role = 'PRIMARY' THEN 1 END)` |
| Alias du `SELECT` dans `HAVING` | `HAVING nb_primary <> 1` : accepté en 23ai, **refusé en 19c** (le `SELECT` s'exécute après le `HAVING`) | Répéter l'expression complète dans le `HAVING` |
| Inventaire au lieu de contrôle | 800 lignes « tout va bien » | Un contrôle ne renvoie **que les anomalies** : filtre `HAVING … <> 1` |
| Colonne ni groupée ni agrégée | `ORA-00979` | Règle d'or 2.3 |
| Croire que `GROUP BY` affiche les catégories vides | Agence 2 sans CORPORATE : pas de ligne à 0 | Le savoir ; on les fera apparaître avec `LEFT JOIN` (notion 3) |

Le piège `AVG` est un **piège de définition**, pas de SQL : « le découvert moyen » vaut 86 000 ou 494 964 selon la question posée. Il faut l'écrire dans la définition retenue (étape 2 de la méthode).

### 2.8 Exercices

| # | Énoncé | Résultat attendu |
| --- | --- | --- |
| E6 | Nombre de transactions **par type** (`txn_type`), du plus fréquent au moins fréquent. | 9 lignes ; la première : `DEPOSIT`, 18 075 — ✅ validé le 03/10 (retirer le `HAVING COUNT(*) > 0` inutile) |
| E7 | Les produits (`product_id`) qui ont **plus de 50 comptes**. | 4 lignes — ✅ validé le 03/10 (ajouter `ORDER BY` ; recoupement 722 + 78 = 800) |
| E8 | Pour chaque agence, **sur une seule ligne** : le nombre de clients et le nombre d'**entreprises**. | 8 lignes ; agence 1 : 91 clients dont 12 entreprises (recoupe E1) — ✅ validé le 03/10 (après correction de la casse `'COMPANY'`) |
| E9 | Combien de clients **n'ont aucun compte** ? Sans jointure : je compare le nombre de clients de `CUSTOMER` avec le nombre de clients **différents** de `ACCOUNT_HOLDER`. | 13 — ✅ validé le 03/10 (500 − 487). En une requête : `SELECT (SELECT COUNT(*) FROM customer) - (SELECT COUNT(DISTINCT customer_id) FROM account_holder) FROM dual;` |
| E10 | Les agences dont le **retrait moyen au guichet** dépasse **130 000 XOF** (`txn_type = 'WITHDRAWAL'`, `channel = 'BRANCH'`, `status = 'POSTED'`). Quelles conditions vont dans `WHERE`, laquelle dans `HAVING` ? | 3 agences — ✅ validé le 05/10 (agences 2, 3, 8). Test : « peut-on décider en regardant **un seul** retrait ? » Oui → `WHERE` ; non (moyenne de l'agence) → `HAVING` |
| E11 | Le montant total des **frais** (`txn_type = 'FEE'`, postés) **par année**. Indice : `EXTRACT(YEAR FROM business_date)`. J'explique pourquoi 2024 est deux fois plus faible que 2025. | 3 lignes ; 2026 : 14 253 960 XOF — ✅ validé le 05/10 (2024 : 6 950 080 ; 2025 : 14 095 700). Effet stock : les frais dépendent du nombre de comptes ouverts, qui part de 0 en janvier 2024 ; 2026 dépasse 2025 en 9 mois seulement |

### 2.9 Le contrôle du projet : S06

**Règle** : chaque compte a **exactement un** titulaire `PRIMARY`. Famille : **cardinalité** (voir `note.md`, section 5).

À écrire dans `sql/00_sanity/sanity_checks.sql`, sous le `TODO` de S06, en deux parties :

1. **Les comptes qui ont 0 ou plusieurs `PRIMARY` parmi leurs titulaires.** Partir de `ACCOUNT_HOLDER`, un paquet par compte, et compter seulement les `PRIMARY` (agrégation conditionnelle, 2.6). Garder les paquets où ce compte est différent de 1. Attendu : 0 ligne.
2. **Les comptes qui n'ont aucun titulaire du tout.** Ils n'ont aucune ligne dans `ACCOUNT_HOLDER`, donc la partie 1 ne peut pas les voir. Avec ce que je sais déjà : je compare le nombre de comptes de `ACCOUNT` avec le nombre de comptes **différents** de `ACCOUNT_HOLDER`. Attendu : les deux chiffres sont égaux (800).

À la notion 3, on réécrira S06 en **une seule requête** avec un `LEFT JOIN`, qui donnera directement le numéro des comptes fautifs.

Prouver que le contrôle fonctionne :

```sql
UPDATE account_holder SET role = 'JOINT' WHERE account_id = 1;   -- le compte 1 n'a plus de PRIMARY
-- relancer S06 partie 1 → doit renvoyer le compte 1
ROLLBACK;                                                        -- on annule
```

### 2.10 À retenir

- Ordre d'exécution : `FROM → WHERE → GROUP BY → HAVING → SELECT → ORDER BY`.
- Règle d'or : chaque colonne du `SELECT` est **groupée ou agrégée** ; chaque colonne groupée est **affichée**.
- `WHERE` filtre des lignes (avant), `HAVING` filtre des paquets (après, avec agrégats).
- Les agrégats ignorent les NULL ; `SUM` de rien = NULL → `NVL(SUM(...), 0)`.
- `COUNT(*)` compte des lignes, `COUNT(DISTINCT x)` compte des choses différentes : toujours se demander **ce que je compte**.
- Agrégation conditionnelle `COUNT(CASE WHEN … THEN 1 END)` : plusieurs indicateurs sur une ligne ; c'est la base de S02 et S06.
- Recoupement systématique : la somme des paquets = le total sans `GROUP BY`.
- **Méthode anti-blocage** : dessiner d'abord le tableau de résultat voulu. `SELECT` = ses colonnes, `GROUP BY` = ses étiquettes, les montants seulement dans `SUM()`/`AVG()`. Quand ça ne marche pas, **retirer** des colonnes, ne pas en ajouter.
  - *Analogie du formulaire* : le directeur remet un formulaire imprimé. Les **en-têtes de colonnes** (« Année », « Total des frais ») = le `SELECT` ; les **en-têtes de lignes** (2024, 2025, 2026) = le `GROUP BY`. Une case ne contient qu'une valeur : impossible d'y écrire « le montant de 2024 » (2 414 prélèvements) → soit on découpe la ligne (montant ajouté au `GROUP BY`), soit Oracle refuse (`ORA-00979`).
  - *Analogie du classement* : une ligne par équipe (étiquette), « matchs joués » et « points » (résumés). On n'ajoute pas « score du match » : c'est un détail d'un match, pas une information sur l'équipe.
- `'FEE'` (entre apostrophes) est une **valeur** ; `amount_xof` (sans apostrophes) est une **colonne**. On somme une colonne, jamais une valeur.
- **Le mot « par » décide du `GROUP BY`** : « total **par** année » → `GROUP BY` l'année ; « **le** total » (sans « par ») → **pas de `GROUP BY`**, une seule ligne. Un montant n'est **jamais** une étiquette : il ne va que dans `SUM()` / `AVG()`. (Piège refait 3 fois : E10, E11, E16.)

## Notion 3 — JOIN (INNER, LEFT)

> La notion la plus utile au travail : dans une vraie base bancaire, l'information est **éparpillée** dans des dizaines de tables. Presque chaque requête en relie plusieurs.

### 3.1 Le problème : l'information est rangée dans plusieurs classeurs

À E3 et E7, j'ai affiché `product_id` : 1, 4, 2… Un responsable ne sait pas ce qu'est « le produit 6 ». Le **nom** du produit est rangé **ailleurs**, dans la table `PRODUCT`.

**L'image : deux classeurs reliés par un numéro.**

```text
Classeur ACCOUNT (les comptes)              Classeur PRODUCT (le catalogue)
┌───────────────┬────────────┐              ┌────────────┬──────────────────────────────┐
│ account_number│ product_id │              │ product_id │ name                         │
├───────────────┼────────────┤              ├────────────┼──────────────────────────────┤
│ 002-040007    │     1  ────┼──────────────►     1      │ Compte courant particulier   │
│ 002-040014    │     5  ────┼──────────────►     5      │ Dépôt à terme 12 mois        │
└───────────────┴────────────┘              └────────────┴──────────────────────────────┘
```

Sur chaque fiche compte, il y a un **numéro de produit**. Pour trouver le nom, on va dans le catalogue chercher **la fiche qui porte le même numéro**. C'est ça, une **jointure** : rapprocher deux tables grâce à une colonne commune.

### 3.2 La syntaxe : JOIN … ON …

```sql
SELECT a.account_number, a.product_id, p.name AS product_name
FROM   account a
JOIN   product p ON p.product_id = a.product_id
ORDER  BY a.account_id
FETCH  FIRST 3 ROWS ONLY;
```

| ACCOUNT_NUMBER | PRODUCT_ID | PRODUCT_NAME |
| --- | ---: | --- |
| 002-040007 | 1 | Compte courant particulier |
| 004-040007 | 1 | Compte courant particulier |
| 002-040014 | 5 | Dépôt à terme 12 mois |

Mot à mot :

| Morceau | Sens |
| --- | --- |
| `FROM account a` | je pars du classeur des comptes, que j'appelle **`a`** (un surnom, ou **alias**) |
| `JOIN product p` | je l'attache au catalogue des produits, que j'appelle **`p`** |
| `ON p.product_id = a.product_id` | **la règle de rapprochement** : « le numéro de produit du catalogue = le numéro de produit du compte » |
| `a.account_number` | la colonne `account_number` **du classeur `a`** |

**Pourquoi les alias `a.` et `p.` ?** Les deux tables ont une colonne `product_id`. Sans préciser laquelle, Oracle refuse : `ORA-00918: column ambiguously defined`. Règle : dès qu'il y a une jointure, **préfixer toutes les colonnes** par l'alias de leur table.

### 3.3 Joindre puis regrouper : E7 avec le nom des produits

```sql
SELECT   p.name, COUNT(*) AS nb_accounts
FROM     account a
JOIN     product p ON p.product_id = a.product_id
GROUP BY p.name
ORDER BY nb_accounts DESC;
```

| NAME | NB_ACCOUNTS |
| --- | ---: |
| Compte courant particulier | 390 |
| Épargne 3,5 % | 163 |
| Compte courant professionnel | 93 |
| Prêt consommation | 76 |
| Dépôt à terme 12 mois | 37 |
| Prêt automobile | 25 |
| Compte courant en euros | 16 |

Ordre d'exécution : la jointure fait partie du `FROM`, donc elle a lieu **en premier**. On attache les classeurs, **puis** on filtre, **puis** on range dans les boîtes.

```text
1. FROM + JOIN   → j'attache les classeurs
2. WHERE         → je garde certaines lignes
3. GROUP BY      → je fais les boîtes
4. HAVING        → je garde certaines boîtes
5. SELECT        → j'écris les colonnes
6. ORDER BY      → je trie
```

### 3.4 Plusieurs jointures à la suite : la chaîne

Pour afficher **le nom du client** d'un compte, il faut passer par le registre des signatures (`ACCOUNT_HOLDER`), car `ACCOUNT` n'a pas de colonne client.

```text
ACCOUNT ──► ACCOUNT_HOLDER ──► CUSTOMER          (qui est le titulaire ?)
   └──────► BRANCH                               (quelle agence ?)
```

```sql
SELECT a.account_number, c.full_name, b.name AS branch_name
FROM   account a
JOIN   account_holder ah ON ah.account_id  = a.account_id
                        AND ah.role        = 'PRIMARY'
JOIN   customer c        ON c.customer_id  = ah.customer_id
JOIN   branch b          ON b.branch_id    = a.branch_id
ORDER  BY a.account_id
FETCH  FIRST 3 ROWS ONLY;
```

| ACCOUNT_NUMBER | FULL_NAME | BRANCH_NAME |
| --- | --- | --- |
| 002-040007 | Lassina Brou | Cocody |
| 004-040007 | Bakary Cissé | Marcory |
| 002-040014 | Ets Tano & Fils | Cocody |

Chaque `JOIN` attache **un classeur de plus**, avec **sa propre règle** `ON`. Le `AND ah.role = 'PRIMARY'` garantit **un seul** titulaire par compte : sans lui, un compte joint apparaîtrait deux fois (voir 3.6).

### 3.5 INNER JOIN ou LEFT JOIN ?

`JOIN` tout court = **`INNER JOIN`** : on ne garde que les lignes qui ont **trouvé un partenaire** de l'autre côté.

**L'image : la soirée dansante.** On forme des couples client ↔ compte.
- **INNER JOIN** : on ne prend la photo **que des couples formés**. Celui qui danse seul **n'est pas sur la photo**.
- **LEFT JOIN** : on prend la photo de **tous les invités de gauche**. Celui qui n'a pas de partenaire est **quand même sur la photo**, avec une place vide (NULL) à côté de lui.

| | Lignes | Pourquoi |
| --- | ---: | --- |
| `customer c JOIN account_holder ah` | **847** | uniquement les clients qui ont au moins une signature |
| `customer c LEFT JOIN account_holder ah` | **860** | les 847 + les **13 clients sans compte**, avec des NULL à droite |

Recoupement : 860 − 847 = **13**, exactement le résultat d'E9.

**Retrouver ceux qui n'ont pas de partenaire** : `LEFT JOIN` puis garder les lignes où le côté droit est vide.

```sql
SELECT c.customer_id, c.full_name
FROM   customer c
LEFT   JOIN account_holder ah ON ah.customer_id = c.customer_id
WHERE  ah.customer_id IS NULL;
```

→ **13 clients**, cette fois **avec leur nom** (E9 ne donnait que le nombre). Par exemple : Drissa Tano, Seydou Traoré… et une seule entreprise, Boulangerie Ouattara.

Règle : **la table « de gauche »** est celle écrite **avant** `LEFT JOIN` ; c'est elle dont on garde **toutes** les lignes. On met donc à gauche la table dont on ne veut perdre personne.

### 3.6 Le piège n° 1 : le fan-out (la jointure qui multiplie)

Total des soldes au 30/09/2026 :

| Requête | Lignes | Total |
| --- | ---: | ---: |
| `DAILY_BALANCE` seule | 694 | **2 153 269 830** |
| `DAILY_BALANCE` jointe à **tous** les titulaires | 740 | **2 366 195 618** |
| `DAILY_BALANCE` jointe aux seuls `PRIMARY` | 694 | 2 153 269 830 ✅ |

La deuxième requête affiche **213 millions de trop** (+ 10 %), **sans aucune erreur**.

Pourquoi : un compte joint a 2 lignes dans le registre (PRIMARY + JOINT). La jointure **colle le solde du compte à chacune des deux lignes** : le solde est compté **deux fois**.

**L'image : la photocopieuse.** Une jointure vers une table qui a **plusieurs** partenaires pour une même ligne **photocopie** cette ligne autant de fois. Si on additionne ensuite les photocopies, le total gonfle.

Parades :
1. **Avant** chaque jointure, se demander : « pour une ligne de gauche, combien de partenaires à droite ? 0, 1, ou **plusieurs** ? »
2. Si plusieurs : réduire à un seul (ici `role = 'PRIMARY'`), ou **pré-agréger** avant de joindre (notion 5).
3. **Recouper** : compter les lignes avant et après la jointure (694 → 740 = alarme), et comparer le total à celui de la table seule.

### 3.7 Pièges

| Piège | Exemple réel | Parade |
| --- | --- | --- |
| Oublier la règle `ON` | `FROM customer, account` sans condition → **400 000** lignes (500 × 800) : chaque client marié à chaque compte | Toujours une condition de rapprochement par jointure |
| Colonne sans alias | `SELECT product_id …` avec deux tables qui l'ont → `ORA-00918` | Préfixer **toutes** les colonnes (`a.`, `p.`) |
| `LEFT JOIN` annulé par le `WHERE` | `LEFT JOIN account_holder ah … WHERE ah.role = 'PRIMARY'` → **800** lignes : les clients sans partenaire (role NULL) sont éliminés, le `LEFT` redevient un `INNER` | Mettre la condition sur la table de droite **dans le `ON`** : `… ON ah.customer_id = c.customer_id AND ah.role = 'PRIMARY'` → **818** lignes, dont 18 clients sans compte PRIMARY (13 sans compte + 5 seulement cotitulaires ou mandataires) |
| Fan-out | +213 millions au 30/09 (3.6) | Vérifier la cardinalité, compter les lignes avant/après |
| `INNER` qui perd des lignes en silence | Un compte sans titulaire disparaît d'un `JOIN` | `LEFT JOIN` quand on ne veut perdre personne |

### 3.8 Exercices

| # | Énoncé | Résultat attendu |
| --- | --- | --- |
| E12 | Le nombre de comptes **par nom de produit**, du plus grand au plus petit. (Je le refais **sans regarder** 3.3.) | 7 lignes ; « Compte courant particulier » : 390 — ✅ validé le 12/10 (j'avais oublié `DESC` : `ORDER BY` trie par défaut du plus petit au plus grand ; regrouper par `p.product_id, p.name` par prudence) |
| E13 | Pour chaque compte : son numéro, le **nom du titulaire principal** et le **nom de l'agence**. Combien de lignes ? Pourquoi ce nombre est-il rassurant ? | 800 lignes ; le compte 002-040014 appartient à « Ets Tano & Fils » (Cocody) — ✅ validé le 14/10 (1er essai avec `'JOINT'` : 39 lignes). 800 = nombre de comptes : aucun compte **perdu** (INNER) ni **photocopié** (fan-out), une ligne par compte |
| E14 | Le nombre de transactions de **septembre 2026** (`txn_date`) par **nom d'agence**, de la plus active à la moins active. Je recoupe le total avec E2. | 8 lignes ; Plateau en tête avec 558 ; total 2 930 — ✅ validé le 14/10 (recoupement 558 + 496 + 403 + 400 + 327 + 275 + 269 + 202 = 2 930 ; préférer `GROUP BY b.branch_id, b.name`) |
| E15 | La **liste** des clients sans aucun compte, avec leur nom et leur type (`LEFT JOIN`). Je recoupe avec E9. | 13 lignes, dont 1 entreprise — ✅ validé le 14/10 (afficher aussi `c.customer_id` à cause des homonymes) |
| E16 | Le **piège du fan-out** : je calcule le total des soldes (`ledger_balance`) au 30/09/2026 (1) depuis `DAILY_BALANCE` seule, (2) en joignant `ACCOUNT_HOLDER` **sans** filtre de rôle. Je compte aussi les lignes. J'explique l'écart en une phrase métier. | 694 lignes / 2 153 269 830 contre 740 lignes / 2 366 195 618 — ✅ validé le 14/10. Ma phrase métier : « Au 30/09/2026, le total des soldes clients affiché est de 2 366 195 618 XOF alors que le total réel est de 2 153 269 830 XOF, soit un écart de 212 925 789 XOF (+10 %). Cet écart vient du fait que certains comptes appartiennent à plusieurs personnes et ont donc été comptés plusieurs fois. Si ce chiffre partait dans un rapport, la direction croirait que les soldes clients sont supérieurs de 213 millions à la réalité. » |

### 3.9 Les contrôles du projet : S07 et S09

**S07 — Le statut actuel = le dernier statut de l'historique.** Famille : **deux sources**.
- Règle : pour chaque compte, `ACCOUNT.status` doit être égal au statut de la période **en cours** dans `ACCOUNT_STATUS_HIST` (celle où `valid_to IS NULL`).
- Pistes :
  - Partir de `ACCOUNT` (on ne veut perdre **aucun** compte) → quel type de jointure ?
  - La condition « période en cours » porte sur la table de droite → où la mettre (3.7) ?
  - Deux sortes d'anomalies : le compte n'a **pas** de période en cours (côté droit vide), **ou** les deux statuts **diffèrent**.
- Attendu : **0 ligne**.

**S09 — Aucune écriture après la clôture d'un compte.** Famille : **cohérence temporelle**.
- Règle : un compte clôturé (`close_date` renseignée) ne doit avoir **aucune** écriture (`GL_ENTRY.entry_date`) **après** sa date de clôture.
- Pistes : joindre `GL_ENTRY` et `ACCOUNT`, puis comparer les deux dates.
- **La question à me poser** : `>` ou `>=` ? J'essaie les deux. Avec l'un, je trouverai **0**, avec l'autre **140**. Lequel est le bon contrôle, et pourquoi ? (Indice : que fait le générateur **le jour même** de la clôture ? `generate.py`, fonction `planned`, cas `"close"`.)
- Attendu : **0 ligne**.

**Bonus — S06 en une seule requête.** Comme prévu à la notion 2 : réécrire S06 en partant de `ACCOUNT` avec un `LEFT JOIN` vers `ACCOUNT_HOLDER`, pour attraper **en une fois** les comptes à 0 PRIMARY, à 2 PRIMARY **et** sans aucun titulaire.

Prouver chaque contrôle avec un `UPDATE` suivi d'un `ROLLBACK`, comme pour S06.

### 3.10 À retenir

- Une jointure **rapproche deux tables** grâce à une colonne commune : `JOIN table alias ON règle`.
- Avec une jointure, **préfixer toutes les colonnes** par l'alias de leur table.
- `JOIN` (INNER) = seulement les couples formés ; `LEFT JOIN` = **tous** ceux de gauche, avec NULL quand il n'y a pas de partenaire.
- « A sans B » = `LEFT JOIN … WHERE b.colonne IS NULL`.
- Une condition sur la table de droite d'un `LEFT JOIN` va **dans le `ON`**, pas dans le `WHERE`.
- **Avant chaque jointure** : « combien de partenaires pour une ligne ? » Plusieurs → risque de **fan-out** (+213 millions au 30/09).
- Recouper : nombre de lignes et total **avant / après** la jointure.
- **Écrire une règle `ON` en 3 étapes** : (1) `DESC` des deux tables ; (2) repérer la colonne qui porte **le même renseignement** (souvent le même nom, souvent en `_id`) ; (3) `ON a.colonne = b.colonne`. Un nom de colonne ne se **devine** jamais (E14 : `t.txn_id` au lieu de `t.branch_id` ; E16 : `account_holder_id` inventé).

## Notion 4 — Sous-requêtes, EXISTS / NOT EXISTS

*À compléter.*

## Notion 5 — CTE (WITH ... AS)

*À compléter.*

## Notion 6 — Fonctions de fenêtrage

*À compléter.*
