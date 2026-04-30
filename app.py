import os
import sqlite3
import streamlit as st
import pandas as pd
from datetime import datetime
from openai import OpenAI

DB_NAME = "autosmart_erp.db"

def database_has_required_tables():
    if not os.path.exists(DB_NAME):
        return False

    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='products'
        """)
        result = cursor.fetchone()
        conn.close()
        return result is not None
    except Exception:
        return False


if not database_has_required_tables():
    if os.path.exists(DB_NAME):
        os.remove(DB_NAME)
    import create_database

st.set_page_config(
    page_title="AutoSmart ERP Intelligence Platform",
    page_icon="AUTO",
    layout="wide"
)

# --------------------------------------------------
# DATABASE HELPERS
# --------------------------------------------------

def get_connection():
    return sqlite3.connect(DB_NAME)


def load_data(query, params=None):
    conn = get_connection()
    df = pd.read_sql_query(query, conn, params=params)
    conn.close()
    return df


def execute_query(query, params=None):
    conn = get_connection()
    cursor = conn.cursor()
    if params:
        cursor.execute(query, params)
    else:
        cursor.execute(query)
    conn.commit()
    conn.close()


# --------------------------------------------------
# DECISION SUPPORT LOGIC
# --------------------------------------------------
def get_openai_client():
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        return None
    return OpenAI(api_key=api_key)


def generate_order_feedback(stock, min_stock, quantity, priority, criticality, lead_time, supplier_risk, dealer_type):
    risk = 10
    reasons = []

    remaining_stock = stock - quantity

    if quantity > stock:
        risk += 45
        reasons.append("Requested quantity exceeds available stock. The order cannot be fully fulfilled from current inventory.")

    if remaining_stock < min_stock:
        risk += 25
        reasons.append("Projected stock after fulfillment falls below the defined minimum stock threshold.")

    if criticality == "High":
        risk += 15
        reasons.append("The selected part is classified as high criticality due to its operational impact.")

    if priority == "Urgent":
        risk += 20
        reasons.append("The order has urgent priority and may directly affect service-level performance.")
    elif priority == "High":
        risk += 10
        reasons.append("The order has high priority and requires close operational monitoring.")

    if lead_time > 18:
        risk += 10
        reasons.append("Supplier lead time is above the preferred replenishment threshold.")

    if supplier_risk == "High":
        risk += 15
        reasons.append("The assigned supplier has a high operational risk classification.")
    elif supplier_risk == "Medium":
        risk += 8
        reasons.append("The assigned supplier has a moderate operational risk classification.")

    if "Fleet" in dealer_type or "Commercial" in dealer_type:
        risk += 5
        reasons.append("The dealer type represents a business-critical customer segment.")

    risk = min(risk, 100)

    if risk >= 75:
        decision = "High Risk: Partial fulfillment, immediate replenishment planning and supplier review are recommended."
    elif risk >= 45:
        decision = "Medium Risk: Order can be processed with inventory monitoring and replenishment control."
    else:
        decision = "Low Risk: Order can be processed under current operational conditions."

    return risk, reasons, decision


def generate_executive_insights(kpis, suppliers, category_demand, delayed_orders):
    insights = []

    if kpis["critical_parts"] > 0:
        insights.append(
            f"There are {kpis['critical_parts']} parts below minimum stock level. These items should be reviewed for replenishment planning."
        )

    high_risk_suppliers = suppliers[suppliers["RiskLevel"] == "High"]
    if len(high_risk_suppliers) > 0:
        insights.append(
            f"The supplier portfolio includes {len(high_risk_suppliers)} high-risk suppliers. Alternative sourcing options should be evaluated."
        )

    if not category_demand.empty:
        top_category = category_demand.iloc[0]
        insights.append(
            f"The highest demand is observed in the {top_category['Category']} category. Safety stock and purchasing frequency should be reviewed for this category."
        )

    if delayed_orders > 0:
        insights.append(
            f"There are {delayed_orders} delayed orders in the system. Lead time and stock availability should be analyzed as potential root causes."
        )

    if not insights:
        insights.append("Operational indicators are within an acceptable range. Current planning parameters can be maintained.")

    return insights


@st.cache_data(ttl=10)
def get_dashboard_data():
    products = load_data("SELECT * FROM products")
    orders = load_data("SELECT * FROM orders")
    suppliers = load_data("SELECT * FROM suppliers")
    dealers = load_data("SELECT * FROM dealers")
    movements = load_data("SELECT * FROM warehouse_movements")
    return products, orders, suppliers, dealers, movements

def generate_fallback_management_report(order_context, risk, reasons, rule_based_decision):
    risk_level = "High" if risk >= 75 else "Medium" if risk >= 45 else "Low"

    report = f"""
