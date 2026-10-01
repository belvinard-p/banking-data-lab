"""Générateur v0 de Lagune Bank (banque fictive, modèle pédagogique générique).

Recrée le schéma CBS_LAB puis charge un jeu de données cohérent (partie double,
soldes = somme des écritures). Données PROPRES : les anomalies arrivent en v1.

Usage :
    python data-generator/generate.py --size small --seed 42
"""
import argparse
import calendar
import math
import random
import sys
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import db  # noqa: E402

START = date(2024, 1, 1)
END = date(2026, 9, 30)
SIZES = {"small": (500, 800), "medium": (5_000, 8_000), "large": (30_000, 50_000)}

# ---------------------------------------------------------------------------
# Référentiels fixes
# ---------------------------------------------------------------------------
BRANCHES = [  # id, code, nom, ville, région
    (1, "001", "Plateau", "Abidjan", "Lagunes"),
    (2, "002", "Cocody", "Abidjan", "Lagunes"),
    (3, "003", "Yopougon", "Abidjan", "Lagunes"),
    (4, "004", "Marcory", "Abidjan", "Lagunes"),
    (5, "005", "Treichville", "Abidjan", "Lagunes"),
    (6, "006", "Bouaké Centre", "Bouaké", "Gbêkê"),
    (7, "007", "Yamoussoukro", "Yamoussoukro", "Bélier"),
    (8, "008", "San-Pédro Port", "San-Pédro", "San-Pédro"),
]
GL = {  # clé: (id, code, libellé, classe, nature)
    "CASH":      (1, "571100", "Caisse agences", 5, "CASH"),
    "CTL_CUR":   (2, "251100", "Comptes courants clientèle", 2, "CONTROL"),
    "CTL_SAV":   (3, "253100", "Comptes d'épargne clientèle", 2, "CONTROL"),
    "CTL_TERM":  (4, "254100", "Dépôts à terme clientèle", 2, "CONTROL"),
    "CTL_LOAN":  (5, "201100", "Crédits à la clientèle", 2, "CONTROL"),
    "INC_FEE":   (6, "706100", "Commissions sur tenue de compte", 7, "INCOME"),
    "INC_INT":   (7, "702100", "Intérêts perçus sur crédits", 7, "INCOME"),
    "EXP_INT":   (8, "602100", "Intérêts versés sur dépôts", 6, "EXPENSE"),
    "CLR_MM":    (9, "471100", "Compensation Mobile Money", 4, "OTHER"),
    "CLR_CARD":  (10, "471200", "Compensation monétique", 4, "OTHER"),
    "CLR_BANK":  (11, "471300", "Compensation virements interbancaires", 4, "OTHER"),
}
G = {k: v[0] for k, v in GL.items()}
PRODUCTS = [  # id, code, famille, nom, devise, taux, frais mensuels, gl collectif, gl produits
    (1, "CC_PART", "CURRENT", "Compte courant particulier", "XOF", 0, 2500, G["CTL_CUR"], G["INC_FEE"]),
    (2, "CC_PRO", "CURRENT", "Compte courant professionnel", "XOF", 0, 7500, G["CTL_CUR"], G["INC_FEE"]),
    (3, "CC_EUR", "CURRENT", "Compte courant en euros", "EUR", 0, 5, G["CTL_CUR"], G["INC_FEE"]),
    (4, "EP_35", "SAVINGS", "Épargne 3,5 %", "XOF", 0.035, 500, G["CTL_SAV"], G["EXP_INT"]),
    (5, "DAT_12", "TERM", "Dépôt à terme 12 mois", "XOF", 0.05, 0, G["CTL_TERM"], G["EXP_INT"]),
    (6, "PR_CONSO", "LOAN", "Prêt consommation", "XOF", 0.12, 0, G["CTL_LOAN"], G["INC_INT"]),
    (7, "PR_AUTO", "LOAN", "Prêt automobile", "XOF", 0.10, 0, G["CTL_LOAN"], G["INC_INT"]),
]
PROD = {p[0]: p for p in PRODUCTS}
HOLIDAYS_MMDD = {(1, 1), (5, 1), (8, 7), (8, 15), (11, 1), (11, 15), (12, 25)}
MM_PARTNERS = ["MM01", "MM02", "MM03"]  # codes fictifs
FIRST = ["Aminata", "Koffi", "Awa", "Yao", "Mariam", "Kouassi", "Fatou", "Adama", "Aya", "Ibrahim",
         "Akissi", "Seydou", "Affoué", "Moussa", "Adjoua", "Bakary", "Rokia", "Serge", "Salimata", "Hervé",
         "Nadège", "Drissa", "Christelle", "Lassina", "Ange", "Kadiatou", "Jean-Marc", "Bintou"]
