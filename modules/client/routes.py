from flask import render_template, request, redirect, url_for, flash, session, url_for, json, Blueprint
from extensions import mysql, MySQLdb, bcrypt, Mail, sendgrid, getProjectRoot
from random import choice
from datetime import datetime
# Stripe Integration and Other Libraries
import stripe
import os

# Stripe Configuration
pub_key = 'pk_test_Ou5mAnbixhkapSeylaXh5tWc00UM74ZJUn'
secret_key = 'sk_test_RnCJnGWTy4nmwr1ncjUuVhvF00tsSzjVtY'
stripe.api_key = secret_key

# Payment Information
payment_amount = 600000

mod = Blueprint('client', __name__, template_folder='templates',
                static_folder='static')


@mod.context_processor
def inject_now():
    return {'now': datetime.utcnow()}


@mod.route('/')
def home():
    return render_template('client/index.jinja')


@mod.route('/about')
def about():
    return render_template('client/about.html')


@mod.route('/contact')
def contact():
    return render_template('client/contact.html')


@mod.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'GET':
        return render_template('client/signup.html')
    else:
        # Activation code for the account
        values = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
        activationCode = ''
        activationCode = activationCode.join(
            [choice(values) for i in range(10)])

        clientName = request.form['registrationName']
        clientEmail = request.form['registrationEmail']
        clientPhone = request.form['registrationPhone']
        clientPassword = request.form['registrationPassword'].encode('utf-8')
        hashedPassword = bcrypt.hashpw(clientPassword, bcrypt.gensalt())
        clientActivated = 0

        cursor = mysql.connection.cursor()
        cursor.execute('INSERT INTO clients (client_name, client_email, client_phone, client_password, client_activated, client_code) VALUES (%s, %s, %s, %s, %s, %s)',
                       (clientName, clientEmail, clientPhone, hashedPassword, clientActivated, activationCode))
        mysql.connection.commit()

        # Send mail using sendgrid

        message = Mail(
            from_email='ss.xlr8@gmail.com',
            to_emails=clientEmail,
            subject='Pizzeria Mar y Ana - Active su cuenta',
            html_content='<strong>El código para activar su cuenta es:</strong><br /><br /><div style="padding:10px;text-align:center;background-color:#D4EDDA;color:#156C7C;font-size:2rem;width:300px;font-weight:bold;">' + activationCode + '</div>'
        )
        try:
            response = sendgrid.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e.message)

        # Init user session
        session['name'] = clientName
        session['email'] = clientEmail

        flash('Registro completado correctamente')
        return redirect('/')


@mod.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        clientEmail = request.form['loginEmail']
        clientPassword = request.form['loginPassword'].encode('utf-8')

        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute(
            'SELECT client_name, client_email, client_password from clients WHERE client_email=%s', (clientEmail, ))
        client = cursor.fetchone()
        cursor.close()

        if client:
            if bcrypt.hashpw(clientPassword, client['client_password'].encode('utf-8')) == client['client_password'].encode('utf-8'):
                session['name'] = client['client_name']
                session['email'] = client['client_email']
                return render_template('client/index.jinja')
            else:
                return redirect('/login?error=wrongPassword')
        else:
            return redirect('/login?error=wrongEmail')

        return render_template('client/index.jinja')
    else:
        return render_template('client/login.jinja')


@mod.route('/logout')
def logout():
    session.clear()
    return render_template('client/index.jinja')


@mod.route('/account')
def account():
    cursor = mysql.connect.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT client_name, client_phone, client_activated, client_img_route FROM clients WHERE client_email=%s LIMIT 1', (session['email'], ))
    clientData = cursor.fetchone()
    cursor.close()

    return render_template('client/client-account.jinja', clientData=clientData)


@mod.route('/account/password_reset')
def forgotPassword():
    return render_template('client/send-code.html')


@mod.route('/account/password_reset/password_change', methods=['GET', 'POST'])
def changePassword():
    if request.method == 'GET':
        return render_template('client/change-password.html')
    else:
        if 'restoreEmail' in session:
            newPassword = request.form['restorePassword'].encode('utf-8')
            hashedPassword = bcrypt.hashpw(newPassword, bcrypt.gensalt())

            cursor = mysql.connection.cursor()
            cursor.execute('UPDATE clients SET client_password = %s WHERE id_client = %s',
                           (hashedPassword, session['idClient']))
            mysql.connection.commit()
            cursor.close()
            session.clear()

            return redirect('/account/password_reset/password_change?status=success')
        else:
            return redirect('/account/password_reset/password_change?status=invalidAction')


@mod.route('/account/send_password_reset_code', methods=['POST'])
def sendPasswordResetCode():
    restoreEmail = request.form['restoreEmail']
    values = '0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
    verificationCode = ''
    verificationCode = verificationCode.join(
        [choice(values) for i in range(10)])

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT id_client FROM clients WHERE client_email = %s', (restoreEmail, ))
    client = cursor.fetchone()
    cursor.close()

    if client:
        session['verificationCode'] = verificationCode
        session['restoreEmail'] = restoreEmail
        session['idClient'] = client['id_client']

        message = Mail(
            from_email='ss.xlr8@gmail.com',
            to_emails=restoreEmail,
            subject='Pizzeria Mar y Ana - Recuperar su cuenta',
            html_content='<strong>El código para recuperar su cuenta es:</strong><br /><br /><div style="padding:10px;text-align:center;background-color:#D4EDDA;color:#156C7C;font-size:2rem;width:300px;font-weight:bold;">' + verificationCode + '</div>'
        )
        try:
            response = sendgrid.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e)

        return redirect('/account/confirm_password_reset_code')
    else:
        return redirect('/account/password_reset?status=wrongEmail')


