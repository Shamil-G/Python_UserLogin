from typing import List, Any

from flask import render_template, request, redirect, flash, url_for, g
from flask_login import LoginManager, login_required, logout_user, login_user, current_user
import cx_Oracle
from werkzeug.security import check_password_hash, generate_password_hash
from db_oracle.connect import get_connection
from articles import app
import config as cfg

login_manager = LoginManager(app)
login_manager.login_view = 'login_page'
if cfg.Debug:
    print("UserLogin стартовал...")

class User:
    id_user = -1
    username = ''
    password = ''
    active = ''
    roles: List[Any] = []
    debug = False

    def new_user(i_username, i_password):
        hash_pwd = generate_password_hash(i_password)
        con = get_connection()
        cursor = con.cursor()
        message = cursor.var(cx_Oracle.DB_TYPE_NVARCHAR)
        cursor.callproc('cop.new_user', [i_username, hash_pwd, message])
        cursor.close()
        con.close()
        return message.getvalue()

    def get_roles(self, cursor):
        if cfg.Debug:
            print("--++ User. Get roles for: " + self.username)
        cursor.execute("select r.name from roles r, users u, users_roles us " +
                       "where u.id_user=us.id_user " +
                       "and   r.id_role=us.id_role " +
                       "and u.id_user=:uid_user", uid_user=self.id_user)

        self.roles.clear()
        for record in cursor:
            for list_val in record:
                self.roles.extend([list_val])

        if self.debug:
            for role in self.roles:
                print("Role: " + role)

    def get_user_by_name(self, user_name):
        if cfg.Debug:
            print("++++ get_user_by_name: " + user_name)
        conn = get_connection()
        cursor = conn.cursor()
        password = cursor.var(cx_Oracle.DB_TYPE_NVARCHAR)
        id_user = cursor.var(cx_Oracle.DB_TYPE_NUMBER)
        cursor.callproc('cop.login', (user_name, password, id_user))
        self.username = user_name
        self.password = password.getvalue()
        self.id_user = id_user.getvalue()

        self.get_roles(cursor)

        cursor.close()
        conn.close()
        if self.password is None:
            return None
        else:
            return self

    def have_role(self, role_name):
        return role_name in self.roles

    def is_authenticated(self):
        if self.password is None:
            return False
        else:
            return True

    def is_active(self):
        if self.active is None:
            return True
        else:
            return False

    def is_anonymous(self):
        if self.password is None:
            return True
        else:
            return False

    def get_id(self):
        return self.username


@login_manager.user_loader
def loader_user(username):
    if cfg.Debug:
        print("LoginManager.user_load: " + username)
    return User().get_user_by_name(username)


@app.route('/logout', methods=['GET', 'POST'])
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.after_request
def redirect_to_signin(response):
    if response.status_code == 401:
        return redirect(url_for('login_page') + '?next=' + request.url)
    return response


@app.before_request
def before_request():
    g.user = current_user


@app.route('/login', methods=['GET', 'POST'])
def login_page():
    username = request.form.get('username')
    user_password = request.form.get('password')
    if username and cfg.Debug:
        print("Login Page. username: "+username)
    if username and user_password:
        user = User().get_user_by_name(username)
        if user is not None and check_password_hash(user.password, user_password):
            login_user(user)
            next_page = request.args.get('next')
            if next_page is not None:
                return redirect(next_page)
            else:
                return redirect(url_for('index'))
        else:
            flash("Имя пользователя или пароль неверны")
            return redirect(url_for('login_page'))

    flash('Введите имя и пароль')
    return render_template('login.html')


@app.route('/register', methods=['GET', 'POST'])
def register():
    username = request.form.get('username')
    password = request.form.get('password')
    password2 = request.form.get('password2')
    if cfg.Debug:
        print("/register. username: "+username)

    if request.method == 'POST':
        if not (username and password and password2):
            flash('Требуется заполнение всех полей')
            return redirect(url_for('register'))
        elif password != password2:
            flash('Пароли не совпадают')
            return redirect(url_for('register'))

        message = User.new_user(username, password)
        if message:
            flash(message)
            return render_template('register.html')
        else:
            return redirect(url_for('login_page'))

    flash("Введите имя и пароль два раза")
    return render_template('register.html')
