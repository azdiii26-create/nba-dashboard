import pandas as pd
import plotly.graph_objects as go

def create_prop_chart(df, stat_col, line_value, last_n=10):
    # Wytnij ostatnie `last_n` meczów
    df = df.tail(last_n)

    # Stwórz nowy DataFrame z potrzebnymi kolumnami
    chart_df = df[['GAME_DATE', 'MATCHUP', stat_col, 'FG3A', 'MIN']].copy()
    chart_df['MIN'] = pd.to_numeric(chart_df['MIN'], errors='coerce')
    chart_df['GAME_DATE'] = pd.to_datetime(chart_df['GAME_DATE']).dt.strftime('%b %d')
    chart_df['OPPONENT'] = chart_df['MATCHUP'].apply(lambda x: " ".join(x.split()[-2:]))
    chart_df['X_LABEL'] = chart_df['OPPONENT'] + "<br>" + chart_df['GAME_DATE']

    # Dodaj kolumnę dla kolorów słupków
    chart_df['color'] = chart_df[stat_col].apply(lambda x: '#2ECC71' if x >= line_value else '#E74C3C')

    # Dodaj kolumnę dla etykiet w słupkach
    chart_df['text'] = chart_df[stat_col].astype(str)

    # Stwórz wykres
    fig = go.Figure(data=go.Bar(
        x=chart_df['X_LABEL'],
        y=chart_df[stat_col],
        marker=dict(
            color=chart_df['color'],
            line=dict(color='rgb(0,0,0)', width=1)
        ),
        text=chart_df['text'],
        textposition='outside'
    ))

    # Dodaj tło i styl
    fig.update_layout(
        title=f'{stat_col} Last {last_n} Games',
        xaxis_title='Game Date',
        yaxis_title=stat_col,
        paper_bgcolor='#0E1117',
        plot_bgcolor='#0E1117',
        font=dict(color='white'),
        legend=dict(x=0, y=1, bgcolor='rgba(0, 0, 0, 0.5)', bordercolor='rgba(0, 0, 0, 0)')
    )

    # Dodaj poziomą linię
    fig.add_hline(y=line_value, line=dict(color='white', dash='dash'), annotation_text=f'Line: {line_value}',
annotation_position='bottom right')

    # Dodaj szarą półprzezroczystą kolumnę dla "FG3M"
    if stat_col == "FG3M":
        fg3a_values = chart_df['FG3A']
        fig.add_trace(go.Bar(
            x=chart_df['X_LABEL'],
            y=fg3a_values,
            marker=dict(color='rgba(150, 150, 150, 0.3)'),
            hoverinfo='none',
            opacity=0.7,
            showlegend=False
        ), secondary_y=True)
        fig.update_yaxes(title='FG3A', secondary_y=True, tickfont=dict(color='lightgray'))

# Dodanie linii minut na prawej osi Y
    fig.add_trace(go.Scatter(
        x=chart_df['X_LABEL'],
        y=chart_df['MIN'],
        name='Minuty (MIN)',
        mode='lines+markers',
        line=dict(color='#F1C40F', width=2, dash='dot'),
        marker=dict(size=6),
        yaxis='y2'
    ))

    fig.update_layout(
        yaxis2=dict(
            title='Minuty',
            overlaying='y',
            side='right',
            showgrid=False,
            range=[0, 48]
        ),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )

    return fig