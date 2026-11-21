from io import BytesIO
from pathlib import Path
import secrets
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi import UploadFile, File
from PIL import Image, UnidentifiedImageError
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Product, Role, StockTransaction, StockChange, User, FarmerProfile, OrderItem, Notification
from app.schemas import ProductCreate, ProductUpdate, ProductOut, StockUpdate
from app.auth import get_current_user, require_role

router = APIRouter(prefix="/products", tags=["products"])
UPLOAD_DIRECTORY = Path(__file__).resolve().parents[2] / "uploads"
MAX_IMAGE_BYTES = 5 * 1024 * 1024
IMAGE_SIGNATURES = {
    "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
    "image/webp": (b"RIFF", ".webp"),
}


@router.get("", response_model=list[ProductOut])
def list_products(
    category: str | None = None,
    search: str | None = None,
    min_price: float | None = Query(default=None, ge=0),
    max_price: float | None = Query(default=None, ge=0),
    available: bool = True,
    sort: str = "newest",
    village: str | None = None,
    unit: str | None = None,
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=60, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(Product).join(User, Product.farmer_id == User.id).outerjoin(
        FarmerProfile, FarmerProfile.user_id == User.id
    ).filter(Product.is_active.is_(True))
    if category:
        query = query.filter(Product.category.ilike(f"%{category}%"))
    if search:
        match = f"%{search}%"
        query = query.filter(
            Product.name.ilike(match) |
            Product.description.ilike(match) |
            User.name.ilike(match) |
            Product.village.ilike(match) |
            FarmerProfile.village.ilike(match)
        )
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)
    if available:
        query = query.filter(Product.stock > 0)
    if village:
        query = query.filter(
            Product.village.ilike(f"%{village}%") |
            FarmerProfile.village.ilike(f"%{village}%")
        )
    if unit:
        query = query.filter(Product.unit == unit)
    if sort == "price_low":
        query = query.order_by(Product.price.asc())
    elif sort == "price_high":
        query = query.order_by(Product.price.desc())
    elif sort == "oldest":
        query = query.order_by(Product.created_at.asc())
    elif sort == "alphabetical":
        query = query.order_by(Product.name.asc())
    elif sort == "popular":
        popularity = db.query(
            OrderItem.product_id.label("product_id"),
            func.coalesce(func.sum(OrderItem.quantity), 0).label("units_sold"),
        ).group_by(OrderItem.product_id).subquery()
        query = query.outerjoin(popularity, popularity.c.product_id == Product.id).order_by(
            popularity.c.units_sold.desc(), Product.created_at.desc()
        )
    else:
        query = query.order_by(Product.created_at.desc(), Product.id.desc())
    return query.offset(offset).limit(limit).all()


