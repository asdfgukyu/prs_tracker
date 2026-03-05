import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

# ── Colour palette ──────────────────────────────────────────────
C = {
    "black":    "#000000",
    "white":    "#FFFFFF",
    "navy":     "#44546A",
    "offwhite": "#E7E6E6",
    "blue":     "#4477AA",
    "pink":     "#CC6677",
    "yellow":   "#DDCC77",
    "green":    "#117733",
    "lightblue":"#8EC8E7",
    "purple":   "#AA4499",
}

# ── Page config ─────────────────────────────────────────────────
st.set_page_config(
    page_title=" London PRS Dashboard — Renters' Rights Act Impact Tracker",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown(f"""
<style>
  .main {{ background-color: {C['offwhite']}; }}
  .block-container {{ padding-top: 4rem; }}
  h1, h2, h3 {{ color: {C['navy']}; }}
  .kpi-card {{
      background: {C['white']}; border-radius: 8px; padding: 16px 20px;
      box-shadow: 0 1px 4px rgba(0,0,0,0.08);
  }}
  .kpi-value {{ font-size: 28px; font-weight: 700; color: {C['black']}; }}
  .kpi-title {{ font-size: 12px; font-weight: 600; color: {C['navy']}; text-transform: uppercase; letter-spacing: 0.5px; }}
  .kpi-sub   {{ font-size: 11px; color: #888; margin-top: 4px; }}
  .act-banner {{
      background: {C['yellow']}44; border: 2px solid {C['yellow']};
      border-radius: 6px; padding: 10px 16px; margin-bottom: 16px;
      font-size: 14px;
  }}
  .section-badge {{
      display: inline-block; border-radius: 4px; font-size: 11px;
      font-weight: 600; padding: 2px 10px; margin-left: 10px;
  }}
</style>
""", unsafe_allow_html=True)

# ── Load & parse data ────────────────────────────────────────────
XLSX_PATH = "PRS_Tracker.xlsx"

@st.cache_data
def load_all_data(path):
    xl = pd.read_excel(path, sheet_name=None, header=None)

    # ── HomeLet Rental Index ─────────────────────────────────────
    # Row 6 = "Date / UK / Greater London …" header; row 7+ = data
    hom = xl["Homelet Rental Index"].iloc[7:].copy()
    hom.columns = ["_drop", "Date", "UK", "Greater London", "UK change", "London change"]
    hom = hom.dropna(subset=["Date"])
    hom["Date"] = pd.to_datetime(hom["Date"], errors="coerce")
    hom = hom.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    for c in ["Greater London", "UK", "UK change", "London change"]:
        hom[c] = pd.to_numeric(hom[c], errors="coerce")
    # Change series only available from mid-2015; drop NaN rows for change chart
    hom_change = hom.dropna(subset=["UK change", "London change"]).copy()
    hom_change["UK change"] = hom_change["UK change"] * 100      # convert to %
    hom_change["London change"] = hom_change["London change"] * 100

    # ── Rightmove rental supply (14-day listings) ────────────────
    # Row 6 = "To rent / To buy" spans; row 7 = column headers; row 8+ = data
    rm = xl["Rental supply rightmove"].iloc[8:].copy()
    rm.columns = ["_drop", "Date", "Day", "24h", "7d", "14d", "Any",
                  "24h_b", "7d_b", "14d_b", "Any_b"]
    rm = rm.dropna(subset=["Date"])
    rm["Date"] = pd.to_datetime(rm["Date"], errors="coerce")
    rm = rm.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    rm["14d"] = pd.to_numeric(rm["14d"], errors="coerce")
    rm_14d = rm.dropna(subset=["14d"])[["Date", "14d"]].copy()

    # ── ONS PIPR annual change (London) ──────────────────────────
    # Row 6 = header row ("Date / Barking and Dagenham / … / London …"); row 7+ = data
    pipr_df = xl["PIPR Annual change"]
    pipr_headers = pipr_df.iloc[6].tolist()
    pipr = pipr_df.iloc[7:].copy()
    pipr.columns = pipr_headers
    pipr = pipr.dropna(subset=["Date"])
    pipr["Date"] = pd.to_datetime(pipr["Date"], errors="coerce")
    pipr = pipr.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    pipr["London"] = pd.to_numeric(pipr["London"], errors="coerce")

    # ── Homeless prevention duty ──────────────────────────────────
    # Row 6 = header; row 7+ = data
    hp = xl["Homeless prevention duty"].iloc[7:].copy()
    hp.columns = ["_drop", "Date", "Region", "Rent arrears", "Sell property",
                  "Re-let property", "Retire", "Disrepair complaint",
                  "Illegal eviction", "Tenant abandoned", "Other"]
    hp = hp.dropna(subset=["Date"]).reset_index(drop=True)
    hp["Date"] = pd.to_datetime(hp["Date"], errors="coerce")
    HP_BANDS = ["Rent arrears", "Sell property", "Re-let property", "Retire",
                "Disrepair complaint", "Illegal eviction", "Tenant abandoned"]
    for col in HP_BANDS:
        hp[col] = pd.to_numeric(hp[col], errors="coerce").fillna(0)
    hp["Total"] = hp[HP_BANDS].sum(axis=1)
    hp["Quarter"] = hp["Date"].dt.to_period("Q").astype(str)
    hp = hp.dropna(subset=["Date"]).reset_index(drop=True)

    # ── Rightmove Rental Price Tracker (annual % change) ─────────
    # Row 6 = header; row 7+ = data
    rm_tracker = xl["Rightmove Rental Price Tracker"].iloc[7:].copy()
    rm_tracker.columns = ["_drop", "Quarter", "London", "Inner London",
                          "Outer London", "Rest of Britain"]
    rm_tracker = rm_tracker.dropna(subset=["Quarter"]).reset_index(drop=True)
    for c in ["London", "Inner London", "Outer London", "Rest of Britain"]:
        rm_tracker[c] = pd.to_numeric(rm_tracker[c], errors="coerce") * 100  # convert to %

    # ── RICS landlord instructions ────────────────────────────────
    # Row 7 = column headers; row 8+ = data
    rics = xl["RICS rental sentiment"].iloc[8:].copy()
    rics.columns = ["_drop", "Quarter", "Tenant demand EW", "Tenant demand London",
                    "Landlord instr EW", "Landlord instr London"]
    rics = rics.dropna(subset=["Quarter"]).reset_index(drop=True)
    for c in ["Tenant demand EW", "Tenant demand London",
              "Landlord instr EW", "Landlord instr London"]:
        rics[c] = pd.to_numeric(rics[c], errors="coerce")

    # ── Met Police illegal evictions (annual totals) ──────────────
    # Row 5 = header; row 6+ = data (last row = Grand Total)
    ev = xl["Met Illegal eviction"].iloc[6:].copy()
    ev.columns = ["_drop", "Borough", "2019", "2020", "2021", "2022", "2023"]
    ev = ev.dropna(subset=["Borough"]).reset_index(drop=True)
    ev_total = ev[ev["Borough"] == "Grand Total"].iloc[0]
    eviction_df = pd.DataFrame({
        "Year": ["2019", "2020", "2021", "2022", "2023"],
        "Cases": [pd.to_numeric(ev_total[y], errors="coerce")
                  for y in ["2019", "2020", "2021", "2022", "2023"]]
    })

    # ── Category 1 hazard (PRS, London) ──────────────────────────
    # Row 5 = header; row 6+ = data
    hz = xl["Category 1 hazard"].iloc[6:].copy()
    hz.columns = ["_drop", "ehsyear", "london", "tenure3", "not_cat1", "cat1", "rate"]
    hz = hz.dropna(subset=["ehsyear"]).reset_index(drop=True)
    hz_prs = hz[hz["tenure3"] == "Private rented"].copy()
    hz_prs["rate"] = pd.to_numeric(hz_prs["rate"], errors="coerce")
    hz_prs["ehsyear"] = hz_prs["ehsyear"].astype(int).astype(str)

    # ── Landlord type (EPLS 2024) ─────────────────────────────────
    # Row 5 = header; row 6+ = data
    lt = xl["Landlord type"].iloc[6:].copy()
    lt.columns = ["_drop", "Type", "n", "pct"]
    lt = lt.dropna(subset=["Type"]).reset_index(drop=True)
    lt["pct"] = pd.to_numeric(lt["pct"], errors="coerce")
    lt = lt.dropna(subset=["pct"]).reset_index(drop=True)
    lt["Type_short"] = ["Individual", "Company", "Both", "Other"][:len(lt)]
    lt["pct_pct"] = (lt["pct"] * 100).round(1)

    # ── Portfolio size (EPLS 2024) ────────────────────────────────
    pt = xl["Size of portfolio"].iloc[6:].copy()
    pt.columns = ["_drop", "Size", "n", "pct"]
    pt = pt.dropna(subset=["Size"]).reset_index(drop=True)
    pt["pct"] = pd.to_numeric(pt["pct"], errors="coerce")
    pt = pt.dropna(subset=["pct"]).reset_index(drop=True)
    pt["Size_short"] = ["1 property", "2–4", "5+", "Other"][:len(pt)]
    pt["pct_pct"] = (pt["pct"] * 100).round(1)

    # ── Guarantor required (EPLS 2024) ───────────────────────────
    guar = xl["Gaurantor EPLS"].iloc[6:].copy()
    guar.columns = ["_drop", "ReqGuaRent", "weighted_n", "pct"]
    guar = guar.dropna(subset=["ReqGuaRent"]).reset_index(drop=True)
    guar["pct"] = pd.to_numeric(guar["pct"], errors="coerce")

    # ── Households in PRS (EHS, London rates) ────────────────────
    # Rate section: header at row 7, data rows 8-23
    hh_df = xl["Households in PRS"]
    hh = hh_df.iloc[8:24].copy()
    hh.columns = ["_drop", "ehsyear", "owners", "social", "prs"]
    hh = hh.dropna(subset=["ehsyear"]).reset_index(drop=True)
    hh = hh[hh["ehsyear"].astype(str).str.match(r"^\d{4}", na=False)].copy()
    for c in ["owners", "social", "prs"]:
        hh[c] = pd.to_numeric(hh[c], errors="coerce")
    hh["ehsyear"] = hh["ehsyear"].astype(int).astype(str)

    # ── Length of stay (private renters, London) ──────────────────
    # Row 7 = header; rows 8-19 = annual data (single-year, not rolling)
    los_df = xl["Length of stay"]
    los = los_df.iloc[8:20].copy()
    los.columns = ["_drop", "ehsyear", "0-1yr", "2yr", "3-4yr", "5-9yr", "10+yr",
                   "_r0", "_r1", "_r2", "_r3", "_r4", "_x1", "_x2"]
    los = los.dropna(subset=["ehsyear"]).reset_index(drop=True)
    los = los[los["ehsyear"].astype(str).str.match(r"^\d{4}", na=False)].copy()
    los["ehsyear"] = los["ehsyear"].astype(int).astype(str)
    for c in ["0-1yr", "2yr", "3-4yr", "5-9yr", "10+yr"]:
        los[c] = pd.to_numeric(los[c], errors="coerce")

    return hom, hom_change, rm_14d, rm_tracker, pipr, hp, rics, eviction_df, hz_prs, lt, pt, guar, hh, los


hom, hom_change, rm_14d, rm_tracker, pipr, hp, rics, eviction_df, hz_prs, lt, pt, guar, hh, los = load_all_data(XLSX_PATH)

# ── Derived KPIs ──────────────────────────────────────────────────
latest_rent      = hom["Greater London"].iloc[-1]
rent_date        = hom["Date"].iloc[-1].strftime("%b %Y")
latest_listings  = int(rm_14d["14d"].iloc[-1])
listings_date    = rm_14d["Date"].iloc[-1].strftime("%b %Y")
latest_pipr      = pipr["London"].iloc[-1]
pipr_date        = pipr["Date"].iloc[-1].strftime("%b %Y")
latest_homeless  = int(hp["Total"].iloc[-1])
homeless_q       = hp["Quarter"].iloc[-1]
rics_row         = rics.dropna(subset=["Landlord instr London"]).iloc[-1]
latest_rics      = rics_row["Landlord instr London"]
rics_q           = rics_row["Quarter"]
eviction_latest  = int(eviction_df["Cases"].iloc[-1])
eviction_year    = eviction_df["Year"].iloc[-1]
hz_latest_rate   = hz_prs["rate"].iloc[-1]
hz_latest_year   = hz_prs["ehsyear"].iloc[-1]
prs_share        = hh["prs"].iloc[-1]
prs_year         = hh["ehsyear"].iloc[-1]
guar_pct         = guar[guar["ReqGuaRent"].isin([
    "A guarantor",
    "Rent in advance, in addition to a deposit",
    "Both"
])]["pct"].sum()

ACT_DATE       = "2026-05-01"   # Act in force — May 2026
ASSENT_DATE    = "2025-10-01"   # Royal Assent — Oct 2025


def _vline(fig, x, label, color, y_label=0.97):
    fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1,
                  xref="x", yref="paper",
                  line=dict(color=color, width=2, dash="dash"))
    fig.add_annotation(x=x, y=y_label, xref="x", yref="paper", text=label,
                       showarrow=False, font=dict(color=color, size=10),
                       yanchor="top", xanchor="left",
                       bgcolor="rgba(255,255,255,0.7)", borderpad=2)


