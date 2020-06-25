from flask import Blueprint, render_template
from datetime import datetime
from extensions import mysql, MySQLdb, bcrypt, getProjectRoot
from flask import render_template, request, redirect, url_for, flash, session, url_for, json, Blueprint
# For File Management
from werkzeug.utils import secure_filename
import os

mod = Blueprint('admin', __name__, template_folder='templates',
                static_folder='static', static_url_path='/admin/static')

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

@mod.context_processor
def inject_now():
    return {'now': datetime.utcnow()}

@mod.route('/login', methods=['GET', 'POST'])
def login():
    if (request.method == 'GET'):
        return render_template('admin/login.jinja')
    if (request.method == 'POST'):
        adminEmail = request.form['adminEmail']
        adminPassword = request.form['adminPassword'].encode('utf-8')
        cursor = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cursor.execute('SELECT admin_user_email, admin_user_name, admin_user_password, admin_user_img_route FROM admin_users WHERE admin_user_email = %s', (adminEmail, ))

        adminUser = cursor.fetchone()
        cursor.close()

        if (adminUser is None):
            return redirect('/admin/login?error=wrongEmail')
        
        if bcrypt.hashpw(adminPassword, adminUser['admin_user_password'].encode('utf-8')) == adminUser['admin_user_password'].encode('utf-8'):
            session['adminEmail'] = adminUser['admin_user_email']
            session['adminName'] = adminUser['admin_user_name']
            session['adminUserImgRoute'] = adminUser['admin_user_img_route']
            return redirect('/admin')
        else:
            return redirect('/admin/login?error=wrongPassword')

@mod.route('/logout')
def logout():
    session.clear()
    return redirect('/admin/login')

@mod.route('/categories')
def viewCategories():
    if not session.get('adminEmail'):
        return redirect('/admin/login')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM categories')
    categoriesData = cursor.fetchall()
    cursor.close()
    return render_template('admin/categories.jinja', categoriesData=categoriesData)

@mod.route('/products')
def viewProducts():
    if not session.get('adminEmail'):
        return redirect('/admin/login')
    cursor = mysql.connection.cursor()
    cursor.execute('SELECT * FROM products')
    productsData = cursor.fetchall()
    cursor.close()
    return render_template('admin/products.jinja', productsData=productsData)

@mod.route('/')
def index():
    if not session.get('adminEmail'):
        return redirect('/admin/login')
    return render_template('admin/index.html')

@mod.route('/categories/add', methods=['POST', 'GET'])
def addCategory():
    if not session.get('adminEmail'):
        return redirect('/admin/login')
    else:
        if request.method == 'GET':
            return render_template('admin/add-category.html')
        if request.method == 'POST':
            uploadFolder = os.path.join(getProjectRoot(), 'modules/static/client/img/categories')
            print(uploadFolder)

            if not os.path.isdir(uploadFolder):
                print("Not Dir")

            categoryName = request.form['categoryName']
            categoryImg = request.files['categoryImg']
            filename, file_extension = os.path.splitext(categoryImg.filename)
            destination = "/".join([uploadFolder, categoryName.lower() + file_extension])
            categoryImgRoute = 'img/categories/' + categoryName.lower() + file_extension
            
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO categories (category_name, category_img_route) VALUES (%s, %s)', (categoryName, categoryImgRoute))
            mysql.connection.commit()
            cursor.close()
            # Save images in the server
            categoryImg.save(destination)

            return redirect('/admin/categories?add=success')

@mod.route('/products/add', methods=['POST', 'GET'])
def addProduct():
    if not session.get('adminEmail'):
        return redirect('/admin/login')
    else:
        if request.method == 'GET':
            return render_template('admin/add-product.html')
        if request.method == 'POST':
            smallImagesFolder = os.pardir.join(getProjectRoot(), 'modules/static/client/img/products/imgs_small')
            largeImagesFolder = os.path.join(getProjectRoot(), 'modules/static/client/img/products/imgs_large')
            print(uploadFolder)

            if not os.path.isdir(uploadFolder):
                print("Not Dir")

            productName = request.form['productName']
            productDescription = request.form['productDescription']
            productSmallImages = request.files('productSmallImages')
            productLargeImages = request.files.getlist('productLargeImages')
            # Save in the database
            cursor = mysql.connection.cursor()
            cursor.execute('INSERT INTO products (product_name, category_img_route) VALUES (%s, %s)', (categoryName, categoryImgRoute))
            mysql.connection.commit()
            # Save images in the server
            for productLargeImage in productLargeImages:
                filename, file_extension = os.path.splitext(productImage.filename)
                destination = "/".join([largeImagesFolder, productName.lower() + file_extension])
                productImgRoute = 'img/products/imgs_large' + productName.lower() + file_extension
                productImage.save(destination)

            return redirect('/admin/products?add=success')

@mod.route('/categories/edit', methods=['POST', 'GET'])
def editCategory():
    if not session.get('adminEmail'):
        return redirect('/admin/login')
    else:
        if request.method == 'GET':
            categoryId = request.args.get('id')
            cursor = mysql.connection.cursor()
            cursor.execute('SELECT * FROM categories WHERE id_category = %s', (categoryId, ))
            categoryData = cursor.fetchone()
            cursor.close()
            return render_template('admin/edit-category.html', categoryData = categoryData)
        else:
            uploadFolder = os.path.join(getProjectRoot(), 'modules/static/client/img/categories')
            categoryId = int(request.form['categoryId'])
            categoryName = request.form['categoryName']
            categoryImg = request.files['categoryImg']
            filename, file_extension = os.path.splitext(categoryImg.filename)
            destination = "/".join([uploadFolder, categoryName.lower() + file_extension])
            categoryImgRoute = 'img/categories/' + categoryName.lower() + file_extension
            
            cursor = mysql.connection.cursor()
            cursor.execute('UPDATE categories SET category_name=%s, category_img_route=%s WHERE id_category=%s', (categoryName, categoryImgRoute, categoryId))
            mysql.connection.commit()
            cursor.close()
            # Save image in the server
            categoryImg.save(destination)

            return redirect('/admin/categories?add=success')



