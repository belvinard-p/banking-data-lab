# Banking Data Analytics & Core Banking SQL Lab

> **Données entièrement fictives, modèle générique.** Lagune Bank n'existe pas ; le schéma ne reproduit le système d'aucune banque ni d'aucun éditeur.

Core Banking simulé sous Oracle (schéma `CBS_LAB`, 20 tables, partie double) pour pratiquer : demande métier floue → SQL → contrôle indépendant → livraison → indicateur.

## Démarrage rapide

Prérequis : Docker Desktop, Python 3.12+.

```bash
cp .env.example .env                 # puis changer les mots de passe
docker compose up -d                 # Oracle 23ai Free ; attendre l'état "healthy"
python -m venv .venv && .venv/Scripts/python -m pip install -r data-generator/requirements.txt
.venv/Scripts/python data-generator/generate.py --size small --seed 42   # recrée le schéma + charge
.venv/Scripts/python tools/db.py run sql/00_sanity/sanity_checks.sql
```

(Sous Linux/macOS : `.venv/bin/...`.) Connexion SQL Developer : hôte `localhost`, port `1521`, service `FREEPDB1`, utilisateur `CBS_LAB`.

## Jeu « small » (seed 42)

| Table | Lignes |
| --- | ---: |
| customer / account | 500 / 800 |
| txn | 62 424 |
| gl_entry | 123 655 |
| daily_balance | 314 058 |

Période simulée : 01/01/2024 → 30/09/2026.

create new branch
