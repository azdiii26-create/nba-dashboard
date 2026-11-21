import streamlit as st
from nba_data import get_nba_teams, get_team_roster, get_player_game_log, get_opponent_defense_stats, get_todays_games, get_injured_players, get_team_pace_stats
from charts import create_prop_chart
import pandas as pd

# Ustawienia strony
st.set_page_config(layout="wide")

# Ustawienie szerokiego ekranu i stylu kafelków
st.markdown("""
    <style>
    div[data-testid="stMetric"] {
        background-color: #161B22;
        border: 1px solid #30363D;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

if "coupon" not in st.session_state:
    st.session_state.coupon = []

# Styl CSS
st.markdown(
    """
    <style>
    .stApp {
        background-color: #0E1117;
        color: white;
        font-family: Arial, sans-serif;
    }
    .stButton > button:first-child {
        background-color: #3498db;
        border: none;
        color: white;
        font-size: 16px;
        padding: 10px 20px;
        border-radius: 5px;
    }
    .stButton > button:first-child:hover {
        background-color: #2980b9;
    }
    .stTextInput > input {
        background-color: #34495e;
        color: white;
        border: 1px solid #1abc9c;
        border-radius: 5px;
        padding: 5px;
    }
    .stSlider > input[type="range"]::-webkit-slider-thumb {
        background-color: #1abc9c;
        border: none;
        border-radius: 50%;
    }
    .stSlider > input[type="range"]::-moz-range-thumb {
        background-color: #1abc9c;
        border: none;
        border-radius: 50%;
    }
    .stSlider > input[type="range"] {
        background-color: #1abc9c;
    }
    .stSlider > input[type="range"]::-webkit-slider-runnable-track {
        background-color: #2c3e50;
    }
    .stSlider > input[type="range"]::-moz-range-track {
        background-color: #2c3e50;
    }
    .stSlider > input[type="range"]::-webkit-slider-thumb:hover {
        background-color: #27ae60;
    }
    .stSlider > input[type="range"]::-moz-range-thumb:hover {
        background-color: #27ae60;
    }
    .stSlider > input[type="range"]::-webkit-slider-thumb:active {
        background-color: #27ae60;
    }
    .stSlider > input[type="range"]::-moz-range-thumb:active {
        background-color: #27ae60;
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Cache danych
@st.cache_data(ttl=3600)
def load_player_data(player_id):
    return get_player_game_log(player_id, '2026-27')

@st.cache_data(ttl=3600)
def load_prev_season_data(player_id):
    return get_player_game_log(player_id, '2025-26')

@st.cache_data(ttl=3600)
def load_teams():
    return get_nba_teams()

@st.cache_data(ttl=3600)
def load_roster(team_id):
    return get_team_roster(team_id)

@st.cache_data(ttl=3600)
def load_defense_stats():
    return get_opponent_defense_stats('2026-27')

@st.cache_data(ttl=3600)
def load_pace_stats():
    return get_team_pace_stats('2026-27')

# Panel filtrów
st.sidebar.title("Filtrowanie")

@st.cache_data(ttl=600)
def load_todays_games():
    return get_todays_games()

@st.cache_data(ttl=1800)
def load_injured_players():
    return get_injured_players()

injured_players = load_injured_players()

with st.sidebar.expander("📅 Dzisiejsze mecze NBA", expanded=True):
    todays_games = load_todays_games()
    if todays_games:
        for game in todays_games:
            st.write(f"• {game['label']}")
    else:
        st.write("Brak zaplanowanych meczów na dziś.")

# 1. Wybór drużyny
nba_teams = load_teams()
selected_team = st.sidebar.selectbox(
    "Wybierz drużynę NBA",
    nba_teams,
    format_func=lambda x: x['full_name']
)

# 2. Wybór aktualnego gracza z wybranej drużyny
team_players = load_roster(selected_team['id'])
selected_player = st.sidebar.selectbox(
    "Wybierz gracza",
    team_players,
    format_func=lambda x: f"{x['Player Name']} ({x['Position']})"
)
player_id = selected_player['Player ID']

# 3. Automatyczne wykrywanie dzisiejszego przeciwnika
other_teams = [t for t in nba_teams if t['id'] != selected_team['id']]
today_opp_id = None

for g in todays_games:
    if g['home_id'] == selected_team['id']:
        today_opp_id = g['away_id']
        break
    elif g['away_id'] == selected_team['id']:
        today_opp_id = g['home_id']
        break

default_opp_idx = 0
if today_opp_id:
    for i, t in enumerate(other_teams):
        if t['id'] == today_opp_id:
            default_opp_idx = i
            break
    st.sidebar.success("Wykryto dzisiejszego przeciwnika!")
else:
    st.sidebar.info("Ta drużyna nie gra dziś meczu (możesz wybrać rywala ręcznie).")

opponent_team = st.sidebar.selectbox(
    "Kolejny przeciwnik (Matchup)",
    other_teams,
    index=default_opp_idx,
    format_func=lambda x: x['full_name'],
    key=f"opp_{selected_team['id']}"
)

# Wybór statystyki
stats = {
    "Punkty": "PTS",
    "Asysty": "AST",
    "Zbiórki": "REB",
    "Punkty + Zbiórki": "PTS+REB",
    "Punkty + Asysty": "PTS+AST",
    "Asysty + Zbiórki": "AST+REB",
    "Punkty + Asysty + Zbiórki": "PTS+AST+REB",
    "Przechwyty": "STL",
    "Straty": "TOV",
    "Bloki": "BLK",
    "Trafione rzuty za 3": "FG3M"
}
selected_stat = st.sidebar.selectbox("Wybierz statystykę", list(stats.keys()))
stat_col = stats[selected_stat]

# Wybór liczby ostatnich meczów
last_n = st.sidebar.selectbox("Liczba ostatnich meczów na wykresie", [5, 10, 15, 20], index=1)

# Karta nagłówkowa: zdjęcie gracza + dane + logotypy meczu
h_col1, h_col2, h_col3 = st.columns([1.2, 3, 1.8])

with h_col1:
    headshot_url = f"https://cdn.nba.com/headshots/nba/latest/1040x760/{player_id}.png"
    st.image(headshot_url, use_container_width=True)

with h_col2:
    st.markdown(f"<h1 style='margin-bottom: 0px;'>{selected_player['Player Name']}</h1>", unsafe_allow_html=True)
    st.markdown(
        f"<p style='color: #8B949E; font-size: 1.1rem;'>"
        f"{selected_team['full_name']} &nbsp;|&nbsp; Mecz przeciwko: <b>{opponent_team['full_name']}</b>"
        f"</p>",
        unsafe_allow_html=True
    )
    inj_status = injured_players.get(selected_player['Player Name'].lower())
    if inj_status:
        st.error(f"🚑 Status kontuzji: {inj_status}")
    else:
        st.success("✅ Status: Gotowy do gry")

with h_col3:
    logo1, vs_col, logo2 = st.columns([2, 1, 2])
    with logo1:
        st.image(f"https://cdn.nba.com/logos/nba/{selected_team['id']}/primary/L/logo.svg", width=70)
    with vs_col:
        st.markdown("<h3 style='text-align: center; padding-top: 15px; color: #8B949E;'>VS</h3>", unsafe_allow_html=True)
    with logo2:
        st.image(f"https://cdn.nba.com/logos/nba/{opponent_team['id']}/primary/L/logo.svg", width=70)

st.markdown("---")

player_data = load_player_data(player_id)
if player_data is None or player_data.empty:
    st.warning("Ten gracz nie rozegrał jeszcze żadnych meczów w bieżącym sezonie.")
    st.stop()

# Filtr Dom / Wyjazd
location_filter = st.sidebar.radio(
    "Miejsce meczu",
    ["Wszystkie", "Tylko Dom (vs.)", "Tylko Wyjazd (@)"]
)

if location_filter == "Tylko Dom (vs.)":
    player_data = player_data[player_data['MATCHUP'].str.contains('vs.')]
elif location_filter == "Tylko Wyjazd (@)":
    player_data = player_data[player_data['MATCHUP'].str.contains('@')]

if player_data.empty:
    st.warning(f"Brak meczów dla wybranego filtra: {location_filter}.")
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Wykres i forma",
    "⚔️ Matchup & H2H",
    "📈 Usage Boost",
    "🔥 Skaner meczu",
    "💰 Moje Typy"
])

