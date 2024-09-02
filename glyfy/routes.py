import re

from flask import Blueprint, render_template, request, redirect, flash, url_for, abort
from unidecode import unidecode

from glyfy.app import db
from glyfy.models import Glyph, Guess, BannedIP

from glyfy.utils import get_client_ip

bp = Blueprint("main", __name__)


@bp.route("/")
def index():
    page = request.args.get("page", 1, type=int)
    glyphs = db.paginate(
        db.select(Glyph).filter_by(is_deleted=False).order_by(Glyph.unicode), page=page
    )

    return render_template("index.html", glyphs=glyphs)


@bp.route("/glyph/<glyph_id>", methods=["GET", "POST"])
def view_glyph(glyph_id):
    glyph = db.one_or_404(
        db.select(Glyph).filter_by(glyph_id=glyph_id, is_deleted=False)
    )
    page = request.args.get("page", 1, type=int)

    if request.method == "POST":
        ip_address = get_client_ip()
        banned_ip = db.session.execute(
            db.select(BannedIP).filter_by(ip_address=ip_address)
        ).first()

        if banned_ip:
            flash("Vaša IP adresa je zakázaná. Nemôžete odosielať odhady.", "error")
        else:
            guess_text = request.form["guess"]
            normalized_guess = normalize_guess(guess_text)

            guess = Guess(
                glyph=glyph, guess_text=normalized_guess, ip_address=ip_address
            )
            db.session.add(guess)
            db.session.commit()

            flash("Váš odhad bol odoslaný!", "success")

        return redirect(url_for("main.view_glyph", glyph_id=glyph.glyph_id))

    guesses = db.paginate(
        db.select(Guess)
        .filter_by(glyph_id=glyph.id, is_deleted=False)
        .order_by(Guess.timestamp.desc()),
        page=page,
        per_page=20,
    )

    return render_template(
        "glyph.html", glyph=glyph, guesses=guesses, user_ip=get_client_ip()
    )


@bp.route("/guess/<int:guess_id>/delete", methods=["POST"])
def delete_guess(guess_id):
    guess = db.get_or_404(Guess, guess_id)
    if guess.ip_address != get_client_ip():
        abort(403)

    guess.is_deleted = True
    db.session.commit()

    flash("Váš odhad bol zmazaný", "success")
    return redirect(url_for("main.view_glyph", glyph_id=guess.glyph.glyph_id))


def normalize_guess(text):
    text = text.lower()
    text = unidecode(text)
    text = re.sub(r"[^ a-z0-9]", "", text)

    return text
