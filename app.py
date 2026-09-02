from __future__ import annotations
import hashlib
import os
import re
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
DATA_DIR = Path(os.getenv("DATA_DIR", str(BASE_DIR / "data")))
THUMB_DIR = DATA_DIR / "thumbs"
DB_PATH = DATA_DIR / "offers.sqlite3"
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "")
DATA_DIR.mkdir(parents=True, exist_ok=True)
THUMB_DIR.mkdir(parents=True, exist_ok=True)

STORE = {"name": "REWE Vigheshan Gahndi oHG", "address": "Industriestraße 40, 65439 Flörsheim-Weilbach", "market_id": "240367"}
OFFERS_URL = "https://www.rewe.de/angebote/floersheim-weilbach/240367/rewe-markt-industriestrasse-40/"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; REWE-Preisarchiv/1.0)", "Accept-Language": "de-DE,de;q=0.9,en;q=0.7"}
app = FastAPI(title="REWE Preisarchiv", version="1.0")

def db():
    conn = sqlite3.connect(DB_PATH); conn.row_factory = sqlite3.Row; return conn

def init_db():
    with closing(db()) as con:
        con.executescript("""
        PRAGMA journal_mode=WAL;
        CREATE TABLE IF NOT EXISTS products (id INTEGER PRIMARY KEY AUTOINCREMENT, product_key TEXT UNIQUE NOT NULL, brand TEXT, name TEXT NOT NULL, variant TEXT, quantity TEXT, category TEXT, image_url TEXT, thumb_path TEXT, created_at TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS price_observations (id INTEGER PRIMARY KEY AUTOINCREMENT, product_id INTEGER NOT NULL, observed_at TEXT NOT NULL, valid_from TEXT, valid_to TEXT, price REAL NOT NULL, normal_price REAL, unit_price TEXT, source_url TEXT, source_type TEXT, page_number INTEGER, FOREIGN KEY(product_id) REFERENCES products(id));
        CREATE INDEX IF NOT EXISTS idx_price_product ON price_observations(product_id, observed_at);
        """); con.commit()

def normalize(s): return re.sub(r"\s+", " ", (s or "")).strip()
def product_key(brand, name, variant, quantity):
    raw = "|".join([normalize(brand).lower(), normalize(name).lower(), normalize(variant).lower(), normalize(quantity).lower()]); return hashlib.sha1(raw.encode("utf-8")).hexdigest()
def parse_price(text):
    if not text: return None
    m = re.search(r"(?<!\d)(\d{1,3}(?:[.,]\d{2}))(?:\s*€)?(?!\d)", text)
    if not m: return None
    try: return float(m.group(1).replace(",", "."))
    except ValueError: return None

def download_thumbnail(url, key):
    if not url: return None
    try:
        r=requests.get(url,headers=HEADERS,timeout=15); r.raise_for_status()
        if "image" not in (r.headers.get("content-type") or "").lower(): return None
        ext=Path(urlparse(url).path).suffix.lower(); ext=ext if ext in (".jpg",".jpeg",".png",".webp") else ".jpg"
        filename=f"{key[:16]}{ext}"; (THUMB_DIR/filename).write_bytes(r.content); return f"/thumbs/{filename}"
    except Exception: return None

def upsert_offer(offer, valid_from=None, valid_to=None, observed_at=None):
    observed_at=observed_at or datetime.now(timezone.utc).isoformat(); key=product_key(offer.get("brand"),offer.get("name"),offer.get("variant"),offer.get("quantity"))
    with closing(db()) as con:
        row=con.execute("SELECT * FROM products WHERE product_key=?",(key,)).fetchone(); thumb=row["thumb_path"] if row else None
        if not thumb and offer.get("image_url"): thumb=download_thumbnail(offer.get("image_url"),key)
        if row:
            con.execute("UPDATE products SET brand=COALESCE(?,brand),name=?,variant=COALESCE(?,variant),quantity=COALESCE(?,quantity),category=COALESCE(?,category),image_url=COALESCE(?,image_url),thumb_path=COALESCE(?,thumb_path) WHERE id=?",(offer.get("brand"),offer["name"],offer.get("variant"),offer.get("quantity"),offer.get("category"),offer.get("image_url"),thumb,row["id"])); pid=row["id"]
        else:
            cur=con.execute("INSERT INTO products (product_key,brand,name,variant,quantity,category,image_url,thumb_path,created_at) VALUES (?,?,?,?,?,?,?,?,?)",(key,offer.get("brand"),offer["name"],offer.get("variant"),offer.get("quantity"),offer.get("category"),offer.get("image_url"),thumb,observed_at)); pid=cur.lastrowid
        same=con.execute("SELECT id FROM price_observations WHERE product_id=? AND substr(observed_at,1,10)=substr(?,1,10) AND price=? AND COALESCE(source_url,'')=COALESCE(?,'')",(pid,observed_at,offer["price"],offer.get("source_url"))).fetchone()
        if not same: con.execute("INSERT INTO price_observations (product_id,observed_at,valid_from,valid_to,price,normal_price,unit_price,source_url,source_type,page_number) VALUES (?,?,?,?,?,?,?,?,?,?)",(pid,observed_at,valid_from,valid_to,offer["price"],offer.get("normal_price"),offer.get("unit_price"),offer.get("source_url"),offer.get("source_type","web"),offer.get("page_number")))
        con.commit()

