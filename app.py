from flask import Flask, render_template, request, redirect, url_for, session, jsonify, flash, abort
import razorpay
from flask_oauthlib.client import OAuth
from firebase_admin import db
import requests
import traceback
import json
import os
from datetime import datetime
from credential import RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, REDIRECT_URI, firebase_admin

UPLOAD_FOLDER = 'static/images'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}


app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.secret_key = "supersecretkey"


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS




client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))


ref_user = db.reference("/user")  
ref_order = db.reference("/order")  
ref_menu = db.reference("/menu") 

@app.route('/login')
def login():
    # Redirect to Google's OAuth 2.0 server
    return redirect(f'https://accounts.google.com/o/oauth2/auth?response_type=code&client_id={GOOGLE_CLIENT_ID}&redirect_uri={REDIRECT_URI}&scope=email profile')



@app.route('/callback')
def callback():
    # Get the authorization code from the request
    code = request.args.get('code')

    # Exchange the authorization code for an access token
    token_response = requests.post('https://oauth2.googleapis.com/token', data={
        'code': code,
        'client_id': GOOGLE_CLIENT_ID,
        'client_secret': GOOGLE_CLIENT_SECRET,
        'redirect_uri': REDIRECT_URI,
        'grant_type': 'authorization_code'
    })

    token_json = token_response.json()
    access_token = token_json.get('access_token')

    # Use the access token to get user information
    user_info_response = requests.get('https://www.googleapis.com/oauth2/v2/userinfo', headers={
        'Authorization': f'Bearer {access_token}'
    })

    user_info = user_info_response.json()
    # Check if email ends with @charusat.edu.in
    if 'email' in user_info and user_info['email'] == ['mr.shashansoni@gmail.com','jigarsarda.ee@charusat.ac.in','vaibhavipatel.cse@charusat.ac.in']:
        session['admin'] = {
            'uid': user_info.get('id', ''),  # Use get() to avoid KeyError
            'email': user_info.get('email', ''),  # Default to empty string if missing
            'displayName': user_info.get('name', 'Unknown'),  # Provide a fallback
            'profilePic': user_info.get('picture', '')  # Default to empty string if missing
        }
        return redirect(url_for('admin'))
    else:
        # Ensure all keys exist before storing user data in session
        session['user'] = {
            'uid': user_info.get('id', ''),  # Use get() to avoid KeyError
            'email': user_info.get('email', ''),  # Default to empty string if missing
            'displayName': user_info.get('name', 'Unknown'),  # Provide a fallback
            'profilePic': user_info.get('picture', '')  # Default to empty string if missing
        }
        
        # Store user data only if 'uid' exists
        if session['user']['uid']:
            ref_user.child(session['user']['uid']).set(session['user'])

        return redirect(url_for('home'))

@app.route('/logout')
def logout():
    session.pop('user', None)
    session.pop('admin', None)
    flash("You have been logged out.")
    return redirect(url_for('index'))



# Group items store-wise
def group_menu_by_store(menu_items):
    store_menu = {}
    for item in menu_items:
        store = item["store"]
        if store not in store_menu:
            store_menu[store] = []
        store_menu[store].append(item)
    return store_menu

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/home')
def home():
    if 'user' in session or 'admin' in session:
        return render_template("home.html")
    return render_template("index.html")
    

@app.route('/admin')
def admin():
    # Fetch data for the admin panel
    if 'admin' in session:
        users = ref_user.get() or {}
        orders = ref_order.get() or {}
        menu_items = ref_menu.get() or {}

        total_orders = len(orders)
        total_revenue = sum(order.get('total_price', 0) for order in orders.values())
        active_users = len(users)

        return render_template(
            "admin.html",
            users=users.values(),
            orders=orders.values(),
            menu_items=menu_items,
            total_orders=total_orders,
            total_revenue=total_revenue,
            active_users=active_users
        )
    abort(404)  

@app.route('/user_management')
def user_management():
    if 'admin' in session:
        users = ref_user.get() or {}
        return render_template("user_management.html", users=users.values())
    abort(404)  

@app.route('/order_management')
def order_management():
    if 'admin' in session:
        orders = ref_order.get() or {}
        return render_template("order_management.html", orders=orders.values())
    abort(404)  


@app.route('/menu_management')
def menu_management():
    if 'admin' in session:
        menu_items = ref_menu.get() or {}
        return render_template("menu_management.html", menu_items=menu_items)
    abort(404)  


