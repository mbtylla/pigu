import csv
import requests
import re
from lxml import etree

INPUT_XML = "zuja.xml"
STOCK_CSV = "zujastock.csv"
TARGET_XML = "piguasortimentas.xml"
URL = "https://zuja.lt/index.php?route=feed/store/generate&filters=YToyOntzOjI0OiJmaWx0ZXJfY3VzdG9tZXJfZ3JvdXBfaWQiO3M6MjoiMTIiO3M6Mzoia2V5IjtzOjMyOiJjODFlNzI4ZDlkNGMyZjYzNmYwNjdmODljYzE0ODYyYyI7fQ==&key=c81e728d9d4c2f636f067f89cc14862c"

# 1. Parsisiunčiame XML iš ZUJA
r = requests.get(URL)
r.raise_for_status()
with open(INPUT_XML, "wb") as f:
    f.write(r.content)
print(f"[INFO] zuja.xml parsisiųstas.")

# 2. Generuojame zujastock.csv (EAN, Stock)
tree = etree.fromstring(r.content)
products = tree.findall(".//product")

with open(STOCK_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["EAN", "stock"])

    for p in products:
        ean = p.findtext("barcode")
        stock = p.findtext("total_quantity")

        if ean is not None and stock is not None:
            writer.writerow([ean.strip(), stock.strip()])

print(f"[INFO] {STOCK_CSV} sugeneruotas.")

# 3. Įkeliame CSV į dict
stock_dict = {}
with open(STOCK_CSV, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        ean = row["EAN"].strip()
        stock_dict[ean] = row["stock"].strip()

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

    stock_new = stock_dict[ean]

    # Pakeičiame stock reikšmę
    product_block = re.sub(
        r"(<stock>).*?(</stock>)",
        lambda m: f"{m.group(1)}{stock_new}{m.group(2)}",
        product_block,
        flags=re.DOTALL
    )

    return product_block

# Visų product blokų keitimas
xml_text_new = re.sub(
    r"<product>.*?</product>",
    update_stock,
    xml_text,
    flags=re.DOTALL
)

with open(TARGET_XML, "w", encoding="utf-8") as f:
    f.write(xml_text_new)

print(f"[INFO] piguasortimentas.xml atnaujintas pagal ZUJA likučius.")
