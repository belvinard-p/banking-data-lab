-- =====================================================================
-- CBS_LAB v2 — clés étrangères, contrôles et index
-- =====================================================================

-- ---------- Clés étrangères ----------
ALTER TABLE customer            ADD CONSTRAINT fk_customer_branch    FOREIGN KEY (branch_id)          REFERENCES branch(branch_id);
ALTER TABLE product             ADD CONSTRAINT fk_product_control_gl FOREIGN KEY (control_gl_id)      REFERENCES gl_account(gl_account_id);
ALTER TABLE product             ADD CONSTRAINT fk_product_income_gl  FOREIGN KEY (income_gl_id)       REFERENCES gl_account(gl_account_id);
ALTER TABLE app_user            ADD CONSTRAINT fk_app_user_branch    FOREIGN KEY (branch_id)          REFERENCES branch(branch_id);
ALTER TABLE account             ADD CONSTRAINT fk_account_product    FOREIGN KEY (product_id)         REFERENCES product(product_id);
ALTER TABLE account             ADD CONSTRAINT fk_account_branch     FOREIGN KEY (branch_id)          REFERENCES branch(branch_id);
ALTER TABLE account_status_hist ADD CONSTRAINT fk_ash_account        FOREIGN KEY (account_id)         REFERENCES account(account_id);
ALTER TABLE account_block       ADD CONSTRAINT fk_block_account      FOREIGN KEY (account_id)         REFERENCES account(account_id);
ALTER TABLE account_holder      ADD CONSTRAINT fk_holder_account     FOREIGN KEY (account_id)         REFERENCES account(account_id);
ALTER TABLE account_holder      ADD CONSTRAINT fk_holder_customer    FOREIGN KEY (customer_id)        REFERENCES customer(customer_id);
ALTER TABLE card                ADD CONSTRAINT fk_card_account       FOREIGN KEY (account_id)         REFERENCES account(account_id);
ALTER TABLE beneficiary         ADD CONSTRAINT fk_benef_customer     FOREIGN KEY (customer_id)        REFERENCES customer(customer_id);
ALTER TABLE fee_rule            ADD CONSTRAINT fk_fee_rule_product   FOREIGN KEY (product_id)         REFERENCES product(product_id);
ALTER TABLE loan                ADD CONSTRAINT fk_loan_account       FOREIGN KEY (account_id)         REFERENCES account(account_id);
ALTER TABLE loan_schedule       ADD CONSTRAINT fk_schedule_loan      FOREIGN KEY (loan_id)            REFERENCES loan(loan_id);
ALTER TABLE loan_payment        ADD CONSTRAINT fk_payment_schedule   FOREIGN KEY (loan_id, installment_no) REFERENCES loan_schedule(loan_id, installment_no);
ALTER TABLE txn                 ADD CONSTRAINT fk_txn_branch         FOREIGN KEY (branch_id)          REFERENCES branch(branch_id);
ALTER TABLE txn                 ADD CONSTRAINT fk_txn_reversal       FOREIGN KEY (reversal_of_txn_id) REFERENCES txn(txn_id);
ALTER TABLE txn                 ADD CONSTRAINT fk_txn_user           FOREIGN KEY (user_id)            REFERENCES app_user(user_id);
ALTER TABLE gl_entry            ADD CONSTRAINT fk_entry_txn          FOREIGN KEY (txn_id)             REFERENCES txn(txn_id);
ALTER TABLE gl_entry            ADD CONSTRAINT fk_entry_gl           FOREIGN KEY (gl_account_id)      REFERENCES gl_account(gl_account_id);
ALTER TABLE gl_entry            ADD CONSTRAINT fk_entry_account      FOREIGN KEY (account_id)         REFERENCES account(account_id);
ALTER TABLE daily_balance       ADD CONSTRAINT fk_balance_account    FOREIGN KEY (account_id)         REFERENCES account(account_id);

-- ---------- Contraintes de domaine ----------
ALTER TABLE account             ADD CONSTRAINT ck_account_status  CHECK (status IN ('ACTIVE','DORMANT','BLOCKED','CLOSED'));
ALTER TABLE account_status_hist ADD CONSTRAINT ck_ash_status      CHECK (status IN ('ACTIVE','DORMANT','BLOCKED','CLOSED'));
ALTER TABLE account_status_hist ADD CONSTRAINT ck_ash_period      CHECK (valid_to IS NULL OR valid_to > valid_from);
ALTER TABLE account_holder      ADD CONSTRAINT ck_holder_role     CHECK (role IN ('PRIMARY','JOINT','PROXY'));
ALTER TABLE product             ADD CONSTRAINT ck_product_family  CHECK (product_family IN ('CURRENT','SAVINGS','TERM','LOAN'));
ALTER TABLE gl_account          ADD CONSTRAINT ck_gl_kind         CHECK (gl_kind IN ('CONTROL','CASH','INCOME','EXPENSE','OTHER'));
ALTER TABLE gl_entry            ADD CONSTRAINT ck_entry_dc        CHECK (dc_flag IN ('D','C'));
ALTER TABLE gl_entry            ADD CONSTRAINT ck_entry_amount    CHECK (amount > 0);
ALTER TABLE txn                 ADD CONSTRAINT ck_txn_status      CHECK (status IN ('POSTED','REJECTED'));
ALTER TABLE business_calendar   ADD CONSTRAINT ck_cal_flag        CHECK (is_business_day IN ('Y','N'));

-- ---------- Clés uniques métier ----------
ALTER TABLE branch     ADD CONSTRAINT uk_branch_code     UNIQUE (branch_code);
ALTER TABLE gl_account ADD CONSTRAINT uk_gl_code         UNIQUE (gl_code);
ALTER TABLE product    ADD CONSTRAINT uk_product_code    UNIQUE (product_code);
ALTER TABLE account    ADD CONSTRAINT uk_account_number  UNIQUE (account_number);
ALTER TABLE txn        ADD CONSTRAINT uk_txn_ref         UNIQUE (txn_ref);

-- ---------- Index (colonnes de jointure et de filtre) ----------
CREATE INDEX ix_customer_branch     ON customer(branch_id);
CREATE INDEX ix_account_product     ON account(product_id);
CREATE INDEX ix_account_branch      ON account(branch_id);
CREATE INDEX ix_holder_customer     ON account_holder(customer_id);
CREATE INDEX ix_block_account       ON account_block(account_id);
CREATE INDEX ix_card_account        ON card(account_id);
CREATE INDEX ix_loan_account        ON loan(account_id);
CREATE INDEX ix_payment_loan        ON loan_payment(loan_id, installment_no);
CREATE INDEX ix_txn_business_date   ON txn(business_date);
CREATE INDEX ix_txn_reversal        ON txn(reversal_of_txn_id);
CREATE INDEX ix_entry_txn           ON gl_entry(txn_id);
CREATE INDEX ix_entry_account_date  ON gl_entry(account_id, entry_date);
CREATE INDEX ix_entry_gl_date       ON gl_entry(gl_account_id, entry_date);