def extract_rewe_offers_html(html, source_url):
    soup=BeautifulSoup(html,"html.parser"); offers=[]; seen=set()
    for h in soup.find_all(["h2","h3","h4"]):
        name=normalize(h.get_text(" ",strip=True)); low=name.lower()
        if not name or len(name)<3 or any(x in low for x in ["angebote","bonus","obst und gemüse","kühlung","tiefkühl","frühstück","kochen und backen","süßes und salziges","bier","haushalt","drogerie","wein und spirituosen","alkoholfreie getränke"]): continue
        card=h
        for _ in range(5):
            if card.parent: card=card.parent
        text=normalize(card.get_text(" ",strip=True)); price=parse_price(text)
        if price is None: continue
        quantity=None; qm=re.search(r"(?:je\s+)?((?:\d+\s*x\s*)?\d+(?:[.,]\d+)?\s*(?:kg|g|l|ml|cl|Stück|St\.|Pckg\.|Becher|Glas|Btl\.|Fl\.-Kasten))",text,re.I)
        if qm: quantity=normalize(qm.group(1))
        unit=None; um=re.search(r"\(1\s*(?:kg|l)\s*=\s*([0-9.,]+\s*€)\)",text,re.I)
        if um: unit=normalize(um.group(1))
        img_url=None; img=card.find("img")
        if img:
            for attr in ("src","data-src","data-lazy-src"):
                val=img.get(attr)
                if val and not val.startswith("data:"): img_url=urljoin(source_url,val); break
        k=(name.lower(),price,quantity or "")
        if k in seen: continue
        seen.add(k); offers.append({"brand":None,"name":name,"variant":None,"quantity":quantity,"price":price,"unit_price":unit,"category":None,"image_url":img_url,"source_url":source_url,"source_type":"rewe_market_page"})
    return offers

def fetch_rewe_offers():
    errors=[]
    try:
        r=requests.get(OFFERS_URL,headers=HEADERS,timeout=25); r.raise_for_status(); offers=extract_rewe_offers_html(r.text,OFFERS_URL)
        if len(offers)>=5: return offers,"requests",errors
    except Exception as exc: errors.append(f"requests: {exc}")
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True); page=browser.new_page(locale="de-DE"); page.goto(OFFERS_URL,wait_until="networkidle",timeout=60000); page.evaluate("window.scrollTo(0, document.body.scrollHeight)"); page.wait_for_timeout(1200); html=page.content(); browser.close()
        return extract_rewe_offers_html(html,OFFERS_URL),"playwright",errors
    except Exception as exc: errors.append(f"playwright: {exc}")
    return [],"failed",errors

def seed_demo():
    demo=[("2026-08-24T08:00:00+00:00",[{"name":"Barilla Pasta Sauce","quantity":"400 g","price":2.29,"category":"Saucen"},{"name":"Dr. Oetker Ristorante Pizza Salame","quantity":"320 g","price":1.99,"category":"Tiefkühlkost"},{"name":"Beck’s Pils","quantity":"20 x 0,5 l","price":11.99,"category":"Bier"}]),("2026-08-31T08:00:00+00:00",[{"name":"Barilla Pasta Sauce","quantity":"400 g","price":1.99,"category":"Saucen"},{"name":"Dr. Oetker Ristorante Pizza Salame","quantity":"320 g","price":1.79,"category":"Tiefkühlkost"},{"name":"Beck’s Pils","quantity":"20 x 0,5 l","price":10.99,"category":"Bier"},{"name":"Kinder Bueno","quantity":"10 x 21,5 g","price":2.99,"category":"Süßigkeiten"},{"name":"Funny-frisch Ofen Chips","quantity":"115 g","price":1.11,"category":"Snacks"}])]
    with closing(db()) as con:
        if con.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]: return
    for observed,offers in demo:
        for o in offers: o.update({"source_url":OFFERS_URL,"source_type":"demo"}); upsert_offer(o,"2026-08-31","2026-09-06",observed_at=observed)

