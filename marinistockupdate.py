import csv
import requests
import re
from lxml import etree

INPUT_XML = "marini-b2b.xml"
STOCK_CSV = "stock.csv"
TARGET_XML = "piguasortimentas.xml"
URL = "https://marini.pl/b2b/marini-b2b.xml"

STOCK_MAP = {
    "brak": 0,
    "mała ilość": 2,
    "średnia ilość": 5,
    "duża ilość": 15
}

def normalize_stock(value):
    if value is None:
        return 0
    value = value.strip().lower()
    return str(STOCK_MAP.get(value, value))

# 1. Parsisiunčiame XML
r = requests.get(URL)
r.raise_for_status()
with open(INPUT_XML, "wb") as f:
    f.write(r.content)
print(f"[INFO] {INPUT_XML} parsisiųstas.")

# 2. Generuojame stock.csv
tree = etree.fromstring(r.content)
b2b_entries = tree.findall(".//b2b")

with open(STOCK_CSV, "w", newline="", encoding="utf-8") as csvfile:
    import csv
    writer = csv.writer(csvfile)
    writer.writerow(["EAN", "stan"])
    for b2b in b2b_entries:
        ean = b2b.findtext("EAN")
        stan = b2b.findtext("stan")
        if ean and stan:
            normalized = normalize_stock(stan)
            writer.writerow([ean.strip(), normalized])
print(f"[INFO] {STOCK_CSV} sugeneruotas.")

# 3. Įkeliame stock.csv į dict
stock_dict = {}
with open(STOCK_CSV, newline="", encoding="utf-8") as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        stock_dict[row["EAN"].strip()] = row["stan"].strip()

# 4. Redaguojame TARGET_XML tik quantity pagal barcode
with open(TARGET_XML, "r", encoding="utf-8") as f:
    xml_text = f.read()

# Regex, kuris randa <product> bloką su barcode ir quantity
def update_stock(match):
    product_block = match.group(0)
    ean_match = re.search(r"<ean>(.*?)</ean>", product_block, re.DOTALL)
    if ean_match:
        ean = ean_match.group(1).strip()
        if ean in stock_dict:
            stock_new = stock_dict[ean]
            product_block = re.sub(
                r"(<stock>).*?(</stock>)",
                lambda m: f"{m.group(1)}{stock_new}{m.group(2)}",
                product_block,
                flags=re.DOTALL
            )
    return product_block

xml_text_new = re.sub(r"<product>.*?</product>", update_stock, xml_text, flags=re.DOTALL)

with open(TARGET_XML, "w", encoding="utf-8") as f:
    f.write(xml_text_new)

print(f"[INFO] {TARGET_XML} atnaujintas pagal stock.csv. CDATA kitur išliko nepakeisti.")
