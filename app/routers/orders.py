from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, joinedload
from app.database import get_db
from app.models import (
    Order, OrderItem, Product, StockTransaction, StockChange, OrderStatus, Role, Notification, CartEntry,
    User,
)
from app.schemas import OrderCheckoutOut, OrderCreate, OrderOut, OrderStatusUpdate
from app.auth import require_role

router = APIRouter(prefix="/orders", tags=["orders"])


def _ensure_order_access(order: Order, user: User, db: Session) -> None:
    if user.role == Role.CUSTOMER and order.customer_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    if user.role == Role.FARMER and not any(
        db.get(Product, item.product_id).farmer_id == user.id for item in order.items
    ):
        raise HTTPException(status_code=403, detail="Not authorized")


@router.post("", response_model=OrderCheckoutOut, status_code=201)
def create_order(payload: OrderCreate, user=Depends(require_role(Role.CUSTOMER)), db: Session = Depends(get_db)):
    if len({item.product_id for item in payload.items}) != len(payload.items):
        raise HTTPException(status_code=422, detail="Duplicate products are not allowed")
    items_by_farmer: dict[int, list[tuple[Product, int]]] = {}
    for cart_item in payload.items:
        product = db.get(Product, cart_item.product_id)
        if not product or not product.is_active:
            raise HTTPException(status_code=404, detail=f"Product {cart_item.product_id} not found")
        if product.stock < cart_item.quantity:
            raise HTTPException(status_code=409, detail=f"Insufficient stock for {product.name}")
        items_by_farmer.setdefault(product.farmer_id, []).append((product, cart_item.quantity))

    orders: list[Order] = []
    for farmer_id, farmer_items in items_by_farmer.items():
        order = Order(
            customer_id=user.id,
            delivery_address=payload.delivery_address,
            total=0,
            pickup_date=payload.pickup_date,
            contact_phone=payload.contact_phone,
            is_demo=user.is_demo,
        )
        total = 0.0
        for product, quantity in farmer_items:
            order.is_demo = order.is_demo or product.is_demo
            product.stock -= quantity
            total += product.price * quantity
            order.items.append(
                OrderItem(product_id=product.id, quantity=quantity, unit_price=product.price)
            )
            db.add(StockTransaction(
                product_id=product.id,
                quantity=-quantity,
                change_type=StockChange.SALE,
                note="Order sale",
            ))
            if product.stock <= 5:
                db.add(Notification(
                    user_id=farmer_id,
                    title=f"Low stock: {product.name}",
                    message=f"Only {product.stock} {product.unit} remain in this listing.",
                    kind="inventory",
                ))
        order.total = round(total, 2)
        db.add(order)
        db.flush()
        orders.append(order)
        db.add(Notification(
            user_id=user.id,
            title=f"Order #{order.id} received",
            message="Your order has been placed and is waiting for farmer confirmation.",
            kind="order",
        ))
        db.add(Notification(
            user_id=farmer_id,
            title=f"New order #{order.id}",
            message="A customer placed an order for one or more of your products.",
            kind="order",
        ))

    db.query(CartEntry).filter_by(user_id=user.id).delete()
    db.commit()
    db.refresh(orders[0])
    return OrderCheckoutOut(
        **OrderOut.model_validate(orders[0]).model_dump(),
        order_ids=[order.id for order in orders],
    )


@router.get("", response_model=list[OrderOut])
def list_orders(user=Depends(require_role(Role.CUSTOMER, Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    query = db.query(Order).options(joinedload(Order.items))
    if user.role == Role.CUSTOMER:
        query = query.filter(Order.customer_id == user.id)
    elif user.role == Role.FARMER:
        product_ids = [p.id for p in db.query(Product).filter(Product.farmer_id == user.id).all()]
        if not product_ids:
            return []
        query = query.join(Order.items).filter(OrderItem.product_id.in_(product_ids)).distinct()
    return query.order_by(Order.created_at.desc()).all()


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user=Depends(require_role(Role.CUSTOMER, Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_order_access(order, user, db)
    return order


@router.patch("/{order_id}/status", response_model=OrderOut)
def update_status(order_id: int, payload: OrderStatusUpdate,
                  user=Depends(require_role(Role.CUSTOMER, Role.FARMER, Role.ADMIN)), db: Session = Depends(get_db)):
    order = db.query(Order).options(joinedload(Order.items)).filter(Order.id == order_id    ).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    _ensure_order_access(order, user, db)
    if user.role == Role.CUSTOMER:
        if payload.status != OrderStatus.CANCELLED or order.status not in {
            OrderStatus.PENDING, OrderStatus.CONFIRMED
        }:
            raise HTTPException(status_code=409, detail="This order can no longer be cancelled")
    if order.status == OrderStatus.CANCELLED and payload.status != OrderStatus.CANCELLED:
        raise HTTPException(status_code=409, detail="Cancelled orders cannot be reopened")

    allowed_transitions = {
        OrderStatus.PENDING: {OrderStatus.ACCEPTED, OrderStatus.CONFIRMED, OrderStatus.REJECTED, OrderStatus.CANCELLED},
        OrderStatus.ACCEPTED: {OrderStatus.READY_FOR_PICKUP, OrderStatus.PREPARING, OrderStatus.CANCELLED, OrderStatus.REJECTED},
        OrderStatus.CONFIRMED: {OrderStatus.ACCEPTED, OrderStatus.READY_FOR_PICKUP, OrderStatus.PREPARING, OrderStatus.DELIVERED, OrderStatus.CANCELLED, OrderStatus.REJECTED},
        OrderStatus.PREPARING: {OrderStatus.READY_FOR_PICKUP, OrderStatus.DELIVERED, OrderStatus.CANCELLED},
        OrderStatus.READY_FOR_PICKUP: {OrderStatus.COMPLETED, OrderStatus.DELIVERED, OrderStatus.CANCELLED},
        OrderStatus.COMPLETED: set(),
        OrderStatus.DELIVERED: set(),
        OrderStatus.CANCELLED: set(),
        OrderStatus.REJECTED: set(),
    }
    if payload.status not in allowed_transitions.get(order.status, set()):
        raise HTTPException(status_code=409, detail=f"Cannot change order from {order.status.value} to {payload.status.value}")

    if payload.status in {OrderStatus.CANCELLED, OrderStatus.REJECTED}:
        for item in order.items:
            product = db.get(Product, item.product_id)
            if product:
                product.stock += item.quantity
                db.add(StockTransaction(product_id=product.id, quantity=item.quantity,
                                         change_type=StockChange.ADJUSTMENT,
                                         note=f"Restored {payload.status.value} order #{order.id}"))
    order.status = payload.status
    db.add(Notification(
        user_id=order.customer_id,
        title=f"Order #{order.id} {payload.status.value.replace('_', ' ')}",
        message=f"Your order status is now {payload.status.value.replace('_', ' ')}.",
        kind="order",
    ))
    db.commit()
    db.refresh(order)
    return order
