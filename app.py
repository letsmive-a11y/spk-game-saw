# app.py
import os
from uuid import uuid4

from flask import Flask, render_template, request, redirect, url_for
from werkzeug.utils import secure_filename
from config import connect_db

app = Flask(__name__)
POSTER_UPLOAD_FOLDER = os.path.join(app.root_path, "static", "uploads", "posters")
ALLOWED_POSTER_EXTENSIONS = {"jpg", "jpeg", "png", "webp", "gif"}


def simpan_file_poster(file_poster):
    if not file_poster or file_poster.filename == "":
        return ""

    filename = secure_filename(file_poster.filename)
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if extension not in ALLOWED_POSTER_EXTENSIONS:
        return ""

    os.makedirs(POSTER_UPLOAD_FOLDER, exist_ok=True)
    nama_file = f"{uuid4().hex}_{filename}"
    file_poster.save(os.path.join(POSTER_UPLOAD_FOLDER, nama_file))
    return url_for("static", filename=f"uploads/posters/{nama_file}")


def hitung_hasil_ranking():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT id_game, nama_game, poster_url FROM game ORDER BY id_game ASC")
    games = cur.fetchall()

    cur.execute("SELECT id_kriteria, nama_kriteria, bobot, tipe FROM kriteria ORDER BY id_kriteria ASC")
    kriterias = cur.fetchall()

    cur.execute("SELECT id_game, id_kriteria, nilai FROM nilai")
    nilai_data = cur.fetchall()

    cur.close()
    conn.close()

    matrix = {}
    for game in games:
        matrix[game[0]] = {}

    for row in nilai_data:
        id_game = row[0]
        id_kriteria = row[1]
        nilai = float(row[2])
        matrix[id_game][id_kriteria] = nilai

    hasil_ranking = []

    for game in games:
        id_game = game[0]
        nama_game = game[1]
        poster_url = game[2]
        total = 0

        for kriteria in kriterias:
            id_kriteria = kriteria[0]
            bobot = float(kriteria[2])
            tipe = kriteria[3]
            nilai_asli = matrix[id_game].get(id_kriteria, 0)

            semua_nilai = []
            for g in games:
                nilai_per_game = matrix[g[0]].get(id_kriteria, 0)
                if nilai_per_game > 0:
                    semua_nilai.append(nilai_per_game)

            if len(semua_nilai) == 0 or nilai_asli == 0:
                normalisasi = 0
            elif tipe == "benefit":
                normalisasi = nilai_asli / max(semua_nilai)
            else:
                normalisasi = min(semua_nilai) / nilai_asli

            total += normalisasi * bobot

        hasil_ranking.append({
            "nama_game": nama_game,
            "poster_url": poster_url,
            "total": round(total, 4)
        })

    return sorted(hasil_ranking, key=lambda x: x["total"], reverse=True)


@app.route("/")
def index():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM game")
    total_film = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kriteria")
    total_kriteria = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM nilai")
    total_nilai = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kriteria WHERE tipe = 'benefit'")
    total_benefit = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM kriteria WHERE tipe = 'cost'")
    total_cost = cur.fetchone()[0]

    cur.execute("""
        SELECT nama_kriteria, bobot, tipe
        FROM kriteria
        ORDER BY id_kriteria ASC
    """)
    daftar_kriteria = cur.fetchall()

    cur.close()
    conn.close()

    kebutuhan_nilai = total_film * total_kriteria
    progres_nilai = 0
    if kebutuhan_nilai > 0:
        progres_nilai = round((total_nilai / kebutuhan_nilai) * 100)

    hasil_ranking = hitung_hasil_ranking()
    film_terbaik = hasil_ranking[0] if hasil_ranking else None

    return render_template(
        "index.html",
        total_film=total_film,
        total_kriteria=total_kriteria,
        total_nilai=total_nilai,
        total_benefit=total_benefit,
        total_cost=total_cost,
        kebutuhan_nilai=kebutuhan_nilai,
        progres_nilai=progres_nilai,
        film_terbaik=film_terbaik,
        film_lain=hasil_ranking[1:5],
        daftar_kriteria=daftar_kriteria
    )


@app.route("/film")
@app.route("/game")
def game():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        SELECT id_game, nama_game, genre, developer, poster_url
        FROM game
        ORDER BY id_game ASC
    """)
    data_game = cur.fetchall()
    cur.close()
    conn.close()
    return render_template("film.html", data_game=data_game)


@app.route("/tambah_film", methods=["POST"])
@app.route("/tambah_game", methods=["POST"])
def tambah_game():
    nama_game = request.form["nama_game"]
    genre = request.form["genre"]
    developer = request.form["developer"]
    poster_url = simpan_file_poster(request.files.get("poster_file"))
    if not poster_url:
        poster_url = request.form.get("poster_url", "")

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO game (nama_game, genre, developer, poster_url)
        VALUES (%s, %s, %s, %s)
    """, (nama_game, genre, developer, poster_url))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/film")


@app.route("/hapus_film/<int:id_game>")
@app.route("/hapus_game/<int:id_game>")
def hapus_game(id_game):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM game WHERE id_game = %s", (id_game,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect("/film")


@app.route("/kriteria")
def kriteria():
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM kriteria ORDER BY id_kriteria ASC")
    data_kriteria = cur.fetchall()
    cur.close()
    conn.close()

    return render_template("kriteria.html", data_kriteria=data_kriteria)


