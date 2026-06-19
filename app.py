from flask import Flask, render_template, request, redirect, url_for, flash, session
from datetime import datetime, timedelta
import mysql.connector as mc
from functools import wraps
from flask import jsonify

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'
app.config['SESSION_TYPE'] = 'filesystem'

# MySQL Database Configuration
def get_db_connection():
    conn = mc.connect(
        host="localhost",
        user="root",
        passwd="Vaishnav8301946204",  # Update with your password
        database="medcl"
    )
    return conn

##
@app.route('/ai_search', methods=['POST'])
def ai_search():
    symptom = request.form.get('symptom', '').lower()

    conn = get_db_connection()
    c = conn.cursor(dictionary=True)

    try:
        # Simple logic: search symptom in medicine description/category
        c.execute('''
            SELECT m.id, m.name, m.description, 
                   MIN(b.selling_price) as min_price
            FROM Medicine m
            JOIN Batch b ON m.id = b.medicine_id
            WHERE (LOWER(m.description) LIKE %s OR LOWER(m.category) LIKE %s)
              AND b.quantity > 0
            GROUP BY m.id
            ORDER BY m.name
        ''', ('%' + symptom + '%', '%' + symptom + '%'))

        results = c.fetchall()

        if results:
            flash(f"Found {len(results)} medicine(s) for '{symptom}'", "success")
        else:
            flash(f"No medicines found for '{symptom}'", "warning")

        return render_template('search_results.html', query=symptom, medicines=results)

    except Exception as e:
        flash(f"AI search error: {str(e)}", "danger")
        return redirect(url_for('home'))
    finally:
        conn.close()


@app.route('/autocomplete')
def autocomplete():
    term = request.args.get('term')
    conn = get_db_connection()
    c = conn.cursor()
    c.execute(
        "SELECT name FROM Medicine WHERE name LIKE %s order by name  LIMIT 10",
        ('%' + term + '%',)
    )
    results = [row[0] for row in c.fetchall()]
    conn.close()
    return jsonify(results)





@app.route('/api/symptom_autocomplete', methods=['GET'])
def symptom_autocomplete():
    term = request.args.get('term', '').lower()

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        # Get distinct symptoms (keywords from description) and their related medicines
        cursor.execute("""
            SELECT DISTINCT description FROM Medicine
            WHERE LOWER(description) LIKE %s
        """, ('%' + term + '%',))

        descriptions = cursor.fetchall()
        suggestions = []

        for desc_row in descriptions:
            symptom_text = desc_row['description']

            # Now fetch all medicines having this symptom in description
            cursor.execute("""
                SELECT name FROM Medicine
                WHERE LOWER(description) = %s
            """, (symptom_text.lower(),))

            meds = cursor.fetchall()
            med_names = [m['name'] for m in meds]

            suggestions.append({
                "label": f"{symptom_text} → " + ", ".join(med_names[:3]),
                "value": symptom_text
            })

        return jsonify(suggestions)
    except Exception as e:
        print("Error:", e)
        return jsonify([])
    finally:
        conn.close()


# Admin login required decorator
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please log in as admin to access this page', 'danger')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

# Admin Login
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        c = conn.cursor(dictionary=True)
        c.execute("SELECT * FROM Admin WHERE username = %s", (username,))
        admin = c.fetchone()
        conn.close()
        
        if admin and admin['password'] == password:
            session['admin_logged_in'] = True
            session['admin_id'] = admin['id']
            flash('Admin login successful!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid admin credentials!', 'danger')
    return render_template('admin/login.html')

# Admin Logout
@app.route('/admin/logout')
@admin_login_required
def admin_logout():
    session.pop('admin_logged_in', None)
    session.pop('admin_id', None)
    flash('You have been logged out as admin.', 'success')
    return redirect(url_for('home'))

