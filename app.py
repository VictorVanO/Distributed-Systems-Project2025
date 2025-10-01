from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Distributed Systems Project 2025"

@app.route('/hello')
def hello():
    return 'Hello, World'

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)


# Start:
# docker build -t scalable-project-app:1.0 .
# docker compose up --build
