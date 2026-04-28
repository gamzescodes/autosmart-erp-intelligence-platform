import sqlite3
import random
from datetime import datetime, timedelta

DB_NAME = "autosmart_erp.db"
random.seed(42)

# -----------------------------
# REFERENCE DATA
# -----------------------------

brands = ["Volkswagen", "Audi", "Skoda", "Seat", "Porsche"]

categories = {
    "Brake System": {
        "criticality": "High",
        "parts": ["Brake Disc", "Brake Pad Set", "Brake Caliper", "ABS Sensor", "Brake Hose"]
    },
    "Engine": {
        "criticality": "High",
        "parts": ["Oil Filter", "Air Filter", "Timing Belt Kit", "Spark Plug", "Engine Mount", "Turbocharger"]
    },
    "Electrical": {
        "criticality": "High",
        "parts": ["Battery 70Ah", "Headlight Module", "Alternator", "Starter Motor", "ECU Module", "Parking Sensor"]
    },
    "Transmission": {
        "criticality": "High",
        "parts": ["Clutch Set", "Gearbox Oil", "Transmission Mount", "Flywheel", "Shift Cable"]
    },
    "Suspension": {
        "criticality": "Medium",
        "parts": ["Shock Absorber", "Control Arm", "Ball Joint", "Stabilizer Link", "Suspension Spring"]
    },
    "Body": {
        "criticality": "Low",
        "parts": ["Wiper Blade Set", "Side Mirror", "Door Handle", "Bumper Bracket", "Grille"]
    },
    "Cooling": {
        "criticality": "Medium",
        "parts": ["Radiator", "Water Pump", "Thermostat", "Cooling Fan", "Expansion Tank"]
    },
    "Fuel System": {
        "criticality": "High",
        "parts": ["Fuel Pump", "Fuel Filter", "Injector", "Fuel Rail", "Tank Cap"]
    }
}

cities = [
    ("Istanbul", "Marmara", "High"),
    ("Ankara", "Central Anatolia", "High"),
    ("Izmir", "Aegean", "Medium"),
    ("Bursa", "Marmara", "High"),
    ("Antalya", "Mediterranean", "Medium"),
    ("Konya", "Central Anatolia", "Medium"),
    ("Adana", "Mediterranean", "Medium"),
    ("Gaziantep", "Southeastern Anatolia", "Medium"),
    ("Trabzon", "Black Sea", "Low"),
    ("Samsun", "Black Sea", "Low"),
    ("Kayseri", "Central Anatolia", "Medium"),
    ("Kocaeli", "Marmara", "High"),
    ("Eskisehir", "Central Anatolia", "Medium"),
    ("Mugla", "Aegean", "Low"),
    ("Diyarbakir", "Southeastern Anatolia", "Medium")
]

supplier_countries = ["Germany", "France", "Japan", "Turkey", "Italy", "Spain", "Czech Republic", "Poland"]
supplier_names = [
    "Bosch Mobility", "Continental Network", "Valeo Automotive", "Denso Components",
    "Mann Filter", "ZF Aftermarket", "Mahle Parts", "Hella Lighting",
    "Schaeffler Group", "Local Aftermarket", "TRW Brake Systems", "NGK Components",
    "Febi Bilstein", "Delphi Technologies", "Textar Brake", "Magneti Marelli",
    "Varta Battery", "Osram Automotive", "Brembo Supply", "SKF Automotive",
    "Pierburg Systems", "Elring Parts", "Gates Powertrain", "INA Components", "Meyle Parts"
]

# -----------------------------
# DATABASE SETUP
# -----------------------------

conn = sqlite3.connect(DB_NAME)
cursor = conn.cursor()

cursor.executescript("""
DROP TABLE IF EXISTS ai_feedback_log;
DROP TABLE IF EXISTS warehouse_movements;
DROP TABLE IF EXISTS orders;
DROP TABLE IF EXISTS products;
DROP TABLE IF EXISTS suppliers;
DROP TABLE IF EXISTS dealers;
""")

cursor.execute("""
CREATE TABLE suppliers (
    SupplierID TEXT PRIMARY KEY,
    SupplierName TEXT,
    Country TEXT,
    AverageLeadTime INTEGER,
    ReliabilityScore REAL,
    RiskLevel TEXT
)
""")

cursor.execute("""
CREATE TABLE dealers (
    DealerID TEXT PRIMARY KEY,
    DealerName TEXT,
    City TEXT,
    Region TEXT,
    DealerType TEXT,
    MonthlyDemandLevel TEXT
)
""")

cursor.execute("""
CREATE TABLE products (
    PartID TEXT PRIMARY KEY,
    PartName TEXT,
    VehicleBrand TEXT,
    Category TEXT,
    CurrentStock INTEGER,
    MinStock INTEGER,
    UnitCost REAL,
    UnitPrice REAL,
    SupplierID TEXT,
    LeadTimeDays INTEGER,
    Criticality TEXT,
    FOREIGN KEY (SupplierID) REFERENCES suppliers(SupplierID)
)
""")

