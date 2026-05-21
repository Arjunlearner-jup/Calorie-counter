#!/usr/bin/env python
# coding: utf-8

import re
import streamlit as st
import pandas as pd
import plotly.express as px

UNIT_TO_GRAMS = {
    "g": 1.0,
    "gram": 1.0,
    "grams": 1.0,
    "kg": 1000.0,
    "oz": 28.3495,
    "ounce": 28.3495,
    "ounces": 28.3495,
    "lb": 453.592,
    "pound": 453.592,
    "pounds": 453.592,
    "ml": 1.0,
}

COUNT_BASED_FOODS = {
    "boiled egg": {"calories_per_unit": 78.0, "protein_per_unit": 6.29, "unit_name": "piece"},
    "egg": {"calories_per_unit": 78.0, "protein_per_unit": 6.29, "unit_name": "piece"},
    "roti": {"calories_per_unit": 106.0, "protein_per_unit": 3.84, "unit_name": "piece"},
    "chapati": {"calories_per_unit": 106.0, "protein_per_unit": 3.84, "unit_name": "piece"},
    "french toast": {"calories_per_unit": 480.0, "protein_per_unit": 27.0, "unit_name": "slice"},
    "snickers": {"calories_per_unit": 250.0, "protein_per_unit": 5.0, "unit_name": "bar"},
    "snickers bar": {"calories_per_unit": 250.0, "protein_per_unit": 5.0, "unit_name": "bar"},
}

WEIGHT_BASED_FOODS = {
    "muesli": {"calories_per_100g": 380.0, "protein_per_100g": 10.8},
    "chips": {"calories_per_100g": 536.0, "protein_per_100g": 7.0},
    "potato chips": {"calories_per_100g": 536.0, "protein_per_100g": 7.0},
    "rice": {"calories_per_100g": 130.0, "protein_per_100g": 2.7},
    "milk": {"calories_per_100g": 61.0, "protein_per_100g": 3.2},
    "almonds": {"calories_per_100g": 579.0, "protein_per_100g": 21.2},
    "oats": {"calories_per_100g": 389.0, "protein_per_100g": 16.9},
    "dal": {"calories_per_100g": 116.0, "protein_per_100g": 9.0},
    "lentil dal": {"calories_per_100g": 116.0, "protein_per_100g": 9.0},
    "moong dal": {"calories_per_100g": 105.0, "protein_per_100g": 7.0},
    "mung beans": {"calories_per_100g": 105.0, "protein_per_100g": 7.0},
    "green gram dal": {"calories_per_100g": 105.0, "protein_per_100g": 7.0},
    "cooked moong dal": {"calories_per_100g": 105.0, "protein_per_100g": 7.0},
    "cooked mung beans": {"calories_per_100g": 105.0, "protein_per_100g": 7.0},
    "cooked green gram dal": {"calories_per_100g": 105.0, "protein_per_100g": 7.0},
    "honey": {"calories_per_100g": 304.0, "protein_per_100g": 0.3},
    "raw honey": {"calories_per_100g": 304.0, "protein_per_100g": 0.3},
    "drumstick chicken": {"calories_per_100g": 193.0, "protein_per_100g": 18.3},
    "chicken drumstick": {"calories_per_100g": 193.0, "protein_per_100g": 18.3},
    "mousse": {"calories_per_100g": 143.0, "protein_per_100g": 3.9},
    "chocolate mousse": {"calories_per_100g": 143.0, "protein_per_100g": 3.9},
}
st.set_page_config(page_title="Calorie & Protein Dashboard", layout="wide")


def is_count_input(quantity_query: str) -> bool:
    q = quantity_query.strip().lower()
    return bool(re.fullmatch(r"\d+(\.\d+)?", q))


def parse_count(quantity_query: str) -> float:
    return float(quantity_query.strip())


def parse_weight_quantity(quantity_query: str) -> float:
    q = quantity_query.strip().lower()
    m = re.search(r"([\d.]+)\s*([a-zA-Z]+)", q)
    if not m:
        raise ValueError("Quantity input should be like: 20 g, 1.5 oz, 2 kg, 100 ml or just 2 for count foods")

    amount = float(m.group(1))
    unit = m.group(2)

    if unit not in UNIT_TO_GRAMS:
        raise ValueError(f"Unsupported unit: {unit}")

    return amount * UNIT_TO_GRAMS[unit]


def get_count_food_reference(food_query: str):
    food_lower = food_query.strip().lower()
    for known_food, ref in COUNT_BASED_FOODS.items():
        if known_food in food_lower:
            return known_food, ref
    return None, None


def get_weight_food_reference(food_query: str):
    food_lower = food_query.strip().lower()
    for known_food, ref in WEIGHT_BASED_FOODS.items():
        if known_food in food_lower:
            return known_food, ref
    return None, None


