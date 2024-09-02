import typing as t
import os
from pathlib import Path

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from glyfy.app import db
from glyfy.models import Glyph

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
auth = HTTPBasicAuth()

admin_heslo = os.getenv("ADMIN_HESLO")
if not admin_heslo:
    raise RuntimeError(
        "`ADMIN_HESLO` nie je v env premenných, nastav ho v súbore `.env`."
    )

USERS = {
    "admin": generate_password_hash(admin_heslo),
}

GLYPHS_PATH = Path(__file__).parent / "static" / "glyphs"


@auth.verify_password
def verify_password(username, password) -> t.Optional[str]:
    user = USERS.get(username)
    return username if user and check_password_hash(user, password) else None


@admin_bp.route("/glyphs")
@auth.login_required
def glyphs():
    page = request.args.get("page", 1, type=int)
    glyphs = db.paginate(db.select(Glyph).order_by(Glyph.unicode), page=page)

    return render_template("admin/glyphs.html", glyphs=glyphs)


@admin_bp.route("/glyphs/add", methods=["GET", "POST"])
@auth.login_required
def add_glyph():
    if request.method == "POST":
        glyph_id = request.form["glyph_id"]
        unicode = request.form["unicode"]
        glyph = Glyph(glyph_id=glyph_id, unicode=unicode)  # type: ignore

        svg_file = request.files["svg_file"]
        if svg_file and svg_file.filename:
            filepath = GLYPHS_PATH / f"{glyph_id}.svg"
            svg_file.save(filepath)

        db.session.add(glyph)
        db.session.commit()
        flash("Symbol bol úspešne pridaný", "success")
        return redirect(url_for("admin.glyphs"))

    return render_template("admin/add_glyph.html")


@admin_bp.route("/glyphs/edit/<int:glyph_id>", methods=["GET", "POST"])
@auth.login_required
def edit_glyph(glyph_id):
    glyph = db.get_or_404(Glyph, glyph_id)

    if request.method == "POST":
        glyph.glyph_id = request.form["glyph_id"]
        glyph.unicode = request.form["unicode"]

        svg_file = request.files["svg_file"]
        if svg_file and svg_file.filename:
            old_filepath = GLYPHS_PATH / f"{glyph.glyph_id}.svg"
            if os.path.exists(old_filepath):
                os.unlink(old_filepath)

            new_filepath = GLYPHS_PATH / f"{glyph.glyph_id}.svg"
            svg_file.save(new_filepath)

        db.session.commit()
        flash("Symbol bol úspešne upravený", "success")
        return redirect(url_for("admin.glyphs"))

    return render_template("admin/edit_glyph.html", glyph=glyph)


@admin_bp.route("/glyphs/delete/<int:glyph_id>", methods=["POST"])
@auth.login_required
def delete_glyph(glyph_id):
    glyph = db.get_or_404(Glyph, glyph_id)

    asset = GLYPHS_PATH / f"{glyph.glyph_id}.svg"
    if os.path.exists(asset):
        os.unlink(asset)

    db.session.delete(glyph)
    db.session.commit()

    flash("Symbol bol úspešne vymazaný", "success")
    return redirect(url_for("admin.glyphs"))
