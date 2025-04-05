import csv
import random
import time
import os
from datetime import datetime
from faker import Faker

fake = Faker()

CSV_FILE = "./../data/prodtest.csv"

HEADER = [
    "customer_account_number",
    "to_recipient_customer_account",
    "old_balance",
    "transaction_amount",
    "new_balance",
    "tp_recipient_customer_account_balance",
    "transaction_time_in_ms",
    "transaction_frequency",
    "average_transaction_amount",
    "account_age_days",
    "method_of_transaction",
    "transaction_currency",
    "location_data",
    "device_used",
    "kyc_status",
    "label_for_fraud",
    "smurfing_indicator",
    "previous_fraud_flag",
    "transaction_id",
    "timestamp",
    "IFSC CODE",
    "IP ADDRESS",
    "MAC address",
    "NARRATION",
    "ECOMMERCE PLATFORM"
]

# Predefined reusable values
customer_pool = [random.randint(10000, 99999) for _ in range(25)]  # 25 unique customers
devices = ["ATM", "Mobile", "Laptop", "Desktop", "POS", "Tablet"]
kyc_statuses = ["FULL", "PARTIAL", "NONE"]
ecommerce_platforms = ["null", "Amazon", "Flipkart", "eBay", "Walmart", "Etsy", "Shopify", "Target", "Best Buy"]
ifsc_codes = ["HDFC0001234", "SBIN0000234", "ICIC0000456", "AXIS0000312", "SBIN0001234", "ICIC0000889"]
methods = list(range(0, 9))

def generate_ip():
    return ".".join(str(random.randint(0, 255)) for _ in range(4))

def generate_mac():
    return ":".join(format(random.randint(0, 255), '02X') for _ in range(6))

def generate_row(transaction_id_num):
    acc_num = random.choice(customer_pool)  # Pick customer randomly
    recipient_acc = random.randint(10000, 99999)
    old_balance = round(random.uniform(10000, 150000), 2)
    txn_amount = round(random.uniform(500, 50000), 2)
    new_balance = round(old_balance - txn_amount, 2)
    recipient_balance = round(random.uniform(10000, 100000), 2)
    txn_time_ms = random.randint(400, 1000)
    txn_freq = random.randint(1, 10)
    avg_txn = round(random.uniform(-3000, 3000), 2)
    account_age = random.randint(100, 3000)
    method = random.choice(methods)
    currency = "INR"
    location = fake.country()
    device = random.choice(devices)
    kyc = random.choice(kyc_statuses)
    label_fraud = random.randint(0, 1)
    smurf = random.randint(0, 1)
    prev_fraud = random.randint(0, 1)
    txn_id = f"T{transaction_id_num:08d}"
    timestamp = datetime.now().strftime("%d/%m/%Y %H:%M:%S")
    ifsc = random.choice(ifsc_codes)
    ip = generate_ip()
    mac = generate_mac()
    ecommerce = random.choice(ecommerce_platforms)
    narration = f"User purchased from {ecommerce}" if ecommerce != "null" else "User made a normal transfer"

    return [
        acc_num, recipient_acc, old_balance, txn_amount, new_balance,
        recipient_balance, txn_time_ms, txn_freq, avg_txn, account_age,
        method, currency, location, device, kyc,
        label_fraud, smurf, prev_fraud, txn_id, timestamp,
        ifsc, ip, mac, narration, ecommerce
    ]

def main():
    print("📁 Output CSV Path:", os.path.abspath(CSV_FILE))

    # First time: Create CSV with header
    if not os.path.isfile(CSV_FILE):
        with open(CSV_FILE, mode='w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(HEADER)

    try:
        with open(CSV_FILE, mode='r') as f:
            reader = list(csv.reader(f))
            transaction_id_num = len(reader)  # Including header
    except Exception as e:
        print("[⚠️] Error reading file. Defaulting to ID 1")
        transaction_id_num = 1

    print("[⏳] Starting data generation every 20 seconds. Writing 10 rows per interval...")

    while True:
        new_rows = []
        for _ in range(10):
            new_rows.append(generate_row(transaction_id_num))
            transaction_id_num += 1

        try:
            with open(CSV_FILE, mode='a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(new_rows)
            print(f"[✅] Added 20 transactions at {datetime.now().strftime('%H:%M:%S')}")
        except Exception as e:
            print(f"[❌] Error writing to file: {e}")
        
        time.sleep(20)  # 60 seconds

if __name__ == "__main__":
    main()