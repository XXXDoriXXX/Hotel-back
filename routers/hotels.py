import os
import uuid
from typing import List, Optional
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from pydantic import BaseModel
from sqlalchemy.orm import Session, joinedload
from starlette import status
from database import get_db
from dependencies import get_current_user, get_current_owner
from models import Hotel, Owner, Media, EntityType
import crud.hotel_crud
from schemas import HotelCreate, HotelWithDetails, MediaBase
from schemas.hotel import HotelAmenitiesUpdate

router = APIRouter(
    prefix="/hotels",
    tags=["hotels"]
)
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

UPLOAD_DIRECTORY = "uploaded_images/hotels"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_hotel(
        hotel_data: HotelCreate,
        db: Session = Depends(get_db),
        current_owner: dict = Depends(get_current_owner)
):

    hotel_dict = hotel_data.dict()
    hotel_dict["owner_id"] = current_owner.id

    db_hotel = crud.hotel_crud.create_hotel(db, hotel_dict)

    if not db_hotel:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Hotel creation failed"
        )

    return db_hotel
@router.get("/search", response_model=List[HotelWithDetails])
def search_hotels(
    name: Optional[str] = None,
    address: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Hotel).options(
        joinedload(Hotel.rooms),
        joinedload(Hotel.employees)
    )

    if name:
        query = query.filter(Hotel.name.ilike(f"%{name}%"))
    if address:
        query = query.filter(Hotel.address.ilike(f"%{address}%"))

    hotels = query.all()
    if not hotels:
        raise HTTPException(status_code=404, detail="No hotels found")
    return hotels
@router.get("/{hotel_id}", response_model=HotelWithDetails)
def get_hotel_by_id(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).options(
        joinedload(Hotel.rooms),
        joinedload(Hotel.media),
        joinedload(Hotel.employees)
    ).filter(Hotel.id == hotel_id).first()

    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    return hotel

@router.delete("/{hotel_id}")
def delete_hotel(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Hotel not found"
        )

    if hotel.owner_id != current_owner.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not the owner of this hotel"
        )

    try:
        deleted = crud.hotel_crud.delete_hotel(db, hotel_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Failed to delete hotel"
            )
        return {"message": "Hotel deleted successfully"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.post("/{hotel_id}/images/upload/", status_code=201)
async def upload_hotel_image(
        hotel_id: int,
        file: UploadFile = File(...),
        db: Session = Depends(get_db),
        current_owner: Owner = Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(status_code=404, detail="Hotel not found or access denied")

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png", "webp"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only jpg, jpeg, png and webp are allowed."
        )

    filename = f"{uuid.uuid4()}.{file_extension}"
    s3_key = f"hotels/{hotel_id}/{filename}"

    try:
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={
                'ContentType': file.content_type,
                'ACL': 'public-read'
            }
        )

        image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

        hotel_image = crud.hotel_crud.create_hotel_media(
            db,
            hotel_id=hotel_id,
            image_url=image_url
        )

        return {
            "id": hotel_image.id,
            "image_url": image_url,
            "message": "Image uploaded successfully"
        }
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error uploading file to S3: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error saving image record: {str(e)}"
        )


@router.delete("/images/{image_id}")
def delete_hotel_image(
        image_id: int,
        db: Session = Depends(get_db),
        current_owner: Owner = Depends(get_current_owner)
):
    image = db.query(Media).filter(Media.id == image_id).first()
    if not image:
        raise HTTPException(status_code=404, detail="Image not found")

    hotel = db.query(Hotel).filter(Hotel.id == image.entity_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(status_code=403, detail="Not authorized")

    try:
        s3_key = image.image_url.split(f"{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[-1]
        s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)

        db.delete(image)
        db.commit()

        return {"message": "Image deleted successfully"}
    except ClientError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error deleting file from S3: {str(e)}"
        )

@router.get("/{hotel_id}/images", response_model=List[MediaBase])
def get_hotel_images(
    hotel_id: int,
    db: Session = Depends(get_db)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    images = db.query(Media).filter(
        Media.entity_type == EntityType.HOTEL,
        Media.entity_id == hotel_id
    ).all()

    return images
@router.put("/{hotel_id}/amenities")
def update_amenities(
    hotel_id: int,
    data: HotelAmenitiesUpdate,
    db: Session = Depends(get_db),
    current_owner: Owner = Depends(get_current_owner)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel or hotel.owner_id != current_owner.id:
        raise HTTPException(status_code=404, detail="Hotel not found or access denied")

    hotel.amenities = list(set(data.amenities))
    db.commit()
    db.refresh(hotel)

    return {
        "message": "Amenities updated successfully",
        "amenities": hotel.amenities
    }

@router.post("/{hotel_id}/view")
def increment_views(
    hotel_id: int,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("is_owner"):
        raise HTTPException(status_code=403, detail="Only clients can add views")

    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")

    hotel.views += 1
    db.commit()
    db.refresh(hotel)

    return {
        "message": f"Views updated successfully. Total views: {hotel.views}",
        "views": hotel.views
    }

class RatingRequest(BaseModel):
      rating: float

class DescriptionUpdate(BaseModel):
    description: str
@router.put("/{hotel_id}/description")
def update_hotel_description(
    hotel_id: int,
    body: DescriptionUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    hotel = db.query(Hotel).filter(Hotel.id == hotel_id).first()
    if not hotel:
        raise HTTPException(status_code=404, detail="Hotel not found")
    if hotel.owner_id != current_user.get("id"):
        raise HTTPException(status_code=403, detail="Not authorized to modify this hotel")

    if len(body.description) > 500:
        raise HTTPException(status_code=400, detail="Description must not exceed 500 characters")

    hotel.description = body.description
    db.commit()
    db.refresh(hotel)
    return {"message": "Hotel description updated successfully"}
