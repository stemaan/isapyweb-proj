import os
import requests
from bs4 import BeautifulSoup


class PortalDownloader:
    """Klasa bazowa dla downloaderów
    """
    def __init__(self, logger, offer_folder='offers', listing_folder='listings'):
        """Konstruktor dla klasy bazowej - zakłada foldery

        :param logger: obiekt loggera
        :param offer_folder: folder w którym zapisywane będą (opcjonalnie) oferty
        :param listing_folder:  folder w którym zapisywane będą (opcjonalnie) listingi
        """
        self.logger = logger
        self.offer_folder = offer_folder
        self.listing_folder = listing_folder
        self.offer_link_prefix = None

        if not os.path.isdir(self.offer_folder):
            os.makedirs(self.offer_folder)
        if not os.path.isdir(self.listing_folder):
            os.makedirs(self.listing_folder)

    def save_file(self, folder_name, file_name, data):
        """Metoda na potrzeby zapisu plików (oferty i listingi)

        :param folder_name: nazwa folderu
        :param file_name: nazwa pliku
        :param data: dane tekstowe
        :return: metoda nie zwraca danych
        """
        full_file_name = os.path.join(folder_name, file_name)
        self.logger.info('Zapis pliku %s' % full_file_name)
        with open(full_file_name, 'w', encoding='UTF-8') as file_out:
            file_out.write(data)

    @staticmethod
    def download_offer(offer_url, save):
        """Metoda statyczna na potrzeby ściągania oferty, zostanie przykryta dostarczoną implementacją

        :param offer_url: link do oferty
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądaną ofertę
        """
        raise NotImplemented

    @staticmethod
    def download_listing_page(category, page, save):
        """
        Metoda statyczna na potrzeby ściągania listingu, zostanie przykryta dostarczoną implementacją

        :param category: kategoria z której ściągane są sane
        :param page: numer kolejny strony listingów
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądany listing
        """
        raise NotImplemented

    @staticmethod
    def get_number_of_listings(html):
        """Metoda statyczna na potrzeby ustalenia liczby dostępnych listingów

        :param html: string z html na podstawie którego należy ustalić liczbę dostępnych listningów
        :return: int
        """
        raise NotImplemented

    def get_links_from_listing(self, html, offer_link):
        """Metoda wydobywająca linki z stringa reprezentującego html

        :param html: string zawierający html
        :param offer_link: wyróżnik linków, które należy wydobyć
        :return: lista unikalnych linków
        """
        self.logger.info('Wyszukiwanie linków')
        soup = BeautifulSoup(html, 'html.parser')
        filtered = soup.findAll('a')
        links_in_filtered = list()

        for item in filtered:
            if item.has_attr('href'):
                if item['href'].startswith(offer_link):
                    links_in_filtered.append(item['href'])

        return set(links_in_filtered)

    def download_number_of_links(self, category, number_of_offers=-1, save=False):
        """Metoda wydobywającą określoną liczbę linków dla wskazanej kategorii.

        :param category: kategoria ofert
        :param number_of_offers: liczba ofert
        :param save: flaga: czy zapisywać listingi
        :return: lista linków z wybranej kategorii. Liczba zwróconych linków <= żądana liczba linków
        """
        self.logger.info('Pozyskiwanie linków')
        first_listing = self.download_listing_page(category, page=1, save=save)
        number_of_listings = self.get_number_of_listings(first_listing)
        temp_listing_number = 1
        all_links = list()

        while temp_listing_number <= number_of_listings:
            listing_page = self.download_listing_page(category, temp_listing_number, save)
            links_from_listing = self.get_links_from_listing(listing_page, self.offer_link_prefix)
            all_links.extend(links_from_listing)

            temp_listing_number += 1
            if number_of_offers == -1:
                continue
            else:
                if len(all_links) >= number_of_offers:
                    break

        if number_of_offers != -1:
            all_links = all_links[:number_of_offers]

        return all_links