LAST = ["Koné", "Kouamé", "Traoré", "Yao", "Ouattara", "Bamba", "Coulibaly", "Diabaté", "N'Guessan",
        "Kouadio", "Touré", "Konan", "Diallo", "Aka", "Cissé", "Gbagbo", "Soro", "Fofana", "Brou",
        "Kra", "Sangaré", "Tano", "Dosso", "Assi"]
COMPANY = ["Ets {} & Fils", "SARL {} Négoce", "{} Transport", "Boulangerie {}", "{} BTP",
           "Pharmacie {}", "{} Agro-Export", "Quincaillerie {}"]


# ---------------------------------------------------------------------------
# Structures
# ---------------------------------------------------------------------------
@dataclass
class Account:
    id: int
    number: str
    product_id: int
    branch_id: int
    customer_id: int
    open_date: date
    currency: str
    overdraft: float = 0
    close_date: date | None = None
    activity_end: date = END       # au-delà, plus aucune opération client
    hist: list = field(default_factory=list)   # [status, valid_from, valid_to]
    salary: float = 0
    has_card: bool = False
    ledger: float = 0

    @property
    def family(self) -> str:
        return PROD[self.product_id][2]

    def status_at(self, d: date) -> str | None:
        for s, f, t in self.hist:
            if f <= d and (t is None or d < t):
                return s
        return None


