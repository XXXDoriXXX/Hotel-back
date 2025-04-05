from enum import Enum as PyEnum
from sqlalchemy import Enum as SQLAEnum
from sqlalchemy import Column, Integer, String, Date, Float, ForeignKey, Boolean, Text, DateTime, func
from sqlalchemy.orm import relationship
from database import Base

class AmenityType(str, PyEnum):
    WI_FI = "wi_fi"
    POOL = "pool"
    GYM = "gym"
    SPA = "spa"
    RESTAURANT = "restaurant"
    PARKING = "parking"
    AIR_CONDITIONING = "air_conditioning"
    BREAKFAST = "breakfast"
    PET_FRIENDLY = "pet_friendly"
    BUSINESS_CENTER = "business_center"

class EntityType(str, PyEnum):
    HOTEL = "hotel"
    ROOM = "room"
    ICON = "icon"
    AVATAR = "avatar"

class RoomType(str, PyEnum):
    STANDARD = "standard"
    DELUXE = "deluxe"
    SUITE = "suite"
    FAMILY = "family"
    PRESIDENTIAL = "presidential"

class BookingStatus(str, PyEnum):
    PENDING = "pending"
    CONFIRMED = "confirmed"
    CANCELLED = "cancelled"
    COMPLETED = "completed"

class PaymentStatus(str, PyEnum):
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    CASH = "cash"
    REFUNDED = "refunded"

class PaymentMethod(str, PyEnum):
    CARD = "card"
    CASH = "cash"

class Address(Base):
    __tablename__ = "addresses"

    id = Column(Integer, primary_key=True, index=True)
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class Person(Base):
    __tablename__ = 'people'

    id = Column(Integer, primary_key=True, index=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    password = Column(String(255), nullable=False)
    is_owner = Column(Boolean, default=False, nullable=False)
    birth_date = Column(Date)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    owner = relationship('Owner', uselist=False, back_populates='person')
    client = relationship('Client', uselist=False, back_populates='person')
    employee = relationship('Employee', uselist=False, back_populates='person')
    ratings = relationship("Rating", back_populates="user", cascade="all, delete")
    media = relationship("Media", back_populates="person", cascade="all, delete")

class Owner(Base):
    __tablename__ = 'owners'

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id', ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    person = relationship('Person', back_populates='owner')
    hotels = relationship('Hotel', back_populates='owner', cascade='all, delete')

class Client(Base):
    __tablename__ = 'clients'

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id', ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    person = relationship('Person', back_populates='client')
    bookings = relationship('Booking', back_populates='client', cascade='all, delete')

class Employee(Base):
    __tablename__ = 'employees'

    id = Column(Integer, primary_key=True, index=True)
    person_id = Column(Integer, ForeignKey('people.id', ondelete="CASCADE", onupdate="CASCADE"), unique=True, nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    position = Column(String(100), nullable=False)
    salary = Column(Float, nullable=False)
    work_experience = Column(Integer, nullable=False)
    is_vacation = Column(Boolean, default=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    person = relationship('Person', back_populates='employee')
    hotel = relationship('Hotel', back_populates='employees')

class Hotel(Base):
    __tablename__ = 'hotels'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('owners.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    views = Column(Integer, default=0)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    address = relationship('Address')
    owner = relationship('Owner', back_populates='hotels')
    rooms = relationship('Room', back_populates='hotel', cascade='all, delete')
    employees = relationship('Employee', back_populates='hotel', cascade='all, delete')
    amenities = relationship('HotelAmenity', back_populates='hotel', cascade='all, delete')
    media = relationship('Media', back_populates='hotel', cascade='all, delete')
    ratings = relationship('Rating', back_populates='hotel', cascade='all, delete')

class Amenity(Base):
    __tablename__ = 'amenities'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    icon_url = Column(String(255), nullable=False)

class HotelAmenity(Base):
    __tablename__ = 'hotel_amenities'

    id = Column(Integer, primary_key=True, index=True)
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    amenity_id = Column(Integer, ForeignKey('amenities.id'), nullable=False)

    hotel = relationship('Hotel', back_populates='amenities')
    amenity = relationship('Amenity')
    room_amenities = relationship('RoomAmenity', back_populates='hotel_amenity', cascade='all, delete')

class RoomAmenity(Base):
    __tablename__ = 'room_amenities'

    id = Column(Integer, primary_key=True, index=True)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    hotel_amenities_id = Column(Integer, ForeignKey('hotel_amenities.id'), nullable=False)
    is_paid = Column(Boolean, default=False)
    quantity = Column(Integer, default=0)
    price = Column(Float)

    room = relationship('Room', back_populates='amenities')
    hotel_amenity = relationship('HotelAmenity', back_populates='room_amenities')

class Media(Base):
    __tablename__ = 'media'

    id = Column(Integer, primary_key=True, index=True)
    image_url = Column(String, nullable=False)
    entity_type = Column(SQLAEnum(EntityType), nullable=False)
    entity_id = Column(Integer, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    hotel = relationship('Hotel', back_populates='media')
    room = relationship('Room', back_populates='media')
    person = relationship('Person', back_populates='media')

class Room(Base):
    __tablename__ = 'rooms'

    id = Column(Integer, primary_key=True, index=True)
    room_number = Column(String(10), unique=True, nullable=False)
    room_type = Column(SQLAEnum(RoomType), nullable=False)
    places = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    hotel = relationship('Hotel', back_populates='rooms')
    bookings = relationship('Booking', back_populates='room', cascade='all, delete')
    media = relationship('Media', back_populates='room', cascade='all, delete')
    amenities = relationship('RoomAmenity', back_populates='room', cascade='all, delete')

class Booking(Base):
    __tablename__ = 'bookings'

    id = Column(Integer, primary_key=True, index=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    date_start = Column(Date, nullable=False)
    date_end = Column(Date, nullable=False)
    guests_count = Column(Integer, default=1, nullable=False)
    total_price = Column(Float, nullable=False)
    status = Column(SQLAEnum(BookingStatus), default=BookingStatus.PENDING, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    client = relationship('Client', back_populates='bookings')
    room = relationship('Room', back_populates='bookings')
    payment = relationship('Payment', back_populates='booking', uselist=False, cascade='all, delete')

class Payment(Base):
    __tablename__ = 'payments'

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    currency = Column(String(3), default="USD", nullable=False)
    status = Column(SQLAEnum(PaymentStatus), default=PaymentStatus.PENDING, nullable=False)
    method = Column(SQLAEnum(PaymentMethod), nullable=False)
    stripe_payment_id = Column(String)
    description = Column(Text)
    refund_amount = Column(Float)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime)

    booking = relationship('Booking', back_populates='payment')
    errors = relationship('PaymentError', back_populates='payment', cascade='all, delete')

class PaymentError(Base):
    __tablename__ = 'payment_errors'

    id = Column(Integer, primary_key=True, index=True)
    payment_id = Column(Integer, ForeignKey('payments.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    error_code = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    occurred_at = Column(DateTime, server_default=func.now())

    payment = relationship('Payment', back_populates='errors')

class Rating(Base):
    __tablename__ = 'ratings'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('people.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete="CASCADE", onupdate="CASCADE"), nullable=False)
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

    user = relationship('Person', back_populates='ratings')
    hotel = relationship('Hotel', back_populates='ratings')