from datetime import datetime
from flask import render_template, abort, request, redirect, url_for
from cosplay import app, make_slug
from database import query_db, update_db
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, HiddenField, FileField
from wtforms.validators import InputRequired, EqualTo
from flask_login import current_user
from itertools import groupby

class UpdateForm(FlaskForm):
    message = TextAreaField('Update', validators=[InputRequired()])

def add_update(message):
    update_db('insert into updates (datetime, message) values (?, ?)',
              [datetime.now(), message])

def get_updates():
    updates = query_db('select * from updates')
    get_day = lambda item: item.get('datetime').date()
    updates = sorted(updates, key=get_day, reverse=True)
    grouped_dates = []
    for k, g in groupby(updates, get_day):
        grouped_dates.append(list(g))      # Store group iterator as a list
    return grouped_dates

# Root index
@app.route('/', methods=['GET', 'POST'])
def index():
    form = UpdateForm()
    if form.validate_on_submit():
        if current_user.is_authenticated:
            add_update(form.message.data)
            return redirect(url_for('index'))
        else:
            abort(403)
    updates = get_updates()
    return render_template('index.html', form=form, updates=updates)


# Error handling
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def not_authorized(error):
    return render_template('403.html'), 403