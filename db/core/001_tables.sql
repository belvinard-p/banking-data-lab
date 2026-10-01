-- =====================================================================
-- CBS_LAB v2 — 20 tables (modèle pédagogique générique, données fictives)
-- Compatibilité : Oracle 19c+ (testé sur Oracle 23ai Free)
-- Les clés étrangères sont dans 002_constraints_indexes.sql
-- =====================================================================

-- ---------- Référentiels ----------
CREATE TABLE branch (
  branch_id     NUMBER(6)      CONSTRAINT pk_branch PRIMARY KEY,
  branch_code   VARCHAR2(10)   NOT NULL,
  name          VARCHAR2(60)   NOT NULL,
  city          VARCHAR2(60)   NOT NULL,
  region        VARCHAR2(60),
  open_date     DATE           NOT NULL
);

CREATE TABLE customer (
  customer_id   NUMBER(12)     CONSTRAINT pk_customer PRIMARY KEY,
  customer_type VARCHAR2(10)   NOT NULL,      -- PERSON|COMPANY
  full_name     VARCHAR2(120)  NOT NULL,
  birth_date    DATE,                          -- NULL pour une personne morale
  segment       VARCHAR2(20)   NOT NULL,      -- RETAIL|PREMIUM|SME|CORPORATE
  branch_id     NUMBER(6)      NOT NULL,
  kyc_status    VARCHAR2(10)   NOT NULL,      -- OK|PENDING|EXPIRED
  created_at    DATE           NOT NULL
);

CREATE TABLE gl_account (
  gl_account_id NUMBER(6)      CONSTRAINT pk_gl_account PRIMARY KEY,
  gl_code       VARCHAR2(10)   NOT NULL,
  label         VARCHAR2(80)   NOT NULL,
  gl_class      NUMBER(1)      NOT NULL,      -- 1..7, plan simplifié
  gl_kind       VARCHAR2(10)   NOT NULL       -- CONTROL|CASH|INCOME|EXPENSE|OTHER
);

CREATE TABLE product (
  product_id     NUMBER(6)     CONSTRAINT pk_product PRIMARY KEY,
  product_code   VARCHAR2(10)  NOT NULL,
  product_family VARCHAR2(10)  NOT NULL,      -- CURRENT|SAVINGS|TERM|LOAN
  name           VARCHAR2(80)  NOT NULL,
  currency       VARCHAR2(3)   NOT NULL,
  interest_rate  NUMBER(6,4)   DEFAULT 0 NOT NULL,   -- taux annuel, ex. 0.035
  monthly_fee    NUMBER(18,2)  DEFAULT 0 NOT NULL,
  control_gl_id  NUMBER(6)     NOT NULL,      -- compte collectif
  income_gl_id   NUMBER(6)                    -- compte de produits (frais/intérêts)
);

CREATE TABLE app_user (
  user_id       NUMBER(6)      CONSTRAINT pk_app_user PRIMARY KEY,
  login         VARCHAR2(30)   NOT NULL,
  role          VARCHAR2(20)   NOT NULL,      -- TELLER|SUPERVISOR|BACKOFFICE
  branch_id     NUMBER(6)      NOT NULL,
  active_flag   CHAR(1)        DEFAULT 'Y' NOT NULL
);

CREATE TABLE business_calendar (
  cal_date        DATE         CONSTRAINT pk_business_calendar PRIMARY KEY,
  is_business_day CHAR(1)      NOT NULL,      -- Y|N
  business_date   DATE         NOT NULL       -- journée comptable de rattachement
);

CREATE TABLE fx_rate (
  currency      VARCHAR2(3)    NOT NULL,
  rate_date     DATE           NOT NULL,
  rate_to_xof   NUMBER(18,6)   NOT NULL,
  CONSTRAINT pk_fx_rate PRIMARY KEY (currency, rate_date)
);

-- ---------- Comptes et contrats ----------
CREATE TABLE account (
  account_id      NUMBER(12)   CONSTRAINT pk_account PRIMARY KEY,
  account_number  VARCHAR2(20) NOT NULL,      -- texte : garder les zéros de tête
  product_id      NUMBER(6)    NOT NULL,
  branch_id       NUMBER(6)    NOT NULL,
  status          VARCHAR2(10) NOT NULL,      -- état ACTUEL : ACTIVE|DORMANT|BLOCKED|CLOSED
  open_date       DATE         NOT NULL,
  close_date      DATE,
  currency        VARCHAR2(3)  NOT NULL,
  overdraft_limit NUMBER(18,2) DEFAULT 0 NOT NULL
);

CREATE TABLE account_status_hist (
  account_id    NUMBER(12)     NOT NULL,
  status        VARCHAR2(10)   NOT NULL,
  valid_from    DATE           NOT NULL,
  valid_to      DATE,                          -- exclusif ; NULL = en cours
  CONSTRAINT pk_account_status_hist PRIMARY KEY (account_id, valid_from)
);

CREATE TABLE account_block (
  block_id      NUMBER(12)     CONSTRAINT pk_account_block PRIMARY KEY,
  account_id    NUMBER(12)     NOT NULL,
  amount        NUMBER(18,2)   NOT NULL,
  reason        VARCHAR2(30)   NOT NULL,      -- SEIZURE|GUARANTEE|OPPOSITION
  start_date    DATE           NOT NULL,
  end_date      DATE                           -- exclusif ; NULL = en cours
);

