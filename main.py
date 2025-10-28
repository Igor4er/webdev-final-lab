from flask import Flask, render_template, request, redirect, url_for
from peewee import SqliteDatabase, Model, TextField, DateTimeField, OperationalError
import datetime
import os

db = SqliteDatabase(os.environ.get("DB_PATH", "db.sqlite3"), pragmas=[('journal_mode', 'wal')])

MSG = os.environ.get("MSG", "")

class Note(Model):
    content = TextField()
    timestamp = DateTimeField(default=datetime.datetime.now)
    remote_addr = TextField()

    class Meta:
        database = db

app = Flask(__name__)

@app.route("/")
def index(*args, **kwargs):
    print(request.headers)
    try:
        notes = Note.select().order_by(Note.timestamp.desc())
        return render_template("index.html", notes=notes, msg=MSG, remote_addr=request.remote_addr)
    except OperationalError as E:
        print(E)
        init_tables()
        if not kwargs.get("afterrun", False):
            return index(afterrun=True)
        else:
            raise E


@app.route("/add", methods=["POST"])
def add_note():
    content = request.form.get("content", "").strip()
    if content:
        Note.create(content=content, remote_addr=request.remote_addr)
    return redirect(url_for("index"))

@app.route("/delete/<int:note_id>")
def delete_note(note_id):
    note = Note.get_or_none(Note.id == note_id)
    if not note or note.remote_addr != request.remote_addr:
        return redirect(url_for("index"))
    Note.delete_by_id(note_id)
    return redirect(url_for("index"))

@app.route("/edit/<int:note_id>", methods=["GET", "POST"])
def edit_note(note_id):
    note = Note.get_or_none(Note.id == note_id)
    if not note or note.remote_addr != request.remote_addr:
        return redirect(url_for("index"))
    if request.method == "POST":
        new_content = request.form.get("content", "").strip()
        if new_content:
            note.content = new_content
            note.timestamp = datetime.datetime.now()
            note.save()
        return redirect(url_for("index"))
    return render_template("edit.html", note=note)


def init_tables():
    db.create_tables([Note])


if __name__ == "__main__":
    init_tables()
    app.run("127.0.0.1", 8043)
