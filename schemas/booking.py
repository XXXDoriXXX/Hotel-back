from pydantic import BaseModel
from datetime import datetime

class BookingCheckoutRequest(BaseModel):
    room_id: int
    date_start: datetime
    date_end: datetime