cursor.execute("""
CREATE TABLE orders (
    OrderID TEXT PRIMARY KEY,
    DealerID TEXT,
    PartID TEXT,
    Quantity INTEGER,
    Priority TEXT,
    OrderDate TEXT,
    Status TEXT,
    Revenue REAL,
    RiskScore INTEGER,
    FOREIGN KEY (DealerID) REFERENCES dealers(DealerID),
    FOREIGN KEY (PartID) REFERENCES products(PartID)
)
""")

cursor.execute("""
CREATE TABLE warehouse_movements (
    MovementID TEXT PRIMARY KEY,
    Date TEXT,
    PartID TEXT,
    MovementType TEXT,
    Quantity INTEGER,
    Reason TEXT,
    FOREIGN KEY (PartID) REFERENCES products(PartID)
)
""")

cursor.execute("""
CREATE TABLE ai_feedback_log (
    FeedbackID TEXT PRIMARY KEY,
    Date TEXT,
    UserRole TEXT,
    Scenario TEXT,
    FeedbackText TEXT,
    RiskScore INTEGER
)
""")

# -----------------------------
# DATA GENERATION
# -----------------------------

# Suppliers
suppliers = []
for i, name in enumerate(supplier_names, start=1):
    supplier_id = f"S{i:03d}"
    country = random.choice(supplier_countries)
    avg_lead_time = random.randint(5, 28)
    reliability = round(random.uniform(0.68, 0.98), 2)
    if reliability >= 0.88:
        risk = "Low"
    elif reliability >= 0.78:
        risk = "Medium"
    else:
        risk = "High"
    suppliers.append((supplier_id, name, country, avg_lead_time, reliability, risk))

cursor.executemany("INSERT INTO suppliers VALUES (?, ?, ?, ?, ?, ?)", suppliers)

# Dealers
dealer_types = ["Authorized Service", "Fleet Service", "Retail Dealer", "Commercial Vehicle Service"]
dealers = []
for i in range(1, 81):
    city, region, demand = random.choice(cities)
    dealer_type = random.choice(dealer_types)
    dealer_id = f"D{i:03d}"
    dealer_name = f"{city} {dealer_type} {i:02d}"
    dealers.append((dealer_id, dealer_name, city, region, dealer_type, demand))

cursor.executemany("INSERT INTO dealers VALUES (?, ?, ?, ?, ?, ?)", dealers)

# Products
products = []
part_counter = 1
for brand in brands:
    for category, details in categories.items():
        for base_part in details["parts"]:
            # Multiple variants per part create a realistic SKU structure.
            for variant in ["Standard", "Premium"]:
                part_id = f"P{part_counter:04d}"
                part_name = f"{brand} {base_part} - {variant}"
                criticality = details["criticality"]
                supplier = random.choice(suppliers)
                supplier_id = supplier[0]
                supplier_lead_time = supplier[3]

                if category in ["Body"]:
                    unit_cost = random.randint(80, 900)
                    min_stock = random.randint(30, 90)
                    current_stock = random.randint(70, 280)
                elif category in ["Engine", "Brake System", "Electrical"]:
                    unit_cost = random.randint(250, 4500)
                    min_stock = random.randint(15, 60)
                    current_stock = random.randint(20, 180)
                else:
                    unit_cost = random.randint(180, 2800)
                    min_stock = random.randint(12, 50)
                    current_stock = random.randint(20, 160)

                margin = random.uniform(1.25, 1.85)
                unit_price = round(unit_cost * margin, 2)
                lead_time = max(3, supplier_lead_time + random.randint(-3, 5))

                products.append((
                    part_id, part_name, brand, category, current_stock, min_stock,
                    unit_cost, unit_price, supplier_id, lead_time, criticality
                ))
                part_counter += 1

# Add extra variants until around 250 products
while len(products) < 250:
    brand = random.choice(brands)
    category = random.choice(list(categories.keys()))
    base_part = random.choice(categories[category]["parts"])
    variant = random.choice(["Eco", "OEM", "Performance", "Fleet Pack"])
    part_id = f"P{part_counter:04d}"
    part_name = f"{brand} {base_part} - {variant}"
    criticality = categories[category]["criticality"]
    supplier = random.choice(suppliers)
    unit_cost = random.randint(100, 5000)
    unit_price = round(unit_cost * random.uniform(1.25, 1.9), 2)
    min_stock = random.randint(10, 80)
    current_stock = random.randint(10, 260)
    lead_time = max(3, supplier[3] + random.randint(-4, 6))
    products.append((part_id, part_name, brand, category, current_stock, min_stock, unit_cost, unit_price, supplier[0], lead_time, criticality))
    part_counter += 1

cursor.executemany("INSERT INTO products VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)", products)

# Helper functions

def weighted_choice(options):
    values, weights = zip(*options)
    return random.choices(values, weights=weights, k=1)[0]


