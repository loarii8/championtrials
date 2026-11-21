import base64
import json
import os
import re
from datetime import date, timedelta
from html import escape

import pandas as pd
import plotly.express as px
import requests
import streamlit as st


API = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")
CATEGORIES = ["Vegetables", "Fruits", "Grains", "Dairy Products", "Homemade Products", "Other"]

st.set_page_config(
    page_title="PejaMarket",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@700;800&display=swap');
    :root { color-scheme:light; --forest:#173f2a; --green:#2f6644; --cream:#f7f5ed; --line:#e6e2d5; --ink:#202820; }
    html, body, [class*="css"] { font-family:'DM Sans',sans-serif; color:var(--ink); }
    .stApp, [data-testid="stAppViewContainer"] { background:var(--cream); color:var(--ink); }
    .block-container { max-width:1280px; padding:1.35rem 1.75rem 2.2rem; }
    [data-testid="stVerticalBlock"] { gap:.75rem; }
    header[data-testid="stHeader"] { background:transparent; pointer-events:none!important; }
    header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"],
    header[data-testid="stHeader"] [data-testid="stSidebarCollapsedControl"] button {
      pointer-events:auto;
    }
    [data-testid="stToolbar"] { visibility:hidden; height:0; }
    [data-testid="stDecoration"] { display:none; }
    section[data-testid="stSidebar"] { background:var(--forest); border-right:0; }
    section[data-testid="stSidebar"] * { color:#fdfcf7 !important; }
    section[data-testid="stSidebar"] .stButton button { background:#f4f1e6; color:var(--forest)!important; border:0; }
    section[data-testid="stSidebar"] [class*="st-key-sidebar_nav_btn_"] button {
      background:transparent!important; color:#fdfcf7!important;
      border:1px solid transparent!important; border-left:3px solid transparent!important;
      border-radius:8px; justify-content:flex-start; text-align:left;
      min-height:40px; padding:.35rem .65rem; font-size:.88rem; font-weight:500;
      transition:background .16s ease, border-color .16s ease;
    }
    section[data-testid="stSidebar"] [class*="st-key-sidebar_nav_btn_"] button:hover {
      background:rgba(255,255,255,.08)!important;
    }
    section[data-testid="stSidebar"] [class*="st-key-sidebar_nav_btn_"] button * {
      color:#fdfcf7!important;
    }
    section[data-testid="stSidebar"] [class*="st-key-toggle_sidebar_"] button,
    section[data-testid="stSidebar"] [class*="st-key-sign_out_"] button {
      background:#f4f1e6!important; color:var(--forest)!important;
    }
    section[data-testid="stSidebar"] [class*="st-key-toggle_sidebar_"] button *,
    section[data-testid="stSidebar"] [class*="st-key-sign_out_"] button * {
      color:var(--forest)!important;
    }
    section[data-testid="stSidebar"] [class*="st-key-toggle_sidebar_"] button [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [class*="st-key-sign_out_"] button [data-testid="stMarkdownContainer"] p {
      color:var(--forest)!important;
    }
    section[data-testid="stSidebar"] [data-testid="stSidebarContent"] {
      height:100vh; overflow-y:auto;
    }
    [data-testid="stSidebarCollapsedControl"] {
      visibility:visible!important; opacity:1!important; z-index:10001!important;
    }
    [data-testid="stSidebarCollapsedControl"] button {
      width:42px; height:42px; border-radius:9px;
      color:var(--forest)!important; background:#f4f1e6!important;
      box-shadow:0 2px 8px rgba(0,0,0,.14);
    }
    [data-testid="stSidebarCollapsedControl"] button svg { color:var(--forest)!important; }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"],
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
    section[data-testid="stSidebar"] button,
    section[data-testid="stSidebar"] button *,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] span {
      color:#fdfcf7!important;
    }
    section[data-testid="stSidebar"] h1,
    section[data-testid="stSidebar"] h2,
    section[data-testid="stSidebar"] h3 {
      color:#fdfcf7!important;
    }
    section[data-testid="stSidebar"] .demo-badge {
      color:#61431c!important;
    }
    section[data-testid="stSidebar"] .sidebar-section-heading {
      margin:.85rem 0 .3rem; padding-left:.55rem; opacity:.62;
      font-size:.68rem; font-weight:700; letter-spacing:.09em;
    }
    .profile-avatar-fallback {
      display:flex; align-items:center; justify-content:center; flex:0 0 auto;
      width:48px; height:48px; border-radius:50%;
      color:#fdfcf7; background:#52745b; border:1px solid rgba(255,255,255,.28);
      font-size:.9rem; font-weight:700; letter-spacing:.04em;
    }
    .profile-avatar-fallback.sidebar-avatar { width:46px; height:46px; }
    .profile-avatar-fallback.profile-avatar-large {
      width:112px; height:112px; color:#31583c; background:#e9eee5;
      border:1px solid #d6e0d1; font-size:1.55rem;
    }
    .profile-avatar-picture {
      display:block; width:112px; height:112px; border-radius:50%;
      object-fit:cover; border:1px solid #d6e0d1;
    }
    .profile-avatar-picture.sidebar-avatar {
      width:46px; height:46px; border-color:rgba(255,255,255,.28);
    }
    section[data-testid="stSidebar"] .pejamarket-compact-sidebar {
      display:none;
    }
    section[data-testid="stSidebar"]:has(.pejamarket-compact-sidebar) {
      width:5.25rem!important; min-width:5.25rem!important; max-width:5.25rem!important;
    }
    section[data-testid="stSidebar"]:has(.pejamarket-compact-sidebar) [data-testid="stSidebarContent"] {
      padding-left:.45rem; padding-right:.45rem;
    }
    section[data-testid="stSidebar"]:has(.pejamarket-compact-sidebar) .stButton button {
      width:100%!important; min-width:48px; justify-content:center;
      padding-left:.25rem; padding-right:.25rem;
    }
    section[data-testid="stSidebar"]:has(.pejamarket-compact-sidebar) .stButton {
      width:100%!important;
    }
    section[data-testid="stSidebar"]:has(.pejamarket-compact-sidebar) [data-testid="stMarkdownContainer"] {
      text-align:center;
    }
    h1,h2,h3 { font-family:'Manrope',sans-serif!important; letter-spacing:-0.03em; }
    h1 { color:var(--forest); }
    div[data-testid="stMetric"], [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stImage"]):not(:has([data-testid="stVerticalBlockBorderWrapper"])) {
      background:#fff; border:1px solid var(--line); border-radius:16px;
      box-shadow:0 6px 20px rgba(38,66,47,.055);
    }
    div[data-testid="stMetric"] { padding:16px; }
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stImage"]):not(:has([data-testid="stVerticalBlockBorderWrapper"])) {
      padding:10px; min-height:335px;
    }
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stImage"]):not(:has([data-testid="stVerticalBlockBorderWrapper"])) [data-testid="stVerticalBlock"] {
      background:#fff;
    }
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"],
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h1,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h2,
    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] h3,
    [data-testid="stAppViewContainer"] label,
    [data-testid="stAppViewContainer"] [data-testid="stCaptionContainer"] {
      color:var(--ink)!important;
    }
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] h2,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
    section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] strong,
    section[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p {
      color:#fdfcf7!important;
    }
    [data-testid="stImage"] img {
      width:100%; height:180px; object-fit:cover; border-radius:12px;
      background:#e9eee5;
    }
    [data-testid="stImage"] { overflow:hidden; }
    [data-testid="stTabs"] button { font-weight:600; }
    [data-testid="stAppViewContainer"] input,
    [data-testid="stAppViewContainer"] textarea,
    [data-testid="stAppViewContainer"] [data-baseweb="select"] > div {
      color:#202820!important; background:#fff!important; border-color:#d6ddcf!important;
      border-radius:9px!important;
    }
    .stButton button, .stDownloadButton button {
      border-radius:9px; border:1px solid var(--green); background:var(--green);
      color:white!important; font-weight:700; min-height:42px;
    }
    .stButton button:hover { background:#245136; border-color:#245136; }
    .stButton button *, .stDownloadButton button * { color:#fff!important; }
    .stButton [data-testid="stMarkdownContainer"],
    .stButton [data-testid="stMarkdownContainer"] * { color:#fff!important; }
    [data-testid="stAppViewContainer"] .stButton [data-testid="stMarkdownContainer"] p {
      color:#fff!important;
    }
    .hero {
      background:#173f2a;
      color:white; border-radius:18px; padding:30px 34px; margin-bottom:20px;
      box-shadow:0 10px 24px rgba(23,63,42,.12);
    }
    .hero h1 { color:white!important; margin:0 0 8px 0; }
    .hero p { color:#e8efe8!important; font-size:1.02rem; max-width:650px; margin-bottom:0; }
    [data-testid="stAppViewContainer"] .hero h1 { color:#fff!important; }
    [data-testid="stAppViewContainer"] .hero p { color:#e8efe8!important; }
    .product-price { color:var(--forest); font-size:1.3rem; font-weight:800; }
    .product-meta { color:#667066; font-size:.88rem; }
    .status { display:inline-block; border-radius:999px; padding:5px 10px; font-size:.78rem; font-weight:700; background:#eef3e9; color:#31583c; }
    .image-fallback {
      height:180px; background:linear-gradient(135deg,#edf2e8,#e3ebdf);
      border:1px solid #d6e0d1; border-radius:12px; display:flex;
      flex-direction:column; align-items:center; justify-content:center; gap:6px;
      color:#31583c; text-align:center;
    }
    .image-fallback-icon { font-size:2.4rem; line-height:1; }
    .image-fallback-title { font-weight:700; font-size:.95rem; }
    .image-fallback-note { color:#667066; font-size:.76rem; }
    [class*="st-key-product-photo-small-"] [data-testid="stImage"] img,
    [class*="st-key-product-photo-small-"] .image-fallback { height:110px; }
    [class*="st-key-product-photo-medium-"] [data-testid="stImage"] img,
    [class*="st-key-product-photo-medium-"] .image-fallback { height:140px; }
    [class*="st-key-product-photo-large-"] [data-testid="stImage"] img,
    [class*="st-key-product-photo-large-"] .image-fallback { height:240px; }
    .small-muted { color:#737d73; font-size:.85rem; }
    .auth-local-hero, .market-local-hero {
      position:relative; display:flex; align-items:flex-end; overflow:hidden;
      border-radius:20px; background-size:cover; background-position:center;
      box-shadow:0 12px 30px rgba(23,63,42,.16); color:#fff;
    }
    .auth-local-hero { min-height:310px; margin-bottom:16px; }
    .market-local-hero { min-height:260px; margin:4px 0 20px; }
    .local-hero-copy {
      width:100%; padding:28px 30px;
      background:linear-gradient(0deg,rgba(13,37,24,.88),rgba(13,37,24,0));
    }
    .local-hero-copy h2 { color:#fff!important; margin:0 0 7px; }
    .local-hero-copy p { color:#f4f4eb!important; margin:0; max-width:700px; }
    .photo-credit { color:#626d62; font-size:.76rem; margin-top:-.35rem; }
    .demo-badge {
      display:inline-block; border-radius:999px; padding:3px 9px;
      color:#61431c; background:#fff0d3; border:1px solid #e8c98e;
      font-size:.72rem; font-weight:700; letter-spacing:.02em;
    }
    .research-card {
      background:#fff; border:1px solid var(--line); border-radius:16px;
      padding:18px; height:100%; box-shadow:0 5px 18px rgba(38,66,47,.045);
    }
    .research-card h3 { margin-top:.4rem; }
    .stImage img { transition:transform .28s ease, box-shadow .28s ease; }
    [data-testid="stVerticalBlockBorderWrapper"]:has([data-testid="stImage"]):hover img {
      transform:scale(1.025); box-shadow:0 10px 24px rgba(23,63,42,.12);
    }
    .st-key-local-photo-boge-rugova [data-testid="stImage"] img {
      height:240px; object-fit:cover; object-position:center 50%; background:#e9eee5;
    }
    @media (max-width: 760px) {
      .block-container { padding:.9rem .8rem 1.5rem; }
      [data-testid="stVerticalBlock"] { gap:.6rem; }
      .hero { padding:24px 20px; }
      .auth-local-hero { min-height:240px; }
      .market-local-hero { min-height:210px; }
      .local-hero-copy { padding:22px 18px; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

if "token" not in st.session_state:
    st.session_state.token = None
    st.session_state.user = None
    st.session_state.cart = {}
    st.session_state.recent = []
    st.session_state.ai_history = {"customer": [], "farmer": []}
st.session_state.setdefault("ai_history", {"customer": [], "farmer": []})
st.session_state.setdefault("recent", [])


def headers():
    if st.session_state.token:
        return {"Authorization": "Bearer " + st.session_state.token}
    return {}


def api(method, path, **kwargs):
    try:
        response = requests.request(method, API + path, headers=headers(), timeout=12, **kwargs)
        if response.status_code >= 400:
            try:
                message = response.json().get("detail", response.text)
            except requests.JSONDecodeError:
                message = response.text
            st.error(str(message))
            return None
        if response.status_code == 204:
            return {}
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Cannot reach the PejaMarket server at {API}. {exc}")
        return None


def profile_picture_bytes():
    try:
        response = requests.get(API + "/auth/profile-picture", headers=headers(), timeout=12)
        if response.status_code == 404:
            return None
        if response.status_code >= 400:
            try:
                message = response.json().get("detail", response.text)
            except requests.JSONDecodeError:
                message = response.text
            st.error(str(message))
            return None
        return response.content
    except requests.RequestException as exc:
        st.error(f"Cannot reach the PejaMarket server at {API}. {exc}")
        return None


def profile_avatar_markup(image_bytes, name, size, content_type="image/webp"):
    size_class = "sidebar-avatar" if size <= 46 else "profile-avatar-large"
    if image_bytes:
        encoded_image = base64.b64encode(image_bytes).decode("ascii")
        return (
            f'<img class="profile-avatar-picture {size_class}" '
            f'src="data:{escape(content_type)};base64,{encoded_image}" '
            f'alt="{escape(name)} profile picture">'
        )
    initials = "".join(part[0] for part in name.split()[:2]).upper() or "P"
    return (
        f'<div class="profile-avatar-fallback {size_class}" role="img" '
        f'aria-label="Default profile picture">{escape(initials)}</div>'
    )


PUBLIC_RESEARCH_IMAGES = api("GET", "/research/images/public") or []
PUBLIC_IMAGE_BY_SOURCE = {
    image["source_page"]: image for image in PUBLIC_RESEARCH_IMAGES
}


def currency(value):
    return f"€{float(value):.2f}"


def product_image(product, height=180, key="product"):
    url = product.get("image_url")
    source_image = PUBLIC_IMAGE_BY_SOURCE.get(product.get("image_source_url"))
    has_attribution = bool(source_image and product.get("image_license"))
    farmer_upload = bool(url and url.startswith("/uploads/"))
    size_class = "small" if height <= 120 else "medium" if height <= 160 else "large" if height >= 220 else "standard"
    with st.container(key=f"product-photo-{size_class}-{key}"):
        if url and (has_attribution or farmer_upload):
            if source_image:
                url = f"/research/images/{source_image['slug']}/file"
            if url.startswith("/"):
                url = API.rstrip("/") + url
            st.image(url, use_container_width=True)
            if has_attribution:
                st.caption(
                    f"Illustrative generic photo · not from Peja or seller stock · {product['image_license']}"
                    if product.get("image_is_generic")
                    else f"Photo attribution: {product['image_attribution']}"
                )
                st.markdown(f"[Image source and license]({product['image_source_url']})")
            else:
                st.caption("Farmer-provided image; source and reuse rights are not independently checked.")
        else:
            category = product.get("category", "Other")
            category_key = category.casefold()
            icon, title = {
                "vegetables": ("🥬", "Fresh vegetables"),
                "fruits": ("🍒", "Fresh fruit"),
                "grains": ("🌾", "Grains and flour"),
                "dairy products": ("🥛", "Dairy products"),
                "homemade products": ("🫙", "Homemade goods"),
            }.get(category_key, ("🌿", "Farm product"))
            st.markdown(
                f'<div class="image-fallback" role="img" aria-label="{escape(title)}">'
                f'<span class="image-fallback-icon">{icon}</span>'
                f'<span class="image-fallback-title">{escape(title)}</span>'
                '<span class="image-fallback-note">Product photo not yet available</span></div>',
                unsafe_allow_html=True,
            )


def demo_badge(label="Demonstration data"):
    st.markdown(f'<span class="demo-badge">{label}</span>', unsafe_allow_html=True)


def image_credit(image):
    credit = image.get("attribution", "")
    source = image.get("source_page", "")
    st.caption(credit)
    if source.startswith("https://commons.wikimedia.org/"):
        st.markdown(f"[Image source and license]({source})")


def render_image_banner(image, title, subtitle, style_class):
    photo_url = escape(
        API.rstrip("/") + f"/research/images/{image['slug']}/file",
        quote=True,
    )
    st.markdown(
        f'<div class="{style_class}" style="background-image:linear-gradient(0deg,rgba(13,37,24,.88),rgba(13,37,24,.04)),url(&quot;{photo_url}&quot;)">'
        f'<div class="local-hero-copy"><h2>{escape(title)}</h2><p>{escape(subtitle)}</p></div></div>',
        unsafe_allow_html=True,
    )
    image_credit(image)


def render_local_photo(image, caption=None):
    with st.container(key=f"local-photo-{image['slug']}"):
        st.image(
            API.rstrip("/") + f"/research/images/{image['slug']}/file",
            caption=caption or image.get("subject", image["title"]),
            use_container_width=True,
        )
        image_credit(image)


def render_local_discovery():
    st.markdown("## Discover Peja and Its Local Agriculture")
    st.write(
        "Explore Peja and Rugova through documented regional context. Landscape and retail "
        "photos show place, not farms, farmers, or the origin of any listing."
    )
    images = PUBLIC_RESEARCH_IMAGES
    image_by_slug = {image["slug"]: image for image in images}
    location_cards = [
        ("rugova-canyon", "Rugova", "The municipality describes Rugova northwest of Peja."),
        ("boge-rugova", "Bogë", "A Rugova winter landscape; not an agricultural photograph."),
        ("kipper-peja", "Peja town", "A retail scene in Peja, not a farm or produce source."),
    ]
    cols = st.columns(3)
    for column, (slug, title, caption) in zip(cols, location_cards):
        image = image_by_slug.get(slug)
        with column:
            with st.container(border=True):
                if image:
                    render_local_photo(image, caption)
                st.subheader(title)

    products = [image_by_slug[slug] for slug in (
        "generic-apples", "generic-tomatoes", "generic-peppers",
        "generic-potatoes", "generic-cheese", "generic-honey",
    ) if slug in image_by_slug]
    if products:
        st.markdown("### Generic product photography")
        st.caption(
            "These licensed photographs are illustrative only. They are not from Peja, "
            "do not show seller inventory, and do not establish local product origin."
        )
        gallery = st.columns(3)
        for index, image in enumerate(products):
            with gallery[index % len(gallery)]:
                with st.container(border=True):
                    render_local_photo(image, image["subject"])

    records = api("GET", "/research/public") or []
    if records:
        st.markdown("### Source-backed regional notes")
        for record in records:
            with st.container(border=True):
                st.markdown(f"**{record['title']}**")
                st.write(record["description"])
                st.caption(
                    f"{record['location']} · {record['verification_status'].replace('_', ' ').title()} · "
                    f"Last reviewed: {str(record.get('last_verified_at') or 'not recorded')[:10]}"
                )
                st.markdown(f"[Source: {record['source']['title']}]({record['source']['url']})")
    else:
        st.info(
            "Source-backed research records are staged for administrator review and are not "
            "published yet. No researched farmers or current local prices were verified."
        )
    with st.expander("Source and methodology"):
        st.write(
            "The research file records its methods, coverage, access date, and source URLs. "
            "The 2014 Agricultural Census is historical; national price data is not treated "
            "as a Peja price list. No farm coordinates or private addresses are included."
        )
        st.caption("The full report is included in the project at research/peja_agriculture_research.md.")


def render_research_admin():
    summary = api("GET", "/research/admin/summary") or {}
    metric_rows = [st.columns(4), st.columns(4)]
    metric_values = [
        ("Researched farms/businesses", "total_researched_businesses"),
        ("Verified businesses", "verified_businesses"),
        ("Publicly documented businesses", "publicly_documented_businesses"),
        ("Demonstration records", "demonstration_records"),
        ("Regional product references", "products_with_regional_information"),
        ("Images with confirmed rights", "images_with_confirmed_rights"),
        ("Records awaiting review", "records_requiring_review"),
        ("Images needing rights review", "images_requiring_rights_review"),
    ]
    for index, (label, key) in enumerate(metric_values):
        metric_rows[index // 4][index % 4].metric(label, summary.get(key, 0))
    st.info(
        "No named Peja farm or farmer was verified in this research. The municipal-listed "
        "restaurant is recorded only as a food venue; it is not a farmer or PejaMarket member."
    )

    st.markdown("### Review researched records")
    search_col, type_col, status_col = st.columns([2, 1, 1])
    record_search = search_col.text_input("Search research records", key="research_search")
    record_type = type_col.selectbox(
        "Record type",
        ["All", "regional_fact", "location", "food_tradition", "historical_market_reference",
         "food_venue", "product_reference", "business", "farm"],
        key="research_type_filter",
    )
    publication_status = status_col.selectbox(
        "Publication status", ["pending", "approved", "rejected", "All"],
        key="research_status_filter",
    )
    params = {
        "search": record_search or None,
        "record_type": None if record_type == "All" else record_type,
        "publication_status": None if publication_status == "All" else publication_status,
    }
    records = api("GET", "/research/admin/records", params=params) or []
    if not records:
        st.info("No research records match these filters.")
    for record in records:
        with st.container(border=True):
            st.markdown(f"**{record['title']}**")
            st.caption(
                f"{record['record_type'].replace('_', ' ').title()} · "
                f"{record['verification_status'].replace('_', ' ').title()} · "
                f"{record['publication_status'].title()} · {record['location'] or 'No location'}"
            )
            st.write(record["description"])
            st.markdown(f"[Source: {record['source']['title']}]({record['source']['url']})")
            verified = record.get("last_verified_at")
            st.caption(f"Last checked: {str(verified)[:10] if verified else 'Not recorded'}")
            with st.form(f"research_record_form_{record['id']}"):
                edit_title = st.text_input("Title", value=record["title"], key=f"rt_{record['id']}")
                edit_description = st.text_area(
                    "Description", value=record["description"], key=f"rd_{record['id']}"
                )
                edit_location = st.text_input(
                    "Location", value=record["location"], key=f"rl_{record['id']}"
                )
                record_types = [
                    "business", "farm", "regional_fact", "location", "food_tradition",
                    "historical_market_reference", "food_venue", "product_reference",
                ]
                edit_record_type = st.selectbox(
                    "Record type",
                    record_types,
                    index=record_types.index(record["record_type"]),
                    key=f"rtype_{record['id']}",
                )
                metadata_text = st.text_area(
                    "Structured metadata (JSON)",
                    value=json.dumps(record["metadata"], ensure_ascii=False, indent=2),
                    key=f"rmeta_{record['id']}",
                )
                form_cols = st.columns(3)
                verification = form_cols[0].selectbox(
                    "Evidence status",
                    ["verified", "publicly_documented", "unverified", "demonstration_data"],
                    index=["verified", "publicly_documented", "unverified", "demonstration_data"].index(
                        record["verification_status"]
                    ),
                    key=f"rv_{record['id']}",
                )
                publish_status = form_cols[1].selectbox(
                    "Publication", ["pending", "approved", "rejected"],
                    index=["pending", "approved", "rejected"].index(record["publication_status"]),
                    key=f"rp_{record['id']}",
                )
                public_permission = form_cols[2].checkbox(
                    "Public display permitted",
                    value=record["public_listing_permission"],
                    key=f"rperm_{record['id']}",
                )
                save_record = st.form_submit_button("Save review")
            if save_record:
                try:
                    metadata = json.loads(metadata_text)
                    if not isinstance(metadata, dict):
                        raise ValueError("Structured metadata must be a JSON object.")
                except (json.JSONDecodeError, ValueError) as exc:
                    st.error(f"Invalid structured metadata: {exc}")
                else:
                    updated = api("PATCH", f"/research/admin/records/{record['id']}", json={
                        "record_type": edit_record_type,
                        "title": edit_title,
                        "description": edit_description,
                        "location": edit_location,
                        "verification_status": verification,
                        "publication_status": publish_status,
                        "public_listing_permission": public_permission,
                        "metadata": metadata,
                    })
                    if updated:
                        st.success("Research record review saved.")
                        st.rerun()
            with st.expander("Edit source record"):
                with st.form(f"research_source_form_{record['id']}"):
                    source = record["source"]
                    source_url = st.text_input("Source URL", value=source["url"])
                    source_title = st.text_input("Source title", value=source["title"])
                    source_publisher = st.text_input("Publisher", value=source["publisher"])
                    source_coverage = st.text_input("Coverage", value=source["coverage"])
                    source_notes = st.text_area("Source notes", value=source["notes"])
                    save_source = st.form_submit_button("Update source")
                if save_source:
                    updated = api("PATCH", f"/research/admin/sources/{source['id']}", json={
                        "url": source_url,
                        "title": source_title,
                        "publisher": source_publisher,
                        "coverage": source_coverage,
                        "notes": source_notes,
                    })
                    if updated:
                        st.success("Source updated.")
                        st.rerun()
            confirm_remove = st.checkbox(
                "Confirm removing this record", key=f"confirm_remove_record_{record['id']}"
            )
            if st.button(
                "Remove research record",
                key=f"remove_record_{record['id']}",
                disabled=not confirm_remove,
            ):
                if api("DELETE", f"/research/admin/records/{record['id']}") is not None:
                    st.success("Research record removed from publication and review lists.")
                    st.rerun()

    st.markdown("### Review image rights and attribution")
    image_search = st.text_input("Search research images", key="research_image_search")
    images = api(
        "GET", "/research/admin/images", params={"search": image_search or None}
    ) or []
    if not images:
        st.info("No images match this search.")
    image_cols = st.columns(2)
    for index, image in enumerate(images):
        with image_cols[index % 2]:
            with st.container(border=True):
                render_local_photo(image, image["subject"])
                st.markdown(f"**{image['title']}**")
                st.caption(
                    f"{image['image_type'].replace('_', ' ').title()} · "
                    f"{'Peja-region image' if image['local_to_peja'] else 'Generic image, not from Peja'}"
                )
                with st.form(f"research_image_form_{image['id']}"):
                    title = st.text_input(
                        "Image title", value=image["title"], key=f"it_{image['id']}"
                    )
                    photographer = st.text_input(
                        "Photographer", value=image["photographer"], key=f"ip_{image['id']}"
                    )
                    license_name = st.text_input(
                        "License", value=image["license"], key=f"il_{image['id']}"
                    )
                    license_url = st.text_input(
                        "License URL", value=image.get("license_url") or "",
                        key=f"ilu_{image['id']}",
                    )
                    attribution = st.text_input(
                        "Attribution", value=image["attribution"], key=f"ia_{image['id']}"
                    )
                    subject = st.text_input(
                        "Subject", value=image["subject"], key=f"is_{image['id']}"
                    )
                    rights_confirmed = st.checkbox(
                        "Usage rights confirmed",
                        value=image["usage_rights_confirmed"],
                        key=f"ir_{image['id']}",
                    )
                    display_publicly = st.checkbox(
                        "Display publicly",
                        value=image["display_publicly"],
                        key=f"idp_{image['id']}",
                    )
                    save_image = st.form_submit_button("Save image review")
                if save_image:
                    updated = api("PATCH", f"/research/admin/images/{image['id']}", json={
                        "title": title,
                        "photographer": photographer,
                        "license": license_name,
                        "license_url": license_url or None,
                        "attribution": attribution,
                        "subject": subject,
                        "usage_rights_confirmed": rights_confirmed,
                        "display_publicly": display_publicly,
                    })
                    if updated:
                        st.success("Image review saved.")
                        st.rerun()
                confirm_remove_image = st.checkbox(
                    "Confirm removing image", key=f"confirm_remove_image_{image['id']}"
                )
                if st.button(
                    "Remove image",
                    key=f"remove_image_{image['id']}",
                    disabled=not confirm_remove_image,
                ):
                    if api("DELETE", f"/research/admin/images/{image['id']}") is not None:
                        st.success("Image removed from public display.")
                        st.rerun()


def status_badge(status):
    st.markdown(f'<span class="status">{status.replace("_", " ").title()}</span>', unsafe_allow_html=True)


def cart_from_backend():
    rows = api("GET", "/cart") or []
    st.session_state.cart = {
        str(row["product"]["id"]): row["quantity"] for row in rows
    }


def toggle_favorite(product_id, favorites):
    if product_id in favorites:
        response = api("DELETE", f"/favorites/{product_id}")
        return response is not None
    response = api("POST", f"/favorites/{product_id}")
    return response is not None


def render_notifications():
    notifications = api("GET", "/notifications") or []
    unread = [item for item in notifications if not item["is_read"]]
    top = st.columns([3, 1])
    top[0].caption(f"{len(unread)} unread notification(s)")
    if unread and top[1].button("Mark all as read", key="read_all_notifications"):
        api("POST", "/notifications/read-all")
        st.rerun()
    if not notifications:
        st.info("You’re all caught up. New order and inventory activity will appear here.")
        return
    for item in notifications:
        with st.container(border=True):
            left, right = st.columns([4, 1])
            left.markdown(f"**{item['title']}**")
            left.write(item["message"])
            left.caption(item["created_at"].replace("T", " ")[:16])
            if not item["is_read"] and right.button("Mark read", key=f"read_notification_{item['id']}"):
                api("PATCH", f"/notifications/{item['id']}/read")
                st.rerun()


def render_profile():
    profile = api("GET", "/auth/profile")
    if not profile:
        return
    user_id = profile["id"]
    editing_key = f"profile_picture_editing_{user_id}"
    version_key = f"profile_picture_upload_version_{user_id}"
    editing_picture = st.session_state.get(editing_key, False)
    current_picture = st.session_state.get("profile_picture_bytes")

    st.markdown("### Change Profile Picture")
    avatar_col, actions_col = st.columns([1, 4], gap="medium")
    with avatar_col:
        st.markdown(
            profile_avatar_markup(current_picture, profile["name"], 112),
            unsafe_allow_html=True,
        )
    with actions_col:
        if editing_picture:
            version = st.session_state.get(version_key, 0)
            uploaded_photo = st.file_uploader(
                "Upload Photo",
                type=["jpg", "jpeg", "png", "webp"],
                key=f"profile_picture_upload_{user_id}_{version}",
            )
            oversized = bool(uploaded_photo and uploaded_photo.size > 5 * 1024 * 1024)
            if uploaded_photo:
                if oversized:
                    st.error("Image must be 5 MB or smaller.")
                else:
                    st.markdown(
                        profile_avatar_markup(
                            uploaded_photo.getvalue(),
                            profile["name"],
                            112,
                            uploaded_photo.type or "application/octet-stream",
                        ),
                        unsafe_allow_html=True,
                    )
            confirm_col, cancel_col = st.columns(2)
            if confirm_col.button(
                "Confirm upload",
                key=f"profile_picture_confirm_{user_id}",
                type="primary",
                disabled=not uploaded_photo or oversized,
                use_container_width=True,
            ):
                result = api(
                    "POST",
                    "/auth/profile-picture",
                    files={
                        "image": (
                            uploaded_photo.name,
                            uploaded_photo.getvalue(),
                            uploaded_photo.type or "application/octet-stream",
                        )
                    },
                )
                if result:
                    st.session_state[editing_key] = False
                    st.session_state[version_key] = version + 1
                    st.success("Profile picture updated.")
                    st.rerun()
            if cancel_col.button(
                "Cancel",
                key=f"profile_picture_cancel_{user_id}",
                use_container_width=True,
            ):
                st.session_state[editing_key] = False
                st.session_state[version_key] = version + 1
                st.rerun()
        else:
            change_col, remove_col = st.columns(2)
            if change_col.button(
                "Change Photo",
                key=f"profile_picture_change_{user_id}",
                use_container_width=True,
            ):
                st.session_state[editing_key] = True
                st.rerun()
            if current_picture and remove_col.button(
                "Remove Photo",
                key=f"profile_picture_remove_{user_id}",
                use_container_width=True,
            ):
                result = api("DELETE", "/auth/profile-picture")
                if result is not None:
                    st.session_state[editing_key] = False
                    st.session_state[version_key] = st.session_state.get(version_key, 0) + 1
                    st.success("Profile picture removed.")
                    st.rerun()

    st.markdown("### Account details")
    st.caption(f"Signed in as {profile['email']}. Email changes require verification and are not available in this local MVP.")
    with st.form("profile_form"):
        name = st.text_input("Full name", value=profile["name"])
        phone = st.text_input("Phone number", value=profile.get("phone") or "")
        fields = {}
        if profile["role"] == "farmer":
            fields["farm_name"] = st.text_input("Farm name", value=profile.get("farm_name") or "")
            fields["village"] = st.text_input("Village or location", value=profile.get("village") or "")
            fields["farm_description"] = st.text_area(
                "About the farm", value=profile.get("farm_description") or ""
            )
            fields["main_products"] = st.text_input(
                "Main products", value=profile.get("main_products") or ""
            )
        save = st.form_submit_button("Save profile", type="primary")
    if save:
        result = api("PUT", "/auth/profile", json={
            "name": name,
            "phone": phone or None,
            **fields,
        })
        if result:
            st.session_state.user["name"] = result["name"]
            st.success("Profile updated.")
            st.rerun()

    with st.expander("Change password"):
        with st.form("password_form"):
            current_password = st.text_input("Current password", type="password")
            new_password = st.text_input("New password (at least 8 characters)", type="password")
            confirm_password = st.text_input("Confirm new password", type="password")
            change = st.form_submit_button("Update password")
        if change:
            if new_password != confirm_password:
                st.error("The new passwords do not match.")
            else:
                result = api("POST", "/auth/change-password", json={
                    "current_password": current_password,
                    "new_password": new_password,
                })
                if result is not None:
                    st.success("Password updated.")


def render_sidebar_navigation(user, role):
    notifications = api("GET", "/notifications") or []
    unread_count = sum(not item["is_read"] for item in notifications)
    picture = profile_picture_bytes()
    st.session_state["profile_picture_bytes"] = picture
    navigation = {
        "customer": [
            ("MAIN", [
                ("⌂", "Overview", "Overview"),
                ("⌕", "Explore Marketplace", "Explore"),
                ("▦", "Browse Categories", "Browse Categories"),
                ("♧", "Discover Farmers", "Farmers"),
                ("◉", "Local Agriculture", "Local discovery"),
            ]),
            ("SHOPPING", [
                ("▣", f"Shopping Cart · {sum(st.session_state.cart.values())}", "Shopping cart"),
                ("▤", "My Orders", "My orders"),
                ("♡", "Favorites", "Favorites"),
                ("◷", "Recently Viewed", "Recently viewed"),
            ]),
            ("MY ACCOUNT", [
                ("○", "My Profile", "My profile"),
                ("◌", f"Notifications · {unread_count}", "Notifications",),
                ("✉", "Messages", "Messages"),
                ("⚙", "Account Settings", "Account settings"),
            ]),
            ("EXTRAS", [
                ("✦", "Farm Assistant", "Farm Assistant"),
                ("?", "Help & Support", "Help & Support"),
                ("i", "About PejaMarket", "About PejaMarket"),
            ]),
        ],
        "farmer": [
            ("MAIN", [
                ("⌂", "Dashboard", "Dashboard"),
                ("▦", "My Products", "My products"),
                ("+", "Add Product", "Add product"),
                ("▣", "Manage Orders", "Manage orders"),
                ("▤", "Sales Analytics", "Sales analytics"),
            ]),
            ("MY ACCOUNT", [
                ("✉", "Customer Messages", "Customer messages"),
                ("○", "Farm Profile", "Farm profile"),
                ("◌", f"Notifications · {unread_count}", "Notifications"),
                ("⚙", "Settings", "Settings"),
            ]),
            ("EXTRAS", [
                ("✦", "Farm Assistant", "Farm Assistant"),
            ]),
        ],
        "admin": [
            ("MAIN", [
                ("⌂", "Admin Overview", "Admin Overview"),
                ("♧", "User Management", "User Management"),
                ("○", "Customers", "Customers"),
                ("✓", "Farmer Verification", "Farmer Verification"),
                ("▦", "Product Management", "Product Management"),
                ("▣", "Orders", "Orders"),
            ]),
            ("REVIEW", [
                ("◉", "Local Data & Research", "Local Data & Research"),
                ("▧", "Image & Source Review", "Image & Source Review"),
            ]),
            ("OTHER", [
                ("▤", "Reports", "Reports"),
                ("⚙", "Settings", "Settings"),
            ]),
        ],
    }
    groups = navigation[role]
    pages = {page for _, items in groups for _, _, page in items}
    default_page = groups[0][1][0][2]
    active_key = f"active_sidebar_page_{role}"
    compact_key = f"compact_sidebar_{role}"
    if st.session_state.get(active_key) not in pages:
        st.session_state[active_key] = default_page

    with st.sidebar:
        compact = st.session_state.get(compact_key, False)
        if compact:
            st.markdown('<div class="pejamarket-compact-sidebar"></div>', unsafe_allow_html=True)
        if st.button(
            "›" if compact else "Collapse navigation",
            key=f"toggle_sidebar_{role}",
            help="Expand navigation" if compact else "Collapse to icons",
            use_container_width=True,
        ):
            st.session_state[compact_key] = not compact
            st.rerun()
        st.markdown("## ◉" if compact else "## PejaMarket")
        if not compact:
            st.caption("Peja, Kosovo")
        st.divider()
        for section, items in groups:
            if not compact:
                st.markdown(
                    f'<p class="sidebar-section-heading">{escape(section)}</p>',
                    unsafe_allow_html=True,
                )
            for icon, label, page in items:
                page_key = re.sub(r"[^a-z0-9]+", "_", page.lower()).strip("_")
                button_key = f"sidebar_nav_btn_{role}_{page_key}"
                selected = page == st.session_state[active_key]
                button_label = (
                    f"{'• ' if selected else ''}{icon}"
                    if compact
                    else f"{'›' if selected else ' '}  {icon}   {label}"
                )
                if st.button(
                    button_label,
                    key=button_key,
                    help=label if compact else None,
                    use_container_width=True,
                ):
                    st.session_state[active_key] = page
                    st.rerun()
        st.divider()
        with st.container(key="sidebar_profile_area"):
            if compact:
                st.markdown(
                    profile_avatar_markup(picture, user["name"], 46),
                    unsafe_allow_html=True,
                )
                if user.get("is_demo"):
                    st.markdown('<span title="Demo account">DEMO</span>', unsafe_allow_html=True)
            else:
                avatar_col, details_col = st.columns([.8, 2.7], gap="small")
                with avatar_col:
                    st.markdown(
                        profile_avatar_markup(picture, user["name"], 46),
                        unsafe_allow_html=True,
                    )
                with details_col:
                    st.markdown(f"**{escape(user['name'])}**")
                    account_type = {"customer": "Customer", "farmer": "Farmer", "admin": "Administrator"}[role]
                    st.caption(f"{account_type} account")
            if user.get("is_demo"):
                demo_badge("DEMO ACCOUNT")
            if not compact:
                st.caption(f"Notifications · {unread_count} unread")
        if st.button(
            "↪" if compact else "Sign out",
            key=f"sign_out_{role}",
            help="Sign out" if compact else None,
            use_container_width=True,
        ):
            st.session_state.token = None
            st.session_state.user = None
            st.session_state.cart = {}
            st.session_state.cart_loaded_for = None
            st.session_state.pop("profile_picture_bytes", None)
            st.session_state.pop(f"profile_picture_editing_{user['id']}", None)
            st.session_state.pop(active_key, None)
            st.session_state.pop(compact_key, None)
            st.rerun()
    return st.session_state[active_key], unread_count


def render_recently_viewed():
    if not st.session_state.recent:
        st.info("Products you open from the marketplace will appear here.")
        return
    recent_products = [
        api("GET", f"/products/{product_id}")
        for product_id in st.session_state.recent
    ]
    for product in [item for item in recent_products if item]:
        with st.container(border=True):
            left, right = st.columns([1, 3])
            with left:
                product_image(product, height=140, key=f"recent-{product['id']}")
            with right:
                st.subheader(product["name"])
                if product.get("is_demo"):
                    demo_badge("DEMO · fictional listing and price")
                else:
                    st.caption(f"{product['category']} · {currency(product['price'])} / {product['unit']}")


def brand_header(title="Fresh from local farms", subtitle="Straight to your table."):
    st.markdown(
        f'<div class="hero"><h1>{title}</h1><p>{subtitle} Explore marketplace listings and source-backed regional context from Peja and nearby villages.</p></div>',
        unsafe_allow_html=True,
    )


if not st.session_state.token:
    left, right = st.columns([1.18, 0.82], gap="large")
    with left:
        landing_images = PUBLIC_RESEARCH_IMAGES
        image_by_slug = {image["slug"]: image for image in landing_images}
        rugova_image = image_by_slug.get("rugova-canyon")
        if rugova_image:
            render_image_banner(
                rugova_image,
                "Rooted in Peja, Inspired by Rugova",
                "Local scenery and agricultural history, presented with sources and without invented sellers.",
                "auth-local-hero",
            )
        boga_image = image_by_slug.get("boge-rugova")
        if boga_image:
            with st.container(border=True):
                secondary_image, secondary_copy = st.columns([1.2, 1])
                with secondary_image:
                    render_local_photo(
                        boga_image,
                        "Bogë winter landscape · local scenery, not a farm photograph.",
                    )
                with secondary_copy:
                    st.markdown("### Peja and Rugova")
                    st.write("Explore the region behind this marketplace.")
        brand_header("PejaMarket", "A local marketplace experience grounded in documented Peja sources.")
        demo = api("GET", "/products", params={"available": "true"}) or []
        if demo:
            preview = [product for product in demo if product.get("image_source_url")][:3]
            cols = st.columns(3)
            for col, product in zip(cols, preview):
                with col:
                    with st.container(border=True):
                        product_image(product, key=f"landing-{product['id']}")
                        st.subheader(product["name"])
                        if product.get("is_demo"):
                            demo_badge("DEMO · fictional listing and price")
                            st.caption(f"Demo price: {currency(product['price'])} / {product['unit']}")
                        else:
                            st.caption(f"{currency(product['price'])} / {product['unit']}")
        landing_meta = api("GET", "/products/meta") or {}
        stat_cols = st.columns(2)
        stat_cols[0].metric("Available registered listings", landing_meta.get("available_products", 0))
        stat_cols[1].metric("Registered farmer accounts", landing_meta.get("farmers", 0))
        st.caption(
            f"{landing_meta.get('demo_available_products', 0)} demonstration listing(s) are shown "
            "separately. Counts are PejaMarket records, not regional market statistics."
        )
        featured_farmers = api("GET", "/farmers") or []
        if featured_farmers:
            farm = featured_farmers[0]
            farm_profile = farm.get("profile") or {}
            with st.container(border=True):
                farm_name = farm_profile.get("farm_name") or farm["name"]
                st.markdown(
                    f"### {'Demonstration farm: ' if farm.get('is_demo') else 'From '}{farm_name}"
                )
                st.caption(f"{farm['name']} · {farm_profile.get('village') or 'Peja region'}")
                st.write(farm_profile.get("description") or "Discover locally grown products from a Peja-area farmer.")
                if farm.get("is_demo"):
                    demo_badge("DEMO FARM · fictional profile")
        st.markdown("### Discover Peja and Its Local Agriculture")
        st.write(
            "Peja and Rugova are represented with source-linked regional research, not invented "
            "farmers or unverified product-origin claims."
        )
        public_records = api("GET", "/research/public") or []
        if public_records:
            for record in public_records[:2]:
                st.markdown(f"**{record['title']}**")
                st.caption(record["description"])
                st.markdown(f"[Source: {record['source']['title']}]({record['source']['url']})")
        else:
            st.info(
                "Local research is staged for administrator approval. Until review, this page "
                "does not publish regional statistics, producer names, or current prices."
            )
        benefit_cols = st.columns(3)
        benefit_cols[0].markdown("**Local context**  \nExplore sourced regional information.")
        benefit_cols[1].markdown("**Pickup-based**  \nArrange collection directly with farmers.")
        benefit_cols[2].markdown("**Clear provenance**  \nDemo content and unverified origins are labeled.")
    with right:
        st.markdown("### Welcome")
        login_tab, register_tab = st.tabs(["Sign in", "Create account"])
        with login_tab:
            email = st.text_input("Email", key="login_email")
            password = st.text_input("Password", type="password", key="login_password")
            remember_me = st.checkbox("Remember me for 30 days")
            if st.button("Sign in", use_container_width=True):
                data = api("POST", "/auth/login", json={
                    "email": email, "password": password, "remember_me": remember_me
                })
                if data:
                    st.session_state.token = data["access_token"]
                    st.session_state.user = data["user"]
                    if data["user"]["role"] == "customer":
                        cart_from_backend()
                    st.rerun()
        with register_tab:
            name = st.text_input("Full name", key="register_name")
            reg_email = st.text_input("Email", key="register_email", placeholder="you@example.com")
            reg_password = st.text_input("Password", type="password", key="register_password")
            password_score = sum((
                len(reg_password) >= 8,
                bool(re.search(r"[A-Z]", reg_password)),
                bool(re.search(r"[a-z]", reg_password)),
                bool(re.search(r"\d", reg_password)),
                bool(re.search(r"[^A-Za-z0-9]", reg_password)),
            ))
            if reg_password:
                st.caption(f"Password strength: {['Very weak', 'Weak', 'Fair', 'Good', 'Strong', 'Strong'][password_score]}")
            confirm_password = st.text_input("Confirm password", type="password", key="confirm_register_password")
            phone = st.text_input("Phone number", key="register_phone")
            role = st.selectbox("Account type", ["Customer", "Farmer"])
            farm_details = {}
            if role == "Farmer":
                st.markdown("**Farm information**")
                farm_details["farm_name"] = st.text_input("Farm name", key="register_farm_name")
                farm_details["village"] = st.text_input("Village or location", key="register_village")
                farm_details["farm_description"] = st.text_area("Short farm description", key="register_farm_description")
                farm_details["main_products"] = st.text_input("Main agricultural products", key="register_main_products")
            terms = st.checkbox("I agree to the marketplace terms and understand this demo does not process payments.")
            if st.button("Create account", use_container_width=True):
                if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", reg_email.strip()):
                    st.error("Enter a valid email address.")
                elif reg_password != confirm_password:
                    st.error("The passwords do not match.")
                elif password_score < 3:
                    st.error("Choose a stronger password with at least 8 characters, letters, and a number.")
                elif role == "Farmer" and (not farm_details["farm_name"].strip() or not farm_details["village"].strip()):
                    st.error("Farm name and location are required for farmer accounts.")
                elif not terms:
                    st.error("Please agree to the terms before creating your account.")
                else:
                    data = api(
                        "POST",
                        "/auth/register",
                        json={
                            "name": name,
                            "email": reg_email,
                            "password": reg_password,
                            "phone": phone or None,
                            "role": role.lower(),
                            "terms_accepted": terms,
                            **farm_details,
                        },
                    )
                    if data:
                        st.session_state.token = data["access_token"]
                        st.session_state.user = data["user"]
                        if data["user"]["role"] == "customer":
                            cart_from_backend()
                        st.success("Account created. Welcome to PejaMarket!")
                        st.rerun()
        with st.expander("Demonstration accounts"):
            st.markdown("- **Customer:** browse and order clearly labeled fictional sample listings.")
            st.markdown("- **Farmer:** manage listings, orders, and sales.")
            st.markdown("- **Administrator:** review platform activity.")
            st.caption("For demo passwords, see the project README.")
    st.stop()


user = st.session_state.user
role = user["role"]

if role == "farmer" and st.session_state.get("product_description_draft"):
    st.session_state["new_product_description"] = st.session_state.pop("product_description_draft")

if role == "customer" and st.session_state.get("cart_loaded_for") != user["id"]:
    cart_from_backend()
    st.session_state.cart_loaded_for = user["id"]

active_page, unread_count = render_sidebar_navigation(user, role)


if role == "customer":
    brand_header("Explore PejaMarket", "Marketplace listings and regional discovery.")
    st.markdown(f"## {active_page}")

    if active_page == "Overview":
        customer_orders = api("GET", "/orders") or []
        st.markdown(f"### Welcome back, {user['name'].split()[0]}")
        total_orders = len(customer_orders)
        pending_orders = sum(order["status"] in {"pending", "accepted", "confirmed", "ready_for_pickup", "preparing"} for order in customer_orders)
        completed_orders = sum(order["status"] in {"completed", "delivered"} for order in customer_orders)
        favorite_count = len(api("GET", "/favorites") or [])
        metric_cols = st.columns(4)
        metric_cols[0].metric("Total orders", total_orders)
        metric_cols[1].metric("In progress", pending_orders)
        metric_cols[2].metric("Completed", completed_orders)
        metric_cols[3].metric("Favorites", favorite_count)
        if any(order.get("is_demo") for order in customer_orders):
            st.caption("Some order history is demonstration data with fictional prices and listings.")
        if customer_orders:
            st.markdown("### Recent activity")
            for order in customer_orders[:3]:
                with st.container(border=True):
                    left, middle, right = st.columns([2, 1, 1])
                    left.markdown(f"**Order #{order['id']}**")
                    left.caption(f"Pickup date: {order.get('pickup_date') or 'To be arranged'}")
                    with middle:
                        status_badge(order["status"])
                    if order.get("is_demo"):
                        left.caption("DEMO order · fictional transaction")
                        right.markdown(f"**Demo total:** {currency(order['total'])}")
                    else:
                        right.markdown(f"### {currency(order['total'])}")
        if st.session_state.recent:
            st.markdown("### Recently viewed")
            recent_products = [
                api("GET", f"/products/{product_id}")
                for product_id in st.session_state.recent
            ]
            for product in [item for item in recent_products if item]:
                if product.get("is_demo"):
                    st.caption(f"{product['name']} · demonstration listing")
                else:
                    st.caption(f"{product['name']} · {currency(product['price'])} / {product['unit']}")
        st.caption("Browse fresh listings or use your favorites to quickly build your next order.")

    if active_page in {"Explore", "Browse Categories"}:
        meta = api("GET", "/products/meta") or {}
        images = PUBLIC_RESEARCH_IMAGES
        image_by_slug = {image["slug"]: image for image in images}
        rugova_image = image_by_slug.get("rugova-canyon")
        if rugova_image:
            render_image_banner(
                rugova_image,
                "Peja and Rugova, in view",
                "Discover local context alongside listings. Scenery does not verify a product's origin.",
                "market-local-hero",
            )
        metric_cols = st.columns(4)
        metric_cols[0].metric("Available registered listings", meta.get("available_products", 0))
        metric_cols[1].metric("Registered farmer accounts", meta.get("farmers", 0))
        metric_cols[2].metric("Demo listings", meta.get("demo_available_products", 0))
        metric_cols[3].metric("Categories", len(meta.get("categories", [])))
        st.caption("Demo listings and prices are fictional examples, not current local offers.")
        featured = api("GET", "/products", params={"sort": "popular", "limit": 3, "available": "true"}) or []
        if featured:
            st.markdown("### Featured PejaMarket listings")
            featured_cols = st.columns(3)
            for column, product in zip(featured_cols, featured):
                with column:
                    with st.container(border=True):
                        product_image(product, key=f"featured-{product['id']}")
                        st.markdown(f"**{product['name']}**")
                        if product.get("is_demo"):
                            demo_badge("DEMO · fictional listing and price")
                        else:
                            st.caption(
                                f"{product.get('farmer_name') or 'Registered farmer'} · "
                                f"{currency(product['price'])} / {product['unit']}"
                            )
        with st.container(border=True):
            if st.button("Clear all filters", key="clear_market_filters"):
                for key, default in {
                    "market_search": "", "market_category": "All", "market_sort": "Newest",
                    "market_village": "All locations", "market_unit": "Any unit",
                    "market_available": True, "market_min": 0.0, "market_max": 20.0,
                    "market_view": "Grid", "market_page_size": 9, "market_page": 1,
                }.items():
                    st.session_state[key] = default
                st.rerun()
            c1, c2, c3 = st.columns([2.1, 1.3, 1.3])
            search = c1.text_input("Search products, farms, or villages", placeholder="Try tomatoes or Rugova", key="market_search")
            category = c2.selectbox("Category", ["All"] + CATEGORIES, key="market_category")
            sort = c3.selectbox(
                "Sort by",
                ["Newest", "Oldest", "Lowest price", "Highest price", "Alphabetical", "Most popular"],
                key="market_sort",
            )
            locations = api("GET", "/farmers") or []
            villages = sorted({
                farmer.get("profile", {}).get("village", "")
                for farmer in locations if farmer.get("profile", {}).get("village")
            })
            c4, c5, c6, c7 = st.columns([1.3, 1, 1, 1])
            village = c4.selectbox("Farmer location", ["All locations"] + villages, key="market_village")
            unit = c5.selectbox("Unit", ["Any unit", "kg", "piece", "liter", "package"], key="market_unit")
            available_only = c6.toggle("In stock only", value=True, key="market_available")
            c7.radio("Layout", ["Grid", "List"], horizontal=True, key="market_view")
            c8, c9, c10 = st.columns([1, 1, 2])
            min_price = c8.number_input("Minimum €", min_value=0.0, value=0.0, step=0.5, key="market_min")
            max_price = c9.number_input("Maximum €", min_value=0.0, value=20.0, step=0.5, key="market_max")
            page_size = c10.selectbox("Products per page", [6, 9, 12, 18], key="market_page_size")

        sort_api = {
            "Newest": "newest", "Oldest": "oldest", "Lowest price": "price_low",
            "Highest price": "price_high", "Alphabetical": "alphabetical",
            "Most popular": "popular",
        }[sort]
        products = api(
            "GET",
            "/products",
            params={
                "search": search or None,
                "category": None if category == "All" else category,
                "min_price": min_price,
                "max_price": max_price,
                "available": str(available_only).lower(),
                "sort": sort_api,
                "village": None if village == "All locations" else village,
                "unit": None if unit == "Any unit" else unit,
                "limit": 100,
            },
        ) or []
        favorite_products = api("GET", "/favorites") or []
        favorite_ids = {product["id"] for product in favorite_products}
        page_count = max(1, (len(products) + page_size - 1) // page_size)
        page = st.number_input("Page", min_value=1, max_value=page_count, value=min(
            st.session_state.get("market_page", 1), page_count
        ), step=1, key="market_page")
        page_products = products[(page - 1) * page_size:page * page_size]

        if not products:
            st.info("No products match these filters.")
        else:
            st.caption(f"Showing {len(page_products)} of {len(products)} listings · Page {page} of {page_count}")
            if st.session_state.market_view == "Grid":
                for start in range(0, len(page_products), 3):
                    cols = st.columns(3)
                    for col, product in zip(cols, page_products[start:start + 3]):
                        with col:
                            with st.container(border=True):
                                product_image(product, key=f"grid-{product['id']}")
                                st.subheader(product["name"])
                                if product.get("is_demo"):
                                    demo_badge("DEMO · fictional listing, origin, stock and price")
                                    st.caption(product["category"])
                                    st.write("Example listing for testing marketplace features; not a current local offer.")
                                else:
                                    st.markdown(f'<span class="product-meta">{product["category"]} · Registered farmer · {product.get("farmer_location") or product["village"]} · {product["stock"]} {product["unit"]} available</span>', unsafe_allow_html=True)
                                    st.write(product["description"])
                                    st.markdown(f'<span class="product-price">{currency(product["price"])}</span><span class="small-muted"> / {product["unit"]}</span>', unsafe_allow_html=True)
                                favorite_col, detail_col, add_col = st.columns(3)
                                if favorite_col.button("♥" if product["id"] in favorite_ids else "♡",
                                                       key=f"favorite_{product['id']}", help="Toggle favorite"):
                                    if toggle_favorite(product["id"], favorite_ids):
                                        st.rerun()
                                if detail_col.button("Details", key=f"details_{product['id']}"):
                                    st.session_state.selected_product_id = product["id"]
                                    st.session_state.recent = [
                                        product["id"],
                                        *[item for item in st.session_state.recent if item != product["id"]],
                                    ][:5]
                                    st.rerun()
                                if add_col.button("Add", key=f"add_{product['id']}", disabled=product["stock"] == 0):
                                    pid = str(product["id"])
                                    quantity = min(st.session_state.cart.get(pid, 0) + 1, product["stock"])
                                    result = api("PUT", f"/cart/{product['id']}", json={"quantity": quantity})
                                    if result:
                                        st.session_state.cart[pid] = quantity
                                        st.toast(f"{product['name']} added to your cart.")
                                        st.rerun()
            else:
                for product in page_products:
                    with st.container(border=True):
                        image_col, info_col, actions_col = st.columns([1, 3, 1.2])
                        with image_col:
                            product_image(product, height=140, key=f"list-{product['id']}")
                        info_col.subheader(product["name"])
                        if product.get("is_demo"):
                            info_col.markdown('<span class="demo-badge">DEMO · fictional listing</span>', unsafe_allow_html=True)
                            info_col.write("Example listing for testing marketplace features; product origin and availability are not verified.")
                            actions_col.markdown(f"**Demo price:** {currency(product['price'])} / {product['unit']}")
                        else:
                            info_col.write(product["description"])
                            info_col.caption(f"{product['category']} · Registered farmer · {product.get('farmer_location')} · {product['stock']} {product['unit']} available")
                            actions_col.markdown(f"### {currency(product['price'])} / {product['unit']}")
                        if actions_col.button("♡ Favorite" if product["id"] not in favorite_ids else "♥ Favorited", key=f"favorite_list_{product['id']}"):
                            if toggle_favorite(product["id"], favorite_ids):
                                st.rerun()
                        if actions_col.button("View details", key=f"details_list_{product['id']}"):
                            st.session_state.selected_product_id = product["id"]
                            st.session_state.recent = [
                                product["id"],
                                *[item for item in st.session_state.recent if item != product["id"]],
                            ][:5]
                            st.rerun()
                        if actions_col.button("Add to cart", key=f"add_list_{product['id']}"):
                            pid = str(product["id"])
                            quantity = min(st.session_state.cart.get(pid, 0) + 1, product["stock"])
                            if api("PUT", f"/cart/{product['id']}", json={"quantity": quantity}):
                                st.session_state.cart[pid] = quantity
                                st.rerun()

            selected_id = st.session_state.get("selected_product_id")
            if selected_id:
                detail = api("GET", f"/products/{selected_id}")
                if detail:
                    st.divider()
                    st.markdown("### Product details")
                    with st.container(border=True):
                        image_col, detail_col = st.columns([1, 2])
                        with image_col:
                            product_image(detail, height=240, key=f"details-{detail['id']}")
                        detail_col.title(detail["name"])
                        if detail.get("is_demo"):
                            detail_col.markdown('<span class="demo-badge">DEMO · fictional listing</span>', unsafe_allow_html=True)
                            detail_col.write(
                                "Example listing for testing marketplace features. Product origin, "
                                "availability, and price are fictional and are not a local offer."
                            )
                            detail_col.caption(f"Demo price: {currency(detail['price'])} / {detail['unit']}")
                        else:
                            detail_col.write(detail["description"])
                        if detail.get("is_demo"):
                            detail_col.caption(
                                f"Demo stock: {detail['stock']} {detail['unit']} · fictional farm profile"
                            )
                        else:
                            detail_col.markdown(
                                f"**{currency(detail['price'])} / {detail['unit']}** · "
                                f"{detail['stock']} available · {detail.get('farmer_name')}"
                            )
                            detail_col.caption(
                                f"Farm location: {detail.get('farmer_location') or detail['village']}"
                            )
                        other_products = api("GET", f"/farmers/{detail['farmer_id']}/products") or []
                        related = [item for item in other_products if item["id"] != detail["id"]][:3]
                        if related:
                            detail_col.markdown("**More from this farm**")
                            detail_col.write(" · ".join(item["name"] for item in related))
                        quantity = detail_col.number_input(
                            "Quantity to add", min_value=1, max_value=max(detail["stock"], 1),
                            value=1, key=f"detail_qty_{selected_id}",
                        )
                        if detail_col.button("Add selected quantity", key=f"detail_add_{selected_id}", disabled=detail["stock"] == 0):
                            pid = str(selected_id)
                            new_quantity = min(st.session_state.cart.get(pid, 0) + quantity, detail["stock"])
                            if api("PUT", f"/cart/{selected_id}", json={"quantity": new_quantity}):
                                st.session_state.cart[pid] = new_quantity
                                st.rerun()
                        if detail_col.button("Close details", key="close_product_details"):
                            del st.session_state.selected_product_id
                            st.rerun()
    if active_page == "Local discovery":
        render_local_discovery()

    if active_page == "Shopping cart":
        if not st.session_state.cart:
            st.info("Your shopping cart is empty. Continue exploring local products in the Explore tab.")
        else:
            cart_rows = api("GET", "/cart") or []
            by_id = {str(row["product"]["id"]): row for row in cart_rows}
            total = 0.0
            contains_demo_item = False
            for pid, quantity in list(st.session_state.cart.items()):
                row = by_id.get(pid)
                if not row:
                    del st.session_state.cart[pid]
                    continue
                product = row["product"]
                with st.container(border=True):
                    c1, c2, c3, c4 = st.columns([0.8, 2.8, 1.2, 1.2])
                    with c1:
                        product_image(product, height=110, key=f"cart-{product['id']}")
                    c2.markdown(f"**{product['name']}**")
                    if product.get("is_demo"):
                        contains_demo_item = True
                        c2.markdown(
                            '<span class="demo-badge">DEMO · fictional listing and price</span>',
                            unsafe_allow_html=True,
                        )
                        c2.caption(f"Demo price: {currency(product['price'])} / {product['unit']}")
                    else:
                        c2.caption(
                            f"Registered farmer · {product.get('farmer_location') or product['village']} · "
                            f"{currency(product['price'])} / {product['unit']}"
                        )
                    new_quantity = c3.number_input(
                        "Quantity", 1, max(product["stock"], 1),
                        min(quantity, max(product["stock"], 1)), key=f"qty_{pid}"
                    )
                    if new_quantity != quantity:
                        if api("PUT", f"/cart/{product['id']}", json={"quantity": new_quantity}):
                            st.session_state.cart[pid] = new_quantity
                    line_total = product["price"] * new_quantity
                    c4.markdown(
                        f"**Demo line:** {currency(line_total)}"
                        if product.get("is_demo") else f"### {currency(line_total)}"
                    )
                    if c4.button("Remove", key=f"remove_{pid}", help="Remove item"):
                        api("DELETE", f"/cart/{product['id']}")
                        del st.session_state.cart[pid]
                        st.rerun()
                    total += line_total

            st.divider()
            clear_col, continue_col = st.columns(2)
            if clear_col.button("Clear cart", key="clear_cart"):
                st.session_state.confirm_clear_cart = True
            if continue_col.button("Continue shopping", key="continue_shopping"):
                st.info("Choose the Explore tab to continue browsing.")
            if st.session_state.get("confirm_clear_cart"):
                st.warning("Remove every item from your cart?")
                confirm_col, keep_col = st.columns(2)
                if confirm_col.button("Yes, clear cart", type="primary"):
                    api("DELETE", "/cart")
                    st.session_state.cart = {}
                    st.session_state.confirm_clear_cart = False
                    st.rerun()
                if keep_col.button("Keep items"):
                    st.session_state.confirm_clear_cart = False
                    st.rerun()
            c1, c2 = st.columns([1.5, 1])
            with c1:
                st.markdown("### Pickup details")
                checkout_profile = api("GET", "/auth/profile") or {}
                st.text_input("Customer name", value=checkout_profile.get("name", ""), disabled=True)
                st.text_input("Email", value=checkout_profile.get("email", ""), disabled=True)
                contact = st.text_input("Contact phone", value=checkout_profile.get("phone") or "", placeholder="+383")
                address = st.text_area(
                    "Pickup location or additional instructions",
                    placeholder="Preferred pickup location or notes for the farmer",
                )
                pickup_date = st.date_input("Pickup date", value=date.today() + timedelta(days=1),
                                            min_value=date.today())
            with c2:
                st.markdown("### Order summary")
                st.metric("Demo total" if contains_demo_item else "Total", currency(total))
                if contains_demo_item:
                    st.warning("This cart contains fictional demonstration listings and prices.")
                st.caption("No payment is collected in this marketplace. Pickup arrangements are confirmed with the farmer.")
                if st.button("Place order", type="primary", use_container_width=True):
                    if len(address.strip()) < 5:
                        st.error("Please enter a complete address.")
                    else:
                        payload = {
                            "items": [{"product_id": int(pid), "quantity": qty}
                                      for pid, qty in st.session_state.cart.items()],
                            "delivery_address": address,
                            "pickup_date": pickup_date.isoformat(),
                            "contact_phone": contact or None,
                        }
                        data = api("POST", "/orders", json=payload)
                        if data:
                            st.session_state.cart = {}
                            st.session_state.cart_loaded_for = user["id"]
                            order_ids = data.get("order_ids", [data["id"]])
                            order_label = ", ".join(f"#{order_id}" for order_id in order_ids)
                            st.success(
                                f"Order {order_label} placed successfully."
                                if len(order_ids) == 1
                                else f"Orders {order_label} placed successfully."
                            )
                            st.balloons()
                            st.rerun()

    if active_page == "My orders":
        order_rows = api("GET", "/orders") or []
        order_products = {
            product["id"]: product
            for product in (
                api("GET", "/products", params={"available": "false", "limit": 100}) or []
            )
        } if order_rows else {}
        if not order_rows:
            st.info("You have no orders yet.")
        else:
            for order in order_rows:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1.5, 1, 1])
                    c1.subheader(f"Order #{order['id']}")
                    with c2:
                        status_badge(order["status"])
                    if order.get("is_demo"):
                        demo_badge("DEMO ORDER")
                        c3.markdown(f"**Demo total:** {currency(order['total'])}")
                    else:
                        c3.markdown(f"### {currency(order['total'])}")
                    st.caption(f"Pickup: {order.get('pickup_date') or 'To be arranged'} · Address: {order['delivery_address']}")
                    for item in order["items"]:
                        product = order_products.get(item["product_id"])
                        item_photo, item_description = st.columns([0.75, 4])
                        if product:
                            with item_photo:
                                product_image(
                                    product,
                                    height=110,
                                    key=f"order-{order['id']}-{product['id']}",
                                )
                        item_description.write(
                            f"{item['quantity']} × "
                            f"{item.get('product_name') or 'product #' + str(item['product_id'])}"
                        )
                    if order["status"] in {"pending", "confirmed"}:
                        if st.button("Cancel order", key=f"cancel_order_{order['id']}"):
                            data = api("PATCH", f"/orders/{order['id']}/status", json={"status": "cancelled"})
                            if data:
                                st.success("Order cancelled and stock restored.")
                                st.rerun()

    if active_page == "Favorites":
        favorite_products = api("GET", "/favorites") or []
        if not favorite_products:
            st.info("No favorites yet. Save products with the heart button while browsing.")
        for start in range(0, len(favorite_products), 3):
            columns = st.columns(3)
            for column, product in zip(columns, favorite_products[start:start + 3]):
                with column:
                    with st.container(border=True):
                        product_image(product, key=f"favorite-{product['id']}")
                        st.subheader(product["name"])
                        if product.get("is_demo"):
                            demo_badge("DEMO · fictional listing and price")
                            st.caption(f"Demo stock: {product['stock']} {product['unit']}")
                            st.caption(f"Demo price: {currency(product['price'])} / {product['unit']}")
                        else:
                            st.caption(f"{product['category']} · Registered farmer · {product['stock']} {product['unit']} available")
                            st.markdown(f"### {currency(product['price'])} / {product['unit']}")
                        if st.button("Add to cart", key=f"favorite_add_{product['id']}", disabled=product["stock"] < 1):
                            pid = str(product["id"])
                            quantity = min(st.session_state.cart.get(pid, 0) + 1, product["stock"])
                            if api("PUT", f"/cart/{product['id']}", json={"quantity": quantity}):
                                st.session_state.cart[pid] = quantity
                                st.rerun()
                        if st.button("Remove favorite", key=f"favorite_remove_{product['id']}"):
                            api("DELETE", f"/favorites/{product['id']}")
                            st.rerun()

    if active_page == "Farmers":
        st.markdown("### Discover registered farmer accounts")
        st.caption("Profile and origin information is supplied by each account holder; demo profiles are explicitly labeled.")
        farmer_search = st.text_input("Search farmers or farms", key="farmer_search")
        farmers = api("GET", "/farmers", params={"search": farmer_search or None}) or []
        if not farmers:
            st.info("No farmers match your search.")
        for start in range(0, len(farmers), 2):
            columns = st.columns(2)
            for column, farmer in zip(columns, farmers[start:start + 2]):
                profile = farmer.get("profile") or {}
                with column:
                    with st.container(border=True):
                        st.markdown(f"### {profile.get('farm_name') or farmer['name']}")
                        st.caption(f"{farmer['name']} · {profile.get('village') or 'Peja region'}")
                        if farmer.get("is_demo"):
                            demo_badge("DEMO FARM · fictional profile")
                            st.write("Fictional account for testing the farmer experience.")
                        else:
                            st.caption("Registered PejaMarket account; business details have not been independently verified.")
                            st.write(profile.get("description") or "No farm description has been supplied.")
                        st.caption(f"{farmer['product_count']} listed products · {farmer['available_products']} available")
                        if profile.get("main_products"):
                            st.write(f"Main products: {profile['main_products']}")
                        if st.button("Explore this farm", key=f"farmer_open_{farmer['id']}"):
                            st.session_state.selected_farmer_id = farmer["id"]
                            st.rerun()
        selected_farmer_id = st.session_state.get("selected_farmer_id")
        if selected_farmer_id:
            farmer = api("GET", f"/farmers/{selected_farmer_id}")
            farmer_products = api("GET", f"/farmers/{selected_farmer_id}/products") or []
            if farmer:
                st.divider()
                st.markdown(f"### Products from {farmer['profile'].get('farm_name') or farmer['name']}")
                if farmer.get("is_demo"):
                    demo_badge("DEMO FARM · fictional profile")
                if not farmer_products:
                    st.info("This farm has no active listings at the moment.")
                for product in farmer_products:
                    with st.container(border=True):
                        left, middle, right = st.columns([1, 3, 1])
                        with left:
                            product_image(product, height=120, key=f"farmer-products-{product['id']}")
                        middle.markdown(f"**{product['name']}**")
                        if product.get("is_demo"):
                            middle.markdown('<span class="demo-badge">DEMO · fictional listing</span>', unsafe_allow_html=True)
                            middle.caption("Example listing; origin and price are not verified.")
                            right.markdown(f"**Demo price:** {currency(product['price'])} / {product['unit']}")
                        else:
                            middle.caption(product["description"])
                            right.markdown(f"### {currency(product['price'])} / {product['unit']}")
                        if right.button("Add", key=f"farmer_product_add_{product['id']}", disabled=product["stock"] < 1):
                            pid = str(product["id"])
                            quantity = min(st.session_state.cart.get(pid, 0) + 1, product["stock"])
                            if api("PUT", f"/cart/{product['id']}", json={"quantity": quantity}):
                                st.session_state.cart[pid] = quantity
                                st.rerun()

    if active_page == "Notifications":
        render_notifications()

    if active_page in {"My profile", "Account settings"}:
        render_profile()

    if active_page == "Farm Assistant":
        st.markdown("### AI Farm Assistant")
        st.caption("Practical agricultural guidance in English")
        if st.button("Clear conversation", key="clear_customer_ai"):
            st.session_state.ai_history["customer"] = []
            st.rerun()
        for turn in st.session_state.ai_history["customer"]:
            with st.chat_message(turn["role"]):
                st.markdown(turn["text"])
                if turn.get("provider"):
                    st.caption(f"Source: {turn['provider']}")
        quick = st.pills(
            "Quick questions",
            [
                "How should I prepare tomatoes for planting?",
                "How do I keep my produce fresh longer?",
                "How can I set a fair local price?",
            ],
        )
        message = st.text_area("Ask a farming question", value=quick or "", height=120)
        if st.button("Ask assistant", type="primary"):
            if len(message.strip()) < 2:
                st.error("Enter a question first.")
            else:
                with st.spinner("Preparing guidance..."):
                    result = api("POST", "/ai/assistant", json={"message": message})
                if result:
                    st.session_state.ai_history["customer"].extend([
                        {"role": "user", "text": message},
                        {"role": "assistant", "text": result["reply"], "provider": result["provider"]},
                    ])
                    st.rerun()

    if active_page == "Recently viewed":
        render_recently_viewed()

    if active_page == "Messages":
        st.info(
            "Direct customer-to-farmer messaging is not available yet. Order and pickup "
            "updates appear in Notifications, and your active orders are available in My Orders."
        )

    if active_page == "Help & Support":
        st.markdown("### Shopping help")
        st.write(
            "Browse listings, add products to your cart, and arrange pickup details when "
            "placing an order. PejaMarket does not collect payment in this local MVP."
        )
        st.write(
            "Listings marked DEMO are fictional examples. Generic product photos are "
            "illustrative and do not verify a seller or product's origin."
        )
        st.caption("Order and inventory updates are available in Notifications.")

    if active_page == "About PejaMarket":
        st.markdown("### A marketplace grounded in Peja sources")
        st.write(
            "PejaMarket combines marketplace tools with documented regional context. "
            "Registered accounts and demonstration profiles are distinguished, and "
            "unverified origins are not presented as facts."
        )
        st.caption(
            "Regional research awaiting administrator review is not published as verified "
            "information. This local MVP does not process payments."
        )


elif role == "farmer":
    brand_header("Your farmer workspace", "Manage listings, prepare orders, and understand your sales.")
    if user.get("is_demo"):
        st.warning("Demonstration account: profile, inventory, orders, and prices are fictional examples.")
    st.markdown(f"## {active_page}")

    if active_page == "Dashboard":
        farmer_products = api("GET", "/products/mine") or []
        farmer_orders = api("GET", "/orders") or []
        analytics = api("GET", "/analytics/farmer") or {}
        pending_count = sum(order["status"] in {"pending", "accepted", "confirmed", "ready_for_pickup", "preparing"} for order in farmer_orders)
        completed_count = sum(order["status"] in {"completed", "delivered"} for order in farmer_orders)
        low_stock = [product for product in farmer_products if product["is_active"] and product["stock"] <= 5]
        metrics = st.columns(5)
        metrics[0].metric("Revenue", currency(analytics.get("revenue", 0)))
        metrics[1].metric("Active products", sum(product["is_active"] for product in farmer_products))
        metrics[2].metric("Pending orders", pending_count)
        metrics[3].metric("Completed orders", completed_count)
        metrics[4].metric("Low-stock items", len(low_stock))
        quick_cols = st.columns(4)
        quick_cols[0].info("Add products from the My products tab.")
        quick_cols[1].info(f"{len(farmer_orders)} order(s) to review.")
        quick_cols[2].info(f"{analytics.get('units_sold', 0)} units sold.")
        quick_cols[3].warning(f"{len(low_stock)} product(s) need restocking." if low_stock else "Inventory levels look good.")
        if farmer_orders:
            st.markdown("### Upcoming pickups")
            for order in sorted(farmer_orders, key=lambda row: row.get("pickup_date") or "9999-12-31")[:5]:
                with st.container(border=True):
                    left, center, right = st.columns([2, 1, 1])
                    left.markdown(f"**Order #{order['id']}**")
                    left.caption(f"Pickup date: {order.get('pickup_date') or 'To be arranged'}")
                    with center:
                        status_badge(order["status"])
                    right.markdown(f"### {currency(order['total'])}")

    if active_page in {"My products", "Add product"}:
        c1, c2 = st.columns([1, 2])
        with c1:
            with st.expander("Add a new listing", expanded=True):
                name = st.text_input("Product name")
                category = st.selectbox("Category", CATEGORIES)
                unit = st.selectbox("Unit", ["kg", "piece", "liter", "package"])
                price = st.number_input("Price per unit (€)", min_value=0.01, value=1.00, step=0.10)
                stock = st.number_input("Available quantity", min_value=0, value=10, step=1)
                village = st.text_input("Village or location", value="Peja")
                image_url = st.text_input("Image URL (optional)")
                product_image_file = st.file_uploader(
                    "Or upload a product photo (JPEG, PNG, WebP; up to 5 MB)",
                    type=["jpg", "jpeg", "png", "webp"],
                    key="new_product_image",
                )
                description = st.text_area("Description", key="new_product_description")
                if st.button("Publish listing", type="primary", use_container_width=True):
                    data = api("POST", "/products", json={
                        "name": name,
                        "category": category,
                        "unit": unit,
                        "price": price,
                        "stock": stock,
                        "village": village,
                        "image_url": image_url or None,
                        "description": description,
                    })
                    if data:
                        if product_image_file:
                            api(
                                "POST",
                                f"/products/{data['id']}/image",
                                files={"image": (
                                    product_image_file.name,
                                    product_image_file.getvalue(),
                                    product_image_file.type,
                                )},
                            )
                        st.success("Listing published.")
                        st.rerun()
        with c2:
            mine = api("GET", "/products/mine") or []
            if not mine:
                st.info("Publish your first product to start selling.")
            for product in mine:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1.2, 2.5, 1])
                    with c1:
                        product_image(product, height=140, key=f"farmer-inventory-{product['id']}")
                    with c2:
                        st.subheader(product["name"])
                        if product.get("is_demo"):
                            demo_badge("DEMO · fictional listing and price")
                            st.caption(f"{product['category']} · Demo price {currency(product['price'])} / {product['unit']}")
                        else:
                            st.write(product["description"])
                            st.caption(f"{product['category']} · {product['village']} · {currency(product['price'])} / {product['unit']}")
                    with c3:
                        st.metric("In stock", f"{product['stock']} {product['unit']}")
                        change = st.number_input("Stock change", -500, 500, 0, key=f"change_{product['id']}")
                        if st.button("Apply", key=f"stock_{product['id']}", use_container_width=True):
                            data = api("POST", f"/products/{product['id']}/stock", json={"quantity": change, "note": "Inventory update"})
                            if data:
                                st.rerun()
                        if st.button("Remove listing", key=f"delete_{product['id']}"):
                            if api("DELETE", f"/products/{product['id']}") is not None:
                                st.rerun()
                    with st.expander("Edit listing"):
                        with st.form(f"edit_product_{product['id']}"):
                            edit_name = st.text_input("Product name", value=product["name"])
                            edit_description = st.text_area("Description", value=product["description"])
                            edit_category = st.selectbox(
                                "Category", CATEGORIES,
                                index=CATEGORIES.index(product["category"]) if product["category"] in CATEGORIES else 0,
                            )
                            edit_price = st.number_input("Price (€)", min_value=0.01, value=float(product["price"]), step=0.1)
                            edit_unit = st.selectbox(
                                "Unit", ["kg", "piece", "liter", "package"],
                                index=["kg", "piece", "liter", "package"].index(product["unit"])
                                if product["unit"] in ["kg", "piece", "liter", "package"] else 0,
                            )
                            edit_location = st.text_input("Location", value=product.get("village") or "")
                            edit_image = st.text_input("Image URL", value=product.get("image_url") or "")
                            replacement_image = st.file_uploader(
                                "Replace product photo",
                                type=["jpg", "jpeg", "png", "webp"],
                                key=f"replace_image_{product['id']}",
                            )
                            edit_active = st.checkbox("Listing is available", value=product["is_active"])
                            save_product = st.form_submit_button("Save changes")
                        if save_product:
                            updated = api("PUT", f"/products/{product['id']}", json={
                                "name": edit_name,
                                "description": edit_description,
                                "category": edit_category,
                                "price": edit_price,
                                "unit": edit_unit,
                                "village": edit_location,
                                "image_url": edit_image or None,
                                "is_active": edit_active,
                            })
                            if updated:
                                if replacement_image:
                                    api(
                                        "POST",
                                        f"/products/{product['id']}/image",
                                        files={"image": (
                                            replacement_image.name,
                                            replacement_image.getvalue(),
                                            replacement_image.type,
                                        )},
                                    )
                                st.success("Listing updated.")
                                st.rerun()

    if active_page == "Manage orders":
        order_rows = api("GET", "/orders") or []
        if not order_rows:
            st.info("No incoming orders.")
        else:
            packing = []
            for order in order_rows:
                with st.container(border=True):
                    c1, c2, c3 = st.columns([1.4, 1.1, 1])
                    c1.subheader(f"Order #{order['id']}")
                    c2.markdown(f'<span class="status">{order["status"].replace("_", " ").title()}</span>', unsafe_allow_html=True)
                    if order.get("is_demo"):
                        demo_badge("DEMO ORDER")
                        c3.markdown(f"**Demo total:** {currency(order['total'])}")
                    else:
                        c3.markdown(f"### {currency(order['total'])}")
                    st.caption(f"Customer #{order['customer_id']} · Pickup: {order.get('pickup_date') or 'Not set'}")
                    transitions = {
                        "pending": ["accepted", "rejected"],
                        "accepted": ["ready_for_pickup", "rejected"],
                        "confirmed": ["accepted", "ready_for_pickup", "preparing", "delivered", "rejected"],
                        "preparing": ["ready_for_pickup", "delivered"],
                        "ready_for_pickup": ["completed", "delivered"],
                    }
                    options = [order["status"]] + transitions.get(order["status"], [])
                    if len(options) > 1:
                        next_status = st.selectbox(
                            "Update status",
                            options,
                            format_func=lambda value: value.replace("_", " ").title(),
                            key=f"status_select_{order['id']}",
                        )
                        if st.button(
                            "Save status", key=f"status_save_{order['id']}",
                            disabled=next_status == order["status"],
                        ):
                            data = api("PATCH", f"/orders/{order['id']}/status", json={"status": next_status})
                            if data:
                                st.success("Order status updated.")
                                st.rerun()
                    for item in order["items"]:
                        packing.append({
                            "Order reference": f"PM-{order['id']}",
                            "Product": f"Product #{item['product_id']}",
                            "Required quantity": item["quantity"],
                            "Pickup date": order.get("pickup_date") or "",
                            "Status": order["status"].replace("_", " ").title(),
                        })
            if packing:
                st.markdown("### Packing list")
                packing_df = pd.DataFrame(packing)
                st.dataframe(packing_df, use_container_width=True, hide_index=True)
                st.download_button(
                    "Export packing list CSV",
                    packing_df.to_csv(index=False).encode("utf-8"),
                    "pejamarket_packing_list.csv",
                    "text/csv",
                    use_container_width=True,
                )

    if active_page == "Sales analytics":
        data = api("GET", "/analytics/farmer") or {}
        c1, c2, c3 = st.columns(3)
        c1.metric("Revenue", currency(data.get("revenue", 0)))
        c2.metric("Units sold", data.get("units_sold", 0))
        c3.metric("Active listings", data.get("active_products", 0))
        rows = data.get("sales_by_category", [])
        if rows:
            df = pd.DataFrame(rows)
            fig = px.bar(df, x="category", y="units", title="Units sold by category",
                         color_discrete_sequence=["#2f6644"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sales analytics will appear after completed orders.")

    if active_page == "Farm Assistant":
        st.markdown("### AI Farm Assistant")
        st.caption("Ask about planting, soil, harvest preparation, storage, and sustainable farming.")
        tab_description, tab_category, tab_chat = st.tabs(["Product description", "Category suggestion", "Farm question"])
        with tab_description:
            product_name = st.text_input("Product name", key="ai_product_name")
            category_ai = st.selectbox("Category", CATEGORIES, key="ai_category")
            qualities = st.text_input("Qualities supplied by you")
            method = st.text_input("Farming method, if known")
            if st.button("Generate description"):
                result = api("POST", "/ai/product-description", json={
                    "product_name": product_name,
                    "category": category_ai,
                    "qualities": qualities,
                    "farming_method": method,
                })
                if result:
                    st.session_state.generated_product_description = result["description"]
                    st.session_state.generated_product_description_provider = result["provider"]
                    st.session_state.generated_description_key = (
                        st.session_state.get("generated_description_key", 0) + 1
                    )
                    st.rerun()
            generated_description = st.session_state.get("generated_product_description")
            if generated_description:
                description_key = f"generated_description_{st.session_state.get('generated_description_key', 0)}"
                edited_description = st.text_area(
                    "Review and edit this description",
                    value=generated_description,
                    height=160,
                    key=description_key,
                )
                st.caption(f"Source: {st.session_state.get('generated_product_description_provider', 'demo')}")
                st.code(edited_description, language=None)
                action_cols = st.columns(2)
                if action_cols[0].button("Use in a new listing", key="use_generated_description"):
                    st.session_state.product_description_draft = edited_description
                    st.success("Saved as your new-product description draft. Open My products to publish it.")
                if action_cols[1].button("Regenerate", key="regenerate_description"):
                    result = api("POST", "/ai/product-description", json={
                        "product_name": product_name,
                        "category": category_ai,
                        "qualities": qualities,
                        "farming_method": method,
                    })
                    if result:
                        st.session_state.generated_product_description = result["description"]
                        st.session_state.generated_product_description_provider = result["provider"]
                        st.session_state.generated_description_key += 1
                        st.rerun()
        with tab_category:
            ai_name = st.text_input("Product name", key="category_name")
            ai_description = st.text_area("Product description")
            if st.button("Suggest category"):
                result = api("POST", "/ai/category-suggestion", json={
                    "product_name": ai_name,
                    "description": ai_description,
                })
                if result:
                    st.success(f"Suggested category: {result['category']} · Unit: {result['unit']} · Title: {result['title']}")
                    st.caption(f"Source: {result['provider']}. Review and confirm these suggestions before using them.")
        with tab_chat:
            if st.button("Clear conversation", key="clear_farmer_ai"):
                st.session_state.ai_history["farmer"] = []
                st.rerun()
            for turn in st.session_state.ai_history["farmer"]:
                with st.chat_message(turn["role"]):
                    st.markdown(turn["text"])
                    if turn.get("provider"):
                        st.caption(f"Source: {turn['provider']}")
            question = st.text_area("Ask an agricultural question", height=120)
            if st.button("Ask", type="primary"):
                result = api("POST", "/ai/chat", json={"message": question})
                if result:
                    st.session_state.ai_history["farmer"].extend([
                        {"role": "user", "text": question},
                        {"role": "assistant", "text": result["reply"], "provider": result["provider"]},
                    ])
                    st.rerun()

    if active_page in {"Farm profile", "Settings"}:
        render_profile()

    if active_page == "Customer messages":
        st.info(
            "Direct customer-to-farmer messaging is not available yet. New order activity "
            "and customer pickup updates are visible in Manage Orders and Notifications."
        )

    if active_page == "Notifications":
        render_notifications()


else:
    st.markdown(f"## {active_page}")

    if active_page in {"Admin Overview", "Reports"}:
        data = api("GET", "/analytics/overview") or {}
        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Registered users", data.get("users", 0))
        c2.metric("Non-demo listings", data.get("products", 0))
        c3.metric("Non-demo orders", data.get("orders", 0))
        c4.metric("Non-demo order total", currency(data.get("revenue", 0)))
        st.caption("Demonstration accounts, products, prices, and orders are excluded from these platform totals.")
        sales = api("GET", "/analytics/admin/sales") or []
        if sales:
            df = pd.DataFrame(sales)
            fig = px.bar(df, x="category", y="revenue", title="Platform sales by category",
                         color_discrete_sequence=["#173f2a"])
            fig.update_layout(paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)")
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sales chart will appear when orders contain completed products.")

    if active_page == "Product Management":
        all_products = api("GET", "/products/mine") or api("GET", "/products") or []
        if not all_products:
            st.info("No listings are available.")
        for product in all_products:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1.2, 3, 1])
                with c1:
                    product_image(product, height=140, key=f"admin-listing-{product['id']}")
                c2.markdown(f"**{product['name']}**")
                c2.caption(f"{product['category']} · Farmer #{product['farmer_id']} · {product['stock']} {product['unit']}")
                if product.get("is_demo"):
                    c2.markdown('<span class="demo-badge">DEMO · fictional listing</span>', unsafe_allow_html=True)
                    c3.metric("Demo price", currency(product["price"]))
                else:
                    c3.metric("Price", currency(product["price"]))
                if st.button("Remove inappropriate listing", key=f"admin_remove_{product['id']}"):
                    if api("DELETE", f"/products/{product['id']}") is not None:
                        st.success("Listing removed.")
                        st.rerun()

    if active_page == "Orders":
        for order in api("GET", "/orders") or []:
            with st.container(border=True):
                c1, c2, c3 = st.columns([1.3, 1, 1])
                c1.subheader(f"Order #{order['id']}")
                c2.markdown(f'<span class="status">{order["status"].replace("_", " ").title()}</span>', unsafe_allow_html=True)
                c3.metric("Total", currency(order["total"]))
                if order.get("is_demo"):
                    demo_badge("DEMO ORDER · fictional transaction")
                st.caption(f"Customer #{order['customer_id']} · {order['delivery_address']}")

    if active_page == "User Management":
        users = api("GET", "/auth/users") or []
        if users:
            st.dataframe(pd.DataFrame(users), use_container_width=True, hide_index=True)
        else:
            st.info("User management is unavailable.")

    if active_page == "Customers":
        user_list = api("GET", "/auth/users") or []
        customers = [row for row in user_list if row["role"] == "customer"]
        if customers:
            st.dataframe(pd.DataFrame(customers), use_container_width=True, hide_index=True)
        else:
            st.info("No customers are registered.")

    if active_page == "Farmer Verification":
        st.info(
            "The current application provides a farmer directory but does not yet include "
            "a verification status or approval workflow."
        )
        farmer_list = api("GET", "/farmers") or []
        if farmer_list:
            rows = [{
                "Name": row["name"],
                "Account type": "Demonstration" if row.get("is_demo") else "Registered",
                "Farm": row.get("profile", {}).get("farm_name"),
                "Village": row.get("profile", {}).get("village"),
                "Products": row.get("product_count", 0),
                "Available": row.get("available_products", 0),
            } for row in farmer_list]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info("No farmers are registered.")

    if active_page in {"Local Data & Research", "Image & Source Review"}:
        render_research_admin()

    if active_page == "Settings":
        render_profile()
