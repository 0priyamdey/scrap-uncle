import os
import json

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from db import db
from helpers import login_required, admin_required

load_dotenv()

app = Flask(__name__)

# ─── Configuration ─────────────────────────────────────────
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-change-me")
app.config["SESSION_PERMANENT"] = False


# ─── User Routes ───────────────────────────────────────────

@app.route("/")
@login_required
def index():
    name = db.execute("SELECT name FROM users WHERE id=?", session['user_id'])
    orders = db.execute("""
            SELECT
            orders.order_id,
            orders.pickup_date,
            orders.time_slot,
            orders.estimated_weight,
            orders.status,
            orders.created_at,
            order_items.category
            FROM orders
            LEFT JOIN order_items ON orders.order_id = order_items.order_id
            WHERE orders.user_id = ? AND (status = ? OR status = ?)""", session["user_id"], "Pending", "Scheduled")

    analytics = db.execute("""
    SELECT order_items.category, COALESCE(SUM(order_items.weight_collected), 0) AS cat_weight, COALESCE(SUM(order_items.total_amount), 0) AS cat_total
    FROM orders
    LEFT JOIN order_items ON order_items.order_id =  orders.order_id
    WHERE user_id = ? AND status IN ('Completed','Cancelled')
    GROUP BY order_items.category""", session["user_id"])

    total_scrap = 0
    total_amount = 0
    for data in analytics:
        total_scrap += float(data['cat_weight'])
        total_amount += float(data['cat_total'])
    return render_template("index.html", name=name[0]['name'].split(), orders=orders, total_scrap=round(total_scrap, 2), total_amount=round(total_amount, 2), analytics=json.dumps(analytics))


@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        phone = request.form.get("phone")
        password = request.form.get("password")
        remember = request.form.get("remember")
        if not phone or not password:
            flash('Please enter your login credentials', 'info')
            return redirect("/login")
        row = db.execute("SELECT * FROM users WHERE phone = ?", phone)
        if len(row) != 1 or not check_password_hash(row[0]["hash"],password):
            flash('Incorrect password', 'danger')
            return redirect("/login")

        session["user_id"] = row[0]["id"]
        if remember:
            session.permanent = True
        return redirect("/")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name")
        phone = request.form.get("phone")
        email = request.form.get("email")
        state = request.form.get("state")
        city = request.form.get("city")
        pin = request.form.get("pin")
        address = request.form.get("address")
        password = request.form.get("password")
        confirmPassword = request.form.get("confirmPassword")

        if not name or not phone or not state or not city or not pin or not address or not password or not confirmPassword:
            flash('Some important fields are misssing', 'info')
            return redirect("/register")
        if len(pin)!=6 or not pin.isdigit() or int(pin)<0:
            flash('Not a valid pincode', 'danger')
            return redirect("/register")
        if len(phone)!=10 or not phone.isdigit() or int(phone)<0:
            flash('Not a valid phone number', 'danger')
            return redirect("/register")
        if password != confirmPassword:
            flash('Password do not match', 'info')
            return redirect("/register")

        try:
            if db.is_postgres:
                user_id = db.execute(
                    "INSERT INTO users(name, phone, email, hash) VALUES(?, ?, ?, ?) RETURNING id",
                    name, phone, email if email else None, generate_password_hash(password))
                db.execute(
                    "INSERT INTO user_addresses (id, state, city, pincode, address) VALUES(?, ?, ?, ?, ?)",
                    user_id, state, city, pin, address)
            else:
                user_id = db.execute(
                    "INSERT INTO users(name, phone, email, hash) VALUES(?, ?, ?, ?)",
                    name, phone, email if email else None, generate_password_hash(password))
                db.execute(
                    "INSERT INTO user_addresses (id, state, city, pincode, address) VALUES(?, ?, ?, ?, ?)",
                    user_id, state, city, pin, address)
        except Exception:
            flash('Phone number already registered', 'danger')
            return redirect("/register")
        return redirect("/login")

    return render_template("/register.html")


