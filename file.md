# Requêtes de sanité — Guide complet

## 1. Que veut dire « contrôle technique » ?

C'est une image empruntée à la voiture. Avant d'autoriser une voiture à rouler, le contrôle technique vérifie une liste de points précis : freins, pneus, phares… Chaque point est soit OK, soit KO. Un seul KO, et on ne prend pas la route.

Pour votre base, c'est pareil. Avant de faire des analyses, vous vérifiez une liste de règles qui doivent toujours être vraies dans une banque. Les informaticiens appellent ces règles des **invariants**. Par exemple : « une transaction est toujours équilibrée », ou « un compte a toujours un titulaire principal ».

| Contrôle technique auto | Requêtes de sanité |
|---|---|
| Un point de contrôle (les freins) | Une requête (S02 : débits = crédits) |
| OK / KO | 0 ligne = OK / des lignes = KO |
| Le rapport indique quelle pièce est défectueuse | Les lignes renvoyées indiquent quelle transaction ou quel compte pose problème |
| On le refait régulièrement | On relance le fichier après chaque chargement |

---

## 2. La méthode pour écrire n'importe quelle requête de contrôle

C'est la clé pour écrire les requêtes S04 à S10. On se pose 4 questions :

1. **Quelle règle doit toujours être vraie ?** Par exemple : « débits = crédits ».
2. **À quoi ressemble une violation ?** Par exemple : « une transaction où débits ≠ crédits ».
3. **Dans quelles tables et colonnes se trouve l'information ?** Par exemple : `GL_ENTRY (txn_id, dc_flag, amount_xof)`.
4. **Écrire la requête qui renvoie les violations.** Résultat attendu : 0 ligne.

> On ne cherche donc jamais à prouver que tout va bien. On cherche les problèmes, et si on n'en trouve aucun, c'est bon.

---

## 3. Les 3 requêtes déjà écrites, décortiquées

J'ai lancées sur votre base : S01 affiche les 20 tables, S02 et S03 renvoient 0 ligne. Votre base est saine sur ces points.

### S01 — Le chargement est-il complet ?

```sql
SELECT table_name, num_rows
FROM   user_tables          -- vue du dictionnaire Oracle : « mes tables »
ORDER  BY table_name;
```

- **Règle :** chaque table contient le volume attendu, et aucune n'est vide.
- `user_tables` n'est pas une de vos tables. C'est le dictionnaire de données d'Oracle, qui décrit vos tables.
- `num_rows` provient des statistiques calculées à la fin du chargement par `DBMS_STATS` dans le générateur. C'est un comptage mémorisé : si vous ajoutez des lignes ensuite, il ne bouge pas.
- C'est la seule requête sans « attendu : 0 ligne ». Elle se lit en comparant avec le README (800 comptes, 62 424 transactions…).

### S02 — Chaque transaction est-elle équilibrée ? (la partie double)

```sql
SELECT txn_id,
       SUM(CASE dc_flag WHEN 'D' THEN amount_xof ELSE 0 END) AS debits,
       SUM(CASE dc_flag WHEN 'C' THEN amount_xof ELSE 0 END) AS credits
FROM   gl_entry
GROUP  BY txn_id
HAVING SUM(CASE dc_flag WHEN 'D' THEN amount_xof ELSE -amount_xof END) <> 0;
```

| Morceau | Rôle |
|---|---|
| `FROM gl_entry` | Les écritures contiennent les débits et les crédits |
| `GROUP BY txn_id` | Une ligne par transaction, qui regroupe ses 2, 3 ou 4 écritures |
| `CASE dc_flag WHEN 'D' THEN amount_xof ELSE 0 END` | Garde le montant si c'est un débit, sinon 0. Le `SUM` donne le total des débits |
| `HAVING ... ELSE -amount_xof ...` | Débit compté en +, crédit en −. Si la transaction est équilibrée, la somme vaut 0 |
| `<> 0` | On ne garde que les transactions déséquilibrées : les violations |
| `amount_xof` (et non `amount`) | On compare tout dans une seule devise |

> **À retenir :** `WHERE` filtre des lignes avant le regroupement, `HAVING` filtre des groupes après. « Débits ≠ crédits » est une propriété du groupe (la transaction), d'où `HAVING`.

### S03 — Les soldes affichés sont-ils justes ? (un recoupement)

