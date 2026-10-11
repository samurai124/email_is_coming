# Job Application Auto-Mailer & Lead Scraper CLI (v2.0)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![AI Powered](https://img.shields.io/badge/AI-Google_Gemini-orange.svg)](https://aistudio.google.com/)
[![Scraping](https://img.shields.io/badge/Scraper-Agent_Reach_Engine-green.svg)](https://github.com/Panniantong/Agent-Reach)

An automated, intelligent application designed to **find & scrape company recruitment emails in any target city or area**, generate personalized cold job application emails with **your resume attached**, and dispatch them safely with built-in anti-spam safeguards.

📄 **A full PDF setup manual is available at:** [`SETUP_AND_USER_GUIDE.pdf`](./SETUP_AND_USER_GUIDE.pdf)

---

## 📁 Project Structure

```text
job_application_mailer/
├── data/
│   ├── companies.csv            <- Target companies & contacts (auto-populated by scraper)
│   ├── sent_log.csv             <- Automatically tracked delivery history (prevents duplicates)
│   └── resumes/
│       └── resume.pdf           <- Your resume PDF to attach
├── templates/
│   └── default_template.txt     <- Fallback customizable email template
├── .env                         <- Your credentials and personal profile
├── .env.example                 <- Example configuration reference
├── lead_scraper.py              <- Phase 1: Area web scraper (Jina Reader + DDG search)
├── ai_generator.py              <- Gemini AI personalization & pitch engine
├── csv_manager.py               <- CSV parser, deduplication & delivery logging
├── email_sender.py              <- SMTP client with TLS, attachments & anti-spam delays
├── config.py                    <- Environment loader & configuration validator
├── main.py                      <- Interactive CLI interface (Phase 1 -> Phase 2)
├── SETUP_AND_USER_GUIDE.pdf     <- Formatted PDF Setup Manual
└── README.md
```

---

## 🚀 Quick Setup (In 3 Simple Steps)

### Étape 1 : Configurer votre profil dans `.env` / Configure `.env`
Ouvrez le fichier `.env` dans un éditeur de texte (Bloc-notes, VS Code...) et remplissez vos informations :

```ini
# Informations personnelles du candidat
SENDER_NAME="Votre Nom Complet"
SENDER_EMAIL="votre_email@gmail.com"
SENDER_PHONE="+212 600000000"
SENDER_LINKEDIN="www.linkedin.com/in/votre-profil"
CANDIDATE_SUMMARY="Développeur Web Full Stack spécialisé en Python, React, et architectures cloud."

# Configuration SMTP Gmail :
SMTP_SERVER="smtp.gmail.com"
SMTP_PORT=587
SENDER_PASSWORD="xxxx xxxx xxxx xxxx"    # Mot de passe d'application Google (16 caractères)

# Clé API Google Gemini (Gratuite) :
GEMINI_API_KEY="votre-cle-gemini"
GEMINI_MODEL="gemini-2.5-flash"

# Fichier de CV à joindre :
RESUME_FILENAME="resume.pdf"
```

#### 🔑 Comment obtenir le mot de passe d'application Gmail (1 minute) :
1. Activez la **Validation en deux étapes** sur votre [Compte Google](https://myaccount.google.com/security).
2. Rendez-vous directement sur : **[https://myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)**.
3. Donnez un nom (ex : `JobMailer`) et cliquez sur **Créer**.
4. Copiez le code de 16 lettres affiché dans l'encadré jaune et collez-le dans `SENDER_PASSWORD` dans votre `.env`.

#### 🤖 Comment obtenir une clé API Gemini gratuite (30 secondes) :
1. Allez sur **[Google AI Studio](https://aistudio.google.com/)**.
2. Cliquez sur **Get API key** et générez une clé.
3. Collez-la dans `GEMINI_API_KEY` dans votre `.env`.

---

### Étape 2 : Placer votre CV / Place your Resume
Placez votre CV au format PDF dans le dossier `data/resumes/` et assurez-vous que son nom correspond à `RESUME_FILENAME` dans le `.env` (par exemple : `resume.pdf` ou `Hamza_Zaidi_CV.pdf`).

---

### Étape 3 : Lancer l'application / Run the App

Ouvrez un terminal PowerShell dans le dossier du projet et exécutez :

```powershell
python main.py
```

Le menu interactif s'affiche :

```text
===============================================================
       JOB APPLICATION AUTO-MAILER (CLI)
       AI-Powered Cold Outreach with Resume Attachment
===============================================================

Select an action:
  1. 🔍 Scrape & Find Company Emails in an Area
  2. 📧 Send Job Application Emails (with Resume & AI)
  3. Exit
```

---

## 🔄 Le flux de travail en deux phases (Two-Phase Workflow)

### Phase 1 : Scraping et Découverte d'entreprises (Option 1)
1. L'application vous demande la **ville/zone** (ex: `Rabat`, `Casablanca`, `Paris`), le **secteur** (ex: `startups`, `agences web`) et le **poste** visé.
2. Le moteur inspiré d'**Agent Reach** (Jina Reader `r.jina.ai` + recherche web) explore le web, visite les pages de recrutement et extrait les emails professionnels.
3. L'IA Gemini synthétise l'activité de l'entreprise pour préparer l'accroche personnalisée.
4. Les entreprises trouvées sont enregistrées dans [`data/companies.csv`](./data/companies.csv) en éliminant automatiquement les doublons.

### Phase 2 : Envoi ciblé et sécurisé (Option 2 & 3)
1. **Prévisualisation (Option 2 - Dry-Run)** : Affiche l'email exactement comme il sera envoyé sans contacter l'entreprise.
2. **Envoi par lot (Option 3)** :
   - Vous demande confirmation (`yes`) avant tout envoi.
   - Attache automatiquement votre CV au format PDF.
   - Applique une temporisation aléatoire (20 à 45 secondes) entre chaque email pour **ne pas être détecté comme spam**.
   - Enregistre chaque envoi réussi dans [`data/sent_log.csv`](./data/sent_log.csv). Relancer l'application n'enverra **JAMAIS** deux fois un email à la même entreprise !

---

## ⚡ Commandes rapides en ligne de commande (Direct Flags)

Vous pouvez également lancer directement des actions sans passer par le menu interactif :

- **Rechercher et scraper des entreprises dans une ville :**
  ```powershell
  python main.py --scrape --area "Casablanca" --industry "startups" --role "Développeur Full Stack" --limit 10
  ```
- **Prévisualiser les 2 prochains emails générés par l'IA :**
  ```powershell
  python main.py --preview 2
  ```
- **Lancer l'envoi des candidatures aux entreprises en attente :**
  ```powershell
  python main.py --send
  ```
- **Consulter les statistiques (envoyés / en attente) :**
  ```powershell
  python main.py --status
  ```
- **Tester la connexion SMTP et la présence du CV :**
  ```powershell
  python main.py --test
  ```

---

## 🛡️ Règles de sécurité & Anti-Spam

> [!IMPORTANT]
> **Limite quotidienne recommandée** : Ne dépassez pas 30 à 50 candidatures par jour depuis une boîte personnelle.
> La temporisation de 20 à 45 secondes intégrée dans l'application simule un comportement humain et préserve la réputation de votre adresse email.
