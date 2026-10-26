import os, json, time, uuid, random, urllib.request, urllib.parse
import xml.etree.ElementTree as ET
from datetime import date
from functools import wraps
from flask import (Flask, render_template, request, redirect, url_for, flash,
                   jsonify, send_from_directory, abort)
from flask_sqlalchemy import SQLAlchemy
from flask_login import (LoginManager, UserMixin, login_user, logout_user,
                         login_required, current_user)
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

BASE = os.path.abspath(os.path.dirname(__file__))
app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("SECRET_KEY", "finspire-dev-key"),
    SQLALCHEMY_DATABASE_URI="sqlite:///finspire.db",
    UPLOAD_FOLDER=os.path.join(BASE, "uploads"),
    MAX_CONTENT_LENGTH=4 * 1024 * 1024,
)
os.makedirs(app.config["UPLOAD_FOLDER"], exist_ok=True)
ALLOWED = {"png", "jpg", "jpeg", "pdf"}
CATEGORIES = ["Food", "Travel", "Shopping", "Bills", "Fun", "Health", "Other"]

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# ---------------- Models ----------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    is_admin = db.Column(db.Boolean, default=False)
    budget = db.Column(db.Float, default=0)
    expenses = db.relationship("Expense", backref="user", cascade="all, delete-orphan")
    goals = db.relationship("Goal", backref="user", cascade="all, delete-orphan")


class Expense(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    category = db.Column(db.String(30), default="Other")
    day = db.Column(db.Date, default=date.today)
    receipt = db.Column(db.String(120))


class Goal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    target = db.Column(db.Float, nullable=False)
    saved = db.Column(db.Float, default=0)
    months = db.Column(db.Integer, default=12)

    @property
    def pct(self):
        return min(100, round(self.saved / self.target * 100)) if self.target else 0

    @property
    def monthly(self):
        return max(0, self.target - self.saved) / max(1, self.months)


@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))


def admin_required(f):
    @wraps(f)
    @login_required
    def wrapper(*a, **k):
        if not current_user.is_admin:
            abort(403)
        return f(*a, **k)
    return wrapper


@app.template_filter("inr")
def inr(n):
    """Format as Indian rupees with lakh/crore grouping, e.g. ₹8,13,187."""
    n = int(round(n or 0))
    sign, digits = ("-" if n < 0 else ""), str(abs(n))
    if len(digits) > 3:
        head, tail = digits[:-3], digits[-3:]
        parts = []
        while len(head) > 2:
            parts.insert(0, head[-2:])
            head = head[:-2]
        if head:
            parts.insert(0, head)
        digits = ",".join(parts) + "," + tail
    return f"₹{sign}{digits}"


def seed():
    db.create_all()
    if User.query.first():
        return
    admin = User(username="admin", password_hash=generate_password_hash("admin123"), is_admin=True)
    demo = User(username="demo", password_hash=generate_password_hash("demo123"), budget=15000)
    db.session.add_all([admin, demo])
    db.session.flush()
    for t, a, c in [("Biryani with friends", 450, "Food"), ("Metro card recharge", 500, "Travel"),
                    ("Electricity bill", 1800, "Bills"), ("Movie night", 600, "Fun"),
                    ("New headphones", 2499, "Shopping"), ("Groceries", 2200, "Food")]:
        db.session.add(Expense(user_id=demo.id, title=t, amount=a, category=c))
    db.session.add(Goal(user_id=demo.id, name="New laptop", target=60000, saved=18000, months=10))
    db.session.commit()


with app.app_context():
    seed()


