import csv
import re

PRICE_CSV = "terminaikainos.csv"
TARGET_XML = "piguasortimentas.xml"

product_info = {}
with open(PRICE_CSV, newline='', encoding='utf-8') as csvfile:
    reader = csv.DictReader(csvfile, delimiter=';')  # <- svarbu
    for row in reader:
        ean = row.get("ean", "").strip()
        price_after_discount_lt = row.get("price_after_discount_lt")
        collection_hours_lt = row.get("collection_hours_lt", "").strip()
        
        if ean:
            product_info[ean] = {
                "price_after_discount_lt": price_after_discount_lt,
                "collection_hours_lt": collection_hours_lt
            }

# 4. Redaguojame TARGET_XML tik quantity pagal barcode
with open(TARGET_XML, "r", encoding="utf-8") as f:
    xml_text = f.read()



# Regex, kuris randa <product> bloką su barcode ir quantity
def update_product(match):
    product_block = match.group(0)
    ean_match = re.search(r"<ean>(.*?)</ean>", product_block, re.DOTALL)
    if ean_match:
        ean = ean_match.group(1).strip()
        if ean in product_info:
            info = product_info[ean]
            price_after_discount_lt_new = info["price_after_discount_lt"]
            collection_hours_lt_new = info["collection_hours_lt"]

            # Atnaujinam <price_after_discount_lt>
            product_block = re.sub(
                r"(<price_after_discount_lt>).*?(</price_after_discount_lt>)",
                lambda m: f"{m.group(1)}{price_after_discount_lt_new}{m.group(2)}",
                product_block,
                flags=re.DOTALL
            )

            # Atnaujinam <collection_hours_lt>
            product_block = re.sub(
                r"(<collection_hours_lt>).*?(</collection_hours_lt>)",
                lambda m: f"{m.group(1)}{collection_hours_lt_new}{m.group(2)}",
                product_block,
                flags=re.DOTALL
            )

    return product_block


xml_text_new = re.sub(r"<product>.*?</product>", update_product, xml_text, flags=re.DOTALL)

with open(TARGET_XML, "w", encoding="utf-8") as f:
    f.write(xml_text_new)

print(f"[INFO] {TARGET_XML} atnaujintas pagal price.csv. CDATA kitur išliko nepakeisti.")
