from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Boolean, JSON, DateTime, func
from sqlalchemy.orm import relationship
from database import Base
class HotelImage(Base):
    __tablename__ = "hotel_images"

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    image_url = Column(String, nullable=False)

    hotel = relationship("Hotel", back_populates="images")
class RoomImage(Base):
    __tablename__ = "room_images"

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey("rooms.id"), nullable=False)
    image_url = Column(String, nullable=False)

    room = relationship("Room", back_populates="images")
class Person(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String, nullable=False)
    last_name = Column(String, nullable=False)
    email = Column(String, nullable=True)
    phone = Column(String, nullable=False)
    password = Column(String, nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)
    birth_date = Column(Date, nullable=True)
    avatar_url = Column(String, nullable=True)
    ratings = relationship("Rating", back_populates="user", cascade="all, delete")
    owner = relationship('Owner', uselist=False, back_populates='person')
    client = relationship('Client', uselist=False, back_populates='person')
    employee = relationship('Employee', uselist=False, back_populates='person')
class Owner(Base):
    __tablename__ = 'owners'

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), unique=True, nullable=False)

    person = relationship('Person', back_populates='owner')
    hotels = relationship('Hotel', back_populates='owner', cascade='all, delete')
class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id'), unique=True, nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)
    position = Column(String, nullable=False)
    salary = Column(Float, nullable=False)
    work_experience = Column(Integer, nullable=False)
    is_vacation = Column(Boolean, default=False)

    person = relationship('Person', back_populates='employee')
    hotel = relationship('Hotel', back_populates='employees')
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
    rating = Column(Float, default=0)
    rating_count = Column(Integer, default=0)
    views = Column(Integer, default=0)
    amenities = Column(JSON, default=list)
    description = Column(String(500), nullable=True)

    ratings = relationship("Rating", back_populates="hotel", cascade="all, delete")
    owner = relationship('Owner', back_populates='hotels')
    rooms = relationship('Room', back_populates='hotel', cascade='all, delete')
    employees = relationship('Employee', back_populates='hotel', cascade='all, delete')
    images = relationship('HotelImage', back_populates='hotel', cascade='all, delete')

class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String, nullable=False)
    room_type = Column(String, nullable=False)
    places = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)
    description = Column(String(500), nullable=True)

    hotel = relationship('Hotel', back_populates='rooms')
    bookings = relationship('Booking', back_populates='room', cascade='all, delete')
    images = relationship('RoomImage', back_populates='room', cascade='all, delete')

class Booking(Base):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)
    total_price = Column(Float, nullable=False)

    payment_id = Column(Integer, ForeignKey("payments.id"), nullable=True)
    status = Column(String, default="active", nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime, nullable=True)
    client = relationship('Client', back_populates='bookings')
    room = relationship('Room', back_populates='bookings')
class Rating(Base):
    __tablename__ = "ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("people.id"), nullable=False)
    hotel_id = Column(Integer, ForeignKey("hotels.id"), nullable=False)
    rating = Column(Float, nullable=False)

    user = relationship("Person", back_populates="ratings")
    hotel = relationship("Hotel", back_populates="ratings")


class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    paid_at = Column(DateTime, nullable=True)