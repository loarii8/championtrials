import json
from pathlib import Path

from sqlalchemy.orm import Session
from app.auth import hash_password
from app.models import (
    User,
    Role,
    Product,
    Order,
    OrderItem,
    OrderStatus,
    FarmerProfile,
    StockTransaction,
    StockChange,
)


DEMO_ACCOUNTS = [
    ("Admin User", "admin@pejamarket.local", "Admin123!", Role.ADMIN),
    ("Green Valley Farm", "farmer@pejamarket.local", "Farmer123!", Role.FARMER),
    ("Demo Customer", "customer@pejamarket.local", "Customer123!", Role.CUSTOMER),
]
DEMO_FARMS = [
    ("Green Valley Farm", "green.valley@pejamarket.local", "Rugova"),
    ("Sunrise Orchard", "sunrise.orchard@pejamarket.local", "Istog"),
    ("Dukagjin Dairy", "dukagjin.dairy@pejamarket.local", "Krushe e Madhe"),
    ("Stone Mill Homestead", "stone.mill@pejamarket.local", "Drelaj"),
    ("Alpine Berry Farm", "alpine.berry@pejamarket.local", "Vranovac"),
]
DEMO_IMAGE_BY_PRODUCT = {
    "Vine Tomatoes": "generic-tomatoes",
    "Baby Spinach": "generic-spinach",
    "Red Apples": "generic-apples",
    "Sweet Peppers": "generic-peppers",
    "Honey Jar": "generic-honey",
    "Garden Cucumbers": "generic-cucumbers",
    "Ripe Pears": "generic-pears",
    "Sour Cherries": "generic-sour-cherries",
    "Natural Yogurt": "generic-natural-yogurt",
    "White Cheese": "generic-cheese",
    "Free-range Eggs": "generic-eggs",
    "Buckwheat Flour": "generic-buckwheat-flour",
    "Whole Corn": "generic-corn-kernels",
    "Wildflower Honey": "generic-honey",
    "Plum Preserves": "generic-plum-jam",
    "Carrots": "generic-carrots",
    "Brown Bread": "generic-brown-bread",
    "Mixed Herb Bundle": "generic-herbs",
}
SEED_IMAGE_URLS = (
    "https://images.unsplash.com/photo-1540420773420-3366772f4999",
    "https://images.unsplash.com/photo-1560806887-1e4cd0b6cbd6",
    "https://images.unsplash.com/photo-1628088062854-d1870b4553da",
    "https://images.unsplash.com/photo-1574323347407-f5e1ad6d020b",
    "https://images.unsplash.com/photo-1488477181946-6428a0291777",
    "https://images.unsplash.com/photo-1466637574441-749b8f19452f",
)


def _image_catalog():
    path = Path(__file__).resolve().parents[1] / "research" / "images.json"
    return {
        image["slug"]: image
        for image in json.loads(path.read_text(encoding="utf-8"))["images"]
    }


def _apply_image_metadata(product, image):
    product.image_url = f"/research/images/{image['slug']}/file"
    product.image_source_url = image["source_page"]
    product.image_license = image["license"]
    product.image_attribution = image["attribution"]
    product.image_is_generic = True


