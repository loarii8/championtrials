from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.auth import require_role
from app.database import get_db
from app.models import FarmerProfile, Product, Role, User

router = APIRouter(prefix="/farmers", tags=["farmers"])


def _farmer_response(farmer: User, db: Session) -> dict[str, object]:
    profile = farmer.farmer_profile
    return {
        "id": farmer.id,
        "name": farmer.name,
        "is_demo": farmer.is_demo,
        "product_count": db.query(func.count(Product.id)).filter(
            Product.farmer_id == farmer.id, Product.is_active.is_(True)
        ).scalar(),
        "available_products": db.query(func.count(Product.id)).filter(
            Product.farmer_id == farmer.id,
            Product.is_active.is_(True),
            Product.stock > 0,
        ).scalar(),
        "profile": (
            {
                "farm_name": profile.farm_name,
                "village": profile.village,
                "description": profile.description,
                "phone": profile.phone,
                "main_products": profile.main_products,
            }
            if profile
            else {
                "farm_name": farmer.name,
                "village": "",
                "description": "",
                "phone": None,
                "main_products": "",
            }
        ),
    }


@router.get("")
def list_farmers(search: str | None = None, village: str | None = None,
                 db: Session = Depends(get_db)):
    query = db.query(User).options(joinedload(User.farmer_profile)).outerjoin(
        FarmerProfile, FarmerProfile.user_id == User.id
    ).filter(User.role == Role.FARMER)
    if search:
        query = query.filter(
            (User.name.ilike(f"%{search}%")) |
            (FarmerProfile.farm_name.ilike(f"%{search}%")) |
            (FarmerProfile.description.ilike(f"%{search}%"))
        )
    if village:
        query = query.filter(FarmerProfile.village.ilike(f"%{village}%"))
    farmers = query.order_by(User.name).all()
    return [_farmer_response(farmer, db) for farmer in farmers]


@router.get("/{farmer_id}")
def get_farmer(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(User).options(joinedload(User.farmer_profile)).filter(
        User.id == farmer_id, User.role == Role.FARMER
    ).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return _farmer_response(farmer, db)


@router.get("/{farmer_id}/products")
def farmer_products(farmer_id: int, db: Session = Depends(get_db)):
    farmer = db.query(User).filter(User.id == farmer_id, User.role == Role.FARMER).first()
    if not farmer:
        raise HTTPException(status_code=404, detail="Farmer not found")
    return db.query(Product).filter(
        Product.farmer_id == farmer_id, Product.is_active.is_(True)
    ).order_by(Product.created_at.desc()).all()