```sql
WITH last_snap AS (                                   -- ① dernier solde photographié
  SELECT account_id, ledger_balance
  FROM  (SELECT d.*, ROW_NUMBER() OVER (PARTITION BY account_id
                                        ORDER BY balance_date DESC) AS rn
         FROM   daily_balance d)
  WHERE  rn = 1
), from_entries AS (                                  -- ② solde recalculé depuis les écritures
  SELECT account_id, SUM(CASE dc_flag WHEN 'C' THEN amount ELSE -amount END) AS balance
  FROM   gl_entry
  WHERE  account_id IS NOT NULL
  GROUP  BY account_id
)
SELECT s.account_id, s.ledger_balance, e.balance      -- ③ on compare
FROM   last_snap s
LEFT   JOIN from_entries e ON e.account_id = s.account_id
WHERE  s.ledger_balance <> NVL(e.balance, 0);
```

- **Règle :** le solde photographié dans `DAILY_BALANCE` doit égaler la somme des écritures. On obtient le même chiffre par deux chemins indépendants.
- ① `ROW_NUMBER() ... ORDER BY balance_date DESC` numérote les photos de chaque compte de la plus récente (1) à la plus ancienne. `rn = 1` garde la dernière.
- ② On recalcule le solde : crédit +, débit −. `account_id IS NOT NULL` exclut les écritures internes de la banque (caisse, commissions).
- ③ Le `LEFT JOIN` garde aussi les comptes sans aucune écriture, et `NVL(..., 0)` traite leur solde comme 0. Avec un `JOIN` simple, ils disparaîtraient sans bruit : c'est le piège classique.
- `WITH` (une CTE) découpe la requête en étapes nommées, que vous pouvez tester séparément.

---

## 4. Les 7 requêtes à écrire : règle, raison et piste

Chaque contrôle appartient à une famille. Une fois la famille reconnue, la technique SQL en découle.

| Famille | Question type | Technique SQL |
|---|---|---|
| Absence | « A sans B » | `NOT EXISTS` |
| Orphelin | « B qui pointe vers un A inexistant » | `NOT EXISTS` ou `LEFT JOIN … IS NULL` |
| Cardinalité | « exactement 1 » | `GROUP BY` + `COUNT` + `HAVING` |
| Cohérence de deux sources | « A dit X, B dit Y » | jointure + comparaison `<>` |
| Période | « les dates se chevauchent » | `LEAD` / `LAG` |
| Agrégat vs référence | « la somme des détails = le total » | pré-agréger, puis comparer |

### S04 — Transactions POSTED sans écriture · famille : absence

- **Règle :** une transaction validée a forcément bougé de l'argent, donc elle a au moins une écriture.
- **Pourquoi :** une opération « validée » qui n'apparaît pas en comptabilité, c'est de l'argent fantôme.
- **Tables :** `TXN (status)`, `GL_ENTRY (txn_id)`.
- **Piste :** partez de `TXN`, filtrez `POSTED`, et gardez celles pour lesquelles il n'existe pas d'écriture avec le même `txn_id`.
- **Bonus :** faites le contrôle inverse. Une transaction `REJECTED` ne doit avoir aucune écriture : dans le générateur, `post()` s'arrête avant de les créer.

### S05 — Écritures orphelines · famille : orphelin

- **Règle :** chaque écriture appartient à une transaction qui existe.
- **Pourquoi :** une écriture sans transaction est un mouvement d'argent dont on ne connaît pas l'origine. C'est un point d'audit grave.
- **Tables :** `GL_ENTRY (txn_id)` → `TXN (txn_id)`.
- **Piste :** c'est S04 dans l'autre sens. On part de `GL_ENTRY`.
- **À savoir :** ici, la clé étrangère `fk_entry_txn` empêche déjà ce cas, donc le résultat sera forcément 0. Le contrôle servira vraiment sur `CBS_BLACKBOX` et en production, où les clés étrangères n'existent souvent pas.

### S06 — Exactement un titulaire PRIMARY par compte · famille : cardinalité

- **Règle :** chaque compte a un et un seul titulaire principal.
- **Pourquoi :** 0 titulaire, c'est un compte sans propriétaire. 2 titulaires, c'est une ambiguïté, et chaque requête « compte → client » doublera les montants (le fan-out).
- **Tables :** `ACCOUNT`, `ACCOUNT_HOLDER (account_id, role)`.
- **Piste :** regroupez par compte et comptez seulement les `PRIMARY` avec `COUNT(CASE WHEN … THEN 1 END)`. Gardez les groupes où ce compte est différent de 1.
- **Piège :** si vous partez uniquement de `ACCOUNT_HOLDER`, un compte sans aucune ligne de titulaire n'apparaîtra jamais. Il faut donc partir de `ACCOUNT`.