# Admin Dashboard
@app.route('/admin/dashboard')
@admin_login_required
def admin_dashboard():
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    
    try:
        # Get counts for dashboard
        c.execute("SELECT COUNT(*) as total_medicines FROM Medicine")
        total_medicines = c.fetchone()['total_medicines']
        
        c.execute("SELECT COUNT(*) as low_stock FROM Batch WHERE quantity < 10")
        low_stock = c.fetchone()['low_stock']
        
        # Expired or near expiry (30 days)
        near_expiry = datetime.now() + timedelta(days=30)
        c.execute("SELECT COUNT(*) as near_expiry FROM Batch WHERE expiry_date <= %s", (near_expiry,))
        near_expiry_count = c.fetchone()['near_expiry']
        
        # Today's sales
        c.execute("SELECT SUM(total_amount) as today_sales FROM Sale WHERE DATE(sale_date) = CURDATE()")
        today_sales = c.fetchone()['today_sales'] or 0
        
        # Get medicines with low stock
        c.execute('''SELECT m.name, b.quantity, b.batch_number 
                    FROM Batch b
                    JOIN Medicine m ON b.medicine_id = m.id
                    WHERE b.quantity < 10
                    ORDER BY b.quantity''')
        low_stock_items = c.fetchall()
        
        # Get near expiry medicines
        c.execute('''SELECT m.name, b.batch_number, b.expiry_date, 
                    DATEDIFF(b.expiry_date, CURDATE()) as days_remaining
                    FROM Batch b
                    JOIN Medicine m ON b.medicine_id = m.id
                    WHERE b.expiry_date <= %s
                    ORDER BY b.expiry_date''', (near_expiry,))
        near_expiry_items = c.fetchall()
        
        return render_template('admin/dashboard.html', 
                             total_medicines=total_medicines,
                             low_stock=low_stock,
                             near_expiry=near_expiry_count,
                             today_sales=today_sales,
                             low_stock_items=low_stock_items,
                             near_expiry_items=near_expiry_items)
    except Exception as e:
        flash(f'Error loading dashboard: {str(e)}', 'danger')
        return redirect(url_for('admin_login'))
    finally:
        conn.close()

# Public Home Page
@app.route('/')
def home():
    #conn = get_db_connection()
    #c = conn.cursor(dictionary=True)
    #try:
     #   c.execute('''SELECT m.id, m.name, m.description, 
      #              MIN(b.selling_price) as min_price,
       #             b.id as batch_id
        #            FROM Medicine m
         #           JOIN Batch b ON m.id = b.medicine_id
          #          WHERE b.quantity > 0
           #         GROUP BY m.id
            #        ORDER BY m.name''')
        #medicines = c.fetchall()
        #return render_template('home.html', medicines=medicines)
    #except Exception as e:
     #   flash(f'Error loading medicines: {str(e)}', 'danger')
      #  return render_template('home.html', medicines=[])
    #finally:
     #   conn.close()

     return render_template('home.html')


@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query', '').strip()
    
    if not query:
        flash('Please enter a search term.', 'warning')
        return redirect(url_for('home'))
    
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    try:
        c.execute('''SELECT m.id, m.name, m.description, 
                    MIN(b.selling_price) as min_price
                    FROM Medicine m
                    JOIN Batch b ON m.id = b.medicine_id
                    WHERE m.name LIKE %s AND b.quantity > 0
                    GROUP BY m.id
                    ORDER BY m.name''', ('%' + query + '%',))
        results = c.fetchall()
        return render_template('search_results.html', query=query, medicines=results)
    except Exception as e:
        flash(f'Error searching medicines: {str(e)}', 'danger')
        return redirect(url_for('home'))
    finally:
        conn.close()




        

# Medicine Details (public)
@app.route('/medicine/<int:id>')
def medicine_details(id):
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    try:
        # Get medicine info
        c.execute("SELECT * FROM Medicine WHERE id = %s", (id,))
        medicine = c.fetchone()
        
        if not medicine:
            flash('Medicine not found!', 'danger')
            return redirect(url_for('home'))
        
        # Get available batches (sorted by expiry date - soonest first)
        c.execute('''SELECT b.*, DATEDIFF(b.expiry_date, CURDATE()) as days_remaining
                    FROM Batch b
                    WHERE b.medicine_id = %s AND b.quantity > 0
                    ORDER BY b.expiry_date''', (id,))
        batches = c.fetchall()
        
        return render_template('medicine_details.html', medicine=medicine, batches=batches)
    except Exception as e:
        flash(f'Error loading medicine details: {str(e)}', 'danger')
        return redirect(url_for('home'))
    finally:
        conn.close()

# Shopping Cart and Checkout
@app.route('/add_to_cart', methods=['POST'])
def add_to_cart():
    batch_id = request.form['batch_id']
    quantity = int(request.form.get('quantity', 1))  # Ensure quantity is an int
    
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    c.execute('''SELECT m.name, b.selling_price 
                 FROM Batch b
                 JOIN Medicine m ON b.medicine_id = m.id
                 WHERE b.id = %s''', (batch_id,))
    item = c.fetchone()
    conn.close()
    
    if not item:
        flash('Item not found!', 'danger')
        return redirect(url_for('home'))
    
    cart = session.get('cart', {})
    if batch_id in cart:
        # Ensure that both quantities are integers before adding
        cart[batch_id]['quantity'] = int(cart[batch_id]['quantity']) + quantity
    else:
        cart[batch_id] = {
            'name': item['name'],
            'price': float(item['selling_price']),  # Ensure price is a float
            'quantity': quantity
        }
    
    session['cart'] = cart
    #flash('Item added to cart!', 'success')
    #return redirect(url_for('home'))
    return redirect(url_for('cart_success'))

