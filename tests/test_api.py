import pytest
from io import BytesIO
from PIL import Image


def login(client, email, password):
    response = client.post("/auth/login", json={"email": email, "password": password})
    assert response.status_code == 200
    return response.json()


def auth_headers(token):
    return {"Authorization": f"Bearer {token}"}


def test_health_and_seed_accounts(client):
    assert client.get("/health").json() == {"status": "ok"}
    assert client.post("/auth/login", json={
        "email": "customer@pejamarket.local", "password": "Customer123!"
    }).status_code == 200
    assert client.post("/auth/login", json={
        "email": "farmer@pejamarket.local", "password": "Farmer123!"
    }).status_code == 200
    assert client.post("/auth/login", json={
        "email": "admin@pejamarket.local", "password": "Admin123!"
    }).status_code == 200


def test_registration_and_role_authorization(client):
    invalid_email = client.post("/auth/register", json={
        "name": "Invalid Email", "email": "not-an-email",
        "password": "Secret123", "role": "customer"
    })
    assert invalid_email.status_code == 422

    response = client.post("/auth/register", json={
        "name": "Test Buyer", "email": "buyer@gmail.com",
        "password": "Secret123", "role": "customer"
    })
    assert response.status_code == 201
    token = response.json()["access_token"]
    me = client.get("/auth/me", headers=auth_headers(token))
    assert me.status_code == 200
    assert me.json()["role"] == "customer"
    assert me.json()["email"] == "buyer@gmail.com"
    gmail_login = client.post("/auth/login", json={
        "email": "buyer@gmail.com", "password": "Secret123"
    })
    assert gmail_login.status_code == 200
    assert client.post("/products", headers=auth_headers(token), json={
        "name": "Forbidden", "category": "Test", "price": 1, "stock": 2
    }).status_code == 403


def test_product_order_stock_and_permissions(client):
    farmer = login(client, "farmer@pejamarket.local", "Farmer123!")
    product = client.post("/products", headers=auth_headers(farmer["access_token"]), json={
        "name": "Test Berries", "description": "Fresh berries", "category": "Fruit",
        "price": 4.25, "stock": 5
    })
    assert product.status_code == 201
    product_data = product.json()
    customer = login(client, "customer@pejamarket.local", "Customer123!")
    assert client.put(
        f"/cart/{product_data['id']}",
        headers=auth_headers(customer["access_token"]),
        json={"quantity": 1},
    ).status_code == 200
    order = client.post("/orders", headers=auth_headers(customer["access_token"]), json={
        "items": [{"product_id": product_data["id"], "quantity": 2}],
        "delivery_address": "1 Market Road"
    })
    assert order.status_code == 201
    assert order.json()["total"] == 8.5
    assert order.json()["is_demo"] is True
    order_id = order.json()["id"]
    assert client.get(
        f"/orders/{order_id}", headers=auth_headers(customer["access_token"])
    ).status_code == 200
    assert client.get(
        f"/orders/{order_id}", headers=auth_headers(farmer["access_token"])
    ).status_code == 200
    other_farmer = client.post("/auth/register", json={
        "name": "Other Farm",
        "email": "other.farm@gmail.com",
        "password": "OtherFarm123",
        "role": "farmer",
    })
    assert other_farmer.status_code == 201
    assert client.get(
        f"/orders/{order_id}",
        headers=auth_headers(other_farmer.json()["access_token"]),
    ).status_code == 403
    assert client.patch(
        f"/orders/{order_id}/status",
        headers=auth_headers(other_farmer.json()["access_token"]),
        json={"status": "confirmed"},
    ).status_code == 403
    assert client.get("/cart", headers=auth_headers(customer["access_token"])).json() == []
    customer_notifications = client.get("/notifications", headers=auth_headers(customer["access_token"]))
    farmer_notifications = client.get("/notifications", headers=auth_headers(farmer["access_token"]))
    assert any("Order" in notification["title"] for notification in customer_notifications.json())
    assert any("New order" in notification["title"] for notification in farmer_notifications.json())
    updated = client.get(f"/products/{product_data['id']}").json()
    assert updated["stock"] == 3
    status_response = client.patch(
        f"/orders/{order.json()['id']}/status",
        headers=auth_headers(farmer["access_token"]),
        json={"status": "confirmed"}
    )
    assert status_response.status_code == 200
    assert status_response.json()["status"] == "confirmed"
    rejected = client.patch(
        f"/orders/{order.json()['id']}/status",
        headers=auth_headers(farmer["access_token"]),
        json={"status": "rejected"},
    )
    assert rejected.status_code == 200
    assert client.get(f"/products/{product_data['id']}").json()["stock"] == 5


