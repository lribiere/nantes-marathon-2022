import re
import pandas as pd
import streamlit as st

from datetime import timedelta as td
from plotly import graph_objects as go
from plotly.subplots import make_subplots


def compute_pace_and_speed(dist: float, chrono: td):
    chrono_tot_secs = chrono.total_seconds()
    pace_in_secs = round(chrono_tot_secs / dist, 2)
    minutes = int(pace_in_secs // 60)
    rest_in_sec = round(pace_in_secs % 60, 2)
    pace = f'{minutes}min{rest_in_sec}s'
    speed = round(3600 * dist / chrono_tot_secs, 2)
    return pace_in_secs, pace, speed


def check_chrono_df(df: pd.DataFrame):
    pattern = re.compile(r"^\d{2}:\d{2}:\d{2}$")
    check = df['chrono'].apply(lambda chrono: bool(pattern.match(chrono))).all()
    return check


courses = {
    '--': None,
    'semi-marathon': [3, 6, 11, 14, 21.0975],
    'marathon': [3, 6, 11, 14, 21.0975, 24, 29, 33, 35, 42.195]
}

lengths = {
    '--': None,
    'semi-marathon': [3, 3, 5, 3, 7.0975],
    'marathon': [3, 3, 5, 3, 7.0975, 2.9025, 5, 4, 2, 7.195],
}

xpos = {
    '--': None,
    'semi-marathon': [1.5, 4.5, 8.5, 12.5, 17.548],
    'marathon': [1.5, 4.5, 8.5, 12.5, 17.548, 22.55, 26.5, 31, 34, 38.6],
}

st.set_page_config(layout="wide")

"""
# Nantes - Marathon/Semi-Marathon 2022
"""
tw_url = 'https://twitter.com/LRibiere'
git_url = 'https://github.com/lribiere/nantes-marathon-2022'
st.markdown(f'17/04/2022 - Par [Laurent Ribiere]({tw_url}) - [Source]({git_url})')

course = st.sidebar.selectbox('Quelle course ?', courses.keys(), index=0)
if course != '--':
    """
    ### Chronos
    """
    kms = courses[course]
    chronos = {}
    for km in kms:
        chrono = st.sidebar.text_input(f'Chrono au km {km}', value='HH:MM:SS', max_chars=8)
        chronos[km] = chrono
else:
    st.write("Veuillez selectionner une course (sur la partie gauche de l'écran).")
    st.stop()


chrono_df = pd.Series(chronos).reset_index()
chrono_df.columns = ['km', 'chrono']
st.table(chrono_df)

if check_chrono_df(chrono_df):
    chrono_df['chrono'] = pd.to_timedelta(chrono_df['chrono'])

    "### Analyse"
    _, avg_pace, avg_speed = compute_pace_and_speed(courses[course][-1],
                                                    chrono_df['chrono'].iloc[-1])
    st.write(f'Vitesse / allure moyennes sur l\'ensemble de la course :')
    st.markdown(f'- vitesse : `{avg_speed}` km/h')
    st.markdown(f'- allure : `{avg_pace}`')

    # Compute chrono by segment
    shifted_chrono = chrono_df['chrono'].shift(-1)
    chrono_by_segement_serie = shifted_chrono - chrono_df['chrono']
    chrono_by_segement_serie.drop(len(chrono_df) - 1, inplace=True)
    chrono_by_segement_serie.index = range(1, len(chrono_by_segement_serie) + 1, 1)
    chrono_by_segement_serie.loc[0] = chrono_df['chrono'][0]
    chrono_by_segement_serie.sort_index(inplace=True)

    # Compute segment's length
    segment_lengths_serie = pd.Series(lengths[course])

    chrono_by_segment_df = pd.DataFrame({'segment_length': segment_lengths_serie,
                                         'segment_chrono': chrono_by_segement_serie})
    print(chrono_by_segment_df)
    pace_speed_df = chrono_by_segment_df.apply(
        lambda row: pd.Series(compute_pace_and_speed(row['segment_length'], row['segment_chrono'])),
        axis=1)
    pace_speed_df.columns = ['pace_in_secs', 'pace', 'speed']
    final_df = pd.concat([chrono_df, chrono_by_segment_df, pace_speed_df], axis=1)
    final_df['xpos'] = xpos[course]

    fig = make_subplots(specs=[[{"secondary_y": True}]])
    fig.add_trace(go.Scatter(x=final_df['xpos'], y=final_df['speed'], text=final_df['speed'],
                             mode='lines+markers+text', textposition="top center",
                             name='Vitesse moy. (km/h)'),
                  secondary_y=False)
    fig.add_trace(go.Bar(x=final_df['xpos'], y=final_df['pace_in_secs'], text=final_df['pace'],
                         textposition="outside", width=final_df['segment_length'],
                         name='Allure moy. (min-sec/km)', opacity=0.5,
                         marker_color='lightslategrey'),
                  secondary_y=True)
    fig.update_layout(yaxis_range=[0, 27],
                      yaxis2_range=[0, 900],
                      yaxis2_showgrid=False,
                      yaxis2_showticklabels=False,
                      title="Vitesse et allure par section",
                      xaxis_title="Km",
                      yaxis_title="Vitesse (km/h)",
                      xaxis=dict(
                          tickmode='linear',
                          tick0=0,
                          dtick=1
                      ),
                      height=600)
    st.plotly_chart(fig, use_container_width=True)
else:
    st.write('Veuillez saisir les chronomètres (sur la partie gauche de l\'écran).')
    st.stop()

