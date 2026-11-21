from io import BytesIO
import os
from pathlib import Path
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi import File, Response, UploadFile
from PIL import Image, ImageOps, UnidentifiedImageError
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Role, FarmerProfile
from app.schemas import UserCreate, Login, Token, UserOut, ProfileUpdate, PasswordChange
from app.auth import hash_password, verify_password, create_access_token, get_current_user, require_role

router = APIRouter(prefix="/auth", tags=["auth"])
PROFILE_IMAGE_DIRECTORY = Path(__file__).resolve().parents[2] / "private_uploads" / "profile_pictures"
MAX_PROFILE_IMAGE_BYTES = 5 * 1024 * 1024
MAX_PROFILE_IMAGE_PIXELS = 40_000_000
PROFILE_IMAGE_FORMATS = {
    "image/jpeg": "JPEG",
    "image/png": "PNG",
    "image/webp": "WEBP",
}


def _stored_profile_image(image_name: str | None) -> Path | None:
    if not image_name:
        return None
    directory = PROFILE_IMAGE_DIRECTORY.resolve()
    image_path = (directory / image_name).resolve()
    if image_path.parent != directory or image_path.suffix != ".webp":
        return None
    return image_path


def _save_profile_image(content: bytes, image_format: str) -> bytes:
    try:
        with Image.open(BytesIO(content)) as image:
            if image.format != image_format:
                raise HTTPException(status_code=415, detail="The uploaded file is not a valid supported image")
            if image.width > 8000 or image.height > 8000 or image.width * image.height > MAX_PROFILE_IMAGE_PIXELS:
                raise HTTPException(status_code=413, detail="Image dimensions are too large")
            image.verify()
        with Image.open(BytesIO(content)) as image:
            image = ImageOps.exif_transpose(image)
            image.thumbnail((512, 512), Image.Resampling.LANCZOS)
            has_alpha = "A" in image.getbands() or "transparency" in image.info
            converted = image.convert("RGBA" if has_alpha else "RGB")
            output = BytesIO()
            converted.save(output, format="WEBP", quality=85, method=6)
            return output.getvalue()
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid supported image") from exc


def _remove_stored_profile_image(image_name: str | None) -> None:
    old_image = _stored_profile_image(image_name)
    if old_image and old_image.is_file():
        old_image.unlink()


@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
def register(payload: UserCreate, db: Session = Depends(get_db)):
    if payload.role not in {Role.CUSTOMER, Role.FARMER}:
        raise HTTPException(status_code=403, detail="Administrator accounts cannot be self-registered")
    if db.query(User).filter(User.email == str(payload.email).lower()).first():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        name=payload.name,
        email=str(payload.email).lower(),
        password_hash=hash_password(payload.password),
        role=payload.role,
        phone=payload.phone,
        terms_accepted=payload.terms_accepted,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    if user.role == Role.FARMER:
        db.add(FarmerProfile(
            user_id=user.id,
            farm_name=payload.farm_name or user.name,
            village=payload.village or "",
            description=payload.farm_description or "",
            phone=payload.phone,
            main_products=payload.main_products or "",
        ))
        db.commit()
    return Token(access_token=create_access_token(user), user=UserOut.model_validate(user))


@router.post("/login", response_model=Token)
def login(payload: Login, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == str(payload.email).lower()).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Incorrect email or password")
    return Token(
        access_token=create_access_token(user, remember_me=payload.remember_me),
        user=UserOut.model_validate(user),
    )


@router.get("/me", response_model=UserOut)
def me(user: User = Depends(get_current_user)):
    return user


@router.get("/profile")
def profile(user: User = Depends(get_current_user)):
    farmer = user.farmer_profile
    return {
        "id": user.id,
        "name": user.name,
        "email": user.email,
        "role": user.role.value,
        "has_profile_picture": bool(user.profile_image_name),
        "phone": user.phone,
        "farm_name": farmer.farm_name if farmer else None,
        "village": farmer.village if farmer else None,
        "farm_description": farmer.description if farmer else None,
        "main_products": farmer.main_products if farmer else None,
    }


@router.get("/profile-picture")
def get_profile_picture(user: User = Depends(get_current_user)):
    image_path = _stored_profile_image(user.profile_image_name)
    if image_path is None or not image_path.is_file():
        raise HTTPException(status_code=404, detail="Profile picture not found")
    return Response(
        content=image_path.read_bytes(),
        media_type="image/webp",
        headers={
            "Cache-Control": "private, no-store",
            "X-Content-Type-Options": "nosniff",
        },
    )


@router.post("/profile-picture")
async def upload_profile_picture(
    image: UploadFile = File(...),
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    image_format = PROFILE_IMAGE_FORMATS.get(image.content_type or "")
    if image_format is None:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image")
    content = await image.read(MAX_PROFILE_IMAGE_BYTES + 1)
    if len(content) > MAX_PROFILE_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller")
    optimized_image = _save_profile_image(content, image_format)

    PROFILE_IMAGE_DIRECTORY.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    PROFILE_IMAGE_DIRECTORY.mkdir(mode=0o700, exist_ok=True)
    os.chmod(PROFILE_IMAGE_DIRECTORY.parent, 0o700)
    os.chmod(PROFILE_IMAGE_DIRECTORY, 0o700)
    image_name = f"{secrets.token_hex(16)}.webp"
    image_path = PROFILE_IMAGE_DIRECTORY / image_name
    descriptor = os.open(image_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(descriptor, "wb") as stored_image:
        stored_image.write(optimized_image)

    old_image_name = user.profile_image_name
    user.profile_image_name = image_name
    try:
        db.commit()
    except SQLAlchemyError:
        db.rollback()
        image_path.unlink(missing_ok=True)
        raise
    _remove_stored_profile_image(old_image_name)
    return {"has_profile_picture": True}


@router.delete("/profile-picture", status_code=status.HTTP_204_NO_CONTENT)
def remove_profile_picture(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    old_image_name = user.profile_image_name
    user.profile_image_name = None
    db.commit()
    _remove_stored_profile_image(old_image_name)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/profile")
def update_profile(payload: ProfileUpdate, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    user.name = payload.name
    user.phone = payload.phone
    if user.role == Role.FARMER:
        farmer = user.farmer_profile
        if farmer is None:
            farmer = FarmerProfile(user_id=user.id)
            db.add(farmer)
        farmer.farm_name = payload.farm_name or user.name
        farmer.village = payload.village or ""
        farmer.description = payload.farm_description or ""
        farmer.main_products = payload.main_products or ""
        farmer.phone = payload.phone
    db.commit()
    db.refresh(user)
    return profile(user)


@router.post("/change-password", status_code=204)
def change_password(payload: PasswordChange, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not verify_password(payload.current_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Current password is incorrect")
    if verify_password(payload.new_password, user.password_hash):
        raise HTTPException(status_code=400, detail="Choose a password different from your current password")
    user.password_hash = hash_password(payload.new_password)
    db.commit()
    return None


@router.get("/users", response_model=list[UserOut])
def list_users(user: User = Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    return db.query(User).order_by(User.created_at.desc()).all()
