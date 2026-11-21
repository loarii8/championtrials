from datetime import datetime, date
from sqlalchemy import String, Integer, Float, ForeignKey, DateTime, Enum, Text, UniqueConstraint, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base
import enum


class Role(str, enum.Enum):
    CUSTOMER = "customer"
    FARMER = "farmer"
    ADMIN = "admin"


class OrderStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    READY_FOR_PICKUP = "ready_for_pickup"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    # Compatibility values retained for existing demonstration clients.
    CONFIRMED = "confirmed"
    PREPARING = "preparing"
    DELIVERED = "delivered"


class StockChange(str, enum.Enum):
    ADD = "add"
    SALE = "sale"
    ADJUSTMENT = "adjustment"


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role), default=Role.CUSTOMER)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    profile_image_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    terms_accepted: Mapped[bool] = mapped_column(default=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    products: Mapped[list["Product"]] = relationship(back_populates="farmer")
    orders: Mapped[list["Order"]] = relationship(back_populates="customer")
    farmer_profile: Mapped["FarmerProfile | None"] = relationship(back_populates="user", uselist=False)


class FarmerProfile(Base):
    __tablename__ = "farmer_profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True, index=True)
    farm_name: Mapped[str] = mapped_column(String(150), default="")
    village: Mapped[str] = mapped_column(String(150), default="")
    description: Mapped[str] = mapped_column(Text, default="")
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    main_products: Mapped[str] = mapped_column(Text, default="")
    user: Mapped["User"] = relationship(back_populates="farmer_profile")


class Product(Base):
    __tablename__ = "products"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(150), index=True)
    description: Mapped[str] = mapped_column(Text, default="")
    category: Mapped[str] = mapped_column(String(80), index=True)
    price: Mapped[float] = mapped_column(Float)
    stock: Mapped[int] = mapped_column(Integer, default=0)
    unit: Mapped[str] = mapped_column(String(20), default="kg")
    village: Mapped[str] = mapped_column(String(150), default="")
    image_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_source_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    image_license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    image_attribution: Mapped[str | None] = mapped_column(String(500), nullable=True)
    image_is_generic: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    origin_status: Mapped[str] = mapped_column(String(40), default="unverified", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    farmer_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    is_active: Mapped[bool] = mapped_column(default=True)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    farmer: Mapped["User"] = relationship(back_populates="products")
    order_items: Mapped[list["OrderItem"]] = relationship(back_populates="product")
    stock_transactions: Mapped[list["StockTransaction"]] = relationship(back_populates="product")

    @property
    def farmer_name(self) -> str | None:
        return self.farmer.name if self.farmer else None

    @property
    def farmer_location(self) -> str | None:
        if self.farmer and self.farmer.farmer_profile:
            return self.farmer.farmer_profile.village
        return self.village


class Order(Base):
    __tablename__ = "orders"
    id: Mapped[int] = mapped_column(primary_key=True)
    customer_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    status: Mapped[OrderStatus] = mapped_column(Enum(OrderStatus), default=OrderStatus.PENDING)
    total: Mapped[float] = mapped_column(Float)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    delivery_address: Mapped[str] = mapped_column(Text)
    pickup_date: Mapped[date | None] = mapped_column(nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    customer: Mapped["User"] = relationship(back_populates="orders")
    items: Mapped[list["OrderItem"]] = relationship(back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"
    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    quantity: Mapped[int] = mapped_column(Integer)
    unit_price: Mapped[float] = mapped_column(Float)
    order: Mapped["Order"] = relationship(back_populates="items")
    product: Mapped["Product"] = relationship(back_populates="order_items")

    @property
    def product_name(self) -> str | None:
        return self.product.name if self.product else None

    @property
    def farmer_name(self) -> str | None:
        return self.product.farmer.name if self.product and self.product.farmer else None


class StockTransaction(Base):
    __tablename__ = "stock_transactions"
    id: Mapped[int] = mapped_column(primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    change_type: Mapped[StockChange] = mapped_column(Enum(StockChange))
    note: Mapped[str] = mapped_column(String(255), default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    product: Mapped["Product"] = relationship(back_populates="stock_transactions")


class Favorite(Base):
    __tablename__ = "favorites"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_favorite_user_product"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship()


class Notification(Base):
    __tablename__ = "notifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(150))
    message: Mapped[str] = mapped_column(Text)
    kind: Mapped[str] = mapped_column(String(50), default="activity")
    is_read: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    user: Mapped["User"] = relationship()


class CartEntry(Base):
    __tablename__ = "cart_entries"
    __table_args__ = (UniqueConstraint("user_id", "product_id", name="uq_cart_user_product"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    user: Mapped["User"] = relationship()
    product: Mapped["Product"] = relationship()


class ResearchSource(Base):
    __tablename__ = "research_sources"
    id: Mapped[int] = mapped_column(primary_key=True)
    url: Mapped[str] = mapped_column(String(1000), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(300))
    publisher: Mapped[str] = mapped_column(String(200), default="")
    source_type: Mapped[str] = mapped_column(String(60), default="public_source")
    coverage: Mapped[str] = mapped_column(Text, default="")
    notes: Mapped[str] = mapped_column(Text, default="")
    accessed_at: Mapped[datetime] = mapped_column(DateTime)


class LocalResearchRecord(Base):
    __tablename__ = "local_research_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    record_type: Mapped[str] = mapped_column(String(60), index=True)
    title: Mapped[str] = mapped_column(String(250))
    description: Mapped[str] = mapped_column(Text)
    location: Mapped[str] = mapped_column(String(200), default="")
    verification_status: Mapped[str] = mapped_column(String(40), default="unverified", index=True)
    publication_status: Mapped[str] = mapped_column(String(30), default="pending", index=True)
    public_listing_permission: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_demo: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("research_sources.id"), index=True)
    metadata_json: Mapped[str] = mapped_column(Text, default="{}")
    last_verified_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source: Mapped["ResearchSource"] = relationship()


class ResearchImage(Base):
    __tablename__ = "research_images"
    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(160), unique=True, index=True)
    title: Mapped[str] = mapped_column(String(250))
    local_asset: Mapped[str] = mapped_column(String(300))
    image_url: Mapped[str] = mapped_column(String(1000))
    source_page: Mapped[str] = mapped_column(String(1000))
    photographer: Mapped[str] = mapped_column(String(200), default="")
    license: Mapped[str] = mapped_column(String(100))
    license_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    attribution: Mapped[str] = mapped_column(String(500))
    subject: Mapped[str] = mapped_column(String(500))
    image_type: Mapped[str] = mapped_column(String(50), index=True)
    local_to_peja: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    usage_rights_confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    display_publicly: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_id: Mapped[int] = mapped_column(ForeignKey("research_sources.id"), index=True)
    last_verified_at: Mapped[datetime] = mapped_column(DateTime)
    source: Mapped["ResearchSource"] = relationship()
