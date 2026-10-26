# Finspire

**Make Money Make Sense.** A personal finance web app with an animated AI money buddy, *Budget Chachu*.

Built for **Code Canvas 2K26** (Theme: MoneyMatters), Crescent Institute of Science & Technology.

---

## Team Members

- Sumaiya Afreen
- Safah

## Project Description

Many people struggle to understand where their money goes and how to grow it. Finspire makes money management smarter, simpler and more accessible with a friendly desi AI guide.

### Features

| Feature | What it does |
|---|---|
| **Budget Chachu (AI chatbot)** | An animated desi uncle who answers finance questions in simple words. He floats, blinks, shows a "thinking" pose while the AI generates a reply, then speaks the answer with mouth and head animation, live typing and optional voice. His eyes follow the cursor, and clicking him shows a money tip. |
| **Personalised suggestion pop-ups** | When a user enters the dashboard, a card carousel suggests ways to put savings to work (emergency fund, SIP with a 10-year projection, index funds, gold, goal progress), based on the user's own spending, budget and goals. |
| **News Flash** | Live headlines on stocks, gold, crypto, economy and savings from trusted Indian finance sources (Economic Times, Mint, Moneycontrol, Business Standard, BusinessLine). The dashboard also shows a Market Pulse panel and pop-up news toasts. |
| **Expense Tracker** | Add and delete expenses, category breakdown, monthly budget progress with over-budget warning, and receipt uploads (png, jpg, pdf). |
| **Savings Planner and Guide** | Goal tracker with progress and required monthly saving, SIP growth calculator, 50/30/20 income splitter and practical tips. |
| **Roles** | A pre-existing **Admin** superuser who can view platform stats and remove users, and regular users with their own private data. |

### How the AI is used

Budget Chachu sends the conversation, plus a summary of the user's expenses, budget and goals, to the Google Gemini API through the Flask backend (the API key never reaches the browser). If no key is set or the call fails, Chachu falls back to built-in answers so the app always works.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python, Flask |
| Frontend | Jinja2, HTML, CSS, Bootstrap 5 (with Bootstrap Icons) |
| Database | SQLite (via Flask-SQLAlchemy) |
| Auth | Flask-Login |
| File Uploads | Werkzeug |

## AI Tools Used

- **Claude (Anthropic)**: project planning, starter code for the Flask app, UI redesign and Chachu animation
- **Google Gemini API**: powers Budget Chachu's answers inside the app
- **GitHub Copilot (VS Code)**: *(keep this line only if you used it)*

## Important Prompts Used

1. "Build a working website with an AI chatbot, with a news flash from trusted websites about stocks, gold, etc., an expenses tracker and a savings planner and guide. Website name Finspire, chatbot name Budget Chachu, a desi animated character that floats, blinks and thinks while the AI generates text."
2. "Use this stack: Python Flask, Jinja2/HTML/CSS/Bootstrap 5, SQLite via Flask-SQLAlchemy, Flask-Login, Werkzeug file uploads. Give me an easy-to-demonstrate application."
3. "Remove emojis, make it more modern and clean with real icons, add pop-up news in the dashboard, suggest pop-up cards to invest my savings when I enter the website, and let Chachu act as if speaking when the AI answers."

*(Add any Copilot prompts you used here.)*


## Bug Solved Independently

*(Write one real bug you found and fixed yourself, with what caused it and how you fixed it.)*

## How to Run

```bash
# 1. Create and activate a virtual environment
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # Mac / Linux

# 2. Install dependencies
pip install -r requirements.txt

# 3. (Optional) Enable the full AI brain
#    Copy .env.example to .env and add a free Gemini key from https://aistudio.google.com/apikey

# 4. Start the app
python app.py
```

Open **http://127.0.0.1:5000**

### Demo accounts

| Role | Username | Password |
|---|---|---|
| User | `demo` | `demo123` |
| Admin | `admin` | `admin123` |

The database is created automatically on first run, with demo data included.

## Project Structure

```
finspire2/
├── app.py                 # Flask routes, models, AI chat, news, suggestions
├── requirements.txt
├── .env.example
├── templates/             # Jinja2 pages (dashboard, chat, news, expenses, savings, admin)
├── static/
│   ├── css/style.css      # Design system and Budget Chachu animations
│   └── js/                # chachu.js, chat.js, dashboard.js
└── uploads/               # Receipt uploads
```

## Disclaimer

Finspire is for education only and does not provide financial advice. Projections are estimates and returns are not guaranteed.
