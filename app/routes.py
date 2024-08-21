from flask import Blueprint, render_template, request, redirect, flash, url_for
from app import db
from app.models import Glyph, Guess

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    glyphs = Glyph.query.paginate()
    return render_template("index.html", glyphs=glyphs)


@bp.route("/glyph/<glyph_id>", methods=["GET", "POST"])
def view_glyph(glyph_id):
    glyph = Glyph.query.filter_by(glyph_id=glyph_id).first_or_404()

    if request.method == "POST":
        guess_text = request.form["guess"]
        riddle_id = request.form["riddle_id"]
        guess = Guess(riddle_id=riddle_id, guess_text=guess_text) # type: ignore
        db.session.add(guess)
        db.session.commit()
        flash("Your guess has been submitted!", "success")
        return redirect(url_for("main.view_glyph", glyph_id=glyph_id))

    return render_template("view_glyph.html", glyph=glyph)
