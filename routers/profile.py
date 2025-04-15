import os
import uuid

import boto3
from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from crud.person_crud import verify_password, get_password_hash
from dependencies import get_current_user
from models import Client, Owner
from database import get_db
from schemas import ProfileUpdateRequest, ChangeCredentialsRequest
from schemas.profile import PersonBase, OwnerUpdateRequest, UpdateOwnerResponse
from utils import create_access_token

router = APIRouter(prefix="/profile", tags=["profile"])
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


# ---------------- CHANGE AVATAR IMAGE ----------------
@router.put("/change_avatar", response_model=dict)
async def change_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.query(Client).filter(Client.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if user.avatar_url:
        try:
            s3_key = user.avatar_url.split(f"{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/")[-1]
            s3_client.delete_object(Bucket=S3_BUCKET, Key=s3_key)
        except ClientError as e:
            raise HTTPException(status_code=500, detail=f"Error deleting old avatar: {str(e)}")

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Invalid file format. Only jpg, jpeg, png are allowed.")

    filename = f"{uuid.uuid4()}.{file_extension}"
    s3_key = f"avatars/{user.id}/{filename}"

    try:
        s3_client.upload_fileobj(
            file.file,
            S3_BUCKET,
            s3_key,
            ExtraArgs={'ContentType': file.content_type}
        )
        image_url = f"https://{S3_BUCKET}.s3.{S3_REGION}.amazonaws.com/{s3_key}"

        user.avatar_url = image_url
        db.commit()
        db.refresh(user)

        return {"image_url": image_url}
    except ClientError as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

    # ---------------- UPDATE OWNER ----------------
@router.put("/update/owner", response_model=UpdateOwnerResponse)
def update_owner(
    owner_data: OwnerUpdateRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    owner = db.query(Owner).filter(Owner.id == current_user["id"]).first()
    if not owner:
        raise HTTPException(status_code=404, detail="Owner not found")

    if not verify_password(owner_data.current_password, owner.password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    if owner_data.first_name:
        owner.first_name = owner_data.first_name
    if owner_data.last_name:
        owner.last_name = owner_data.last_name
    if owner_data.email:
        owner.email = owner_data.email
    if owner_data.phone:
        owner.phone = owner_data.phone
    if owner_data.new_password:
        owner.password = get_password_hash(owner_data.new_password)

    db.commit()
    db.refresh(owner)

    token_data = {
        "id": owner.id,
        "first_name": owner.first_name,
        "last_name": owner.last_name,
        "email": owner.email,
        "phone": owner.phone,
        "is_owner": True,
        "owner_id": owner.id
    }
    new_token = create_access_token(token_data)

    return {"owner": owner, "new_token": new_token}
    # ---------------- UPDATE CLIENT ----------------
@router.put("/update/client", response_model=PersonBase)
def update_credentials(
    credentials: ChangeCredentialsRequest,
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user)
):
    user = db.query(Client).filter(Client.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(credentials.current_password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect current password")

    if credentials.first_name:
        user.first_name = credentials.first_name
    if credentials.last_name:
        user.last_name = credentials.last_name
    if credentials.phone:
        user.phone = credentials.phone
    if credentials.birth_date:
        user.birth_date = credentials.birth_date

    if credentials.new_email:
        user.email = credentials.new_email

    if credentials.new_password:
        if credentials.new_password != credentials.confirm_password:
            raise HTTPException(status_code=400, detail="Passwords do not match")
        user.password = get_password_hash(credentials.new_password)

    db.commit()
    db.refresh(user)
    return user

    # ---------------- GET PROFILE ----------------
@router.get("/", response_model=PersonBase)
def get_profile(
        db: Session = Depends(get_db),
        current_user: dict = Depends(get_current_user)
):
    user = db.query(Client).filter(Client.id == current_user["id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user