def product_rows():
    with closing(db()) as con:
        rows=con.execute("""SELECT p.*,po.price AS current_price,po.unit_price AS current_unit_price,po.observed_at AS current_observed_at,po.source_url AS current_source_url,COUNT(DISTINCT printf('%.4f',ph.price)) AS distinct_price_count,COUNT(ph.id) AS observation_count,MIN(ph.price) AS min_price,MAX(ph.price) AS max_price FROM products p JOIN price_observations po ON po.id=(SELECT id FROM price_observations x WHERE x.product_id=p.id ORDER BY x.observed_at DESC,x.id DESC LIMIT 1) JOIN price_observations ph ON ph.product_id=p.id GROUP BY p.id ORDER BY p.category,p.name""").fetchall(); return [dict(r) for r in rows]

@app.on_event("startup")
def startup(): init_db(); seed_demo()
@app.get("/")
def index(): return FileResponse(STATIC_DIR/"index.html")
@app.get("/api/status")
def status():
    with closing(db()) as con: p=con.execute("SELECT COUNT(*) c FROM products").fetchone()["c"]; obs=con.execute("SELECT COUNT(*) c FROM price_observations").fetchone()["c"]; last=con.execute("SELECT MAX(observed_at) d FROM price_observations").fetchone()["d"]
    return {"store":STORE,"products":p,"observations":obs,"last_update":last}
@app.get("/api/products")
def products(search:str="",category:str=""):
    rows=product_rows()
    if search:
        q=search.lower(); rows=[r for r in rows if q in " ".join([r.get("brand") or "",r.get("name") or "",r.get("variant") or "",r.get("quantity") or ""]).lower()]
    if category: rows=[r for r in rows if (r.get("category") or "")==category]
    return rows
@app.get("/api/categories")
def categories():
    with closing(db()) as con: return [dict(r) for r in con.execute("SELECT category,COUNT(*) count FROM products WHERE category IS NOT NULL AND category<>'' GROUP BY category ORDER BY category").fetchall()]
@app.get("/api/products/{product_id}/history")
def history(product_id:int):
    with closing(db()) as con:
        prod=con.execute("SELECT * FROM products WHERE id=?",(product_id,)).fetchone()
        if not prod: raise HTTPException(404,"Produkt nicht gefunden")
        rows=con.execute("SELECT observed_at,valid_from,valid_to,price,normal_price,unit_price,source_url,source_type,page_number FROM price_observations WHERE product_id=? ORDER BY observed_at ASC,id ASC",(product_id,)).fetchall()
    return {"product":dict(prod),"history":[dict(r) for r in rows]}
class ManualOffer(BaseModel):
    name:str; price:float; brand:str|None=None; variant:str|None=None; quantity:str|None=None; category:str|None=None; image_url:str|None=None; valid_from:str|None=None; valid_to:str|None=None

def require_admin(request:Request):
    if ADMIN_TOKEN and request.headers.get("x-admin-token","")!=ADMIN_TOKEN: raise HTTPException(401,"Admin-Token fehlt oder ist falsch")
@app.post("/api/offers/manual")
def manual(offer:ManualOffer,request:Request):
    require_admin(request); data=offer.model_dump(); vf=data.pop("valid_from"); vt=data.pop("valid_to"); data["source_type"]="manual"; data["source_url"]=None; upsert_offer(data,vf,vt); return {"ok":True}
@app.post("/api/update")
def update(request:Request):
    require_admin(request); offers,mode,errors=fetch_rewe_offers()
    if not offers: return JSONResponse(status_code=502,content={"ok":False,"mode":mode,"saved":0,"errors":errors,"message":"Keine Angebote zuverlässig erkannt. Demodaten bleiben erhalten."})
    for o in offers: upsert_offer(o)
    return {"ok":True,"mode":mode,"saved":len(offers),"errors":errors}
@app.post("/api/reset-demo")
def reset_demo(request:Request):
    require_admin(request)
    with closing(db()) as con: con.execute("DELETE FROM price_observations"); con.execute("DELETE FROM products"); con.commit()
    seed_demo(); return {"ok":True}
@app.get("/health")
def health(): return {"status":"ok","database":str(DB_PATH),"store":STORE["market_id"]}
@app.get("/manifest.webmanifest")
def manifest(): return FileResponse(STATIC_DIR/"manifest.webmanifest",media_type="application/manifest+json")
app.mount("/thumbs",StaticFiles(directory=THUMB_DIR),name="thumbs")
app.mount("/static",StaticFiles(directory=STATIC_DIR),name="static")
