import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import altair as alt

# Function to calculate the amortization schedule with Sondertilgungen
def calculate_tilgungsplan(auszahlungsdatum, darlehensbetrag, sollzins, sollzinsbindung, ratenhoehe, sondertilgungen, num_sondertilgungen, sondertilgungen_start):
    # Convert sollzins to a monthly interest rate
    monatlicher_zinssatz = (sollzins / 100) / 12

    # Start date
    current_date = datetime.strptime(auszahlungsdatum, "%m.%Y")
    current_date = current_date.replace(day=28) + timedelta(days=4)  # Move to the next month
    current_date = current_date.replace(day=1) - timedelta(days=1)  # Go to last day of the month

    # Sondertilgungen start date
    sondertilgungen_start_date = datetime.strptime(sondertilgungen_start, "%m.%Y")
    sondertilgungen_start_date = sondertilgungen_start_date.replace(day=28) + timedelta(days=4)
    sondertilgungen_start_date = sondertilgungen_start_date.replace(day=1) - timedelta(days=1)

    # Initialize values
    restschuld = darlehensbetrag
    tilgungsplan = []
    gesamt_zins = 0
    gesamt_tilgung = 0
    gesamt_raten = 0

    tilgungsplan.append([
        current_date.strftime("%d.%m.%Y"),
        0,
        0,
        0,
        round(restschuld, 2),
    ])

    current_date = current_date + timedelta(days=32)
    current_date = current_date.replace(day=1) - timedelta(days=1)

    # Track Sondertilgungen
    sondertilgung_dates = []
    if num_sondertilgungen > 0 and sondertilgungen > 0:
        for i in range(num_sondertilgungen):
            sondertilgung_date = sondertilgungen_start_date.replace(year=sondertilgungen_start_date.year + i)
            sondertilgung_dates.append(sondertilgung_date)

    # Generate the schedule
    for _ in range(sollzinsbindung * 12):
        if restschuld <= 0:
            break

        zinsanteil = restschuld * monatlicher_zinssatz
        tilgungsanteil = ratenhoehe - zinsanteil
        
        if tilgungsanteil > restschuld:
            tilgungsanteil = restschuld
            ratenhoehe = zinsanteil + tilgungsanteil

        restschuld -= tilgungsanteil

        # Apply Sondertilgungen
        if current_date in sondertilgung_dates:
            sondertilgung_zinsanteil = 0

            restschuld -= sondertilgungen
            if restschuld < 0:
                restschuld = 0

            tilgungsplan.append([
                current_date.strftime("%d.%m.%Y"),
                "",
                "",
                round(sondertilgungen, 2),
                round(restschuld, 2),
            ])

        gesamt_zins += zinsanteil
        gesamt_tilgung += tilgungsanteil
        gesamt_raten += ratenhoehe

        tilgungsplan.append([
            current_date.strftime("%d.%m.%Y"),
            round(ratenhoehe, 2),
            round(zinsanteil, 2),
            round(tilgungsanteil, 2),
            round(restschuld, 2),
        ])

        current_date = current_date + timedelta(days=32)
        current_date = current_date.replace(day=1) - timedelta(days=1)

    # Correcting the Restschuld column
    for i in range(1, len(tilgungsplan)):
        tilgungsplan[i][4] = tilgungsplan[i-1][4] - tilgungsplan[i-1][3]

    return tilgungsplan, gesamt_raten, gesamt_zins, gesamt_tilgung, restschuld

# Streamlit UI
st.title("Tilgungsrechner mit Sondertilgungen")

# User inputs
auszahlungsdatum = st.text_input("Auszahlungsdatum (MM.YYYY):", value="01.2025")
darlehensbetrag = st.number_input("Darlehensbetrag (EUR):", min_value=0.0, value=400000.0, step=10000.0)
sollzins = st.number_input("Sollzins (p.a. in %):", min_value=0.0, value=3.0, step=0.1)
sollzinsbindung = st.number_input("Sollzinsbindung (Jahre):", min_value=1, value=10, step=1)
ratenhoehe = st.number_input("Ratenhöhe (pro Monat in EUR):", min_value=0.0, value=2000.0, step=100.0)

# Sondertilgungen option
sondertilgungen_option = st.checkbox("Sondertilgungen berücksichtigen")
sondertilgungen = 0
num_sondertilgungen = 0
sondertilgungen_start = "01.2026"

if sondertilgungen_option:
    sondertilgungen = st.number_input("Höhe der Sondertilgung (EUR):", min_value=0.0, value=5000.0, step=100.0)
    num_sondertilgungen = st.number_input("Anzahl der Sondertilgungen:", min_value=1, value=10, step=1)
    sondertilgungen_start = st.text_input("Startdatum der Sondertilgungen (MM.YYYY):", value="01.2026")

# Plotting the Tilgungsplan
if st.button("Berechnen"):
    tilgungsplan, gesamt_raten, gesamt_zins, gesamt_tilgung, restschuld = calculate_tilgungsplan(
        auszahlungsdatum, darlehensbetrag, sollzins, sollzinsbindung, ratenhoehe, sondertilgungen, num_sondertilgungen, sondertilgungen_start
    )

    # Display results
    st.subheader("Ergebnisse")
    st.write(f"Restschuld: {restschuld:.2f} EUR")
    st.write(f"Ratenhöhe pro Monat: {ratenhoehe:.2f} EUR")
    st.write(f"Ratenhöhe pro Jahr: {ratenhoehe * 12:.2f} EUR")
    st.write(f"Summe der Ratenzahlungen: {gesamt_raten:.2f} EUR")
    st.write(f"Enthaltene Zinsleistungen: {gesamt_zins:.2f} EUR")
    st.write(f"Erbrachte Tilgungsleistungen: {gesamt_tilgung:.2f} EUR")

    # Convert tilgungsplan to DataFrame for display
    tilgungsplan_df = pd.DataFrame(
        tilgungsplan,
        columns=["Datum", "Ratenhöhe", "Zinsanteil", "Tilgungsanteil", "Restschuld"]
    )

    # Display the DataFrame
    st.subheader("Tilgungsplan")
    st.dataframe(tilgungsplan_df)

    # Convert Datum column to datetime for plotting
    tilgungsplan_df["Datum"] = pd.to_datetime(tilgungsplan_df["Datum"].str.split(" ").str[0], format="%d.%m.%Y", errors="coerce")

    # Drop rows with NaT values
    tilgungsplan_df.dropna(subset=["Datum"], inplace=True)

    # Plot Restschuld
    st.subheader("Restschuld Verlauf")
    restschuld_chart = pd.DataFrame({
        "Datum": tilgungsplan_df["Datum"],
        "Restschuld": tilgungsplan_df["Restschuld"]
    })
    st.line_chart(restschuld_chart.set_index("Datum"))

    # Plot Zinsanteil and Tilgungsanteil
    t_df = pd.DataFrame(tilgungsplan_df)
    t_df = t_df.drop(columns=['Restschuld']) 
    t_df['Zinsanteil'] = pd.to_numeric(t_df['Zinsanteil'])
    t_df = t_df.dropna()    
    st.subheader("Verlauf von Zinsanteil und Tilgungsanteil")
    other_values_chart = pd.DataFrame({
        "Datum": t_df["Datum"],
        "Zinsanteil": t_df["Zinsanteil"],
        "Tilgungsanteil": t_df["Tilgungsanteil"]
    })
    st.line_chart(other_values_chart.set_index("Datum"))