import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import random
import time
import json
import os
import copy

# Seiten-Konfiguration (kompakt für Handy & Desktop)
st.set_page_config(page_title="Gaudi-Nachtturnier", page_icon="🎾", layout="wide", initial_sidebar_state="collapsed")

DATEI_SPEICHER = "turnier_daten.json"
ADMIN_PASSWORT = "admin123"   # Dein Admin-Passwort

# --- CUSTOM CSS FÜR MODERNE OPTIK, MOBILE LESBARKEIT & SAUBERE OBERFLÄCHE ---
st.markdown("""
<style>
    .block-container {
        padding-top: 1.2rem !important;
        padding-bottom: 5.5rem !important;
        max-width: 1100px;
    }
    [data-testid="stToolbar"],
    [data-testid="stDecoration"],
    [data-testid="stStatusWidget"],
    [data-testid="manage-app-button"],
    #MainMenu,
    footer,
    .viewerBadge_container__r5tak,
    .styles_viewerBadge__CvC9N,
    div[class*="viewerBadge"],
    div[class*="StatusWidget"],
    div[class*="hostBadge"],
    a[href*="streamlit.io/cloud"] {
        display: none !important;
        visibility: hidden !important;
        opacity: 0 !important;
        pointer-events: none !important;
    }
    header[data-testid="stHeader"] {
        background: transparent !important;
    }
    .court-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
        color: #f8fafc;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
    }
    .court-card-highlight {
        background: linear-gradient(135deg, #064e3b 0%, #0f172a 100%);
        border: 2px solid #10b981;
        border-radius: 14px;
        padding: 14px 16px;
        margin-bottom: 10px;
        color: #f8fafc;
        box-shadow: 0 0 15px rgba(16, 185, 129, 0.25);
    }
    .court-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #334155;
        padding-bottom: 6px;
        margin-bottom: 10px;
        font-size: 0.9rem;
        color: #94a3b8;
    }
    .court-badge {
        background-color: #0284c7;
        color: white;
        padding: 2px 10px;
        border-radius: 20px;
        font-weight: 700;
        font-size: 0.85rem;
    }
    .team-row {
        font-size: 1.08rem;
        font-weight: 600;
        padding: 4px 0;
        color: #f1f5f9;
    }
    .vs-divider {
        text-align: center;
        font-size: 0.78rem;
        font-weight: 800;
        color: #38bdf8;
        letter-spacing: 2px;
        margin: 2px 0;
    }
    .pause-box {
        background-color: #451a03;
        border: 1px solid #d97706;
        border-radius: 12px;
        padding: 12px 16px;
        color: #fef3c7;
        margin-bottom: 14px;
        font-size: 1rem;
    }
    .pause-box-highlight {
        background-color: #78350f;
        border: 2px solid #f59e0b;
        border-radius: 12px;
        padding: 12px 16px;
        color: #ffffff;
        margin-bottom: 14px;
        font-size: 1.05rem;
    }
</style>
""", unsafe_allow_html=True)

# --- DAUERHAFTE SPEICHERUNG ---
def daten_laden():
    if os.path.exists(DATEI_SPEICHER):
        try:
            with open(DATEI_SPEICHER, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"spieler": [], "runden": [], "timer_end": None}

def daten_speichern():
    daten = {
        "spieler": st.session_state.spieler,
        "runden": st.session_state.runden,
        "timer_end": st.session_state.timer_end
    }
    with open(DATEI_SPEICHER, "w", encoding="utf-8") as f:
        json.dump(daten, f, ensure_ascii=False, indent=2)

# Immer aktuelle Daten laden
gespeichert = daten_laden()
st.session_state.spieler = gespeichert.get("spieler", [])
st.session_state.runden = gespeichert.get("runden", [])
st.session_state.timer_end = gespeichert.get("timer_end", None)

if "is_admin" not in st.session_state:
    st.session_state.is_admin = False
if "show_login" not in st.session_state:
    st.session_state.show_login = False

# --- KOPFZEILE MIT DIREKTEM ADMIN-BUTTON ---
head_col1, head_col2, head_col3 = st.columns([3.0, 1.3, 1.1])
with head_col1:
    st.markdown("## 🎾 Gaudi-Nachtturnier")
with head_col2:
    if st.button("🔄 Aktualisieren", use_container_width=True, help="Lädt die neuesten Paarungen & Ergebnisse"):
        st.rerun()
with head_col3:
    if not st.session_state.is_admin:
        if st.button("🔐 Admin", use_container_width=True, help="Login für Turnierleitung"):
            st.session_state.show_login = not st.session_state.show_login
            st.rerun()
    else:
        if st.button("🚪 Logout", use_container_width=True, help="Zurück zur Teilnehmer-Ansicht"):
            st.session_state.is_admin = False
            st.session_state.show_login = False
            st.rerun()

if st.session_state.show_login and not st.session_state.is_admin:
    with st.container(border=True):
        lc1, lc2 = st.columns([3, 1])
        with lc1:
            pw_eingabe = st.text_input("Admin-Passwort", type="password", placeholder="Passwort eingeben...", label_visibility="collapsed")
        with lc2:
            if st.button("Anmelden", type="primary", use_container_width=True):
                if pw_eingabe == ADMIN_PASSWORT:
                    st.session_state.is_admin = True
                    st.session_state.show_login = False
                    st.rerun()
                else:
                    st.error("Falsches Passwort")