# ---------------- Auth ----------------
@app.route("/")
def home():
    return render_template("home.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        u = request.form["username"].strip()
        p = request.form["password"]
        if len(u) < 3 or len(p) < 4:
            flash("Username min 3 chars and password min 4 chars.", "warning")
        elif User.query.filter_by(username=u).first():
            flash("That username is taken.", "danger")
        else:
            user = User(username=u, password_hash=generate_password_hash(p))
            db.session.add(user)
            db.session.commit()
            login_user(user)
            flash("Welcome to Finspire!", "success")
            return redirect(url_for("dashboard"))
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"].strip()).first()
        if user and check_password_hash(user.password_hash, request.form["password"]):
            login_user(user)
            return redirect(url_for("admin_panel" if user.is_admin else "dashboard"))
        flash("Wrong username or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("home"))


# ---------------- Dashboard ----------------
TIPS = ["Pay yourself first: move savings out on salary day.",
        "Keep 3-6 months of expenses as an emergency fund.",
        "Credit-card interest is 30-40% a year. Avoid it!",
        "Start a SIP early. Time in the market beats timing the market.",
        "Track every rupee for 30 days. You will be surprised!"]


def summary(user):
    total = sum(e.amount for e in user.expenses)
    by = {}
    for e in user.expenses:
        by[e.category] = by.get(e.category, 0) + e.amount
    return total, dict(sorted(by.items(), key=lambda x: -x[1]))


def suggestions(user):
    """Personalised, educational suggestion cards shown when the user enters the site."""
    total, by = summary(user)
    saved = sum(g.saved for g in user.goals)
    surplus = max(0, user.budget - total) if user.budget else 0
    base = surplus or saved * 0.05
    cards = []
    target = round(max(total, 5000) * 3, -2)
    if saved < target:
        cards.append(dict(icon="shield-check", tag="Safety first", title="Build your emergency fund",
                          body=f"Aim for {inr(target)}, about 3 months of your spending, in a savings account or liquid fund before taking market risk.",
                          prompt="How do I build an emergency fund?"))
    sip = int(max(500, round(base * 0.5, -2)))
    fv = sip * ((1.01 ** 120 - 1) / 0.01) * 1.01
    cards.append(dict(icon="graph-up-arrow", tag="Long-term growth", title=f"Start a monthly SIP of {inr(sip)}",
                      body=f"At an assumed 12% a year, {inr(sip)} a month could grow to about {inr(fv)} in 10 years. Estimate only, returns are not guaranteed.",
                      prompt="Explain how a SIP works with an example"))
    cards.append(dict(icon="pie-chart", tag="Diversify", title="Spread risk with index funds",
                      body="A low-cost Nifty 50 index fund gives you a slice of India's top companies without picking individual stocks.",
                      prompt="What is an index fund and is it good for beginners?"))
    cards.append(dict(icon="coin", tag="Inflation hedge", title="Keep 5-10% in gold",
                      body="Sovereign Gold Bonds and gold ETFs are cleaner and cheaper than jewellery for investing in gold.",
                      prompt="Is gold a good investment?"))
    open_goals = [g for g in user.goals if g.pct < 100]
    if open_goals:
        g = open_goals[0]
        cards.append(dict(icon="bullseye", tag="Your goal", title=f"Stay on track for {g.name}",
                          body=f"Save {inr(g.monthly)} a month to reach {inr(g.target)} in {g.months} months. You are {g.pct}% there.",
                          prompt=f"How can I reach my goal of {g.name} faster?"))
    if user.budget and total > user.budget and by:
        top = next(iter(by))
        cards.insert(0, dict(icon="exclamation-triangle", tag="Heads up", title="You are over budget",
                             body=f"Your biggest category is {top}. Trimming it first is the fastest way to free up money to invest.",
                             prompt="How can I cut my spending?"))
    return cards[:5]


@app.route("/dashboard")
@login_required
def dashboard():
    total, by = summary(current_user)
    return render_template("dashboard.html", total=total, by=by, tip=random.choice(TIPS),
                           suggestions=suggestions(current_user))


# ---------------- Expenses ----------------
@app.route("/expenses", methods=["GET", "POST"])
@login_required
def expenses():
    if request.method == "POST":
        try:
            amount = float(request.form["amount"])
        except ValueError:
            flash("Enter a valid amount.", "danger")
            return redirect(url_for("expenses"))
        fname = None
        f = request.files.get("receipt")
        if f and f.filename:
            ext = f.filename.rsplit(".", 1)[-1].lower()
            if ext in ALLOWED:
                fname = uuid.uuid4().hex[:10] + "_" + secure_filename(f.filename)
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], fname))
            else:
                flash("Receipt must be png, jpg or pdf.", "warning")
        d = date.fromisoformat(request.form.get("day") or date.today().isoformat())
        db.session.add(Expense(user_id=current_user.id, title=request.form["title"].strip(),
                               amount=amount, category=request.form["category"], day=d, receipt=fname))
        db.session.commit()
        flash("Expense added.", "success")
        return redirect(url_for("expenses"))
    items = Expense.query.filter_by(user_id=current_user.id).order_by(Expense.day.desc(), Expense.id.desc()).all()
    total, by = summary(current_user)
    return render_template("expenses.html", items=items, total=total, by=by,
                           cats=CATEGORIES, today=date.today().isoformat())


