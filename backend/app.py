from flask import Flask, render_template, redirect, url_for, request, session, flash
import mysql.connector
import os
from werkzeug.utils import secure_filename

app = Flask(__name__,
            static_folder='C:/Users/LUCIFER/OneDrive/Desktop/E-commerce/frontend/static',
            template_folder='C:/Users/LUCIFER/OneDrive/Desktop/E-commerce/frontend/templates')

app.secret_key = 'secure_2002'

# MySQL Database connection
db = mysql.connector.connect(
    host="localhost",
    user="root",
    password="2002",
    database="ecommerce_db",
    connection_timeout=3600  # Set timeout to 1 hour
)

cursor = db.cursor()

# Directory to save uploaded images
UPLOAD_FOLDER = 'C:/Users/LUCIFER/OneDrive/Desktop/E-commerce/frontend/static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cursor.execute("SELECT * FROM users WHERE email=%s AND password=%s AND role=%s", (email, password, role))
        user = cursor.fetchone()

        if user:
            session['user_id'] = user[0]
            session['name'] = user[1]
            session['email'] = email
            session['role'] = role
            if role == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid credentials')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        cursor.execute("INSERT INTO users (name, email, password, role) VALUES (%s, %s, %s, %s)",
                       (name, email, password, role))
        db.commit()
        flash('Registration successful!')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('name', None)
    session.pop('email', None)
    session.pop('role', None)
    flash('You have been logged out.')
    return redirect(url_for('index'))

@app.route('/admin/dashboard')
def admin_dashboard():
    if 'role' in session and session['role'] == 'admin':
        return render_template('admin_dashboard.html')
    else:
        flash('Access denied!')
        return redirect(url_for('login'))

@app.route('/add_product', methods=['GET', 'POST'])
def add_product():
    if 'role' in session and session['role'] == 'admin':
        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']
            price = request.form['price']
            image = request.files['image']

            # Save the image and get the filename
            image_filename = secure_filename(image.filename)
            image.save(os.path.join(app.config['UPLOAD_FOLDER'], image_filename))

            cursor.execute("INSERT INTO products (name, description, price, image) VALUES (%s, %s, %s, %s)",
                           (name, description, price, image_filename))
            db.commit()
            flash('Product added successfully!')
            return redirect(url_for('admin_dashboard'))

        return render_template('add_product.html')
    else:
        flash('Access denied!')
        return redirect(url_for('login'))

@app.route('/view_products')
def view_products():
    cursor.execute("SELECT id, name, description, price, image FROM products")
    products = cursor.fetchall()
    products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3], 'image': row[4]} for row in products]
    return render_template('view_products.html', products=products)

@app.route('/user/dashboard')
def user_dashboard():
    if 'role' in session and session['role'] == 'user':
        cursor.execute("SELECT id, name, description, price, image FROM products")
        products = cursor.fetchall()
        products = [{'id': row[0], 'name': row[1], 'description': row[2], 'price': row[3], 'image': row[4]} for row in products]
        return render_template('user_dashboard.html', products=products)
    else:
        flash('Access denied!')
        return redirect(url_for('login'))

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    if 'user_id' in session:
        cursor.execute("SELECT id, name, price, image FROM products WHERE id=%s", (product_id,))
        product = cursor.fetchone()

        if product:
            # Store cart in session
            if 'cart' not in session:
                session['cart'] = []
            session['cart'].append({
                'id': product[0],
                'name': product[1],
                'price': product[2],
                'image': product[3]  # Add image to the cart
            })
            flash('Product added to cart!')
        else:
            flash('Product not found!')
    else:
        flash('You need to be logged in to add products to the cart.')

    return redirect(url_for('user_dashboard'))


@app.route('/cart')
def cart():
    if 'cart' in session:
        return render_template('cart.html', cart=session['cart'])
    else:
        flash('Your cart is empty.')
        return redirect(url_for('user_dashboard'))

@app.route('/view_orders')
def view_orders():
    if 'user_id' in session:
        cursor.execute("SELECT * FROM orders WHERE user_id=%s", (session['user_id'],))
        orders = cursor.fetchall()
        return render_template('view_orders.html', orders=orders)
    else:
        flash('You need to log in to view orders.')
        return redirect(url_for('login'))
    

@app.route('/checkout')
def checkout():
    if 'user_id' in session:
        # Implement checkout logic here
        return render_template('checkout.html')
    else:
        flash('You need to be logged in to checkout.')
        return redirect(url_for('login'))
    
@app.route('/remove_from_cart/<int:product_id>', methods=['POST'])
def remove_from_cart(product_id):
    if 'cart' in session:
        # Filter out the product to remove
        session['cart'] = [item for item in session['cart'] if item['id'] != product_id]
        flash('Product removed from cart!')
    else:
        flash('Your cart is empty.')

    return redirect(url_for('cart'))


@app.route('/buy_now/<int:product_id>', methods=['POST'])
def buy_now(product_id):
    if 'user_id' in session:
        cursor.execute("SELECT id, name, price FROM products WHERE id=%s", (product_id,))
        product = cursor.fetchone()

        if product:
            # Handle checkout logic here (e.g., create an order)
            # For example, let's just add a dummy order
            cursor.execute("INSERT INTO orders (user_id, product_id, quantity) VALUES (%s, %s, %s)",
                           (session['user_id'], product_id, 1))
            db.commit()
            flash('Product purchased!')
            # Optionally, redirect to a confirmation or order summary page
            return redirect(url_for('order_confirmation'))  # Adjust as needed
        else:
            flash('Product not found!')
    else:
        flash('You need to log in to complete the purchase.')

    return redirect(url_for('cart'))


@app.route('/order_confirmation')
def order_confirmation():
    if 'user_id' in session:
        return render_template('order_confirmation.html')
    else:
        flash('You need to log in to view your order confirmation.')
        return redirect(url_for('login'))




if __name__ == '__main__':
    app.run(debug=True)
