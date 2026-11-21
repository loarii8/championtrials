from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field
from app.models import Role, OrderStatus


class UserCreate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(min_length=6, max_length=128)
    role: Role = Role.CUSTOMER
    terms_accepted: bool = False
    phone: str | None = Field(default=None, max_length=50)
    farm_name: str | None = Field(default=None, max_length=150)
    village: str | None = Field(default=None, max_length=150)
    farm_description: str | None = Field(default=None, max_length=2000)
    main_products: str | None = Field(default=None, max_length=500)


class UserOut(BaseModel):
    id: int
    name: str
    email: str
    role: Role
    phone: str | None = None
    is_demo: bool = False
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserOut


class Login(BaseModel):
    email: str = Field(min_length=3, max_length=255)
    password: str
    remember_me: bool = False


class ProductCreate(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    description: str = ""
    category: str = Field(min_length=1, max_length=80)
    price: float = Field(gt=0)
    stock: int = Field(ge=0)
    unit: str = Field(default="kg", max_length=20)
    village: str = Field(default="", max_length=150)
    image_url: str | None = None


class ProductUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=150)
    description: str | None = None
    category: str | None = Field(default=None, min_length=1, max_length=80)
    price: float | None = Field(default=None, gt=0)
    stock: int | None = Field(default=None, ge=0)
    unit: str | None = Field(default=None, max_length=20)
    village: str | None = Field(default=None, max_length=150)
    image_url: str | None = None
    is_active: bool | None = None


class StockUpdate(BaseModel):
    quantity: int
    note: str = ""


class ProductOut(BaseModel):
    id: int
    name: str
    description: str
    category: str
    price: float
    stock: int
    unit: str
    village: str
    image_url: str | None
    image_source_url: str | None = None
    image_license: str | None = None
    image_attribution: str | None = None
    image_is_generic: bool = False
    origin_status: str = "unverified"
    farmer_id: int
    is_active: bool
    is_demo: bool = False
    created_at: datetime | None = None
    farmer_name: str | None = None
    farmer_location: str | None = None
    model_config = {"from_attributes": True}


class CartItem(BaseModel):
    product_id: int
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    items: list[CartItem] = Field(min_length=1)
    delivery_address: str = Field(min_length=5)
    pickup_date: date | None = None
    contact_phone: str | None = Field(default=None, max_length=50)


class OrderItemOut(BaseModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    product_name: str | None = None
    farmer_name: str | None = None
    model_config = {"from_attributes": True}


class OrderOut(BaseModel):
    id: int
    customer_id: int
    status: OrderStatus
    total: float
    is_demo: bool = False
    delivery_address: str
    pickup_date: date | None = None
    contact_phone: str | None = None
    created_at: datetime
    items: list[OrderItemOut]
    model_config = {"from_attributes": True}


class OrderCheckoutOut(OrderOut):
    order_ids: list[int]


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class ProfileUpdate(BaseModel):
    name: str = Field(min_length=2, max_length=100)
    phone: str | None = Field(default=None, max_length=50)
    farm_name: str | None = Field(default=None, max_length=150)
    village: str | None = Field(default=None, max_length=150)
    farm_description: str | None = Field(default=None, max_length=2000)
    main_products: str | None = Field(default=None, max_length=500)


class PasswordChange(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class NotificationOut(BaseModel):
    id: int
    title: str
    message: str
    kind: str
    is_read: bool
    created_at: datetime

    model_config = {"from_attributes": True}


class CartQuantityUpdate(BaseModel):
    quantity: int = Field(ge=1, le=1000)
