# Notes — ce que je dois retenir

> Fiche de révision personnelle, complétée au fil du parcours. Une notion = un exemple concret.
> Dernière mise à jour : 01/10/2026 (semaine 1, niveau 0).

## 1. Le projet en une phrase

Je construis une banque fictive (**Lagune Bank**, XOF, 8 agences) sous Oracle pour apprendre à transformer une **demande métier floue** en **chiffre juste, vérifié et documenté**.

## 2. Les concepts métier essentiels

### Un Core Banking = un grand livre comptable

Chaque opération produit des **écritures équilibrées** (débits = crédits). Un solde n'est **que la somme des écritures**.

Exemple — dépôt d'espèces de 100 000 XOF au guichet :

| Écriture | Compte comptable | Compte client | Sens | Montant |
| --- | --- | --- | --- | ---: |
| 1 | 571100 Caisse | — | Débit | 100 000 |
| 2 | 251100 Comptes courants | 001-45872 | Crédit | 100 000 |

Convention du lab : un **crédit augmente** le solde d'un compte client, un **débit le diminue**.

### Transaction ≠ écriture

- 1 transaction (`TXN`) = 2 écritures ou plus (`GL_ENTRY`).
- Pour **compter des opérations** → `TXN`. Si je compte `GL_ENTRY`, j'obtiens le double.

### `GL_ENTRY` = les lignes du grand livre

GL = *General Ledger* = **grand livre**. `TXN` décrit l'**événement** (« Mme Koné vire 50 000 à M. Traoré »). `GL_ENTRY` contient les **lignes comptables** que cet événement produit.

```text
TXN (1) ──< GL_ENTRY (2..n) >── GL_ACCOUNT (toujours)
                  └──────────>── ACCOUNT    (seulement si un client est concerné)
```

Exemple : virement de 50 000 XOF avec 500 XOF de frais = **1 transaction, 4 écritures**.

| entry | txn_id | gl_account | account_id | dc_flag | amount |
| --- | --- | --- | --- | --- | ---: |
| 1 | 9001 | 251100 Comptes courants | Koné | D | 50 000 |
| 2 | 9001 | 251100 Comptes courants | Traoré | C | 50 000 |
| 3 | 9001 | 251100 Comptes courants | Koné | D | 500 |
| 4 | 9001 | 706100 Commissions | **NULL** | C | 500 |

- Débits (50 500) = crédits (50 500) → la transaction est **équilibrée**.
- `account_id` est NULL quand l'écriture ne touche **que** la banque (caisse, commissions…).
- `gl_account_id` est **toujours** renseigné : c'est la vision comptable de la banque.
- Les colonnes à connaître :
  - `dc_flag` : D (débit) ou C (crédit) ;
  - `amount` : le montant dans la devise du compte ;
  - `amount_xof` : la contre-valeur en XOF ;
  - `entry_date` : la date comptable ;
  - `value_date` : la date de valeur.

Trois requêtes types :

```sql
-- Solde d'un compte client = somme de ses écritures
SELECT SUM(CASE dc_flag WHEN 'C' THEN amount ELSE -amount END)
FROM   gl_entry WHERE account_id = :id;

-- Contrôle : chaque transaction est équilibrée (attendu : 0 ligne)
SELECT txn_id FROM gl_entry GROUP BY txn_id
HAVING SUM(CASE dc_flag WHEN 'D' THEN amount_xof ELSE -amount_xof END) <> 0;

-- Compter des opérations : sur TXN, pas sur GL_ENTRY
SELECT COUNT(*) FROM txn WHERE status = 'POSTED';
```

### Les trois soldes

| Solde | Calcul |
| --- | --- |
| Comptable | Somme des écritures |
| Disponible | Comptable − blocages en cours + découvert autorisé |
| En valeur | Somme des écritures selon leur **date de valeur** |

Exemple : comptable 500 000, blocage 150 000, découvert autorisé 100 000 → **disponible 450 000 XOF**.

### Un statut a une histoire

