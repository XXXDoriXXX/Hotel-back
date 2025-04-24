import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Boolean, Text, DateTime, func, Enum
from sqlalchemy.orm import relationship
from database import Base

class RoomType(enum.Enum):
    standard = "standard"
    deluxe = "deluxe"
    suite = "suite"
    family = "family"
    presidential = "presidential"

class BookingStatus(enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"

class PaymentStatus(enum.Enum):
    pending = "pending"
    paid = "paid"
    failed = "failed"
    cash = "cash"
    refunded = "refunded"

class EntityType(enum.Enum):
    hotel = "hotel"
    room = "room"
    icon = "icon"
    avatar = "avatar"

# Models
class Address(Base):
    __tablename__ = 'addresses'
    id = Column(Integer, primary_key=True, autoincrement=True)
    street = Column(String(255), nullable=False)
    city = Column(String(100), nullable=False)
    state = Column(String(100))
    country = Column(String(100), nullable=False)
    postal_code = Column(String(20), nullable=False)
    latitude = Column(Float)
    longitude = Column(Float)

class Owner(Base):
    __tablename__ = 'owner'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), nullable=False)
    stripe_account_id = Column(String(255), nullable=True)
    password = Column(String(255), nullable=False)
    hotels = relationship("Hotel", back_populates="owner")

class Client(Base):
    __tablename__ = 'clients'
    id = Column(Integer, primary_key=True, autoincrement=True)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    phone = Column(String(20), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    birth_date = Column(DateTime, nullable=False)
    avatar_url = Column(String(250))
    created_at = Column(DateTime, server_default=func.now())
    bookings = relationship("Booking", back_populates="client")
    ratings = relationship("Rating", back_populates="client")

class Employee(Base):
    __tablename__ = 'employees'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False)
    first_name = Column(String(50), nullable=False)
    last_name = Column(String(50), nullable=False)
    position = Column(String(100), nullable=False)
    salary = Column(Float, nullable=False)
    hotel = relationship("Hotel", back_populates="employees")

class Hotel(Base):
    __tablename__ = 'hotels'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), nullable=False)
    address_id = Column(Integer, ForeignKey('addresses.id'), nullable=False)
    owner_id = Column(Integer, ForeignKey('owner.id'), nullable=False)
    description = Column(Text)
    address = relationship("Address")
    owner = relationship("Owner", back_populates="hotels")
    employees = relationship("Employee", back_populates="hotel")
    rooms = relationship("Room", back_populates="hotel")
    images = relationship("HotelImg", back_populates="hotel")
    amenities = relationship("AmenityHotel", back_populates="hotel")
    ratings = relationship("Rating", back_populates="hotel")

class Amenity(Base):
    __tablename__ = 'amenities'
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)
    description = Column(String(255))
    is_hotel = Column(Boolean, nullable=False)
    hotel_amenities = relationship("AmenityHotel", back_populates="amenity")
    room_amenities = relationship("AmenityRoom", back_populates="amenity")

class AmenityHotel(Base):
    __tablename__ = 'amenities_hotel'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False)
    amenity_id = Column(Integer, ForeignKey('amenities.id', ondelete='CASCADE'), nullable=False)
    hotel = relationship("Hotel", back_populates="amenities")
    amenity = relationship("Amenity", back_populates="hotel_amenities")

class AmenityRoom(Base):
    __tablename__ = 'amenities_room'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False)
    amenity_id = Column(Integer, ForeignKey('amenities.id', ondelete='CASCADE'), nullable=False)
    room = relationship("Room", back_populates="amenities")
    amenity = relationship("Amenity", back_populates="room_amenities")

class HotelImg(Base):
    __tablename__ = 'hotel_img'
    id = Column(Integer, primary_key=True, autoincrement=True)
    hotel_id = Column(Integer, ForeignKey('hotels.id'), nullable=False)
    image_url = Column(String(255), nullable=False)
    hotel = relationship("Hotel", back_populates="images")

class RoomImg(Base):
    __tablename__ = 'room_img'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_id = Column(Integer, ForeignKey('rooms.id'), nullable=False)
    image_url = Column(String(255), nullable=False)
    room = relationship("Room", back_populates="images")

class Room(Base):
    __tablename__ = 'rooms'
    id = Column(Integer, primary_key=True, autoincrement=True)
    room_number = Column(String(10), unique=False, nullable=False)
    room_type = Column(Enum(RoomType), nullable=False)
    places = Column(Integer, nullable=False)
    price_per_night = Column(Float, nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False)
    description = Column(Text)
    hotel = relationship("Hotel", back_populates="rooms")
    images = relationship("RoomImg", back_populates="room")
    amenities = relationship("AmenityRoom", back_populates="room")
    bookings = relationship("Booking", back_populates="room")

class Booking(Base):
    __tablename__ = 'bookings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    client_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    room_id = Column(Integer, ForeignKey('rooms.id', ondelete='CASCADE'), nullable=False)
    date_start = Column(DateTime, nullable=False)
    date_end = Column(DateTime, nullable=False)
    status = Column(Enum(BookingStatus), default='pending', nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    client = relationship("Client", back_populates="bookings")
    room = relationship("Room", back_populates="bookings")
    payments = relationship("Payment", back_populates="booking")

class Payment(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    amount = Column(Float, nullable=False)
    booking_id = Column(Integer, ForeignKey('bookings.id', ondelete='CASCADE'), nullable=False)
    currency = Column(String(3), default='USD', nullable=False)
    status = Column(Enum(PaymentStatus), default='pending', nullable=False)
    is_card = Column(Boolean, default=True)
    stripe_payment_id = Column(String(255))
    description = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    paid_at = Column(DateTime)
    booking = relationship("Booking", back_populates="payments")
    errors = relationship("PaymentError", back_populates="payment")

class PaymentError(Base):
    __tablename__ = 'payment_errors'
    id = Column(Integer, primary_key=True, autoincrement=True)
    payment_id = Column(Integer, ForeignKey('payments.id', ondelete='CASCADE'), nullable=False)
    error_code = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=False)
    occurred_at = Column(DateTime, server_default=func.now())
    payment = relationship("Payment", back_populates="errors")

class Rating(Base):
    __tablename__ = 'ratings'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('clients.id', ondelete='CASCADE'), nullable=False)
    hotel_id = Column(Integer, ForeignKey('hotels.id', ondelete='CASCADE'), nullable=False)
    views = Column(Integer, default=0)
    rating = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    client = relationship("Client", back_populates="ratings")
    hotel = relationship("Hotel", back_populates="ratings")