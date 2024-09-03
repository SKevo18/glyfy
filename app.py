from glyfy.app import APP, DB

if __name__ == "__main__":
    with APP.app_context():
        DB.create_all()

    APP.run(debug=True, port=5051)
