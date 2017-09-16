import sys
sys.path.insert(0, '/var/www/cosplay/')
import os
import glob
from flask import Flask, jsonify
from flask_wtf.csrf import CSRFProtect as flask_csrfprotect
from flask_wtf import FlaskForm
from wtforms import BooleanField
from wtforms.validators import InputRequired
import bleach
from re import sub
from unidecode import unidecode
from flask_login import current_user

app = Flask(__name__, static_url_path='/static')
app.config.from_object(__name__)
csrf = flask_csrfprotect(app)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'wardrobe.db'),
    SECRET_KEY='development key',
    USERNAME='admin',
    PASSWORD='default',
    UPLOAD_FOLDER=os.path.join(app.root_path, "static/uploads/"),
    ALLOWED_EXTENSIONS=set(['png', 'jpg', 'jpeg', 'gif'])
))


@app.template_filter('sanitize')
def clean(text):
    return bleach.clean(text)


@app.context_processor
def get_carousel():
    img = sorted(glob.iglob('static/uploads/*/photo/*.*'), key=os.path.getctime)
    return dict(carousel=img[:3])


def make_slug(*args):
    raw_slug = '-'.join(filter(None, args))
    slug = str.lower(sub('\W+', '-', unidecode(raw_slug)))
    return slug


class DeleteForm(FlaskForm):
    agree = BooleanField('Yes', validators=[InputRequired()])


import costumes
import database
import tutorials
import about
import home