@app.post("/expenses/<int:eid>/delete")
@login_required
def delete_expense(eid):
    e = db.get_or_404(Expense, eid)
    if e.user_id != current_user.id:
        abort(403)
    if e.receipt:
        try:
            os.remove(os.path.join(app.config["UPLOAD_FOLDER"], e.receipt))
        except OSError:
            pass
    db.session.delete(e)
    db.session.commit()
    return redirect(url_for("expenses"))


@app.post("/budget")
@login_required
def set_budget():
    try:
        current_user.budget = float(request.form["budget"] or 0)
        db.session.commit()
        flash("Monthly budget saved.", "success")
    except ValueError:
        flash("Enter a valid budget.", "danger")
    return redirect(request.referrer or url_for("expenses"))


@app.route("/receipts/<name>")
@login_required
def receipt(name):
    e = Expense.query.filter_by(receipt=name).first_or_404()
    if e.user_id != current_user.id and not current_user.is_admin:
        abort(403)
    return send_from_directory(app.config["UPLOAD_FOLDER"], name)


# ---------------- Savings ----------------
@app.route("/savings", methods=["GET", "POST"])
@login_required
def savings():
    if request.method == "POST":
        try:
            db.session.add(Goal(user_id=current_user.id, name=request.form["name"].strip(),
                                target=float(request.form["target"]),
                                saved=float(request.form.get("saved") or 0),
                                months=int(request.form["months"])))
            db.session.commit()
            flash("Goal created.", "success")
        except ValueError:
            flash("Please enter valid numbers.", "danger")
        return redirect(url_for("savings"))
    return render_template("savings.html", goals=current_user.goals)


@app.post("/goals/<int:gid>/add")
@login_required
def goal_add(gid):
    g = db.get_or_404(Goal, gid)
    if g.user_id != current_user.id:
        abort(403)
    try:
        g.saved += float(request.form["amount"])
        db.session.commit()
    except ValueError:
        flash("Enter a valid amount.", "danger")
    return redirect(url_for("savings"))


@app.post("/goals/<int:gid>/delete")
@login_required
def goal_delete(gid):
    g = db.get_or_404(Goal, gid)
    if g.user_id != current_user.id:
        abort(403)
    db.session.delete(g)
    db.session.commit()
    return redirect(url_for("savings"))


# ---------------- Admin ----------------
@app.route("/admin")
@admin_required
def admin_panel():
    users = User.query.order_by(User.id).all()
    stats = {"users": len(users), "expenses": Expense.query.count(),
             "tracked": db.session.query(db.func.sum(Expense.amount)).scalar() or 0,
             "goals": Goal.query.count()}
    return render_template("admin.html", users=users, stats=stats)


@app.post("/admin/users/<int:uid>/delete")
@admin_required
def admin_delete_user(uid):
    u = db.get_or_404(User, uid)
    if u.is_admin:
        flash("Admin cannot be deleted.", "warning")
    else:
        db.session.delete(u)
        db.session.commit()
        flash(f"User {u.username} removed.", "success")
    return redirect(url_for("admin_panel"))


# ---------------- Budget Chachu (AI chat) ----------------
SYSTEM = ("You are Budget Chachu, a friendly desi uncle inside the Finspire app who explains money simply to Indians. "
          "Reply in simple English (a little Hinglish like 'beta' is fine), under 150 words, use INR examples, "
          "short points when helpful, never promise returns, and remind that this is education, not financial advice. "
          "Never use emojis or markdown other than **bold**. Write short, natural sentences that sound good when spoken aloud. "
          "If the user's expense summary is given, personalise your tips.")


