
import json
import re

from bs4 import BeautifulSoup


class Offer:
    """
    Klasa reprezentująca ofertę
    """
    field_names = ['kolor', 'kraj', 'liczba_miejsc', 'moc', 'naped', 'pojemnosc', 'przebieg', 'rodzaj_paliwa',
                   'rok_produkcji', 'uszkodzony', 'nadwozie', 'cena', 'waluta', 'marka', 'typ', 'model', 'id_oferty',
                   'tytul', 'nazwa_sprzedajacego', 'id_sprzedajacego', 'lokalizacja', 'miejscowosc', 'wojewodztwo']

    def __init__(self, logger):
        """Konstruktor inicjalizujący wartości domyślne dla atrytbutów oferty oraz zapisujący referencję do loggera

        :param logger:
        """
        self.logger = logger
        self.anomalie = ''
        for field in Offer.field_names:
            setattr(self, field, None)

    def post_process(self):
        """
        Metoda dostosowująca postać oferty (a konkretnie atrybuty).
        Tu następuje walidacja i ewentualna zmiana typu atrybutów cena i przebieg, moc, pojemność.
        Metoda tworzy także listę wykrytych anomalii.

        """

        anomalie = list()

        if isinstance(self.cena, str):
            try:
                self.cena = int(float(self.cena))
            except Exception:
                self.cena = 0
                self.logger.info('Anomalia dla atrybutu cena')
                anomalie.append('cena')

        if isinstance(self.przebieg, str):
            self.przebieg = self.przebieg.replace(' ', '')
            try:
                __temp = self.przebieg.upper()
                __temp = __temp.replace('KM', '')
                self.przebieg = int(float(__temp))
            except Exception:
                self.przebieg = 0
                self.logger.info('Anomalia dla atrybutu przebieg')
                anomalie.append('przebieg')

        self.pojemnosc = self.pojemnosc.upper().replace('CM3', '').replace('CM³', '').replace(' ','')
        self.moc = self.moc.upper().replace('KM', '').replace(' ','')

        self.anomalie = ", ".join(anomalie)

    def __repr__(self):
        return str(self.__dict__)


class AllegroOfferParser:
    """
    Implementacja klasy parsującej oferty z portalu Allegro
    """
    def __init__(self, logger):
        self.logger = logger

    def get_details(self, _data):
        """
        Implementacja parsera, który wydobywa wartości atrybutów oferty z przekazanego stringa (html)

        :param _data: string zawierający html z ofertą
        :return: obiekt klasy Offer
        """
        self.logger.info('Metoda get_details()')
        soup = BeautifulSoup(_data, 'html.parser')
        parameters_filtered = soup.find(attrs={"data-box-name": "Parameters"})

        labels = {"Kolor": 'kolor', "Kraj pochodzenia": 'kraj', "Liczba miejsc": 'liczba_miejsc', "Moc": 'moc',
                  "Napęd": 'naped', "Pojemność silnika": 'pojemnosc', "Przebieg": 'przebieg',
                  "Rodzaj paliwa": 'rodzaj_paliwa', "Rok produkcji": 'rok_produkcji', "Uszkodzony": 'uszkodzony',
                  "Nadwozie": 'nadwozie'}

        big_data = Offer(self.logger)

        for key, label in labels.items():
            anchor = parameters_filtered.find("div", text=key + ":")
            try:
                value = anchor.find_next_sibling("div").text

            except AttributeError as err:
                self.logger.info('Wyjątek dla klucza %s' % key)
                value = 'NULL'

            setattr(big_data, label, value)

        filtered = soup.find(itemprop="price")
        big_data.cena = filtered.get('content')

        filtered = soup.find(itemprop="priceCurrency")
        big_data.waluta = filtered.get('content')

        filtered = soup.find(content="index, follow")
        dataLayer_txt = filtered.find_next_sibling("script")
        dataLayer_txt = dataLayer_txt.text

        json_beginning = dataLayer_txt.find('{')
        json_ending = dataLayer_txt.rfind(']}')
        some_json = json.loads(dataLayer_txt[json_beginning:json_ending])

        navigation = some_json['headNavigation'].split('|')
        big_data.marka = navigation[3]
        big_data.typ = navigation[4]
        big_data.model = navigation[5]

        big_data.id_oferty = some_json['idItem']
        big_data.tytul = some_json['offerName']
        big_data.nazwa_sprzedajacego = some_json['sellerName']
        big_data.id_sprzedajacego = some_json['sellerId']

        filtered = soup.find(attrs={'data-analytics-interaction-value': "LocationShow"})
        if not filtered:
            filtered = soup.find(attrs={'data-analytics-interaction-value': "locationShow"})

        big_data.lokalizacja = filtered.text
        location = filtered.text.split(', woj. ')
        big_data.miejscowosc = location[0]
        big_data.wojewodztwo = location[1]

        big_data.post_process()
        return big_data