@app.route('/cart/success')
def cart_success():
    return render_template('cart_success.html')



@app.route('/cart', methods=['GET', 'POST'])
def cart():
    if request.method == 'POST':
        # Process the order
        conn = get_db_connection()
        c = conn.cursor(dictionary=True)
        try:
            customer_name = request.form['name']
            customer_phone = request.form['phone']
            customer_email = request.form.get('email', '')
            customer_address = request.form.get('address', '')

            batch_ids = request.form.getlist('batch_id')
            quantities = [int(q) for q in request.form.getlist('quantity')]

            if not all(q > 0 for q in quantities):
                flash('Invalid quantities!', 'danger')
                return redirect(url_for('cart'))

            # Add customer
            c.execute('''INSERT INTO Customer (name, phone, email, address)
                         VALUES (%s, %s, %s, %s)''',
                      (customer_name, customer_phone, customer_email, customer_address))
            customer_id = c.lastrowid
            conn.commit()

            # Process each item
            for batch_id, quantity in zip(batch_ids, quantities):
                c.execute('''SELECT selling_price, quantity 
                             FROM Batch 
                             WHERE id = %s''', (batch_id,))
                batch = c.fetchone()

                if not batch or batch['quantity'] < quantity:
                    flash('Not enough stock!', 'danger')
                    conn.rollback()
                    return redirect(url_for('cart'))

                c.execute('''UPDATE Batch 
                             SET quantity = quantity - %s 
                             WHERE id = %s''',
                          (quantity, batch_id))

                total_amount = quantity * float(batch['selling_price'])  # Ensure price is a float
                c.execute('''INSERT INTO Sale 
                             (batch_id, customer_id, quantity, unit_price, total_amount)
                             VALUES (%s, %s, %s, %s, %s)''',
                          (batch_id, customer_id, quantity, batch['selling_price'], total_amount))

            conn.commit()
            session.pop('cart', None)  # Clear cart
            flash('Order placed successfully!', 'success')
            return redirect(url_for('order_success'))

        except Exception as e:
            conn.rollback()
            flash(f'Order error: {str(e)}', 'danger')
        finally:
            conn.close()

    # GET request – display cart
    cart = session.get('cart', {})
    # Make sure quantities are integers and prices are floats when calculating subtotal
    subtotal = sum(float(item['price']) * int(item['quantity']) for item in cart.values()) if cart else 0
    total = subtotal  # Add taxes or shipping if needed

    return render_template('cart.html', subtotal=subtotal, total=total)
