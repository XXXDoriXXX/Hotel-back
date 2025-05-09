# utils/images.py
from PIL import Image
from io import BytesIO
import uuid

MAX_WIDTH = 1920
MAX_HEIGHT = 1080
ALLOWED_IMAGE_TYPES = {"jpg", "jpeg", "png", "webp"}

def process_and_upload_image(file, s3_client, bucket, region, path_prefix: str) -> str:
    ext = file.filename.split(".")[-1].lower()
    if ext not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Invalid image format")

    contents = file.file.read()
    image = Image.open(BytesIO(contents)).convert("RGB")
    image.thumbnail((MAX_WIDTH, MAX_HEIGHT), Image.LANCZOS)

    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=85)
    buffer.seek(0)

    filename = f"{uuid.uuid4()}.jpg"
    s3_key = f"{path_prefix}/{filename}"

    s3_client.upload_fileobj(
        buffer,
        bucket,
        s3_key,
        ExtraArgs={"ContentType": "image/jpeg"}
    )

    return f"https://{bucket}.s3.{region}.amazonaws.com/{s3_key}"