@mod.route('/account/confirm_password_reset_code', methods=['GET', 'POST'])
def confirmPasswordResetCode():
    if request.method == 'GET':
        return render_template('client/verify-code.html')
    else:
        code = request.form['restoreCode']
        codeSend = session['verificationCode']

        if code == codeSend:
            return redirect('/account/password_reset/password_change')
        else:
            return redirect('/account/confirm_password_reset_code?status=wrongCode')


@mod.route('/account/verify', methods=['POST'])
def verifyEmail():
    clientCode = request.form['clientCode']
    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute(
        'SELECT client_code FROM clients WHERE client_email=%s', (session['email'], ))
    dbClientCode = cursor.fetchone()['client_code']

    if (dbClientCode == ''):
        return redirect('/account?verify=already')
    elif dbClientCode == clientCode:
        cursor.execute(
            'UPDATE clients SET client_activated=%s, client_code=%s WHERE client_email=%s', (1, '', session['email']))
        mysql.connection.commit()
        cursor.close()
        return redirect('/account?verify=success')
    else:
        return redirect('/account?verify=error')


@mod.route('/account/update', methods=['POST'])
def updateAccount():
    clientName = request.form['clientName']
    clientPhone = request.form['clientPhone']

    cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cursor.execute('UPDATE clients SET client_name=%s, client_phone=%s WHERE client_email=%s',
                   (clientName, clientPhone, session['email']))
    mysql.connection.commit()
    cursor.close()

    return redirect('/account?update=success')


@mod.route('/account/profile_image_change', methods=['POST'])
def updateProfileImage():
    profileImg = request.files['profileImage']
    sessionEmail = session['email']

    uploadFolder = os.path.join(
        getProjectRoot(), 'modules/static/client/img/profiles')
    filename, file_extension = os.path.splitext(profileImg.filename)
    destination = "/".join([uploadFolder,
                            sessionEmail.lower() + file_extension])
    profileImgRoute = 'img/profiles/' + sessionEmail.lower() + file_extension

    cursor = mysql.connection.cursor()
    cursor.execute('UPDATE clients SET client_img_route=%s WHERE client_email=%s',
                   (profileImgRoute, sessionEmail))
    mysql.connection.commit()
    cursor.close()

    # Save image in the server
    profileImg.save(destination)
    return redirect('/account?update=success')


@mod.route('/menu')
def menu():
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM categories')
    categoriesData = cursor.fetchall()
    cursor.close()
    return render_template('client/menu.html', categoriesData=categoriesData)


@mod.route('/menu/category')
def category():
    categoryId = request.args.get('id')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM products WHERE id_category=' + categoryId)
    productsData = cursor.fetchall()
    cursor.execute(
        'SELECT category_name FROM categories WHERE id_category=' + categoryId)
    categoryName = cursor.fetchone()[0]
    cursor.close()
    return render_template('client/products.jinja', productsData=productsData, categoryName=categoryName)


@mod.route('/menu/product/details')
def viewPizza():
    productId = request.args.get('productId')
    cursor = mysql.connect.cursor()
    cursor.execute('SELECT id_product, products.id_category, product_Name, product_desc, product_img_small_route, category_name FROM products JOIN categories ON products.id_category=categories.id_category WHERE id_product=%s', (productId))
    productData = cursor.fetchone()
    cursor.execute(
        'SELECT id_price, price_desc, price FROM prices WHERE id_product=%s ORDER BY price ASC', (productId, ))
    productPricesData = cursor.fetchall()
    cursor.execute(
        'SELECT product_image_route FROM product_images WHERE id_product=%s', (productId, ))
    productImagesData = cursor.fetchall()
    cursor.close()
    return render_template('client/product-details.jinja', productData=productData, productPricesData=productPricesData, productImagesData=productImagesData)


@mod.route('/cart')
def cart():
    return render_template('client/cart.jinja')


@mod.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if request.method == 'POST':
        requestedProductOrders = request.json
        print(requestedProductOrders)
        global product_orders
        product_orders = []

        for productOrder in requestedProductOrders:
            product_orders.append(
                {
                    "name": productOrder['productName'],
                    "amount": int(productOrder['productPrice']) * 100,
                    "currency": "crc",
                    "quantity": productOrder['productQuantity']
                }
            )
        if len(product_orders) == 0:
            return json.dumps({'error': '0 product orders'}), 400, {'ContentType': 'application/json'}
        else:
            if session:
                clientEmail = session['email']
            else:
                clientEmail = None
            stripe_session = stripe.checkout.Session.create(
                success_url="http://127.0.0.1:3000/checkout/success",
                cancel_url="https://example.com/cancel",
                customer_email=clientEmail,
                payment_method_types=["card"],
                locale='es',
                line_items=product_orders
            )
            return json.dumps({'success': True, 'stripe_id': stripe_session.id}), 200, {'ContentType': 'application/json'}
    else:
        return render_template('client/checkout.jinja', pub_key=pub_key)


@mod.route('/checkout/success')
def checkoutSuccess():
    return render_template('client/checkout-success.html')
