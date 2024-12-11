from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base

class Person(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)  # Нове поле
    owner = relationship('Owner', uselist=False, back_populates='person')
    client = relationship('Client', uselist=False, back_populates='person')
class Owner(Base):
    __tablename__ = 'owners'

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), unique=True, nullable=False)

    person = relationship('Person', back_populates='owner')
    hotels = relationship('Hotel', back_populates='owner', cascade='all, delete')

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), unique=True, nullable=False)

    person = relationship('Person', back_populates='client')
    bookings = relationship('Booking', back_populates='client', cascade='all, delete')

class Hotel(Base):
    __tablename__ = 'hotels'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    address = Column(String, nullable=False)
    owner_id = Column(Integer, ForeignKey('owners.id'), nullable=False)

    owner = relationship('Owner', back_populates='hotels')
    rooms = relationship('Room', back_populates='hotel', cascade='all, delete')

class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, nullable=False)
    room_type = Column(String, nullable=False)
    places = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)

    hotel = relationship('Hotel', back_populates='rooms')
    bookings = relationship('Booking', back_populates='room', cascade='all, delete')

class Booking(Base):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)
    total_price = Column(Float, nullable=False)

    client = relationship('Client', back_populates='bookings')
    room = relationship('Room', back_populates='bookings')
