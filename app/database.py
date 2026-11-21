import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("TEST_DATABASE_URL") or os.getenv("DATABASE_URL", "sqlite:///./pejamarket.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def migrate_sqlite_schema(engine):
    if not str(engine.url).startswith("sqlite"):
        return
    from sqlalchemy import text
    with engine.begin() as connection:
        def columns(table):
            return {row[1] for row in connection.exec_driver_sql(f"PRAGMA table_info({table})")}

        product_columns = columns("products")
        product_alters = {
            "unit": "VARCHAR(20) NOT NULL DEFAULT 'kg'",
            "village": "VARCHAR(150) NOT NULL DEFAULT ''",
            "created_at": "DATETIME",
            "image_source_url": "VARCHAR(1000)",
            "image_license": "VARCHAR(100)",
            "image_attribution": "VARCHAR(500)",
            "image_is_generic": "BOOLEAN NOT NULL DEFAULT 0",
            "origin_status": "VARCHAR(40) NOT NULL DEFAULT 'unverified'",
            "is_demo": "BOOLEAN NOT NULL DEFAULT 0",
        }
        for name, column_type in product_alters.items():
            if name not in product_columns:
                connection.execute(text(f"ALTER TABLE products ADD COLUMN {name} {column_type}"))

        order_columns = columns("orders")
        order_alters = {
            "pickup_date": "DATE",
            "contact_phone": "VARCHAR(50)",
            "is_demo": "BOOLEAN NOT NULL DEFAULT 0",
        }
        for name, column_type in order_alters.items():
            if name not in order_columns:
                connection.execute(text(f"ALTER TABLE orders ADD COLUMN {name} {column_type}"))

        user_columns = columns("users")
        if "phone" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN phone VARCHAR(50)"))
        if "profile_image_name" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN profile_image_name VARCHAR(100)"))
        if "terms_accepted" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN terms_accepted BOOLEAN NOT NULL DEFAULT 0"))
        if "is_demo" not in user_columns:
            connection.execute(text("ALTER TABLE users ADD COLUMN is_demo BOOLEAN NOT NULL DEFAULT 0"))
        farmer_columns = columns("farmer_profiles")
        if farmer_columns and "main_products" not in farmer_columns:
            connection.execute(text("ALTER TABLE farmer_profiles ADD COLUMN main_products TEXT NOT NULL DEFAULT ''"))

        connection.execute(text("UPDATE products SET category = 'Fruits' WHERE lower(category) = 'fruit'"))
        connection.execute(text("UPDATE products SET category = 'Dairy Products' WHERE lower(category) = 'dairy'"))
        connection.execute(text("UPDATE products SET category = 'Homemade Products' WHERE lower(category) = 'pantry'"))
