# bulk_amenities_post.py

import requests

API_URL = "https://hotel-back-production-558e.up.railway.app/amenities/"
AMENITIES = [
  { "name": "Private Bathroom", "description": "Room includes a private bathroom", "is_hotel": False },
  { "name": "Desk", "description": "Work desk available in the room", "is_hotel": False },
  { "name": "Hairdryer", "description": "Hairdryer provided", "is_hotel": False},
  { "name": "Electric Kettle", "description": "In-room electric kettle for tea or coffee", "is_hotel": False},
  { "name": "Iron and Ironing Board", "description": "Available upon request", "is_hotel": False },
  { "name": "Soundproofing", "description": "Rooms with sound insulation", "is_hotel": False },
  { "name": "Safe", "description": "In-room safe for valuables", "is_hotel": False },
  { "name": "Balcony", "description": "Room with private balcony", "is_hotel": False },
  { "name": "Towels and Linens", "description": "Fresh towels and bed linen included", "is_hotel": False },
  { "name": "Clothes Rack", "description": "Space to hang clothes", "is_hotel": False }
]



for amenity in AMENITIES:
    res = requests.post(API_URL, json=amenity)
    if res.status_code == 201:
        print(f"Added: {amenity['name']}")
    elif res.status_code == 409:
        print(f"Already exists: {amenity['name']}")
    else:
        print(f"Failed: {amenity['name']} - {res.status_code} - {res.text}")
