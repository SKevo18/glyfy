import typing as t
import os
import re

from pathlib import Path
from sqlalchemy import case, func
from sqlalchemy.exc import IntegrityError

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from glyfy.app import DB
from glyfy.models import Glyph, Guess, BannedIP, Vote
from glyfy.utils import get_client_ip

ADMIN_BP = Blueprint("admin", __name__, url_prefix="/admin")
AUTH = HTTPBasicAuth()

GLYPHS_PATH = Path(__file__).parent / "static" / "glyphs"

admin_heslo = os.getenv("ADMIN_HESLO")
if not admin_heslo:
    raise RuntimeError(
        "`ADMIN_HESLO` nie je v env premenných, nastav ho v súbore `.env`."
    )

users = {
    "admin": generate_password_hash(admin_heslo),
}


@AUTH.verify_password
def verify_password(username, password) -> t.Optional[str]:
    user = users.get(username)
    return username if user and check_password_hash(user, password) else None


@ADMIN_BP.route("/")
def redirect_admin():
    return redirect(url_for("admin.glyphs"))


@ADMIN_BP.route("/glyphs")
@AUTH.login_required
def glyphs():
    page = request.args.get("page", 1, type=int)
    glyphs = DB.paginate(DB.select(Glyph).order_by(Glyph.unicode), page=page)
    return render_template("admin/glyphs.html", glyphs=glyphs)


@ADMIN_BP.route("/glyphs/add", methods=["GET", "POST"])
@AUTH.login_required
def add_glyph():
    if request.method == "POST":
        glyph_id = request.form["glyph_id"]
        unicode = request.form["unicode"]

        if not re.match(r"^[a-zA-Z0-9]+$", glyph_id):
            flash("ID glyfu môže obsahovať iba alfanumerické znaky.", "error")
            return render_template("admin/add_glyph.html")

        try:
            unicode_value = int(unicode)
            if unicode_value <= 0:
                raise ValueError
        except ValueError:
            flash("Unicode hodnota musí byť kladné celé číslo väčšie ako 0.", "error")
            return render_template("admin/add_glyph.html")

        glyph = Glyph(glyph_id=glyph_id, unicode=unicode_value)

        svg_file = request.files["svg_file"]
        if svg_file and svg_file.filename:
            filepath = GLYPHS_PATH / f"{glyph_id}.svg"
            svg_file.save(filepath)

        try:
            DB.session.add(glyph)
            DB.session.commit()

            flash("Symbol bol úspešne pridaný", "success")
            return redirect(url_for("admin.glyphs"))

        except IntegrityError as e:
            DB.session.rollback()

            if "glyph_id" in str(e.orig):
                flash("Chyba: ID glyfu už existuje. Prosím, zvoľte iné ID.", "error")
            elif "unicode" in str(e.orig):
                flash(
                    "Chyba: Unicode hodnota už existuje. Prosím, zvoľte inú hodnotu.",
                    "error",
                )
            else:
                flash("Chyba pri pridávaní glyfu. Skúste to znova.", "error")

    return render_template("admin/add_glyph.html")


@ADMIN_BP.route("/glyphs/edit/<int:glyph_id>", methods=["GET", "POST"])
@AUTH.login_required
def edit_glyph(glyph_id):
    glyph = DB.get_or_404(Glyph, glyph_id)

    if request.method == "POST":
        glyph.glyph_id = request.form["glyph_id"]

        try:
            unicode = int(request.form["unicode"])
            if unicode <= 0:
                raise ValueError
        except ValueError:
            flash("Unicode hodnota musí byť kladné celé číslo väčšie ako 0.", "error")
            return render_template("admin/edit_glyph.html", glyph=glyph)

        glyph.unicode = unicode

        svg_file = request.files["svg_file"]
        if svg_file and svg_file.filename:
            old_filepath = GLYPHS_PATH / f"{request.form["glyph_id"]}.svg"
            if old_filepath.exists():
                old_filepath.unlink()

            new_filepath = GLYPHS_PATH / f"{glyph.glyph_id}.svg"
            svg_file.save(new_filepath)

        try:
            DB.session.commit()

            flash("Symbol bol úspešne upravený", "success")
            return redirect(url_for("admin.glyphs"))

        except IntegrityError as e:
            DB.session.rollback()

            if "glyph_id" in str(e.orig):
                flash("Chyba: ID glyfu už existuje. Prosím, zvoľte iné ID.", "error")
            elif "unicode" in str(e.orig):
                flash(
                    "Chyba: Unicode hodnota už existuje. Prosím, zvoľte inú hodnotu.",
                    "error",
                )
            else:
                flash("Chyba pri úprave glyfu. Skúste to znova.", "error")

    return render_template("admin/edit_glyph.html", glyph=glyph)


