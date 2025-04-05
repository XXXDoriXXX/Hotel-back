import os
import uuid

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from crud.person_crud import verify_password, get_password_hash
from dependencies import get_current_user
from models import Person, Media, EntityType
from database import get_db
from routers.hotels import S3_BUCKET, s3_client, S3_REGION
from schemas import PersonBase, ChangeCredentialsRequest

router = APIRouter(prefix="/profile", tags=["profile"])


@router.put("/change_avatar")
async def change_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(Person).filter(Person.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    old_avatar = db.query(Media).filter(
        Media.entity_type == EntityType.AVATAR,
        Media.entity_id == user.id
    ).first()
    if old_avatar:
        try:
            s3_key = old_avatar.image_url.split(f"{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[-1]
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
            db.delete(old_avatar)
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error deleting old avatar: {str(e)}")

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Invalid file format")

    filename = f"{uuid.uuid4()}.{file_extension}"
    s3_key = f"avatars/{user.id}/{filename}"

    try:
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={'ContentType': file.content_type, 'ACL': 'public-read'}
        )
        image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

        new_avatar = Media(
            image_url=image_url,
            entity_type=EntityType.AVATAR,
            entity_id=user.id,
            person=user
        )
        db.add(new_avatar)
        db.commit()

        return {"message": "Avatar updated successfully", "image_url": image_url}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")


@router.get("/avatar")
def get_avatar(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    avatar = db.query(Media).filter(
        Media.entity_type == EntityType.AVATAR,
        Media.entity_id == current_user["id"]
    ).first()

    if not avatar:
        raise HTTPException(status_code=404, detail="Avatar not found")

    return {"image_url": avatar.image_url}

@router.put("/", response_model=PersonBase)
def update_profile(
    updated_data: dict,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.query(Person).filter(Person.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if "first_name" in updated_data:
        user.first_name = updated_data["first_name"]
    if "last_name" in updated_data:
        user.last_name = updated_data["last_name"]
    if "email" in updated_data:
        user.email = updated_data["email"]
    if "phone" in updated_data:
        user.phone = updated_data["phone"]
    if "birth_date" in updated_data:
        user.birth_date = updated_data["birth_date"]

    db.commit()
    db.refresh(user)
    return user
@router.put("/change_credentials")
def change_credentials(
    credentials: ChangeCredentialsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.query(Person).filter(Person.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(credentials.current_password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    if credentials.new_password:
        user.password = get_password_hash(credentials.new_password)

    if credentials.new_email:
        existing_user = db.query(Person).filter(Person.email == credentials.new_email).first()
        if existing_user:
            raise HTTPException(status_code=400, detail="This email is already in use")
        user.email = credentials.new_email

    db.commit()
    db.refresh(user)

    return {"message": "Credentials updated successfully"}


@router.get("/", response_model=PersonBase)
def get_profile(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    user = db.query(Person).filter(Person.id == current_user["id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user