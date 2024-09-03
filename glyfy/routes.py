import re

from flask import Blueprint, render_template, request, redirect, flash, url_for, abort
from unidecode import unidecode

from glyfy.app import db
from glyfy.models import Glyph, Guess, BannedIP, Vote

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

            existing_guess = db.session.execute(
                db.select(Guess).filter_by(
                    glyph_id=glyph.id, guess_text=normalized_guess
                )
            ).scalar_one_or_none()

            if existing_guess:
                existing_vote = db.session.execute(
                    db.select(Vote).filter_by(
                        guess_id=existing_guess.id, ip_address=ip_address
                    )
                ).scalar_one_or_none()

                if not existing_vote:
                    new_vote = Vote(
                        guess_id=existing_guess.id,
                        ip_address=ip_address,
                        is_upvote=True,
                    )

                    db.session.add(new_vote)
                    db.session.commit()
                    flash("Existujúci odhad bol automaticky upvote-nutý!", "success")
                else:
                    flash("Tento odhad už existuje a vy ste ho už hodnotili.", "info")
            else:
                guess = Guess(
                    glyph=glyph, guess_text=normalized_guess, ip_address=ip_address
                )
                db.session.add(guess)
                db.session.commit()

                new_vote = Vote(
                    guess_id=guess.id, ip_address=ip_address, is_upvote=True
                )
                db.session.add(new_vote)
                db.session.commit()

                flash("Váš odhad bol odoslaný a automaticky upvote-nutý!", "success")

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


@bp.route("/guess/<int:guess_id>/vote", methods=["POST"])
def vote_guess(guess_id):
    guess = db.get_or_404(Guess, guess_id)
    ip_address = get_client_ip()
    is_upvote = request.form.get("vote_type") == "upvote"

    existing_vote = db.session.execute(
        db.select(Vote).filter_by(guess_id=guess_id, ip_address=ip_address)
    ).scalar_one_or_none()

    if existing_vote:
        if existing_vote.is_upvote == is_upvote:
            db.session.delete(existing_vote)
            flash("Váš hlas bol odstránený", "success")
        else:
            existing_vote.is_upvote = is_upvote
            flash("Váš hlas bol zmenený", "success")
    else:
        new_vote = Vote(guess_id=guess_id, ip_address=ip_address, is_upvote=is_upvote)
        db.session.add(new_vote)
        flash("Váš hlas bol zaznamenaný", "success")

    db.session.commit()
    return redirect(url_for("main.view_glyph", glyph_id=guess.glyph.glyph_id))


def normalize_guess(text):
    text = text.lower()
    text = text.strip()
    text = unidecode(text)
    text = re.sub(r"\s+", " ", text)
    text = re.sub(r"[^ a-z0-9]", "", text)

    return text
