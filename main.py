import base64
import csv
import glob
import json
import os
import sys
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from groq import Groq

load_dotenv()

MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"
RECEIPT_IMAGE_PATH = "dataset/receipts/1164-receipt.jpg"
BANK_STATEMENTS_GLOB = "dataset/bank_statements/*.csv"
AMOUNT_TOLERANCE = Decimal("0.01")


def image_to_data_url(path: str) -> str:
    with open(path, "rb") as file:
        b64 = base64.b64encode(file.read()).decode("utf-8")
    return f"data:image/jpeg;base64,{b64}"


def to_decimal(value: Any) -> Optional[Decimal]:
    if value is None:
        return None
    try:
        normalized_value = str(value).strip().replace(",", ".")
        return Decimal(normalized_value)
    except (InvalidOperation, TypeError, ValueError):
        return None


def load_bank_transactions(csv_glob: str = BANK_STATEMENTS_GLOB) -> List[Dict[str, Any]]:
    transactions: List[Dict[str, Any]] = []
    for csv_path in sorted(glob.glob(csv_glob)):
        with open(csv_path, "r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            for row in reader:
                row_amount = to_decimal(row.get("amount"))
                if row_amount is None:
                    continue

                row_currency = (row.get("currency") or "").strip().upper()
                transactions.append(
                    {
                        "date": row.get("date"),
                        "amount": float(row_amount),
                        "currency": row_currency,
                        "vendor": row.get("vendor"),
                        "source": row.get("source"),
                        "statement_file": os.path.basename(csv_path),
                    }
                )
    return transactions


def match_bank_transactions(
    extracted_ticket: Dict[str, Any], bank_transactions: List[Dict[str, Any]]
) -> Dict[str, Any]:
    receipt_amount = to_decimal(extracted_ticket.get("total_ttc"))
    receipt_currency = (extracted_ticket.get("currency") or "").strip().upper()

    if receipt_amount is None:
        return {"match_strategy": "none", "matched_transactions": []}

    amount_matches: List[Dict[str, Any]] = []
    exact_currency_matches: List[Dict[str, Any]] = []
    for tx in bank_transactions:
        tx_amount = to_decimal(tx.get("amount"))
        tx_currency = (tx.get("currency") or "").strip().upper()
        if tx_amount is None:
            continue

        if abs(tx_amount - receipt_amount) <= AMOUNT_TOLERANCE:
            enriched_tx = {
                **tx,
                "currency_match": bool(receipt_currency) and tx_currency == receipt_currency,
            }
            amount_matches.append(enriched_tx)
            if enriched_tx["currency_match"]:
                exact_currency_matches.append(enriched_tx)

    if exact_currency_matches:
        return {
            "match_strategy": "amount_and_currency",
            "matched_transactions": exact_currency_matches,
        }

    if amount_matches:
        return {"match_strategy": "amount_only", "matched_transactions": amount_matches}

    return {"match_strategy": "none", "matched_transactions": []}


def analyze_receipt_with_ai(image_path: str, model: str = MODEL) -> Dict[str, Any]:
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    image_data_url = image_to_data_url(image_path)

    completion = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "Tu extrais des tickets de caisse. Retourne uniquement un JSON valide.",
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            "Lis ce ticket et renvoie ce JSON exact: "
                            '{"merchant": string|null, "date": string|null, '
                            '"total_ttc": number|null, "currency": string|null, '
                            '"payment_method": string|null, "raw_text": string}'
                        ),
                    },
                    {
                        "type": "image_url",
                        "image_url": {"url": image_data_url},
                    },
                ],
            },
        ],
        temperature=0,
        response_format={"type": "json_object"},
        max_completion_tokens=1024,
        top_p=1,
        stream=False,
    )

    content = completion.choices[0].message.content
    return json.loads(content)


def analyze_and_match_receipt(
    image_path: str, csv_glob: str = BANK_STATEMENTS_GLOB
) -> Dict[str, Any]:
    extracted_ticket = analyze_receipt_with_ai(image_path)
    bank_transactions = load_bank_transactions(csv_glob)
    matching_data = match_bank_transactions(extracted_ticket, bank_transactions)
    matches = matching_data["matched_transactions"]

    return {
        "receipt_analysis": extracted_ticket,
        "matching": {
            "matched_count": len(matches),
            "match_strategy": matching_data["match_strategy"],
            "matched_transactions": matches,
        },
    }


def main() -> None:
    image_path = sys.argv[1] if len(sys.argv) > 1 else RECEIPT_IMAGE_PATH
    result = analyze_and_match_receipt(image_path=image_path, csv_glob=BANK_STATEMENTS_GLOB)
    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()