with tab1:
    # Automatyczna linia bukmacherska ze średniej (zawsze z końcówką .5, np. 24.5)
    season_avg = player_data[stat_col].mean()
    default_line = max(0.5, float(round(season_avg - 0.5) + 0.5))

    # Pole do ręcznej korekty pod Superbet (resetuje się przy zmianie gracza lub statystyki)
    line_value = st.sidebar.number_input(
        "Linia (korekta pod Superbet)",
        min_value=0.5,
        value=default_line,
        step=0.5,
        key=f"line_{player_id}_{stat_col}"
    )
    hit_rate = round((player_data[stat_col] >= line_value).mean() * 100, 2)
    st.markdown(f"**Hit Rate** za cały sezon: {hit_rate}% — {int(hit_rate * len(player_data) / 100)} z{len(player_data)} meczów")

    # Kafelki KPI
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        last_5 = (player_data.tail(5)[stat_col] >= line_value).mean()
        st.metric("LAST 5", f"{last_5:.0%}")

    with col2:
        last_10 = (player_data.tail(10)[stat_col] >= line_value).mean()
        st.metric("LAST 10", f"{last_10:.0%}")

    with col3:
        avg_last_10 = player_data.tail(10)[stat_col].mean()
        avg_last_10_diff = avg_last_10 - line_value
        st.metric("ŚREDNIA L10", f"{avg_last_10:.1f} {'+' if avg_last_10_diff > 0 else ''}{avg_last_10_diff:.1f}")

    with col4:
        avg_season = player_data[stat_col].mean()
        st.metric("ŚREDNIA SEZONOWA", f"{avg_season:.1f}")

    # Trend minut na parkiecie (L5 vs Sezon)
    if 'MIN' in player_data.columns:
        min_series = pd.to_numeric(player_data['MIN'], errors='coerce').dropna()
        if len(min_series) >= 5:
            min_season = min_series.mean()
            min_l5 = min_series.tail(5).mean()
            min_diff = min_l5 - min_season

            if min_diff >= 2.5:
                st.success(f"⏱️ **Trend minut ROŚNIE:** śr. **{min_l5:.1f} min** w L5 (sezon: {min_season:.1f} min | **+{min_diff:.1f}**)")
            elif min_diff <= -2.5:
                st.warning(f"⏱️ **Trend minut SPADA:** śr. **{min_l5:.1f} min** w L5 (sezon: {min_season:.1f} min | **{min_diff:.1f}**) — uważaj na OVER!")
            else:
                st.info(f"⏱️ **Stabilne minuty:** śr. **{min_l5:.1f} min** w L5 (sezon: {min_season:.1f} min)")

    # Wskaźnik zmęczenia (Back-to-Back / dni odpoczynku)
    from datetime import datetime, timedelta

    full_player_data = load_player_data(player_id)
    if full_player_data is not None and not full_player_data.empty:
        last_game_date = pd.to_datetime(full_player_data['GAME_DATE']).max().date()
        # Przeliczenie na datę w USA (ET), żeby w nocy w Polsce dobrze liczyło dni
        us_today = (datetime.now() - timedelta(hours=6)).date()
        days_since_last = (us_today - last_game_date).days

        if days_since_last == 1:
            st.error(f"🔋 **BACK-TO-BACK (0 dni odpoczynku)!** Ostatni mecz: {last_game_date.strftime('%d.%m.%Y')} — wyższe ryzyko zmęczenia lub mniejszych minut.")
        elif days_since_last == 2:
            st.info(f"🔋 **Normalny rytm (1 dzień odpoczynku).** Ostatni mecz: {last_game_date.strftime('%d.%m.%Y')}.")
        elif days_since_last >= 3:
            st.success(f"🔋 **Wypoczęty ({days_since_last - 1} dni odpoczynku).** Ostatni mecz: {last_game_date.strftime('%d.%m.%Y')}.")

    # Wykres
    fig = create_prop_chart(player_data, stat_col, line_value, last_n)
    st.plotly_chart(fig, use_container_width=True)

    # Szybkie zapisywanie typu do Bet Trackera
    with st.expander("➕ Zapisz ten typ do mojego Bet Trackera"):
        b_col1, b_col2, b_col3, b_col4 = st.columns(4)
        with b_col1:
            bet_dir = st.selectbox("Kierunek", ["OVER", "UNDER"], key=f"dir_{player_id}")
        with b_col2:
            bet_odds = st.number_input("Kurs", min_value=1.01, max_value=20.0, value=1.85, step=0.05, key=f"odds_{player_id}")
        with b_col3:
            bet_stake = st.number_input("Stawka (PLN)", min_value=1.0, max_value=10000.0, value=100.0, step=10.0, key=f"stake_{player_id}")
        with b_col4:
            st.write("")
            st.write("")
            save_bet = st.button("💾 Zapisz typ", use_container_width=True)

        if save_bet:
            import os
            from datetime import datetime
            tracker_file = "moje_typy.csv"
            new_bet = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Gracz": selected_player['Player Name'],
                "Mecz": f"{selected_team['abbreviation']} vs {opponent_team['abbreviation']}",
                "Typ": f"{selected_stat} {bet_dir} {line_value}",
                "Kurs": bet_odds,
                "Stawka": bet_stake,
                "Status": "Oczekujący"
            }])
            if os.path.exists(tracker_file):
                old_df = pd.read_csv(tracker_file)
                updated_df = pd.concat([old_df, new_bet], ignore_index=True)
            else:
                updated_df = new_bet
            updated_df.to_csv(tracker_file, index=False)
            st.success("✅ Zapisano typ! Możesz go rozliczyć w zakładce '💰 Moje Typy'.")
        
        if st.button("🛒 Dodaj do kuponu AKO", use_container_width=True):
            st.session_state.coupon.append({
                "Gracz": selected_player['Player Name'],
                "Mecz": f"{selected_team['abbreviation']} vs {opponent_team['abbreviation']}",
                "Typ": f"{selected_stat} {bet_dir} {line_value}",
                "Kurs": bet_odds
            })
            st.success(f"🛒 Dodano do kuponu! Liczba zdarzeń w koszyku: **{len(st.session_state.coupon)}**")

