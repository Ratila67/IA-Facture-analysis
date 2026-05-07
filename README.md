# TP-Fact - Receipt Matcher Studio

Un mini-lab IA qui lit un ticket de caisse, extrait ses infos cles, puis tente un rapprochement automatique avec des releves bancaires CSV.

---

## Pourquoi ce projet existe

Le but: eliminer le rapprochement manuel ticket <-> transaction bancaire.

Ce projet combine:
- Vision + extraction IA sur une image de ticket
- Normalisation des donnees (montants, devises)
- Matching intelligent sur les releves bancaires
- Interface Streamlit orientee demo

---

## Experience utilisateur (version courte)

1. Ouvrir l'app Streamlit  
2. Choisir un receipt dans la sidebar  
3. Cliquer sur `Analyser maintenant`  
4. Voir:
   - les metriques ticket (total, marchand, devise),
   - la strategie de match (`amount_and_currency`, `amount_only`, `none`),
   - les transactions candidates dans les CSV.

---

## Stack

- Python 3.9+
- Groq API (analyse IA ticket)
- Streamlit (UI)
- CSV natif (releves bancaires)

---

## Structure du projet

```text
TP-Fact/
|- app.py                         # Interface Streamlit
|- main.py                        # Logique extraction + matching
|- requirements.txt
|- .env                           # Contient GROQ_API_KEY (non versionne)
`- dataset/
   |- receipts/                   # Images de tickets
   `- bank_statements/            # Releves CSV
```

---

## Setup rapide

```bash
cd /Users/jeromew/Documents/Hetic/TD-Hakim/TP-Fact
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Creer un fichier `.env`:

```bash
echo "GROQ_API_KEY=ta_cle_api" > .env
```

---

## Lancer l'application (mode UI)

```bash
source .venv/bin/activate
streamlit run app.py
```

---

## Lancer en script (mode terminal)

Analyse d'un ticket par defaut:

```bash
source .venv/bin/activate
python main.py
```

Analyse d'un ticket specifique:

```bash
python main.py dataset/receipts/1164-receipt.jpg
```

Sortie:
- `receipt_analysis` (donnees extraites par IA)
- `matching`:
  - `matched_count`
  - `match_strategy`
  - `matched_transactions`

---

## Comment fonctionne le matching

Le moteur:
- charge tous les fichiers `dataset/bank_statements/*.csv`,
- normalise les montants (`22,70` et `22.70` sont traites pareil),
- cherche les transactions avec tolerance de `0.01`.

Strategie:
- `amount_and_currency`: match fort (montant + devise)
- `amount_only`: fallback quand la devise IA est incertaine
- `none`: aucune transaction candidate

---

## Demo script (pour presenter le projet)

Tu peux presenter en 30 secondes comme ca:

> "Je selectionne un ticket dans l'UI.  
> L'IA extrait montant, date, marchand et devise.  
> Ensuite le moteur scanne tous les releves CSV et retourne les transactions candidates avec un niveau de confiance."

---

## Bonnes pratiques Git

Le projet ignore deja:
- `.env`
- `.venv/`
- cache Python
- `dataset/*`

Donc tu peux versionner le code sans exposer ni secret ni gros fichiers dataset.

---

## Next steps possibles

- Matching fuzzy sur le marchand (`merchant` vs `vendor`)
- Score global de confiance (montant + devise + date + vendor)
- Export automatique en JSON/CSV des resultats
- Mode batch sur un dossier complet de tickets

---

Si tu veux, je peux aussi te faire une version README "portfolio" (avec badges, GIF demo, KPI et captures) prete pour recruteurs.