@app.route("/tambah_kriteria", methods=["POST"])
def tambah_kriteria():
    nama_kriteria = request.form["nama_kriteria"]
    bobot = float(request.form["bobot"]) / 100
    tipe = request.form["tipe"]

    conn = connect_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO kriteria (nama_kriteria, bobot, tipe)
        VALUES (%s, %s, %s)
    """, (nama_kriteria, bobot, tipe))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("kriteria"))

@app.route("/nilai")
def nilai():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM game ORDER BY id_game ASC")
    data_game = cur.fetchall()

    cur.execute("SELECT * FROM kriteria ORDER BY id_kriteria ASC")
    data_kriteria = cur.fetchall()

    cur.execute("""
        SELECT nilai.id_nilai, game.nama_game, kriteria.nama_kriteria, nilai.nilai
        FROM nilai
        JOIN game ON nilai.id_game = game.id_game
        JOIN kriteria ON nilai.id_kriteria = kriteria.id_kriteria
        ORDER BY nilai.id_nilai ASC
    """)
    data_nilai = cur.fetchall()

    cur.execute("SELECT id_game, id_kriteria, nilai FROM nilai")
    nilai_matrix = {}
    for id_game, id_kriteria, nilai_item in cur.fetchall():
        nilai_matrix[(id_game, id_kriteria)] = nilai_item

    cur.close()
    conn.close()

    return render_template(
        "nilai.html",
        data_game=data_game,
        data_kriteria=data_kriteria,
        data_nilai=data_nilai,
        nilai_matrix=nilai_matrix
    )


@app.route("/simpan_nilai", methods=["POST"])
def simpan_nilai():
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("SELECT id_game FROM game ORDER BY id_game ASC")
    data_game = cur.fetchall()

    cur.execute("SELECT id_kriteria FROM kriteria ORDER BY id_kriteria ASC")
    data_kriteria = cur.fetchall()

    for game in data_game:
        for kriteria in data_kriteria:
            id_game = game[0]
            id_kriteria = kriteria[0]
            nilai = request.form.get(f"nilai_{id_game}_{id_kriteria}", "").strip()

            cur.execute("""
                DELETE FROM nilai
                WHERE id_game = %s AND id_kriteria = %s
            """, (id_game, id_kriteria))

            if nilai:
                cur.execute("""
                    INSERT INTO nilai (id_game, id_kriteria, nilai)
                    VALUES (%s, %s, %s)
                """, (id_game, id_kriteria, nilai))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("nilai"))


@app.route("/tambah_nilai", methods=["POST"])
def tambah_nilai():
    id_game = request.form["id_game"]
    id_kriteria = request.form["id_kriteria"]
    nilai = request.form["nilai"]

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        DELETE FROM nilai 
        WHERE id_game = %s AND id_kriteria = %s
    """, (id_game, id_kriteria))

    cur.execute("""
        INSERT INTO nilai (id_game, id_kriteria, nilai)
        VALUES (%s, %s, %s)
    """, (id_game, id_kriteria, nilai))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("nilai"))


@app.route("/hapus_nilai/<int:id_nilai>")
def hapus_nilai(id_nilai):
    conn = connect_db()
    cur = conn.cursor()

    cur.execute("DELETE FROM nilai WHERE id_nilai = %s", (id_nilai,))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("nilai"))

@app.route("/update_film/<int:id_game>", methods=["POST"])
@app.route("/update_game/<int:id_game>", methods=["POST"])
def update_game(id_game):
    nama_game = request.form["nama_game"]
    genre = request.form["genre"]
    developer = request.form["developer"]
    poster_url = simpan_file_poster(request.files.get("poster_file"))
    if not poster_url:
        poster_url = request.form.get("poster_url", "")

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE game 
        SET nama_game = %s, genre = %s, developer = %s, poster_url = %s
        WHERE id_game = %s
    """, (nama_game, genre, developer, poster_url, id_game))

    conn.commit()
    cur.close()
    conn.close()

    return redirect("/film")

@app.route("/update_kriteria/<int:id_kriteria>", methods=["POST"])
def update_kriteria(id_kriteria):
    nama_kriteria = request.form["nama_kriteria"]
    bobot = float(request.form["bobot"]) / 100
    tipe = request.form["tipe"]

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE kriteria
        SET nama_kriteria = %s, bobot = %s, tipe = %s
        WHERE id_kriteria = %s
    """, (nama_kriteria, bobot, tipe, id_kriteria))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("kriteria"))

@app.route("/update_nilai/<int:id_nilai>", methods=["POST"])
def update_nilai(id_nilai):
    id_game = request.form["id_game"]
    id_kriteria = request.form["id_kriteria"]
    nilai = request.form["nilai"]

    conn = connect_db()
    cur = conn.cursor()

    cur.execute("""
        UPDATE nilai
        SET id_game = %s, id_kriteria = %s, nilai = %s
        WHERE id_nilai = %s
    """, (id_game, id_kriteria, nilai, id_nilai))

    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("nilai"))

@app.route("/hasil")
def hasil():
    hasil_ranking = hitung_hasil_ranking()
    return render_template("hasil.html", hasil_ranking=hasil_ranking)


@app.route("/hapus_kriteria/<int:id_kriteria>")
def hapus_kriteria(id_kriteria):
    conn = connect_db()
    cur = conn.cursor()
    cur.execute("DELETE FROM kriteria WHERE id_kriteria = %s", (id_kriteria,))
    conn.commit()
    cur.close()
    conn.close()

    return redirect(url_for("kriteria"))


if __name__ == "__main__":
    app.run(debug=True)