- `ACCOUNT.status` = état **actuel** uniquement.
- Question à une date passée (« actifs au 31/08 ») → **`ACCOUNT_STATUS_HIST`** avec `valid_from <= :as_of AND (valid_to IS NULL OR valid_to > :as_of)`.

### On n'efface pas, on extourne

Frais de 2 500 prélevés par erreur → une transaction inverse de 2 500 qui pointe vers l'originale (`reversal_of_txn_id`). Les deux restent en base. Pour un total net, il faut **soit exclure les deux, soit compter les deux**, jamais une seule.

### Le calendrier compte

Pas de solde photographié le week-end ni les jours fériés. « J-30 » = **dernier jour ouvré disponible** ≤ J-30.

### Client ↔ compte : la table `ACCOUNT_HOLDER`

`ACCOUNT` n'a **pas** de colonne client, `CUSTOMER` n'a pas de colonne compte. Le lien passe par `ACCOUNT_HOLDER` : une ligne = « tel client détient tel compte, avec tel rôle » (`PRIMARY`, `JOINT`, `PROXY`).

```text
CUSTOMER (1) ──< ACCOUNT_HOLDER >── (1) ACCOUNT
```

- Un client → plusieurs comptes (client 440, Moussa Dosso : 6 comptes, 3 PRIMARY + 3 JOINT).
- Un compte → plusieurs titulaires (compte 1 : client 1 PRIMARY + client 95 JOINT = compte joint).
- Relation **plusieurs-à-plusieurs** → table intermédiaire. Analogie : le registre des signatures.
- Conséquence : 847 lignes mais 487 clients différents → compter des clients = `COUNT(DISTINCT customer_id)`.
- C'est aussi la source du **fan-out** : passer par cette table pour aller du client aux montants peut compter deux fois un compte joint.

### Les trois dates d'une opération (`TXN`)