class OtomotoDownloader(PortalDownloader):
    """
    Implementacja dla portalu Otomoto
    """
    def __init__(self, logger):
        """
        Konstruktor inicjalizujący wartości domyślne dla klasy Otomoto

        :param logger: obiekt współdzielonego loggera
        """
        super().__init__(logger=logger, offer_folder='offers/otomoto')
        self.base_url = 'https://www.otomoto.pl/'
        self.listing_url1 = self.base_url + 'osobowe/{}/'
        self.listing_url2 = self.base_url + 'osobowe/{}/?page={}'
        self.offer_link_prefix = self.base_url + 'oferta/'

    @staticmethod
    def get_number_of_listings(html):
        """Implementacja metody dla klasy Otomoto

        :param html: string zawierający kod html
        :return: liczba listingów dostępnych na portalu
        """
        soup = BeautifulSoup(html, 'html.parser')
        filtered = soup.find(attrs={"class": "om-pager rel"})
        filtered = filtered.findAll('span', attrs={"class": "page"})
        numbers = [int(element.text) for element in filtered if element.text.isdigit()]
        return max(numbers)

    def download_offer(self, offer_url, save=False):
        """Implementacja metody dla klasy Otomoto

        :param offer_url: link do oferty
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądaną ofertę
        """
        data = requests.get(offer_url)
        data = data.text

        if save:
            soup = BeautifulSoup(data, 'html.parser')
            filtered = soup.find('span', attrs={"class": "om-button blue spoiler seller-phones__button"})
            offer_id = filtered['data-id_raw']
            file_name = 'offer_{}.html'.format(offer_id)
            self.save_file(self.offer_folder, file_name, data)
        return data

    def download_listing_page(self, category, page=1, save=False):
        """Implementacja metody dla klasy Otomoto

        :param category: kategoria z której ściągane są sane
        :param page: numer kolejny strony listingów
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądany listing
        """
        if page == 1:
            url = self.listing_url1.format(category)
        else:
            url = self.listing_url2.format(category, page)

        data = requests.get(url)
        data = data.text

        if save:
            file_name = 'listing_{}_{}.html'.format(category.replace('/', '_'), page)
            self.save_file(self.listing_folder, file_name, data)

        return data


class AllegroDownloader(PortalDownloader):
    """
    Implementacja dla portalu Allegro
    """
    def __init__(self, logger):
        """
        Konstruktor inicjalizujący wartości domyślne dla klasy Allegro

        :param logger: obiekt współdzielonego loggera
        """
        super().__init__(logger=logger, offer_folder='offers/allegro')
        self.base_url = 'https://allegro.pl/'
        self.listing_url = self.base_url + 'kategoria/{}?order=m&p={}'
        self.offer_link_prefix = self.base_url + 'ogloszenie'

    @staticmethod
    def get_number_of_listings(html):
        """Implementacja metody dla klasy Allegro

        :param html: string zawierający kod html
        :return: liczba listingów dostępnych na portalu
        """
        soup = BeautifulSoup(html, 'html.parser')
        filtered = soup.find(attrs={"class": "m-pagination__text"})
        return int(filtered.get_text())

    def download_offer(self, offer_url, save=False):
        """Implementacja metody dla klasy Allegro

        :param offer_url: link do oferty
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądaną ofertę
        """
        data = requests.get(offer_url)
        data = data.text

        if save:
            offer_id = offer_url.split('-')[-1]
            file_name = 'offer_{}.html'.format(offer_id)
            self.save_file(self.offer_folder, file_name, data)
        return data

    def download_listing_page(self, category, page=1, save=False):
        """Implementacja metody dla klasy Allegro

        :param category: kategoria z której ściągane są sane
        :param page: numer kolejny strony listingów
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądany listing
        """
        url = self.listing_url.format(category, page)
        data = requests.get(url)
        data = data.text

        if save:
            file_name = 'listing_{}_{}.html'.format(category, page)
            self.save_file(self.listing_folder, file_name, data)

        return data


