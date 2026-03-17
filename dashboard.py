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
    "grey":     "#AEAAAA",
}

# ── Commentary ───────────────────────────────────────────────────
# Edit bullet points here — one key per section.
# Add or remove strings from each list freely.
COMMENTARY = {
    # Rental Price Indexes — right-hand panel bullets (3 sources compared)
    "rent_indexes": [
        "The ONS PIPR is the official measure of private rent inflation, covering all tenancies including renewals",
        "The Rightmove tracker reflects asking rents on new listings only — typically a leading indicator",
        "HomeLet captures agreed rents on new tenancies, sitting between the two in terms of coverage",
    ],
    # Rental Price Indexes — full-width notes below all 3 charts
    "rent_indexes_notes": [
        "All three indices show London rent growth easing from peaks seen in 2022–23",
        "Divergence between indices reflects methodological differences: ONS lags due to inclusion of existing tenancies, while Rightmove moves first as a new-listings measure",
        "Add further notes or external source commentary here",
    ],
    # Homelessness — full-width notes below all 3 charts
    "homelessness_notes": [
        "Add homelessness commentary here",
        "Additional notes from external sources can go here",
    ],
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
    hom = xl["Homelet Rental Index"].iloc[7:].copy()
    hom.columns = ["_drop", "Date", "UK", "Greater London", "UK change", "London change"]
    hom = hom.dropna(subset=["Date"])
    hom["Date"] = pd.to_datetime(hom["Date"], errors="coerce")
    hom = hom.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    for c in ["Greater London", "UK", "UK change", "London change"]:
        hom[c] = pd.to_numeric(hom[c], errors="coerce")
    hom_change = hom.dropna(subset=["UK change", "London change"]).copy()
    hom_change = hom_change[hom_change["Date"] >= "2019-01-01"].reset_index(drop=True)
    hom_change["UK change"] = hom_change["UK change"] * 100
    hom_change["London change"] = hom_change["London change"] * 100

    # ── Rightmove rental supply (14-day listings) ────────────────
    rm = xl["Rental supply rightmove"].iloc[8:].copy()
    rm.columns = ["_drop", "Date", "Day", "24h", "7d", "14d", "Any",
                  "24h_b", "7d_b", "14d_b", "Any_b"]
    rm = rm.dropna(subset=["Date"])
    rm["Date"] = pd.to_datetime(rm["Date"], errors="coerce")
    rm = rm.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    rm["14d"] = pd.to_numeric(rm["14d"], errors="coerce")
    rm_14d = rm.dropna(subset=["14d"])[["Date", "14d"]].copy()

    # ── ONS PIPR annual change (London) ──────────────────────────
    pipr_df = xl["PIPR Annual change"]
    pipr_headers = pipr_df.iloc[6].tolist()
    pipr = pipr_df.iloc[7:].copy()
    pipr.columns = pipr_headers
    pipr = pipr.dropna(subset=["Date"])
    pipr["Date"] = pd.to_datetime(pipr["Date"], errors="coerce")
    pipr = pipr.dropna(subset=["Date"]).sort_values("Date").reset_index(drop=True)
    pipr["London"] = pd.to_numeric(pipr["London"], errors="coerce")

    # ── Prevention duty by reason ─────────────────────────────────
    hp = xl["Prevention duty by reason"].iloc[7:].copy()
    hp.columns = ["_drop", "Date", "Region",
                  "Total rent arrears", "Rent arrears (rent increase)",
                  "Sell property", "Re-let property", "Retire",
                  "Disrepair complaint", "Illegal eviction",
                  "Tenant abandoned", "Other"]
    hp = hp.dropna(subset=["Date"]).reset_index(drop=True)
    hp["Date"] = pd.to_datetime(hp["Date"], errors="coerce")
    for col in ["Total rent arrears", "Rent arrears (rent increase)", "Sell property",
                "Re-let property", "Retire", "Disrepair complaint",
                "Illegal eviction", "Tenant abandoned", "Other"]:
        hp[col] = pd.to_numeric(hp[col], errors="coerce").fillna(0)
    # Lump Retire, Tenant abandoned and Other into one category
    hp["Other reasons"] = hp["Retire"] + hp["Tenant abandoned"] + hp["Other"]
    HP_BANDS = ["Total rent arrears", "Rent arrears (rent increase)",
                "Sell property", "Re-let property",
                "Disrepair complaint", "Illegal eviction", "Other reasons"]
    hp["Total"] = hp[HP_BANDS].sum(axis=1)
    hp["Quarter"] = hp["Date"].dt.to_period("Q").astype(str)
    hp = hp.dropna(subset=["Date"]).reset_index(drop=True)

    # ── Relief duty by reason ─────────────────────────────────
    rd = xl["Relief duty by reason"].iloc[7:].copy()
    rd.columns = ["_drop", "Date", "Region",
                  "Total rent arrears", "Rent arrears (rent increase)",
                  "Sell property", "Re-let property", "Retire",
                  "Disrepair complaint", "Illegal eviction",
                  "Tenant abandoned", "Other"]
    rd = rd.dropna(subset=["Date"]).reset_index(drop=True)
    rd["Date"] = pd.to_datetime(rd["Date"], errors="coerce")
    for col in ["Total rent arrears", "Rent arrears (rent increase)", "Sell property",
                "Re-let property", "Retire", "Disrepair complaint",
                "Illegal eviction", "Tenant abandoned", "Other"]:
        rd[col] = pd.to_numeric(rd[col], errors="coerce").fillna(0)
    # Lump Retire, Tenant abandoned and Other into one category
    rd["Other reasons"] = rd["Retire"] + rd["Tenant abandoned"] + rd["Other"]
    RD_BANDS = ["Total rent arrears", "Rent arrears (rent increase)",
                "Sell property", "Re-let property",
                "Disrepair complaint", "Illegal eviction", "Other reasons"]
    rd["Total"] = rd[RD_BANDS].sum(axis=1)
    rd["Quarter"] = rd["Date"].dt.to_period("Q").astype(str)
    rd = rd.dropna(subset=["Date"]).reset_index(drop=True)

    # ── S21 Prevention duty ─────────────────────────────────
    s21 = xl["Prevention duty S21"].iloc[7:].copy()
    s21.columns = ["_drop", "Date", "Region",
                    "Prevention duty owed due to S21"]
    s21 = s21.dropna(subset=["Date"]).reset_index(drop=True)
    s21["Date"] = pd.to_datetime(s21["Date"], errors="coerce")
    S21_BANDS = ["Prevention duty owed due to S21"]
    for col in S21_BANDS:
        s21[col] = pd.to_numeric(s21[col], errors="coerce").fillna(0)
    s21["Total"] = s21[S21_BANDS].sum(axis=1)
    s21["Quarter"] = s21["Date"].dt.to_period("Q").astype(str)
    s21 =s21.dropna(subset=["Date"]).reset_index(drop=True)

    # ── Rightmove Rental Price Tracker (annual % change) ─────────
    rm_tracker = xl["Rightmove Rental Price Tracker"].iloc[7:].copy()
    rm_tracker.columns = ["_drop", "Quarter", "London", "Inner London",
                          "Outer London", "Rest of Britain"]
    rm_tracker = rm_tracker.dropna(subset=["Quarter"]).reset_index(drop=True)
    for c in ["London", "Inner London", "Outer London", "Rest of Britain"]:
        rm_tracker[c] = pd.to_numeric(rm_tracker[c], errors="coerce") * 100

    # ── RICS landlord instructions ────────────────────────────────
    rics = xl["RICS rental sentiment"].iloc[8:].copy()
    rics.columns = ["_drop", "Quarter", "Tenant demand EW", "Tenant demand London",
                    "Landlord instr EW", "Landlord instr London"]
    rics = rics.dropna(subset=["Quarter"]).reset_index(drop=True)
    for c in ["Tenant demand EW", "Tenant demand London",
              "Landlord instr EW", "Landlord instr London"]:
        rics[c] = pd.to_numeric(rics[c], errors="coerce")
    rics = rics[rics["Quarter"].str[:4] >= "2019"].reset_index(drop=True)

    # ── Met Police illegal evictions (annual totals) ──────────────
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
    hz = xl["Category 1 hazard"].iloc[6:].copy()
    hz.columns = ["_drop", "ehsyear", "london", "tenure3", "not_cat1", "cat1", "rate"]
    hz = hz.dropna(subset=["ehsyear"]).reset_index(drop=True)
    hz_prs = hz[hz["tenure3"] == "Private rented"].copy()
    hz_prs["rate"] = pd.to_numeric(hz_prs["rate"], errors="coerce")
    hz_prs["ehsyear"] = hz_prs["ehsyear"].astype(int).astype(str)

    # ── Landlord type (EPLS 2024) ─────────────────────────────────
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
    hh_df = xl["Households in PRS"]
    hh = hh_df.iloc[8:24].copy()
    hh.columns = ["_drop", "ehsyear", "owners", "social", "prs"]
    hh = hh.dropna(subset=["ehsyear"]).reset_index(drop=True)
    hh = hh[hh["ehsyear"].astype(str).str.match(r"^\d{4}", na=False)].copy()
    for c in ["owners", "social", "prs"]:
        hh[c] = pd.to_numeric(hh[c], errors="coerce")
    hh["ehsyear"] = hh["ehsyear"].astype(int).astype(str)

    # ── Length of stay (private renters, London) ──────────────────
    los_df = xl["Length of stay"]
    los = los_df.iloc[8:20].copy()
    los.columns = ["_drop", "ehsyear", "0-1yr", "2yr", "3-4yr", "5-9yr", "10+yr",
                   "_r0", "_r1", "_r2", "_r3", "_r4", "_x1", "_x2"]
    los = los.dropna(subset=["ehsyear"]).reset_index(drop=True)
    los = los[los["ehsyear"].astype(str).str.match(r"^\d{4}", na=False)].copy()
    los["ehsyear"] = los["ehsyear"].astype(int).astype(str)
    for c in ["0-1yr", "2yr", "3-4yr", "5-9yr", "10+yr"]:
        los[c] = pd.to_numeric(los[c], errors="coerce")

    return hom, hom_change, rm_14d, rm_tracker, pipr, hp, rd, s21, rics, eviction_df, hz_prs, lt, pt, guar, hh, los


hom, hom_change, rm_14d, rm_tracker, pipr, hp, rd, s21, rics, eviction_df, hz_prs, lt, pt, guar, hh, los = load_all_data(XLSX_PATH)

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

ACT_DATE     = "2026-05-01"
ASSENT_DATE  = "2025-10-01"


def _vline(fig, x, label, color, y_label=0.97):
    fig.add_shape(type="line", x0=x, x1=x, y0=0, y1=1,
                  xref="x", yref="paper",
                  line=dict(color=color, width=2, dash="dash"))
    fig.add_annotation(x=x, y=y_label, xref="x", yref="paper", text=label,
                       showarrow=False, font=dict(color=color, size=10),
                       yanchor="top", xanchor="left",
                       bgcolor="rgba(255,255,255,0.7)", borderpad=2)


def add_reference_lines_date(fig):
    _vline(fig, ASSENT_DATE, "Royal Assent Oct 2025", C["grey"], y_label=0.97)
    _vline(fig, ACT_DATE,    "Act in force May 2026",  C["grey"], y_label=0.80)


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

with st.expander("📋 Key legislative changes introduced by the Renters' Rights Act", expanded=False):
    st.markdown("""
    The Renters' Rights Act (RRA) is due to come into effect in **May 2026**, introducing the following key legislative changes:

    - **Abolition of Section 21 'no fault' evictions**, removing a landlord's ability to evict tenants without providing a valid reason.
    - **Abolition of Assured Shorthold Tenancies**, with all tenancies transitioning to periodic tenancies on an ongoing basis.
    - **Extended protection periods** preventing landlords from evicting tenants on the grounds of selling the property or reclaiming it for personal use.
    - **Rent increases limited to once per year**, in line with prevailing market rates.
    - **Prohibition on advance rent payments**, preventing landlords from requesting more than one month's rent upfront.
    - **Introduction of the Private Rented Sector (PRS) Decent Homes Standard**, establishing minimum property condition requirements across the sector.
    """)

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

    k1, k2, k3 = st.columns(3)
    for col, title, val, sub, accent in [
        (k1, "Avg. Asking Rent",       f"£{int(latest_rent):,}",  f"HomeLet — {rent_date}",       C["blue"]),
        (k2, "New Listings (14 days)", f"{latest_listings:,}",    f"Rightmove — {listings_date}", C["lightblue"]),
        (k3, "Annual Rent Change",     f"{latest_pipr:+.1f}%",    f"ONS PIPR — {pipr_date}",      C["green"]),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left:4px solid {accent}">
              <div class="kpi-title">{title}</div>
              <div class="kpi-value">{val}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ════════════════════════════════════
    # GROUP 1 — RENTAL PRICE INDEXES
    # ════════════════════════════════════
    st.markdown(f"""<hr style="border:none; border-top:2px solid {C['navy']}; margin:8px 0 4px 0;">""", unsafe_allow_html=True)
    st.markdown(f"<span style='font-size:15px; font-weight:700; color:{C['navy']}'>Rental Price Indexes</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    rpi_left, rpi_right = st.columns(2)

    with rpi_left:
        st.markdown("**Annual Rent Change (%) — Rental Price Indexes**")
        st.caption("Click a trace to hide/show it. Double-click to isolate.")

        # ── Align all 3 sources to a common monthly date axis from 2020 ──
        pipr_2020 = pipr[pipr["Date"] >= "2023-01-01"].copy()

        # Rightmove is quarterly — interpolate to monthly for overlay
        rm_2020 = rm_tracker[rm_tracker["Quarter"].str[:4] >= "2023"].reset_index(drop=True)
        # Convert quarter strings to approximate mid-quarter dates
        def q_to_date(q):
            yr, qt = q.split(" Q")
            month = {"1": "02", "2": "05", "3": "08", "4": "11"}[qt]
            return pd.Timestamp(f"{yr}-{month}-01")
        rm_2020["Date"] = rm_2020["Quarter"].apply(q_to_date)

        hom_2020 = hom_change[hom_change["Date"] >= "2023-01-01"].copy()

        fig_rpi = go.Figure()

        # ONS PIPR — London
        fig_rpi.add_trace(go.Scatter(
            x=pipr_2020["Date"], y=pipr_2020["London"],
            name="London",
            legendgroup="ons",
            legendgrouptitle=dict(text="ONS PIPR", font=dict(size=11, color=C["navy"])),
            line=dict(color=C["pink"], width=2),
            hovertemplate="%{x|%b %Y}: %{y:.0f}%<extra>ONS PIPR — London</extra>"))

        # Rightmove — all London geographies grouped, each visible in legend
        for series, color, width in [
            ("London",       C["blue"],   2.0),
            ("Inner London", C["purple"], 1.5),
            ("Outer London", C["yellow"], 1.5),
        ]:
            fig_rpi.add_trace(go.Scatter(
                x=rm_2020["Date"], y=rm_2020[series],
                name=series,
                legendgroup="rightmove",
                legendgrouptitle=dict(text="Rightmove", font=dict(size=11, color=C["navy"])),
                showlegend=True,
                line=dict(color=color, width=width, dash="dot"),
                hovertemplate=f"%{{x|%b %Y}}: %{{y:.0f}}%<extra>Rightmove — {series}</extra>"))

        # Rightmove — Rest of Britain only with eng_toggle
        if eng_toggle:
            fig_rpi.add_trace(go.Scatter(
                x=rm_2020["Date"], y=rm_2020["Rest of Britain"],
                name="Rightmove — Rest of Britain",
                legendgroup="rightmove_rob",
                line=dict(color=C["green"], width=1.5, dash="dot"),
                hovertemplate="%{x|%b %Y}: %{y:.0f}%<extra>Rightmove — Rest of Britain</extra>"))

        # HomeLet — London always visible
        fig_rpi.add_trace(go.Scatter(
            x=hom_2020["Date"], y=hom_2020["London change"],
            name="London",
            legendgroup="homelet",
            legendgrouptitle=dict(text="HomeLet", font=dict(size=11, color=C["navy"])),
            line=dict(color=C["green"], width=2, dash="dash"),
            hovertemplate="%{x|%b %Y}: %{y:.0f}%<extra>HomeLet — London</extra>"))
        # HomeLet — UK only with eng_toggle
        if eng_toggle:
            fig_rpi.add_trace(go.Scatter(
                x=hom_2020["Date"], y=hom_2020["UK change"],
                name="UK",
                legendgroup="homelet",
                line=dict(color=C["lightblue"], width=1.5, dash="dash"),
                hovertemplate="%{x|%b %Y}: %{y:.0f}%<extra>HomeLet — UK</extra>"))

        fig_rpi.add_hline(y=0, line=dict(color=C["black"], width=1))
        add_reference_lines_date(fig_rpi)
        fig_rpi.update_layout(
            height=520, margin=dict(l=0, r=0, t=30, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            yaxis=dict(ticksuffix="%"),
            legend=dict(font=dict(size=11), orientation="h",
                        yanchor="bottom", y=1.02, xanchor="left", x=0))
        fig_rpi.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig_rpi.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_rpi, use_container_width=True)

    with rpi_right:
        if COMMENTARY.get("rent_indexes"):
            bullets = "".join(f"<li style='margin-bottom:8px'>{b}</li>" for b in COMMENTARY["rent_indexes"])
            st.markdown(f"""
            <div style="border-left:3px solid {C['navy']}; padding:12px 16px;
                        background:{C['white']}; border-radius:4px; font-size:14px;">
              <p style="margin:0 0 10px 0; font-weight:600; color:{C['navy']};">About these indicators</p>
              <ul style="margin:0; padding-left:18px; color:{C['black']};">{bullets}</ul>
            </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════
    # GROUP 2 — HOMELESSNESS
    # ════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""<hr style="border:none; border-top:2px solid {C['navy']}; margin:8px 0 4px 0;">""", unsafe_allow_html=True)
    st.markdown(f"<span style='font-size:15px; font-weight:700; color:{C['navy']}'>Homelessness</span>", unsafe_allow_html=True)
    st.markdown("<br>", unsafe_allow_html=True)

    prev_duty, rel_duty, s21_duty = st.columns(3)
    with prev_duty:
        st.markdown("**Homeless Prevention Duty by Reason** — MHCLG")
        hp_colors = [C["blue"], C["purple"], C["lightblue"], C["yellow"],
                    C["pink"], C["green"], C["navy"], C["grey"]]
        hp_labels = {
        "Total rent arrears":           "Total rent arrears",
        "Rent arrears (rent increase)": "Rent arrears (rent increase)",
        "Sell property":                "Landlord wishing to sell",
        "Re-let property":              "Landlord re-letting",
        "Disrepair complaint":          "Tenant complained about disrepair",
        "Illegal eviction":             "Illegal eviction",
        "Other reasons":                "Other",
    }
        fig_prev = go.Figure()
        for (col_key, label), color in zip(hp_labels.items(), hp_colors):
                fig_prev.add_trace(go.Bar(
                    x=hp["Quarter"], y=hp[col_key],
                    name=label, marker_color=color,
                    # visible="legendonly" if col_key == "Other reasons" else True,
                    hovertemplate=f"%{{x}}: %{{y:,.0f}}<extra>{label}</extra>"))
        fig_prev.update_layout(barmode="stack", height=280,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            legend=dict(font=dict(size=9), orientation="v", x=1.01, y=1, xanchor="left"))
        fig_prev.update_xaxes(showgrid=False)
        fig_prev.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_prev, use_container_width=True)
    
    with rel_duty:
        st.markdown("**Homeless Relief Duty by Reason** — MHCLG")
        rd_colors = [C["blue"], C["purple"], C["lightblue"], C["yellow"],
                    C["pink"], C["green"], C["navy"], C["grey"]]
        rd_labels = {
        "Total rent arrears":           "Total rent arrears",
        "Rent arrears (rent increase)": "Rent arrears (rent increase)",
        "Sell property":                "Landlord wishing to sell",
        "Re-let property":              "Landlord re-letting",
        "Disrepair complaint":          "Tenant complained about disrepair",
        "Illegal eviction":             "Illegal eviction",
        "Other reasons":                "Other",
    }
        fig_rel = go.Figure()
        for (col_key, label), color in zip(rd_labels.items(), rd_colors):
                fig_rel.add_trace(go.Bar(
                    x=rd["Quarter"], y=rd[col_key],
                    name=label, marker_color=color,
                    # visible="legendonly" if col_key == "Other reasons" else True,
                    hovertemplate=f"%{{x}}: %{{y:,.0f}}<extra>{label}</extra>"))
        fig_rel.update_layout(barmode="stack", height=280,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            legend=dict(font=dict(size=9), orientation="v", x=1.01, y=1, xanchor="left"))
        fig_rel.update_xaxes(showgrid=False)
        fig_rel.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_rel, use_container_width=True)
    
    with s21_duty:
        st.markdown("**Prevention Duty owed due to S21** — MHCLG")
        fig_s21 = go.Figure()
        fig_s21.add_trace(go.Bar(
            x=s21["Quarter"], y=s21["Total"],
            name="S21 prevention duty", marker_color=C["pink"],
            hovertemplate="%{x}: %{y:,.0f}<extra>S21 prevention duty</extra>"))
        fig_s21.update_layout(height=280, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            showlegend=False)
        fig_s21.update_xaxes(showgrid=False)
        fig_s21.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_s21, use_container_width=True)
        


    if COMMENTARY.get("homelessness_notes"):
        bullets = "".join(f"<li style='margin-bottom:6px'>{b}</li>" for b in COMMENTARY["homelessness_notes"])
        st.markdown(f"""
        <div style="border-left:3px solid {C['navy']}; padding:10px 16px; margin-top:8px;
                    background:{C['white']}; border-radius:4px; font-size:14px;">
          <ul style="margin:0; padding-left:18px; color:{C['black']};">{bullets}</ul>
        </div>""", unsafe_allow_html=True)

    # ════════════════════════════════════
    # UNGROUPED CHARTS
    # ════════════════════════════════════
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(f"""<hr style="border:none; border-top:1px solid {C['grey']}; margin:8px 0 16px 0;">""", unsafe_allow_html=True)

    col5, col6 = st.columns(2)

    with col5:
        st.markdown("**Tenant Demand & Landlord Instructions** — RICS UK Residential Market Survey")
        rics_plot = rics.dropna(subset=["Landlord instr London"]).copy()
        fig5 = go.Figure()
        fig5.add_trace(go.Scatter(
            x=rics_plot["Quarter"], y=rics_plot["Tenant demand London"],
            name="Tenant demand — London", line=dict(color=C["blue"], width=2),
            hovertemplate="%{x}: %{y:.0f}<extra>Tenant demand — London</extra>"))
        fig5.add_trace(go.Scatter(
            x=rics_plot["Quarter"], y=rics_plot["Landlord instr London"],
            name="Landlord instructions — London", line=dict(color=C["pink"], width=2),
            hovertemplate="%{x}: %{y:.0f}<extra>Landlord instructions — London</extra>"))
        if eng_toggle:
            fig5.add_trace(go.Scatter(
                x=rics_plot["Quarter"], y=rics_plot["Tenant demand EW"],
                name="Tenant demand — E&W", line=dict(color=C["lightblue"], width=2, dash="dot"),
                hovertemplate="%{x}: %{y:.0f}<extra>Tenant demand — E&W</extra>"))
            fig5.add_trace(go.Scatter(
                x=rics_plot["Quarter"], y=rics_plot["Landlord instr EW"],
                name="Landlord instr. — E&W", line=dict(color=C["yellow"], width=2, dash="dot"),
                hovertemplate="%{x}: %{y:.0f}<extra>Landlord instr. — E&W</extra>"))
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
        fig6.add_trace(go.Scatter(
            x=rm_14d["Date"], y=rm_14d["14d"],
            name="London", line=dict(color=C["green"], width=2),
            hovertemplate="%{x|%b %Y}: %{y:,.0f}<extra>14-day listings</extra>"))
        add_reference_lines_date(fig6)
        fig6.update_layout(height=380, margin=dict(l=0, r=0, t=8, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            showlegend=False)
        fig6.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig6.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig6, use_container_width=True)

    st.markdown("### Data Table — Market Monitoring")
    monitor_df = pd.DataFrame([
        ["HomeLet Rental Index",           "Avg. asking rent (London)",       f"£{int(latest_rent):,} pcm",                 "—", rent_date,                      "Monthly"],
        ["Rightmove Rental Price Tracker", "Annual rent change — London",     f"{rm_tracker['London'].iloc[-1]:+.1f}%",   "—", rm_tracker["Quarter"].iloc[-1], "Quarterly"],
        ["ONS Price Index of Priv Rent",   "Annual rent change (London)",     f"{latest_pipr:+.1f}%",                       "—", pipr_date,                      "Monthly"],
        ["RICS",                           "Landlord instr. sentiment (Lon)", f"{latest_rics:.0f}",                         "—", rics_q,                         "Quarterly"],
        ["MHCLG Homelessness Stats",       "Prevention duty cases (London)",  f"{latest_homeless:,}",                       "—", homeless_q,                     "Quarterly"],
        ["Met Police (FOI)",               "Illegal eviction cases (London)", str(eviction_latest),                         "—", eviction_year,                  "One-off"],
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

    k1, k2, k3, k4 = st.columns(4)
    for col, title, val, sub, accent in [
        (k1, "Proportion of households in PRS",      f"{prs_share:.1%}",          f"EHS {prs_year}",       C["purple"]),
        (k2, "PRS households in Cat 1 hazard homes", f"{hz_latest_rate:.1%}",     f"EHS {hz_latest_year}", C["pink"]),
        (k3, "Guarantor/Advance required",           f"{guar_pct:.0%}",           "EPLS 2024",             C["green"]),
        (k4, "Landlords with 1 property only",       f"{pt['pct'].iloc[0]:.0%}", "EPLS 2024",              C["yellow"]),
    ]:
        with col:
            st.markdown(f"""
            <div class="kpi-card" style="border-left:4px solid {accent}">
              <div class="kpi-title">{title}</div>
              <div class="kpi-value">{val}</div>
              <div class="kpi-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_wide, col_narrow = st.columns([3, 1])

    with col_wide:
        st.markdown("**Households by tenure (%)** — English Housing Survey")
        fig_tenure = go.Figure()
        for tenure_col, label, color in [
            ("prs",    "Private renters", C["purple"]),
            ("social", "Social sector",   C["green"]),
            ("owners", "Owner occupiers", C["blue"]),
        ]:
            fig_tenure.add_trace(go.Scatter(
                x=hh["ehsyear"], y=(hh[tenure_col] * 100).round(1),
                name=label, line=dict(color=color, width=2),
                mode="lines+markers", marker=dict(size=6),
                hovertemplate=f"%{{x}}: %{{y:.0f}}%<extra>{label}</extra>"))
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
            marker=dict(size=7),
            hovertemplate="%{x}: %{y:.0f}%<extra>Cat 1 Hazard rate</extra>"))
        fig_hz.update_layout(height=270, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            yaxis=dict(ticksuffix="%", rangemode="tozero"), showlegend=False)
        fig_hz.update_xaxes(showgrid=True, gridcolor=C["offwhite"], tickangle=45)
        fig_hz.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_hz, use_container_width=True)

    col_pie, col_stay = st.columns([1, 2])

    with col_pie:
        st.markdown("**Guarantor / Advance Required** — English Private Landlord Survey, 2024")
        guar_map = {
            "A guarantor":                               "Guarantor",
            "Rent in advance, in addition to a deposit": "Rent advance",
            "Both":                                      "Both",
            "Neither":                                   "Neither",
            "Don't know":                                "Don't know",
        }
        guar_plot = guar.copy()
        guar_plot["Label"] = guar_plot["ReqGuaRent"].map(guar_map)
        guar_plot = guar_plot.dropna(subset=["Label", "pct"])
        pie_colors = [C["green"], C["blue"], C["pink"], C["yellow"], C["lightblue"]]
        fig_pie = go.Figure(go.Pie(
            labels=guar_plot["Label"],
            values=(guar_plot["pct"] * 100).round(1),
            marker=dict(colors=pie_colors, line=dict(color=C["white"], width=2)),
            textinfo="label+percent", textfont=dict(size=11), hole=0.35,
            hovertemplate="%{label}: %{value:.0f}%<extra></extra>"))
        fig_pie.update_layout(height=270, margin=dict(l=0, r=0, t=10, b=7),
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
                x=los["ehsyear"], y=(los[col_key] * 100).round(1),
                name=label, marker_color=color,
                hovertemplate=f"%{{x}}: %{{y:.0f}}%<extra>{label}</extra>"))
        fig_stay.update_layout(barmode="stack", height=270,
            margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            yaxis=dict(ticksuffix="%", range=[0, 100]),
            legend=dict(font=dict(size=11), orientation="h",
                yanchor="bottom", y=1.02, xanchor="left", x=0))
        fig_stay.update_xaxes(showgrid=False)
        fig_stay.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_stay, use_container_width=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        st.markdown("**Landlord Type** — English Private Landlord Survey, 2024")
        fig_lt = px.bar(lt, x="pct_pct", y="Type_short", orientation="h",
            color_discrete_sequence=[C["blue"]])
        fig_lt.update_traces(hovertemplate="%{y}: %{x:.0f}%<extra></extra>")
        fig_lt.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            xaxis_ticksuffix="%", showlegend=False, xaxis_title="", yaxis_title="")
        fig_lt.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig_lt.update_yaxes(showgrid=False)
        st.plotly_chart(fig_lt, use_container_width=True)

    with col2:
        st.markdown("**Portfolio Size** — English Private Landlord Survey, 2024")
        fig_pt = px.bar(pt, x="pct_pct", y="Size_short", orientation="h",
            color_discrete_sequence=[C["purple"]])
        fig_pt.update_traces(hovertemplate="%{y}: %{x:.0f}%<extra></extra>")
        fig_pt.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"],
            xaxis_ticksuffix="%", showlegend=False, xaxis_title="", yaxis_title="")
        fig_pt.update_xaxes(showgrid=True, gridcolor=C["offwhite"])
        fig_pt.update_yaxes(showgrid=False)
        st.plotly_chart(fig_pt, use_container_width=True)

    with col3:
        st.markdown("**Illegal Eviction Cases** — Met Police")
        fig_ev = go.Figure()
        fig_ev.add_trace(go.Bar(
            x=eviction_df["Year"], y=eviction_df["Cases"],
            marker_color=C["yellow"],
            hovertemplate="%{x}: %{y:.0f}<extra>Cases</extra>"))
        fig_ev.update_layout(height=200, margin=dict(l=0, r=0, t=10, b=0),
            paper_bgcolor=C["white"], plot_bgcolor=C["white"], showlegend=False)
        fig_ev.update_xaxes(showgrid=False)
        fig_ev.update_yaxes(showgrid=True, gridcolor=C["offwhite"])
        st.plotly_chart(fig_ev, use_container_width=True)

    st.markdown("### Data Table — Sector Context")
    context_df = pd.DataFrame([
        ["English Housing Survey", "PRS share of stock",          f"{prs_share:.1%}",          "—", prs_year,       "Annual"],
        ["EPLS 2024",              "Guarantor/advance required",  f"{guar_pct:.0%}",            "—", "2024",         "One-off"],
        ["EPLS 2024",              "Landlord type — individual",  f"{lt['pct'].iloc[0]:.0%}",   "—", "2024",         "One-off"],
        ["EPLS 2024",              "Portfolio size — 1 property", f"{pt['pct'].iloc[0]:.0%}",   "—", "2024",         "One-off"],
        ["English Housing Survey", "Cat 1 hazard homes (PRS)",    f"{hz_latest_rate:.1%}",      "—", hz_latest_year, "Annual"],
        ["Met Police",             "Illegal eviction cases",      str(eviction_latest),          "—", eviction_year,  "One-off (FOI)"],
    ], columns=["Source", "Metric", "London", "England", "Year", "Frequency"])
    if not eng_toggle:
        context_df["England"] = "—"
    st.dataframe(context_df, use_container_width=True, hide_index=True)