| Colonne | Question | Nom en banque |
| --- | --- | --- |
| `txn_date` | Quand le client a-t-il agi ? (avec l'heure) | Date d'opération |
| `business_date` | Dans quelle journée comptable la banque l'a-t-elle enregistrée ? | Date comptable |
| `value_date` | À partir de quand l'argent compte-t-il pour les intérêts ? | Date de valeur |

- Exemple réel : paiement carte n° 45, **samedi** 06/01/2024 16h11 → comptabilisé **lundi** 08/01/2024. 11 770 opérations (19 %) sont dans ce cas (week-ends, fériés).
- Analogie : lettre postée samedi soir (opération), tamponnée lundi (comptable), chèque encaissé plus tard (valeur).
- Choisir la date fait partie de la **définition** : activité client → `txn_date` ; comptabilité, frais, arrêté → `business_date` ; intérêts, solde en valeur → `value_date`.
- ⚠️ Limite du lab : `value_date` = `business_date` partout (`generate.py`, ligne 364). À citer si on calcule des intérêts ou un solde en valeur.

### Le segment = la catégorie commerciale du client

| Segment | Signification | Type | Nb |
| --- | --- | --- | ---: |
| RETAIL | Particulier grand public, offres standard | PERSON | 378 |
| PREMIUM | Particulier aisé, conseiller dédié | PERSON | 53 |
| SME | PME (*Small and Medium Enterprises*) | COMPANY | 55 |
| CORPORATE | Grande entreprise, chargé d'affaires dédié | COMPANY | 14 |

- Sert à adapter offres, tarifs et suivi ; axe d'analyse très fréquent (`GROUP BY segment` : encours, commissions, attrition par segment).
- ⚠️ Limite du lab : dans une vraie banque, le segment dépend de critères mesurables (revenus, patrimoine, chiffre d'affaires). Ici il est tiré **au hasard** (`generate.py`, lignes 185-191) → les PREMIUM ne sont pas forcément plus riches. À citer dans les limites d'une note de livraison.

## 3. Pièges Oracle

| Piège | À retenir |
| --- | --- |
| `DATE` contient une heure | `= DATE '2026-06-30'` rate les lignes à 14h32. Utiliser `>= DATE '2026-06-30' AND < DATE '2026-07-01'` |
| `''` vaut `NULL` | `WHERE col = ''` ne renvoie jamais rien → `IS NULL` |
| Format d'affichage des dates (NLS) | Toujours un masque explicite : `TO_CHAR(d, 'DD/MM/YYYY')`, `TO_DATE('20260930', 'YYYYMMDD')` |
| `NOT IN` + `NULL` | Un seul `NULL` dans la sous-requête → 0 ligne. Utiliser **`NOT EXISTS`** |

## 4. Pièges SQL

### Le fan-out (jointure qui multiplie les lignes)

Un compte joint a 2 titulaires → `CUSTOMER → ACCOUNT_HOLDER → ACCOUNT → GL_ENTRY` duplique chaque écriture → **montant doublé, sans aucune erreur affichée**.

Parades :
- Vérifier la **cardinalité** de chaque jointure avant d'écrire la requête.
- **Pré-agréger** avant de joindre (ex. paiements de prêt par échéance).
- Utiliser `EXISTS` quand je veux seulement savoir « si ça existe ».
- Comparer `COUNT(*)` et `COUNT(DISTINCT id)` : s'ils diffèrent, il y a des doublons.

## 5. Ma méthode pour chaque demande

1. **Ticket** : reformuler et poser 3 questions (quelle date d'arrêté ? quel périmètre ? quelle unité ?).
2. **Définition** : écrire ce que veut dire « actif », « client », « encours »…
3. **Données** nécessaires.
4. **Tables et cardinalités** : y a-t-il un risque de doublon ?
5. **Requête** : des CTE successives, chacune testable seule.
6. **Validation** : nombre de lignes, total de contrôle, cas limites, **recoupement par un calcul indépendant**.
7. **Livraison** : note de livraison + une phrase métier.

**Phrase d'interprétation = un chiffre + un périmètre + une explication.** Exemple (E4) :
> « Sur la période du 01/01/2024 au 30/09/2026, 580 opérations Mobile Money ont été rejetées, toutes des retraits du compte vers un wallet, pour solde disponible insuffisant. »

Toujours préciser les **limites** : « dans ce modèle », ce que le chiffre ne couvre pas (ex. une vraie banque rejette aussi des dépôts : compte bloqué, plafond, KYC, anti-blanchiment).

### Requêtes de sanité / contrôles : « 0 ligne = tout va bien »

Avant toute analyse, je vérifie que la base est digne de confiance (`sql/00_sanity/sanity_checks.sql`, à relancer après chaque chargement).

Une requête de contrôle **cherche les anomalies** : 0 ligne = règle respectée ; chaque ligne renvoyée = un problème à investiguer.

```sql
-- Modèle générique : les lignes de A qui n'ont aucune ligne liée dans B
SELECT a.id FROM table_a a
WHERE  <filtre>
AND    NOT EXISTS (SELECT 1 FROM table_b b WHERE b.a_id = a.id);
```

Familles de contrôles : volumétrie, partie double (débits = crédits), recoupement de soldes, orphelins, unicité (1 seul titulaire PRIMARY), cohérence entre deux sources (statut actuel vs historique), chevauchement de périodes, mouvements après clôture.

**Contrôle technique** = une liste de règles qui doivent **toujours** être vraies (des invariants), vérifiées une par une avant d'utiliser la base. Chaque requête = un point OK/KO.

**Écrire un contrôle en 4 questions :**
1. Quelle règle doit toujours être vraie ?
2. À quoi ressemble une **violation** ?
3. Quelles tables et colonnes ?
4. Requête qui renvoie les violations → attendu 0 ligne.

| Famille | Question type | Technique SQL |
| --- | --- | --- |
| Absence | A sans B | `NOT EXISTS` |
| Orphelin | B pointe vers un A inexistant | `NOT EXISTS` ou `LEFT JOIN … IS NULL` |
| Cardinalité | exactement 1 | `GROUP BY` + `COUNT(CASE WHEN …)` + `HAVING <> 1` |
| Deux sources | A dit X, B dit Y | jointure + `<>` |
| Période | chevauchement | `LEAD(valid_from) OVER (PARTITION BY … ORDER BY …)` |
| Agrégat vs référence | somme des détails = total | **pré-agréger** dans une CTE, puis comparer |

Pièges récurrents :
- Partir de la **bonne table** : un compte sans aucun titulaire n'apparaît pas si je pars de `ACCOUNT_HOLDER`.
- Un `JOIN` simple fait disparaître les lignes sans correspondance → `LEFT JOIN` + `NVL`.
- `WHERE` filtre des lignes **avant** le `GROUP BY` ; `HAVING` filtre des **groupes** après.
- `>` ou `>=` sur les dates : se demander ce qui se passe **le jour même**.
- Un contrôle n'est prouvé que s'il a déjà trouvé quelque chose : casser une donnée (`UPDATE`), vérifier qu'il la détecte, puis `ROLLBACK`.

> Règle d'or : on ne livre **jamais** un chiffre sans l'avoir recoupé autrement.

> **Ne jamais ajuster une requête pour obtenir le chiffre attendu** (ex. `FETCH FIRST 12` pour « trouver » 12 lignes). Le chiffre attendu sert à **vérifier**. S'il ne correspond pas, je cherche **pourquoi** : filtre manquant, jointure qui duplique, piège de date ou de NULL.
> Erreur faite le 02/10/2026 sur l'exercice E1 : 91 clients coupés à 12, dont seulement 2 entreprises.

### Recouper = obtenir le même chiffre par un autre chemin

Si deux calculs **indépendants** donnent le même résultat, le chiffre est fiable. S'ils diffèrent, il y a une erreur à trouver **avant** de livrer.

| Mon chiffre | Recoupement possible |
| --- | --- |
| Transactions par agence (avec jointure) | Total général = `COUNT(*)` sur `TXN` seul, mêmes filtres, sans jointure |
| Solde d'un compte (somme des écritures) | = solde photographié dans `DAILY_BALANCE` |
| Somme des soldes clients d'un produit | = solde du compte comptable collectif (ex. 251100) : c'est le **rapprochement** |
| KPI calculé en SQL | Même KPI recalculé en Python/pandas à partir des tables brutes |
| N'importe quel résultat | 3 lignes vérifiées **à la main** |

Exemple : ma requête donne 1 250 transactions en août, mais `SELECT COUNT(*) FROM txn` avec les mêmes filtres en donne 1 180 → 70 lignes en trop → probablement une jointure qui duplique (fan-out).

⚠️ **Validation circulaire** = vérifier avec la même logique (relancer la même requête, ou contrôler des données avec le script qui les a générées). Ça ne prouve rien : le recoupement doit passer par une **autre source** ou une **autre méthode**.

## 6. Pièges d'environnement

| Symptôme | Cause | Solution |
| --- | --- | --- |
| `Fatal error in launcher: Unable to create process` avec un chemin bizarre | Le `.venv` a gardé un ancien chemin (dossier renommé ou déplacé) | `rm -rf .venv` puis `python -m venv .venv` |
| — | `pip.exe` dépend d'un chemin fixe | Préférer **`.venv/Scripts/python -m pip install ...`** |
| `ORA-01017: invalid credential` | L'image Docker ne crée l'utilisateur qu'au **1er démarrage du volume**. Si `.env` change après, la base garde l'ancien mot de passe | Réaligner le mot de passe (voir ci-dessous) ou repartir de zéro avec `docker compose down -v` (⚠️ efface toute la base) |

Réaligner le mot de passe de `CBS_LAB` sur `.env` (connexion administrateur interne au conteneur, sans mot de passe) :

```bash
MSYS_NO_PATHCONV=1 docker exec banking-oracle bash -c 'sqlplus -s / as sysdba <<EOF
ALTER SESSION SET CONTAINER = FREEPDB1;
ALTER USER $APP_USER IDENTIFIED BY "$APP_USER_PASSWORD" ACCOUNT UNLOCK;
EOF'
```

Réflexe face à une erreur `ORA-xxxxx` : lire le **code**, il dit presque toujours la cause (01017 = identifiants, 12541 = rien n'écoute sur le port, 00942 = table introuvable ou pas de droit).

Un `.venv` ne se déplace pas et ne se commite pas : il se **recrée** à partir de `requirements.txt`.

### TOAD vs SQL Developer

- Oracle Database = le **moteur** (exécute). TOAD, SQL Developer, SQL*Plus = des **clients** (envoient le SQL).
- Même requête = même résultat dans tous les clients. J'apprends le **SQL et Oracle**, pas un logiciel.
- TOAD (Quest) est payant → pas installé dans le projet ; SQL Developer (Oracle) est gratuit → utilisé chez moi.
- Au travail : vérifier que l'**autocommit est désactivé** dans TOAD (sinon un `UPDATE`/`DELETE` par erreur est validé immédiatement).
- Raccourcis : SQL Developer Ctrl+Entrée / F5 ; TOAD généralement F9 (requête) / F5 (script) / Ctrl+E (plan).
- Jamais d'exercice du projet sur la base de la banque.

### Héberger la base dans le cloud ?

- **Render** : pas d'Oracle géré (seulement PostgreSQL) ; Oracle en Docker demande ≥ 2 Go de RAM + disque persistant (payant) ; un service web n'expose que du HTTP, donc pas de connexion directe au port 1521 depuis mon terminal. → Render servira **plus tard** pour l'**API** (niveau 8), pas pour la base.
- **Oracle Cloud Free Tier** (« Always Free ») : Autonomous Database accessible depuis SQLcl / SQL Developer avec un *wallet*. Seule option simple et gratuite pour un Oracle en ligne (vérifier les quotas actuels).
- Par défaut : la base reste **en local** (Docker) ; l'objectif du portfolio est qu'un tiers l'installe en moins de 15 minutes.
- ⚠️ Ne jamais accéder au projet depuis le réseau de l'employeur.

### Le générateur (`data-generator/generate.py`)

Il invente 33 mois de vie bancaire (01/01/2024 → 30/09/2026) en mémoire, puis recrée le schéma et charge Oracle.

- **Graine** `--seed 42` : mêmes données à chaque exécution, donc résultats testables.
- **`post()`** = la partie double : 1 ligne `TXN` + 1 ligne `GL_ENTRY` par jambe, solde client mis à jour.
- **Simulation jour par jour** : salaires le 25, retraits en hausse en décembre, cartes, Mobile Money, virements, frais en fin de mois (2 % extournés), intérêts trimestriels, photo des soldes chaque jour ouvré.
- Paiement refusé si disponible insuffisant → `TXN.status = 'REJECTED'` **sans écriture**.
- Prêts : 75 % bons payeurs, 15 % en retard (paiements partiels), 10 % défaillants.
- v0 = données **propres**. v1 (sem. 14-15) = données **sales** + manifeste d'anomalies.
- Options : `--size small|medium|large`, `--dry-run` (sans charger la base).

### Voir la base

```text
Docker (conteneur banking-oracle) → Oracle (moteur) → FREEPDB1 (base) → CBS_LAB (schéma) → tables
```

On ne « voit » pas les tables dans Docker : on s'y connecte avec un **client SQL** sur `localhost:1521`, service `FREEPDB1`, utilisateur `CBS_LAB`.

- **SQL Developer** (ou l'extension VS Code) : connexion de type *Service name* = `FREEPDB1`. Exécuter : Ctrl+Entrée.
- **SQL*Plus** dans le conteneur : `winpty docker exec -it banking-oracle sqlplus CBS_LAB@FREEPDB1`

```sql
SELECT table_name, num_rows FROM user_tables ORDER BY table_name;  -- mes tables
DESC account                                                        -- colonnes d'une table
SELECT * FROM account FETCH FIRST 10 ROWS ONLY;                     -- aperçu, toujours limité
```

## 7. Règles de confidentialité

- Le projet se fait **chez moi**, avec des **données générées** uniquement.
- Aucun nom d'employeur, aucune table ni aucune donnée réelle dans le dépôt.
- `.env` (mots de passe) n'est jamais commité.

## 8. Où j'en suis

- [x] Plan de formation lu
- [x] Environnement préparé (Docker, schéma, générateur v0, outil `tools/db.py`)
- [x] Oracle lancé et jeu « small » chargé (01/10/2026 : 62 424 transactions, 123 655 écritures)
- [ ] Requêtes de sanité S04 → S10 écrites
- [ ] Journal de la semaine 1 rempli
- [ ] Niveau 1 : exercices 1 à 20 (bloc A)

## 9. Journal des notions apprises

<!-- Format : date — notion — exemple ou erreur faite -->

- 01/10/2026 — Transaction vs écriture, partie double, trois soldes, piège du fan-out.
- 01/10/2026 — `GL_ENTRY` : une ligne par écriture, `account_id` NULL pour les comptes internes, solde = somme signée des écritures.
- 01/10/2026 — Recouper : retrouver le même chiffre par une source ou une méthode indépendante ; éviter la validation circulaire.
- 01/10/2026 — `.venv` cassé après un renommage de dossier : le recréer, et utiliser `python -m pip`.
- 01/10/2026 — `ORA-01017` : utilisateur créé au 1er démarrage du volume avec un autre mot de passe ; réaligné par `ALTER USER`.
- 01/10/2026 — Le générateur : graine fixe, `post()` = partie double, simulation jour par jour, transactions rejetées sans écriture.
- 01/10/2026 — Requêtes de contrôle : invariants, méthode en 4 questions, 6 familles (absence, orphelin, cardinalité, deux sources, période, agrégat vs référence).
- 02/10/2026 — Notion 1 (voir `oracle.md`) : ordre d'exécution, `AND` avant `OR`, `BETWEEN` perd le dernier jour (2 093 au lieu de 2 930), `<> 'MM01'` ignore les NULL.
- 02/10/2026 — E1 : filtre « entreprises » oublié, et `FETCH FIRST 12` utilisé pour forcer le chiffre attendu. Leçon : le chiffre attendu sert à vérifier, pas à construire.
- 02/10/2026 — E1 validé. Afficher des colonnes de contrôle pendant le développement, les retirer à la livraison. Style : mots-clés en MAJUSCULES, noms en minuscules.
- 02/10/2026 — E2 : `BETWEEN DATE '2026-09-01' AND DATE '2026-09-30'` → 2 093 au lieu de 2 930 ; les 837 transactions du 30/09 perdues à cause de l'heure. Voir l'heure : `TO_CHAR(d, 'DD/MM/YYYY HH24:MI:SS')`. Pour compter : `COUNT(*)`, pas `SELECT *`.
- 02/10/2026 — Le nombre de lignes affiché par SQL Developer (ex. 200) = la taille du **paquet chargé**, pas le nombre de résultats. Pour savoir combien : `COUNT(*)`.
- 02/10/2026 — E3 : « en 2026 » traduit par sept.–oct. (4 lignes au lieu de 56). Reformuler la période en phrase avant de l'écrire. Intervalle semi-ouvert **toujours**, même si la colonne n'a pas d'heure. Vérifier les heures : `WHERE d <> TRUNC(d)`.
- 02/10/2026 — E3 validé (56). E4 validé : `WHERE` s'exécute avant `SELECT`, donc inutile de retester les filtres dans le `CASE` ; `CASE col WHEN ...` (forme courte) ; `ELSE 'Autre'` pour rendre visibles les cas imprévus ; un nom de colonne dit ce qu'elle contient.
- 02/10/2026 — E5 : `= NULL` ne renvoie rien, sans erreur. `COUNT(*)` sans `GROUP BY` → toujours 1 ligne (éventuellement 0) ; avec `GROUP BY` → aucune ligne s'il n'y a aucune catégorie. Une colonne du `GROUP BY` doit être affichée dans le `SELECT`.
- 02/10/2026 — E5 validé, **notion 1 terminée**. Ne jamais déduire le sens d'une colonne de son nom (`created_at` = entrée en relation, pas date de création de l'entreprise). Vérifier l'inverse avant d'affirmer « NULL = entreprise ».
- 03/10/2026 — E6 validé. `HAVING COUNT(*) > 0` est toujours vrai (un paquet n'existe que s'il contient au moins une ligne) : chaque ligne d'une requête doit avoir une raison d'être. « Par type » : demander si on compte aussi les opérations rejetées.
- 03/10/2026 — E7 validé. E8 : `'person'` / `'company'` en minuscules → 0 partout, sans erreur (valeurs stockées en MAJUSCULES). Réflexe : un comptage à 0 inattendu → `SELECT DISTINCT col FROM table` pour voir les vraies valeurs.
- 03/10/2026 — E8 validé : agrégation conditionnelle, plusieurs indicateurs sur une ligne par agence. Ne jamais inventer d'explication métier à un écart (ex. 20,5 % d'entreprises à San-Pédro) sans l'avoir vérifiée : ici, c'est le hasard du générateur.
- 03/10/2026 — E9 validé (13 clients sans compte). Erreur : `COUNT(DISTINCT account_id)` → 800, donc 500 − 800 = −300 : **un résultat impossible signale une erreur de logique**. Toujours se demander « qu'est-ce que je compte ? » (signatures vs personnes). `dual` = table d'une ligne pour un calcul isolé.
- 05/10/2026 — E10 (1er essai) : `GROUP BY amount, txn_type, channel, status, branch_id` → 1 702 boîtes au lieu de 8 ; la moyenne d'une boîte de montants identiques = le montant lui-même. Le `GROUP BY` ne contient que ce qui suit « **par** » dans la question. Filtre « au guichet » oublié. `amount` mélange euros et XOF → utiliser `amount_xof` pour additionner ou comparer (agence 5 : 116 436 vs 127 870).
- 05/10/2026 — E10 (2e essai) : deux `GROUP BY` dans une requête (interdit : chaque clause une seule fois, ordre fixe) ; colonne `branch` inexistante (`branch_id`). E10 validé. **WHERE ou HAVING ?** → « peut-on décider en regardant une seule ligne ? » Oui = `WHERE`, non (besoin de la boîte entière) = `HAVING`.
- 05/10/2026 — E11 (1er essai) : `SUM(FEE)` → `ORA-00904`. `'FEE'` est une **valeur** (ce qui est écrit dans la rubrique `txn_type`), pas une **colonne**. Entre apostrophes = valeur ; sans apostrophes = colonne ; en cas de doute : `DESC txn`. Étiquette calculée `EXTRACT(YEAR FROM business_date)` : à mettre dans le `SELECT` **et** le `GROUP BY` (réussi).
- 05/10/2026 — E11 (2e essai) : `SUM('FEE')` additionne un texte → `ORA-01722` ; `amount_xof` remis dans le `GROUP BY` (même piège qu'E10). **Habitude à perdre : ajouter des colonnes quand ça ne marche pas.** Méthode : dessiner d'abord le tableau voulu ; `SELECT` = ses colonnes, `GROUP BY` = ses étiquettes, le montant seulement dans `SUM()`. `ORA-00979` = presque toujours une colonne **en trop** dans le `SELECT`.
- 05/10/2026 — E11 (3e essai) : `amount_xof` toujours dans le `GROUP BY` → 12 lignes ; **`FETCH FIRST 3` ajouté pour obtenir les 3 lignes attendues** → 2026 affiché à 623 500 au lieu de 14 253 960 (moins de 5 % du vrai total). **Même erreur qu'E1** : un nombre de lignes inattendu est une **alarme**, pas un chiffre à corriger en coupant.
- 05/10/2026 — E11 validé, **exercices de la notion 2 terminés**. Effet stock : les frais suivent le nombre de comptes ouverts (2024 : 6,95 M ; 2025 : 14,1 M ; 2026 : 14,25 M en 9 mois). Comparer des périodes égales.


Ce fichier est le contrôle technique de votre base. Ce sont 10 requêtes à lancer juste après chaque chargement, pour vérifier que les données sont cohérentes avant de faire la moindre analyse dessus.