def add_reference_lines_date(fig):
    """For charts whose x-axis is a datetime / date string (ISO format)."""
    _vline(fig, ASSENT_DATE, "Royal Assent Oct 2025", C["lightblue"], y_label=0.97)
    _vline(fig, ACT_DATE,    "Act in force May 2026",  C["yellow"],    y_label=0.80)


def add_reference_lines_quarter(fig):
    """For charts where x-axis uses quarter strings like '2025 Q4'."""
    _vline(fig, "2025 Q4", "Royal Assent Oct 2025", C["lightblue"], y_label=0.97)
    _vline(fig, "2026 Q2", "Act in force May 2026",  C["yellow"],    y_label=0.80)


# ── Header ───────────────────────────────────────────────────────
st.markdown(f"""
<div style="background:{C['navy']}; padding:16px 24px; border-radius:8px; margin-bottom:16px;">
  <span style="color:{C['white']}; font-size:20px; font-weight:700;">
      London Private Rented Sector Dashboard
  </span><br>
  <span style="color:{C['lightblue']}; font-size:13px;">
      Tracking the impact of the Renters' Rights Act — London focus
  </span>
</div>
""", unsafe_allow_html=True)

st.markdown("""
<div class="act-banner">
  ⚑ <strong>Renters' Rights Act</strong> — Royal Assent granted <strong>October 2025</strong>.
  Act comes into force <strong>May 2026</strong>. Charts show reference lines at both points.
</div>
""", unsafe_allow_html=True)

