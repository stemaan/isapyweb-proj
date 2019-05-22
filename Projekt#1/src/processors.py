
# tqdm nie działa najlepiej w oknie PyCharm, polecam uruchamianie z terminala/linii poleceń
import tqdm

import time
import logging
import sys

from models import Kampanie, Oferty, Portale
from sqlalchemy import func
from db_engine import Session

from parsers import AllegroOfferParser, Autoscout24OfferParser, OlxOfferParser, OtomotoOfferParser
from downloaders import AllegroDownloader, AutoScout24Downloader, OlxDownloader, OtomotoDownloader
from fileloaders import AllegroFileloader, AutoScout24Fileloader, OlxFileloader, OtomotoFileloader

allegro_categories_mapping = {
    'ford focus mk3': 'focus-mk3-2010-110752',
    'passat b8':'passat-b8-2014-250759' }

olx_categories_mapping = {
    'ford focus mk3': 'ford/focus/',
    'passat b8': 'volkswagen/passat'}

otomoto_categories_mapping = {
    'ford focus mk3': 'ford/focus/mk3-2010',
    'passat b8': 'volkswagen/passat'}

autoscout24_categories_mapping = {
    'ford focus mk3': 'ford/focus/',
    'passat b8': 'volkswagen/passat'}

all_categories_mappings = {
    'Allegro': allegro_categories_mapping,
    'Olx': olx_categories_mapping,
    'Otomoto': otomoto_categories_mapping,
    'Autoscout24': autoscout24_categories_mapping
                            }


class PortalProcessor:
    """
    Klasa bazowa dla procesorów ofert. Celem działania procesora jest przeprowadzenie procesu:
    #. pozyskanie surowych danych (z portalu lub pliku)
    #. wydobycie żądanych danych
    #. zapis danych w bazie danych
    """

    def __init__(self, logger, portal_name, api, session):
        """
        Inicjalizacja wartości początkowych

        :param logger: obiekt loggera
        :param portal_name: nazwa portalu
        :param api: informacja o użytym API
        :param session: sesja bazy danych
        """
        self.logger = logger
        self.portal_name = portal_name
        self.api = api
        self.session = session
        self._offer_downloader = None
        self._offer_parser = None
        self.offer_downloader = None
        self.offer_parser = None

    def create_campaign(self):
        """
        Utworzenie kampanii na potrzeby ładowania danych do bazy danych. Metoda zakłada także portal, jeśli go nie było.

        """
        self.portal = my_session.query(Portale).filter(Portale.nazwa_portalu == self.portal_name).first()
        if self.portal is None:
            self.logger.info('Tworzenie portalu %s' % self.portal_name)
            self.portal = Portale(nazwa_portalu=self.portal_name)
            self.session.add(self.portal)
            self.session.commit()

        self.logger.info('Tworzenie kampanii')
        self.kampania = Kampanie(data=func.now(), id_portalu=self.portal.idx, rodzaj_api=self.api)
        self.session.add(self.kampania)
        self.session.commit()

    def start_plugins(self):
        """
        Instancjowanie przekazanych klas parsera i downloadera

        """
        self.logger.info('Tworzenie parsera')
        self.offer_parser = self._offer_parser(self.logger)
        self.logger.info('Tworzenie downloadera')
        self.offer_downloader = self._offer_downloader(self.logger)

    def prepare_campaign(self):
        """
        Przygotowanie obiektów do pracy

        """
        self.create_campaign()
        self.start_plugins()

    def download_offers_from_list(self, list_of_links, save):
        """
        Metoda realizująca główną pętlę przetwania. Dla wybranych namiarów na oferty wykonywane są następujące kroki:
        #. ściąganie oferty
        #. wydobywanie danych z oferty
        #. zapis obiektu ofertu w bazie danych
        Przetwarzaniu towarzyszy pasek postępu


        :param list_of_links: lista namiarów na oferty
        :param save: informacja czy oferty mają zostać zapisane na potrzeby deweloperskie/analizy
        """
        for link in tqdm.tqdm(list_of_links):
            self.logger.info('Ściąganie z %s' % link)
            try:
                offer_html = self.offer_downloader.download_offer(link, save=save)
            except Exception as exc:
                self.logger.debug('Wystąpił wyjątek dla metody download_offer() dla linku %s: %s' % (link, exc))
                return

            try:
                offer_json = self.offer_parser.get_details(offer_html)
            except Exception as exc:
                self.logger.debug('Wystąpił wyjątek dla metody get_details() dla linku %s: %s' % (link, exc))
                return

            offer_object = Oferty()

            offer_object.id_kampanii = self.kampania.idx

            fields = list(offer_json.__dict__.keys())

            self.logger.info('Przepisywanie wartości')
            for field in fields:
                setattr(offer_object, field, getattr(offer_json, field))

            self.session.add(offer_object)
            self.session.commit()
            self.logger.info('Oferta została zapisana w bazie')

    def process(self, _category, number_of_offers, save):
        """
        Wyświetlenie informacji o rozpoczęciu przetwarzania, odczyt zamapowania kategorii, uruchomienie głównego przetwarzania.

        :param _category: uniweralna wartość kategorii, na podstawie której zostanie odczyta kategoria specyficzna dla portalu
        :param number_of_offers: liczba ofert do przetworzenia
        :param save: informacja czy oferty mają zostać zapisane na potrzeby deweloperskie/analizy
        :return:
        """
        template = 'Ściaganie %s, kategoria: %s, number of offers: %s'
        print(template % (self.portal_name, _category, number_of_offers))
        self.logger.info(template % (self.portal_name, _category, number_of_offers))

        category = all_categories_mappings[self.portal_name][_category]
        links = self.offer_downloader.download_number_of_links(category, number_of_offers=number_of_offers, save=save)
        self.download_offers_from_list(links, save=True)