@app.route("/orders")
@login_required
def orders():
    orders = db.execute("""
        SELECT
        orders.order_id,
        orders.pickup_date,
        orders.time_slot,
        orders.vehicle_type,
        orders.estimated_weight,
        orders.status,
        orders.created_at,
        order_items.category,
        order_items.rate_per_kg,
        order_items.weight_collected,
        order_items.total_amount,
        order_items.setteled_date
        FROM orders
        LEFT JOIN order_items ON orders.order_id = order_items.order_id
        WHERE orders.user_id = ? AND (status = ? OR status = ?)""", session["user_id"], "Pending", "Scheduled")

    pastorders = db.execute("""
        SELECT
        orders.order_id,
        orders.pickup_date,
        orders.time_slot,
        orders.vehicle_type,
        orders.estimated_weight,
        orders.status,
        orders.created_at,
        order_items.category,
        order_items.rate_per_kg,
        order_items.weight_collected,
        order_items.total_amount,
        order_items.setteled_date
        FROM orders
        LEFT JOIN order_items ON orders.order_id = order_items.order_id
        WHERE orders.user_id = ? AND (orders.status = ? OR orders.status = ?)""", session["user_id"], "Completed", "Cancelled")
    return render_template("orders.html", orders=orders, pastorders=pastorders)


@app.route("/placeorder", methods=["GET", "POST"])
@login_required
def addorder():
    if request.method == "POST":
        category = request.form.get("category")
        weight = request.form.get("weight")
        pickup_date = request.form.get("pickup_date")
        time_slot = request.form.get("time_slot")
        vehicle = request.form.get("vehicle")
        address = request.form.get("address")

        if not category or not weight or not pickup_date or not time_slot or not vehicle or not address:
            flash('Some mandatory fields are missing', 'info')
            return render_template("/placeorder.html")

        if db.is_postgres:
            orderID = db.execute(
                "INSERT INTO orders (user_id, pickup_date, time_slot, vehicle_type, estimated_weight, aid) VALUES (?, ?, ?, ?, ?, ?) RETURNING order_id",
                session["user_id"], pickup_date, time_slot, vehicle, weight, address)
        else:
            orderID = db.execute(
                "INSERT INTO orders (user_id, pickup_date, time_slot, vehicle_type, estimated_weight, aid) VALUES (?, ?, ?, ?, ?, ?)",
                session["user_id"], pickup_date, time_slot, vehicle, weight, address)
        db.execute("INSERT INTO order_items (order_id, category) VALUES (?, ?)", orderID, category)
        flash('Order placed successfully','success')
        return redirect("/")

    user_address = db.execute("SELECT aid, state, city, pincode, address FROM user_addresses WHERE id = ?", session["user_id"])
    return render_template("placeorder.html", addresses=user_address)

@app.route("/profile")
@login_required
def profile():
    details = db.execute('SELECT * FROM users WHERE id = ?', session['user_id'])
    addresses = db.execute('SELECT * FROM user_addresses LEFT JOIN users ON users.id = user_addresses.id WHERE users.id = ?', session['user_id'])
    return render_template("profile.html", details=details[0], addresses=addresses)

@app.route("/profile/update", methods=['POST'])
@login_required
def update():
    name = request.form.get("name")
    email = request.form.get("email")
    newPassword = request.form.get("newPassword")
    curPassword = request.form.get("curPassword")

    row = db.execute("SELECT * FROM users WHERE id = ?", session['user_id'])

    if not curPassword or not len(row)==1 or not check_password_hash(row[0]["hash"],curPassword):
        flash('Invalid password', 'danger')
        return redirect("/profile")
    if name:
        db.execute('UPDATE users SET name = ? WHERE id = ?', name, session['user_id'])
    if email:
        db.execute('UPDATE users SET email = ? WHERE id = ?', email, session['user_id'])
    if newPassword:
        db.execute('UPDATE users SET hash = ? WHERE id = ?', generate_password_hash(newPassword), session['user_id'])

    return redirect("/profile")