@app.route('/delete_user/<user_id>')
def delete_user(user_id):
    ref_user.child(user_id).delete()
    flash("User  deleted successfully!")
    return redirect(url_for('user_management'))

@app.route('/delete_order/<order_id>')
def delete_order(order_id):
    ref_order.child(order_id).delete()
    flash("Order deleted successfully!")
    return redirect(url_for('order_management'))

@app.route('/delete_menu_item/<item_id>')
def delete_menu_item(item_id):
    ref_menu.child(item_id).delete()
    flash("Menu item deleted successfully!")
    return redirect(url_for('menu_management'))

def get_menu_from_firebase():
    # Reference to the 'menu' path in Realtime Database
    menu_ref = db.reference("menu")
    menu_data = menu_ref.get()  # This fetches the data stored under 'menu'

    # Check if the data exists and is in the expected format (a list)
    if menu_data is None:
        print("No menu data found in Firebase.")
        return []

    if not isinstance(menu_data, list):
        print(f"Unexpected data format in Firebase: {type(menu_data)}")
        return []

    # Since menu_data is a list, we can directly return it
    return menu_data


@app.route('/add_menu_item', methods=['POST'])
def add_menu_item():
    
    item_name = request.form['item_name']
    price = request.form['price']
    category = request.form['category']
    store = request.form['store']
    
    # Handle the image upload
    image = request.files['image']
    image_filename = image.filename  # Get a secure file name
    image_path = os.path.join('static', 'images', image_filename)
    image.save(os.path.join(app.root_path, image))  # Save the image in the static/images folder
    
    # Code to add the new item to your database
    # Example using Firebase:
    ref = db.reference('menu')
    ref.push({
        'name': item_name,
        'price': price,
        'category': category,
        'store': store,
        'image_path': image_path  # Save the image path to the database
    })
    
    flash('Menu item added successfully!')
    return redirect(url_for('menu_management'))




@app.route('/get_order_details/<payment_id>', methods=['GET'])
def get_order_details(payment_id):
    # Query Firebase to find the order that matches the payment_id
    orders_ref = ref_order.order_by_child('payment_id').equal_to(payment_id).get()

    if not orders_ref:
        return jsonify({'status': 'failed', 'message': 'Order with given payment_id not found'}), 404

    # Extract the first matching order (assuming payment_id is unique)
    order_data = next(iter(orders_ref.values()))

    # Get the items for the order
    items = order_data.get('items', [])
    
    return jsonify({
        'status': 'success',
        'items': items
    })




@app.route('/menu', methods=["GET", "POST"])
def menu():
    if 'user' in session or 'admin' in session:
        if "cart" not in session:
            session["cart"] = {}

        if request.method == "POST":
            item_name = request.form.get("item_name")
            if item_name:
                cart = session["cart"]

                # Fetch the item details from Firebase instead of using MENU_ITEMS directly
                menu_items = get_menu_from_firebase()  # Fetch menu from Firebase
                item = next((item for item in menu_items if item["name"] == item_name), None)
                
                if item:
                    store_name = item["store"]

                    if store_name not in cart:
                        cart[store_name] = {}

                    if item_name in cart[store_name]:
                        cart[store_name][item_name]["quantity"] += 1
                    else:
                        cart[store_name][item_name] = {"price": item["price"], "quantity": 1}

                    session["cart"] = cart
                    session.modified = True

        menu_items = get_menu_from_firebase()  # Fetch menu from Firebase
        grouped_menu = group_menu_by_store(menu_items)  # Assuming this function exists
        return render_template("menu.html", menu_by_store=grouped_menu)
    return render_template("index.html")



def group_menu_by_store(menu_items):
    grouped = {}
    for item in menu_items:
        store = item["store"]
        if store not in grouped:
            grouped[store] = []
        grouped[store].append(item)
    return grouped


@app.route('/cart', methods=["GET", "POST"])
def cart():
    if 'user' in session or 'admin' in session:
        if "cart" not in session:
            session["cart"] = {}

        if request.method == "POST":
            action = request.form.get("action")
            item_name = request.form.get("item_name")
            store_name = request.form.get("store_name")

            if action == "remove" and store_name in session["cart"] and item_name in session["cart"][store_name]:
                session["cart"][store_name][item_name]["quantity"] -= 1
                if session["cart"][store_name][item_name]["quantity"] <= 0:
                    del session["cart"][store_name][item_name]
                if not session["cart"][store_name]:
                    del session["cart"][store_name]
                session.modified = True

            elif action == "increase" and store_name in session["cart"] and item_name in session["cart"][store_name]:
                session["cart"][store_name][item_name]["quantity"] += 1
                session.modified = True

            elif action == "checkout":
                bill_items = session["cart"]
                total_price = sum(
                    item["price"] * item["quantity"] for store_items in bill_items.values() for item in store_items.values()
                )
                session["bill_items"] = bill_items
                session["total_price"] = total_price
                return render_template("bill.html", bill_items=bill_items, total_price=total_price)
            
        total_price = sum(
            item["price"] * item["quantity"] for store_items in session["cart"].values() for item in store_items.values()
        )

        return render_template("cart.html", cart=session["cart"], total_price=total_price)
    return render_template("index.html")


