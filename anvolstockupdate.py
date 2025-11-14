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

# 2. Generuojame anvolstock.csv
tree = etree.fromstring(r.content)
products = tree.findall(".//product")

with open(STOCK_CSV, "w", newline="", encoding="utf-8") as csvfile:
    writer = csv.writer(csvfile)
    writer.writerow(["EAN", "stock_ee"])

    for p in products:
        ean = p.findtext("ean")
        stock_ee = p.findtext("stocks/stock_ee")  # <-- TEISINGAS KELIAS

        if ean and stock_ee:
            writer.writerow([ean.strip(), stock_ee.strip()])

print(f"[INFO] {STOCK_CSV} sugeneruotas.")

# 3. Įkeliame stock.csv į dict
stock_dict = {}
with open(STOCK_CSV, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        stock_dict[row["EAN"].strip()] = row["stock_ee"].strip()

# 4. Redaguojame TARGET_XML tik quantity pagal barcode
with open(TARGET_XML, "r", encoding="utf-8") as f:
    xml_text = f.read()

# Regex, kuris randa <product> bloką su barcode ir stock
def update_stock(match):
    product_block = match.group(0)

    # Surandame EAN
    ean_match = re.search(r"<ean>(.*?)</ean>", product_block, re.DOTALL)
    if not ean_match:
        return product_block

    ean = ean_match.group(1).strip()

    # Surandame kainą
    price_match = re.search(r"<price>(.*?)</price>", product_block, re.DOTALL)
    price_value = None
    if price_match:
        try:
            price_value = float(price_match.group(1).strip())
        except:
            price_value = None

    # Jei kaina < 10 €, visada rodomas 0 likutis
    if price_value is not None and price_value < 10:
        stock_new = "0"
    else:
        stock_new = stock_dict.get(ean)
        if stock_new is None:
            return product_block  # Nėra ANVOL likučio šiam EAN

    # Pakeičiame stock reikšmę
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

print(f"[INFO] piguasortimentas.xml atnaujintas pagal anvolstock.csv.")