class OlxOfferParser:
    """
    Implementacja klasy parsującej oferty z portalu Olx
    """
    def __init__(self, logger):
        self.logger = logger

    def get_details(self, _data):
        """
        Implementacja parsera, który wydobywa wartości atrybutów oferty z przekazanego stringa (html)

        :param _data: string zawierający html z ofertą
        :return: obiekt klasy Offer
        """
        self.logger.info('Metoda get_details()')
        soup = BeautifulSoup(_data, 'html.parser')

        parameters_filtered = soup.find(class_='details fixed marginbott20 margintop5 full')

        labels = {"Kolor": 'kolor', "Kraj pochodzenia": 'kraj', "Liczba miejsc": 'liczba_miejsc', "Moc silnika": 'moc',
                  "Skrzynia biegów": 'naped', "Poj. silnika": 'pojemnosc', "Przebieg": 'przebieg',
                  "Paliwo": 'rodzaj_paliwa', "Rok produkcji": 'rok_produkcji', "Stan techniczny": 'uszkodzony',
                  "Typ nadwozia": 'nadwozie', 'Marka': 'marka', 'Model':'typ'}

        big_data = Offer(self.logger)
        big_data.model = ''
        for key, label in labels.items():
            anchor = parameters_filtered.find("th", text=key)
            try:
                value = anchor.find_next_sibling("td", attrs='value').text.strip()

            except AttributeError as err:
                self.logger.info('Wyjątek dla klucza %s' % key)
                value = 'NULL'

            setattr(big_data, label, value)

        pattern = re.compile('var trackingData.*siteUrl')

        matched = soup.find('script', text=pattern).text

        json_beginning = matched.find('{"$config"')
        json_ending = matched.find("}}'", json_beginning)

        txt = matched[json_beginning:json_ending+2]

        some_json = json.loads(txt)
        some_json = some_json['pageView']

        big_data.cena = some_json['ad_price']
        big_data.waluta = some_json['price_currency']
        big_data.id_sprzedajacego = some_json['seller_id']
        big_data.id_oferty = some_json['ad_id']

        big_data.lokalizacja = some_json['city_name'] + ', woj. ' + some_json['region_name']
        big_data.miejscowosc = some_json['city_name']
        big_data.wojewodztwo = some_json['region_name']
        big_data.nazwa_sprzedajacego = soup.find(class_="block brkword xx-large").text.strip()
        big_data.tytul = soup.find(class_='offer-titlebox').contents[1].text.strip()

        big_data.post_process()
        return big_data


class OtomotoOfferParser:
    """
    Implementacja klasy parsującej oferty z portalu Otomoto
    """
    def __init__(self, logger):
        self.logger = logger

    def get_details(self, _data):
        """
        Implementacja parsera, który wydobywa wartości atrybutów oferty z przekazanego stringa (html)

        :param _data: string zawierający html z ofertą
        :return: obiekt klasy Offer
        """
        self.logger.info('Metoda get_details()')
        soup = BeautifulSoup(_data, 'html.parser')

        parameters_filtered = soup.find(id='parameters')

        labels = {"Kolor": 'kolor', "Kraj pochodzenia": 'kraj', "Liczba miejsc": 'liczba_miejsc', "Moc": 'moc',
                  "Napęd": 'naped', "Pojemność skokowa": 'pojemnosc', "Przebieg": 'przebieg',
                  "Rodzaj paliwa": 'rodzaj_paliwa', "Rok produkcji": 'rok_produkcji', "Bezwypadkowy": 'uszkodzony',
                  "Typ": 'nadwozie', 'Marka pojazdu': 'marka', 'Model pojazdu': 'typ', 'Wersja':'model'}

        big_data = Offer(self.logger)

        for key, label in labels.items():
            anchor = parameters_filtered.find("span", text=key)
            try:
                value = anchor.find_next_sibling("div").text.strip()

                # na pierwszy rzut oka pojawia się konsternacja, ale to wynika z wykorzystania przeciwstawnych określeń
                # dla stanu auta (bezwypadkowy vs uszkodzony)
                if key == 'Bezwypadkowy':
                    if value == 'Tak':
                        value = 'Nie'
                    elif value == 'Nie':
                        value = 'Tak'

            except AttributeError as err:
                self.logger.info('Wyjątek dla klucza %s' % key)
                value = 'NULL'

            setattr(big_data, label, value)

        pattern = re.compile('window.ninjaPV = {')
        matched = soup.find('script', text=pattern).text

        json_beginning = matched.find('window.ninjaPV = {')
        json_beginning = matched.find('{', json_beginning)
        json_ending = matched.find("};", json_beginning)

        txt = matched[json_beginning:json_ending+1]

        some_json = json.loads(txt)

        big_data.cena = some_json['ad_price']
        big_data.waluta = some_json['price_currency']
        big_data.id_sprzedajacego = some_json['seller_id']
        big_data.id_oferty = some_json['ad_id']

        big_data.lokalizacja = some_json['city_name'] + ', woj. ' + some_json['region_name']
        big_data.miejscowosc = some_json['city_name']
        big_data.wojewodztwo = some_json['region_name']

        big_data.nazwa_sprzedajacego = soup.find(class_='seller-box__seller-name').text.replace('\n', '').strip()

        title_beginning = _data.find('var ad_title=')
        title_beginning = _data.find("'", title_beginning)
        title_ending = _data.find("';", title_beginning)
        title_contents = _data[title_beginning+1:title_ending].strip()
        big_data.tytul = title_contents

        big_data.post_process()
        return big_data


