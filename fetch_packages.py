import imaplib
import email
from email.header import decode_header
import json
import os
import re
import sys
from datetime import datetime, timedelta


CARRIERS = {
    "auto-confirm@amazon.com": "Amazon",
    "shipment-tracking@amazon.com": "Amazon",
    "ship-confirm@amazon.com": "Amazon",
    "delivery-tracking@amazon.com": "Amazon",
    "order-update@amazon.com": "Amazon",
    "tracking@ups.com": "UPS",
    "pkginfo@ups.com": "UPS",
    "noreply@ups.com": "UPS",
    "fedex@fedex.com": "FedEx",
    "trk@fedex.com": "FedEx",
    "noreply@fedex.com": "FedEx",
    "usps@email.usps.com": "USPS",
    "auto-reply@usps.com": "USPS",
    "noreply@usps.com": "USPS",
}

OUT_FOR_DELIVERY_KEYWORDS = [
    "out for delivery",
    "arriving today",
    "delivery today",
]

SHIPPED_KEYWORDS = [
    "your order has shipped",
    "arriving tomorrow",
    "delivery tomorrow",
    "has shipped",
    "on its way",
]


def load_config(config_path):
    with open(config_path, "r") as f:
        return json.load(f)


def decode_str(s):
    if s is None:
        return ""
    parts = decode_header(s)
    result = ""
    for part, enc in parts:
        if isinstance(part, bytes):
            result += part.decode(enc or "utf-8", errors="replace")
        else:
            result += part
    return result


def extract_email_address(from_str):
    if "<" in from_str:
        return from_str.split("<")[1].strip(">").strip().lower()
    return from_str.strip().lower()


def get_body(msg):
    if msg.is_multipart():
        for part in msg.walk():
            if part.get_content_type() == "text/plain":
                try:
                    return part.get_payload(decode=True).decode("utf-8", errors="replace")
                except Exception:
                    pass
    else:
        try:
            return msg.get_payload(decode=True).decode("utf-8", errors="replace")
        except Exception:
            pass
    return ""


def extract_item(subject, body):
    match = re.search(r'["](.*?)["|]', subject)
    if match:
        item = match.group(1).strip()
        if len(item) > 3:
            return item[:35] + "..." if len(item) > 35 else item
    return None


def fetch_all_packages(config):
    accounts = config.get("accounts", [])
    lookback_days = config.get("lookbackDays", 1)
    max_packages = config.get("maxPackages", 5)

    seen = {}
    packages = []

    since_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%d-%b-%Y")

    for account in accounts:
        server = account.get("server", "")
        username = account.get("username", "")
        password = account.get("password", "")

        if not server or not username or not password:
            print(f"Skipping account with missing credentials: {username or '(no username)'}")
            continue

        try:
            mail = imaplib.IMAP4_SSL(server)
            mail.login(username, password)
            mail.select("inbox")

            _, messages = mail.search(None, f"SINCE {since_date}")
            email_ids = messages[0].split()

            for eid in reversed(email_ids):
                _, msg_data = mail.fetch(eid, "(BODY.PEEK[])")
                msg = email.message_from_bytes(msg_data[0][1])
                sender = extract_email_address(decode_str(msg["From"]))
                subject = decode_str(msg["Subject"]).strip()
                body = get_body(msg)
                subject_lower = subject.lower()
                body_lower = body.lower()

                carrier_name = CARRIERS.get(sender)
                if not carrier_name:
                    continue

                item = extract_item(subject, body)
                dedup_key = (carrier_name, item)

                if subject_lower.startswith("delivered:") or "your package was delivered" in body_lower:
                    if dedup_key in seen:
                        packages[seen[dedup_key]]["status"] = "Delivered"
                    else:
                        seen[dedup_key] = len(packages)
                        packages.append({
                            "carrier": carrier_name,
                            "status": "Delivered",
                            "item": item,
                        })
                    continue

                combined = subject_lower + " " + body_lower

                if any(k in combined for k in OUT_FOR_DELIVERY_KEYWORDS):
                    status_text = "Out for Delivery"
                elif any(k in combined for k in SHIPPED_KEYWORDS):
                    status_text = "Shipped"
                else:
                    continue

                if dedup_key in seen:
                    current = packages[seen[dedup_key]]["status"]
                    if current != "Delivered" and status_text == "Out for Delivery":
                        packages[seen[dedup_key]]["status"] = "Out for Delivery"
                else:
                    seen[dedup_key] = len(packages)
                    packages.append({
                        "carrier": carrier_name,
                        "status": status_text,
                        "item": item,
                    })

            mail.logout()

        except Exception as e:
            print(f"Error ({username}): {e}")

    return packages[:max_packages]


def main():
    if len(sys.argv) < 2:
        config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "accounts_config.json")
    else:
        config_path = sys.argv[1]

    if not os.path.exists(config_path):
        print(f"Config file not found: {config_path}")
        # Write empty result
        output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packages_data.json")
        with open(output_path, "w") as f:
            json.dump([], f)
        return

    config = load_config(config_path)
    packages = fetch_all_packages(config)

    output_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "packages_data.json")
    with open(output_path, "w") as f:
        json.dump(packages, f)

    print(f"Packages: {packages}")


if __name__ == "__main__":
    main()