CREATE TABLE account_holder (
  account_id    NUMBER(12)     NOT NULL,
  customer_id   NUMBER(12)     NOT NULL,
  role          VARCHAR2(10)   NOT NULL,      -- PRIMARY|JOINT|PROXY
  CONSTRAINT pk_account_holder PRIMARY KEY (account_id, customer_id)
);

CREATE TABLE card (
  card_id       NUMBER(12)     CONSTRAINT pk_card PRIMARY KEY,
  account_id    NUMBER(12)     NOT NULL,
  card_type     VARCHAR2(10)   NOT NULL,      -- DEBIT|PREPAID
  masked_pan    VARCHAR2(19)   NOT NULL,
  status        VARCHAR2(10)   NOT NULL,      -- ACTIVE|BLOCKED|EXPIRED
  expiry_date   DATE           NOT NULL
);

CREATE TABLE beneficiary (
  beneficiary_id NUMBER(12)    CONSTRAINT pk_beneficiary PRIMARY KEY,
  customer_id    NUMBER(12)    NOT NULL,
  name           VARCHAR2(120) NOT NULL,
  bank_code      VARCHAR2(10)  NOT NULL,
  account_ref    VARCHAR2(30)  NOT NULL
);

CREATE TABLE fee_rule (
  fee_rule_id   NUMBER(6)      CONSTRAINT pk_fee_rule PRIMARY KEY,
  product_id    NUMBER(6)      NOT NULL,
  fee_type      VARCHAR2(20)   NOT NULL,      -- MAINTENANCE|CARD|SMS
  amount        NUMBER(18,2)   NOT NULL,
  frequency     VARCHAR2(10)   NOT NULL       -- MONTHLY|YEARLY
);

CREATE TABLE loan (
  loan_id       NUMBER(12)     CONSTRAINT pk_loan PRIMARY KEY,
  account_id    NUMBER(12)     NOT NULL,
  principal     NUMBER(18,2)   NOT NULL,
  rate          NUMBER(6,4)    NOT NULL,
  start_date    DATE           NOT NULL,
  maturity_date DATE           NOT NULL,
  term_months   NUMBER(4)      NOT NULL,
  status        VARCHAR2(10)   NOT NULL       -- ACTIVE|CLOSED (état actuel)
);

CREATE TABLE loan_schedule (
  loan_id        NUMBER(12)    NOT NULL,
  installment_no NUMBER(4)     NOT NULL,
  due_date       DATE          NOT NULL,
  principal_due  NUMBER(18,2)  NOT NULL,
  interest_due   NUMBER(18,2)  NOT NULL,
  CONSTRAINT pk_loan_schedule PRIMARY KEY (loan_id, installment_no)
);

CREATE TABLE loan_payment (
  payment_id     NUMBER(12)    CONSTRAINT pk_loan_payment PRIMARY KEY,
  loan_id        NUMBER(12)    NOT NULL,
  installment_no NUMBER(4)     NOT NULL,
  pay_date       DATE          NOT NULL,
  principal_paid NUMBER(18,2)  NOT NULL,
  interest_paid  NUMBER(18,2)  NOT NULL
);

-- ---------- Mouvements et états ----------
CREATE TABLE txn (
  txn_id             NUMBER(12)   CONSTRAINT pk_txn PRIMARY KEY,
  txn_ref            VARCHAR2(20) NOT NULL,
  txn_type           VARCHAR2(15) NOT NULL,   -- DEPOSIT|WITHDRAWAL|TRANSFER|CARD_PAYMENT|FEE|INTEREST|LOAN_DISB|LOAN_REPAY|REVERSAL
  channel            VARCHAR2(15) NOT NULL,   -- BRANCH|CARD|MOBILE_MONEY|TRANSFER|BATCH
  partner_code       VARCHAR2(10),            -- partenaire Mobile Money fictif, sinon NULL
  branch_id          NUMBER(6)    NOT NULL,   -- agence d'initiation
  txn_date           DATE         NOT NULL,   -- avec heure
  business_date      DATE         NOT NULL,   -- journée comptable
  value_date         DATE         NOT NULL,
  amount             NUMBER(18,2) NOT NULL,
  currency           VARCHAR2(3)  NOT NULL,
  amount_xof         NUMBER(18,2) NOT NULL,
  status             VARCHAR2(10) NOT NULL,   -- POSTED|REJECTED
  reversal_of_txn_id NUMBER(12),
  user_id            NUMBER(6)                -- NULL pour les opérations batch
);

CREATE TABLE gl_entry (
  entry_id      NUMBER(14)     CONSTRAINT pk_gl_entry PRIMARY KEY,
  txn_id        NUMBER(12)     NOT NULL,
  gl_account_id NUMBER(6)      NOT NULL,      -- toujours renseigné
  account_id    NUMBER(12),                   -- NULL si compte interne seul
  dc_flag       CHAR(1)        NOT NULL,      -- D|C
  amount        NUMBER(18,2)   NOT NULL,
  currency      VARCHAR2(3)    NOT NULL,
  amount_xof    NUMBER(18,2)   NOT NULL,
  entry_date    DATE           NOT NULL,      -- date comptable
  value_date    DATE           NOT NULL
);

CREATE TABLE daily_balance (
  account_id        NUMBER(12)   NOT NULL,
  balance_date      DATE         NOT NULL,    -- jours ouvrés uniquement, solde en FIN de journée
  ledger_balance    NUMBER(18,2) NOT NULL,
  available_balance NUMBER(18,2) NOT NULL,
  CONSTRAINT pk_daily_balance PRIMARY KEY (account_id, balance_date)
);
