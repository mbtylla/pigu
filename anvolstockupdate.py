import csv
import requests
import re
from lxml import etree

INPUT_XML = "anvol.xml"
STOCK_CSV = "anvolstock.csv"
TARGET_XML = "piguasortimentas.xml"
URL = "https://xml.anvol.eu/wholesale-lt-products.xml"

# 1. Parsisiunčiame XML
r = requests.get(URL)
r.raise_for_status()
with open(INPUT_XML, "wb") as f:
    f.write(r.content)
print(f"[INFO] anvol.xml parsisiųstas.")

# 2. Generuojame anvolstock.csv (EAN, Price, Stock)
tree = etree.fromstring(r.content)
products = tree.findall(".//product")

with open(STOCK_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["EAN", "price", "stock_ee"])

    for p in products:
        ean = p.findtext("ean")
        price = p.findtext("price")
        stock_ee = p.findtext("stocks/stock_ee")

        if ean and price and stock_ee:
            writer.writerow([ean.strip(), price.strip(), stock_ee.strip()])

print(f"[INFO] {STOCK_CSV} sugeneruotas.")

# 3. Įkeliame CSV į dict
stock_dict = {}
with open(STOCK_CSV, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        ean = row["EAN"].strip()
        stock_dict[ean] = {
            "price": float(row["price"]),
            "stock": row["stock_ee"].strip()
        }

# 4. Redaguojame pigu XML
with open(TARGET_XML, "r", encoding="utf-8") as f:
    xml_text = f.read()

# Produkto blokų keitimo funkcija
def update_stock(match):
    product_block = match.group(0)

    ean_match = re.search(r"<ean>(.*?)</ean>", product_block, re.DOTALL)
    if not ean_match:
        return product_block

    ean = ean_match.group(1).strip()

    if ean not in stock_dict:
        return product_block

    supplier_price = stock_dict[ean]["price"]
    supplier_stock = stock_dict[ean]["stock"]

    # Taisyklė: jei ANVOL kaina < 7 €, stock = 0
    if supplier_price < 7:
        stock_new = "0"
    else:
        stock_new = supplier_stock

    product_block = re.sub(
        r"(<stock>).*?(</stock>)",
        lambda m: f"{m.group(1)}{stock_new}{m.group(2)}",
        product_block,
        flags=re.DOTALL
    )

    return product_block

xml_text_new = re.sub(
    r"<product>.*?</product>",
    update_stock,
    xml_text,
    flags=re.DOTALL
)

with open(TARGET_XML, "w", encoding="utf-8") as f:
    f.write(xml_text_new)

print(f"[INFO] piguasortimentas.xml atnaujintas pagal ANVOL kainas ir likučius.")
