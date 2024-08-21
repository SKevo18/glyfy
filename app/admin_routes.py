import os

from flask import Blueprint, render_template, redirect, url_for, request, flash
from app import db
from app.models import Glyph

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")


@admin_bp.route("/glyphs")
def glyphs():
    page = request.args.get("page", 1, type=int)
    glyphs = Glyph.query.paginate(page=page, per_page=20)
    return render_template("admin/glyphs.html", glyphs=glyphs)


@admin_bp.route("/glyphs/add", methods=["GET", "POST"])
def add_glyph():
    if request.method == "POST":
        glyph_id = request.form["glyph_id"]
        unicode = request.form["unicode"]
        glyph = Glyph(glyph_id=glyph_id, unicode=unicode)  # type: ignore

        svg_file = request.files["svg_file"]
        if svg_file and svg_file.filename:
            filepath = os.path.join("app/static/assets/glyphs", f"{glyph.glyph_id}.svg")
            svg_file.save(filepath)

        db.session.add(glyph)
        db.session.commit()
        flash("Glyph added successfully", "success")
        return redirect(url_for("admin.glyphs"))

    return render_template("admin/add_glyph.html")


@admin_bp.route("/glyphs/delete/<int:glyph_id>", methods=["POST"])
def delete_glyph(glyph_id):
    glyph = Glyph.query.get_or_404(glyph_id)

    asset = os.path.join("app/static/assets/glyphs", f"{glyph.glyph_id}.svg")
    if os.path.exists(asset):
        os.unlink(asset)

    db.session.delete(glyph)
    db.session.commit()
    flash("Glyph deleted successfully", "success")
    return redirect(url_for("admin.glyphs"))
