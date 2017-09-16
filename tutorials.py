from flask import render_template, abort, request, redirect, url_for
from cosplay import app, make_slug
from database import query_db, update_db
from images import save_image
from about import User
from home import add_update
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms.validators import InputRequired
from flask_login import login_required, current_user


def get_tutorial(slug):
    tutorial = query_db('select * from tutorials where slug = ?',
                        [slug], one=True)
    if tutorial is None:
        return None
    tutorial['author'] = User(id=tutorial['author'])
    return tutorial


class TutorialForm(FlaskForm):
    title = StringField('Title', validators=[InputRequired()])
    content = TextAreaField(validators=[InputRequired()], id='tutorial_content')


# Tutorial pages
@app.route('/tutorials/')
def tutorial_index():
    tutorials = query_db("select title, slug from \
                        tutorials order by id desc")
    return render_template('tutorials/index.html', tutorials=tutorials)


@app.route('/tutorials/<slug>')
def tutorial_page(slug):
    tutorial = get_tutorial(slug)
    if tutorial is None:
        abort(404)
    return render_template('tutorials/page.html', tutorial=tutorial)


@app.route('/tutorials/<slug>/edit', methods=['GET', 'POST'])
@login_required
def tutorial_edit(slug):
    tutorial = get_tutorial(slug)
    if tutorial is None:
        abort(404)
    if not current_user.username == tutorial['author']['username']:
        abort(401)
    form = TutorialForm(**tutorial)
    if form.validate_on_submit():
        update_db("update tutorials set title = ?, content = ? where slug = ?",
                  [form.title.data, form.content.data, slug])
        add_update("<a href='%s'>%s</a> updated <a href='%s'>%s</a>" %  (url_for('user_page', username=current_user.username), current_user.display_name, url_for('tutorial_page', slug=slug), form.title.data))
        return redirect(url_for('tutorial_page', slug=slug))
    return render_template('tutorials/form.html', form=form, slug=slug)


@app.route('/tutorials/new', methods=['GET', 'POST'])
@login_required
def tutorial_new():
    form = TutorialForm()
    if form.validate_on_submit():
        author = current_user.id
        slug = make_slug(form.title.data)
        update_db("insert into tutorials (title, content, author, slug) values (?, ?, ?, ?)",
                  [form.title.data, form.content.data, author, slug])
        add_update("<a href='%s'>%s</a> added <a href='%s'>%s</a>" %  (url_for('user_page', username=current_user.username), current_user.display_name, url_for('tutorial_page', slug=slug), form.title.data))
        return redirect(url_for('tutorial_index'))

    return render_template('tutorials/form.html', form=form)