@app.route("/profile/addaddress", methods=['POST'])
@login_required
def addaddress():
    if request.method == "POST":
        state = request.form.get("state")
        city = request.form.get("city")
        pin = request.form.get("pincode")
        address = request.form.get("address")

        if not state or not city or not pin or not address:
            flash('Please provide all the credentials', 'info')
            return redirect("/profile")
        if len(pin)!=6 or not pin.isdigit() or int(pin)<0:
            flash('Please enter a valid pincode', 'info')
            return redirect("/profile")

        db.execute("INSERT INTO user_addresses (id, state, city, pincode, address) VALUES(?, ?, ?, ?, ?)",
                    session['user_id'], state, city, pin, address)
    return redirect("/profile")

@app.route("/profile/address/delete", methods=['POST'])
@login_required
def delete():
    db.execute('DELETE FROM user_addresses WHERE aid = ?', request.form.get('aid'))
    return redirect('/profile')

@app.route("/contacts")
def contacts():
    return render_template("contacts.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


# ─── Admin Routes ──────────────────────────────────────────

@app.route('/admin/login', methods=['GET','POST'])
def admin_login():
    if request.method == 'POST':
        adminid = request.form.get('adminid')
        password = request.form.get('password')

        if not adminid or not password:
            flash('Please enter your login credentials', 'info')
            return redirect("/admin/login")
        row = db.execute("SELECT * FROM admin_creds WHERE name = ?", adminid)
        if len(row) != 1 or not check_password_hash(row[0]["hash"],password):
            flash('Incorrect password', 'danger')
            return redirect("/admin/login")

        session["admin_id"] = row[0]["admin_id"]
        return redirect("/admin")
    return render_template('adminlogin.html')

@app.route('/admin', methods=['GET','POST'])
@admin_required
def admin():
    if request.method=='POST':
        order = request.form.get('order_id')
        status = request.form.get('status')
        category = request.form.get('category')
        rates = request.form.get('rate')
        weight = request.form.get('weight')
        totalAmount = request.form.get('totalAmount')
        settledAt = request.form.get('settledAt')
        if status:
            db.execute('UPDATE orders SET status = ? WHERE order_id = ?', status.capitalize(), order)
        if category:
            db.execute('UPDATE order_items SET category = ? WHERE order_id = ?', category, order)
        if rates and weight:
            db.execute('UPDATE order_items SET rate_per_kg = ?, weight_collected = ? WHERE order_id = ?', rates, weight, order)
        if totalAmount:
            db.execute('UPDATE order_items SET total_amount = ? WHERE order_id = ?', totalAmount, order)
        if settledAt:
            db.execute('UPDATE order_items SET setteled_date = ? WHERE order_id = ?', settledAt, order)
        return redirect('/admin')

    orders = db.execute("""
            SELECT orders.order_id, users.name, users.phone, users.email, orders.pickup_date, orders.time_slot, orders.vehicle_type, orders.estimated_weight,
            orders.status, orders.created_at, order_items.category, order_items.rate_per_kg, order_items.weight_collected, order_items.total_amount,
            order_items.setteled_date, user_addresses.city, user_addresses.state, user_addresses.address, user_addresses.pincode
            from orders
            join users on orders.user_id = users.id
            join order_items on order_items.order_id = orders.order_id
            join user_addresses on orders.aid = user_addresses.aid
            ORDER BY orders.order_id DESC""")
    return render_template('admin.html', orders=orders)

@app.route('/users')
@admin_required
def users():
    users = db.execute("""
        SELECT id, name, phone, email
        FROM users
        ORDER BY name DESC""")
    return render_template("users.html", users=users)

@app.route('/adminlogout')
def admin_logout():
    session.pop("admin_id", None)
    return redirect('/admin/login')


# ─── Entry Point ───────────────────────────────────────────

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
