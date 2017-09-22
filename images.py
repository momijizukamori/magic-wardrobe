import os

from flask import jsonify, request
from PIL import Image, ExifTags
from dumper import dump
from werkzeug.utils import secure_filename
from cosplay import app, csrf
from database import query_db, update_db


@app.route('/upload', methods=['POST'])
@csrf.exempt
def upload():
    app.logger.debug("hit the uploader")
    # print 'hit the uploader'
    print dump(request.form)
    image = request.files['upload']
    type = request.form['type']

    # #FIXME: validate request
    filename = save_image(image, type)
    return jsonify(fileName=filename, uploaded=1)


def save_image(image, type=None):
    filename = secure_filename(image.filename)

    # get our path, check for existance, and make it if necessary
    path = os.path.join(app.config['UPLOAD_FOLDER'], type)

    if not os.path.exists(path):
        os.makedirs(path)

    location = os.path.join(path, filename)
    image.save(location)
    make_thumbnail(location)
    return filename


def delete_image(image_id, costume_id, type):
    image = query_db("select filename from images where id = ?", [image_id], one=True)
    update_db("delete from images where id = ?", [image_id])

    path = os.path.join(app.config['UPLOAD_FOLDER'], costume_id, type)
    os.remove(os.path.join(path, image['filename']))
    os.remove(os.path.join(path, 'thumbnails', image['filename']))
    return


def make_thumbnail(image, size=150):
    orig = Image.open(image)

    #If no ExifTags, no rotating needed.
    try:
    # Grab orientation value.
        image_exif = orig._getexif()
        image_orientation = image_exif[274]

    # Rotate depending on orientation.
        if image_orientation == 3:
            orig = orig.rotate(180)
        if image_orientation == 6:
            orig = orig.rotate(-90)
        if image_orientation == 8:
            orig = orig.rotate(90)

    # Save rotated image.
        orig.save(image)
    except:
        pass

    path, filename = os.path.split(image)

    if orig.width > orig.height:
        factor = orig.height / float(size)
        y_resize = size
        x_resize = orig.width / factor
    else:
        factor = orig.width / float(size)
        y_resize = orig.height / factor
        x_resize = size
    thumb = orig.resize((int(x_resize), int(y_resize)), 3).crop((0, 0, size, size))
    thumbnail_path = os.path.join(path, 'thumbnails', filename)

    if not os.path.exists(path + '/thumbnails'):
        os.makedirs(path + '/thumbnails')
    thumb.save(thumbnail_path)
    return thumbnail_path


def load_images(costume_id):
    images = {}
    images['photos'] = query_db("select id, filename, `order` from images \
                                where costume_id = ? and type = 'photo' order by `order`",
                                [costume_id])
    images['references'] = query_db("select id, filename, `order` from images \
                                    where costume_id = ? and type \
                                    = 'ref' order by `order`", [costume_id])
    return images


def save_images(images, costume_id, type):

    for image in images:
        if image.form.id.data:
            if image.form.deleted.data:
                delete_image(image.form.id.data, costume_id, type)
            if image.form.reordered.data:
                update_db("update images set `order` = ? where id = ?",
                          [image.form.order.data, image.form.id.data])

        else:
            filename = image.form.filename.data
            new_path = os.path.join(app.config['UPLOAD_FOLDER'], str(costume_id), type)
            old_path = os.path.join(app.config['UPLOAD_FOLDER'], type)

            if not os.path.exists(new_path):
                os.makedirs(new_path)

            if not os.path.exists(new_path + '/thumbnails'):
                os.makedirs(new_path + '/thumbnails')

            os.rename(os.path.join(old_path, filename), os.path.join(new_path, filename))
            os.rename(os.path.join(old_path, 'thumbnails', filename), os.path.join(new_path, 'thumbnails', filename))

            update_db("insert into images (filename, `order`, type, \
                       costume_id) values (?, ?, ?, ?)",
                      [image.form.filename.data, image.form.order.data, type, costume_id])
    return

