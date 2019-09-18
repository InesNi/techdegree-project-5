from flask import (Flask, render_template, redirect,
                   g, flash, url_for, request, abort)
from flask_login import (login_user, logout_user, current_user,
                         login_required, LoginManager)
from flask_bcrypt import check_password_hash

import models
import forms


app = Flask(__name__)
app.secret_key = "mcq0w98572390=ikDB&£b**D"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


@login_manager.user_loader
def load_user(userid):
    try:
        return models.User.get(models.User.id == userid)
    except models.DoesNotExist:
        return None


@app.before_request
def before_request():
    """Connect to the database before each request"""
    g.db = models.DATABASE
    g.db.connect()
    g.user = current_user


@app.after_request
def after_request(response):
    """Close the database connection after each request"""
    g.db.close()
    return response


# HOME PAGE

@app.route('/')
def index():
    entries = models.Entry.select().order_by('-date')
    return render_template('index.html', entries=entries)


# REGISTER

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Registers user"""
    form = forms.RegisterForm()
    if form.validate_on_submit():
        models.User.create_user(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        flash("Yay, you registered!", "success")
        return redirect(url_for('login'))
    return render_template('register.html', title="Register", form=form)


# LOGIN

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Logs in user"""
    form = forms.LoginForm()
    if form.validate_on_submit():
        try:
            user = models.User.get(models.User.email == form.email.data)
        except models.DoesNotExist:
            flash("Your email or password is incorrect", "error")
        else:
            if check_password_hash(user.password, form.password.data):
                login_user(user)
                flash("You've been logged in", "success")
                return redirect(url_for('index'))
            else:
                flash("Your email or password is incorrect", "error")
    return render_template('login.html', title="Log In", form=form)


# LOGOUT

@app.route('/logout')
@login_required
def logout():
    """Logs out user"""
    logout_user()
    flash("You've been logged out", "success")
    return redirect(url_for('index'))


# ENTRIES PAGE

@app.route('/entries')
def entries():
    """Fetches all entries"""
    entries = models.Entry.select().order_by('-date')
    return render_template('entries.html', title="Journal Entries",
                           entries=entries)


# ENTRIES BY TAG

@app.route('/<tag>')
def entries_by_tag(tag):
    """Fetches all entries related to tag that is passed in"""
    label = models.Tag.select().where(models.Tag.tag == tag).get()
    entries = label.get_entries()
    return render_template(
        'entries.html',title="Journal Entries|{}".format(tag),entries=entries
        )


# ADD ENTRY

@app.route('/entries/new', methods=['GET', 'POST'])
@login_required
def add():
    """Creates new entry from data provided in AddEntryForm"""
    form = forms.AddEntryForm()
    if form.validate_on_submit():
        # creates new entry with data inputed in form by user
        entry = models.Entry.create(
                title=form.title.data,
                date=form.date.data,
                time_spent=form.time_spent.data,
                content=form.content.data,
                resources=form.resources.data,
                slug=form.title.data.strip().lower().replace(' ', '-'),
                author=g.user._get_current_object()
        )
        # creates or gets tags inputed in form and
        # creates their relationship with entry
        for item in form.tags.data.strip().split(','):
            tag, created = models.Tag.get_or_create(tag=item)
            models.EntryTags.create(tag=tag, entry=entry)
        flash("New entry successfully made", "success")
        return redirect(url_for('index'))
    return render_template('new.html', title="New Entry", form=form)


# INDIVIDUAL ENTRY PAGE

@app.route('/entries/<slug>')
def details(slug):
    """Takes one argument-slug and queries Entry table for
    Entry with matching slug attribute which it passes to
    template to be displayed
    """
    entry = models.Entry.select().where(models.Entry.slug == slug).get()
    return render_template('detail.html',title=entry.title, entry=entry)


# EDIT

@app.route('/entries/<slug>/edit', methods=['GET', 'POST'])
@login_required
def edit(slug):
    """Edits the entry which slug attribute matches the argument passed in"""
    entry = models.Entry.select().where(models.Entry.slug == slug).get()
    if entry.author != current_user:
        abort(403)
    form = forms.AddEntryForm()
    if form.validate_on_submit():
        # updates entry with data provided in form
        models.Entry.update(
            title=form.title.data,
            date=form.date.data,
            time_spent=form.time_spent.data,
            content=form.content.data,
            resources=form.resources.data,
            slug=form.title.data.strip().lower().replace(' ', '-')
        ).where(models.Entry.id == entry.id).execute()
        new_tags = form.tags.data.split(',')
        # deletes existing Tag if it is removed in update data
        # and is not connected to any of the other Entries,
        # and deletes relationship(EntryTag) between Entry and removed Tag
        for tag in entry.get_tags():
            if tag.tag not in new_tags:
                if len(models.EntryTags.select().where(tag == tag.tag)) == 1:
                    tag.delete_instance()
                models.EntryTags.delete().where(
                    tag == tag, entry == entry
                    ).execute()
        # gets or creates tags given in update form and
        # creates relationship between them and entry if nonexistant
        for item in new_tags:
            tag, created = models.Tag.get_or_create(tag=item)
            models.EntryTags.get_or_create(tag=tag, entry=entry)

        flash("Entry successfully updated", "success")
        return redirect(url_for('index'))
    # populates the form with existing data when displaying the page
    elif request.method == 'GET':
        form.title.data = entry.title
        form.date.data = entry.date
        form.time_spent.data = entry.time_spent
        form.content.data = entry.content
        form.resources.data = entry.resources
        form.tags.data = ','.join([tag.tag for tag in entry.get_tags()])
    return render_template('edit.html', form=form,title="Edit Entry",
                           entry=entry)


# DELETE

@app.route('/entries/<slug>/delete', methods=['GET', 'POST'])
@login_required
def delete(slug):
    """Deletes chosen entry"""
    entry = models.Entry.select().where(models.Entry.slug == slug).get()
    if entry.author != current_user:
        abort(403)
    entry.delete_instance()
    return redirect(url_for('index'))


if __name__ == '__main__':
    models.initialize()
    app.run(debug=True)