class OlxDownloader(PortalDownloader):
    """
    Implementacja dla portalu Olx
    """

    def __init__(self, logger):
        """
        Konstruktor inicjalizujący wartości domyślne dla klasy Olx

        :param logger: obiekt współdzielonego loggera
        """
        super().__init__(logger=logger, offer_folder='offers/olx')
        self.base_url = 'https://www.olx.pl/'
        self.listing_url1 = self.base_url + 'motoryzacja/samochody/{}/'
        self.listing_url2 = self.base_url + 'motoryzacja/samochody/{}/?page={}'
        self.offer_link_prefix = self.base_url + 'oferta/'

    @staticmethod
    def get_number_of_listings(html):
        """Implementacja metody dla klasy Olx

        :param html: string zawierający kod html
        :return: liczba listingów dostępnych na portalu
        """
        soup = BeautifulSoup(html, 'html.parser')
        filtered = soup.find(attrs={"class": "pager rel clr"})
        filtered = filtered.findAll('span', attrs={"class": "item fleft"})

        numbers = [int(element.text.strip()) for element in filtered if element.text.strip().isdigit()]
        return max(numbers)

    def download_offer(self, offer_url, save=False):
        """Implementacja metody dla klasy Olx

        :param offer_url: link do oferty
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądaną ofertę
        """
        data = requests.get(offer_url)
        data = data.text

        if save:
            soup = BeautifulSoup(data, 'html.parser')
            filtered = soup.find('div', attrs={"class": "clm-samurai"})
            offer_id = filtered['data-item']
            file_name = 'offer_{}.html'.format(offer_id)
            self.save_file(self.offer_folder, file_name, data)
        return data

    def download_listing_page(self, category, page=1, save=False):
        """Implementacja metody dla klasy Olx

        :param category: kategoria z której ściągane są sane
        :param page: numer kolejny strony listingów
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądany listing
        """
        if page == 1:
            url = self.listing_url1.format(category)
        else:
            url = self.listing_url2.format(category, page)

        data = requests.get(url)
        data = data.text

        if save:
            file_name = 'listing_{}_{}.html'.format(category.replace('/', '_'), page)
            self.save_file(self.listing_folder, file_name, data)

        return data


class AutoScout24Downloader(PortalDownloader):
    """
    Implementacja dla portalu AutoScout24. Ta implementacja nieznacząco różni się od pozostałych implementacji:
    # .brak metody get_number_of_listings(html)
    #. własna implementacja download_listing_page o nazwie asc_download_listing_page
    """

    def __init__(self, logger):
        """
        Konstruktor inicjalizujący wartości domyślne dla klasy AutoScout24

        :param logger: obiekt współdzielonego loggera
        """
        super().__init__(logger=logger, offer_folder='offers/autoscout24')
        self.base_url = 'https://www.autoscout24.pl/'
        self.listing_url1 = self.base_url + 'lst/{}?fregfrom={}&fregto={}&page={}'
        self.offer_link_prefix = '/oferta/'

    def download_offer(self, offer_url, save=False):
        """Implementacja metody dla klasy AutoScout24

        :param offer_url: link do oferty
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądaną ofertę
        """
        data = requests.get(self.base_url + offer_url)
        data = data.text

        if save:
            soup = BeautifulSoup(data, 'html.parser')
            filtered = soup.find('input', attrs={"name": "classifiedGuid"})
            offer_id = filtered['value']
            file_name = 'offer_{}.html'.format(offer_id)
            self.save_file(self.offer_folder, file_name, data)
        return data

    def asc_download_listing_page(self, category, page, from_year, to_year, save=False):
        """Implementacja metody dla klasy AutoScout24

        :param category: kategoria z której ściągane są sane
        :param page: numer kolejny strony listingów
        :param from_year: rok początkowy dla zapytania
        :param to_year: rok końcowy dla zapytania
        :param save: flaga: czy zapisywać dane
        :return: string zawierający żądany listing
        """
        url = self.listing_url1.format(category, from_year, to_year, page)

        data = requests.get(url)
        data = data.text

        if save:
            file_name = 'listing_{}_{}.html'.format(category.replace('/', '_'), page)
            self.save_file(self.listing_folder, file_name, data)

        return data

    def download_number_of_links(self, category, number_of_offers=-1, from_year=2000, to_year=2001, save=False):
        """Metoda wydobywającą określoną liczbę linków dla wskazanej kategorii.

        :param category: kategoria ofert
        :param number_of_offers: liczba ofert
        :param from_year: rok początkowy dla zapytania
        :param to_year: rok końcowy dla zapytania
        :param save: flaga: czy zapisywać listingi
        :return: lista linków z wybranej kategorii. Liczba zwróconych linków <= żądana liczba linków
        """

        number_of_listings = 20
        temp_listing_number = 1
        all_links = list()

        while temp_listing_number <= number_of_listings:
            listing_page = self.asc_download_listing_page(category, temp_listing_number, from_year=from_year,
                                                          to_year=to_year, save=save)
            links_from_listing = self.get_links_from_listing(listing_page, self.offer_link_prefix)
            all_links.extend(links_from_listing)

            temp_listing_number += 1
            if number_of_offers == -1:
                continue
            else:
                if len(all_links) >= number_of_offers:
                    break

        if number_of_offers != -1:
            all_links = all_links[:number_of_offers]

        return all_links

