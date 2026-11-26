import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.llm import heuristic_extract

SAMPLES = [
    {
        "name": "Acme standard",
        "text": """
Supplier: Acme Technologies
Invoice Number: INV-2026-001
Invoice Date: 2026-10-28
Currency: INR
PO Number: PO-4412
Total Amount: 1125000
""",
        "expected": {"invoiceNumber": "INV-2026-001", "supplierName_contains": "Acme", "currency": "INR", "totalAmount": 1125000.0},
    },
    {
        "name": "Vertex missing fields",
        "text": """
Supplier: Vertex Solutions
Invoice Number: INV-2026-003
Total Amount: 186200
""",
        "expected": {"invoiceNumber": "INV-2026-003", "currency": None},
    },
]


def run():
    correct = 0
    total = 0
    for sample in SAMPLES:
        inv = heuristic_extract(sample["text"])
        exp = sample["expected"]
        ok = True
        for key, val in exp.items():
            if key.endswith("_contains"):
                field = key.replace("_contains", "")
                actual = getattr(inv, field, None)
                if not (actual and val.lower() in str(actual).lower()):
                    ok = False
            else:
                if getattr(inv, key, None) != val:
                    ok = False
        total += len(exp)
        # count per-field
        for key in exp:
            k = key.replace("_contains", "")
            val = exp[key]
            actual = getattr(inv, k, None)
            if key.endswith("_contains"):
                field_ok = bool(actual and val.lower() in str(actual).lower())
            else:
                field_ok = (actual == val)
            if field_ok:
                correct += 1
        print(f"{sample['name']}: {'PASS' if ok else 'PARTIAL'} -> {inv.model_dump(include={'invoiceNumber','supplierName','currency','totalAmount'})}")
    accuracy = (correct / total * 100) if total else 0.0
    print(f"\nField accuracy: {correct}/{total} = {accuracy:.1f}%")


if __name__ == "__main__":
    run()