eng_toggle = st.toggle("Show England / UK comparison", value=False)

tab1, tab2 = st.tabs([
    "📊 Market Monitoring — Quarterly / Monthly",
    "📋 Sector Context — Annual / One-off"
])

# ════════════════════════════════════════════════════════════════
# TAB 1 — MARKET MONITORING
# ════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(
        "### Key Indicators &nbsp;"
        "<span class='section-badge' style='background:#4477AA22;color:#4477AA;"
        "border:1px solid #4477AA'>Regularly Updated</span>",
        unsafe_allow_html=True
    )

    k1, k2, k3= st.columns(3)
    for col, title, val, sub, accent in [
        (k1, "Avg. Asking Rent",  f"£{int(latest_rent):,}",    f"HomeLet — {rent_date}",       C["blue"]),
        (k2, "New Listings (14 days)",      f"{latest_listings:,}",      f"Rightmove — {listings_date}", C["lightblue"]),
        # (k3, "RICS Landlord Sentiment",     f"{latest_rics:.0f}",        f"RICS — {rics_q}",             C["pink"]),
        # (k4, "Homeless Prevention Cases",   f"{latest_homeless:,}",      f"{homeless_q}",                C["purple"]),
        (k3, "Annual Rent Change", f"{latest_pipr:+.1f}%",      f"ONS PIPR — {pipr_date}",      C["green"]),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left:4px solid {accent}">
              <div class="kpi-title">{title}</div>
              <div class="kpi-value">{val}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Annual Rent Change (%)** — HomeLet Rental Index")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hom_change["Date"], y=hom_change["London change"],
            name="London", line=dict(color=C["blue"], width=2)))
        fig.add_trace(go.Scatter(x=hom_change["Date"], y=hom_change["UK change"],
            name="UK", line=dict(color=C["lightblue"], width=2,
            dash="dot" if not eng_toggle else "solid"),
            visible=True if eng_toggle else "legendonly"))
        fig.add_hline(y=0, line=dict(color=C["black"], width=1))
        add_reference_lines_date(fig)
        fig.update_layout(height=280, margin=dict(l=0, r=0, t=8, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            yaxis=dict(ticksuffix="%"), legend=dict(font=dict(size=11)))
        fig.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("**Annual Asking Rent Change (%)** — Rightmove Rental Price Tracker")
        rm_colors = {
            "London":          C["blue"],
            "Inner London":    C["pink"],
            "Outer London":    C["yellow"],
            "Rest of Britain": C["green"],
        }
        quarters = rm_tracker["Quarter"].tolist()
        x_idx = list(range(len(quarters)))
        # Royal Assent = Oct 2025 → sits inside Q4 2025, which is index 21
        # Act in force = May 2026 → ~1.5 quarters beyond last data point
        assent_x = quarters.index("2025 Q4") if "2025 Q4" in quarters else len(quarters) - 1
        act_x    = len(quarters) - 1 + 1.5   # project beyond last point

        fig2 = go.Figure()
        for series, color in rm_colors.items():
            if not eng_toggle and series == "Rest of Britain":
                continue
            fig2.add_trace(go.Scatter(
                x=x_idx, y=rm_tracker[series].tolist(),
                name=series, line=dict(color=color, width=2)))
        fig2.add_hline(y=0, line=dict(color=C["black"], width=1))
        for x_pos, label, color, y_label in [
            (assent_x, "Royal Assent Oct 2025", C["lightblue"], 0.97),
            (act_x,    "Act in force May 2026",  C["yellow"],    0.80),
        ]:
            fig2.add_shape(type="line", x0=x_pos, x1=x_pos, y0=0, y1=1,
                           xref="x", yref="paper",
                           line=dict(color=color, width=2, dash="dash"))
            fig2.add_annotation(x=x_pos, y=y_label, xref="x", yref="paper", text=label,
                                showarrow=False, font=dict(color=color, size=10),
                                yanchor="top", xanchor="left",
                                bgcolor="rgba(255,255,255,0.7)", borderpad=2)
        fig2.update_layout(height=280, margin=dict(l=0, r=20, t=8, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            yaxis=dict(ticksuffix="%"), legend=dict(font=dict(size=11)),
            xaxis=dict(
                tickmode="array",
                tickvals=x_idx[::2],
                ticktext=quarters[::2],
                tickangle=45,
            ))
        fig2.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig2.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig2, use_container_width=True)

    col3, col4 = st.columns(2)

    with col3:
        st.markdown("**Annual Rent Change (%)** — ONS Price Index of Private Rents")
        fig3 = go.Figure()
        fig3.add_trace(go.Scatter(x=pipr["Date"], y=pipr["London"],
            name="London", line=dict(color=C["pink"], width=2)))
        add_reference_lines_date(fig3)
        fig3.update_layout(height=280, margin=dict(l=0, r=0, t=8, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            showlegend=False, yaxis=dict(ticksuffix="%"))
        fig3.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig3.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig3, use_container_width=True)

    with col4:
        st.markdown("**Homeless Prevention Duty — by Reason** — MHCLG")
        hp_colors = [C["blue"], C["purple"], C["lightblue"], C["yellow"],
                     C["pink"], C["green"], C["navy"]]
        hp_labels = {
            "Rent arrears":       "Rent arrears (rent increase)",
            "Sell property":      "Landlord selling",
            "Re-let property":    "Landlord re-letting",
            "Retire":             "Landlord retiring",
            "Disrepair complaint":"Tenant complained — disrepair",
            "Illegal eviction":   "Illegal eviction",
            "Tenant abandoned":   "Tenant abandoned property",
        }
        fig4 = go.Figure()
        for (band, label), color in zip(hp_labels.items(), hp_colors):
            fig4.add_trace(go.Bar(
                x=hp["Quarter"], y=hp[band],
                name=label, marker_color=color))
        fig4.update_layout(
            barmode="stack",
            height=280, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            legend=dict(font=dict(size=10), orientation="v",
                        x=1.01, y=1, xanchor="left"))
        fig4.update_xaxes(showgrid=False)
        fig4.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig4, use_container_width=True)

    col5, col6 = st.columns(2)
    with col5:
        st.markdown("**Tenant Demand & Landlord Instructions** — RICS UK Residential Market Survey")
        rics_plot = rics.dropna(subset=["Landlord instr London"]).copy()
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(x=rics_plot["Quarter"], y=rics_plot["Tenant demand London"],
            name="Tenant demand — London", line=dict(color=C["blue"], width=2)))
        fig5.add_trace(go.Scatter(x=rics_plot["Quarter"], y=rics_plot["Landlord instr London"],
            name="Landlord instructions — London", line=dict(color=C["pink"], width=2)))
        if eng_toggle:
            fig5.add_trace(go.Scatter(x=rics_plot["Quarter"], y=rics_plot["Tenant demand EW"],
                name="Tenant demand — E&W", line=dict(color=C["lightblue"], width=2, dash="dot")))
            fig5.add_trace(go.Scatter(x=rics_plot["Quarter"], y=rics_plot["Landlord instr EW"],
                name="Landlord instr. — E&W", line=dict(color=C["yellow"], width=2, dash="dot")))
        fig5.add_hline(y=0, line=dict(color=C["black"], width=1))
        fig5.update_layout(height=380, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            legend=dict(font=dict(size=11), orientation="h",
                yanchor="bottom", y=1.02, xanchor="left", x=0))
        fig5.update_xaxes(showgrid=True, gridcolor=C["offwhite"], tickangle=45, nticks=20)
        fig5.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig5, use_container_width=True)

    with col6:
        st.markdown("**Rental Listings listed on Rightmove in the last 14 days** — Rightmove via GLA")
        fig6 = go.Figure()
        fig6.add_trace(go.Scatter(x=rm_14d["Date"], y=rm_14d["14d"],
            name="London", line=dict(color=C["green"], width=2)))
        add_reference_lines_date(fig6)
        fig6.update_layout(height=380, margin=dict(l=0, r=0, t=8, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            showlegend=False, yaxis=dict(ticksuffix="k"))
        fig6.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig6.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig6, use_container_width=True)

    st.markdown("### Data Table — Market Monitoring")
    monitor_df = pd.DataFrame([
        ["HomeLet Rental Index",         "Avg. asking rent (London)",        f"£{int(latest_rent):,} pcm", "—", rent_date,     "Monthly"],
        ["Rightmove Rental Price Tracker", "Annual rent change — London",       f"{rm_tracker['London'].iloc[-1]:+.1f}%",  "—", rm_tracker['Quarter'].iloc[-1], "Quarterly"],
        ["ONS Price Index of Priv Rent", "Annual rent change (London)",       f"{latest_pipr:+.1f}%",       "—", pipr_date,     "Monthly"],
        ["RICS",                          "Landlord instr. sentiment (Lon)", f"{latest_rics:.0f}",          "—", rics_q,        "Quarterly"],
        ["MHCLG Homelessness Stats",     "Prevention duty cases (London)",    f"{latest_homeless:,}",       "—", homeless_q,    "Quarterly"],
        ["Met Police (FOI)",             "Illegal eviction cases (London)",   str(eviction_latest),          "—", eviction_year, "One-off"],
    ], columns=["Source", "Metric", "London", "England/UK", "Period", "Frequency"])
    if not eng_toggle:
        monitor_df["England/UK"] = "—"
    st.dataframe(monitor_df, use_container_width=True, hide_index=True)


