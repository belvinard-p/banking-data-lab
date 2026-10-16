-- =====================================================================
-- Niveau 0 — 10 requêtes de sanité sur CBS_LAB (jeu small, seed 42)
-- Lancer : python tools/db.py run sql/00_sanity/sanity_checks.sql
-- Les 3 premières sont des exemples ; écrivez les 7 suivantes vous-même.
-- =====================================================================

-- S01 — Nombre de lignes par table (statistiques collectées après chargement)
SELECT table_name, num_rows
FROM   user_tables
ORDER  BY table_name;

-- S02 — Débits = crédits pour chaque transaction (attendu : 0 ligne)
SELECT txn_id,
       SUM(CASE dc_flag WHEN 'D' THEN amount_xof ELSE 0 END) AS debits,
       SUM(CASE dc_flag WHEN 'C' THEN amount_xof ELSE 0 END) AS credits
FROM   gl_entry
GROUP  BY txn_id
HAVING SUM(CASE dc_flag WHEN 'D' THEN amount_xof ELSE -amount_xof END) <> 0;

-- S03 — Le dernier solde photographié = somme des écritures (attendu : 0 ligne)
WITH last_snap AS (
  SELECT account_id, ledger_balance
  FROM  (SELECT d.*, ROW_NUMBER() OVER (PARTITION BY account_id ORDER BY balance_date DESC) AS rn
         FROM   daily_balance d)
  WHERE  rn = 1
), from_entries AS (
  SELECT account_id, SUM(CASE dc_flag WHEN 'C' THEN amount ELSE -amount END) AS balance
  FROM   gl_entry
  WHERE  account_id IS NOT NULL
  GROUP  BY account_id
)
SELECT s.account_id, s.ledger_balance, e.balance
FROM   last_snap s
LEFT   JOIN from_entries e ON e.account_id = s.account_id
WHERE  s.ledger_balance <> NVL(e.balance, 0);

-- S04 — TODO : transactions POSTED sans aucune écriture (attendu : 0)
--        Indice : NOT EXISTS. Et les REJECTED, ont-elles des écritures ?

-- S05 — TODO : écritures dont la transaction n'existe pas (orphelins, attendu : 0)

-- S06a — Chaque compte a exactement un titulaire PRIMARY (attendu : 0 ligne)
--         Testé : UPDATE du compte 1 en JOINT → renvoie « compte 1, nb_primary = 0 » ; ROLLBACK.
SELECT   account_id,
         COUNT(CASE WHEN role = 'PRIMARY' THEN 1 END) AS nb_primary
FROM     account_holder
GROUP BY account_id
HAVING   COUNT(CASE WHEN role = 'PRIMARY' THEN 1 END) <> 1;

-- S06b — Comptes sans aucun titulaire, invisibles pour S06a (attendu : 1 ligne avec 0)
--         À réécrire en notion 4 avec NOT EXISTS pour lister directement les comptes fautifs.
SELECT (SELECT COUNT(*)                   FROM account)
     - (SELECT COUNT(DISTINCT account_id) FROM account_holder) AS nb_accounts_without_holder
FROM   dual;

-- S07 — Le statut actuel (ACCOUNT.status) = le statut de la période en cours de
--        ACCOUNT_STATUS_HIST (valid_to IS NULL), et chaque compte a une période en cours (attendu : 0 ligne)
--        Testé : UPDATE du compte 1 en CLOSED → renvoie « compte 1, CLOSED / ACTIVE » ; ROLLBACK.
SELECT a.account_id,
       a.status AS statut_account,
       h.status AS statut_historique
FROM   account a
LEFT   JOIN account_status_hist h ON h.account_id = a.account_id
                                 AND h.valid_to   IS NULL
WHERE  (a.status <> h.status OR h.account_id IS NULL);

-- S08 — TODO : périodes de statut qui se chevauchent pour un même compte (attendu : 0)
--        Indice : LEAD(valid_from) OVER (PARTITION BY account_id ORDER BY valid_from)

-- S09 — Aucune écriture après la date de clôture d'un compte (attendu : 0 ligne en v0)
--        « > » et non « >= » : le jour même de la clôture, l'écriture qui solde le compte est normale (140 cas).
--        Testé : close_date du compte 5 avancée de 30 jours → renvoie 4 écritures ; ROLLBACK.
SELECT e.entry_id, e.account_id, e.entry_date, a.close_date
FROM   gl_entry e
JOIN   account a ON a.account_id = e.account_id
WHERE  a.close_date IS NOT NULL
AND    e.entry_date > a.close_date;

-- S10 — TODO : pour chaque prêt, somme des principal_due = principal (attendu : 0 écart)