### S07 — Statut actuel = dernier statut de l'historique · famille : cohérence de deux sources

- **Règle :** `ACCOUNT.status` doit être identique au statut de la période en cours dans `ACCOUNT_STATUS_HIST` (celle où `valid_to IS NULL`).
- **Pourquoi :** si deux tables racontent deux histoires différentes, lequel des deux chiffres livrer ? Il faut le savoir avant.
- **Tables :** `ACCOUNT (status)`, `ACCOUNT_STATUS_HIST (status, valid_to)`.
- **Piste :** joignez le compte à sa période en cours, puis gardez les lignes où les deux statuts diffèrent.
- **Piège :** un compte qui n'a aucune période en cours est aussi une anomalie. Avec un `JOIN` simple, il disparaît.

### S08 — Périodes de statut qui se chevauchent · famille : période

- **Règle :** pour un même compte, une période doit finir avant ou au moment où la suivante commence.
- **Pourquoi :** si un compte est « ACTIVE du 01/01 au 31/12 » et « BLOCKED à partir du 01/06 », il sera compté deux fois au 31/08.

**Exemple :**

```
ACTIVE   valid_from 02/01/2024  valid_to 14/03/2026
BLOCKED  valid_from 14/03/2026  valid_to NULL        ← OK : la 1re finit quand la 2e commence
BLOCKED  valid_from 01/03/2026  ...                  ← KO : commence avant la fin de la 1re
```

- **Piste :** `LEAD(valid_from) OVER (PARTITION BY account_id ORDER BY valid_from)` place, sur chaque ligne, la date de début de la période suivante. Faites-le dans une CTE, puis gardez les lignes où `valid_to` dépasse ce début suivant.
- **Piège :** une période avec `valid_to IS NULL` (« en cours ») qui n'est pas la dernière est aussi un chevauchement, puisqu'elle ne finit jamais.

### S09 — Écritures après la clôture du compte · famille : cohérence temporelle

- **Règle :** un compte clôturé ne bouge plus après sa date de clôture.
- **Pourquoi :** une écriture sur un compte fermé est soit une erreur, soit une fraude.
- **Tables :** `GL_ENTRY (account_id, entry_date)`, `ACCOUNT (close_date)`.
- **Piste :** une jointure, puis une comparaison de dates sur les comptes qui ont une `close_date`.
- **Question à vous poser :** faut-il utiliser `>` ou `>=` ? Indice : le générateur verse le solde restant au client le jour même de la clôture (fonction `planned`, cas `"close"`).

### S10 — L'échéancier rembourse exactement le capital prêté · famille : agrégat vs référence

- **Règle :** pour chaque prêt, la somme des `principal_due` de l'échéancier = `LOAN.principal`.
- **Pourquoi :** si l'échéancier ne rembourse pas exactement ce qui a été prêté, tous vos calculs de capital restant dû et de PAR seront faux.
- **Tables :** `LOAN (principal)`, `LOAN_SCHEDULE (loan_id, principal_due)`.
- **Piste :** pré-agrégez l'échéancier par prêt dans une CTE, puis joignez à `LOAN` et comparez.
- **Piège :** joindre d'abord et sommer ensuite fonctionne ici, mais prenez le réflexe de pré-agréger. Dès qu'une troisième table s'ajoute (les paiements), joindre avant de sommer multiplie les montants.

---

## 5. Ordre conseillé

**S04 → S05** (même technique, dans les deux sens) **→ S09 → S10 → S06 → S07 → S08** (la plus difficile).

Pour chacune : écrivez-la, lancez-la avec `Ctrl+Entrée` et vérifiez qu'elle renvoie 0 ligne. Puis cassez volontairement une donnée pour prouver que le contrôle détecte bien le problème :

```sql
UPDATE account SET status = 'CLOSED' WHERE account_id = 1;   -- S07 doit maintenant renvoyer 1 ligne
ROLLBACK;
```


https://docs.oracle.com/en/database/oracle/oracle-database/23/sqlrf/

https://livesql.oracle.com/