# ════════════════════════════════════════════════════════════════
# TAB 2 — SECTOR CONTEXT
# ════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(
        "### Sector Context &nbsp;"
        "<span class='section-badge' style='background:#AA449922;color:#AA4499;"
        "border:1px solid #AA4499'>Annual / One-off</span>",
        unsafe_allow_html=True
    )

    k1, k2, k3, k4,  = st.columns(4)
    for col, title, val, sub, accent in [
        (k1, "Proportion of households in PRS", f"{prs_share:.1%}",             f"EHS {prs_year}",             C["purple"]),
        (k2, "PRS households in Cat 1 hazards homes", f"{hz_latest_rate:.1%}",        f"EHS {hz_latest_year}",       C["pink"]),
        # (k3, "Illegal Eviction Cases",      str(eviction_latest),           f"Met Police {eviction_year}", C["yellow"]),
        (k3, "Guarantor/Advance Required", f"{guar_pct:.0%}",              "EPLS 2024",           C["green"]),
        (k4, "Landlord type — Individual", f"{lt['pct'].iloc[0]:.0%}",     "EPLS 2024",                    C["yellow"]),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left:4px solid {accent}">
              <div class="kpi-title">{title}</div>
              <div class="kpi-value">{val}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Row 1: PRS share line (wide) + Cat 1 hazard line (narrow) ─
    col_wide, col_narrow = st.columns([3, 1])

    with col_wide:
        st.markdown("** Households by tenure (%)** — English Housing Survey")
        fig_tenure = go.Figure()
        for tenure_col, label, color in [
            ("prs",    "Private renters", C["purple"]),
            ("social", "Social sector",   C["green"]),
            ("owners", "Owner occupiers", C["blue"]),
        ]:
            fig_tenure.add_trace(go.Scatter(
                x=hh["ehsyear"], y=(hh[tenure_col] * 100).round(1),
                name=label, line=dict(color=color, width=2),
                mode="lines+markers", marker=dict(size=6)
            ))
        fig_tenure.update_layout(height=270, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            yaxis=dict(ticksuffix="%", rangemode="tozero"),
            legend=dict(font=dict(size=11), orientation="h",
                yanchor="bottom", y=1.02, xanchor="left", x=0))
        fig_tenure.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig_tenure.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_tenure, use_container_width=True)

    with col_narrow:
        st.markdown("**Cat 1 Hazards (% PRS)** — English Housing Survey")
        fig_hz = go.Figure()
        fig_hz.add_trace(go.Scatter(
            x=hz_prs["ehsyear"], y=(hz_prs["rate"] * 100).round(1),
            line=dict(color=C["pink"], width=2), mode="lines+markers",
            marker=dict(size=7)
        ))
        fig_hz.update_layout(height=270, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            yaxis=dict(ticksuffix="%", rangemode="tozero"), showlegend=False)
        fig_hz.update_xaxes(showgrid=True, gridcolor=C["offwhite"], tickangle=45)
        fig_hz.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_hz, use_container_width=True)

    # ── Row 2: Guarantor pie charts + Length of stay stacked bar ──
    col_pie, col_stay = st.columns([1, 2])

    with col_pie:
        st.markdown("**Guarantor / Advance Required** — English Private Landlord Survey 2024")
        # Simplify into three slices: Guarantor only, Rent advance only, Both, Neither
        guar_labels = ["Guarantor", "Rent advance", "Both", "Neither", "Don't know"]
        guar_map    = {
            "A guarantor":                               "Guarantor",
            "Rent in advance, in addition to a deposit": "Rent advance",
            "Both":                                      "Both",
            "Neither":                                   "Neither",
            "Don't know":                                "Don't know",
        }
        guar_plot = guar.copy()
        guar_plot["Label"] = guar_plot["ReqGuaRent"].map(guar_map)
        guar_plot = guar_plot.dropna(subset=["Label", "pct"])
        pie_colors = [C["green"], C["blue"], C["purple"], C["offwhite"], C["lightblue"]]
        fig_pie = go.Figure(go.Pie(
            labels=guar_plot["Label"],
            values=(guar_plot["pct"] * 100).round(1),
            marker=dict(colors=pie_colors,
                        line=dict(color=C["white"], width=2)),
            textinfo="label+percent",
            textfont=dict(size=11),
            hole=0.35,
        ))
        fig_pie.update_layout(height=270, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], showlegend=False)
        st.plotly_chart(fig_pie, use_container_width=True)

    with col_stay:
        st.markdown("**Length of Current Stay — Private Renters (%)** — English Housing Survey")
        stay_bands = {
            "0–1 yr":  "0-1yr",
            "2 yrs":   "2yr",
            "3–4 yrs": "3-4yr",
            "5–9 yrs": "5-9yr",
            "10+ yrs": "10+yr",
        }
        stay_colors = [C["blue"], C["lightblue"], C["green"], C["yellow"], C["pink"]]
        fig_stay = go.Figure()
        for (label, col_key), color in zip(stay_bands.items(), stay_colors):
            fig_stay.add_trace(go.Bar(
                x=los["ehsyear"],
                y=(los[col_key] * 100).round(1),
                name=label,
                marker_color=color,
            ))
        fig_stay.update_layout(
            barmode="stack",
            height=270, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            yaxis=dict(ticksuffix="%", range=[0, 100]),
            legend=dict(font=dict(size=11), orientation="h",
                yanchor="bottom", y=1.02, xanchor="left", x=0)
        )
        fig_stay.update_xaxes(showgrid=False, gridcolor=C["offwhite"])
        fig_stay.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_stay, use_container_width=True)

    # ── Row 3: Landlord type + portfolio size + illegal evictions ──
    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Landlord Type** — English Private Landlord Survey 2024")
        fig_lt = px.bar(lt, x="pct_pct", y="Type_short", orientation="h",
            color_discrete_sequence=[C["blue"]])
        fig_lt.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            xaxis_ticksuffix="%", showlegend=False, xaxis_title="", yaxis_title="")
        fig_lt.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig_lt.update_yaxes(showgrid=False)
        st.plotly_chart(fig_lt, use_container_width=True)

    with col2:
        st.markdown("**Portfolio Size** — English Private Landlord Survey 2024")
        fig_pt = px.bar(pt, x="pct_pct", y="Size_short", orientation="h",
            color_discrete_sequence=[C["purple"]])
        fig_pt.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            xaxis_ticksuffix="%", showlegend=False, xaxis_title="", yaxis_title="")
        fig_pt.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig_pt.update_yaxes(showgrid=False)
        st.plotly_chart(fig_pt, use_container_width=True)

    with col3:
        st.markdown("**Illegal Eviction Cases** — Met Police")
        fig_ev = go.Figure()
        fig_ev.add_trace(go.Bar(x=eviction_df["Year"], y=eviction_df["Cases"],
            marker_color=C["yellow"]))
        fig_ev.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"], showlegend=False)
        fig_ev.update_xaxes(showgrid=False)
        fig_ev.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_ev, use_container_width=True)

    # ── Data table ────────────────────────────────────────────────
    st.markdown("### Data Table — Sector Context")
    context_df = pd.DataFrame([
        ["English Housing Survey", "PRS share of stock",           f"{prs_share:.1%}",            "—", prs_year,       "Annual"],
        ["EPLS 2024",              "Guarantor/advance required",   f"{guar_pct:.0%}",             "—", "2024",         "One-off"],
        ["EPLS 2024",              "Landlord type — individual",   f"{lt['pct'].iloc[0]:.0%}",    "—", "2024",         "One-off"],
        ["EPLS 2024",              "Portfolio size — 1 property",  f"{pt['pct'].iloc[0]:.0%}",    "—", "2024",         "One-off"],
        ["English Housing Survey", "Cat 1 hazard homes (PRS)",     f"{hz_latest_rate:.1%}",       "—", hz_latest_year, "Annual"],
        ["Met Police",             "Illegal eviction cases",       str(eviction_latest),           "—", eviction_year,  "One-off (FOI)"],
    ], columns=["Source", "Metric", "London", "England", "Year", "Frequency"])
    if not eng_toggle:
        context_df["England"] = "—"
    st.dataframe(context_df, use_container_width=True, hide_index=True)