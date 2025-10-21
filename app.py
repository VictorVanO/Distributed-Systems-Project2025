from flask import Flask, request, redirect, render_template_string

app = Flask(__name__)

contacts = [
    {"name": "Madame Dulont", "email": "alice@mail.com", "phone": "+32 475 11 22 33"},
    {"name": "Karim Amrani", "email": "karim@example.org", "phone": "+32 484 44 55 66"},
]

@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        phone = request.form["phone"]
        if name and email:
            contacts.append({"name": name, "email": email, "phone": phone})
        return redirect("/")

    html = """
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <title>Carnet de contacts</title>
        <style>
            body {
                background-color: #696969;
                color: #f1f1f1;
                font-family: Arial, sans-serif;
                padding: 40px;
                padding-top: 15px;
            }
            h1 {
                text-align: center;
                color: #ffffff;
                margin-bottom: 50px;
            }
            form {
                width: 60%;
                margin: 0 auto 30px auto;
                background: #4f4f4f;
                padding: 15px;
                border-radius: 6px;
                box-shadow: 0 0 10px rgba(0,0,0,0.4);
                text-align: center;
            }
            input {
                margin: 5px;
                padding: 10px;
                border: 1px solid #555;
                border-radius: 4px;
                background-color: #7b7b7b;
                color: #fff;
                width: 28%;
                font-size: 18px;
            }
            input::placeholder {
                color: #ddd;
            }
            input:focus {
                outline: none;
                border-color: #4CAF50;
                background-color: #8a8a8a;
            }
            button {
                margin-top: 15px;
                padding: 15px;
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 6px;
                cursor: pointer;
                font-size: 20px;
                font-weight: bold;
                width: 60%;
                transition: background-color 0.3s ease, transform 0.1s ease;
            }
            button:hover {
                background-color: #45a049;
                transform: scale(1.02);
            }
            table {
                width: 60%;
                margin: 0 auto;
                border-collapse: collapse;
                border-radius: 6px;
                overflow: hidden;
                box-shadow: 0 0 10px rgba(0,0,0,0.3);
            }
            th, td {
                border: 1px solid #555;
                padding: 12px;
                text-align: left;
            }
            th {
                background-color: #303030; /* plus foncé pour l'en-tête */
                color: #fff;
            }
            tr {
                background-color: #404040; /* couleur de base des lignes */
            }
            tr:hover {
                background-color: #505050;
            }
        </style>
    </head>
    <body>
        <h1>📇 Carnet de contacts</h1>

        <form method="POST">
            <input type="text" name="name" placeholder="Nom" required>
            <input type="email" name="email" placeholder="Email" required>
            <input type="text" name="phone" placeholder="Téléphone">
            <br>
            <button type="submit">Ajouter</button>
        </form>

        <table>
            <tr>
                <th>Nom</th>
                <th>Email</th>
                <th>Téléphone</th>
            </tr>
            {% for c in contacts %}
            <tr>
                <td>{{ c.name }}</td>
                <td>{{ c.email }}</td>
                <td>{{ c.phone }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html, contacts=contacts)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080, debug=True)
