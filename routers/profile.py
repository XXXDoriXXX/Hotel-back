import os
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from crud.person_crud import verify_password, get_password_hash
from dependencies import get_current_user
from models import Person
from database import get_db
from schemas import PersonBase, ChangeCredentialsRequest

router = APIRouter(prefix="/profile", tags=["profile"])
UPLOAD_DIRECTORY = "uploaded_images/avatars"
os.makedirs(UPLOAD_DIRECTORY, exist_ok=True)

@router.put("/change_avatar")
async def change_avatar(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: dict = Depends(get_current_user),
):
    user = db.query(Person).filter(Person.id == current_user["id"]).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    file_extension = file.filename.split(".")[-1].lower()
    if file_extension not in ["jpg", "jpeg", "png"]:
        raise HTTPException(status_code=400, detail="Invalid file format. Only jpg, jpeg, and png are allowed.")

    if user.avatar_url:
        old_file_path = user.avatar_url.lstrip("/")
        if os.path.exists(old_file_path):
            os.remove(old_file_path)

    filename = f"{user.id}.{file_extension}"
    file_path = os.path.join(UPLOAD_DIRECTORY, filename)

    try:
        with open(file_path, "wb") as f:
            f.write(await file.read())
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error saving file: {str(e)}")

    user.avatar_url = f"/{UPLOAD_DIRECTORY}/{filename}"
    db.commit()
    db.refresh(user)

    return {"message": "Avatar updated successfully", "avatar_url": user.avatar_url}


@router.get("/avatar")
def get_avatar(db: Session = Depends(get_db), current_user: dict = Depends(get_current_user)):
    print("CURRENT USER:", current_user)

    user = db.query(Person).filter(Person.id == current_user["id"]).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not user.avatar_url:
        raise HTTPException(status_code=404, detail="Avatar not found")

    return {"avatar_url": user.avatar_url}


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