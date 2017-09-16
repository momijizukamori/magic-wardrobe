from flask import render_template, abort, request, redirect, url_for
from cosplay import app, make_slug
from database import query_db, update_db
from images import save_image, save_images
from flask_wtf import FlaskForm
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms import StringField, PasswordField, TextAreaField, HiddenField, FileField
from wtforms.validators import InputRequired, EqualTo
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from dumper import dump

login_manager = LoginManager()
login_manager.init_app(app)


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    password = PasswordField('Password', validators=[InputRequired()])


class UserForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired()])
    display_name = StringField('Display Name', validators=[InputRequired()])
    profile_pic = FileField('Photo')
    about = TextAreaField('About')
    id = HiddenField()


class NewUserForm(UserForm):
    password = PasswordField('Password', validators=[InputRequired()])
    confirm = PasswordField('Confirm Password', validators=[InputRequired(),
                            EqualTo('new_password', message='Passwords must match')])


class User(UserMixin):
    key_order = ['username', 'id', 'display_name', 'about', 'profile_pic']

    def __init__(self, username=None, id=None):
        if username is not None:
            user = query_db('select * from users where username = ?',
                            [username], one=True)
            if user is None:
                abort(403)
            self.username = username
            self.id = user['id']
            self.display_name = user['display_name']
            self.about = user['about']
            self.profile_pic = user['profile_pic']
        if id is not None:
            user = query_db('select * from users where id = ?', [id], one=True)
            self.username = user['username']
            self.id = id
            self.display_name = user['display_name']
            self.about = user['about']
            self.profile_pic = user['profile_pic']

    def is_correct_password(self, plaintext):
        pw_hash = query_db('select password from users where id = ?',
                           [self.id], one=True)
        return check_password_hash(pw_hash['password'], plaintext)

    def set_password(self, plaintext):
        self._password = generate_password_hash(plaintext)

    def __getitem__(self, key):
        result = getattr(self, self.key_order[key])
        return result


def new_user(username, password, display_name=None):
    pw_hash = generate_password_hash(password)
    if display_name is None:
        display_name = username
    update_db('insert into users (username, password) values (?, ?)',
              [username, pw_hash])


def delete_user(username):
    user = User(username)
    update_db('delete from tutorials where author = ?', [user.id])
    update_db('delete from costumes where cosplayer = ?', [user.id])
    update_db('delete from users where id = ?', [user.id])


@login_manager.user_loader
def load_user(user_id):
    return User(id=user_id)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User(form.username.data)
        if user.is_correct_password(form.password.data):
            login_user(user)
            print 'logged in!'
            return redirect(url_for('index'))

        else:
            return redirect(url_for('login'))

    return render_template('login.html', form=form)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/cosplayers/')
def user_index():
    users = query_db('select display_name, username, profile_pic from users')
    return render_template('users/index.html', users=users)


@app.route('/cosplayers/new', methods=['GET', 'POST'])
@login_required
def user_new():
    form = NewUserForm()
    if form.is_submitted():
        username = form.username.data
        display_name = form.display_name.data or username
        pw_hash = generate_password_hash(form.password.data)
        update_db("insert into users (username, display_name, about, password) \
                  values (?, ?, ?, ?)", [username, display_name,
                  form.about.data, pw_hash])
        return redirect(url_for('user_index'))
    return render_template('users/form.html', form=form)


@app.route('/cosplayers/<username>')
def user_page(username):
    user = User(username)
    costumes = query_db("select id, name, series, variant, slug, cover from \
                    costumes where cosplayer = ? order by id desc", [user.id])
    tutorials = query_db("select title, slug from \
        tutorials where author = ? order by id desc", [user.id])
    return render_template('users/page.html', user=user, costumes=costumes, tutorials=tutorials)


@app.route('/cosplayers/<username>/edit', methods=['GET', 'POST'])
@login_required
def user_edit(username):
    user = User(username)
    form = UserForm(obj=user)

    if not current_user.username == user.username:
        abort(401)
    if form.validate_on_submit():
        username = form.username.data
        display_name = form.display_name.data or username
        update_db("update users set username = ?, display_name = ?, about = ? \
                  where id = ?", [username, display_name,
                  form.about.data, form.id.data])
        return redirect(url_for('user_page', username=username))
    return render_template('users/form.html', form=form)