def calculate_from_query(quantity_query: str, food_query: str):
    if is_count_input(quantity_query):
        count = parse_count(quantity_query)
        matched_food, ref = get_count_food_reference(food_query)

        if ref is None:
            raise ValueError("Count input is only supported for hardcoded count-based foods")

        calories = count * ref["calories_per_unit"]
        protein = count * ref["protein_per_unit"]

        return {
            "input_quantity": quantity_query,
            "input_food": food_query,
            "matched_food": matched_food,
            "quantity_type": "count",
            "grams": None,
            "calories": round(calories, 2),
            "protein_g": round(protein, 2),
        }

    grams = parse_weight_quantity(quantity_query)
    matched_food, ref = get_weight_food_reference(food_query)

    if ref is None:
        raise ValueError("Weight input food not found in local food database")

    calories = ref["calories_per_100g"] * grams / 100.0
    protein = ref["protein_per_100g"] * grams / 100.0

    return {
        "input_quantity": quantity_query,
        "input_food": food_query,
        "matched_food": matched_food,
        "quantity_type": "weight",
        "grams": round(grams, 2),
        "calories": round(calories, 2),
        "protein_g": round(protein, 2),
    }


def process_meal_entries(meal_name, entries):
    meal_results = []
    for quantity, food in entries:
        if quantity.strip() and food.strip():
            try:
                result = calculate_from_query(quantity, food)
                result["meal"] = meal_name
                meal_results.append(result)
            except Exception as e:
                st.warning(f"{meal_name}: {food} -> {e}")
    return meal_results


@st.cache_data
def convert_df_to_csv(dataframe):
    return dataframe.to_csv(index=False).encode("utf-8")


st.title("🍎 Calorie & Protein Dashboard")

with st.form("meal_form"):
    st.subheader("Breakfast")
    b1_col1, b1_col2 = st.columns(2)
    breakfast_qty_1 = b1_col1.text_input("Breakfast - Quantity 1", placeholder="e.g. 2 or 200 g")
    breakfast_food_1 = b1_col2.text_input("Breakfast - Food 1", placeholder="e.g. boiled egg or milk")

    b2_col1, b2_col2 = st.columns(2)
    breakfast_qty_2 = b2_col1.text_input("Breakfast - Quantity 2", placeholder="e.g. 2 or 100 g")
    breakfast_food_2 = b2_col2.text_input("Breakfast - Food 2", placeholder="e.g. french toast or oats")

    b3_col1, b3_col2 = st.columns(2)
    breakfast_qty_3 = b3_col1.text_input("Breakfast - Quantity 3", placeholder="e.g. 50 g")
    breakfast_food_3 = b3_col2.text_input("Breakfast - Food 3", placeholder="e.g. almonds")

    st.subheader("Lunch")
    l1_col1, l1_col2 = st.columns(2)
    lunch_qty_1 = l1_col1.text_input("Lunch - Quantity 1", placeholder="e.g. 2 or 150 g")
    lunch_food_1 = l1_col2.text_input("Lunch - Food 1", placeholder="e.g. roti or rice")

    l2_col1, l2_col2 = st.columns(2)
    lunch_qty_2 = l2_col1.text_input("Lunch - Quantity 2", placeholder="e.g. 100 g")
    lunch_food_2 = l2_col2.text_input("Lunch - Food 2", placeholder="e.g. dal")

    l3_col1, l3_col2 = st.columns(2)
    lunch_qty_3 = l3_col1.text_input("Lunch - Quantity 3", placeholder="e.g. 120 g")
    lunch_food_3 = l3_col2.text_input("Lunch - Food 3", placeholder="e.g. rice")

    st.subheader("Snacks")
    s1_col1, s1_col2 = st.columns(2)
    snacks_qty_1 = s1_col1.text_input("Snacks - Quantity 1", placeholder="e.g. 2 or 30 g")
    snacks_food_1 = s1_col2.text_input("Snacks - Food 1", placeholder="e.g. french toast or almonds")

    s2_col1, s2_col2 = st.columns(2)
    snacks_qty_2 = s2_col1.text_input("Snacks - Quantity 2", placeholder="e.g. 1 or 100 g")
    snacks_food_2 = s2_col2.text_input("Snacks - Food 2", placeholder="e.g. egg or muesli")

    s3_col1, s3_col2 = st.columns(2)
    snacks_qty_3 = s3_col1.text_input("Snacks - Quantity 3", placeholder="e.g. 150 g")
    snacks_food_3 = s3_col2.text_input("Snacks - Food 3", placeholder="e.g. milk")

    st.subheader("Dinner")
    d1_col1, d1_col2 = st.columns(2)
    dinner_qty_1 = d1_col1.text_input("Dinner - Quantity 1", placeholder="e.g. 2 or 150 g")
    dinner_food_1 = d1_col2.text_input("Dinner - Food 1", placeholder="e.g. chapati or rice")

    d2_col1, d2_col2 = st.columns(2)
    dinner_qty_2 = d2_col1.text_input("Dinner - Quantity 2", placeholder="e.g. 100 g")
    dinner_food_2 = d2_col2.text_input("Dinner - Food 2", placeholder="e.g. cooked lentil dal")

    d3_col1, d3_col2 = st.columns(2)
    dinner_qty_3 = d3_col1.text_input("Dinner - Quantity 3", placeholder="e.g. 100 g")
    dinner_food_3 = d3_col2.text_input("Dinner - Food 3", placeholder="e.g. milk or rice")

    submitted = st.form_submit_button("Calculate")

