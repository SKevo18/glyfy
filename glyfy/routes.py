from flask import Blueprint, render_template, request, redirect, flash, url_for
from glyfy.app import db
from glyfy.models import Glyph, Guess

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    glyphs = db.paginate(db.select(Glyph).order_by(Glyph.unicode), page=page)

    return render_template("index.html", glyphs=glyphs)


@bp.route("/glyph/<glyph_id>", methods=["GET", "POST"])
def view_glyph(glyph_id):
    glyph = db.one_or_404(db.select(Glyph).filter_by(glyph_id=glyph_id))

    if request.method == "POST":
        guess_text = request.form["guess"]
        glyph_id = request.form["glyph_id"]
        guess = Guess(glyph=glyph, guess_text=guess_text)

        db.session.add(guess)
        db.session.commit()

        flash("Your guess has been submitted!", "success")
        return redirect(url_for("main.view_glyph", glyph_id=glyph.glyph_id))

    return render_template("view_glyph.html", glyph=glyph)
