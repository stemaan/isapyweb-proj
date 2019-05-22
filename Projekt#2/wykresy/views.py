import os
import time
import hashlib
import pandas as pd
import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from flask import render_template, redirect, url_for, flash
from flask_login import current_user, login_user, logout_user, login_required
from flask.views import View

from . import app, db
from . import ROZMIARY

from .models import Kampanie, Oferty, Portale, User
from .forms import LoginForm, GraphForm


class ListView(View):
    def get_template_name(self):
        raise NotImplementedError()

    def render_template(self, context):
        return render_template(self.get_template_name(), **context)

    def dispatch_request(self):
        context = {'objects': self.get_objects()}
        return self.render_template(context)

    def get_objects(self):
        raise NotImplementedError()


class Statystyki(ListView):
    decorators = [login_required]

    def get_template_name(self):
        return 'statystyki.html'

    def get_objects(self):
        liczba_kampanii = Kampanie.query.count()
        liczba_ofert = Oferty.query.count()
        liczba_portali = Portale.query.count()

        najstarsze_auto = db.session.query(db.func.min(Oferty.rok_produkcji)).one()[0]
        najmlodsze_auto = db.session.query(db.func.max(Oferty.rok_produkcji)).one()[0]
        najtansze_auto = db.session.query(db.func.min(Oferty.cena)).one()[0]
        najdrozsze_auto = db.session.query(db.func.max(Oferty.cena)).one()[0]
        najmniejszy_przebieg = db.session.query(db.func.min(Oferty.przebieg)).one()[0]
        najwiekszy_przebieg = db.session.query(db.func.max(Oferty.przebieg)).one()[0]

        context = {'Liczba kampanii': liczba_kampanii, 'Liczba ofert': liczba_ofert, 'Liczba portali': liczba_portali}
        context.update({'Najstarszy rocznik': najstarsze_auto})
        context.update({'Najmłodszy rocznik': najmlodsze_auto})
        context.update({'Najtańsze auto': najtansze_auto})
        context.update({'Najdroższe auto': najdrozsze_auto})
        context.update({'Najmniejszy przebieg': najmniejszy_przebieg})
        context.update({'Największy przebieg': najwiekszy_przebieg})
        return context


class Pomocnik(ListView):
    def get_template_name(self):
        return 'pomocnik.html'

    def get_objects(self):
        context = list()
        context.append(('app.root_path', app.root_path))
        context.append(('app.instance_path', app.instance_path))
        context.append(("app.config['SQLALCHEMY_DATABASE_URI']", app.config['SQLALCHEMY_DATABASE_URI']))
        context.append(("app.config['PANDAS_DATABASE_URI']", app.config['PANDAS_DATABASE_URI']))
        context.append(('', ''))
        context.append(('', ''))

        for key, value in app.config.items():
            context.append((key, value))
        context.append(('', ''))
        context.append(('', ''))

        for rule in app.url_map.iter_rules():
            line = "{} {}".format(rule.endpoint, ','.join(rule.methods))
            context.append((rule, line))

        return context


@app.route('/index')
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/graph', methods=['GET', 'POST'])
@login_required
def graph():

    oferty_df = pd.read_sql_table('oferty', str(app.config['PANDAS_DATABASE_URI']), index_col='idx')
    marki_list = list(set(oferty_df.marka))
    roczniki_list = list(sorted(set(oferty_df.rok_produkcji)))

    form = GraphForm()
    choices = list()
    choices.append(['Wszystkie', 'Wszystkie'])
    choices.extend([(marka, marka) for marka in marki_list])
    form.marka.choices = choices
    form.marka.default = choices[0][0]
    form.rocznik_min.choices = [(rocznik, rocznik) for rocznik in roczniki_list]
    form.rocznik_max.choices = [(rocznik, rocznik) for rocznik in roczniki_list]
    form.rocznik_min.default = "2000"
    form.rocznik_max.default = "2019"

    if form.is_submitted():
        if form.data['marka'] == 'Wszystkie':
            marki = marki_list
        else:
            marki = [form.data['marka'], ]

        rocznik_start = int(form.data['rocznik_min'])
        rocznik_stop = int(form.data['rocznik_max'])

        fig, ax = plt.subplots(figsize=ROZMIARY)
        fig.suptitle('Marki - przebieg')

        ax.set_ylabel('Przebieg w km')
        ax.set_xlabel('Rocznik')

        for marka in marki:
            ofx = oferty_df[
                (oferty_df.marka == marka) &
                (oferty_df.przebieg > 10000) &
                (oferty_df.rok_produkcji.between(rocznik_start, rocznik_stop))
                ].groupby('rok_produkcji')

            ax.plot(ofx.przebieg.mean(), label=marka)

        ax.legend(loc=2)

        folder_name = os.path.join(app.root_path, 'static', 'images')
        file_name = '%s.png' % time.time()
        fig.savefig(os.path.join(folder_name, file_name))

        return render_template('graph.html', filename='images/%s' % file_name,
                               form=form, marka=marki, zakres_lat=(rocznik_start, rocznik_stop))
    else:
        form.process()
        return render_template('graph_form.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        flash('Już jesteś zalogowany')
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        hashed_password = hashlib.md5(form.password.data.encode()).hexdigest()
        user = User.query.filter_by(login=form.login.data, password=hashed_password).first()

        if user is None:
            flash('Niepoprawny login i/lub hasło')
            return redirect(url_for('login'))

        login_user(user)
        flash('Zostałeś zalogowany')
        return redirect(url_for('index'))

    return render_template('login_form.html', form=form, tytul='Skorzystaj z panelu logowania')


@app.route('/logout')
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash('Zostałeś wylogowany')
        return redirect(url_for('index'))

    flash('Nie byłeś zalogowany')
    return redirect(url_for('index'))


@app.route('/add_user', methods=['GET', 'POST'])
@login_required
def add_user():
    form = LoginForm()

    if form.validate_on_submit():
        existing_user = User.query.filter_by(login=form.login.data).first()
        if existing_user is None:
            user = User()
            user.login = form.login.data
            user.password = hashlib.md5(form.password.data.encode()).hexdigest()

            db.session.add(user)
            db.session.commit()
            flash('Konto zostało założone')
            return redirect(url_for('add_user'))

        else:
            flash('Konto o tym loginie już istnieje w systemie')
            return redirect(url_for('add_user'))

    return render_template('login_form.html', form=form, tytul='Utwórz konto użytkownika systemu')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def catch_all(path):
    return 'Nastąpiła próba otwarcia nietypowej ścieżki: %s' % path


app.add_url_rule('/statystyki', view_func=Statystyki.as_view('statystyki'))
app.add_url_rule('/pomocnik', view_func=Pomocnik.as_view('pomocnik'))
