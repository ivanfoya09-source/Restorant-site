import os
from dotenv import load_dotenv

from flask import Flask, flash, render_template, redirect, request, url_for
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_caching import Cache

from models import db, User, Menu, Reservation, Order, OrderItem
from forms import SignUpForm, SignInForm, ReservationForm

load_dotenv()

app = Flask(__name__)


app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("SQLALCHEMY_DATABASE_URI")
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

if not app.config["SQLALCHEMY_DATABASE_URI"]:
    raise RuntimeError(" Немає SQLALCHEMY_DATABASE_URI")

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "sign_in"

cache = Cache(app, config={
    "CACHE_TYPE": "SimpleCache",
    "CACHE_DEFAULT_TIMEOUT": 60
})


# with app.app_context():
#     db.drop_all()
#     db.create_all()

@login_manager.user_loader
def user_loader(user_id):
    return db.session.get(User, user_id)


@app.route("/sign_up/", methods=["GET", "POST"])
def sign_up():
    form = SignUpForm()

    if form.validate_on_submit():
        if User.query.filter_by(username=form.username.data).first():
            flash("Користувач вже існує.")
            return redirect(url_for("sign_up"))

        user = User(
            username=form.username.data,
            email=form.email.data or None,
            fullname=form.fullname.data or None
        )

        user.set_password(form.password.data)

        db.session.add(user)
        db.session.commit()

        flash("Реєстрація успішна.")
        return redirect(url_for("sign_in"))

    return render_template("sign_up.html", form=form)


@app.route("/sign_in/", methods=["GET", "POST"])
def sign_in():
    form = SignInForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user and user.verify_password(form.password.data):
            login_user(user)
            flash("Ви увійшли.")
            return redirect(url_for("index"))

        flash("Невірний логін або пароль.")
        return redirect(url_for("sign_in"))

    return render_template("sign_in.html", form=form)


@app.get("/logout/")
@login_required
def logout():
    logout_user()
    flash("Ви вийшли з акаунту.")
    return redirect(url_for("sign_in"))


@app.get("/")
@login_required
def index():
    category = request.args.get("category")

    if category:
        menu = Menu.query.filter_by(category=category).all()
    else:
        menu = Menu.query.all()

    return render_template("index.html", menu=menu, category=category)


@app.route("/reserve/", methods=["GET", "POST"])
@login_required
def reserve():
    form = ReservationForm()
    menu = Menu.query.all()

    if form.validate_on_submit():
        reservation = Reservation(
            time_start=form.time.data,
            table=form.table.data,
            user_id=current_user.id
        )

        db.session.add(reservation)
        db.session.commit()

        cache.clear()

        flash("Стіл заброньовано.")
        return redirect(url_for("index"))

    return render_template("reserve.html", form=form, menu=menu)


from flask import session

@app.get("/add_to_cart/<menu_id>")
@login_required
def add_to_cart(menu_id):
    item = db.session.get(Menu, menu_id)

    if not item:
        flash("Такої страви не існує")
        return redirect(url_for("index"))

    cart = session.get("cart", {})
    cart[menu_id] = cart.get(menu_id, 0) + 1
    session["cart"] = cart

    flash(f"➕ Додано: {item.name}", "success")
    return redirect(url_for("cart"))


@app.get("/cart/")
@login_required
def cart():
    cart = session.get("cart", {})

    if not cart:
        flash("🛒 Кошик порожній", "info")

    items = []

    for menu_id, qty in cart.items():
        item = db.session.get(Menu, menu_id)
        if item:
            items.append((item, qty))

    return render_template("cart.html", items=items)


@app.get("/order/")
@login_required
def create_order():
    cart: dict[str, int] = session.get("cart", {})

    if not cart:
        flash("Кошик пустий")
        return redirect(url_for("index"))

    order = Order(
        user_id=current_user.id,
        reservation_id=None
    )

    db.session.add(order)

    for menu_id, qty in cart.items():
        item = db.session.get(Menu, menu_id)

        if not item:
            continue

        order_item = OrderItem(
            menu_id=menu_id,
            order_id=order.id,
            quantity=qty
        )
        db.session.add(order_item)

    db.session.commit()

    session["cart"] = {}
    cache.clear()

    flash("Замовлення створено")
    return redirect(url_for("index"))
    