class Lab:
    def __init__(self, seed: int, n_customers: int, n_accounts: int):
        self.r = random.Random(seed)
        self.nc, self.na = n_customers, n_accounts
        self.rows = defaultdict(list)
        self.txn_seq = 0
        self.entry_seq = 0
        self.blocks = defaultdict(list)    # account_id -> [(amount, start, end)]
        self.events = defaultdict(list)    # date -> [callable] (opérations planifiées)

    # ----- calendrier et taux -------------------------------------------
    def build_calendar(self):
        self.cal = {}
        d = END + timedelta(days=15)
        nxt = None
        while d >= START:
            is_bd = d.weekday() < 5 and (d.month, d.day) not in HOLIDAYS_MMDD
            if is_bd:
                nxt = d
            self.cal[d] = (is_bd, nxt)
            d -= timedelta(days=1)
        for d in sorted(self.cal):
            if d <= END:
                self.rows["business_calendar"].append((d, "Y" if self.cal[d][0] else "N", self.cal[d][1]))
        usd = 605.0
        self.fx = {}
        for d in sorted(self.cal):
            if d > END or not self.cal[d][0]:
                continue
            usd = max(540.0, min(680.0, usd * (1 + self.r.gauss(0, 0.004))))
            self.fx[d] = {"EUR": 655.957, "USD": round(usd, 4), "XOF": 1.0}
            self.rows["fx_rate"].append(("EUR", d, 655.957))
            self.rows["fx_rate"].append(("USD", d, round(usd, 4)))

    def bd(self, d: date) -> date:
        return self.cal[d][1]

    def is_bd(self, d: date) -> bool:
        return self.cal[d][0]

    def rand_date(self, lo: date, hi: date) -> date:
        return lo + timedelta(days=self.r.randint(0, max(0, (hi - lo).days)))

    # ----- référentiels -------------------------------------------------
    def build_reference(self):
        self.rows["branch"] = [(b[0], b[1], b[2], b[3], b[4], date(2005 + b[0], 3, 1)) for b in BRANCHES]
        self.rows["gl_account"] = list(GL.values())
        self.rows["product"] = [(p[0], p[1], p[2], p[3], p[4], p[5], p[6], p[7], p[8]) for p in PRODUCTS]
        fid = 0
        for p in PRODUCTS:
            if p[6]:
                fid += 1
                self.rows["fee_rule"].append((fid, p[0], "MAINTENANCE", p[6], "MONTHLY"))
            if p[2] == "CURRENT":
                fid += 1
                self.rows["fee_rule"].append((fid, p[0], "CARD", 12000 if p[4] == "XOF" else 18, "YEARLY"))
        uid = 0
        self.tellers = defaultdict(list)
        for b in BRANCHES:
            for role, n in (("SUPERVISOR", 1), ("TELLER", 2)):
                for _ in range(n):
                    uid += 1
                    self.rows["app_user"].append((uid, f"u{b[1]}{uid:03d}", role, b[0], "Y"))
                    self.tellers[b[0]].append(uid)
        self.backoffice = []
        for _ in range(2):
            uid += 1
            self.rows["app_user"].append((uid, f"bo{uid:03d}", "BACKOFFICE", 1, "Y"))
            self.backoffice.append(uid)
        uid += 1
        self.rows["app_user"].append((uid, f"u001{uid:03d}", "TELLER", 1, "N"))  # agent parti

    def build_customers(self):
        self.customers = []
        for cid in range(1, self.nc + 1):
            is_co = self.r.random() < 0.12
            branch = self.r.choices([b[0] for b in BRANCHES], weights=[18, 16, 14, 12, 10, 12, 10, 8])[0]
            if is_co:
                name = self.r.choice(COMPANY).format(self.r.choice(LAST))
                birth, seg = None, self.r.choice(["SME", "SME", "CORPORATE"])
            else:
                name = f"{self.r.choice(FIRST)} {self.r.choice(LAST)}"
                birth = self.rand_date(date(1950, 1, 1), date(2005, 12, 31))
                seg = "PREMIUM" if self.r.random() < 0.12 else "RETAIL"
            created = self.rand_date(date(2015, 1, 1), END - timedelta(days=60))
            kyc = self.r.choices(["OK", "PENDING", "EXPIRED"], weights=[88, 4, 8])[0]
            self.customers.append([cid, "COMPANY" if is_co else "PERSON", name, birth, seg, branch, kyc, created])
            if self.r.random() < 0.3:
                for _ in range(self.r.randint(1, 3)):
                    bid = len(self.rows["beneficiary"]) + 1
                    self.rows["beneficiary"].append(
                        (bid, cid, f"{self.r.choice(FIRST)} {self.r.choice(LAST)}",
                         f"CI{self.r.randint(100, 199)}", f"{self.r.randint(10**9, 10**10 - 1)}"))

    # ----- comptes ------------------------------------------------------
    def pick_product(self, cust, first: bool) -> int:
        if cust[1] == "COMPANY":
            return self.r.choices([2, 3, 5, 6], weights=[80, 6, 8, 6])[0]
        if first:
            return self.r.choices([1, 3, 4], weights=[88, 2, 10])[0]
        return self.r.choices([1, 4, 5, 6, 7], weights=[10, 40, 10, 28, 12])[0]

    def build_accounts(self):
        r = self.r
        holders_first = [c for c in self.customers if r.random() > 0.03]   # ~3 % sans compte
        owners = [(c, True) for c in holders_first]
        while len(owners) < self.na:
            owners.append((r.choice(holders_first), False))
        owners = owners[: self.na]
        span = (END - timedelta(days=30) - START).days
        self.accounts: list[Account] = []
        seq_by_branch = defaultdict(int)
        for aid, (cust, first) in enumerate(owners, start=1):
            pid = self.pick_product(cust, first)
            od = self.bd(START + timedelta(days=int(r.random() ** 1.4 * span)))
            cust[7] = min(cust[7], od)                      # le client existe avant son compte
            seq_by_branch[cust[5]] += 1
            num = f"{BRANCHES[cust[5] - 1][1]}-{seq_by_branch[cust[5]] * 7 + 40000:06d}"
            a = Account(aid, num, pid, cust[5], cust[0], od, PROD[pid][4])
            if pid == 2 and r.random() < 0.5:
                a.overdraft = r.choice([500_000, 1_000_000, 2_000_000])
            elif pid == 1 and r.random() < 0.2:
                a.overdraft = 100_000
            if pid in (1, 3) and cust[1] == "PERSON" and r.random() < 0.6:
                a.salary = round(r.lognormvariate(12.6, 0.5), -3) / (655.957 if pid == 3 else 1)
            a.has_card = a.family == "CURRENT" and r.random() < 0.6
            self.accounts.append(a)
        self.by_id = {a.id: a for a in self.accounts}
        for a in self.accounts:
            self.plan_lifecycle(a)
        self.holders()

    def plan_lifecycle(self, a: Account):
        r = self.r
        a.hist = [["ACTIVE", a.open_date, None]]
        if a.family in ("CURRENT", "SAVINGS"):
            self.events[a.open_date].append(("open_deposit", a))
        if a.family == "TERM":
            mat = self.bd(min(a.open_date + timedelta(days=365), END + timedelta(days=10)))
            self.events[a.open_date].append(("term_open", a))
            if mat <= END:
                self.events[mat].append(("term_mature", a))
                a.close_date = mat
                a.hist = [["ACTIVE", a.open_date, mat], ["CLOSED", mat, None]]
            return
        if a.family == "LOAN":
            self.plan_loan(a)
            return
        x = r.random()
        if x < 0.08 and (END - a.open_date).days > 120:                                  # clôture
            cd = self.bd(self.rand_date(a.open_date + timedelta(days=90), END - timedelta(days=5)))
            if cd <= END:
                a.close_date = cd
                a.hist = [["ACTIVE", a.open_date, cd], ["CLOSED", cd, None]]
                self.events[cd].append(("close", a))
        elif x < 0.20 and (END - a.open_date).days > 460:                                # inactivité
            last = self.rand_date(a.open_date + timedelta(days=60), END - timedelta(days=395))
            a.activity_end = last
            if r.random() < 0.75:                                                        # passé dormant
                dd = last + timedelta(days=365)
                a.hist = [["ACTIVE", a.open_date, dd], ["DORMANT", dd, None]]
        elif x < 0.24 and (END - a.open_date).days > 60:                                 # blocage
            bf = self.rand_date(a.open_date + timedelta(days=30), END - timedelta(days=10))
            bt = bf + timedelta(days=r.randint(30, 200)) if r.random() < 0.5 else None
            if bt and bt > END:
                bt = None
            a.hist = [["ACTIVE", a.open_date, bf], ["BLOCKED", bf, bt]] + ([["ACTIVE", bt, None]] if bt else [])
        if a.close_date is None and r.random() < 0.05:                                   # blocage de montant
            s = self.rand_date(a.open_date + timedelta(days=10), END - timedelta(days=5))
            e = s + timedelta(days=r.randint(30, 180)) if r.random() < 0.6 else None
            amt = r.choice([50_000, 150_000, 300_000, 500_000]) / (655.957 if a.currency == "EUR" else 1)
            self.blocks[a.id].append((round(amt, 2), s, e))

    def holders(self):
        r = self.r
        same_branch = defaultdict(list)
        for c in self.customers:
            same_branch[c[5]].append(c[0])
        for a in self.accounts:
            self.rows["account_holder"].append((a.id, a.customer_id, "PRIMARY"))
            if a.family == "CURRENT" and r.random() < 0.10:
                other = r.choice(same_branch[a.branch_id])
                if other != a.customer_id:
                    self.rows["account_holder"].append((a.id, other, "JOINT" if r.random() < 0.8 else "PROXY"))

    # ----- crédits ------------------------------------------------------
    def plan_loan(self, a: Account):
        r = self.r
        p = PROD[a.product_id]
        principal = round(r.uniform(500_000, 3_000_000 if p[1] == "PR_CONSO" else 15_000_000), -4)
        n = r.choice([12, 24, 36]) if p[1] == "PR_CONSO" else r.choice([36, 48, 60])
        rate = p[5]
        mr = rate / 12
        pmt = principal * mr / (1 - (1 + mr) ** -n)
        bal, sched = principal, []
        day = min(a.open_date.day, 28)
        for k in range(1, n + 1):
            y, m = divmod(a.open_date.month - 1 + k, 12)
            due = date(a.open_date.year + y, m + 1, day)
            interest = round(bal * mr)
            princ = bal if k == n else round(pmt - interest)
            bal -= princ
            sched.append((k, due, princ, interest))
        loan_id = len(self.rows["loan"]) + 1
        a.loan_id = loan_id
        profile = r.choices(["good", "late", "default"], weights=[75, 15, 10])[0]
        stop = r.randint(3, max(3, n - 1)) if profile == "default" else n + 1
        paid_all, last_pay = True, None
        for k, due, princ, interest in sched:
            self.rows["loan_schedule"].append((loan_id, k, due, princ, interest))
            if k >= stop:
                paid_all = False
                continue
            delay = r.randint(0, 3) if profile == "good" else r.randint(5, 75)
            parts = [(1.0, delay)]
            if profile == "late" and r.random() < 0.35:
                share = r.uniform(0.4, 0.7)
                parts = [(share, delay), (1 - share, delay + r.randint(15, 45))]
            done_p = done_i = 0
            for i, (share, dl) in enumerate(parts):
                pd = due + timedelta(days=dl)
                if pd > END or self.bd(pd) > END:      # pas encore payé à la date de fin
                    paid_all = False
                    break
                pd = self.bd(pd)
                pp = princ - done_p if i == len(parts) - 1 else round(princ * share)
                ip = interest - done_i if i == len(parts) - 1 else round(interest * share)
                done_p, done_i = done_p + pp, done_i + ip
                pay_id = len(self.rows["loan_payment"]) + 1
                self.rows["loan_payment"].append((pay_id, loan_id, k, pd, pp, ip))
                self.events[pd].append(("loan_pay", a, pp, ip))
                last_pay = max(last_pay or pd, pd)
        self.events[a.open_date].append(("loan_disb", a, principal))
        status = "CLOSED" if paid_all else "ACTIVE"
        self.rows["loan"].append((loan_id, a.id, principal, rate, a.open_date, sched[-1][1], n, status))
        if paid_all:
            a.close_date = last_pay
            a.hist = [["ACTIVE", a.open_date, last_pay], ["CLOSED", last_pay, None]]

    # ----- écritures ----------------------------------------------------
    def post(self, ttype, channel, d, a, amount, legs, *, user=None, partner=None,
             reversal_of=None, branch=None, rejected=False, hour=None):
        """legs = [(gl_id, account_id|None, 'D'|'C')] : toutes du même montant (2 jambes équilibrées)
        ou [(gl_id, account_id, dc, montant)] pour des jambes de montants différents."""
        self.txn_seq += 1
        tid = self.txn_seq
        bdate = self.bd(d)
        ccy = a.currency if a else "XOF"
        fx = self.fx[bdate][ccy]
        if hour is None:
            hour = self.r.randint(8, 16) if channel == "BRANCH" else self.r.randint(0, 23)
        tdate = datetime(d.year, d.month, d.day, hour, self.r.randint(0, 59), self.r.randint(0, 59))
        if channel == "BATCH":
            tdate = datetime(d.year, d.month, d.day, 23, 30, 0)
        amount = round(amount, 2)
        self.rows["txn"].append((tid, f"TX{tid:010d}", ttype, channel, partner,
                                 branch or (a.branch_id if a else 1), tdate, bdate, bdate, amount, ccy,
                                 round(amount * fx), "REJECTED" if rejected else "POSTED", reversal_of, user))
        if rejected:
            return tid
        for leg in legs:
            gl_id, acc_id, dc = leg[:3]
            amt = round(leg[3] if len(leg) == 4 else amount, 2)
            if amt <= 0:
                continue
            self.entry_seq += 1
            self.rows["gl_entry"].append((self.entry_seq, tid, gl_id, acc_id, dc, amt, ccy,
                                          round(amt * fx), bdate, bdate))
            if acc_id is not None:
                self.by_id[acc_id].ledger += amt if dc == "C" else -amt
        return tid

    def available(self, a: Account, d: date) -> float:
        blocked = sum(amt for amt, s, e in self.blocks[a.id] if s <= d and (e is None or d < e))
        return a.ledger + a.overdraft - blocked

    def ctl(self, a: Account) -> int:
        return PROD[a.product_id][7]

    def teller(self, branch_id: int) -> int:
        return self.r.choice(self.tellers[branch_id])

    # ----- simulation jour par jour ------------------------------------
    def simulate(self):
        d = START
        current_xof = [a for a in self.accounts if a.product_id in (1, 2)]
        while d <= END:
            business = self.is_bd(d)
            december = d.month == 12 and d.day >= 15
            for ev in self.events.get(d, []):
                self.planned(ev, d)
            for a in self.accounts:
                if a.open_date >= d or (a.close_date and d >= a.close_date) or d > a.activity_end:
                    continue
                if a.status_at(d) != "ACTIVE" or a.family not in ("CURRENT", "SAVINGS"):
                    continue
                self.customer_activity(a, d, business, december, current_xof)
            last_day = d.day == calendar.monthrange(d.year, d.month)[1]
            if last_day:
                self.month_end(d)
            if business:
                self.snapshot(d)
            d += timedelta(days=1)

    def customer_activity(self, a, d, business, december, current_xof):
        r = self.r
        k = 1 if a.currency == "XOF" else 1 / 655.957
        cash, ctl = G["CASH"], self.ctl(a)
        if a.family == "SAVINGS":
            if business and r.random() < 0.03:
                self.post("DEPOSIT", "BRANCH", d, a, round(r.uniform(10_000, 300_000), -3),
                          [(cash, None, "D"), (ctl, a.id, "C")], user=self.teller(a.branch_id))
            elif business and r.random() < 0.01:
                amt = min(round(r.uniform(20_000, 500_000), -3), max(0, self.available(a, d)))
                if amt >= 5_000:
                    self.post("WITHDRAWAL", "BRANCH", d, a, amt,
                              [(ctl, a.id, "D"), (cash, None, "C")], user=self.teller(a.branch_id))
            return
        # comptes courants
        if a.salary and d.day == 25:
            self.post("TRANSFER", "TRANSFER", d, a, round(a.salary * r.uniform(0.98, 1.02), 0 if k == 1 else 2),
                      [(G["CLR_BANK"], None, "D"), (ctl, a.id, "C")])
        pro = a.product_id == 2
        if business and r.random() < (0.10 if pro else 0.04):
            amt = round(r.lognormvariate(12.5 if pro else 11.3, 0.8) * k, 0 if k == 1 else 2)
            branch = a.branch_id if r.random() < 0.9 else r.randint(1, len(BRANCHES))
            self.post("DEPOSIT", "BRANCH", d, a, amt, [(cash, None, "D"), (ctl, a.id, "C")],
                      user=self.teller(branch), branch=branch)
        if business and r.random() < (0.10 if december else 0.05):
            amt = math.floor(min(r.lognormvariate(11.5, 0.7) * k, self.available(a, d)) / (1000 * k)) * 1000 * k
            if amt >= 5_000 * k:
                self.post("WITHDRAWAL", "BRANCH", d, a, amt, [(ctl, a.id, "D"), (cash, None, "C")],
                          user=self.teller(a.branch_id))
        if a.has_card and r.random() < 0.05:
            amt = round(r.lognormvariate(10.3, 0.9) * k, 0 if k == 1 else 2)
            self.post("CARD_PAYMENT", "CARD", d, a, amt, [(ctl, a.id, "D"), (G["CLR_CARD"], None, "C")],
                      rejected=amt > self.available(a, d))
        if a.currency == "XOF" and r.random() < 0.05:
            amt = round(r.lognormvariate(10.0, 0.9), -2) or 1_000
            partner = r.choice(MM_PARTNERS)
            if r.random() < 0.5:   # wallet -> compte
                self.post("DEPOSIT", "MOBILE_MONEY", d, a, amt, [(G["CLR_MM"], None, "D"), (ctl, a.id, "C")],
                          partner=partner)
            else:                  # compte -> wallet
                self.post("WITHDRAWAL", "MOBILE_MONEY", d, a, amt, [(ctl, a.id, "D"), (G["CLR_MM"], None, "C")],
                          partner=partner, rejected=amt > self.available(a, d))
        if a.currency == "XOF" and r.random() < 0.01:
            b = r.choice(current_xof)
            amt = round(r.uniform(10_000, 400_000), -3)
            if (b.id != a.id and b.open_date < d and not (b.close_date and d >= b.close_date)
                    and d <= b.activity_end and b.status_at(d) == "ACTIVE" and amt <= self.available(a, d)):
                self.post("TRANSFER", "TRANSFER", d, a, amt, [(ctl, a.id, "D"), (self.ctl(b), b.id, "C")])

    def planned(self, ev, d):
        kind, a = ev[0], ev[1]
        cash, ctl = G["CASH"], self.ctl(a)
        if kind == "open_deposit":
            k = 1 if a.currency == "XOF" else 1 / 655.957
            self.post("DEPOSIT", "BRANCH", d, a, round(self.r.uniform(10_000, 500_000) * k, 0 if k == 1 else 2),
                      [(cash, None, "D"), (ctl, a.id, "C")], user=self.teller(a.branch_id))
        elif kind == "term_open":
            a.term_amount = round(self.r.uniform(1_000_000, 20_000_000), -5)
            self.post("DEPOSIT", "TRANSFER", d, a, a.term_amount, [(G["CLR_BANK"], None, "D"), (ctl, a.id, "C")])
        elif kind == "term_mature":
            interest = round(a.ledger * PROD[a.product_id][5])
            self.post("INTEREST", "BATCH", d, a, interest, [(G["EXP_INT"], None, "D"), (ctl, a.id, "C")])
            self.post("WITHDRAWAL", "TRANSFER", d, a, a.ledger, [(ctl, a.id, "D"), (G["CLR_BANK"], None, "C")])
        elif kind == "loan_disb":
            self.post("LOAN_DISB", "BRANCH", d, a, ev[2], [(ctl, a.id, "D"), (cash, None, "C")],
                      user=self.teller(a.branch_id))
        elif kind == "loan_pay":
            pp, ip = ev[2], ev[3]
            self.post("LOAN_REPAY", "BRANCH", d, a, pp + ip,
                      [(cash, None, "D", pp + ip), (ctl, a.id, "C", pp), (G["INC_INT"], None, "C", ip)],
                      user=self.teller(a.branch_id))
        elif kind == "close":
            if a.ledger > 0:
                self.post("WITHDRAWAL", "BRANCH", d, a, a.ledger, [(ctl, a.id, "D"), (cash, None, "C")],
                          user=self.teller(a.branch_id))
            elif a.ledger < 0:
                self.post("DEPOSIT", "BRANCH", d, a, -a.ledger, [(cash, None, "D"), (ctl, a.id, "C")],
                          user=self.teller(a.branch_id))
        elif kind == "reverse_fee":
            orig_id, amt = ev[2], ev[3]
            if not (a.close_date and d >= a.close_date):
                self.post("REVERSAL", "BRANCH", d, a, amt, [(G["INC_FEE"], None, "D"), (ctl, a.id, "C")],
                          reversal_of=orig_id, user=self.r.choice(self.backoffice), branch=1)

    def month_end(self, d):
        r = self.r
        quarter_end = d.month in (3, 6, 9, 12)
        for a in self.accounts:
            if a.open_date >= d or (a.close_date and d >= a.close_date):
                continue
            p = PROD[a.product_id]
            if p[6] and a.family in ("CURRENT", "SAVINGS"):
                tid = self.post("FEE", "BATCH", d, a, p[6], [(self.ctl(a), a.id, "D"), (G["INC_FEE"], None, "C")])
                if r.random() < 0.02:
                    when = d + timedelta(days=r.randint(3, 12))
                    if when <= END:
                        self.events[when].append(("reverse_fee", a, tid, p[6]))
            if quarter_end and a.family == "SAVINGS" and a.ledger > 0:
                interest = round(a.ledger * p[5] / 4)
                if interest > 0:
                    self.post("INTEREST", "BATCH", d, a, interest, [(G["EXP_INT"], None, "D"), (self.ctl(a), a.id, "C")])

    def snapshot(self, d):
        for a in self.accounts:
            if a.open_date > d or (a.close_date and d > a.close_date):
                continue
            avail = a.ledger if a.family in ("LOAN", "TERM") else self.available(a, d)
            self.rows["daily_balance"].append((a.id, d, round(a.ledger, 2), round(avail, 2)))

    # ----- finalisation -------------------------------------------------
    def finalize(self):
        self.rows["customer"] = [tuple(c) for c in self.customers]
        for a in self.accounts:
            self.rows["account"].append((a.id, a.number, a.product_id, a.branch_id, a.hist[-1][0], a.open_date,
                                         a.close_date, a.currency, a.overdraft))
            for s, f, t in a.hist:
                self.rows["account_status_hist"].append((a.id, s, f, t))
            for amt, s, e in self.blocks[a.id]:
                self.rows["account_block"].append((len(self.rows["account_block"]) + 1, a.id, amt,
                                                   self.r.choice(["SEIZURE", "GUARANTEE", "OPPOSITION"]), s, e))
            if a.has_card:
                exp = a.open_date + timedelta(days=3 * 365)
                pan = f"4{self.r.randint(10**4, 10**5 - 1)}******{self.r.randint(1000, 9999)}"
                status = "EXPIRED" if exp < END else ("BLOCKED" if a.hist[-1][0] == "BLOCKED" else "ACTIVE")
                self.rows["card"].append((len(self.rows["card"]) + 1, a.id, "DEBIT", pan, status, exp))