@app.route('/create_order', methods=['POST'])
def create_order():
    # Ensure total price exists in session
    total_price = session.get("total_price")
    
    if total_price is None:
        return jsonify({"error": "Total price is missing!"}), 400

    try:
        total_price = float(total_price)  # Ensure it’s a valid number
        if total_price <= 0:
            return jsonify({"error": "Total price must be greater than zero!"}), 400
    except ValueError:
        return jsonify({"error": "Invalid total price format!"}), 400

    total_price_paise = int(total_price * 100)  # Convert to paise

    # Create order on Razorpay
    order_data = {
        "amount": total_price_paise,
        "currency": "INR",
        "payment_capture": 1  # Auto capture payment
    }

    try:
        order = client.order.create(order_data)
        return jsonify(order)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/verify_payment', methods=['POST'])
def verify_payment():
    data = request.json
    razorpay_payment_id = data.get("razorpay_payment_id")
    razorpay_order_id = data.get("razorpay_order_id")
    razorpay_signature = data.get("razorpay_signature")

    params_dict = {
        "razorpay_order_id": razorpay_order_id,
        "razorpay_payment_id": razorpay_payment_id,
        "razorpay_signature": razorpay_signature
    }

    try:
        client.utility.verify_payment_signature(params_dict)
    except razorpay.errors.SignatureVerificationError:
        return jsonify({"status": "failed", "message": "Payment verification failed!"}), 400

    # Retrieve order details from session
    user = session.get("user")  # Ensure user data is stored in session
    bill_items = session.get("bill_items", [])
    total_price = session.get("total_price")
    payment_id = razorpay_payment_id

    if not user or not total_price:
        return jsonify({"status": "failed", "message": "Order details missing!"}), 400

    # Convert items dictionary to a list of dictionaries
    items_list = []
    for vendor, menu in bill_items.items():
        for item_name, details in menu.items():
            items_list.append({
                "vendor": vendor,
                "name": item_name,
                "price": details["price"],
                "quantity": details["quantity"]
            })

    # Now order_data has a valid JSON structure
    order_data = {
        "user_id": str(user.get("uid")),
        "email": str(user.get("email")),
        "items": items_list,  # Convert to a list
        "total_price": float(total_price),
        "payment_id": str(payment_id),
        "timestamp": datetime.now().isoformat(),
        "status": "Paid"
    }

    try:
        ref_order.push(order_data)  # Push to Firebase
    except Exception as e:
        error_message = str(e)
        return jsonify({"status": "failed", "message": error_message}), 500

    # Clear session after successful payment
    for key in ["cart", "bill_items", "total_price", "order_id"]:
        session.pop(key, None)

    print(url_for('home'))



@app.route('/order_details')
def order_details():
    if 'user' in session or 'admin' in session:
        if 'uid' not in session['user']:
            return redirect(url_for('login'))  # Redirect to login if no session

        user_uid = session['user']['uid']
        
        # Get all the orders for the current user from Firebase
        orders_ref = db.reference('order')
        user_orders = orders_ref.order_by_child('user_id').equal_to(user_uid).get()

        # Check the structure of user_orders
        if user_orders is None:
            user_orders = {}  # Set to empty list if no orders are found

        items_dict = {key: user_orders[key]['items'] for key in user_orders.keys()}
        items_list = [item for order_items in items_dict.values() for item in order_items]

        for order in user_orders.values():
            for item in order['items']:
                item['quantity'] = int(item['quantity'])  # Convert to int
                item['price'] = float(item['price'])  # Convert to float
            # Pass the orders to the template
        return render_template('order_details.html', items=items_list,orders=user_orders)
    return render_template("index.html")



def get_orders_by_uid(uid):

    # Query orders based on user_id (uid)
    orders = ref_order.order_by_child('user_id').equal_to(uid).get()

    if orders:
        return orders
    else:
        return None 


if __name__ == "__main__":
    app.run(debug=True)
