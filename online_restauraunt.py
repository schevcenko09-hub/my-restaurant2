
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


class CartItem(db.Model):

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    quantity = db.Column(
        db.Integer,
        nullable=False,
        default=1
    )


with app.app_context():
    db.create_all()


dishes = {

    "bruschetta": {
        "name": "Брускета з томатами",
        "description": "Хрусткий хліб, томати, базилік та оливкова олія.",
        "price": 8
    },

    "burrata": {
        "name": "Буррата з томатами",
        "description": "Ніжна буррата, свіжі томати та базилік.",
        "price": 11
    },

    "carpaccio": {
        "name": "Карпачо з яловичини",
        "description": "Тонко нарізана яловичина, пармезан та рукола.",
        "price": 13
    },

    "carbonara": {
        "name": "Карбонара",
        "description": "Паста, бекон, пармезан та вершковий соус.",
        "price": 14
    },

    "chicken_pasta": {
        "name": "Куряча паста",
        "description": "Паста з куркою, грибами та вершковим соусом.",
        "price": 15
    },

    "truffle_pasta": {
        "name": "Трюфельна паста",
        "description": "Паста з трюфельним соусом та пармезаном.",
        "price": 16
    },

    "margherita": {
        "name": "Маргарита",
        "description": "Томатний соус, моцарела та базилік.",
        "price": 11
    },

    "pepperoni": {
        "name": "Пепероні",
        "description": "Томатний соус, моцарела та пепероні.",
        "price": 13
    },

    "four_cheese": {
        "name": "Чотири сира",
        "description": "Моцарела, пармезан, горгонзола та чедер.",
        "price": 14
    },

    "salmon": {
        "name": "Лосось з овочами",
        "description": "Запечений лосось, сезонні овочі та соус.",
        "price": 21
    },

    "chicken": {
        "name": "Куряче філе",
        "description": "Куряче філе, картопля та соус.",
        "price": 17
    },

    "steak": {
        "name": "Яловичий стейк",
        "description": "Соковитий стейк з картоплею та овочами.",
        "price": 24
    },

    "classic_burger": {
        "name": "Класичний бургер",
        "description": "Яловичина, сир, салат, томати та соус.",
        "price": 14
    },

    "cheeseburger": {
        "name": "Чізбургер",
        "description": "Яловичина, подвійний сир та спеціальний соус.",
        "price": 15
    },

    "chicken_burger": {
        "name": "Курячий бургер",
        "description": "Хрустка курка, салат та соус.",
        "price": 14
    },

    "tiramisu": {
        "name": "Тірамісу",
        "description": "Класичний італійський десерт.",
        "price": 7
    },

    "cheesecake": {
        "name": "Чізкейк",
        "description": "Ніжний сирний десерт з ягідним соусом.",
        "price": 7
    },

    "fondant": {
        "name": "Шоколадний фондан",
        "description": "Шоколадний фондан з ванільним морозивом.",
        "price": 8
    },

    "coffee": {
        "name": "Кава",
        "description": "Еспресо, американо, капучино або латте.",
        "price": 3
    },

    "tea": {
        "name": "Чай",
        "description": "Зелений, чорний або трав'яний чай.",
        "price": 2
    },

    "juice": {
        "name": "Сік",
        "description": "Апельсиновий або яблучний сік.",
        "price": 4
    },

    "water": {
        "name": "Вода",
        "description": "Пляшкова або газована вода.",
        "price": 2
    }
}


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


@app.route("/dish/<dish_id>")
def dish(dish_id):

    selected_dish = dishes.get(dish_id)

    if selected_dish is None:
        return "Страву не знайдено", 404

    return render_template(
        "dish.html",
        dish=selected_dish,
        dish_id=dish_id
    )


@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        password2 = request.form.get(
            "password2",
            ""
        )

        if not name or not email or not password or not password2:

            return render_template(
                "register.html",
                error="Заповніть усі поля."
            )

        if password != password2:

            return render_template(
                "register.html",
                error="Паролі не збігаються."
            )

        existing_user = User.query.filter_by(
            email=email
        ).first()

        if existing_user:

            return render_template(
                "register.html",
                error="Користувач з таким email вже існує."
            )

        hashed_password = generate_password_hash(
            password
        )

        new_user = User(
            username=name,
            email=email,
            password=hashed_password
        )

        db.session.add(
            new_user
        )

        db.session.commit()

        return redirect(
            url_for("login")
        )

    return render_template(
        "register.html"
    )


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

    return render_template(
        "login.html"
    )


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


@app.route("/cart")
def cart():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    items = CartItem.query.filter_by(
        user_id=session["user_id"]
    ).all()

    total = sum(
        item.price * item.quantity
        for item in items
    )

    return render_template(
        "cart.html",
        items=items,
        total=total
    )


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    dish_id = request.form.get(
        "dish_id"
    )

    selected_dish = dishes.get(
        dish_id
    )

    if selected_dish is None:

        return "Страву не знайдено", 404

    item = CartItem.query.filter_by(
        user_id=session["user_id"],
        name=selected_dish["name"]
    ).first()

    if item:

        item.quantity += 1

    else:

        item = CartItem(
            user_id=session["user_id"],
            name=selected_dish["name"],
            price=selected_dish["price"],
            quantity=1
        )

        db.session.add(
            item
        )

    db.session.commit()

    return redirect(
        url_for("cart")
    )


@app.route(
    "/remove-from-cart/<int:item_id>",
    methods=["POST"]
)
def remove_from_cart(item_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    item = CartItem.query.filter_by(
        id=item_id,
        user_id=session["user_id"]
    ).first()

    if item:

        db.session.delete(
            item
        )

        db.session.commit()

    return redirect(
        url_for("cart")
    )


@app.route(
    "/increase-cart/<int:item_id>",
    methods=["POST"]
)
def increase_cart(item_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    item = CartItem.query.filter_by(
        id=item_id,
        user_id=session["user_id"]
    ).first()

    if item:

        item.quantity += 1

        db.session.commit()

    return redirect(
        url_for("cart")
    )


@app.route(
    "/decrease-cart/<int:item_id>",
    methods=["POST"]
)
def decrease_cart(item_id):

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    item = CartItem.query.filter_by(
        id=item_id,
        user_id=session["user_id"]
    ).first()

    if item:

        if item.quantity > 1:

            item.quantity -= 1

        else:

            db.session.delete(
                item
            )

        db.session.commit()

    return redirect(
        url_for("cart")
    )


@app.route(
    "/clear-cart",
    methods=["POST"]
)
def clear_cart():

    if "user_id" not in session:

        return redirect(
            url_for("login")
        )

    CartItem.query.filter_by(
        user_id=session["user_id"]
    ).delete()

    db.session.commit()

    return redirect(
        url_for("cart")
    )


if __name__ == "__main__":
    app.run(debug=True,port=5001)

