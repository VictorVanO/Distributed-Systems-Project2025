import os, hashlib, pymysql
from flask import Flask, request, redirect, render_template_string, abort

app = Flask(__name__)

# --- Connexions MySQL (simples, uniquement les primaires : s0 et s1) ---
def connect(uri: str):
    # URI sous forme: "user:pass@host:port/db"
    userpass, hostdb = uri.split("@", 1)
    user, pw = userpass.split(":", 1)
    hostport, db = hostdb.split("/", 1)
    host, port = hostport.split(":")
    return pymysql.connect(
        host=host, port=int(port), user=user, password=pw, database=db,
        autocommit=True, charset="utf8mb4", cursorclass=pymysql.cursors.Cursor
    )

DB_URI_S0_PRIMARY = os.getenv("DB_URI_S0_PRIMARY", "user:pass@mysql_s0_primary:3306/contactsdb")
DB_URI_S1_PRIMARY = os.getenv("DB_URI_S1_PRIMARY", "user:pass@mysql_s1_primary:3306/contactsdb")

DDL = """
CREATE TABLE IF NOT EXISTS contacts (
  id INT AUTO_INCREMENT PRIMARY KEY,
  name  VARCHAR(200) NOT NULL,
  email VARCHAR(255) NOT NULL,
  phone VARCHAR(50)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
"""

def init_db():
    # Assure la présence de la table sur les deux shards
    for uri in (DB_URI_S0_PRIMARY, DB_URI_S1_PRIMARY):
        try:
            con = connect(uri)
            with con.cursor() as cur:
                cur.execute(DDL)
            con.close()
            print(f"✅ Table 'contacts' prête sur {uri}")
        except Exception as e:
            print(f"⚠️ Erreur de connexion à {uri} :", e)

def shard_from_email(email: str) -> int:
    # 0 ou 1 selon hash(email)
    h = hashlib.sha256(email.encode("utf-8")).hexdigest()
    return int(h, 16) % 2

@app.route("/health")
def health():
    return "ok", 200

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name  = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        if not name or not email:
            abort(400, "name and email required")

        shard = shard_from_email(email)
        uri = DB_URI_S0_PRIMARY if shard == 0 else DB_URI_S1_PRIMARY
        con = connect(uri)
        with con.cursor() as cur:
            cur.execute("INSERT INTO contacts (name,email,phone) VALUES (%s,%s,%s)", (name, email, phone))
        con.close()
        return redirect("/")

    # GET : lire sur les deux shards et fusionner
    contacts = []
    for uri in (DB_URI_S0_PRIMARY, DB_URI_S1_PRIMARY):
        try:
            con = connect(uri)
            with con.cursor() as cur:
                cur.execute("SELECT name,email,phone FROM contacts ORDER BY id DESC LIMIT 100")
                for (n, e, p) in cur.fetchall():
                    contacts.append({"name": n, "email": e, "phone": p})
            con.close()
        except Exception:
            pass

    html = """
    <!DOCTYPE html><html lang="fr"><head><meta charset="UTF-8">
    <title>Carnet de contacts</title>
    <style>
    body{background:#696969;color:#f1f1f1;font-family:Arial;padding:24px}
    h1{text-align:center;margin:10px 0 24px}
    form,table{width:60%;margin:0 auto 24px;background:#4f4f4f;padding:16px;border-radius:6px}
    input{margin:6px;padding:10px;border:1px solid #555;border-radius:4px;background:#7b7b7b;color:#fff;width:28%}
    input::placeholder{color:#ffffff;opacity:0.8;}
    button{display:block;margin:12px auto 0;padding:12px 20px;background:#4CAF50;border:0;border-radius:6px;color:#fff;font-weight:700; width:60%; font-size:18px; cursor:pointer;}
    button:hover{ background:#45a049; transform:scale(1.03); }
    table{border-collapse:collapse}
    th,td{border:1px solid #555;padding:10px;text-align:left}
    th{background:#303030}
    tr{background:#404040}
    </style></head><body>
      <h1>📇 Carnet de contacts</h1>
      <form method="POST">
        <input name="name"  placeholder="Nom" required>
        <input name="email" placeholder="Email" required>
        <input name="phone" placeholder="Téléphone">
        <button type="submit">Ajouter</button>
      </form>
      <table>
        <tr><th>Nom</th><th>Email</th><th>Téléphone</th></tr>
        {% for c in contacts %}
          <tr><td>{{ c.name }}</td><td>{{ c.email }}</td><td>{{ c.phone }}</td></tr>
        {% endfor %}
      </table>
    </body></html>
    """
    return render_template_string(html, contacts=contacts)

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=8080, debug=True)