with app.app_context():
    db.create_all()

    if not Menu.query.first():
        items = [
            # 🍕 ПІЦА
            Menu(name="Піца Маргарита", price=180, picture="images/pizza.jpg", category="pizza"),
            Menu(name="Піца Пепероні", price=210, picture="images/pizza.jpg", category="pizza"),
            Menu(name="Піца 4 сири", price=230, picture="images/pizza.jpg", category="pizza"),

            # 🍔 БУРГЕРИ
            Menu(name="Класичний бургер", price=150, picture="images/burger.jpg", category="burger"),
            Menu(name="Чізбургер", price=170, picture="images/burger.jpg", category="burger"),
            Menu(name="Дабл бургер", price=220, picture="images/burger.jpg", category="burger"),

            # 🥗 САЛАТИ
            Menu(name="Салат Цезар", price=120, picture="images/salad.jpg", category="salad"),
            Menu(name="Грецький салат", price=110, picture="images/salad.jpg", category="salad"),

            # 🍝 ПАСТА
            Menu(name="Паста Карбонара", price=190, picture="images/pasta.jpg", category="pasta"),
            Menu(name="Паста Болоньєзе", price=200, picture="images/pasta.jpg", category="pasta"),

            # 🍜 СУПИ
            Menu(name="Борщ", price=90, picture="images/soup.jpg", category="soup"),
            Menu(name="Крем-суп грибний", price=100, picture="images/soup.jpg", category="soup"),

            # 🍟 ЗАКУСКИ
            Menu(name="Картопля фрі", price=80, picture="images/fries.jpg", category="snack"),
            Menu(name="Нагетси", price=120, picture="images/nuggets.jpg", category="snack"),

            # 🥤 НАПОЇ
            Menu(name="Кола", price=50, picture="images/drink.jpg", category="drink"),
            Menu(name="Сік апельсиновий", price=60, picture="images/drink.jpg", category="drink"),
            Menu(name="Вода", price=30, picture="images/drink.jpg", category="drink"),
        ]

        db.session.add_all(items)
        db.session.commit()


@app.get("/remove_from_cart/<menu_id>")
@login_required
def remove_from_cart(menu_id):
    cart = session.get("cart", {})

    if menu_id in cart:
        cart[menu_id] -= 1
        if cart[menu_id] <= 0:
            del cart[menu_id]

    session["cart"] = cart
    return redirect(url_for("cart"))


@app.get("/delete_from_cart/<menu_id>")
@login_required
def delete_from_cart(menu_id):
    cart = session.get("cart", {})

    if menu_id in cart:
        del cart[menu_id]

    session["cart"] = cart
    flash("❌ Товар видалено", "info")

    return redirect(url_for("cart"))

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            email="admin@test.com",
            fullname="Admin",
            is_admin=True
        )
        admin.set_password("admin123")

        db.session.add(admin)
        db.session.commit()

    # меню
    if not Menu.query.first():
        items = [
            Menu(name="Піца Маргарита", price=180, picture="images/pizza.jpg", category="pizza"),
            Menu(name="Піца Пепероні", price=210, picture="images/pizza.jpg", category="pizza"),
            Menu(name="Піца 4 сири", price=230, picture="images/pizza.jpg", category="pizza"),
        ]

        db.session.add_all(items)
        db.session.commit()


from flask import abort

def admin_required():
    if not current_user.is_authenticated or not current_user.is_admin:
        abort(403)


@app.get("/admin/delete_menu/<menu_id>")
@login_required
def delete_menu(menu_id):
    admin_required()

    item = db.session.get(Menu, menu_id)

    if item:
        db.session.delete(item)
        db.session.commit()
        flash("Видалено")

    return redirect(url_for("index"))


@app.route("/admin/add_menu", methods=["GET", "POST"])
@login_required
def add_menu():
    admin_required()

    if request.method == "POST":
        name = request.form.get("name")
        price = request.form.get("price")
        category = request.form.get("category")
        picture = request.form.get("picture")

        if not name or not price:
            flash("Заповни всі поля")
            return redirect(url_for("add_menu"))

        item = Menu(
            name=name,
            price=float(price),
            category=category,
            picture=picture
        )

        db.session.add(item)
        db.session.commit()

        flash("Страву додано ✔")
        return redirect(url_for("index"))

    return render_template("admin_add.html")


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)