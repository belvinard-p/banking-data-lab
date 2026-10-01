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

-- S06 — TODO : comptes sans titulaire PRIMARY, ou avec plus d'un PRIMARY (attendu : 0)

-- S07 — TODO : le statut actuel (ACCOUNT.status) = dernier statut de ACCOUNT_STATUS_HIST
--        (celui dont valid_to IS NULL). Attendu : 0 écart.

-- S08 — TODO : périodes de statut qui se chevauchent pour un même compte (attendu : 0)
--        Indice : LEAD(valid_from) OVER (PARTITION BY account_id ORDER BY valid_from)

-- S09 — TODO : écritures sur un compte après sa date de clôture (attendu : 0 en v0)

-- S10 — TODO : pour chaque prêt, somme des principal_due = principal (attendu : 0 écart)