# Podsumowanie
over_line_count = (player_data[stat_col] >= line_value).sum()
avg_last_10 = player_data.tail(10)[stat_col].mean()
st.write(f"Gracz przekroczył linię **{over_line_count}** razy w sezonie.")
st.write(f"Średnia z ostatnich 10 meczów: **{avg_last_10:.1f}**")

with tab2:
    # Analiza obrony kolejnego przeciwnika (Matchup)
    st.subheader(f"Analiza Matchupu vs {opponent_team['full_name']}")
    def_df = load_defense_stats()
    opp_col = f"OPP_{stat_col}"

    if not def_df.empty and opp_col in def_df.columns:
        # Ranking: 1 = najlepsza obrona (pozwala na najmniej), 30 = najsłabsza obrona (pozwala na najwięcej)
        def_df['RANK'] = def_df[opp_col].rank(ascending=True).astype(int)
        opp_row = def_df[def_df['TEAM_ID'] == opponent_team['id']]

        if not opp_row.empty:
            rank = int(opp_row['RANK'].values[0])
            allowed_avg = float(opp_row[opp_col].values[0])

            if rank >= 21:
                st.success(
                    f"**ŁATWY MATCHUP ({rank}. obrona w NBA na 30)** — "
                    f"{opponent_team['full_name']} pozwala rywalom średnio na **{allowed_avg:.1f}** "
                    f"({selected_stat}) na mecz. To zwiększa szanse na przekroczenie linii {line_value}."
                )
            elif rank <= 10:
                st.error(
                    f"**TRUDNY MATCHUP ({rank}. obrona w NBA na 30)** — "
                    f"{opponent_team['full_name']} bardzo dobrze broni tę statystykę "
                    f"(pozwala tylko na **{allowed_avg:.1f}** na mecz). Uważaj z graniem OVER {line_value}."
                )
            else:
                st.info(
                    f"**NEUTRALNY MATCHUP ({rank}. obrona w NBA na 30)** — "
                    f"{opponent_team['full_name']} pozwala rywalom średnio na **{allowed_avg:.1f}** "
                    f"({selected_stat}) na mecz."
                )

    # Analiza tempa gry (Pace Matchup)
    pace_df = load_pace_stats()
    if not pace_df.empty:
        team_pace_row = pace_df[pace_df['TEAM_ID'] == selected_team['id']]
        opp_pace_row = pace_df[pace_df['TEAM_ID'] == opponent_team['id']]

        if not team_pace_row.empty and not opp_pace_row.empty:
            t_pace = float(team_pace_row['PACE'].values[0])
            t_rank = int(team_pace_row['PACE_RANK'].values[0])
            o_pace = float(opp_pace_row['PACE'].values[0])
            o_rank = int(opp_pace_row['PACE_RANK'].values[0])

            avg_rank = (t_rank + o_rank) / 2
            est_pace = (t_pace + o_pace) / 2

            pace_info = (
                f"{selected_team['abbreviation']}: **{t_pace:.1f}** ({t_rank}. w NBA) vs "
                f"{opponent_team['abbreviation']}: **{o_pace:.1f}** ({o_rank}. w NBA) | "
                f"Szac. tempo meczu: **{est_pace:.1f}**"
            )

            if avg_rank <= 11:
                st.success(f"⚡ **SZYBKIE TEMPO MECZU (sprzyja OVER):** {pace_info}")
            elif avg_rank >= 20:
                st.warning(f"🐢 **WOLNE TEMPO MECZU (mniej posiadań):** {pace_info}")
            else:
                st.info(f"⚖️ **ŚREDNIE TEMPO MECZU:** {pace_info}")

            # Ryzyko pogromu (Blowout Risk na podstawie Net Rating)
            if 'NET_RATING' in pace_df.columns:
                t_net = float(team_pace_row['NET_RATING'].values[0])
                o_net = float(opp_pace_row['NET_RATING'].values[0])
                net_diff = abs(t_net - o_net)

                net_info = (
                    f"{selected_team['abbreviation']}: **{t_net:+.1f}** vs "
                    f"{opponent_team['abbreviation']}: **{o_net:+.1f}** "
                    f"(różnica: **{net_diff:.1f}**)"
                )

                if net_diff >= 9.0:
                    st.warning(f"🚨 **WYSOKIE RYZYKO POGROMU (Blowout Risk):** {net_info} — liderzy mogą grać mniej w 4. kwarcie!")
                elif net_diff >= 5.0:
                    st.info(f"⚠️ **Umiarkowana przewaga jednej ze stron:** {net_info}")
                else:
                    st.success(f"🤝 **Wyrównany mecz (niskie ryzyko pogromu):** {net_info}")

    # Historia H2H przeciwko wybranemu rywalowi (obecny + poprzedni sezon)
    st.subheader(f"⚔️ Historia H2H: {selected_player['Player Name']} vs {opponent_team['full_name']}")

    import pandas as pd
    prev_data = load_prev_season_data(player_id)
    all_games = pd.concat([prev_data, player_data], ignore_index=True) if prev_data is not None and not prev_data.empty else player_data.copy()

    opp_abbr = opponent_team['abbreviation']
    h2h_df = all_games[all_games['MATCHUP'].str.endswith(opp_abbr)].copy()

    if not h2h_df.empty and stat_col in h2h_df.columns:
        h2h_avg = h2h_df[stat_col].mean()
        h2h_hit = (h2h_df[stat_col] >= line_value).mean() * 100
        h2h_hits_count = int((h2h_df[stat_col] >= line_value).sum())

        c1, c2, c3 = st.columns(3)
        c1.metric("Mecze H2H (2025-27)", len(h2h_df))
        c2.metric(f"Średnia H2H ({selected_stat})", f"{h2h_avg:.1f}")
        c3.metric(f"Hit Rate H2H (linia {line_value})", f"{h2h_hit:.0f}% ({h2h_hits_count}/{len(h2h_df)})")

        # Wyświetlenie tabeli z konkretnymi meczami (od najnowszych)
        cols_to_show = ['GAME_DATE', 'MATCHUP', 'MIN', stat_col]
        for extra in ['PTS', 'REB', 'AST']:
            if extra in h2h_df.columns and extra not in cols_to_show:
                cols_to_show.append(extra)

        st.dataframe(h2h_df[cols_to_show].iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.info(f"Brak meczów H2H przeciwko {opponent_team['full_name']} w sezonach 2025-27.")

with tab3:
    # Analiza Usage Boost (gra bez wybranego / kontuzjowanego kolegi z drużyny)
    st.subheader("📈 Analiza bez kolegi z drużyny (Usage Boost)")

    teammates = [p for p in team_players if p['Player ID'] != player_id]

    def format_teammate(p):
        inj = injured_players.get(p['Player Name'].lower())
        return f"🚑 {p['Player Name']} ({inj})" if inj else p['Player Name']

    selected_teammate = st.selectbox(
        "Sprawdź statystyki gracza w meczach BEZ tego zawodnika:",
        [None] + teammates,
        format_func=lambda x: "-- Wybierz kolegę z drużyny --" if x is None else format_teammate(x),
        key=f"usage_{player_id}"
    )

    if selected_teammate is not None:
        tm_id = selected_teammate['Player ID']
        tm_curr = load_player_data(tm_id)
        tm_prev = load_prev_season_data(tm_id)

        tm_games_list = [df for df in [tm_prev, tm_curr] if df is not None and not df.empty]
        tm_game_ids = set(pd.concat(tm_games_list, ignore_index=True)['Game_ID']) if tm_games_list else set()

        # Łączymy pełne logi wybranego gracza (2025-27) bez filtra Dom/Wyjazd
        p_curr_full = load_player_data(player_id)
        p_games_list = [df for df in [prev_data, p_curr_full] if df is not None and not df.empty]
        p_all = pd.concat(p_games_list, ignore_index=True) if p_games_list else pd.DataFrame()

        if not p_all.empty and 'Game_ID' in p_all.columns and stat_col in p_all.columns:
            without_tm = p_all[~p_all['Game_ID'].isin(tm_game_ids)]
            with_tm = p_all[p_all['Game_ID'].isin(tm_game_ids)]

            if not without_tm.empty:
                avg_without = without_tm[stat_col].mean()
                hit_without = (without_tm[stat_col] >= line_value).mean() * 100
                hits_count = int((without_tm[stat_col] >= line_value).sum())

                avg_with = with_tm[stat_col].mean() if not with_tm.empty else 0.0
                diff = avg_without - avg_with

                u1, u2, u3 = st.columns(3)
                u1.metric(
                    f"Średnia BEZ ({len(without_tm)} meczów)",
                    f"{avg_without:.1f}",
                    delta=f"{diff:+.1f} vs z nim" if not with_tm.empty else None
                )
                u2.metric(
                    f"Hit Rate BEZ (linia {line_value})",
                    f"{hit_without:.0f}% ({hits_count}/{len(without_tm)})"
                )
                u3.metric(
                    f"Średnia Z ({len(with_tm)} meczów)",
                    f"{avg_with:.1f}" if not with_tm.empty else "Brak"
                )
            else:
                st.info(f"{selected_player['Player Name']} nie rozegrał w sezonach 2025-27 żadnego meczu bez {selected_teammate['Player Name']}.")

with tab4:
    st.subheader(f"🔥 Skaner meczu: {selected_team['full_name']} vs {opponent_team['full_name']}")

    scan_mode = st.radio(
        "Zakres skanowania:",
        [
            f"Tylko {selected_team['full_name']} (TOP 5)",
            f"Cały mecz: {selected_team['abbreviation']} + {opponent_team['abbreviation']} (TOP 10)"
        ],
        horizontal=True
    )

    if st.button("🚀 Uruchom skaner typów"):
        import time
        import pandas as pd

        def_df = load_defense_stats()
        candidates = []

        # Budujemy listę drużyn do przeskanowania: (drużyna_gracza, przeciwnik, skład)
        teams_to_scan = [(selected_team, opponent_team, team_players)]
        if "Cały mecz" in scan_mode:
            opp_roster = load_roster(opponent_team['id'])
            if opp_roster:
                teams_to_scan.append((opponent_team, selected_team, opp_roster))

        total_players = sum(len(roster) for _, _, roster in teams_to_scan)
        processed = 0
        progress_bar = st.progress(0)
        status_text = st.empty()

        for team_obj, opp_obj, roster in teams_to_scan:
            for player in roster:
                processed += 1
                progress_bar.progress(processed / total_players)

                # Pomijamy graczy z raportu kontuzji / wykluczonych na mecz
                if player['Player Name'].lower() in injured_players:
                    continue

                status_text.text(f"Analizuję [{team_obj['abbreviation']}]: {player['Player Name']} ({processed}/{total_players})...")

                p_df = load_player_data(player['Player ID'])
                if p_df is None or len(p_df) < 5:
                    continue

                for stat_name, stat_code in stats.items():
                    if stat_code not in p_df.columns:
                        continue

                    s_avg = p_df[stat_code].mean()
                    if s_avg < 0.8:
                        continue

                    est_line = max(0.5, float(round(s_avg - 0.5) + 0.5))
                    l10 = p_df.tail(10)[stat_code]
                    hit_l10 = (l10 >= est_line).mean() * 100
                    l10_avg = l10.mean()

                    # Sprawdzenie obrony rywala dla konkretnej drużyny
                    opp_col = f"OPP_{stat_code}"
                    rank = 15
                    if not def_df.empty and opp_col in def_df.columns:
                        ranks = def_df[opp_col].rank(ascending=True)
                        opp_match = def_df[def_df['TEAM_ID'] == opp_obj['id']]
                        if not opp_match.empty:
                            rank = int(ranks.loc[opp_match.index[0]])

                    matchup_score = (rank / 30) * 100
                    total_score = (hit_l10 * 0.65) + (matchup_score * 0.35)

                    candidates.append({
                        "Drużyna": team_obj['abbreviation'],
                        "Gracz": player['Player Name'],
                        "Statystyka": stat_name,
                        "Linia (szac.)": est_line,
                        "Średnia L10": round(l10_avg, 1),
                        "Hit Rate L10 (%)": round(hit_l10, 0),
                        "Obrona rywala": f"{rank}/30",
                        "Ocena": round(total_score, 1)
                    })

                time.sleep(0.2)

        progress_bar.empty()
        status_text.empty()

        if candidates:
            top_n = 10 if "Cały mecz" in scan_mode else 5
            top_df = pd.DataFrame(candidates).sort_values(by="Ocena", ascending=False).head(top_n)
            st.dataframe(
    top_df,
    use_container_width=True,
    hide_index=True,
    column_config={
        "Drużyna": st.column_config.TextColumn("Drużyna", width="small"),
        "Linia (szac.)": st.column_config.NumberColumn("Linia", format="%.1f"),
        "Średnia L10": st.column_config.NumberColumn("Śr. L10", format="%.1f"),
        "Hit Rate L10 (%)": st.column_config.ProgressColumn(
            "Hit Rate L10",
            format="%d%%",
            min_value=0,
            max_value=100,
        ),
        "Ocena": st.column_config.ProgressColumn(
            "Siła typu",
            format="%.1f / 100",
            min_value=0,
            max_value=100,
        ),
    }
)
        else:
            st.warning("Nie znaleziono wystarczającej liczby danych do wygenerowania typów.")

with tab5:
    import os
    st.subheader("💰 Twój Bet Tracker & ROI")
    tracker_file = "moje_typy.csv"

    # Sekcja aktywnego kuponu AKO (Koszyk)
    if st.session_state.coupon:
        st.markdown("### 🧾 Aktywny kupon (AKO)")
        coupon_df = pd.DataFrame(st.session_state.coupon)
        st.dataframe(coupon_df, use_container_width=True, hide_index=True)

        # Automatyczne mnożenie kursów
        total_odds = 1.0
        for item in st.session_state.coupon:
            total_odds *= item["Kurs"]

        ak1, ak2, ak3 = st.columns([2, 2, 1])
        with ak1:
            ako_stake = st.number_input("Stawka kuponu (PLN)", min_value=1.0, max_value=10000.0, value=100.0, step=10.0, key="ako_stake")
        with ak2:
            st.metric("Kurs całkowity (AKO)", f"{total_odds:.2f}", f"Potencjalna wygrana: {ako_stake * total_odds:.2f} PLN")
        with ak3:
            st.write("")
            if st.button("🗑️ Wyczyść", use_container_width=True):
                st.session_state.coupon = []
                st.rerun()

        if st.button("💾 Zapisz kupon AKO do historii", type="primary", use_container_width=True):
            from datetime import datetime
            opis_typow = " | ".join([f"{x['Gracz']} ({x['Typ']})" for x in st.session_state.coupon])
            new_ako = pd.DataFrame([{
                "Data": datetime.now().strftime("%Y-%m-%d"),
                "Gracz": f"KUPON AKO ({len(st.session_state.coupon)} zdarz.)",
                "Mecz": "Wiele meczów",
                "Typ": opis_typow,
                "Kurs": round(total_odds, 2),
                "Stawka": ako_stake,
                "Status": "Oczekujący"
            }])
            if os.path.exists(tracker_file):
                old_df = pd.read_csv(tracker_file)
                updated_df = pd.concat([old_df, new_ako], ignore_index=True)
            else:
                updated_df = new_ako
            updated_df.to_csv(tracker_file, index=False)
            st.session_state.coupon = []
            st.success("✅ Zapisano kupon AKO w historii!")
            st.rerun()

        st.markdown("---")
        
    if os.path.exists(tracker_file):
        bets_df = pd.read_csv(tracker_file)

        if not bets_df.empty:
            # Obliczanie statystyk dla rozliczonych typów
            settled = bets_df[bets_df["Status"].isin(["Wygrany", "Przegrany", "Zwrot"])].copy()
            wins = len(settled[settled["Status"] == "Wygrany"])
            losses = len(settled[settled["Status"] == "Przegrany"])
            win_rate = (wins / (wins + losses) * 100) if (wins + losses) > 0 else 0.0

            def calc_profit(row):
                if row["Status"] == "Wygrany":
                    return row["Stawka"] * (row["Kurs"] - 1)
                elif row["Status"] == "Przegrany":
                    return -row["Stawka"]
                return 0.0

            total_profit = settled.apply(calc_profit, axis=1).sum() if not settled.empty else 0.0
            total_staked = settled["Stawka"].sum() if not settled.empty else 0.0
            yield_pct = (total_profit / total_staked * 100) if total_staked > 0 else 0.0

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Wszystkie typy", len(bets_df))
            m2.metric("Skuteczność", f"{win_rate:.1f}% ({wins}-{losses})")
            m3.metric("Zysk / Strata", f"{total_profit:+.2f} PLN")
            m4.metric("Yield", f"{yield_pct:+.1f}%")

            st.markdown("Zmień status w kolumnie **Status** po zakończeniu meczu i kliknij przycisk poniżej:")
            edited_df = st.data_editor(
                bets_df,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Status": st.column_config.SelectboxColumn(
                        "Status",
                        options=["Oczekujący", "Wygrany", "Przegrany", "Zwrot"],
                        required=True
                    )
                }
            )

            if st.button("💾 Zapisz rozliczenia"):
                edited_df.to_csv(tracker_file, index=False)
                st.success("Zaktualizowano historię typów!")
                st.rerun()
        else:
            st.info("Brak zapisanych typów. Dodaj pierwszy typ pod wykresem w zakładce '📊 Wykres i forma'.")
    else:
        st.info("Brak zapisanych typów. Dodaj pierwszy typ pod wykresem w zakładce '📊 Wykres i forma'.")

# Uruchomienie aplikacji
# streamlit run app.py