@ADMIN_BP.route("/glyphs/<int:glyph_id>/guesses")
@AUTH.login_required
def view_guesses(glyph_id):
    glyph = DB.get_or_404(Glyph, glyph_id)
    page = request.args.get("page", 1, type=int)

    guesses = DB.paginate(
        DB.select(Guess)
        .filter_by(glyph_id=glyph.id)
        .outerjoin(Vote)
        .group_by(Guess.id)
        .order_by(func.sum(case((Vote.is_upvote, 1), else_=-1)).desc().nulls_last())
        .order_by(Guess.timestamp.desc()),
        page=page,
        per_page=20,
    )

    return render_template("admin/view_guesses.html", glyph=glyph, guesses=guesses)


@ADMIN_BP.route("/glyphs/<int:glyph_id>/toggle_delete", methods=["POST"])
@AUTH.login_required
def toggle_delete_glyph(glyph_id):
    toggle_delete_or_remove(Glyph, glyph_id)

    return redirect(url_for("admin.glyphs"))


@ADMIN_BP.route("/glyphs/<int:glyph_id>/permanent_delete", methods=["POST"])
@AUTH.login_required
def permanent_delete_glyph(glyph_id):
    if toggle_delete_or_remove(Glyph, glyph_id, permanent=True):
        return redirect(url_for("admin.glyphs"))

    return redirect(url_for("admin.view_guesses", glyph_id=glyph_id))


@ADMIN_BP.route("/guesses/<int:guess_id>/toggle_delete", methods=["POST"])
@AUTH.login_required
def toggle_delete_guess(guess_id):
    toggle_delete_or_remove(Guess, guess_id)

    return redirect(request.referrer)


@ADMIN_BP.route("/guesses/<int:guess_id>/permanent_delete", methods=["POST"])
@AUTH.login_required
def permanent_delete_guess(guess_id):
    if toggle_delete_or_remove(Guess, guess_id, permanent=True):
        return redirect(request.referrer)

    return redirect(request.referrer)


@ADMIN_BP.route("/banned_ips", methods=["GET", "POST"])
@AUTH.login_required
def banned_ips():
    if request.method == "POST":
        ip_address = request.form["ip_address"]
        banned_ip = BannedIP(ip_address=ip_address)

        DB.session.add(banned_ip)
        try:
            DB.session.commit()
            flash("IP adresa bola úspešne zakázaná", "success")
        except IntegrityError:
            DB.session.rollback()
            flash("Táto IP adresa je už zakázaná", "error")

    page = request.args.get("page", 1, type=int)
    banned_ips = DB.paginate(DB.select(BannedIP), page=page, per_page=20)

    return render_template(
        "admin/banned_ips.html", banned_ips=banned_ips, current_ip=get_client_ip()
    )


@ADMIN_BP.route("/banned_ips/<int:banned_ip_id>/delete", methods=["POST"])
@AUTH.login_required
def delete_banned_ip(banned_ip_id):
    banned_ip = DB.get_or_404(BannedIP, banned_ip_id)

    DB.session.delete(banned_ip)
    DB.session.commit()

    flash("IP adresa bola úspešne odstránená zo zoznamu zakázaných", "success")
    return redirect(url_for("admin.banned_ips"))


def toggle_delete_or_remove(model, item_id, permanent=False):
    item = DB.get_or_404(model, item_id)

    if permanent:
        if not item.is_deleted:
            flash(
                "Nemôžete trvalo vymazať položku, ktorá nie je označená ako vymazaná.",
                "error",
            )
            return False

        DB.session.delete(item)
        flash("Položka bola trvalo vymazaná", "success")
    else:
        item.is_deleted = not item.is_deleted
        action = "označená ako vymazaná" if item.is_deleted else "obnovená"

        flash(f"Položka bola {action}", "success")

    DB.session.commit()
    return True
