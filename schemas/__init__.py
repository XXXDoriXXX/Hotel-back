from .auth import ClientCreate, OwnerCreate
from .hotel import HotelImgBase, HotelBase, HotelCreate, HotelWithAll, HotelWithAmenities, HotelWithImagesAndAddress, AddressCreate
from .room import RoomBase, RoomImgBase, RoomWithAmenities, RoomCreate, RoomDetails, RoomType
from .profile import ProfileUpdateRequest, ChangeCredentialsRequest, AvatarRequest