class AllegroProcessor(PortalProcessor):
    """
    Implementacja procesora dla Allegro
    """

    def __init__(self, logger, session, provider="portal"):
        """
        Inicjalizacja procesora

        :param logger: obiekt współdzielonego loggera
        :param session: obiekt sesji bazodanowej
        :param provider: informacja o klasie dostarczającej obiekty
        """
        self.portal_name = 'Allegro'
        self.api = 'scrapper'
        logger.info('Inicjalizacja procesora: %s, api: %s' % (self.portal_name, self.api))
        self.session = session
        super().__init__(logger, self.portal_name, self.api, self.session)
        self._offer_parser = AllegroOfferParser
        if provider == "portal":
            self._offer_downloader = AllegroDownloader
        elif provider == "file":
            self._offer_downloader = AllegroFileloader
        else:
            raise ModuleNotFoundError


class OtomotoProcessor(PortalProcessor):
    """
    Implementacja procesora dla Otomoto
    """

    def __init__(self, logger, session, provider="portal"):
        """
        Inicjalizacja procesora

        :param logger: obiekt współdzielonego loggera
        :param session: obiekt sesji bazodanowej
        :param provider: informacja o klasie dostarczającej obiekty
        """

        self.portal_name = 'Otomoto'
        self.api = 'scrapper'
        logger.info('Inicjalizacja procesora: %s, api: %s' % (self.portal_name, self.api))
        self.session = session
        super().__init__(logger, self.portal_name, self.api, self.session)
        self._offer_parser = OtomotoOfferParser
        if provider == "portal":
            self._offer_downloader = OtomotoDownloader
        elif provider == "file":
            self._offer_downloader = OtomotoFileloader
        else:
            raise ModuleNotFoundError