def test_mixed_farmer_checkout_is_private_and_fulfilled_independently(client):
    import uuid

    first_farmer = login(client, "farmer@pejamarket.local", "Farmer123!")
    second_farmer = client.post("/auth/register", json={
        "name": "Second Farm",
        "email": f"second-{uuid.uuid4().hex}@gmail.com",
        "password": "OtherFarm123",
        "role": "farmer",
    }).json()
    customer = login(client, "customer@pejamarket.local", "Customer123!")

    first_product = client.post("/products", headers=auth_headers(first_farmer["access_token"]), json={
        "name": "First Farm Apples", "category": "Fruit", "price": 2, "stock": 5,
    }).json()
    second_product = client.post(
        "/products",
        headers=auth_headers(second_farmer["access_token"]),
        json={"name": "Second Farm Pears", "category": "Fruit", "price": 3, "stock": 5},
    ).json()

    checkout = client.post("/orders", headers=auth_headers(customer["access_token"]), json={
        "items": [
            {"product_id": first_product["id"], "quantity": 2},
            {"product_id": second_product["id"], "quantity": 2},
        ],
        "delivery_address": "1 Market Road",
    })
    assert checkout.status_code == 201
    data = checkout.json()
    assert len(data["order_ids"]) == 2
    assert data["id"] == data["order_ids"][0]

    first_order_id, second_order_id = data["order_ids"]
    first_order = client.get(
        f"/orders/{first_order_id}", headers=auth_headers(first_farmer["access_token"])
    )
    second_order = client.get(
        f"/orders/{second_order_id}", headers=auth_headers(second_farmer["access_token"])
    )
    assert first_order.status_code == second_order.status_code == 200
    assert {item["product_id"] for item in first_order.json()["items"]} == {first_product["id"]}
    assert {item["product_id"] for item in second_order.json()["items"]} == {second_product["id"]}
    assert client.get(
        f"/orders/{second_order_id}", headers=auth_headers(first_farmer["access_token"])
    ).status_code == 403
    assert client.get(
        f"/orders/{first_order_id}", headers=auth_headers(second_farmer["access_token"])
    ).status_code == 403

    rejected = client.patch(
        f"/orders/{first_order_id}/status",
        headers=auth_headers(first_farmer["access_token"]),
        json={"status": "rejected"},
    )
    assert rejected.status_code == 200
    assert client.get(f"/products/{first_product['id']}").json()["stock"] == 5
    assert client.get(f"/products/{second_product['id']}").json()["stock"] == 3

    customer_orders = client.get("/orders", headers=auth_headers(customer["access_token"])).json()
    assert set(data["order_ids"]).issubset({order["id"] for order in customer_orders})