@router.get("/mine", response_model=list[ProductOut])
def mine(user=Depends(require_role(Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    query = db.query(Product)
    if user.role == Role.FARMER:
        query = query.filter(Product.farmer_id == user.id)
    return query.order_by(Product.id.desc()).all()


@router.get("/meta")
def marketplace_meta(db: Session = Depends(get_db)):
    return {
        "available_products": db.query(Product).filter(
            Product.is_active.is_(True), Product.stock > 0, Product.is_demo.is_(False)
        ).count(),
        "demo_available_products": db.query(Product).filter(
            Product.is_active.is_(True), Product.stock > 0, Product.is_demo.is_(True)
        ).count(),
        "farmers": db.query(User.id).filter(
            User.role == Role.FARMER, User.is_demo.is_(False)
        ).count(),
        "demo_farmers": db.query(User.id).filter(
            User.role == Role.FARMER, User.is_demo.is_(True)
        ).count(),
        "categories": sorted(
            category for (category,) in db.query(Product.category).filter(
                Product.is_active.is_(True)
            ).distinct().all()
        ),
    }


@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, user=Depends(require_role(Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    product = Product(**payload.model_dump(), farmer_id=user.id)
    db.add(product)
    db.commit()
    db.refresh(product)
    if product.stock:
        db.add(StockTransaction(product_id=product.id, quantity=product.stock, change_type=StockChange.ADD, note="Initial stock"))
    db.add(Notification(
        user_id=user.id,
        title=f"{product.name} published",
        message="Your product listing is live in the marketplace.",
        kind="listing",
    ))
    db.commit()
    return product


@router.post("/{product_id}/image", response_model=ProductOut)
async def upload_product_image(
    product_id: int,
    image: UploadFile = File(...),
    user=Depends(require_role(Role.FARMER, Role.ADMIN)),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if product is None or not product.is_active:
        raise HTTPException(status_code=404, detail="Product not found")
    if user.role == Role.FARMER and product.farmer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own products")
    signature = IMAGE_SIGNATURES.get(image.content_type or "")
    if signature is None:
        raise HTTPException(status_code=415, detail="Upload a JPEG, PNG, or WebP image")
    content = await image.read(MAX_IMAGE_BYTES + 1)
    if len(content) > MAX_IMAGE_BYTES:
        raise HTTPException(status_code=413, detail="Image must be 5 MB or smaller")
    file_signature, extension = signature
    if not content.startswith(file_signature) or (
        image.content_type == "image/webp" and content[8:12] != b"WEBP"
    ):
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid supported image")
    try:
        with Image.open(BytesIO(content)) as decoded:
            if decoded.format not in {"JPEG", "PNG", "WEBP"}:
                raise HTTPException(status_code=415, detail="The uploaded file is not a valid supported image")
            decoded.verify()
        with Image.open(BytesIO(content)) as decoded:
            if decoded.width > 8000 or decoded.height > 8000:
                raise HTTPException(status_code=413, detail="Image dimensions must be 8000 pixels or smaller")
    except UnidentifiedImageError as exc:
        raise HTTPException(status_code=415, detail="The uploaded file is not a valid image") from exc
    UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)
    filename = f"{secrets.token_hex(16)}{extension}"
    target = UPLOAD_DIRECTORY / filename
    target.write_bytes(content)
    if product.image_url and product.image_url.startswith("/uploads/"):
        old_image = (UPLOAD_DIRECTORY / Path(product.image_url).name).resolve()
        if old_image.parent == UPLOAD_DIRECTORY.resolve() and old_image.is_file():
            old_image.unlink()
    product.image_url = f"/uploads/{filename}"
    product.image_source_url = None
    product.image_license = "Farmer-provided; rights not independently verified"
    product.image_attribution = (
        f"Image supplied by {product.farmer.name}; source and reuse rights not independently checked."
    )
    product.image_is_generic = False
    db.commit()
    db.refresh(product)
    return product


@router.put("/{product_id}", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, user=Depends(require_role(Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if user.role == Role.FARMER and product.farmer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own products")
    old_stock = product.stock
    updates = payload.model_dump(exclude_unset=True)
    if "image_url" in updates and updates["image_url"] != product.image_url:
        product.image_source_url = None
        product.image_license = "Farmer-provided; rights not independently verified"
        product.image_attribution = "External image URL supplied with this listing; rights not independently checked."
        product.image_is_generic = False
    for field, value in updates.items():
        setattr(product, field, value)
    db.commit()
    if payload.stock is not None and payload.stock != old_stock:
        db.add(StockTransaction(product_id=product.id, quantity=payload.stock - old_stock,
                                 change_type=StockChange.ADJUSTMENT, note="Manual stock adjustment"))
        db.commit()
    db.refresh(product)
    return product


@router.post("/{product_id}/stock", response_model=ProductOut)
def add_stock(product_id: int, payload: StockUpdate, user=Depends(require_role(Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if user.role == Role.FARMER and product.farmer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own products")
    if payload.quantity == 0:
        raise HTTPException(status_code=422, detail="Quantity cannot be zero")
    if product.stock + payload.quantity < 0:
        raise HTTPException(status_code=409, detail="Stock cannot be negative")
    product.stock += payload.quantity
    db.add(StockTransaction(product_id=product.id, quantity=payload.quantity,
                             change_type=StockChange.ADD if payload.quantity > 0 else StockChange.ADJUSTMENT,
                             note=payload.note or "Stock update"))
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, user=Depends(require_role(Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if user.role == Role.FARMER and product.farmer_id != user.id:
        raise HTTPException(status_code=403, detail="You can only manage your own products")
    product.is_active = False
    db.commit()
    return None
