from datetime import datetime
from glyfy.app import db


class Glyph(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    glyph_id = db.Column(db.String(64), unique=True, nullable=False)
    unicode = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def __repr__(self):
        return f"<Glyph {self.glyph_id}>"


class Meaning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    phrase = db.Column(db.String(256), nullable=False)
    glyph_id = db.Column(db.Integer, db.ForeignKey("glyph.id"), nullable=False)
    glyph = db.relationship("Glyph", backref=db.backref("meanings", lazy=True))

    def __repr__(self):
        return f"<Meaning {self.phrase}>"


class Guess(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    glyph_id = db.Column(db.Integer, db.ForeignKey("glyph.id"), nullable=False)
    guess_text = db.Column(db.String(256), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.now)

    glyph = db.relationship("Glyph", backref=db.backref("guesses", lazy=True))

    def __repr__(self):
        return f"<Guess {self.guess_text}>"
