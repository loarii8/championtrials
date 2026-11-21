# PejaMarket

PejaMarket is a local MVP for an agricultural marketplace. It includes a FastAPI REST API, a Streamlit web frontend, SQLite/SQLAlchemy persistence, JWT authentication, role-based dashboards, inventory transactions, orders, analytics, and an Anthropic assistant with an automatic demo fallback.

## Features

- Customer registration and sign-in
- Registration and sign-in with any valid email address (accounts are stored locally; no verification email is sent)
- Farmer and admin role authorization
- Product browsing, product/farmer/village search, category/unit/location/price filters, sorting, and pagination
- Product details, farmer discovery, favorites, and farmer-managed product photo uploads
- Database-persisted customer cart and transactional order creation
- Stock decrements and stock-change history
- Customer, farmer, and admin dashboards
- Role-scoped sidebar navigation with compact icon mode and responsive drawer behavior
- Private profile-picture uploads for customer, farmer, and administrator accounts
- Account profiles, password changes, and event-based in-app notifications
- Order status updates
- Admin and farmer analytics
- Source-linked Peja regional research with an administrator review/publish workflow
- Licensed local landscape imagery and separately labeled generic product photographs
- Clear separation between registered accounts, researched public records, and fictional demo data
- Anthropic API integration or built-in demo responses
- Seed users and produce
- Separate test database

Direct customer/farmer messaging and a farmer-verification approval workflow are not
implemented in this MVP. Their navigation pages explain the current alternatives and
limitations without implying that those workflows are available.

## Demo accounts

| Role | Email | Password |
|---|---|---|
| Admin | `admin@pejamarket.local` | `Admin123!` |
| Farmer | `farmer@pejamarket.local` | `Farmer123!` |
| Customer | `customer@pejamarket.local` | `Customer123!` |

## Windows setup (PowerShell)

From the project directory:

```powershell
py -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
Copy-Item .env.example .env
```

Start the backend:

```powershell
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

Open a second PowerShell window, activate the environment, and start Streamlit:

```powershell
cd C:\path\to\championtrials
.venv\Scripts\Activate.ps1
streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8501
```

Open `http://127.0.0.1:8501`. API documentation is at `http://127.0.0.1:8000/docs`.

## Windows Command Prompt setup (cmd.exe)

```bat
py -m venv .venv
.venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another Command Prompt:

```bat
cd C:\path\to\championtrials
.venv\Scripts\activate.bat
streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8501
```

## Linux/macOS setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

In another terminal:

```bash
source .venv/bin/activate
streamlit run frontend/app.py --server.address 127.0.0.1 --server.port 8501
```

## Configuration

Create `.env` from `.env.example`. `DATABASE_URL` controls the application SQLite database. Set `ANTHROPIC_API_KEY` to enable Anthropic; without it (or if the API call fails), the AI assistant returns a demo response based only on the supplied product details.

Set a unique `SECRET_KEY` of at least 32 characters for stable sessions across application restarts. For example, generate one with `python -c "import secrets; print(secrets.token_urlsafe(48))"`. Local development generates a temporary random key when this is unset, which invalidates sessions on restart. Production and staging require an explicitly configured key; set `APP_ENV=production` or `APP_ENV=staging` to enable that check. Set `CORS_ALLOWED_ORIGINS` to a comma-separated list of exact frontend origins; it defaults to the local Streamlit addresses and does not allow credentialed or wildcard requests.

Checkout creates a separate order for each farmer represented in the cart. This keeps order details, status changes, and stock restoration scoped to the seller while allowing customers to check out items from multiple farms together. The checkout response includes all generated order IDs.

Set `BACKEND_URL` if the API runs elsewhere. It defaults to `http://127.0.0.1:8000`.

Product image uploads are validated (JPEG, PNG, or WebP, up to 5 MB) and stored locally in the ignored `uploads/` directory. They are served by FastAPI and are not committed to source control. Profile pictures accept the same formats and size limit, are resized and optimized as WebP, and are stored separately in `private_uploads/`; access is limited to the signed-in account and files are not publicly served.

The MVP validates email address syntax but does not send verification or password-reset emails. Password changes are available from the signed-in profile page. Do not use the demonstration deployment as a production identity or email service.

## Peja research data and photography

- Research methodology and limitations: [research/peja_agriculture_research.md](research/peja_agriculture_research.md)
- Structured sources, records, product references, and imagery: `research/*.json`
- Downloaded, optimized photos: `assets/local/` and `assets/products/`
- Local photographs depict Rugova scenery or Peja retail, not farms or agricultural products.
- Product photographs are matched generic illustrations, including a Bulgarian yogurt photo for the Natural Yogurt demo listing; they are not photos of Peja produce or a seller's inventory. Image credits, source pages, and reuse licenses appear beside product images and are tracked in the database. Listings without a suitable image show a category-specific fallback.
- Product-origin claims, current farmer identities, and current local prices are not inferred from regional context. No named Peja farmer or farm was verified in this research; no researched product has an imported price.
- Research data is imported idempotently at startup into source-linked database records. New research records remain unpublished until an administrator approves them and enables public display in **Local Data & Research**. Images are served only when rights are recorded as confirmed and public display is enabled.
- Existing seeded demo accounts, listings, orders, stock, and prices are flagged as fictional. Demo inventory is kept out of platform analytics; demo orders and demo prices are labeled in the UI. New user-created accounts and listings remain separate from researched records.
- SQLite migration adds profile-picture metadata and provenance/demo-status fields without dropping existing tables or rows.

For tests, `TEST_DATABASE_URL` defaults to `sqlite:///./test_pejamarket.db` in `tests/conftest.py`. This keeps test data separate from `pejamarket.db`.

## Tests

From the project directory with dependencies installed:

```bash
pytest -q
```

On Windows PowerShell:

```powershell
pytest -q
```
