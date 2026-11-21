from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session, joinedload

from app.auth import get_current_user, require_role
from app.database import get_db
from app.models import CartEntry, Favorite, Notification, Product, Role, User
from app.schemas import CartQuantityUpdate, NotificationOut

favorites_router = APIRouter(prefix="/favorites", tags=["favorites"])
notifications_router = APIRouter(prefix="/notifications", tags=["notifications"])
cart_router = APIRouter(prefix="/cart", tags=["cart"])


@cart_router.get("")
def get_cart(user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)):
    entries = db.query(CartEntry).options(
        joinedload(CartEntry.product).joinedload(Product.farmer)
    ).filter(CartEntry.user_id == user.id).all()
    return [
        {"quantity": entry.quantity, "product": entry.product}
        for entry in entries if entry.product and entry.product.is_active
    ]


@cart_router.put("/{product_id}")
def set_cart_quantity(product_id: int, payload: CartQuantityUpdate,
                      user: User = Depends(require_role(Role.CUSTOMER)),
                      db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id, Product.is_active.is_(True)
    ).first()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.quantity > product.stock:
        raise HTTPException(status_code=409, detail="Requested quantity exceeds available stock")
    entry = db.query(CartEntry).filter_by(user_id=user.id, product_id=product_id).first()
    if entry is None:
        entry = CartEntry(user_id=user.id, product_id=product_id, quantity=payload.quantity)
        db.add(entry)
    else:
        entry.quantity = payload.quantity
    db.commit()
    return {"product_id": product_id, "quantity": payload.quantity}


@cart_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_cart_item(product_id: int, user: User = Depends(require_role(Role.CUSTOMER)),
                     db: Session = Depends(get_db)):
    db.query(CartEntry).filter_by(user_id=user.id, product_id=product_id).delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@cart_router.delete("", status_code=status.HTTP_204_NO_CONTENT)
def clear_cart(user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)):
    db.query(CartEntry).filter_by(user_id=user.id).delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@favorites_router.get("")
def list_favorites(user: User = Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)):
    favorites = (
        db.query(Favorite)
        .options(joinedload(Favorite.product).joinedload(Product.farmer))
        .filter(Favorite.user_id == user.id)
        .order_by(Favorite.created_at.desc())
        .all()
    )
    return [favorite.product for favorite in favorites if favorite.product and favorite.product.is_active]


@favorites_router.post("/{product_id}", status_code=status.HTTP_201_CREATED)
def add_favorite(product_id: int, user: User = Depends(require_role(Role.CUSTOMER)),
                 db: Session = Depends(get_db)):
    product = db.query(Product).filter(
        Product.id == product_id, Product.is_active.is_(True)
    ).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    favorite = db.query(Favorite).filter_by(user_id=user.id, product_id=product_id).first()
    if favorite is None:
        db.add(Favorite(user_id=user.id, product_id=product_id))
        db.commit()
    return {"product_id": product_id, "is_favorite": True}


@favorites_router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_favorite(product_id: int, user: User = Depends(require_role(Role.CUSTOMER)),
                    db: Session = Depends(get_db)):
    db.query(Favorite).filter_by(user_id=user.id, product_id=product_id).delete()
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@notifications_router.get("", response_model=list[NotificationOut])
def list_notifications(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    return db.query(Notification).filter(
        Notification.user_id == user.id
    ).order_by(Notification.created_at.desc()).limit(100).all()


@notifications_router.patch("/{notification_id}/read", response_model=NotificationOut)
def mark_notification_read(notification_id: int, user: User = Depends(get_current_user),
                           db: Session = Depends(get_db)):
    notification = db.query(Notification).filter(
        Notification.id == notification_id, Notification.user_id == user.id
    ).first()
    if notification is None:
        raise HTTPException(status_code=404, detail="Notification not found")
    notification.is_read = True
    db.commit()
    db.refresh(notification)
    return notification


@notifications_router.post("/read-all", status_code=status.HTTP_204_NO_CONTENT)
def mark_all_notifications_read(user: User = Depends(get_current_user),
                                db: Session = Depends(get_db)):
    db.query(Notification).filter(
        Notification.user_id == user.id, Notification.is_read.is_(False)
    ).update({"is_read": True}, synchronize_session=False)
    db.commit()
    return Response(status_code=status.HTTP_204_NO_CONTENT)
