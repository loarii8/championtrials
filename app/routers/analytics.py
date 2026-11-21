from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Product, Order, OrderItem, Role, StockTransaction
from app.auth import require_role

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(user=Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    revenue = db.query(func.coalesce(func.sum(Order.total), 0)).filter(
        Order.is_demo.is_(False)
    ).scalar()
    return {
        "users": db.query(func.count(User.id)).filter(User.is_demo.is_(False)).scalar(),
        "products": db.query(func.count(Product.id)).filter(
            Product.is_active.is_(True), Product.is_demo.is_(False)
        ).scalar(),
        "orders": db.query(func.count(Order.id)).filter(Order.is_demo.is_(False)).scalar(),
        "revenue": round(float(revenue), 2),
    }


@router.get("/farmer")
def farmer_analytics(user=Depends(require_role(Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    products = db.query(Product).filter(Product.is_demo.is_(False))
    if user.role == Role.FARMER:
        products = products.filter(Product.farmer_id == user.id)
    product_ids = [p.id for p in products.all()]
    if not product_ids:
        return {"revenue": 0, "units_sold": 0, "active_products": 0, "sales_by_category": []}
    revenue = db.query(func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0)).join(
        Order, Order.id == OrderItem.order_id
    ).filter(OrderItem.product_id.in_(product_ids), Order.is_demo.is_(False)).scalar()
    units = db.query(func.coalesce(func.sum(OrderItem.quantity), 0)).join(
        Order, Order.id == OrderItem.order_id
    ).filter(OrderItem.product_id.in_(product_ids), Order.is_demo.is_(False)).scalar()
    categories = db.query(Product.category, func.coalesce(func.sum(OrderItem.quantity), 0)).join(
        OrderItem, OrderItem.product_id == Product.id
    ).join(Order, Order.id == OrderItem.order_id).filter(
        Product.id.in_(product_ids), Order.is_demo.is_(False)
    ).group_by(Product.category).all()
    return {
        "revenue": round(float(revenue), 2),
        "units_sold": int(units),
        "active_products": len(product_ids),
        "sales_by_category": [{"category": c, "units": int(u)} for c, u in categories],
    }


@router.get("/admin/sales")
def sales(user=Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    rows = db.query(
        Product.category,
        func.coalesce(func.sum(OrderItem.quantity * OrderItem.unit_price), 0),
    ).join(
        OrderItem, OrderItem.product_id == Product.id
    ).join(
        Order, Order.id == OrderItem.order_id
    ).filter(
        Product.is_demo.is_(False), Order.is_demo.is_(False)
    ).group_by(Product.category).all()
    return [{"category": category, "revenue": round(float(revenue), 2)} for category, revenue in rows]


@router.get("/admin")
def admin_analytics(user=Depends(require_role(Role.ADMIN)), db: Session = Depends(get_db)):
    return overview(user=user, db=db)
