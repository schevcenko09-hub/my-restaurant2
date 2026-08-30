

import os

from werkzeug.utils import secure_filename

from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash


app = Flask(__name__)



app.config["UPLOAD_FOLDER"] = os.path.join(
    app.static_folder,
    "images"
)

app.config["MAX_CONTENT_LENGTH"] = 5 * 1024 * 1024

ALLOWED_EXTENSIONS = {
    "png",
    "jpg",
    "jpeg",
    "webp"
}

os.makedirs(
    app.config["UPLOAD_FOLDER"],
    exist_ok=True
)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in ALLOWED_EXTENSIONS
    )




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


ADMIN_EMAIL = "schevcenko09@icloud.com"
ADMIN_PASSWORD = "RT0909cv67HJ"


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


class Admin(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
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


class Dish(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    name = db.Column(
        db.String(200),
        nullable=False
    )

    description = db.Column(
        db.Text,
        nullable=False
    )

    price = db.Column(
        db.Float,
        nullable=False
    )

    category = db.Column(
        db.String(100),
        nullable=False
    )

    image = db.Column(
        db.String(255),
        nullable=True
    )


class Order(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey("user.id"),
        nullable=False
    )

    total = db.Column(
        db.Float,
        nullable=False
    )

    status = db.Column(
        db.String(50),
        nullable=False,
        default="Нове"
    )

    created_at = db.Column(
        db.DateTime,
        nullable=False,
        default=db.func.now()
    )

    user = db.relationship(
        "User",
        backref=db.backref(
            "orders",
            lazy=True
        )
    )

    items = db.relationship(
        "OrderItem",
        backref="order",
        lazy=True,
        cascade="all, delete-orphan"
    )


class OrderItem(db.Model):
    id = db.Column(
        db.Integer,
        primary_key=True
    )

    order_id = db.Column(
        db.Integer,
        db.ForeignKey("order.id"),
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
        nullable=False
    )


with app.app_context():
    db.create_all()

    try:
        from sqlalchemy import inspect, text

        inspector = inspect(db.engine)

        dish_columns = [
            column["name"]
            for column in inspector.get_columns("dish")
        ]

        if "image" not in dish_columns:
            with db.engine.connect() as connection:
                connection.execute(
                    text(
                        "ALTER TABLE dish ADD COLUMN image VARCHAR(255)"
                    )
                )

                connection.commit()

    except Exception as e:
        print(
            "Помилка під час оновлення таблиці Dish:",
            e
        )



    existing_admin = Admin.query.filter_by(
        email=ADMIN_EMAIL
    ).first()

    if not existing_admin:
        new_admin = Admin(
            email=ADMIN_EMAIL,
            password=generate_password_hash(
                ADMIN_PASSWORD
            )
        )

        db.session.add(new_admin)
        db.session.commit()


initial_dishes = [
    {
        "name": "Брускета з томатами",
        "description": "Хрусткий хліб, томати, базилік та оливкова олія.",
        "price": 8,
        "category": "Закуски"
    },
    {
        "name": "Буррата з томатами",
        "description": "Ніжна буррата, свіжі томати та базилік.",
        "price": 11,
        "category": "Закуски"
    },
    {
        "name": "Карпачо з яловичини",
        "description": "Тонко нарізана яловичина, пармезан та рукола.",
        "price": 13,
        "category": "Закуски"
    },
    {
        "name": "Карбонара",
        "description": "Паста, бекон, пармезан та вершковий соус.",
        "price": 14,
        "category": "Паста"
    },
    {
        "name": "Куряча паста",
        "description": "Паста з куркою, грибами та вершковим соусом.",
        "price": 15,
        "category": "Паста"
    },
    {
        "name": "Трюфельна паста",
        "description": "Паста з трюфельним соусом та пармезаном.",
        "price": 16,
        "category": "Паста"
    },
    {
        "name": "Маргарита",
        "description": "Томатний соус, моцарела та базилік.",
        "price": 11,
        "category": "Піца"
    },
    {
        "name": "Пепероні",
        "description": "Томатний соус, моцарела та пепероні.",
        "price": 13,
        "category": "Піца"
    },
    {
        "name": "Чотири сира",
        "description": "Моцарела, пармезан, горгонзола та чедер.",
        "price": 14,
        "category": "Піца"
    },
    {
        "name": "Лосось з овочами",
        "description": "Запечений лосось, сезонні овочі та соус.",
        "price": 21,
        "category": "Основні страви"
    },
    {
        "name": "Куряче філе",
        "description": "Куряче філе, картопля та соус.",
        "price": 17,
        "category": "Основні страви"
    },
    {
        "name": "Яловичий стейк",
        "description": "Соковитий стейк з картоплею та овочами.",
        "price": 24,
        "category": "Основні страви"
    },
    {
        "name": "Класичний бургер",
        "description": "Яловичина, сир, салат, томати та соус.",
        "price": 14,
        "category": "Бургери"
    },
    {
        "name": "Чізбургер",
        "description": "Яловичина, подвійний сир та спеціальний соус.",
        "price": 15,
        "category": "Бургери"
    },
    {
        "name": "Курячий бургер",
        "description": "Хрустка курка, салат та соус.",
        "price": 14,
        "category": "Бургери"
    },
    {
        "name": "Тірамісу",
        "description": "Класичний італійський десерт.",
        "price": 7,
        "category": "Десерти"
    },
    {
        "name": "Чізкейк",
        "description": "Ніжний сирний десерт з ягідним соусом.",
        "price": 7,
        "category": "Десерти"
    },
    {
        "name": "Шоколадний фондан",
        "description": "Шоколадний фондан з ванільним морозивом.",
        "price": 8,
        "category": "Десерти"
    },
    {
        "name": "Кава",
        "description": "Еспресо, американо, капучино або латте.",
        "price": 3,
        "category": "Напої"
    },
    {
        "name": "Чай",
        "description": "Зелений, чорний або трав'яний чай.",
        "price": 2,
        "category": "Напої"
    },
    {
        "name": "Сік",
        "description": "Апельсиновий або яблучний сік.",
        "price": 4,
        "category": "Напої"
    },
    {
        "name": "Вода",
        "description": "Пляшкова або газована вода.",
        "price": 2,
        "category": "Напої"
    }
]


with app.app_context():
    if Dish.query.count() == 0:
        for data in initial_dishes:
            db.session.add(
                Dish(
                    name=data["name"],
                    description=data["description"],
                    price=data["price"],
                    category=data["category"]
                )
            )

        db.session.commit()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/menu")
def menu():
    dishes = Dish.query.order_by(Dish.id).all()

    categories = {}

    for dish in dishes:
        if dish.category not in categories:
            categories[dish.category] = []

        categories[dish.category].append(dish)

    return render_template(
        "menu.html",
        categories=categories
    )


@app.route("/dish/<int:dish_id>")
def dish(dish_id):
    selected_dish = Dish.query.get_or_404(dish_id)

    return render_template(
        "dish.html",
        dish=selected_dish
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

        new_user = User(
            username=name,
            email=email,
            password=generate_password_hash(password)
        )

        db.session.add(new_user)
        db.session.commit()

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

        # АВТОМАТИЧНИЙ ВХІД АДМІНІСТРАТОРА
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session.clear()

            session["is_admin"] = True
            session["admin_email"] = ADMIN_EMAIL

            return redirect(url_for("admin"))

        user = User.query.filter_by(
            email=email
        ).first()

        if user and check_password_hash(
            user.password,
            password
        ):
            session.clear()

            session["user_id"] = user.id
            session["username"] = user.username
            session["email"] = user.email
            session["is_admin"] = False

            return redirect(url_for("index"))

        return render_template(
            "login.html",
            error="Неправильний email або пароль."
        )

    return render_template("login.html")


@app.route("/profile")
def profile():
    if "user_id" not in session:
        return redirect(url_for("login"))

    return render_template(
        "profile.html",
        username=session["username"],
        email=session["email"]
    )


@app.route("/logout")
def logout():
    session.clear()

    return redirect(url_for("index"))


@app.route("/cart")
def cart():
    if "user_id" not in session:
        return redirect(url_for("login"))

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
        return redirect(url_for("login"))

    dish_id = request.form.get("dish_id")

    try:
        dish_id = int(dish_id)
    except (TypeError, ValueError):
        return "Неправильний ID страви", 400

    selected_dish = Dish.query.get(dish_id)

    if selected_dish is None:
        return "Страву не знайдено", 404

    item = CartItem.query.filter_by(
        user_id=session["user_id"],
        name=selected_dish.name
    ).first()

    if item:
        item.quantity += 1
    else:
        db.session.add(
            CartItem(
                user_id=session["user_id"],
                name=selected_dish.name,
                price=selected_dish.price,
                quantity=1
            )
        )

    db.session.commit()

    return redirect(url_for("cart"))


@app.route("/remove-from-cart/<int:item_id>", methods=["POST"])
def remove_from_cart(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    item = CartItem.query.filter_by(
        id=item_id,
        user_id=session["user_id"]
    ).first()

    if item:
        db.session.delete(item)
        db.session.commit()

    return redirect(url_for("cart"))


@app.route("/increase-cart/<int:item_id>", methods=["POST"])
def increase_cart(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    item = CartItem.query.filter_by(
        id=item_id,
        user_id=session["user_id"]
    ).first()

    if item:
        item.quantity += 1
        db.session.commit()

    return redirect(url_for("cart"))


@app.route("/decrease-cart/<int:item_id>", methods=["POST"])
def decrease_cart(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    item = CartItem.query.filter_by(
        id=item_id,
        user_id=session["user_id"]
    ).first()

    if item:
        if item.quantity > 1:
            item.quantity -= 1
        else:
            db.session.delete(item)

        db.session.commit()

    return redirect(url_for("cart"))


@app.route("/clear-cart", methods=["POST"])
def clear_cart():
    if "user_id" not in session:
        return redirect(url_for("login"))

    CartItem.query.filter_by(
        user_id=session["user_id"]
    ).delete()

    db.session.commit()

    return redirect(url_for("cart"))


@app.route("/create-order", methods=["POST"])
def create_order():
    if "user_id" not in session:
        return redirect(url_for("login"))

    items = CartItem.query.filter_by(
        user_id=session["user_id"]
    ).all()

    if not items:
        return redirect(url_for("cart"))

    total = sum(
        item.price * item.quantity
        for item in items
    )

    new_order = Order(
        user_id=session["user_id"],
        total=total,
        status="Нове"
    )

    db.session.add(new_order)
    db.session.flush()

    for item in items:
        db.session.add(
            OrderItem(
                order_id=new_order.id,
                name=item.name,
                price=item.price,
                quantity=item.quantity
            )
        )

    for item in items:
        db.session.delete(item)

    db.session.commit()

    return render_template(
        "order_success.html",
        order=new_order
    )


@app.route("/orders")
def orders():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_orders = Order.query.filter_by(
        user_id=session["user_id"]
    ).order_by(
        Order.created_at.desc()
    ).all()

    return render_template(
        "orders.html",
        orders=user_orders
    )



@app.route("/cancel-order/<int:order_id>", methods=["POST"])
def cancel_order(order_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    order = Order.query.filter_by(
        id=order_id,
        user_id=session["user_id"]
    ).first_or_404()

    if order.status == "Нове":
        order.status = "Скасовано"
        db.session.commit()

    return redirect(url_for("orders"))




# =========================
# АДМІН-ПАНЕЛЬ
# =========================

@app.route("/admin")
def admin():
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    dishes = Dish.query.order_by(
        Dish.category,
        Dish.id
    ).all()

    return render_template(
        "admin.html",
        dishes=dishes
    )


@app.route("/admin/orders")
def admin_orders():

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    orders = Order.query.order_by(
        Order.created_at.desc()
    ).all()

    return render_template(
        "admin_orders.html",
        orders=orders
    )




@app.route("/admin/add", methods=["GET", "POST"])
def admin_add():

    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        image = request.files.get("image")

        if not name or not description or not price or not category:
            return render_template(
                "admin_edit.html",
                error="Заповніть усі поля.",
                dish=None
            )

        try:
            price = float(price)

            if price < 0:
                raise ValueError

        except ValueError:
            return render_template(
                "admin_edit.html",
                error="Ціна повинна бути правильним числом.",
                dish=None
            )

        image_filename = None

        if image and image.filename:

            if not allowed_file(image.filename):
                return render_template(
                    "admin_edit.html",
                    error="Дозволені тільки JPG, JPEG, PNG та WEBP.",
                    dish=None
                )

            original_filename = secure_filename(
                image.filename
            )

            extension = original_filename.rsplit(
                ".",
                1
            )[1].lower()

            image_filename = (
                f"dish_{name.lower().replace(' ', '_')}_"
                f"{int(__import__('time').time())}."
                f"{extension}"
            )

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                image_filename
            )

            image.save(image_path)

        new_dish = Dish(
            name=name,
            description=description,
            price=price,
            category=category,
            image=image_filename
        )

        db.session.add(new_dish)
        db.session.commit()

        return redirect(
            url_for("admin")
        )

    return render_template(
        "admin_edit.html",
        dish=None
    )



@app.route(
    "/admin/edit/<int:dish_id>",
    methods=["GET", "POST"]
)
def admin_edit(dish_id):

    if not session.get("is_admin"):
        return redirect(
            url_for("admin_login")
        )

    selected_dish = Dish.query.get_or_404(
        dish_id
    )

    if request.method == "POST":

        name = request.form.get(
            "name",
            ""
        ).strip()

        description = request.form.get(
            "description",
            ""
        ).strip()

        price = request.form.get(
            "price",
            ""
        ).strip()

        category = request.form.get(
            "category",
            ""
        ).strip()

        image = request.files.get("image")

        if not name or not description or not price or not category:
            return render_template(
                "admin_edit.html",
                error="Заповніть усі поля.",
                dish=selected_dish
            )

        try:
            price = float(price)

            if price < 0:
                raise ValueError

        except ValueError:
            return render_template(
                "admin_edit.html",
                error="Ціна повинна бути правильним числом.",
                dish=selected_dish
            )

        selected_dish.name = name
        selected_dish.description = description
        selected_dish.price = price
        selected_dish.category = category

        # Якщо вибрали нове фото
        if image and image.filename:

            if not allowed_file(image.filename):
                return render_template(
                    "admin_edit.html",
                    error="Дозволені тільки JPG, JPEG, PNG та WEBP.",
                    dish=selected_dish
                )

            original_filename = secure_filename(
                image.filename
            )

            extension = original_filename.rsplit(
                ".",
                1
            )[1].lower()

            image_filename = (
                f"dish_{selected_dish.id}_"
                f"{int(__import__('time').time())}."
                f"{extension}"
            )

            image_path = os.path.join(
                app.config["UPLOAD_FOLDER"],
                image_filename
            )

            image.save(image_path)

            # Видаляємо старе фото
            if selected_dish.image:

                old_image_path = os.path.join(
                    app.config["UPLOAD_FOLDER"],
                    selected_dish.image
                )

                if os.path.exists(old_image_path):

                    try:
                        os.remove(
                            old_image_path
                        )

                    except OSError:
                        pass

            selected_dish.image = image_filename

        db.session.commit()

        return redirect(
            url_for("admin")
        )

    return render_template(
        "admin_edit.html",
        dish=selected_dish
    )


@app.route("/admin/delete/<int:dish_id>", methods=["POST"])
def admin_delete(dish_id):
    if not session.get("is_admin"):
        return redirect(url_for("login"))

    selected_dish = Dish.query.get_or_404(dish_id)

    db.session.delete(selected_dish)
    db.session.commit()

    return redirect(url_for("admin"))


@app.route("/admin/order/<int:order_id>/status", methods=["POST"])
def admin_order_status(order_id):
    if not session.get("is_admin"):
        return redirect(url_for("admin_login"))

    order = Order.query.get_or_404(order_id)

    status = request.form.get(
        "status",
        "Нове"
    )

    allowed_statuses = [
        "Нове",
        "Виконується",
        "Виконано",
        "Скасовано"
    ]

    if status in allowed_statuses:
        order.status = status
        db.session.commit()

    
    return redirect(url_for("admin_orders"))



@app.route("/admin/logout")
def admin_logout():
    session.pop("is_admin", None)
    session.pop("admin_email", None)

    return redirect(url_for("profile"))


if __name__ == "__main__":
    app.run(debug=True,port=5001)