if submitted:
    all_results = []

    breakfast_entries = [
        (breakfast_qty_1, breakfast_food_1),
        (breakfast_qty_2, breakfast_food_2),
        (breakfast_qty_3, breakfast_food_3),
    ]
    lunch_entries = [
        (lunch_qty_1, lunch_food_1),
        (lunch_qty_2, lunch_food_2),
        (lunch_qty_3, lunch_food_3),
    ]
    snacks_entries = [
        (snacks_qty_1, snacks_food_1),
        (snacks_qty_2, snacks_food_2),
        (snacks_qty_3, snacks_food_3),
    ]
    dinner_entries = [
        (dinner_qty_1, dinner_food_1),
        (dinner_qty_2, dinner_food_2),
        (dinner_qty_3, dinner_food_3),
    ]

    all_results.extend(process_meal_entries("Breakfast", breakfast_entries))
    all_results.extend(process_meal_entries("Lunch", lunch_entries))
    all_results.extend(process_meal_entries("Snacks", snacks_entries))
    all_results.extend(process_meal_entries("Dinner", dinner_entries))

    if all_results:
        df = pd.DataFrame(all_results)

        total_calories = df["calories"].sum()
        total_protein = df["protein_g"].sum()

        st.subheader("Daily Summary")
        c1, c2 = st.columns(2)
        c1.metric("Total Calories", round(total_calories, 2))
        c2.metric("Total Protein (g)", round(total_protein, 2))

        st.subheader("Food-wise Breakdown")

        breakdown_df = df[[
            "meal",
            "input_quantity",
            "input_food",
            "matched_food",
            "quantity_type",
            "grams",
            "calories",
            "protein_g"
        ]].copy()

        breakdown_df.columns = [
            "Meal",
            "Quantity",
            "Food Entered",
            "Matched Food",
            "Quantity Type",
            "Grams",
            "Calories",
            "Protein (g)"
        ]

        st.dataframe(
            breakdown_df,
            use_container_width=True,
            column_config={
                "Calories": st.column_config.NumberColumn(format="%.2f"),
                "Protein (g)": st.column_config.NumberColumn(format="%.2f"),
                "Grams": st.column_config.NumberColumn(format="%.2f"),
            }
        )

        csv = convert_df_to_csv(breakdown_df)
        st.download_button(
            label="Download breakdown as CSV",
            data=csv,
            file_name="food_breakdown.csv",
            mime="text/csv"
        )

        chart_df = pd.DataFrame({
            "Metric": ["Calories", "Protein"],
            "Value": [total_calories, total_protein]
        })

        st.subheader("Total Calories and Protein")

        fig = px.pie(
            chart_df,
            names="Metric",
            values="Value",
            hole=0.45,
            color="Metric",
            color_discrete_map={
                "Calories": "#1f77b4",
                "Protein": "#ff7f0e"
            }
        )

        fig.update_traces(
            textinfo="label+percent+value",
            hovertemplate="<b>%{label}</b><br>Value: %{value:.2f}<br>Percent: %{percent}<extra></extra>"
        )

        fig.update_layout(height=500, legend_title_text="Metric")
        st.plotly_chart(fig, use_container_width=True)

        st.subheader("Food-wise Nutrition Chart")

        food_chart_df = breakdown_df.melt(
            id_vars=["Meal", "Food Entered"],
            value_vars=["Calories", "Protein (g)"],
            var_name="Metric",
            value_name="Value"
        )

        fig_bar = px.bar(
            food_chart_df,
            x="Food Entered",
            y="Value",
            color="Metric",
            barmode="group",
            facet_row="Meal",
            title="Calories and Protein by Food Item"
        )

        fig_bar.update_layout(height=800)
        st.plotly_chart(fig_bar, use_container_width=True)

    else:
        st.warning("Please enter at least one quantity and food product.")