def offline_reply(q):
    q = q.lower()
    rules = [(("sip", "mutual"), "**SIP** means investing a fixed amount monthly in a mutual fund. Even ₹500/month builds the habit and smooths market ups and downs. Start small, stay long, beta!"),
             (("save", "saving"), "Try the **50/30/20 rule**: 50% needs, 30% wants, 20% savings. Pay yourself first, on salary day itself."),
             (("budget", "expense", "spend"), "Track every rupee for a month in the Expenses tab, then cap your wants. Arre wah, awareness itself saves money!"),
             (("gold",), "Gold hedges inflation, but keep it around 5-10% of your money. Sovereign Gold Bonds and gold ETFs are cleaner than jewellery."),
             (("stock", "share", "nifty", "sensex"), "Stocks are tiny pieces of companies: higher return, higher risk. Learn first, start with index funds, never invest money needed within 3 years."),
             (("emergency",), "Keep **3-6 months of expenses** in a savings account or liquid fund before investing anywhere else."),
             (("loan", "credit", "emi"), "Avoid credit-card interest (30-40% a year!). Keep total EMIs under 40% of income.")]
    for keys, ans in rules:
        if any(k in q for k in keys):
            return ans
    return "Namaste beta! I am Budget Chachu. Ask me about budgeting, saving, SIP, gold, stocks, loans or emergency funds."


@app.route("/chat")
@login_required
def chat():
    return render_template("chat.html", prefill=request.args.get("q", "")[:200])


@app.post("/api/chat")
@login_required
def api_chat():
    msgs = (request.get_json(silent=True) or {}).get("messages", [])
    last = msgs[-1]["content"] if msgs else ""
    key = os.getenv("GEMINI_API_KEY")
    if not key:
        return jsonify(reply=offline_reply(last), offline=True)
    total, by = summary(current_user)
    ctx = (f"\nUser expense summary: total {total:.0f} INR, by category {by}, monthly budget {current_user.budget:.0f} INR. "
           f"Savings goals: {[(g.name, g.saved, g.target) for g in current_user.goals]}.")
    try:
        model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
        body = json.dumps({
            "systemInstruction": {"parts": [{"text": SYSTEM + ctx}]},
            "contents": [{"role": "user" if m["role"] == "user" else "model",
                          "parts": [{"text": str(m["content"])[:2000]}]} for m in msgs[-10:]]}).encode()
        req = urllib.request.Request(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            data=body, headers={"Content-Type": "application/json", "x-goog-api-key": key})
        with urllib.request.urlopen(req, timeout=25) as r:
            data = json.load(r)
        reply = "".join(p.get("text", "") for p in data["candidates"][0]["content"]["parts"])
        return jsonify(reply=reply)
    except Exception as e:
        app.logger.warning("Gemini failed: %s", e)
        return jsonify(reply=offline_reply(last), offline=True)


# ---------------- News ----------------
SITES = ("(site:economictimes.indiatimes.com OR site:livemint.com OR site:moneycontrol.com "
         "OR site:business-standard.com OR site:thehindubusinessline.com)")
TOPICS = {"stocks": "sensex nifty stock market", "gold": "gold price india", "crypto": "bitcoin crypto",
          "economy": "RBI inflation india economy", "savings": "mutual funds SIP savings"}
_news_cache = {}


@app.route("/news")
@login_required
def news():
    return render_template("news.html")


@app.route("/api/news")
@login_required
def api_news():
    cat = request.args.get("cat", "stocks")
    cat = cat if cat in TOPICS else "stocks"
    hit = _news_cache.get(cat)
    if hit and time.time() - hit[0] < 600:
        return jsonify(hit[1])
    try:
        q = urllib.parse.quote(f"{TOPICS[cat]} {SITES} when:2d")
        req = urllib.request.Request(f"https://news.google.com/rss/search?q={q}&hl=en-IN&gl=IN&ceid=IN:en",
                                     headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            root = ET.fromstring(r.read())
        items = []
        for it in root.iter("item"):
            title = it.findtext("title", "")
            head, _, src = title.rpartition(" - ")
            items.append({"title": head or title, "source": src or "News",
                          "link": it.findtext("link", "#"), "date": (it.findtext("pubDate") or "")[:22]})
            if len(items) == 12:
                break
        _news_cache[cat] = (time.time(), items)
        return jsonify(items)
    except Exception as e:
        app.logger.warning("News failed: %s", e)
        return jsonify([]), 502


if __name__ == "__main__":
    app.run(debug=True)