def test_insufficient_stock_and_ai_fallback(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    customer = login(client, "customer@pejamarket.local", "Customer123!")
    product_response = client.get("/products")
    product = product_response.json()[0]
    response = client.post("/orders", headers=auth_headers(customer["access_token"]), json={
        "items": [{"product_id": product["id"], "quantity": product["stock"] + 100}],
        "delivery_address": "1 Market Road"
    })
    assert response.status_code == 409
    ai = client.post("/ai/assistant", json={"message": "How should I grow tomatoes?"})
    assert ai.status_code == 200
    assert ai.json()["provider"] == "demo"
    description = client.post("/ai/product-description", json={
        "product_name": "Apples", "category": "Fruit",
    })
    assert description.status_code == 200
    assert description.json()["provider"] == "demo"
    assert description.json()["description"] == "Apples."
    assert "Peja" not in description.json()["description"]


def test_production_secret_requires_a_strong_configured_value():
    from app.auth import _resolve_secret_key

    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _resolve_secret_key("change-this-secret-key-in-production", "production")
    with pytest.raises(RuntimeError, match="SECRET_KEY"):
        _resolve_secret_key(None, "staging")
    assert _resolve_secret_key("a" * 48, "production") == "a" * 48


def test_cors_is_restricted_to_configured_frontend_origins(client):
    from app.main import _configured_cors_origins

    with pytest.raises(RuntimeError, match="explicit origins"):
        _configured_cors_origins("*")

    allowed = client.options("/auth/me", headers={
        "Origin": "http://localhost:8501",
        "Access-Control-Request-Method": "GET",
    })
    assert allowed.headers["access-control-allow-origin"] == "http://localhost:8501"
    assert "access-control-allow-credentials" not in allowed.headers

    denied = client.options("/auth/me", headers={
        "Origin": "https://untrusted.example",
        "Access-Control-Request-Method": "GET",
    })
    assert "access-control-allow-origin" not in denied.headers


def test_ai_provider_failures_are_logged_and_use_demo_fallback(client, monkeypatch, caplog):
    import logging
    import sys
    from types import ModuleType

    anthropic = ModuleType("anthropic")

    class FailingMessages:
        def create(self, **kwargs):
            raise RuntimeError("Provider unavailable")

    class FailingAnthropic:
        def __init__(self, **kwargs):
            self.messages = FailingMessages()

    setattr(anthropic, "Anthropic", FailingAnthropic)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-key")
    monkeypatch.setitem(sys.modules, "anthropic", anthropic)

    with caplog.at_level(logging.WARNING, logger="app.routers.ai"):
        assistant = client.post("/ai/assistant", json={"message": "Help with tomatoes"})
        description = client.post(
            "/ai/product-description",
            json={"product_name": "Apples", "category": "Fruit"},
        )

    assert assistant.status_code == 200
    assert assistant.json()["provider"] == "demo"
    assert description.status_code == 200
    assert description.json()["provider"] == "demo"
    assert caplog.text.count("request failed (RuntimeError)") == 2


def test_admin_analytics(client):
    admin = login(client, "admin@pejamarket.local", "Admin123!")
    response = client.get("/analytics/overview", headers=auth_headers(admin["access_token"]))
    assert response.status_code == 200
    assert set(response.json()) == {"users", "products", "orders", "revenue"}


def test_favorites_are_private_and_persistent(client):
    customer = login(client, "customer@pejamarket.local", "Customer123!")
    second_customer = client.post("/auth/register", json={
        "name": "Second Buyer", "email": "second.buyer@gmail.com",
        "password": "Secret123", "role": "customer"
    }).json()
    product = client.get("/products").json()[0]

    add = client.post(f"/favorites/{product['id']}", headers=auth_headers(customer["access_token"]))
    assert add.status_code == 201
    own = client.get("/favorites", headers=auth_headers(customer["access_token"]))
    assert [item["id"] for item in own.json()] == [product["id"]]
    other = client.get("/favorites", headers=auth_headers(second_customer["access_token"]))
    assert other.json() == []
    assert client.delete(
        f"/favorites/{product['id']}", headers=auth_headers(customer["access_token"])
    ).status_code == 204


def test_farmer_profile_and_notifications(client):
    farmer_response = client.post("/auth/register", json={
        "name": "Farm Owner",
        "email": "farm.owner@gmail.com",
        "password": "FarmPass123",
        "role": "farmer",
        "phone": "+38344123456",
        "farm_name": "Hilltop Produce",
        "village": "Rugova",
        "farm_description": "A small demonstration farm.",
        "main_products": "Apples, herbs",
    })
    assert farmer_response.status_code == 201
    token = farmer_response.json()["access_token"]
    profile = client.get("/auth/profile", headers=auth_headers(token)).json()
    assert profile["farm_name"] == "Hilltop Produce"
    assert profile["main_products"] == "Apples, herbs"

    updated = client.put("/auth/profile", headers=auth_headers(token), json={
        "name": "Farm Owner",
        "phone": "+38344999999",
        "farm_name": "Hilltop Farm",
        "village": "Rugova",
        "farm_description": "Updated farm information",
        "main_products": "Apples",
    })
    assert updated.status_code == 200
    assert updated.json()["phone"] == "+38344999999"
    assert client.get("/notifications", headers=auth_headers(token)).status_code == 200


def test_marketplace_search_filters_and_farmer_discovery(client):
    search = client.get("/products", params={"search": "Rugova", "sort": "alphabetical"})
    assert search.status_code == 200
    assert search.json()
    farmers = client.get("/farmers")
    assert farmers.status_code == 200
    assert farmers.json()
    assert farmers.json()[0]["product_count"] >= 0
    farmer_summary = farmers.json()[0]
    farmer_id = farmer_summary["id"]
    assert client.get(f"/farmers/{farmer_id}").json() == farmer_summary
    assert client.get(f"/farmers/{farmer_id}/products").status_code == 200
    assert client.get("/farmers", params={"search": "Farm", "village": "Rugova"}).status_code == 200


def test_cart_persists_and_enforces_stock(client):
    customer = login(client, "customer@pejamarket.local", "Customer123!")
    headers = auth_headers(customer["access_token"])
    product = client.get("/products").json()[0]

    saved = client.put(
        f"/cart/{product['id']}", headers=headers,
        json={"quantity": 2},
    )
    assert saved.status_code == 200
    cart = client.get("/cart", headers=headers)
    assert cart.status_code == 200
    assert any(row["product"]["id"] == product["id"] and row["quantity"] == 2 for row in cart.json())
    too_many = client.put(
        f"/cart/{product['id']}", headers=headers,
        json={"quantity": product["stock"] + 1},
    )
    assert too_many.status_code == 409
    assert client.delete("/cart", headers=headers).status_code == 204
    assert client.get("/cart", headers=headers).json() == []


def test_farmer_can_upload_product_image(client, monkeypatch, tmp_path):
    from app.routers import products as products_router

    monkeypatch.setattr(products_router, "UPLOAD_DIRECTORY", tmp_path)
    farmer = login(client, "farmer@pejamarket.local", "Farmer123!")
    headers = auth_headers(farmer["access_token"])
    product = client.post("/products", headers=headers, json={
        "name": "Image Test Produce",
        "category": "Other",
        "price": 1.5,
        "stock": 3,
    })
    assert product.status_code == 201
    image = BytesIO()
    Image.new("RGB", (4, 4), color="green").save(image, format="PNG")
    uploaded = client.post(
        f"/products/{product.json()['id']}/image",
        headers=headers,
        files={"image": ("produce.png", image.getvalue(), "image/png")},
    )
    assert uploaded.status_code == 200
    assert uploaded.json()["image_url"].startswith("/uploads/")
    assert list(tmp_path.iterdir())


def test_profile_pictures_are_private_persistent_and_role_scoped(client, monkeypatch, tmp_path):
    from app.routers import auth as auth_router

    private_directory = tmp_path / "private" / "profile_pictures"
    monkeypatch.setattr(auth_router, "PROFILE_IMAGE_DIRECTORY", private_directory)
    accounts = [
        ("customer", "customer@pejamarket.local", "Customer123!", "PNG", "image/png"),
        ("farmer", "farmer@pejamarket.local", "Farmer123!", "JPEG", "image/jpeg"),
        ("admin", "admin@pejamarket.local", "Admin123!", "WEBP", "image/webp"),
    ]
    headers_by_role = {}
    pictures_by_role = {}

    for index, (role, email, password, image_format, content_type) in enumerate(accounts):
        signed_in = login(client, email, password)
        headers = auth_headers(signed_in["access_token"])
        headers_by_role[role] = headers
        assert client.get("/auth/profile", headers=headers).json()["has_profile_picture"] is False
        assert client.get("/auth/profile-picture", headers=headers).status_code == 404

        image = BytesIO()
        image_mode = "RGBA" if image_format == "PNG" else "RGB"
        image_color = (30 + index * 50, 90, 45, 128) if image_mode == "RGBA" else (30 + index * 50, 90, 45)
        Image.new(image_mode, (900, 600), color=image_color).save(image, format=image_format)
        uploaded = client.post(
            "/auth/profile-picture",
            headers=headers,
            files={"image": (f"profile.{image_format.lower()}", image.getvalue(), content_type)},
        )
        assert uploaded.status_code == 200
        assert uploaded.json() == {"has_profile_picture": True}
        assert client.get("/auth/profile", headers=headers).json()["has_profile_picture"] is True

        picture = client.get("/auth/profile-picture", headers=headers)
        assert picture.status_code == 200
        assert picture.headers["content-type"] == "image/webp"
        assert picture.headers["cache-control"] == "private, no-store"
        decoded = Image.open(BytesIO(picture.content))
        assert decoded.format == "WEBP"
        assert decoded.width <= 512 and decoded.height <= 512
        if image_mode == "RGBA":
            assert decoded.mode == "RGBA"
        pictures_by_role[role] = picture.content

        signed_in_again = login(client, email, password)
        refreshed_picture = client.get(
            "/auth/profile-picture",
            headers=auth_headers(signed_in_again["access_token"]),
        )
        assert refreshed_picture.content == picture.content

    original_customer_picture = pictures_by_role["customer"]
    replacement_image = BytesIO()
    Image.new("RGB", (180, 180), color="purple").save(replacement_image, format="PNG")
    replacement = client.post(
        "/auth/profile-picture",
        headers=headers_by_role["customer"],
        files={"image": ("replacement.png", replacement_image.getvalue(), "image/png")},
    )
    assert replacement.status_code == 200
    pictures_by_role["customer"] = client.get(
        "/auth/profile-picture", headers=headers_by_role["customer"]
    ).content
    assert pictures_by_role["customer"] != original_customer_picture
    assert len(list(private_directory.glob("*.webp"))) == 3
    customer_signed_in_again = login(client, "customer@pejamarket.local", "Customer123!")
    assert client.get(
        "/auth/profile-picture",
        headers=auth_headers(customer_signed_in_again["access_token"]),
    ).content == pictures_by_role["customer"]

    assert pictures_by_role["customer"] != pictures_by_role["farmer"]
    assert pictures_by_role["farmer"] != pictures_by_role["admin"]
    assert client.get(
        "/auth/profile-picture", headers=headers_by_role["farmer"]
    ).content == pictures_by_role["farmer"]
    assert client.get(
        "/auth/profile-picture", headers=headers_by_role["customer"]
    ).content == pictures_by_role["customer"]

    admin_picture_before = client.get(
        "/auth/profile-picture", headers=headers_by_role["admin"]
    ).content
    admin = client.get("/auth/profile", headers=headers_by_role["admin"]).json()
    assert client.post(
        f"/auth/users/{admin['id']}/profile-picture",
        headers=headers_by_role["customer"],
        files={"image": ("other.png", pictures_by_role["customer"], "image/webp")},
    ).status_code == 404
    assert client.get(
        "/auth/profile-picture", headers=headers_by_role["admin"]
    ).content == admin_picture_before

    stored_names = [path.name for path in private_directory.iterdir()]
    assert len(stored_names) == 3
    assert all(client.get(f"/uploads/{name}").status_code == 404 for name in stored_names)
    assert client.get("/auth/profile-picture").status_code == 403

    removed = client.delete("/auth/profile-picture", headers=headers_by_role["customer"])
    assert removed.status_code == 204
    assert client.get(
        "/auth/profile-picture", headers=headers_by_role["customer"]
    ).status_code == 404
    assert client.get("/auth/profile", headers=headers_by_role["customer"]).json()["has_profile_picture"] is False
    assert len(list(private_directory.glob("*.webp"))) == 2
    assert client.get(
        "/auth/profile-picture", headers=headers_by_role["farmer"]
    ).content == pictures_by_role["farmer"]


def test_profile_picture_upload_validates_type_size_and_image_content(client, monkeypatch, tmp_path):
    from app.routers import auth as auth_router

    monkeypatch.setattr(auth_router, "PROFILE_IMAGE_DIRECTORY", tmp_path / "private" / "profiles")
    customer = login(client, "customer@pejamarket.local", "Customer123!")
    headers = auth_headers(customer["access_token"])

    unsupported_type = client.post(
        "/auth/profile-picture",
        headers=headers,
        files={"image": ("photo.gif", b"GIF89a", "image/gif")},
    )
    assert unsupported_type.status_code == 415

    invalid_image = client.post(
        "/auth/profile-picture",
        headers=headers,
        files={"image": ("photo.png", b"not a PNG", "image/png")},
    )
    assert invalid_image.status_code == 415

    oversized = client.post(
        "/auth/profile-picture",
        headers=headers,
        files={"image": ("photo.png", b"x" * (5 * 1024 * 1024 + 1), "image/png")},
    )
    assert oversized.status_code == 413


def test_researched_records_require_admin_approval_and_keep_sources(client):
    customer = login(client, "customer@pejamarket.local", "Customer123!")
    assert client.get(
        "/research/admin/summary",
        headers=auth_headers(customer["access_token"]),
    ).status_code == 403
    assert client.get("/research/public").json() == []

    public_images = client.get("/research/images/public")
    assert public_images.status_code == 200
    image_slugs = {image["slug"] for image in public_images.json()}
    assert {"rugova-canyon", "boge-rugova", "kipper-peja", "generic-apples"} <= image_slugs
    assert client.get("/research/images/rugova-canyon/file").status_code == 200
    assert client.get("/research/images/generic-apples/file").status_code == 200
    admin_headers = auth_headers(login(client, "admin@pejamarket.local", "Admin123!")["access_token"])
    image_rows = client.get("/research/admin/images", headers=admin_headers).json()
    apple_image = next(row for row in image_rows if row["slug"] == "generic-apples")
    rugova_image = next(row for row in image_rows if row["slug"] == "rugova-canyon")
    original_source_url = rugova_image["source"]["url"]
    updated_source_url = "https://commons.wikimedia.org/wiki/File/Rugova_Canyon_test.jpg"
    source_update = client.patch(
        f"/research/admin/sources/{rugova_image['source']['id']}",
        headers=admin_headers,
        json={"url": updated_source_url},
    )
    assert source_update.status_code == 200
    updated_rugova = next(
        row for row in client.get("/research/admin/images", headers=admin_headers).json()
        if row["slug"] == "rugova-canyon"
    )
    assert updated_rugova["source_page"] == updated_source_url
    assert client.patch(
        f"/research/admin/sources/{rugova_image['source']['id']}",
        headers=admin_headers,
        json={"url": original_source_url},
    ).status_code == 200

    hidden_image = client.patch(
        f"/research/admin/images/{apple_image['id']}",
        headers=admin_headers,
        json={"usage_rights_confirmed": False, "display_publicly": False},
    )
    assert hidden_image.status_code == 200
    assert client.get("/research/images/generic-apples/file").status_code == 404
    assert client.patch(
        f"/research/admin/images/{apple_image['id']}",
        headers=admin_headers,
        json={"usage_rights_confirmed": True, "display_publicly": True},
    ).status_code == 200

    admin = login(client, "admin@pejamarket.local", "Admin123!")
    headers = auth_headers(admin["access_token"])
    summary = client.get("/research/admin/summary", headers=headers)
    assert summary.status_code == 200
    assert summary.json()["total_researched_businesses"] == 0
    assert summary.json()["records_requiring_review"] >= 10
    records = client.get("/research/admin/records", headers=headers).json()
    venue = next(row for row in records if row["slug"] == "restaurant-bjeshka-municipal-listing")
    assert venue["metadata"]["is_farmer"] is False
    assert venue["publication_status"] == "pending"
    assert venue["source"]["url"].startswith("https://peja.rks-gov.net/")

    approved = client.patch(
        f"/research/admin/records/{venue['id']}",
        headers=headers,
        json={
            "publication_status": "approved",
            "public_listing_permission": True,
        },
    )
    assert approved.status_code == 200
    public = client.get("/research/public").json()
    assert any(row["slug"] == venue["slug"] for row in public)

    hidden = client.patch(
        f"/research/admin/records/{venue['id']}",
        headers=headers,
        json={"public_listing_permission": False},
    )
    assert hidden.status_code == 200
    assert all(row["slug"] != venue["slug"] for row in client.get("/research/public").json())


def test_research_import_is_idempotent(client, db):
    from app.models import LocalResearchRecord, ResearchImage, ResearchSource
    from app.research_data import import_research_data

    client.get("/health")
    before = (
        db.query(LocalResearchRecord).count(),
        db.query(ResearchImage).count(),
        db.query(ResearchSource).count(),
    )
    import_research_data(db)
    import_research_data(db)
    after = (
        db.query(LocalResearchRecord).count(),
        db.query(ResearchImage).count(),
        db.query(ResearchSource).count(),
    )
    assert after == before


def test_seed_accounts_and_market_data_are_explicitly_demo(client):
    customer = login(client, "customer@pejamarket.local", "Customer123!")
    me = client.get("/auth/me", headers=auth_headers(customer["access_token"]))
    assert me.json()["is_demo"] is True
    products = client.get("/products", params={"available": "true"}).json()
    demo_product = next(
        product for product in products
        if product["is_demo"] and product["image_is_generic"]
    )
    assert demo_product["image_is_generic"] is True
    assert demo_product["image_source_url"].startswith("https://commons.wikimedia.org/")

    by_name = {product["name"]: product for product in products}
    expected_photos = {
        "Vine Tomatoes": "generic-tomatoes",
        "Baby Spinach": "generic-spinach",
        "Red Apples": "generic-apples",
        "Sweet Peppers": "generic-peppers",
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
    for product_name, image_slug in expected_photos.items():
        product = by_name[product_name]
        assert product["image_url"] == f"/research/images/{image_slug}/file"
        assert product["image_is_generic"] is True
        assert client.get(f"/research/images/{image_slug}/file").status_code == 200
    for product_name in ("Strawberries", "Fresh Cow Milk", "Green Beans"):
        assert by_name[product_name]["image_url"] is None

    admin = login(client, "admin@pejamarket.local", "Admin123!")
    totals = client.get(
        "/analytics/overview",
        headers=auth_headers(admin["access_token"]),
    ).json()
    assert totals["orders"] == 0
    assert totals["revenue"] == 0


def test_seed_backfills_legacy_demo_image_paths(client, db):
    from app.models import Product, User
    from app.seed import seed

    farmer = db.query(User).filter_by(email="farmer@pejamarket.local").one()
    legacy_product = Product(
        name="Honey Jar",
        category="Homemade Products",
        price=8.5,
        stock=2,
        unit="package",
        farmer_id=farmer.id,
        image_url="/products/honey.jpg",
        is_demo=True,
    )
    db.add(legacy_product)
    db.commit()
    seed(db)
    db.refresh(legacy_product)

    assert legacy_product.image_url == "/research/images/generic-honey/file"
    assert legacy_product.image_source_url == (
        "https://commons.wikimedia.org/wiki/File:Three_French_monofloral_honey_jars.jpg"
    )
    assert legacy_product.image_is_generic is True
