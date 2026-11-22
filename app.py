import os
import socket

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Ma'lumotlar bazasi manzili muhit o'zgaruvchisidan olinadi.
# Lokal: SQLite (hech narsa o'rnatish shart emas).
# Bulutda: DATABASE_URL orqali PostgreSQL beriladi. Kod o'zgarmaydi.
db_url = os.getenv("DATABASE_URL", "sqlite:///tasks.db")
if db_url.startswith("postgres://"):  # ba'zi PaaS shunday manzil beradi
    db_url = db_url.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = db_url
db = SQLAlchemy(app)


class Task(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    done = db.Column(db.Boolean, default=False, nullable=False)

    def to_dict(self):
        return {"id": self.id, "title": self.title, "done": self.done}


with app.app_context():
    db.create_all()


@app.get("/")
def index():
    # hostname hisobotda skrinshot uchun qulay: ilova qaysi serverda ishlayotganini ko'rsatadi
    return jsonify(
        message="Task Manager API ishlayapti",
        server=socket.gethostname(),
        database=db.engine.dialect.name,
    )


@app.get("/health")
def health():
    return jsonify(status="ok")


@app.get("/tasks")
def list_tasks():
    tasks = Task.query.order_by(Task.id).all()
    return jsonify([t.to_dict() for t in tasks])


@app.post("/tasks")
def create_task():
    data = request.get_json(silent=True) or {}
    title = (data.get("title") or "").strip()
    if not title:
        return jsonify(error="title majburiy"), 400
    task = Task(title=title)
    db.session.add(task)
    db.session.commit()
    return jsonify(task.to_dict()), 201


@app.put("/tasks/<int:task_id>")
def update_task(task_id):
    task = db.get_or_404(Task, task_id)
    data = request.get_json(silent=True) or {}
    if "title" in data:
        task.title = data["title"]
    if "done" in data:
        task.done = bool(data["done"])
    db.session.commit()
    return jsonify(task.to_dict())


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    task = db.get_or_404(Task, task_id)
    db.session.delete(task)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 5000)), debug=True)