# Admin Medicine Management
@app.route('/admin/medicines')
@admin_login_required
def manage_medicines():
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    try:
        c.execute('''SELECT m.*, 
                    (SELECT SUM(quantity) FROM Batch WHERE medicine_id = m.id) as total_quantity
                    FROM Medicine m
                    ORDER BY m.name''')
        medicines = c.fetchall()
        return render_template('admin/medicines.html', medicines=medicines)
    except Exception as e:
        flash(f'Error retrieving medicines: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

# Add Medicine
@app.route('/admin/medicine/add', methods=['GET', 'POST'])
@admin_login_required
def add_medicine():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        manufacturer = request.form['manufacturer']
        
        conn = get_db_connection()
        c = conn.cursor()
        try:
            c.execute('''INSERT INTO Medicine (name, description, category, manufacturer)
                        VALUES (%s, %s, %s, %s)''',
                     (name, description, category, manufacturer))
            conn.commit()
            flash('Medicine added successfully!', 'success')
            return redirect(url_for('manage_medicines'))
        except Exception as e:
            conn.rollback()
            flash(f'Error adding medicine: {str(e)}', 'danger')
        finally:
            conn.close()
    
    return render_template('admin/add_medicine.html')

# Edit Medicine
@app.route('/admin/medicine/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_medicine(id):
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    
    if request.method == 'POST':
        # Handle form submission
        name = request.form['name']
        description = request.form['description']
        category = request.form['category']
        manufacturer = request.form['manufacturer']
        
        try:
            c.execute('''UPDATE Medicine SET 
                        name = %s, description = %s, 
                        category = %s, manufacturer = %s
                        WHERE id = %s''',
                     (name, description, category, manufacturer, id))
            conn.commit()
            flash('Medicine updated successfully!', 'success')
            return redirect(url_for('manage_medicines'))
        except Exception as e:
            conn.rollback()
            flash(f'Error updating medicine: {str(e)}', 'danger')
    
    # GET request - show edit form
    c.execute("SELECT * FROM Medicine WHERE id = %s", (id,))
    medicine = c.fetchone()
    conn.close()
    
    if not medicine:
        flash('Medicine not found!', 'danger')
        return redirect(url_for('manage_medicines'))
    
    return render_template('admin/edit_medicine.html', medicine=medicine)

# Delete Medicine
@app.route('/admin/medicine/delete/<int:id>', methods=['POST'])
@admin_login_required
def delete_medicine(id):
    conn = get_db_connection()
    c = conn.cursor()
    
    try:
        # First check if there are any batches for this medicine
        c.execute("SELECT COUNT(*) FROM Batch WHERE medicine_id = %s", (id,))
        batch_count = c.fetchone()[0]
        
        if batch_count > 0:
            flash('Cannot delete medicine with existing batches! Delete batches first.', 'danger')
        else:
            c.execute("DELETE FROM Medicine WHERE id = %s", (id,))
            conn.commit()
            flash('Medicine deleted successfully!', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'Error deleting medicine: {str(e)}', 'danger')
    finally:
        conn.close()
    
    return redirect(url_for('manage_medicines'))

# Admin Batch Management
@app.route('/admin/batches')
@admin_login_required
def manage_batches():
    conn = None
    try:
        conn = get_db_connection()
        c = conn.cursor(dictionary=True)
        
        # Execute the query
        c.execute('''SELECT b.*, m.name as medicine_name,
                    DATEDIFF(b.expiry_date, CURDATE()) as days_remaining
                    FROM Batch b
                    JOIN Medicine m ON b.medicine_id = m.id
                    ORDER BY b.expiry_date''')
        
        batches = c.fetchall()
        
        return render_template('admin/batches.html', 
                            batches=batches if batches else [])
        
    except Exception as e:
        flash(f'Error retrieving batches: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    finally:
        if conn:
            conn.close()

# Add Batch
@app.route('/admin/batch/add', methods=['GET', 'POST'])
@admin_login_required
def add_batch():
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    try:
        if request.method == 'POST':
            medicine_id = request.form['medicine_id']
            batch_number = request.form['batch_number']
            manufacturing_date = request.form['manufacturing_date']
            expiry_date = request.form['expiry_date']
            quantity = int(request.form['quantity'])
            cost_price = float(request.form['cost_price'])
            selling_price = float(request.form['selling_price'])
            
            try:
                c.execute('''INSERT INTO Batch 
                            (medicine_id, batch_number, manufacturing_date, expiry_date, 
                             quantity, cost_price, selling_price)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)''',
                         (medicine_id, batch_number, manufacturing_date, expiry_date, 
                          quantity, cost_price, selling_price))
                conn.commit()
                flash('Batch added successfully!', 'success')
                return redirect(url_for('manage_batches'))
            except Exception as e:
                conn.rollback()
                flash(f'Error adding batch: {str(e)}', 'danger')
        
        # GET request - show form
        c.execute("SELECT id, name FROM Medicine ORDER BY name")
        medicines = c.fetchall()
        return render_template('admin/add_batch.html', medicines=medicines)
    finally:
        conn.close()

# Edit Batch
@app.route('/admin/batch/edit/<int:id>', methods=['GET', 'POST'])
@admin_login_required
def edit_batch(id):
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    
    try:
        if request.method == 'POST':
            # Handle form submission
            batch_number = request.form['batch_number']
            manufacturing_date = request.form['manufacturing_date']
            expiry_date = request.form['expiry_date']
            quantity = int(request.form['quantity'])
            cost_price = float(request.form['cost_price'])
            selling_price = float(request.form['selling_price'])

            c.execute('''UPDATE Batch SET
                        batch_number = %s,
                        manufacturing_date = %s,
                        expiry_date = %s,
                        quantity = %s,
                        cost_price = %s,
                        selling_price = %s
                        WHERE id = %s''',
                    (batch_number, manufacturing_date, expiry_date,
                     quantity, cost_price, selling_price, id))
            conn.commit()
            flash('Batch updated successfully!', 'success')
            return redirect(url_for('manage_batches'))

        # GET request - show edit form
        c.execute('''SELECT b.*, m.name as medicine_name 
                    FROM Batch b
                    JOIN Medicine m ON b.medicine_id = m.id
                    WHERE b.id = %s''', (id,))
        batch = c.fetchone()
        
        if not batch:
            flash('Batch not found!', 'danger')
            return redirect(url_for('manage_batches'))
        
        # Get all medicines for dropdown
        c.execute("SELECT id, name FROM Medicine ORDER BY name")
        medicines = c.fetchall()
        
        return render_template('admin/edit_batch.html',
                            batch=batch,
                            medicines=medicines)
    
    except Exception as e:
        conn.rollback()
        flash(f'Error: {str(e)}', 'danger')
        return redirect(url_for('manage_batches'))
    
    finally:
        conn.close()

# Admin Reports
@app.route('/admin/reports/sales')
@admin_login_required
def sales_report():
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    try:
        # Get filter parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query based on filters
        query = '''SELECT s.id, m.name as medicine_name, b.batch_number, 
                  s.quantity, s.unit_price, s.total_amount, s.sale_date,
                  c.name as customer_name,
                  (s.unit_price - b.cost_price) * s.quantity as profit
                  FROM Sale s
                  JOIN Batch b ON s.batch_id = b.id
                  JOIN Medicine m ON b.medicine_id = m.id
                  LEFT JOIN Customer c ON s.customer_id = c.id'''
        
        params = []
        
        if start_date and end_date:
            query += " WHERE DATE(s.sale_date) BETWEEN %s AND %s"
            params.extend([start_date, end_date])
        elif start_date:
            query += " WHERE DATE(s.sale_date) >= %s"
            params.append(start_date)
        elif end_date:
            query += " WHERE DATE(s.sale_date) <= %s"
            params.append(end_date)
        
        query += " ORDER BY s.sale_date DESC"
        
        c.execute(query, params)
        sales = c.fetchall()
        
        # Calculate totals
        c.execute("SELECT SUM(s.total_amount) as total_sales, SUM((s.unit_price - b.cost_price) * s.quantity) as total_profit FROM Sale s JOIN Batch b ON s.batch_id = b.id")
        totals = c.fetchone()
        total_sales = totals['total_sales'] or 0
        total_profit = totals['total_profit'] or 0
        
        if start_date or end_date:
            total_query = '''SELECT SUM(s.total_amount) as filtered_sales, 
                           SUM((s.unit_price - b.cost_price) * s.quantity) as filtered_profit 
                           FROM Sale s JOIN Batch b ON s.batch_id = b.id'''
            if start_date and end_date:
                total_query += " WHERE DATE(s.sale_date) BETWEEN %s AND %s"
                params = [start_date, end_date]
            elif start_date:
                total_query += " WHERE DATE(s.sale_date) >= %s"
                params = [start_date]
            elif end_date:
                total_query += " WHERE DATE(s.sale_date) <= %s"
                params = [end_date]
            
            c.execute(total_query, params)
            filtered_totals = c.fetchone()
            filtered_sales = filtered_totals['filtered_sales'] or 0
            filtered_profit = filtered_totals['filtered_profit'] or 0
        else:
            filtered_sales = total_sales
            filtered_profit = total_profit
        
        return render_template('admin/sales_report.html', 
                             sales=sales,
                             total_sales=total_sales,
                             total_profit=total_profit,
                             filtered_sales=filtered_sales,
                             filtered_profit=filtered_profit,
                             start_date=start_date,
                             end_date=end_date)
    except Exception as e:
        flash(f'Error generating sales report: {str(e)}', 'danger')
        return redirect(url_for('admin_dashboard'))
    finally:
        conn.close()

@app.route('/orders')
def orders():
    conn = get_db_connection()
    c = conn.cursor(dictionary=True)
    try:
        c.execute('''
            SELECT s.id, m.name as medicine_name, b.batch_number,
                   s.quantity, s.unit_price, s.total_amount, s.sale_date
            FROM Sale s
            JOIN Batch b ON s.batch_id = b.id
            JOIN Medicine m ON b.medicine_id = m.id
            ORDER BY s.sale_date DESC
        ''')
        orders = c.fetchall()
        return render_template('orders.html', orders=orders)
    except Exception as e:
        flash(f"Error loading orders: {str(e)}", "danger")
        return redirect(url_for('home'))
    finally:
        conn.close()


@app.route('/order/success')
def order_success():
    return render_template('order_success.html')


if __name__ == '__main__':
    app.run(debug=True)