class Autoscout24OfferParser:
    """
    Implementacja klasy parsującej oferty z portalu Autoscout24
    """

    def __init__(self, logger):
        self.logger = logger

    def get_details(self, _data):
        """
        Implementacja parsera, który wydobywa wartości atrybutów oferty z przekazanego stringa (html)

        :param _data: string zawierający html z ofertą
        :return: obiekt klasy Offer
        """
        self.logger.info('Metoda get_details()')
        soup = BeautifulSoup(_data, 'html.parser')

        parameters_filtered = soup.find(name='s24-ad-targeting', attrs={'style': 'display:none;'})
        parameters_filtered = json.loads(parameters_filtered.text)

        big_data = Offer(self.logger)

        big_data.cena = parameters_filtered['cost']
        big_data.waluta = 'EUR'

        if parameters_filtered['fuel'][0] == 'D':
            big_data.rodzaj_paliwa = 'Diesel'
        elif parameters_filtered['fuel'][0] == 'B':
            big_data.rodzaj_paliwa = 'Benzyna'
        else:
            big_data.rodzaj_paliwa = None

        labels = {"sthp": 'moc', "Napęd": 'naped', "stccm": 'pojemnosc', "stmil": 'przebieg', "styea": 'rok_produkcji',
                  "uszkodzony": 'uszkodzony', 'stmak': 'marka', 'stmod': 'typ'}

        for key, label in labels.items():
            try:
                value = parameters_filtered[key]
            except Exception:
                self.logger.info('Wyjątek dla klucza %s' % key)
                value = None

            setattr(big_data, label, value)

        if isinstance(big_data.moc, int):
            big_data.moc = str(big_data.moc)
        elif big_data.moc is None:
            big_data.moc = ''

        if isinstance(big_data.pojemnosc, int):
            big_data.pojemnosc = str(big_data.pojemnosc)
        elif big_data.pojemnosc is None:
            big_data.pojemnosc = ''

        labels = {'Kolor zewnętrzny': 'kolor', 'Typ nadwozia': 'nadwozie', 'Miejsca siedzące': 'liczba_miejsc'}

        filtered = soup.find(class_='cldt-categorized-data cldt-data-section sc-pull-right')

        for key, label in labels.items():
            anchor = filtered.find("dt", text=key)
            try:
                value = anchor.find_next_sibling("dd").text
                value = value.replace('\n', '').strip()

            except Exception as err:
                value = None

            setattr(big_data, label, value)

        big_data.id_oferty = soup.find(class_='btn-watchlist cldt-action-icon').attrs['data-classified-guid'].strip()

        try:
            user_name = soup.find(attrs={'data-item-name': 'vendor-company-name'}).text.strip()
        except Exception:
            self.logger.info("Wyjątek dla 'data-item-name': 'vendor-company-name'")
            user_name = None

        if user_name is None:
            try:
                user_name = soup.find(attrs={'data-item-name': 'vendor-private-seller-title'}).text.strip()
            except Exception:
                self.logger.info("Wyjątek dla data-item-name': 'vendor-private-seller-title'")
                user_name = None

        big_data.nazwa_sprzedajacego = user_name
        big_data.id_sprzedajacego = user_name

        try:
            location = soup.find(attrs={'data-item-name': 'vendor-contact-city'}).text.strip()
        except AttributeError:
            self.logger.info("Wyjątek dla 'data-item-name': 'vendor-contact-city'")
            location = ''

        try:
            country = soup.find(attrs={'data-item-name': 'vendor-contact-country'}).text.strip()
        except AttributeError:
            self.logger.info("Wyjątek dla 'data-item-name': 'vendor-contact-city'")
            country = ''

        big_data.lokalizacja = location + ' ' + country
        big_data.kraj = ''
        big_data.miejscowosc = location
        big_data.wojewodztwo = ''

        big_data.tytul = soup.find('div', attrs={'data-type': "title"}).text
        big_data.naped = ''
        big_data.model = ''
        big_data.uszkodzony = ''

        big_data.post_process()
        return big_data