Operational Assessment

The order was evaluated using the internal ERP decision rules. The selected part, dealer segment, supplier risk, stock level and replenishment lead time were assessed together.

Business Risk

Calculated risk level: {risk_level}
Calculated risk score: {risk}/100

Main risk drivers:
"""

    if reasons:
        for reason in reasons:
            report += f"\n- {reason}"
    else:
        report += "\n- No significant operational risk driver was detected."

    report += f"""

Recommended Action

{rule_based_decision}

Additional recommendation:
The inventory planning team should monitor the remaining stock level and review replenishment parameters if similar demand continues.

Management Note

This report was generated by the internal ERP decision support layer. If the external AI service is available, the system can enrich this output with a more contextual management interpretation.
"""
    return report


def generate_api_decision_report(order_context, risk, reasons, rule_based_decision):
    client = get_openai_client()

    if client is None:
        return generate_fallback_management_report(
            order_context, risk, reasons, rule_based_decision
        )

    prompt = f"""
You are an enterprise ERP decision support analyst for an automotive after-sales operation.

Analyze the following ERP transaction context and produce a professional decision support report.

ERP Transaction Context:
{order_context}

Calculated Risk Score:
{risk}/100

Rule-Based Risk Drivers:
{reasons}

Rule-Based Decision:
{rule_based_decision}

Write the output in a professional business format with these sections:
1. Operational Assessment
2. Business Risk
3. Recommended Action
4. Management Note

