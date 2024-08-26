import os

from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

from glyfy.app import db
from glyfy.models import Glyph

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")
auth = HTTPBasicAuth()

admin_heslo = os.getenv("ADMIN_HESLO")
if not admin_heslo:
    raise RuntimeError("`ADMIN_HESLO` nie je v env premenných, nastav ho v súbore `.env`.")

USERS = {
    "admin": generate_password_hash(admin_heslo),
}

@auth.verify_password
def verify_password(username, password):
    user = USERS.get(username)

    if user and check_password_hash(user, password):
        return username


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
            filepath = os.path.join("glyfy/static/assets/glyphs", f"{glyph.glyph_id}.svg")
            svg_file.save(filepath)

        db.session.add(glyph)
        db.session.commit()
        flash("Glyph added successfully", "success")
        return redirect(url_for("admin.glyphs"))

    return render_template("admin/add_glyph.html")


@admin_bp.route("/glyphs/delete/<int:glyph_id>", methods=["POST"])
@auth.login_required
def delete_glyph(glyph_id):
    glyph = db.get_or_404(Glyph, glyph_id)

    asset = os.path.join("glyfy/static/assets/glyphs", f"{glyph.glyph_id}.svg")
    if os.path.exists(asset):
        os.unlink(asset)

    db.session.delete(glyph)
    db.session.commit()
    flash("Glyph deleted successfully", "success")
    return redirect(url_for("admin.glyphs"))