LOAD_ORDER = ["branch", "gl_account", "product", "app_user", "business_calendar", "fx_rate", "customer",
              "account", "account_status_hist", "account_block", "account_holder", "card", "beneficiary",
              "fee_rule", "loan", "loan_schedule", "loan_payment", "txn", "gl_entry", "daily_balance"]


def bind_types(rows):
    """Type de chaque colonne d'après sa première valeur non NULL (sinon executemany devine mal)."""
    types = []
    for col in range(len(rows[0])):
        v = next((row[col] for row in rows if row[col] is not None), None)
        if isinstance(v, (date, datetime)):
            types.append(db.oracledb.DB_TYPE_DATE)
        elif isinstance(v, (int, float)):
            types.append(db.oracledb.DB_TYPE_NUMBER)
        else:
            types.append(200)
    return types


def load(lab: Lab):
    with db.connect() as conn, conn.cursor() as cur:
        db.drop_all(cur)
        for f in sorted((ROOT / "db" / "core").glob("*.sql")):
            db.run_file(cur, f)
        for table in LOAD_ORDER:
            rows = lab.rows[table]
            if not rows:
                continue
            binds = ", ".join(f":{i + 1}" for i in range(len(rows[0])))
            cur.setinputsizes(*bind_types(rows))
            for i in range(0, len(rows), 20_000):
                cur.executemany(f"INSERT INTO {table} VALUES ({binds})", rows[i:i + 20_000])
            conn.commit()
            print(f"  {table:<22}{len(rows):>10,}")
        cur.execute("BEGIN DBMS_STATS.GATHER_SCHEMA_STATS(USER); END;")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--size", choices=SIZES, default="small")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--dry-run", action="store_true", help="générer sans charger la base")
    args = ap.parse_args()
    t0 = time.time()
    lab = Lab(args.seed, *SIZES[args.size])
    lab.build_calendar()
    lab.build_reference()
    lab.build_customers()
    lab.build_accounts()
    lab.simulate()
    lab.finalize()
    print(f"Généré en {time.time() - t0:.1f}s (seed={args.seed}, size={args.size})")
    if args.dry_run:
        for t in LOAD_ORDER:
            print(f"  {t:<22}{len(lab.rows[t]):>10,}")
        return
    load(lab)
    print(f"Chargé en {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
