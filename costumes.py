from flask import render_template, abort, redirect, url_for, request
from cosplay import app, make_slug, DeleteForm
from database import query_db, update_db
from about import User
from home import add_update
from images import save_image, save_images, load_images
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, FormField, FieldList, TextAreaField, HiddenField, IntegerField
from wtforms.validators import InputRequired
from flask_wtf.file import FileField, FileRequired
from flask_login import login_required, current_user
from dumper import dump
from shutil import rmtree
import os


def get_costume(slug):
    costume = query_db('select * from costumes where slug = ?',
                       [slug], one=True)
    if costume is None:
        return None
    components = query_db("select id, name, text from components where \
                          costume_id = ?", [costume['id']])
    costume['components'] = components
    costume['cosplayer'] = User(id=costume['cosplayer'])
    images = load_images(costume['id'])
    costume['references'] = images['references']
    costume['photos'] = images['photos']

    return costume


class ComponentForm(FlaskForm):
    name = StringField('Name')
    text = TextAreaField('Description')
    deleted = HiddenField()
    id = HiddenField()


class PhotoForm(FlaskForm):
    filename = HiddenField()
    order = HiddenField()
    id = HiddenField()
    deleted = HiddenField()
    reordered = HiddenField()


class CostumeForm(FlaskForm):
    name = StringField('Character', validators=[InputRequired()])
    id = HiddenField()
    series = StringField('Series', validators=[InputRequired()])
    variant = StringField('Variant')
    notes = TextAreaField('Notes')
    components = FieldList(FormField(ComponentForm))
    photo_upload = FileField('Add Photos')
    ref_upload = FileField('Add References')
    photos = FieldList(FormField(PhotoForm))
    references = FieldList(FormField(PhotoForm))
    year = IntegerField('Made In')
    status = SelectField('Status', choices=[('active', 'active'), ('planned', 'planned'), ('wip', 'in progress'), ('retired', 'retired'), ('draft', 'draft')])


# Costume pages
@app.route('/costumes/')
def costume_index():
    costumes = query_db("select id, name, series, variant, slug, cover, status from \
                        costumes order by id desc")
    return render_template('costumes/index.html', costumes=costumes)


@app.route('/costumes/new', methods=['GET', 'POST'])
@login_required
def costume_new():
    form = CostumeForm()
    if form.is_submitted():
        save_costume(form)
        return redirect(url_for('costume_index'))

    # add blank component entry at the end
    form.components.append_entry()

    return render_template('costumes/form.html', form=form)


@app.route('/costumes/<slug>')
def costume_page(slug):
    costume = get_costume(slug)
    if costume is None:
        abort(404)
    costume['images'] = load_images(costume['id'])
    return render_template('costumes/page.html', costume=costume, slug=slug)


@app.route('/costumes/<slug>/edit', methods=['GET', 'POST'])
@login_required
def costume_edit(slug):
    # look up the costume and its components in the db
    costume = get_costume(slug)
    if costume is None:
        abort(404)

    if not current_user.username == costume['cosplayer'].username:
        abort(401)

    # Load in the character data to the form
    form = CostumeForm(**costume)

    # add blank component entry at the end
    form.components.append_entry()

    if form.validate_on_submit():
        new_slug = save_costume(form)
        return redirect(url_for('costume_page', slug=new_slug))

    return render_template('costumes/form.html', form=form, slug=slug)


@app.route('/costumes/<slug>/delete', methods=['GET', 'POST'])
@login_required
def costume_delete(slug):
    # look up the costume and its components in the db
    costume = get_costume(slug)
    if costume is None:
        abort(404)

    if not current_user.username == costume['cosplayer'].username:
        abort(401)

    form = DeleteForm()
    id = costume['id']
    if form.validate_on_submit():
        update_db("delete from components where costume_id = ?", [id])
        update_db("delete from images where costume_id = ?", [id])
        update_db("delete from costumes where id = ?", [id])
        path = os.path.join(app.config['UPLOAD_FOLDER'], str(id))
        if os.path.exists(path):
            rmtree(path)
        return redirect(url_for('costume_index'))

    return render_template('delete.html', form=form)


def save_costume(form):
    name = form.name.data
    series = form.series.data
    variant = form.variant.data
    photos = form.photos
    references = form.references
    cosplayer = current_user.id
    status = form.status.data
    year = form.year.data
    notes = form.notes.data

    slug = make_slug(name, series, variant)
    if form.photo_upload.data:
        save_image(form.photo_upload.data, 'photo')
    if form.ref_upload.data:
        save_image(form.ref_upload.data, 'ref')

    if form.id.data:
        costume_id = form.id.data
        update_db("update costumes set name = ?, series = ?, variant = ?, \
          notes = ?, status = ?, year = ?, slug = ? where id = ?", [name, series,
          variant, notes, status, year, slug, costume_id])
        add_update("<a href='%s'>%s</a> updated <a href='%s'>%s - %s</a>" %  (url_for('user_page', username=current_user.username), current_user.display_name, url_for('costume_page', slug=slug), name, series))
    else:
        costume_id = update_db("insert into costumes (name, series, variant, notes, \
                           status, year, slug, cosplayer) values (?, ?, ?, ?, ?, ?, ?, ?)", [name,
                           series, variant, notes, status, year, slug, cosplayer])
        add_update("<a href='%s'>%s</a> added <a href='%s'>%s - %s</a>" %  (url_for('user_page', username=current_user.username), current_user.display_name, url_for('costume_page', slug=slug), name, series))

    for component in form.components:
        if component.form.name.data:
            if component.form.id.data:
                if component.form.deleted.data:
                    update_db("delete from components where id = ?", [component.form.id.data])
                else:
                    update_db('update components set name = ?, text = ? where \
                               id = ?', [component.form.name.data,
                                component.form.text.data, component.form.id.data])
            else:
                update_db('insert into components (name, text, costume_id) \
                          values (?, ?, ?)', [component.form.name.data,
                          component.form.text.data, costume_id])

    cover_photo = next( (photo for photo in photos if not photo.form.deleted.data), None)

    #FIXME: why is data not being processed? I don't know
    if cover_photo:
        update_db('update costumes set cover = ? where id = ?', [cover_photo.filename.object_data, costume_id])
    save_images(photos, costume_id, 'photo')
    save_images(references, costume_id, 'ref')
    return slug