# --- AUTONOMER LIVE-TIMER (SYNCHRONISIERT SICH ALLE 3 SEKUNDEN SELBST) ---
@st.fragment(run_every=3)
def render_live_timer():
    aktuelle_daten = daten_laden()
    aktuelles_timer_end = aktuelle_daten.get("timer_end", None)
    timer_aktiv = aktuelles_timer_end is not None

    if st.session_state.is_admin:
        t_col1, t_col2 = st.columns([2, 1])
        with t_col2:
            if st.button(
                "▶️ 20-Min.-Timer starten",
                type="primary",
                use_container_width=True,
                disabled=timer_aktiv,
                key="btn_start_timer"
            ):
                neu = daten_laden()
                neu["timer_end"] = time.time() + 20 * 60
                with open(DATEI_SPEICHER, "w", encoding="utf-8") as f:
                    json.dump(neu, f, ensure_ascii=False, indent=2)
                st.session_state.timer_end = neu["timer_end"]
                st.rerun()
            if st.button(
                "⏹️ Timer stoppen / Reset",
                use_container_width=True,
                disabled=not timer_aktiv,
                key="btn_stop_timer"
            ):
                neu = daten_laden()
                neu["timer_end"] = None
                with open(DATEI_SPEICHER, "w", encoding="utf-8") as f:
                    json.dump(neu, f, ensure_ascii=False, indent=2)
                st.session_state.timer_end = None
                st.rerun()
        timer_container = t_col1
    else:
        timer_container = st.container()

    with timer_container:
        if aktuelles_timer_end:
            end_ms = int(aktuelles_timer_end * 1000)
            timer_html = f"""
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%); color: #38bdf8; padding: 12px; border-radius: 14px; text-align: center; font-family: sans-serif; border: 2px solid #38bdf8; box-shadow: 0 4px 12px rgba(56, 189, 248, 0.15);">
                <div style="font-size: 12px; letter-spacing: 1.5px; color: #94a3b8; margin-bottom: 2px;">VERBLEIBENDE RUNDENZEIT</div>
                <div id="countdown" style="font-size: 48px; font-weight: 800; letter-spacing: 3px; line-height: 1.1;">20:00</div>
            </div>
            <script>
                var endTime = {end_ms};
                var alarmGespielt = false;
                function updateTimer() {{
                    var now = new Date().getTime();
                    var distance = endTime - now;
                    var el = document.getElementById("countdown");
                    if (!el) return;
                    if (distance <= 0) {{
                        el.innerHTML = "00:00 · ZEIT UM!";
                        el.style.color = "#ef4444";
                        el.parentElement.style.borderColor = "#ef4444";
                        if (!alarmGespielt) {{
                            alarmGespielt = true;
                            try {{
                                var ctx = new (window.AudioContext || window.webkitAudioContext)();
                                var osc = ctx.createOscillator();
                                osc.type = "sine";
                                osc.frequency.setValueAtTime(880, ctx.currentTime);
                                osc.connect(ctx.destination);
                                osc.start();
                                osc.stop(ctx.currentTime + 1.2);
                            }} catch(e) {{}}
                        }}
                        return;
                    }}
                    var minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
                    var seconds = Math.floor((distance % (1000 * 60)) / 1000);
                    el.innerHTML = (minutes < 10 ? "0" : "") + minutes + ":" + (seconds < 10 ? "0" : "") + seconds;
                }}
                updateTimer();
                setInterval(updateTimer, 250);
            </script>
            """
            components.html(timer_html, height=108)
        else:
            components.html("""
            <div style="background-color: #1e293b; color: #94a3b8; padding: 12px; border-radius: 14px; text-align: center; font-family: sans-serif; border: 1px dashed #475569;">
                <div style="font-size: 12px; letter-spacing: 1.5px; margin-bottom: 2px;">RUNDEN-TIMER</div>
                <div style="font-size: 48px; font-weight: 800; letter-spacing: 3px; line-height: 1.1;">20:00</div>
            </div>
            """, height=108)

render_live_timer()

# --- HILFSFUNKTIONEN FÜR REALISTISCHE SPIELSTÄRKE & AUSLOSUNG ---
STÄRKE_LABELS = {
    0: "0 - Top-Spieler (nahe einst. LK)",
    1: "1 - Stark (LK 17–21 / Stammspieler)",
    2: "2 - Mannschaft / LK 22+",
    3: "3 - Mittel (Freizeit)",
    4: "4 - Einsteiger"
}

def get_power_rating(spieler):
    st_val = spieler["Stärke"]
    ist_jugend = spieler.get("Jugend", False)
    if spieler["Geschlecht"] == "m":
        if ist_jugend:
            return {0: 11.2, 1: 9.1, 2: 7.5, 3: 5.8, 4: 3.5}.get(st_val, 5.8)
        return {0: 12.5, 1: 10.3, 2: 8.6, 3: 6.8, 4: 4.0}.get(st_val, 6.8)
    else:
        if ist_jugend:
            return {0: 9.2, 1: 7.3, 2: 5.8, 3: 4.2, 4: 2.4}.get(st_val, 4.2)
        return {0: 10.3, 1: 8.5, 2: 6.8, 3: 5.0, 4: 2.8}.get(st_val, 5.0)

def bewerte_team_kombi(p1, p2):
    strafe = 0
    if p1["Stärke"] == 4 and p2["Stärke"] == 4:
        strafe += 4000
    if {p1["Stärke"], p2["Stärke"]} == {0, 4}:
        strafe += 3000
    partner_diff = abs(get_power_rating(p1) - get_power_rating(p2))
    if partner_diff > 6.5:
        strafe += (partner_diff - 6.5) * 350
    strafe += p1["Partner"].count(p2["Name"]) * 3000
    return strafe

def bewerte_platz(team1, team2):
    strafe = 0
    alle_vier = team1 + team2
    hat_jugend = any(p.get("Jugend", False) for p in alle_vier)
    hat_einsteiger = any(p["Stärke"] == 4 for p in alle_vier)
    if hat_jugend and hat_einsteiger:
        strafe += 8000
        
    strafe += bewerte_team_kombi(team1[0], team1[1])
    strafe += bewerte_team_kombi(team2[0], team2[1])
    
    rating_t1 = get_power_rating(team1[0]) + get_power_rating(team1[1])
    rating_t2 = get_power_rating(team2[0]) + get_power_rating(team2[1])
    diff_rating = abs(rating_t1 - rating_t2)
    strafe += (diff_rating ** 2) * 180
    if diff_rating > 1.8:
        strafe += 2500 + ((diff_rating - 1.8) * 1500)
        
    for p1 in team1:
        for p2 in team2:
            anz_gegner = p1["Gegner"].count(p2["Name"])
            if anz_gegner >= 2:
                strafe += 12000
            else:
                strafe += anz_gegner * 850
            if p2["Name"] in p1["Partner"]:
                strafe += 400
                
    return strafe

