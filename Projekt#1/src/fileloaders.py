import os


class PortalFileloader:
    """
    Klasa bazowa na potrzeby odczytu ofert z dysku
    """
    def __init__(self, logger, offer_folder='offers'):
        """Konstruktor dla klasy bazowej

        :param logger: obiekt loggera
        :param offer_folder: folder nadrzędny dla folderów z ofertami
        """
        self.offer_folder = offer_folder
        self.logger = logger

    def download_offer(self, link, save=False):
        """
        Metoda odczytująca ofertę o przekazanej nazwie

        :param link: nazwa oferty
        :param save: parametr pomijany, obecny dla kompatybilności z klasami downloaders
        :return: string z html oferty
        """
        full_file_name = os.path.join(self.offer_folder, link)
        self.logger.info('Odczyt pliku: %s' % full_file_name)
        with open(full_file_name, 'r', encoding='utf-8') as file_in:
            html = file_in.read()
        return html

    def download_number_of_links(self, category, number_of_offers=-1, save=False):
        """
        Metoda zwracająca liczbę plików ofert dla danego portalu znajdujących się na dysku

        :param category: parametr pomijany, obecny dla kompatybilności z klasami downloaders
        :param number_of_offers: liczba ofert
        :param save: parametr pomijany, obecny dla kompatybilności z klasami downloaders
        :return: lista nazw plików
        """
        file_list = os.listdir(self.offer_folder)
        if number_of_offers == -1:
            return file_list
        else:
            return file_list[:number_of_offers]


class AllegroFileloader(PortalFileloader):
    """
    Implementacja dla plików portalu Allegro
    """
    def __init__(self, logger):
        """
        Konstruktor inicjalizujący wartości domyślne dla klasy Otomoto

        :param logger: obiekt współdzielonego loggera
        """
        super().__init__(logger=logger, offer_folder='offers/allegro')


class OlxFileloader(PortalFileloader):
    """
    Implementacja dla plików portalu OLx
    """
    def __init__(self, logger):
        """
        Konstruktor inicjalizujący wartości domyślne dla klasy Olx

        :param logger: obiekt współdzielonego loggera
        """
        super().__init__(logger=logger, offer_folder='offers/olx')


class OtomotoFileloader(PortalFileloader):
    """
    Implementacja dla plików portalu Otomoto
    """
    def __init__(self, logger):
        """
        Konstruktor inicjalizujący wartości domyślne dla klasy Otomoto

        :param logger: obiekt współdzielonego loggera
        """
        super().__init__(logger=logger, offer_folder='offers/otomoto')


class AutoScout24Fileloader(PortalFileloader):
    """
    Implementacja dla plików portalu AutoScout24
    """
    def __init__(self, logger):
        """
        Konstruktor inicjalizujący wartości domyślne dla klasy AutoScout24

        :param logger: obiekt współdzielonego loggera
        """
        super().__init__(logger=logger, offer_folder='offers/autoscout24')

    def download_number_of_links(self, category, number_of_offers=-1, from_year=2000, to_year=2001, save=False):
        """
        Metoda specyficzna dla portalu AutoScout24

        :param category: parametr pomijany, obecny dla kompatybilności z klasami downloaders
        :param number_of_offers: liczba_ofert
        :param from_year: parametr pomijany, obecny dla kompatybilności z klasami downloaders
        :param to_year: parametr pomijany, obecny dla kompatybilności z klasami downloaders
        :param save: parametr pomijany, obecny dla kompatybilności z klasami downloaders
        :return:
        """
        return super().download_number_of_links(category=category, number_of_offers=number_of_offers, save=save)