class Autoscout24Processor(PortalProcessor):
    """
    Implementacja procesora dla Autoscout24
    """

    def __init__(self, logger, session, provider="portal"):
        """
        Inicjalizacja procesora

        :param logger: obiekt współdzielonego loggera
        :param session: obiekt sesji bazodanowej
        :param provider: informacja o klasie dostarczającej obiekty
        """

        self.portal_name = 'Autoscout24'
        self.api = 'scrapper'
        logger.info('Inicjalizacja procesora: %s, api: %s' % (self.portal_name, self.api))
        self.session = session
        super().__init__(logger, self.portal_name, self.api, self.session)
        self._offer_parser = Autoscout24OfferParser
        if provider == "portal":
            self._offer_downloader = AutoScout24Downloader
        elif provider == "file":
            self._offer_downloader = AutoScout24Fileloader
        else:
            raise ModuleNotFoundError

    def asc_process(self, _category, number_of_offers, from_year, to_year, save):
        """
        Specyficzna implementacja dla Autoscout24 ze względu na większą liczbę parametrów niż standardowa

        :param _category: uniweralna wartość kategorii, na podstawie której zostanie odczyta kategoria specyficzna dla portalu
        :param number_of_offers: liczba ofert do przetworzenia
        :param from_year: rok początkowy
        :param to_year: rok końcowy
        :param save: informacja czy oferty mają zostać zapisane na potrzeby deweloperskie/analizy
        :return:
        """

        template = 'Ściąganie z %s, kategoria: %s, number of offers: %s'
        print(template % (self.portal_name, _category, number_of_offers))
        self.logger.info(template % (self.portal_name, _category, number_of_offers))

        category = all_categories_mappings[self.portal_name][_category]
        links = self.offer_downloader.download_number_of_links(category, number_of_offers=number_of_offers, from_year=from_year, to_year=to_year, save=save)
        self.download_offers_from_list(links, save=True)


class OlxProcessor(PortalProcessor):
    """
    Implementacja procesora dla Olx
    """
    def __init__(self, logger, session, provider="portal"):
        """
        Inicjalizacja procesora

        :param logger: obiekt współdzielonego loggera
        :param session: obiekt sesji bazodanowej
        :param provider: informacja o klasie dostarczającej obiekty
        """
        self.portal_name = 'Olx'
        self.api = 'scrapper'
        logger.info('Inicjalizacja procesora: %s, api: %s' % (self.portal_name, self.api))
        self.session = session
        super().__init__(logger, self.portal_name, self.api, self.session)
        self._offer_parser = OlxOfferParser
        if provider == "portal":
            self._offer_downloader = OlxDownloader
        elif provider == "file":
            self._offer_downloader = OlxFileloader
        else:
            raise ModuleNotFoundError


def test_allegro_processor(logger, session, provider):
    processor = AllegroProcessor(logger=logger, session=session, provider=provider)
    processor.prepare_campaign()
    category = 'ford focus mk3'
    processor.process(category, number_of_offers=4, save=True)
    category = 'passat b8'
    processor.process(category, number_of_offers=4, save=True)


def test_otomoto_processor(logger, session, provider):
    processor = OtomotoProcessor(logger=logger, session=session, provider=provider)
    processor.prepare_campaign()
    category = 'ford focus mk3'
    processor.process(category, number_of_offers=4, save=True)
    category = 'passat b8'
    processor.process(category, number_of_offers=4, save=True)


def test_olx_processor(logger, session, provider):
    processor = OlxProcessor(logger=logger, session=session, provider=provider)
    processor.prepare_campaign()
    category = 'ford focus mk3'
    processor.process(category, number_of_offers=4, save=True)
    category = 'passat b8'
    processor.process(category, number_of_offers=4, save=True)


def test_autoscout24_processor(logger, session, provider):
    processor = Autoscout24Processor(logger=logger, session=session, provider=provider)
    processor.prepare_campaign()
    category = 'ford focus mk3'
    processor.asc_process(category, number_of_offers=4, from_year=2005, to_year=2011, save=True)
    category = 'passat b8'
    processor.asc_process(category, number_of_offers=4, from_year=2014, to_year=2019, save=True)


if __name__ == '__main__':
    start_time = time.time()

    my_logger = logging.getLogger('Offers_processor')
    logging.basicConfig(filename='{}.log'.format(sys.argv[0]), level=logging.DEBUG)

    my_provider = "portal"
    my_session = Session()

    test_allegro_processor(my_logger, my_session, my_provider)
    test_otomoto_processor(my_logger, my_session, my_provider)
    test_olx_processor(my_logger, my_session, my_provider)
    test_autoscout24_processor(my_logger, my_session, my_provider)

    stop_time = time.time()
    print('Duration: {0:.3} seconds'.format(stop_time - start_time))
