from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, DECIMAL
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Kampanie(Base):
    """
    Model reprezentujący kampanie
    """
    __tablename__ = 'kampanie'

    idx = Column(Integer, primary_key=True)
    data = Column(DateTime)
    id_portalu = Column(Integer, ForeignKey('portale.idx'))
    rodzaj_api = Column(String(50))

    portal = relationship('Portale', back_populates='kampania')
    oferta = relationship('Oferty', back_populates='kampania')

    def __repr__(self):
        return f'<Kampanie(idx={self.idx}, api={self.rodzaj_api})>'


class Portale(Base):
    """
    Model reprezentujący portale
    """
    __tablename__ = 'portale'

    idx = Column(Integer, primary_key=True)
    nazwa_portalu = Column(String(20))

    kampania = relationship('Kampanie', back_populates='portal')

    def __repr__(self):
        return f'<Portal(idx={self.idx}, nazwa_portalu={self.nazwa_portalu})>'


class Oferty(Base):
    """
    Model reprezentujący oferty
    """

    __tablename__ = 'oferty'

    idx = Column(Integer, primary_key=True)
    id_kampanii = Column(Integer, ForeignKey('kampanie.idx'))
    id_oferty = Column(String(40), nullable=False)
    id_sprzedajacego = Column(String(50), nullable=False)
    lokalizacja = Column(String(70))
    tytul = Column(String(70))
    cena = Column(DECIMAL(14, 2), default="0")
    marka = Column(String(120), nullable=False)
    model = Column(String(120), nullable=False)
    typ = Column(String(120), nullable=False)
    rok_produkcji = Column(Integer, nullable=False)
    przebieg = Column(Integer, default=0)
    pojemnosc = Column(Integer)
    moc = Column(Integer)
    rodzaj_paliwa = Column(String(20))
    kolor = Column(String(40))
    uszkodzony = Column(String(1))
    kraj = Column(String(20))
    naped = Column(String(20))
    liczba_miejsc = Column(Integer)
    miejscowosc = Column(String(100))
    wojewodztwo = Column(String(100))
    nadwozie = Column(String(40))
    anomalie = Column(String(40), default='')

    kampania = relationship('Kampanie', back_populates='oferta')

    def __repr__(self):
        return f'<Oferty(idx={self.idx}, id_oferty={self.id_oferty})>'