def seed(db: Session):
    for name, email, password, role in DEMO_ACCOUNTS:
        if not db.query(User).filter(User.email == email).first():
            db.add(User(
                name=name, email=email, password_hash=hash_password(password),
                role=role, is_demo=True,
            ))
    db.commit()
    for name, email, village in DEMO_FARMS:
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                name=name, email=email, password_hash=hash_password("Farmer123!"),
                role=Role.FARMER, is_demo=True,
            )
            db.add(user)
            db.flush()
        user.is_demo = True
        profile = db.query(FarmerProfile).filter(FarmerProfile.user_id == user.id).first()
        if profile is None:
            profile = FarmerProfile(user_id=user.id)
            db.add(profile)
        if not profile.description or "Fictional demonstration farm" in profile.description:
            profile.farm_name = name
            profile.village = village
            profile.description = f"Fictional demonstration farm near {village}, Kosovo."
    for number in range(1, 10):
        email = f"customer{number}@pejamarket.local"
        user = db.query(User).filter(User.email == email).first()
        if not user:
            user = User(
                name=f"Demo Customer {number}", email=email,
                password_hash=hash_password("Customer123!"), role=Role.CUSTOMER,
                is_demo=True,
            )
            db.add(user)
        user.is_demo = True
    for _, email, _, _ in DEMO_ACCOUNTS:
        user = db.query(User).filter(User.email == email).first()
        if user:
            user.is_demo = True
    db.commit()

    demo_farmer_ids = [
        farmer_id for (farmer_id,) in db.query(User.id).filter(
            User.role == Role.FARMER, User.is_demo.is_(True)
        ).all()
    ]
    if demo_farmer_ids:
        db.query(Product).filter(Product.farmer_id.in_(demo_farmer_ids)).update(
            {Product.is_demo: True}, synchronize_session=False
        )
    for product in db.query(Product).filter(Product.is_demo.is_(True)).all():
        product.description = (
            "Fictional demonstration listing. Product origin, stock, price, and availability "
            "are not verified and are not a current local offer."
        )
    image_catalog = _image_catalog()
    if db.query(Product).filter(Product.is_demo.is_(True)).count() < 20:
        farmers = db.query(User).filter(
            User.role == Role.FARMER, User.is_demo.is_(True)
        ).order_by(User.id).all()
        catalog = [
            ("Vine Tomatoes", "Locally grown vine tomatoes.", "Vegetables", 3.20, "kg", "Rugova"),
            ("Baby Spinach", "Fresh washed baby spinach.", "Vegetables", 2.40, "package", "Istog"),
            ("Red Apples", "Crisp seasonal apples.", "Fruits", 3.80, "kg", "Drelaj"),
            ("Sweet Peppers", "Fresh red and yellow peppers.", "Vegetables", 4.10, "kg", "Rugova"),
            ("Strawberries", "Small-batch strawberries.", "Fruits", 5.50, "package", "Vranovac"),
            ("Fresh Cow Milk", "Fresh demonstration dairy milk.", "Dairy Products", 1.20, "liter", "Krushe e Madhe"),
            ("White Cheese", "Locally produced fresh cheese.", "Dairy Products", 7.80, "kg", "Krushe e Madhe"),
            ("Free-range Eggs", "A dozen fresh eggs.", "Dairy Products", 5.00, "package", "Rugova"),
            ("Buckwheat Flour", "Stone-ground buckwheat flour.", "Grains", 3.60, "package", "Drelaj"),
            ("Whole Corn", "Locally harvested whole corn.", "Grains", 2.90, "kg", "Istog"),
            ("Wildflower Honey", "Pure wildflower honey.", "Homemade Products", 8.50, "package", "Rugova"),
            ("Plum Preserves", "Homemade plum preserves.", "Homemade Products", 6.40, "package", "Vranovac"),
            ("Green Beans", "Fresh green beans.", "Vegetables", 3.50, "kg", "Istog"),
            ("Carrots", "Crunchy local carrots.", "Vegetables", 2.20, "kg", "Drelaj"),
            ("Garden Cucumbers", "Fresh garden cucumbers.", "Vegetables", 2.80, "kg", "Rugova"),
            ("Ripe Pears", "Seasonal ripe pears.", "Fruits", 4.20, "kg", "Istog"),
            ("Sour Cherries", "Fresh sour cherries.", "Fruits", 5.20, "kg", "Vranovac"),
            ("Natural Yogurt", "Plain natural yogurt.", "Dairy Products", 2.10, "package", "Krushe e Madhe"),
            ("Brown Bread", "Freshly baked brown bread.", "Homemade Products", 2.50, "piece", "Drelaj"),
            ("Mixed Herb Bundle", "Parsley, mint, and garden herbs.", "Other", 1.80, "package", "Rugova"),
        ]
        for index, (name, description, category, price, unit, village) in enumerate(catalog):
            if db.query(Product).filter(Product.name == name).first():
                continue
            image = image_catalog.get(DEMO_IMAGE_BY_PRODUCT.get(name, ""))
            product = Product(
                name=name,
                description=(
                    "Fictional demonstration listing. Product origin, stock, price, and "
                    "availability are not verified and are not a current local offer."
                ),
                category=category,
                price=price,
                stock=20 + ((index * 7) % 45),
                unit=unit,
                village=village,
                farmer_id=farmers[index % len(farmers)].id,
                is_active=True,
                image_url=None,
                is_demo=True,
            )
            if image:
                _apply_image_metadata(product, image)
            db.add(product)
            db.flush()
            db.add(StockTransaction(product_id=product.id, quantity=product.stock,
                                    change_type=StockChange.ADD, note="Demonstration seed inventory"))
        db.commit()

    image_catalog = _image_catalog()
    known_demo_urls = {url for url in SEED_IMAGE_URLS}
    for product in db.query(Product).filter(Product.is_demo.is_(True)).all():
        image = image_catalog.get(DEMO_IMAGE_BY_PRODUCT.get(product.name, ""))
        legacy_image = bool(
            product.image_url
            and (
                any(product.image_url.startswith(url) for url in known_demo_urls)
                or product.image_url.startswith("/products/")
            )
        )
        if image and (not product.image_url or legacy_image):
            _apply_image_metadata(product, image)
        elif legacy_image:
            product.image_url = None
            product.image_source_url = None
            product.image_license = None
            product.image_attribution = None
            product.image_is_generic = False

    demo_customer_ids = [
        customer_id for (customer_id,) in db.query(User.id).filter(
            User.role == Role.CUSTOMER, User.is_demo.is_(True)
        ).all()
    ]
    demo_order_ids = db.query(OrderItem.order_id).join(Product).filter(
        Product.is_demo.is_(True)
    )
    db.query(Order).filter(
        (Order.customer_id.in_(demo_customer_ids)) | (Order.id.in_(demo_order_ids))
    ).update({Order.is_demo: True}, synchronize_session=False)
    db.commit()
    if db.query(Order).filter(Order.is_demo.is_(True)).count() < 10:
        customers = db.query(User).filter(
            User.role == Role.CUSTOMER, User.is_demo.is_(True)
        ).order_by(User.id).all()
        products = db.query(Product).filter(
            Product.is_active.is_(True), Product.is_demo.is_(True)
        ).all()
        statuses = [
            OrderStatus.PENDING,
            OrderStatus.ACCEPTED,
            OrderStatus.READY_FOR_PICKUP,
            OrderStatus.COMPLETED,
            OrderStatus.CANCELLED,
            OrderStatus.REJECTED,
        ]
        for index in range(10):
            product = products[index % len(products)]
            quantity = 1 + (index % 3)
            status = statuses[index % len(statuses)]
            order = Order(
                customer_id=customers[index % len(customers)].id,
                status=status,
                total=round(product.price * quantity, 2),
                is_demo=True,
                delivery_address=f"{5 + index} Demonstration Road, Peja",
            )
            db.add(order)
            db.flush()
            db.add(OrderItem(order_id=order.id, product_id=product.id,
                             quantity=quantity, unit_price=product.price))
        db.commit()

    db.commit()
