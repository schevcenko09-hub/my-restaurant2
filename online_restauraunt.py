
import os

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)




app.config["SECRET_KEY"] = os.environ.get(
    "SECRET_KEY",
    "vybe-secret-key"
)



database_url = os.environ.get("DATABASE_URL")

if database_url:

    if database_url.startswith("postgres://"):
        database_url = database_url.replace(
            "postgres://",
            "postgresql://",
            1
        )

    app.config["SQLALCHEMY_DATABASE_URI"] = database_url

else:

    
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"


app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)




class User(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    username = db.Column(
        db.String(100),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    password = db.Column(
        db.String(255),
        nullable=False
    )




with app.app_context():
    db.create_all()




@app.route("/")
def index():

    return render_template(
        "index.html"
    )



@app.route("/menu")
def menu():

    return render_template(
        "menu.html"
    )




@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password2 = request.form.get("password2", "")

        # Перевірка полів
        if not name or not email or not password or not password2:
            return render_template(
                "register.html",
                error="Заповніть усі поля."
            )

        # Перевірка паролів
        if password != password2:
            return render_template(
                "register.html",
                error="Паролі не збігаються."
            )

        # Перевірка email
        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:
            return render_template(
                "register.html",
                error="Користувач з таким email вже існує."
            )

        # Створюємо хеш пароля
        hashed_password = generate_password_hash(password)

        # Створюємо користувача
        new_user = User(
            username=name,
            email=email,
            password=hashed_password
        )

        # Зберігаємо в базу
        db.session.add(new_user)
        db.session.commit()

        # Після реєстрації → сторінка входу
        return redirect(url_for("login"))

    return render_template("register.html")




@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):

            session["user_id"] = user.id
            session["username"] = user.username
            session["email"] = user.email

            return redirect(
                url_for("index")
            )

        return render_template(
            "login.html",
            error="Неправильний email або пароль."
        )

    return render_template("login.html")



@app.route("/profile")
def profile():

    

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )


    return render_template(
        "profile.html",
        username=session["username"],
        email=session["email"]
    )




@app.route("/logout")
def logout():

    
    session.clear()


    return redirect(
        url_for("index")
    )






if __name__ == "__main__":
    app.run(debug=True, port=5001)