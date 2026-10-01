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

> Règle d'or : on ne livre **jamais** un chiffre sans l'avoir recoupé autrement.

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
