from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session, joinedload
from typing import List
import os, uuid, boto3
from database import get_db
from dependencies import get_current_owner
from models import Hotel, HotelImg,  Address
from schemas.hotel import HotelCreate, HotelBase, HotelImgBase, HotelWithImages,
router = APIRouter(prefix="/hotels", tags=["hotels"])

S3_BUCKET = os.getenv('S3_BUCKET')
S3_REGION = os.getenv('S3_REGION')
AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')

s3_client = boto3.client(
    's3',
    region_name=S3_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)

# ---------------- CREATE HOTEL ----------------
@router.post("/", response_model=HotelBase, status_code=201)
def create_hotel(
    hotel_data: HotelCreate,
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    addr_data = hotel_data.address.dict()
    address = Address(**addr_data)
    db.add(address)
    db.commit()
    db.refresh(address)

    hotel = Hotel(
        name=hotel_data.name,
        description=hotel_data.description,
        owner_id=current_owner.id,
        address_id=address.id
    )
    db.add(hotel)
    db.commit()
    db.refresh(hotel)
    return hotel
# ---------------- GET HOTEL BY ID ----------------
@router.get("/{hotel_id}", response_model=HotelWithImages)
def get_hotel(hotel_id: int, db: Session = Depends(get_db)):
    hotel = db.query(Hotel).options(joinedload(Hotel.images)).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(404, "Hotel not found")
    return hotel

# ---------------- GET ALL HOTELS ----------------
@router.get("/", response_model=List[HotelBase])
def get_all_hotels(db: Session = Depends(get_db)):
    return db.query(Hotel).all()

# ---------------- DELETE HOTEL ----------------
@router.delete("/{hotel_id}")
def delete_hotel(hotel_id: int, db: Session = Depends(get_db), current_owner = Depends(get_current_owner)):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(404, "Hotel not found")
    if hotel.owner_id != current_owner.id:
        raise HTTPException(403, "You are not the owner of this hotel")
    db.delete(hotel)
    db.commit()
    return {"message": "Hotel deleted"}

# ---------------- UPLOAD HOTEL IMAGE ----------------
@router.post("/{hotel_id}/images", response_model=HotelImgBase)
async def upload_image(
    hotel_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_owner = Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(404, "Hotel not found or no access")

    ext = file.filename.split(".")[-1].lower()
    if ext not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(400, "Invalid image format")

    filename = f"{uuid.uuid4()}.{ext}"
    s3_key = f"hotels/{hotel_id}/{filename}"
    try:
        s3_client.upload_fileobj(
            file.file, S3_BUCKET, s3_key,
            ExtraArgs={
                "ContentType": file.content_type
            }
        )
        url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"
        image = HotelImg(hotel_id=hotel_id, image_url=url)
        db.add(image)
        db.commit()
        db.refresh(image)
        return image
    except Exception as e:
        raise HTTPException(500, f"Upload failed: {str(e)}")

# ---------------- GET HOTEL IMAGES ----------------
@router.get("/{hotel_id}/images", response_model=List[HotelImgBase])
def get_images(hotel_id: int, db: Session = Depends(get_db)):
    return db.query(HotelImg).filter(HotelImg.hotel_id == hotel_id).all()

# ---------------- DELETE HOTEL IMAGE ----------------
@router.delete("/images/{image_id}")
def delete_image(image_id: int, db: Session = Depends(get_db), current_owner = Depends(get_current_owner)):
    image = db.query(HotelImg).filter(HotelImg.id == image_id).first()
    if not image:
        raise HTTPException(404, "Image not found")
    hotel = db.query(Hotel).filter(Hotel.id == image.hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(403, "Not authorized")

    s3_key = image.image_url.split(f"{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[-1]
    s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

    db.delete(image)
    db.commit()
    return {"message": "Image deleted"}