def generiere_runde(spieler_liste, plaetze=5):
    aktive = [p for p in spieler_liste if p.get("Aktiv", True)]
    if len(aktive) < 4:
        return [], []
        
    beste_loesung = None
    bester_score = float("inf")
    
    ges_w = sum(1 for p in aktive if p["Geschlecht"] == "w")
    ziel_anteil_w = ges_w / len(aktive) if len(aktive) > 0 else 0.5
    
    for _ in range(9000):
        maenner = [p for p in aktive if p["Geschlecht"] == "m"]
        frauen = [p for p in aktive if p["Geschlecht"] == "w"]
        
        random.shuffle(maenner)
        random.shuffle(frauen)
        
        maenner.sort(key=lambda x: (0 if x.get("Letzte_Pause", False) else 1, x["Spiele"]))
        frauen.sort(key=lambda x: (0 if x.get("Letzte_Pause", False) else 1, x["Spiele"]))
        
        max_plaetze = min(len(aktive) // 4, plaetze)
        beste_kombi = None
        
        for p_count in range(max_plaetze, 0, -1):
            gueltige_kombis = []
            ziel_w_spieler = p_count * 4 * ziel_anteil_w
            
            for n_mixed in range(p_count + 1):
                for n_herren in range(p_count - n_mixed + 1):
                    n_damen = p_count - n_mixed - n_herren
                    req_m = 2 * n_mixed + 4 * n_herren
                    req_w = 2 * n_mixed + 4 * n_damen
                    if len(maenner) >= req_m and len(frauen) >= req_w:
                        pause_m = maenner[req_m:]
                        pause_w = frauen[req_w:]
                        doppel_pausen = sum(1 for p in pause_m + pause_w if p.get("Letzte_Pause", False))
                        spiel_summe = sum(x["Spiele"] for x in maenner[:req_m]) + sum(x["Spiele"] for x in frauen[:req_w])
                        abweichung_schnitt = abs(req_w - ziel_w_spieler)
                        gueltige_kombis.append((doppel_pausen, spiel_summe, abweichung_schnitt, -n_mixed, n_mixed, n_herren, n_damen))
            if gueltige_kombis:
                gueltige_kombis.sort()
                _, _, _, _, n_mixed, n_herren, n_damen = gueltige_kombis[0]
                beste_kombi = (n_mixed, n_herren, n_damen)
                break
                
        if not beste_kombi:
            return [], [p["Name"] for p in aktive]
            
        n_mixed, n_herren, n_damen = beste_kombi
        req_m = 2 * n_mixed + 4 * n_herren
        req_w = 2 * n_mixed + 4 * n_damen
        
        aktiv_m = maenner[:req_m]
        aktiv_w = frauen[:req_w]
        pause = maenner[req_m:] + frauen[req_w:]
        
        random.shuffle(aktiv_m)
        random.shuffle(aktiv_w)
        
        strafpunkte = 0
        strafpunkte += sum(20000 for p in pause if p.get("Letzte_Pause", False))
        
        matches = []
        platz_nr = 1
        
        for _ in range(n_mixed):
            m1, m2 = aktiv_m.pop(0), aktiv_m.pop(0)
            w1, w2 = aktiv_w.pop(0), aktiv_w.pop(0)
            optionen = [([m1, w2], [m2, w1]), ([m1, w1], [m2, w2])]
            optionen.sort(key=lambda opt: bewerte_platz(opt[0], opt[1]))
            team1, team2 = optionen[0]
            strafpunkte += bewerte_platz(team1, team2)
            matches.append((platz_nr, "Mixed", team1, team2))
            platz_nr += 1
            
        for _ in range(n_herren):
            m1, m2, m3, m4 = aktiv_m.pop(0), aktiv_m.pop(0), aktiv_m.pop(0), aktiv_m.pop(0)
            optionen = [([m1, m4], [m2, m3]), ([m1, m3], [m2, m4]), ([m1, m2], [m3, m4])]
            optionen.sort(key=lambda opt: bewerte_platz(opt[0], opt[1]))
            team1, team2 = optionen[0]
            strafpunkte += bewerte_platz(team1, team2)
            matches.append((platz_nr, "Herren-Doppel", team1, team2))
            platz_nr += 1
            
        for _ in range(n_damen):
            w1, w2, w3, w4 = aktiv_w.pop(0), aktiv_w.pop(0), aktiv_w.pop(0), aktiv_w.pop(0)
            optionen = [([w1, w4], [w2, w3]), ([w1, w3], [w2, w4]), ([w1, w2], [w3, w4])]
            optionen.sort(key=lambda opt: bewerte_platz(opt[0], opt[1]))
            team1, team2 = optionen[0]
            strafpunkte += bewerte_platz(team1, team2)
            matches.append((platz_nr, "Damen-Doppel", team1, team2))
            platz_nr += 1
            
        if strafpunkte < bester_score:
            bester_score = strafpunkte
            formatierte_matches = []
            for p_nr, typ, team1, team2 in matches:
                formatierte_matches.append({
                    "Platz": p_nr,
                    "Typ": typ,
                    "Team1": [team1[0]["Name"], team1[1]["Name"]],
                    "Team2": [team2[0]["Name"], team2[1]["Name"]],
                    "Punkte1": 0,
                    "Punkte2": 0,
                    "Gemeldet": False,
                    "Gemeldet_um": None,
                    "Erfasst": False
                })
            beste_loesung = (formatierte_matches, [p["Name"] for p in pause])
            
    return beste_loesung

def berechne_spieler_historie_neu():
    """Berechnet Spiele, Pausen, Partner und Gegner aus allen Runden sauber neu."""
    name_zu_spieler = {s["Name"]: s for s in st.session_state.spieler}
    for s in st.session_state.spieler:
        s["Spiele"] = 0
        s["Pausen"] = 0
        s["Letzte_Pause"] = False
        s["Partner"] = []
        s["Gegner"] = []

    for r in st.session_state.runden:
        for p_name in r.get("Pause", []):
            if p_name in name_zu_spieler:
                name_zu_spieler[p_name]["Pausen"] += 1
                name_zu_spieler[p_name]["Letzte_Pause"] = True
        for m in r["Matches"]:
            t1_a, t1_b = m["Team1"]
            t2_a, t2_b = m["Team2"]
            for name in [t1_a, t1_b, t2_a, t2_b]:
                if name in name_zu_spieler:
                    name_zu_spieler[name]["Spiele"] += 1
                    name_zu_spieler[name]["Letzte_Pause"] = False
            if t1_a in name_zu_spieler and t1_b in name_zu_spieler:
                name_zu_spieler[t1_a]["Partner"].append(t1_b)
                name_zu_spieler[t1_b]["Partner"].append(t1_a)
            if t2_a in name_zu_spieler and t2_b in name_zu_spieler:
                name_zu_spieler[t2_a]["Partner"].append(t2_b)
                name_zu_spieler[t2_b]["Partner"].append(t2_a)
            for a in [t1_a, t1_b]:
                for b in [t2_a, t2_b]:
                    if a in name_zu_spieler and b in name_zu_spieler:
                        name_zu_spieler[a]["Gegner"].append(b)
                        name_zu_spieler[b]["Gegner"].append(a)

def bewerte_tausch_kandidaten(r_idx, pos_a):
    """Bewertet alle möglichen Tauschpartner B für den gewählten Spieler A nach allen Turnierkriterien."""
    name_zu_spieler = {s["Name"]: s for s in st.session_state.spieler}
    vorherige_runden = st.session_state.runden[:r_idx]
    aktuelle_runde = st.session_state.runden[r_idx]

    hist_partner = {s["Name"]: [] for s in st.session_state.spieler}
    hist_gegner = {s["Name"]: [] for s in st.session_state.spieler}
    pause_vorrunde = set()
    for prev_i, prev_r in enumerate(vorherige_runden):
        if prev_i == r_idx - 1:
            pause_vorrunde = set(prev_r.get("Pause", []))
        for m in prev_r["Matches"]:
            t1a, t1b = m["Team1"]
            t2a, t2b = m["Team2"]
            if t1a in hist_partner and t1b in hist_partner:
                hist_partner[t1a].append(t1b)
                hist_partner[t1b].append(t1a)
            if t2a in hist_partner and t2b in hist_partner:
                hist_partner[t2a].append(t2b)
                hist_partner[t2b].append(t2a)
            for x in [t1a, t1b]:
                for y in [t2a, t2b]:
                    if x in hist_gegner and y in hist_gegner:
                        hist_gegner[x].append(y)
                        hist_gegner[y].append(x)

    temp_spieler = {}
    for name, s in name_zu_spieler.items():
        cp = copy.deepcopy(s)
        cp["Partner"] = hist_partner.get(name, [])
        cp["Gegner"] = hist_gegner.get(name, [])
        temp_spieler[name] = cp

    kandidaten = []
    alle_pos = []
    for m_i, match in enumerate(aktuelle_runde["Matches"]):
        for t_key, team_bez in [("Team1", "Team 1"), ("Team2", "Team 2")]:
            for s_i, sp_name in enumerate(match[t_key]):
                alle_pos.append(("match", m_i, t_key, s_i, sp_name, f"Platz {match['Platz']} · {team_bez}"))
    for p_i, p_name in enumerate(aktuelle_runde.get("Pause", [])):
        alle_pos.append(("pause", p_i, None, None, p_name, "☕ Pause"))

    name_a = pos_a[4]
    sp_a = temp_spieler.get(name_a)

    for pos_b in alle_pos:
        name_b = pos_b[4]
        if name_a == name_b:
            continue

        sim_matches = copy.deepcopy(aktuelle_runde["Matches"])
        sim_pause = list(aktuelle_runde.get("Pause", []))

        if pos_a[0] == "match":
            sim_matches[pos_a[1]][pos_a[2]][pos_a[3]] = name_b
        else:
            sim_pause[pos_a[1]] = name_b

        if pos_b[0] == "match":
            sim_matches[pos_b[1]][pos_b[2]][pos_b[3]] = name_a
        else:
            sim_pause[pos_b[1]] = name_a

        score = 0
        hinweise = []

        sp_b = temp_spieler.get(name_b)
        if sp_a and sp_b and sp_a["Geschlecht"] != sp_b["Geschlecht"]:
            score += 4500
            hinweise.append("Geschlecht wechselt")

        for p_n in sim_pause:
            if p_n in pause_vorrunde:
                score += 15000
                hinweise.append(f"Doppelpause {p_n}")

        betroffene_m = set()
        if pos_a[0] == "match":
            betroffene_m.add(pos_a[1])
        if pos_b[0] == "match":
            betroffene_m.add(pos_b[1])

        max_diff = 0.0
        for m_i in betroffene_m:
            m_obj = sim_matches[m_i]
            if all(n in temp_spieler for n in m_obj["Team1"] + m_obj["Team2"]):
                t1 = [temp_spieler[m_obj["Team1"][0]], temp_spieler[m_obj["Team1"][1]]]
                t2 = [temp_spieler[m_obj["Team2"][0]], temp_spieler[m_obj["Team2"][1]]]
                score += bewerte_platz(t1, t2)

                r1 = get_power_rating(t1[0]) + get_power_rating(t1[1])
                r2 = get_power_rating(t2[0]) + get_power_rating(t2[1])
                diff = abs(r1 - r2)
                if diff > max_diff:
                    max_diff = diff

                for team in [t1, t2]:
                    if team[1]["Name"] in team[0]["Partner"]:
                        hinweise.append("Partner-Doppelung")
                for p1 in t1:
                    for p2 in t2:
                        g_cnt = p1["Gegner"].count(p2["Name"])
                        if g_cnt >= 2:
                            hinweise.append(f"{g_cnt + 1}× Gegner")
                        elif g_cnt == 1:
                            hinweise.append("2× Gegner")

        hinweise = list(dict.fromkeys(hinweise))
        if max_diff > 2.2:
            hinweise.append(f"Stärke-Diff {max_diff:.1f}")

        if score < 1200 and not hinweise:
            ampel = "🟢 TOP"
            grund = f"Passt ideal (Diff {max_diff:.1f})"
        elif score < 4000:
            ampel = "🟡 OK"
            grund = ", ".join(hinweise) if hinweise else f"Diff {max_diff:.1f}"
        else:
            ampel = "🔴 UNGÜNSTIG"
            grund = ", ".join(hinweise) if hinweise else "Hohe Abweichung"

        label = f"{ampel} · {name_b} ({pos_b[5]}) — {grund}"
        kandidaten.append((score, label, pos_b))

    kandidaten.sort(key=lambda x: x[0])
    return kandidaten

def pruefe_runden_kollisionen(r_idx):
    """Prüft die gewählte Runde gegen alle bisherigen Runden auf Doppelungen & Balance."""
    warnungen = []
    name_zu_spieler = {s["Name"]: s for s in st.session_state.spieler}
    vorherige_runden = st.session_state.runden[:r_idx]
    aktuelle_runde = st.session_state.runden[r_idx]

    partner_verlauf = {}
    gegner_verlauf = {}
    pause_vorrunde = set()

    for prev_i, prev_r in enumerate(vorherige_runden):
        if prev_i == r_idx - 1:
            pause_vorrunde = set(prev_r.get("Pause", []))
        for m in prev_r["Matches"]:
            for team in [m["Team1"], m["Team2"]]:
                key_p = tuple(sorted(team))
                partner_verlauf[key_p] = partner_verlauf.get(key_p, 0) + 1
            for a in m["Team1"]:
                for b in m["Team2"]:
                    key_g = tuple(sorted([a, b]))
                    gegner_verlauf[key_g] = gegner_verlauf.get(key_g, 0) + 1

    for p_name in aktuelle_runde.get("Pause", []):
        if p_name in pause_vorrunde:
            warnungen.append(f"☕ **{p_name}** hatte bereits in der Vorrunde Pause (Doppelpause!).")

    for m in aktuelle_runde["Matches"]:
        platz = m["Platz"]
        for team in [m["Team1"], m["Team2"]]:
            key_p = tuple(sorted(team))
            if partner_verlauf.get(key_p, 0) >= 1:
                warnungen.append(f"🤝 **Platz {platz}:** {team[0]} & {team[1]} haben bereits zusammen als Doppel gespielt.")
        for a in m["Team1"]:
            for b in m["Team2"]:
                key_g = tuple(sorted([a, b]))
                bisher = gegner_verlauf.get(key_g, 0)
                if bisher >= 2:
                    warnungen.append(f"⚔️ **Platz {platz}:** {a} vs. {b} treffen bereits zum {bisher + 1}. Mal aufeinander.")
                elif bisher == 1:
                    warnungen.append(f"ℹ️ **Platz {platz}:** {a} & {b} standen sich schon 1x als Gegner gegenüber.")

        if all(n in name_zu_spieler for n in m["Team1"] + m["Team2"]):
            r1 = get_power_rating(name_zu_spieler[m["Team1"][0]]) + get_power_rating(name_zu_spieler[m["Team1"][1]])
            r2 = get_power_rating(name_zu_spieler[m["Team2"][0]]) + get_power_rating(name_zu_spieler[m["Team2"][1]])
            diff = abs(r1 - r2)
            if diff > 2.5:
                warnungen.append(f"⚖️ **Platz {platz}:** Deutlicher Spielstärke-Unterschied ({r1:.1f} vs. {r2:.1f} Punkte).")

    return warnungen

def berechne_tabelle_df():
    stats = {s["Name"]: {"Name": s["Name"], "Spiele": 0, "Siege": 0, "Plus": 0, "Minus": 0} for s in st.session_state.spieler}
    for r in st.session_state.runden:
        if not r.get("Freigegeben", True):
            continue
        for m in r["Matches"]:
            if (m.get("Erfasst", False) or m.get("Gemeldet", False)) and (m["Punkte1"] > 0 or m["Punkte2"] > 0):
                p1, p2 = int(m["Punkte1"]), int(m["Punkte2"])
                for name in m["Team1"]:
                    if name in stats:
                        stats[name]["Spiele"] += 1
                        stats[name]["Plus"] += p1
                        stats[name]["Minus"] += p2
                        if p1 > p2:
                            stats[name]["Siege"] += 1
                for name in m["Team2"]:
                    if name in stats:
                        stats[name]["Spiele"] += 1
                        stats[name]["Plus"] += p2
                        stats[name]["Minus"] += p1
                        if p2 > p1:
                            stats[name]["Siege"] += 1
                        
    tabelle = []
    for s in stats.values():
        diff = s["Plus"] - s["Minus"]
        tabelle.append({
            "Spieler": s["Name"],
            "Sp.": s["Spiele"],
            "Siege": s["Siege"],
            "Diff.": diff,
            "Punkte": f"{s['Plus']}:{s['Minus']}",
            "_plus": s["Plus"],
            "_minus": s["Minus"]
        })
        
    df_tab = pd.DataFrame(tabelle)
    df_tab = df_tab.sort_values(
        by=["Siege", "Diff.", "_plus", "_minus"],
        ascending=[False, False, False, True]
    ).drop(columns=["_plus", "_minus"]).reset_index(drop=True)
    df_tab.index += 1
    return df_tab

def hat_manuelle_aenderung(runde):
    """Prüft, ob die aktuelle Runde gegenüber der gespeicherten Original-Auslosung verändert wurde."""
    orig_matches = runde.get("Original_Matches")
    orig_pause = runde.get("Original_Pause")
    if orig_matches is None or orig_pause is None:
        return False
    if runde.get("Pause", []) != orig_pause:
        return True
    for cur_m, org_m in zip(runde["Matches"], orig_matches):
        if cur_m["Team1"] != org_m["Team1"] or cur_m["Team2"] != org_m["Team2"]:
            return True
    return False

# ==============================================================================
# ANSICHT 1: ADMIN-MODUS (TURNIERLEITUNG)
# ==============================================================================
if st.session_state.is_admin:
    tab1, tab2, tab3, tab4 = st.tabs(["1. Teilnehmer", "2. Runden & Ergebnisse", "3. Live-Tabelle", "4. Begegnungs-Statistik"])

    with tab1:
        st.subheader("Spieler anmelden (max. 30)")
        col1, col2, col3, col4, col5 = st.columns([2.3, 0.9, 2.3, 1.2, 1.1])
        with col1:
            name = st.text_input("Name", placeholder="z.B. Max Mustermann")
        with col2:
            geschlecht = st.selectbox("Geschlecht", ["m", "w"])
        with col3:
            staerke = st.selectbox("Spielstärke", [0, 1, 2, 3, 4], index=1, format_func=lambda x: STÄRKE_LABELS[x])
        with col4:
            st.write("")
            st.write("")
            jugend = st.checkbox("Jugend (16-17)")
        with col5:
            st.write("")
            st.write("")
            if st.button("Hinzufügen", use_container_width=True):
                if name and len(st.session_state.spieler) < 30:
                    if any(s["Name"].lower() == name.strip().lower() for s in st.session_state.spieler):
                        st.warning("Name existiert bereits!")
                    else:
                        st.session_state.spieler.append({
                            "Name": name.strip(), "Geschlecht": geschlecht, "Stärke": staerke,
                            "Jugend": jugend, "Aktiv": True, "Spiele": 0, "Pausen": 0,
                            "Letzte_Pause": False, "Partner": [], "Gegner": []
                        })
                        daten_speichern()
                        st.rerun()

        if st.session_state.spieler:
            aktive_spieler = [s for s in st.session_state.spieler if s.get("Aktiv", True)]
            m_count = sum(1 for s in aktive_spieler if s["Geschlecht"] == "m")
            w_count = sum(1 for s in aktive_spieler if s["Geschlecht"] == "w")
            st.write(f"**Spielbereite Teilnehmer: {len(aktive_spieler)} ({m_count} Herren, {w_count} Damen)**")
            
            for idx, s in enumerate(st.session_state.spieler):
                sc1, sc2, sc3, sc4, sc5, sc6 = st.columns([2.8, 0.8, 1.4, 1.8, 1.3, 0.6])
                status_icon = "✅" if s.get("Aktiv", True) else "⏸️"
                jugend_tag = " 🎾*(Jugend)*" if s.get("Jugend", False) else ""
                sc1.write(f"**{s['Name']}**{jugend_tag} {status_icon}")
                sc2.write(f"{'Herr' if s['Geschlecht']=='m' else 'Dame'}")
                
                with sc3:
                    aktuelle_st = s["Stärke"] if s["Stärke"] in [0, 1, 2, 3, 4] else 3
                    neue_staerke = st.selectbox(
                        "Stärke", [0, 1, 2, 3, 4], index=aktuelle_st,
                        key=f"st_edit_{s['Name']}", label_visibility="collapsed", format_func=lambda x: f"Stärke {x}"
                    )
                    if neue_staerke != s["Stärke"]:
                        st.session_state.spieler[idx]["Stärke"] = neue_staerke
                        daten_speichern()
                        st.rerun()
                        
                sc4.write(f"Spiele: {s['Spiele']} | Pausen: {s['Pausen']}")
                with sc5:
                    btn_label = "Abmelden" if s.get("Aktiv", True) else "Aktivieren"
                    if st.button(btn_label, key=f"toggle_{s['Name']}", use_container_width=True):
                        st.session_state.spieler[idx]["Aktiv"] = not s.get("Aktiv", True)
                        daten_speichern()
                        st.rerun()
                with sc6:
                    if len(st.session_state.runden) == 0:
                        if st.button("🗑️", key=f"del_{s['Name']}", help="Spieler komplett entfernen"):
                            st.session_state.spieler.pop(idx)
                            daten_speichern()
                            st.rerun()

            st.divider()

            # --- EIN-KLICK-BACKUP & WIEDERHERSTELLUNG ---
            with st.expander("💾 Backup sichern & wiederherstellen (empfohlen vor & während des Turniers)"):
                b_col1, b_col2 = st.columns(2)
                with b_col1:
                    st.info("Speichere den aktuellen Stand (Teilnehmer, Auslosungen & Ergebnisse) lokal als Datei auf deinem Gerät.")
                    backup_json = json.dumps({
                        "spieler": st.session_state.spieler,
                        "runden": st.session_state.runden,
                        "timer_end": st.session_state.timer_end
                    }, ensure_ascii=False, indent=2)
                    st.download_button(
                        label="⬇️ Aktuellen Turnierstand herunterladen (JSON)",
                        data=backup_json,
                        file_name=f"nachtturnier_backup_r{len(st.session_state.runden)}.json",
                        mime="application/json",
                        use_container_width=True
                    )
                with b_col2:
                    st.info("Lade eine zuvor gesicherte Backup-Datei hoch, um den Spielstand sofort wiederherzustellen.")
                    uploaded_backup = st.file_uploader("Backup-Datei (.json) auswählen", type=["json"], label_visibility="collapsed")
                    if uploaded_backup is not None:
                        if st.button("⬆️ Dieses Backup jetzt einspielen", type="primary", use_container_width=True):
                            try:
                                geladene_daten = json.load(uploaded_backup)
                                if "spieler" in geladene_daten and "runden" in geladene_daten:
                                    st.session_state.spieler = geladene_daten["spieler"]
                                    st.session_state.runden = geladene_daten["runden"]
                                    st.session_state.timer_end = geladene_daten.get("timer_end", None)
                                    daten_speichern()
                                    st.toast("Backup erfolgreich eingespielt!")
                                    st.rerun()
                                else:
                                    st.error("Ungültige Backup-Datei.")
                            except Exception as e:
                                st.error(f"Fehler beim Einlesen: {e}")

            with st.expander("⚠️ Turnier zurücksetzen (Testlauf beenden oder alles löschen)"):
                r_col1, r_col2 = st.columns(2)
                with r_col1:
                    st.info("Alle Runden & Ergebnisse werden auf 0 gesetzt, **deine Teilnehmerliste bleibt erhalten**.")
                    if st.button("🔄 Nur Runden & Ergebnisse zurücksetzen (Spieler behalten)", use_container_width=True):
                        st.session_state.runden = []
                        st.session_state.timer_end = None
                        for s in st.session_state.spieler:
                            s["Spiele"] = 0
                            s["Pausen"] = 0
                            s["Letzte_Pause"] = False
                            s["Partner"] = []
                            s["Gegner"] = []
                        daten_speichern()
                        st.rerun()
                with r_col2:
                    st.warning("Setzt das Programm komplett zurück – **inklusive Löschen aller Spieler**.")
                    if st.button("🗑️ Komplettes Turnier zurücksetzen (inkl. aller Spieler)", use_container_width=True):
                        st.session_state.spieler = []
                        st.session_state.runden = []
                        st.session_state.timer_end = None
                        daten_speichern()
                        st.rerun()

    with tab2:
        st.subheader("Spielrunden verwalten (6 Runden à 20 Min.)")
        aktive_anzahl = sum(1 for s in st.session_state.spieler if s.get("Aktiv", True))
        if aktive_anzahl < 4:
            st.info("Bitte melde zuerst mindestens 4 spielbereite Teilnehmer an.")
        else:
            hat_unveroeffentlichte = any(not r.get("Freigegeben", True) for r in st.session_state.runden)
            if len(st.session_state.runden) < 6:
                if hat_unveroeffentlichte:
                    st.warning("Bitte gib zuerst den aktuellen Runden-Entwurf frei (oder verwirf ihn), bevor du die nächste Runde auslost.")
                else:
                    if st.button(f"🎲 Runde {len(st.session_state.runden) + 1} als Entwurf auslosen", type="primary"):
                        matches, pausierende = generiere_runde(st.session_state.spieler, plaetze=5)
                        st.session_state.runden.append({
                            "Runde": len(st.session_state.runden) + 1,
                            "Matches": matches,
                            "Pause": pausierende,
                            "Original_Matches": copy.deepcopy(matches),
                            "Original_Pause": list(pausierende),
                            "Freigegeben": False
                        })
                        berechne_spieler_historie_neu()
                        daten_speichern()
                        st.rerun()

            for r_idx in range(len(st.session_state.runden) - 1, -1, -1):
                runde = st.session_state.runden[r_idx]
                ist_live = runde.get("Freigegeben", True)
                status_badge = "🟢 LIVE" if ist_live else "🟡 ENTWURF (noch nicht für Teilnehmer sichtbar)"
                
                with st.expander(f"Runde {runde['Runde']} · {status_badge} (Pause: {', '.join(runde['Pause']) if runde['Pause'] else 'Niemand'})", expanded=(r_idx == len(st.session_state.runden) - 1)):
                    
                    if not ist_live:
                        st.warning("🔒 **Vorschau-Modus:** Teilnehmer sehen diese Runde noch nicht. Prüfe die Paarungen und gib sie frei, sobald alles passt.")
                        f_col1, f_col2, f_col3 = st.columns([2, 1.5, 1.5])
                        with f_col1:
                            if st.button(f"📢 Runde {runde['Runde']} jetzt für Teilnehmer freigeben", key=f"pub_r{r_idx}", type="primary", use_container_width=True):
                                st.session_state.runden[r_idx]["Freigegeben"] = True
                                daten_speichern()
                                st.toast(f"Runde {runde['Runde']} ist jetzt live!")
                                st.rerun()
                        with f_col2:
                            if st.button("🎲 Neu auslosen", key=f"reroll_r{r_idx}", use_container_width=True):
                                st.session_state.runden.pop(r_idx)
                                berechne_spieler_historie_neu()
                                matches, pausierende = generiere_runde(st.session_state.spieler, plaetze=5)
                                st.session_state.runden.append({
                                    "Runde": r_idx + 1,
                                    "Matches": matches,
                                    "Pause": pausierende,
                                    "Original_Matches": copy.deepcopy(matches),
                                    "Original_Pause": list(pausierende),
                                    "Freigegeben": False
                                })
                                berechne_spieler_historie_neu()
                                daten_speichern()
                                st.rerun()
                        with f_col3:
                            if st.button("🗑️ Entwurf verwerfen", key=f"drop_r{r_idx}", use_container_width=True):
                                st.session_state.runden.pop(r_idx)
                                berechne_spieler_historie_neu()
                                daten_speichern()
                                st.rerun()
                        st.markdown("---")

                    for m_idx, m in enumerate(runde["Matches"]):
                        c1, c2, c3, c4, c5 = st.columns([1.4, 3.5, 1.5, 1.8, 1.4])
                        c1.markdown(f"**Platz {m['Platz']}** ({m.get('Typ', '')})")
                        c2.write(f"**{m['Team1'][0]} & {m['Team1'][1]}** 🆚 **{m['Team2'][0]} & {m['Team2'][1]}**")
                        
                        with c3:
                            if m["Erfasst"]:
                                st.success(f"✅ {m['Punkte1']}:{m['Punkte2']}")
                            elif m.get("Gemeldet", False):
                                st.info(f"📲 {m['Punkte1']}:{m['Punkte2']}")
                            else:
                                st.caption("⏳ Offen")
                                
                        with c4:
                            sc1, sc2 = st.columns(2)
                            p1 = sc1.number_input(
                                "T1", min_value=0, max_value=99, value=int(m["Punkte1"]),
                                key=f"r{r_idx}_m{m_idx}_p1_{m['Punkte1']}_{m['Punkte2']}", label_visibility="collapsed"
                            )
                            p2 = sc2.number_input(
                                "T2", min_value=0, max_value=99, value=int(m["Punkte2"]),
                                key=f"r{r_idx}_m{m_idx}_p2_{m['Punkte1']}_{m['Punkte2']}", label_visibility="collapsed"
                            )
                        with c5:
                            btn_text = "✅ Bestätigen" if m.get("Gemeldet", False) and not m["Erfasst"] else "💾 Speichern"
                            if st.button(btn_text, key=f"save_r{r_idx}_m{m_idx}", use_container_width=True):
                                runde["Matches"][m_idx]["Punkte1"] = int(p1)
                                runde["Matches"][m_idx]["Punkte2"] = int(p2)
                                runde["Matches"][m_idx]["Erfasst"] = True
                                daten_speichern()
                                st.toast(f"Platz {m['Platz']} gespeichert!")
                                st.rerun()

                    # --- MANUELLE PAARUNGS-ANPASSUNG MIT INTELLIGENTEN TAUSCH-VORSCHLÄGEN ---
                    st.markdown("---")
                    with st.expander(f"🔀 Paarungen in Runde {runde['Runde']} manuell tauschen (inkl. Smart-Vorschläge)", expanded=(not ist_live)):
                        alle_in_runde = []
                        positionen = {}
                        for m_i, match in enumerate(runde["Matches"]):
                            for t_key, team_bez in [("Team1", "Team 1"), ("Team2", "Team 2")]:
                                for s_i, sp_name in enumerate(match[t_key]):
                                    label = f"{sp_name} (Platz {match['Platz']} · {team_bez})"
                                    alle_in_runde.append(label)
                                    positionen[label] = ("match", m_i, t_key, s_i, sp_name)
                        for p_i, p_name in enumerate(runde.get("Pause", [])):
                            label = f"{p_name} (☕ Pause)"
                            alle_in_runde.append(label)
                            positionen[label] = ("pause", p_i, None, None, p_name)

                        if len(alle_in_runde) >= 2:
                            st.caption("1️⃣ Wähle links den Spieler, den du versetzen möchtest – rechts sortiert das System automatisch die besten Tauschpartner nach oben:")
                            sw1, sw2, sw3 = st.columns([1.8, 2.7, 1.2])
                            with sw1:
                                auswahl_a = st.selectbox("Spieler A", alle_in_runde, key=f"swap_a_{r_idx}", label_visibility="collapsed")
                            
                            pos_a = positionen[auswahl_a]
                            kandidaten_liste = bewerte_tausch_kandidaten(r_idx, pos_a)
                            kandidaten_labels = [k[1] for k in kandidaten_liste]
                            kandidaten_map = {k[1]: k[2] for k in kandidaten_liste}

                            with sw2:
                                auswahl_b_label = st.selectbox("Vorgeschlagener Tauschpartner B", kandidaten_labels, key=f"swap_b_{r_idx}_{pos_a[4]}", label_visibility="collapsed")
                            with sw3:
                                if st.button("🔄 Tauschen", key=f"do_swap_{r_idx}", use_container_width=True):
                                    pos_b = kandidaten_map[auswahl_b_label]
                                    name_a = pos_a[4]
                                    name_b = pos_b[4]

                                    if pos_a[0] == "match":
                                        runde["Matches"][pos_a[1]][pos_a[2]][pos_a[3]] = name_b
                                    else:
                                        runde["Pause"][pos_a[1]] = name_b

                                    if pos_b[0] == "match":
                                        runde["Matches"][pos_b[1]][pos_b[2]][pos_b[3]] = name_a
                                    else:
                                        runde["Pause"][pos_b[1]] = name_a

                                    berechne_spieler_historie_neu()
                                    daten_speichern()
                                    st.toast(f"{name_a} ↔ {name_b} getauscht!")
                                    st.rerun()

                        if hat_manuelle_aenderung(runde):
                            if st.button(f"↩️ Manuelle Änderungen verwerfen & Original-Auslosung Runde {runde['Runde']} wiederherstellen", key=f"undo_swap_{r_idx}", use_container_width=True):
                                for m_i, orig_m in enumerate(runde["Original_Matches"]):
                                    runde["Matches"][m_i]["Team1"] = list(orig_m["Team1"])
                                    runde["Matches"][m_i]["Team2"] = list(orig_m["Team2"])
                                runde["Pause"] = list(runde["Original_Pause"])
                                berechne_spieler_historie_neu()
                                daten_speichern()
                                st.toast("Ursprüngliche Auslosung wiederhergestellt!")
                                st.rerun()

                        warnungen = pruefe_runden_kollisionen(r_idx)
                        if warnungen:
                            st.warning("**Automatischer Check (Hinweise zu dieser Runde):**\n\n" + "\n".join(f"- {w}" for w in warnungen))
                        else:
                            st.success("✅ **Check bestanden:** Keine doppelten Partner, keine Mehrfach-Gegner und ausgeglichene Spielstärken.")

    with tab3:
        st.subheader("🏆 Live-Tabelle")
        if st.session_state.spieler:
            st.dataframe(berechne_tabelle_df(), use_container_width=True)

    with tab4:
        st.subheader("📊 Partner- & Gegner-Statistik")
        if not st.session_state.spieler or not st.session_state.runden:
            st.info("Sobald mindestens eine Runde ausgelost wurde, erscheint hier die komplette Begegnungs-Übersicht.")
        else:
            partner_counts = {}
            gegner_counts = {}
            for r in st.session_state.runden:
                for m in r["Matches"]:
                    for team in [m["Team1"], m["Team2"]]:
                        kp = tuple(sorted(team))
                        partner_counts[kp] = partner_counts.get(kp, 0) + 1
                    for a in m["Team1"]:
                        for b in m["Team2"]:
                            kg = tuple(sorted([a, b]))
                            gegner_counts[kg] = gegner_counts.get(kg, 0) + 1

            mehrfach_partner = [(k, v) for k, v in sorted(partner_counts.items(), key=lambda x: -x[1]) if v >= 2]
            mehrfach_gegner = [(k, v) for k, v in sorted(gegner_counts.items(), key=lambda x: -x[1]) if v >= 2]

            stat_c1, stat_c2 = st.columns(2)
            with stat_c1:
                st.markdown("#### 🤝 Mehrfache Doppel-Partner (≥ 2×)")
                if mehrfach_partner:
                    for (p1, p2), cnt in mehrfach_partner:
                        st.warning(f"**{p1} & {p2}** → **{cnt}×** zusammen")
                else:
                    st.success("✅ Bisher hat noch kein Doppel-Team zweimal zusammengespielt!")

            with stat_c2:
                st.markdown("#### ⚔️ Mehrfache Gegner-Duelle (≥ 2×)")
                if mehrfach_gegner:
                    for (p1, p2), cnt in mehrfach_gegner:
                        if cnt >= 3:
                            st.error(f"**{p1} vs. {p2}** → **{cnt}×** gegeneinander")
                        else:
                            st.info(f"**{p1} vs. {p2}** → **{cnt}×** gegeneinander")
                else:
                    st.success("✅ Bisher gab es noch keine wiederholten Gegner-Duelle!")

            st.divider()
            st.markdown("#### 📋 Gesamtübersicht pro Spieler (über alle ausgelosten Runden)")

            def format_haeufigkeit(namens_liste):
                if not namens_liste:
                    return "—"
                counts = {}
                for n in namens_liste:
                    counts[n] = counts.get(n, 0) + 1
                sortiert = sorted(counts.items(), key=lambda x: (-x[1], x[0]))
                return ", ".join([f"{n} ({c}×)" if c > 1 else n for n, c in sortiert])

            uebersicht_rows = []
            for s in sorted(st.session_state.spieler, key=lambda x: x["Name"]):
                uebersicht_rows.append({
                    "Spieler": s["Name"],
                    "Spiele": s["Spiele"],
                    "Pausen": s["Pausen"],
                    "Bisherige Partner": format_haeufigkeit(s.get("Partner", [])),
                    "Bisherige Gegner": format_haeufigkeit(s.get("Gegner", []))
                })
            st.dataframe(pd.DataFrame(uebersicht_rows), use_container_width=True, hide_index=True, height=620)

# ==============================================================================
# ANSICHT 2: TEILNEHMER-MODUS (OPTIMIERT FÜR SMARTPHONES)
# ==============================================================================
else:
    p_tab1, p_tab2, p_tab3 = st.tabs(["🎾 Aktuelle Runde", "🏆 Tabelle", "📋 Alle Runden"])
    
    sichtbare_runden = [(idx, r) for idx, r in enumerate(st.session_state.runden) if r.get("Freigegeben", True)]
    
    with p_tab1:
        if not sichtbare_runden:
            st.info("Das Turnier startet gleich – sobald Runde 1 freigegeben ist, erscheinen hier eure Plätze und Paarungen.")
        else:
            r_idx, aktuelle = sichtbare_runden[-1]
            
            alle_namen = ["— Alle Plätze anzeigen —"] + sorted([s["Name"] for s in st.session_state.spieler])
            mein_name = st.selectbox("🔍 Deinen Namen hervorheben:", alle_namen, label_visibility="collapsed")
            
            st.markdown(f"### Runde {aktuelle['Runde']} von 6")
            
            if aktuelle["Pause"]:
                hat_pause = mein_name in aktuelle["Pause"]
                pause_class = "pause-box-highlight" if hat_pause else "pause-box"
                prefix = "⭐ DU HAST PAUSE:" if hat_pause else "☕ Pause:"
                st.markdown(f'<div class="{pause_class}"><strong>{prefix}</strong> {", ".join(aktuelle["Pause"])}</div>', unsafe_allow_html=True)
                
            jetzt = time.time()
            for m_idx, m in enumerate(aktuelle["Matches"]):
                alle_im_match = m["Team1"] + m["Team2"]
                ist_mein_spiel = mein_name in alle_im_match
                card_class = "court-card-highlight" if ist_mein_spiel else "court-card"
                
                gemeldet_um = m.get("Gemeldet_um", None)
                rest_korrektur_sek = int(300 - (jetzt - gemeldet_um)) if (m.get("Gemeldet", False) and gemeldet_um) else 0
                darf_korrigieren = (not m["Erfasst"]) and m.get("Gemeldet", False) and (rest_korrektur_sek > 0)
                
                if m["Erfasst"]:
                    status_html = f'<span style="color:#4ade80; font-weight:700;">✅ {m["Punkte1"]} : {m["Punkte2"]}</span>'
                elif m.get("Gemeldet", False):
                    if darf_korrigieren:
                        timer_span_id = f"korr_timer_{r_idx}_{m_idx}"
                        status_html = (
                            f'<span style="color:#38bdf8; font-weight:700;">'
                            f'📲 {m["Punkte1"]} : {m["Punkte2"]} · '
                            f'<span id="{timer_span_id}" style="color:#fbbf24; font-variant-numeric: tabular-nums;"></span>'
                            f'</span>'
                        )
                    else:
                        status_html = f'<span style="color:#4ade80; font-weight:700;">🔒 {m["Punkte1"]} : {m["Punkte2"]}</span>'
                else:
                    status_html = '<span style="color:#94a3b8;">Läuft</span>'
                    
                def fmt_name(n):
                    return f"<span style='color:#34d399; text-decoration:underline;'>{n}</span>" if n == mein_name else n
                    
                t1_str = f"{fmt_name(m['Team1'][0])} &amp; {fmt_name(m['Team1'][1])}"
                t2_str = f"{fmt_name(m['Team2'][0])} &amp; {fmt_name(m['Team2'][1])}"
                
                card_html = f"""
                <div class="{card_class}">
                    <div class="court-header">
                        <span><span class="court-badge">PLATZ {m['Platz']}</span> &nbsp;{m.get('Typ', '')}</span>
                        {status_html}
                    </div>
                    <div class="team-row">🟢 {t1_str}</div>
                    <div class="vs-divider">— VS —</div>
                    <div class="team-row">🔵 {t2_str}</div>
                </div>
                """
                st.markdown(card_html, unsafe_allow_html=True)
                
                if darf_korrigieren:
                    korr_end_ms = int((gemeldet_um + 300) * 1000)
                    timer_span_id = f"korr_timer_{r_idx}_{m_idx}"
                    components.html(f"""
                    <script>
                        (function() {{
                            var endT = {korr_end_ms};
                            function tick() {{
                                var el = window.parent.document.getElementById("{timer_span_id}");
                                if (!el) return;
                                var diff = endT - Date.now();
                                if (diff <= 0) {{
                                    el.innerHTML = "gesperrt";
                                    el.style.color = "#94a3b8";
                                    return;
                                }}
                                var m = Math.floor(diff / 60000);
                                var s = Math.floor((diff % 60000) / 1000);
                                el.innerHTML = "✏️ " + (m < 10 ? "0" : "") + m + ":" + (s < 10 ? "0" : "") + s;
                                setTimeout(tick, 250);
                            }}
                            tick();
                        }})();
                    </script>
                    """, height=0)
                
                if (not m["Erfasst"] and not m.get("Gemeldet", False)) or darf_korrigieren:
                    expander_titel = f"✏️ Ergebnis Platz {m['Platz']} korrigieren" if darf_korrigieren else f"📝 Ergebnis Platz {m['Platz']} melden"
                        
                    with st.expander(expander_titel):
                        ic1, ic2 = st.columns(2)
                        with ic1:
                            mp1 = st.number_input(
                                f"🟢 {m['Team1'][0].split()[0]} & {m['Team1'][1].split()[0]}",
                                min_value=0, max_value=99, value=int(m["Punkte1"]),
                                key=f"player_p1_{r_idx}_{m_idx}_{m['Punkte1']}"
                            )
                        with ic2:
                            mp2 = st.number_input(
                                f"🔵 {m['Team2'][0].split()[0]} & {m['Team2'][1].split()[0]}",
                                min_value=0, max_value=99, value=int(m["Punkte2"]),
                                key=f"player_p2_{r_idx}_{m_idx}_{m['Punkte2']}"
                            )
                        btn_label = f"🔄 Korrigiertes Ergebnis Platz {m['Platz']} speichern" if darf_korrigieren else f"📤 Ergebnis Platz {m['Platz']} absenden"
                        if st.button(btn_label, key=f"send_{r_idx}_{m_idx}", type="primary", use_container_width=True):
                            if mp1 == 0 and mp2 == 0:
                                st.warning("Bitte Punkte eingeben.")
                            else:
                                frisch = daten_laden()
                                match_ref = frisch["runden"][r_idx]["Matches"][m_idx]
                                if match_ref.get("Gemeldet_um") and (time.time() - match_ref["Gemeldet_um"] > 300):
                                    st.error("Die 5-Minuten-Korrekturzeit ist abgelaufen – bitte kurz bei der Turnierleitung melden.")
                                else:
                                    match_ref["Punkte1"] = int(mp1)
                                    match_ref["Punkte2"] = int(mp2)
                                    match_ref["Gemeldet"] = True
                                    if not match_ref.get("Gemeldet_um"):
                                        match_ref["Gemeldet_um"] = time.time()
                                    with open(DATEI_SPEICHER, "w", encoding="utf-8") as f:
                                        json.dump(frisch, f, ensure_ascii=False, indent=2)
                                    st.rerun()
                    
    with p_tab2:
        st.subheader("🏆 Live-Tabelle")
        if st.session_state.spieler:
            st.dataframe(berechne_tabelle_df(), use_container_width=True, height=650)
            
    with p_tab3:
        st.subheader("Alle bisherigen Runden")
        if not sichtbare_runden:
            st.write("Noch keine Runden freigegeben.")
        else:
            for _, r in reversed(sichtbare_runden):
                with st.expander(f"Runde {r['Runde']} (Pause: {', '.join(r['Pause']) if r['Pause'] else '-'})", expanded=False):
                    for m in r["Matches"]:
                        erg = f" → **{m['Punkte1']}:{m['Punkte2']}**" if (m["Erfasst"] or m.get("Gemeldet", False)) else ""
                        st.write(f"**Platz {m['Platz']}:** {m['Team1'][0]} & {m['Team1'][1]} vs. {m['Team2'][0]} & {m['Team2'][1]}{erg}")