Keep it concise, realistic and suitable for an ERP management dashboard.
"""

    try:
        response = client.responses.create(
            model="gpt-4.1-mini",
            input=prompt
        )
        return response.output_text

    except Exception:
        return generate_fallback_management_report(
            order_context, risk, reasons, rule_based_decision
        )



# --------------------------------------------------
# APPLICATION HEADER
# --------------------------------------------------

st.title("AutoSmart ERP Intelligence Platform")
st.caption("Automotive After-Sales Operations | Inventory Intelligence | Decision Support")

with st.sidebar:
    st.header("Modules")
    page = st.radio(
        "Select module",
        [
            "Executive Overview",
            "Demand Intelligence",
            "Order Management",
            "Decision Support Center",
            "Data Explorer",
            "System Architecture"
        ]
    )

    st.divider()
    st.caption("Connected database: autosmart_erp.db")
    if st.button("Refresh Data"):
        st.cache_data.clear()
        st.rerun()


# --------------------------------------------------
# EXECUTIVE OVERVIEW
# --------------------------------------------------

if page == "Executive Overview":
    products, orders, suppliers, dealers, movements = get_dashboard_data()

    completed = orders[orders["Status"] == "Completed"]
    delayed_orders = len(orders[orders["Status"] == "Delayed"])
    rejected_orders = len(orders[orders["Status"] == "Rejected"])
    critical_parts = products[products["CurrentStock"] <= products["MinStock"]]

    kpis = {
        "total_revenue": completed["Revenue"].sum(),
        "total_orders": len(orders),
        "critical_parts": len(critical_parts),
        "avg_risk": orders["RiskScore"].mean(),
        "delayed_orders": delayed_orders,
        "rejected_orders": rejected_orders
    }

    st.subheader("Executive Overview")

    row1_col1, row1_col2, row1_col3 = st.columns(3)

    row1_col1.metric("Total Revenue", f"TRY {kpis['total_revenue']:,.0f}")
    row1_col2.metric("Total Orders", f"{kpis['total_orders']:,}")
    row1_col3.metric("Average Risk Score", f"{kpis['avg_risk']:.1f}/100")

    row2_col1, row2_col2, row2_col3 = st.columns(3)

    row2_col1.metric("Critical Parts", kpis["critical_parts"])
    row2_col2.metric("Delayed Orders", delayed_orders)
    row2_col3.metric("Rejected Orders", rejected_orders)

    st.divider()

    left, right = st.columns([2, 1])

    with left:
        st.write("### Monthly Revenue Trend")
        orders["OrderDate"] = pd.to_datetime(orders["OrderDate"])
        monthly = orders.groupby(orders["OrderDate"].dt.to_period("M")).agg(
            Revenue=("Revenue", "sum")
        ).reset_index()
        monthly["OrderDate"] = monthly["OrderDate"].astype(str)

        st.line_chart(monthly.set_index("OrderDate")["Revenue"])

    with right:
        st.write("### Management Insight")
        category_demand = orders.merge(products[["PartID", "Category"]], on="PartID", how="left")
        category_demand = category_demand.groupby("Category")["Quantity"].sum().reset_index().sort_values("Quantity", ascending=False)

        insights = generate_executive_insights(kpis, suppliers, category_demand, delayed_orders)
        for insight in insights:
            st.info(insight)

    st.divider()

    col_a, col_b = st.columns(2)

    with col_a:
        st.write("### Critical Inventory Items")
        if critical_parts.empty:
            st.success("No inventory item is currently below its minimum stock level.")
        else:
            critical_view = critical_parts[[
                "PartID", "PartName", "VehicleBrand", "Category", "CurrentStock", "MinStock", "LeadTimeDays", "Criticality"
            ]].sort_values("CurrentStock")
            st.dataframe(critical_view.head(20), use_container_width=True, hide_index=True)

    with col_b:
        st.write("### Highest Risk Orders")
        high_risk = orders.merge(products[["PartID", "PartName", "Category", "Criticality"]], on="PartID", how="left")
        high_risk = high_risk.merge(dealers[["DealerID", "DealerName", "City", "DealerType"]], on="DealerID", how="left")
        high_risk = high_risk.sort_values("RiskScore", ascending=False)
        st.dataframe(high_risk[[
            "OrderID", "DealerName", "City", "PartName", "Quantity", "Priority", "Status", "RiskScore"
        ]].head(20), use_container_width=True, hide_index=True)


# --------------------------------------------------
# DEMAND INTELLIGENCE
# --------------------------------------------------

elif page == "Demand Intelligence":
    products, orders, suppliers, dealers, movements = get_dashboard_data()
    data = orders.merge(products, on="PartID", how="left").merge(dealers, on="DealerID", how="left")

    st.subheader("Demand Intelligence")
    st.write("Historical demand is analyzed by brand, region, product category, dealer segment and revenue contribution.")

    filter_col1, filter_col2, filter_col3 = st.columns(3)
    with filter_col1:
        selected_brand = st.multiselect("Vehicle Brand", sorted(data["VehicleBrand"].dropna().unique()))
    with filter_col2:
        selected_region = st.multiselect("Region", sorted(data["Region"].dropna().unique()))
    with filter_col3:
        selected_category = st.multiselect("Product Category", sorted(data["Category"].dropna().unique()))

    filtered = data.copy()
    if selected_brand:
        filtered = filtered[filtered["VehicleBrand"].isin(selected_brand)]
    if selected_region:
        filtered = filtered[filtered["Region"].isin(selected_region)]
    if selected_category:
        filtered = filtered[filtered["Category"].isin(selected_category)]

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Filtered Orders", f"{len(filtered):,}")
    c2.metric("Filtered Revenue", f"TRY {filtered['Revenue'].sum():,.0f}")
    c3.metric("Average Risk", f"{filtered['RiskScore'].mean():.1f}/100")
    c4.metric("Total Quantity", f"{filtered['Quantity'].sum():,}")

    st.divider()

    left, right = st.columns(2)

    with left:
        st.write("### Demand by Product Category")
        category = filtered.groupby("Category")["Quantity"].sum().sort_values(ascending=False)
        st.bar_chart(category)

    with right:
        st.write("### Demand by Region")
        region = filtered.groupby("Region")["Quantity"].sum().sort_values(ascending=False)
        st.bar_chart(region)

    left2, right2 = st.columns(2)

    with left2:
        st.write("### Top Requested Parts")
        top_parts = filtered.groupby("PartName").agg(
            Quantity=("Quantity", "sum"),
            Revenue=("Revenue", "sum"),
            AverageRisk=("RiskScore", "mean")
        ).sort_values("Quantity", ascending=False).head(15).reset_index()
        st.dataframe(top_parts, use_container_width=True, hide_index=True)

    with right2:
        st.write("### Dealer Demand Ranking")
        top_dealers = filtered.groupby(["DealerName", "City", "DealerType"]).agg(
            Orders=("OrderID", "count"),
            Quantity=("Quantity", "sum"),
            Revenue=("Revenue", "sum")
        ).sort_values("Revenue", ascending=False).head(15).reset_index()
        st.dataframe(top_dealers, use_container_width=True, hide_index=True)


# --------------------------------------------------
# ORDER MANAGEMENT
# --------------------------------------------------

elif page == "Order Management":
    st.subheader("Order Management")
    st.write("This module evaluates dealer orders using inventory availability, supplier risk, lead time, product criticality and customer segment.")

    products = load_data("""
        SELECT p.*, s.SupplierName, s.ReliabilityScore, s.RiskLevel
        FROM products p
        LEFT JOIN suppliers s ON p.SupplierID = s.SupplierID
    """)
    dealers = load_data("SELECT * FROM dealers")

    col1, col2 = st.columns(2)
    with col1:
        dealer_name = st.selectbox("Dealer / Service Point", dealers["DealerName"].tolist())
        part_name = st.selectbox("Automotive Part", products["PartName"].tolist())
    with col2:
        quantity = st.number_input("Order Quantity", min_value=1, max_value=500, value=5)
        priority = st.selectbox("Order Priority", ["Normal", "High", "Urgent"])

    selected_product = products[products["PartName"] == part_name].iloc[0]
    selected_dealer = dealers[dealers["DealerName"] == dealer_name].iloc[0]

    st.write("### Operational Context")
    context_cols = st.columns(5)
    context_cols[0].metric("Current Stock", int(selected_product["CurrentStock"]))
    context_cols[1].metric("Minimum Stock", int(selected_product["MinStock"]))
    context_cols[2].metric("Lead Time", f"{int(selected_product['LeadTimeDays'])} days")
    context_cols[3].metric("Supplier Risk", selected_product["RiskLevel"])
    context_cols[4].metric("Criticality", selected_product["Criticality"])

    if st.button("Submit and Process Order"):
        stock = int(selected_product["CurrentStock"])
        min_stock = int(selected_product["MinStock"])

        risk, reasons, decision = generate_order_feedback(
            stock=stock,
            min_stock=min_stock,
            quantity=int(quantity),
            priority=priority,
            criticality=selected_product["Criticality"],
            lead_time=int(selected_product["LeadTimeDays"]),
            supplier_risk=selected_product["RiskLevel"],
            dealer_type=selected_dealer["DealerType"]
        )

        st.write("### Process Execution")
        st.write("Order received")
        st.write("Inventory availability checked")
        st.write("Operational risk calculated")
        st.write("Decision support output generated")

        if int(quantity) <= stock:
            new_stock = stock - int(quantity)

            execute_query(
                "UPDATE products SET CurrentStock = ? WHERE PartID = ?",
                (new_stock, selected_product["PartID"])
            )

            order_id = f"O{datetime.now().strftime('%Y%m%d%H%M%S')}"
            revenue = float(quantity) * float(selected_product["UnitPrice"])

            execute_query(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    order_id,
                    selected_dealer["DealerID"],
                    selected_product["PartID"],
                    int(quantity),
                    priority,
                    datetime.now().strftime("%Y-%m-%d"),
                    "Completed",
                    revenue,
                    risk
                )
            )

            movement_id = f"M{datetime.now().strftime('%Y%m%d%H%M%S')}"
            execute_query(
                "INSERT INTO warehouse_movements VALUES (?, ?, ?, ?, ?, ?)",
                (
                    movement_id,
                    datetime.now().strftime("%Y-%m-%d"),
                    selected_product["PartID"],
                    "Outbound",
                    int(quantity),
                    "Dealer shipment"
                )
            )

            st.success("Order processed successfully. Inventory and warehouse records have been updated.")

            if new_stock < min_stock:
                st.warning("Replenishment action required. Projected stock is below the minimum threshold.")
        else:
            new_stock = stock
            st.error("Order cannot be fulfilled because requested quantity exceeds available stock.")

        st.write("### Decision Support Report")
        st.metric("Calculated Risk Score", f"{risk}/100")

        if risk >= 75:
            st.error(decision)
        elif risk >= 45:
            st.warning(decision)
        else:
            st.success(decision)

        st.write("### Key Risk Drivers")
        if reasons:
            for reason in reasons:
                st.write(f"- {reason}")
        else:
            st.write("No significant risk driver was detected for this transaction.")

        st.session_state["last_order_context"] = {
            "dealer": dealer_name,
            "dealer_type": selected_dealer["DealerType"],
            "city": selected_dealer["City"],
            "part": part_name,
            "vehicle_brand": selected_product["VehicleBrand"],
            "category": selected_product["Category"],
            "stock_before_order": stock,
            "minimum_stock": min_stock,
            "quantity": int(quantity),
            "remaining_stock": max(new_stock, 0),
            "priority": priority,
            "supplier": selected_product["SupplierName"],
            "supplier_risk": selected_product["RiskLevel"],
            "supplier_reliability": selected_product["ReliabilityScore"],
            "lead_time_days": int(selected_product["LeadTimeDays"]),
            "criticality": selected_product["Criticality"]
        }

        st.session_state["last_risk"] = risk
        st.session_state["last_reasons"] = reasons
        st.session_state["last_decision"] = decision

        scenario = f"Dealer: {dealer_name}; Part: {part_name}; Quantity: {quantity}; Priority: {priority}"
        feedback_text = decision + " Risk drivers: " + " | ".join(reasons)
        feedback_id = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}"
        execute_query(
            "INSERT INTO ai_feedback_log VALUES (?, ?, ?, ?, ?, ?)",
            (feedback_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Business User", scenario, feedback_text, risk)
        )

    st.divider()
    st.write("### AI Decision Support")

    if "last_order_context" in st.session_state:
        if st.button("Generate AI Management Report"):
            report = generate_api_decision_report(
                st.session_state["last_order_context"],
                st.session_state["last_risk"],
                st.session_state["last_reasons"],
                st.session_state["last_decision"]
            )

            st.write("### AI Management Report")

            if report is None:
                st.warning("API key not found. Using internal logic only.")

            else:
                st.write("### AI Management Report")

                st.caption("Generated by Internal Decision Engine / External AI Service when available")

                with st.container(border=True):
                    st.markdown(report)
    else:
        st.info("Process an order first to generate AI analysis.")

# --------------------------------------------------
# DECISION SUPPORT CENTER
# --------------------------------------------------

elif page == "Decision Support Center":
    st.subheader("Decision Support Center")
    st.write("Operational issues are evaluated using structured ERP decision rules and business risk indicators.")

    role = st.selectbox("Business Role", ["Sales Operations", "Warehouse Planning", "Purchasing", "Operations Management", "Digital Transformation"])
    scenario = st.text_area(
        "Operational Issue",
        placeholder="Example: A high-priority dealer order requires a critical brake component, but stock is close to the minimum threshold and supplier lead time is long."
    )

    if st.button("Generate Decision Support Output"):
        text = scenario.lower()
        recommendations = []
        risk = 30

        if "stock" in text or "stok" in text or "low" in text or "minimum" in text:
            recommendations.append("Review minimum stock and safety stock parameters for the affected item group.")
            risk += 20
        if "urgent" in text or "acil" in text or "priority" in text:
            recommendations.append("Evaluate customer priority and consider partial fulfillment if full fulfillment creates inventory risk.")
            risk += 20
        if "supplier" in text or "tedarik" in text or "lead time" in text:
            recommendations.append("Review supplier performance and evaluate alternative sourcing options.")
            risk += 20
        if "dealer" in text or "bayi" in text or "customer" in text:
            recommendations.append("Assess dealer segment and service-level commitment before allocation decision.")
            risk += 10
        if "forecast" in text or "tahmin" in text or "demand" in text:
            recommendations.append("Use demand forecasting outputs to adjust future replenishment parameters.")
            risk += 10

        if not recommendations:
            recommendations.append("Analyze process data to identify bottlenecks, manual handoffs and decision delays.")

        risk = min(risk, 100)

        if risk >= 75:
            summary = "High-priority operational issue. Immediate action and management review are recommended."
            st.error(summary)
        elif risk >= 50:
            summary = "Moderate operational risk. Monitoring and corrective planning are recommended."
            st.warning(summary)
        else:
            summary = "Controlled operational risk. Process visibility and standardization should be maintained."
            st.success(summary)

        st.write("### Recommended Actions")
        for rec in recommendations:
            st.write(f"- {rec}")

        feedback_id = f"F{datetime.now().strftime('%Y%m%d%H%M%S')}"
        feedback_text = summary + " Actions: " + " | ".join(recommendations)
        execute_query(
            "INSERT INTO ai_feedback_log VALUES (?, ?, ?, ?, ?, ?)",
            (feedback_id, datetime.now().strftime("%Y-%m-%d %H:%M:%S"), role, scenario, feedback_text, risk)
        )
        st.caption("Decision support output has been saved to the system log.")

    st.divider()
    st.write("### Recent Decision Support Records")
    logs = load_data("SELECT * FROM ai_feedback_log ORDER BY Date DESC LIMIT 20")
    st.dataframe(logs, use_container_width=True, hide_index=True)


# --------------------------------------------------
# DATA EXPLORER
# --------------------------------------------------

elif page == "Data Explorer":
    st.subheader("Data Explorer")
    st.write("This module provides controlled visibility into the relational ERP data model used by the platform.")

    table = st.selectbox("Database Table", ["products", "orders", "suppliers", "dealers", "warehouse_movements", "ai_feedback_log"])
    limit = st.slider("Number of Rows", 10, 500, 50)
    df = load_data(f"SELECT * FROM {table} LIMIT {limit}")
    st.dataframe(df, use_container_width=True, hide_index=True)

    count_df = load_data(f"SELECT COUNT(*) as RowCount FROM {table}")
    st.metric(f"Total Records in {table}", int(count_df["RowCount"].iloc[0]))


# --------------------------------------------------
# SYSTEM ARCHITECTURE
# --------------------------------------------------

elif page == "System Architecture":
    st.subheader("System Architecture")
    st.markdown(
        """
        ### AutoSmart ERP Intelligence Platform

        This platform is designed as a sector-specific ERP prototype for automotive after-sales spare parts and logistics operations.

        **Core system layers:**

        1. **Data Layer**  
        Relational database containing products, suppliers, dealers, orders, warehouse movements and decision support records.

        2. **Business Process Layer**  
        Order processing, inventory update, warehouse movement creation and operational risk scoring.

        3. **Decision Support Layer**  
        Rule-based intelligence that evaluates stock availability, supplier risk, lead time, product criticality and dealer segment.

        4. **Management Intelligence Layer**  
        Executive KPIs, demand analytics, critical inventory monitoring and operational insight generation.

        **Digital transformation perspective:**  
        Traditional ERP systems record transactions. New-generation ERP platforms should interpret operational data, detect risks and guide business users toward better decisions.
        """
    )