def demand_multiplier(month, category):
    # Winter season: battery, wiper, lighting, heating-related electrical demand rises.
    if month in [11, 12, 1, 2]:
        if category in ["Electrical", "Body"]:
            return 1.6
        if category in ["Brake System"]:
            return 1.25
    # Summer travel season: filters, cooling, brake demand rises.
    if month in [6, 7, 8]:
        if category in ["Cooling", "Engine", "Brake System"]:
            return 1.4
    return 1.0


def calculate_risk(priority, criticality, supplier_risk, lead_time, status):
    risk = 15
    if priority == "Urgent":
        risk += 25
    elif priority == "High":
        risk += 12
    if criticality == "High":
        risk += 20
    elif criticality == "Medium":
        risk += 10
    if supplier_risk == "High":
        risk += 18
    elif supplier_risk == "Medium":
        risk += 9
    if lead_time > 18:
        risk += 12
    if status == "Delayed":
        risk += 20
    elif status == "Rejected":
        risk += 30
    return min(risk, 100)

# Orders and warehouse movements
orders = []
movements = []
start_date = datetime.now() - timedelta(days=365)
movement_counter = 1

product_lookup = {p[0]: p for p in products}
supplier_lookup = {s[0]: s for s in suppliers}
dealer_lookup = {d[0]: d for d in dealers}

for i in range(1, 12001):
    order_id = f"O{i:06d}"

    # Demand-heavy dealers selected more often.
    dealer = weighted_choice([
        (d, 5 if d[5] == "High" else 3 if d[5] == "Medium" else 1)
        for d in dealers
    ])

    product = random.choice(products)
    part_id = product[0]
    category = product[3]
    criticality = product[10]
    supplier = supplier_lookup[product[8]]

    order_date_dt = start_date + timedelta(days=random.randint(0, 365))
    month = order_date_dt.month
    multiplier = demand_multiplier(month, category)

    base_qty = random.randint(1, 8)
    if dealer[5] == "High":
        base_qty += random.randint(1, 6)
    if multiplier > 1.0:
        base_qty = int(base_qty * multiplier)
    quantity = max(1, base_qty)

    priority = weighted_choice([
        ("Normal", 65),
        ("High", 25),
        ("Urgent", 10)
    ])

    # Status depends on supplier risk and priority.
    delay_probability = 0.06
    reject_probability = 0.025
    if supplier[5] == "High":
        delay_probability += 0.08
    if priority == "Urgent":
        delay_probability += 0.04
    if criticality == "High":
        reject_probability += 0.01

    rand = random.random()
    if rand < reject_probability:
        status = "Rejected"
    elif rand < reject_probability + delay_probability:
        status = "Delayed"
    else:
        status = "Completed"

    revenue = round(quantity * product[7], 2) if status == "Completed" else 0
    risk_score = calculate_risk(priority, criticality, supplier[5], product[9], status)

    orders.append((
        order_id, dealer[0], part_id, quantity, priority,
        order_date_dt.strftime("%Y-%m-%d"), status, revenue, risk_score
    ))

    if status == "Completed":
        movements.append((
            f"M{movement_counter:07d}", order_date_dt.strftime("%Y-%m-%d"), part_id,
            "Outbound", quantity, "Dealer order shipment"
        ))
        movement_counter += 1

# Inbound replenishment movements
for i in range(1, 3501):
    product = random.choice(products)
    part_id = product[0]
    date_dt = start_date + timedelta(days=random.randint(0, 365))
    qty = random.randint(10, 80)
    movements.append((
        f"M{movement_counter:07d}", date_dt.strftime("%Y-%m-%d"), part_id,
        "Inbound", qty, "Supplier replenishment"
    ))
    movement_counter += 1

cursor.executemany("""
INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
""", orders)

cursor.executemany("""
INSERT INTO warehouse_movements VALUES (?, ?, ?, ?, ?, ?)
""", movements)

# Sample AI feedback log records
sample_feedback = [
    ("F0001", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Sales Consultant", "Urgent dealer order with low stock", "High-risk order. Recommend partial shipment and urgent replenishment.", 82),
    ("F0002", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Warehouse Planner", "Critical stock detected for brake parts", "Safety-critical category. Increase minimum stock threshold and review supplier lead time.", 76),
    ("F0003", datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Purchasing Specialist", "Supplier delay risk", "Supplier reliability is below threshold. Alternative supplier should be evaluated.", 69),
]

cursor.executemany("INSERT INTO ai_feedback_log VALUES (?, ?, ?, ?, ?, ?)", sample_feedback)

conn.commit()
conn.close()

print("AutoSmart ERP large automotive database created successfully.")
print(f"Suppliers: {len(suppliers)}")
print(f"Dealers: {len(dealers)}")
print(f"Products: {len(products)}")
print(f"Orders: {len(orders)}")
print(f"Warehouse movements: {len(movements)}")
