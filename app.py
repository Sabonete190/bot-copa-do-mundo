import streamlit as st
import math
import pandas as pd
import os
import requests
import base64
from datetime import datetime

# =========================
# FUNÇÃO KELLY
# =========================

def calcular_kelly(probabilidade, odd):

    if odd <= 1:
        return 0

    b = odd - 1

    kelly = (
        (probabilidade * b)
        - (1 - probabilidade)
    ) / b

    return max(kelly, 0)
# CONFIGURAÇÃO DA PÁGINA
st.set_page_config(
    page_title="Bot copa do mundo",
    layout="centered"
)
st.markdown("""
<style>

.stApp{
    background:#0b0f19;
}

h1,h2,h3{
    color:white;
}

p,label{
    color:#d1d5db;
}

div[data-testid="stNumberInput"]{
    background:#151c2c;
    padding:8px;
    border-radius:12px;
}

div[data-testid="stTextInput"]{
    background:#151c2c;
    padding:8px;
    border-radius:12px;
}

.stButton button{
    width:100%;
    border-radius:12px;
    height:50px;
    font-weight:bold;
}

</style>
""", unsafe_allow_html=True)

# =========================
# SESSION STATE
# =========================

if "melhor_mercado" not in st.session_state:

    st.session_state["melhor_mercado"] = "N/A"

# TÍTULO
st.markdown("""
<div style="
background:#111827;
padding:20px;
border-radius:15px;
text-align:center;
margin-bottom:20px;
">

<h1 style="color:white;">
🏆 BOT COPA DO MUNDO
</h1>

<p style="color:#9ca3af;">
Modelo Estatístico Profissional
</p>

</div>
""", unsafe_allow_html=True)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("ROI", "--")

with col2:
    st.metric("Winrate", "--")

with col3:
    st.metric("Lucro", "--")

with col4:
    st.metric("Apostas", "--")
# =========================
# HISTÓRICO CSV
# =========================

ARQUIVO_HISTORICO = "historico_copa.csv"

ARQUIVO_APRENDIZADO = "aprendizado_copa.csv"

# =========================
# GITHUB
# =========================

GITHUB_TOKEN = st.secrets["GITHUB_TOKEN"]
GITHUB_USER = st.secrets["GITHUB_USER"]
GITHUB_REPO = st.secrets["GITHUB_REPO"]

def salvar_no_github(nome_arquivo):

    url = f"https://api.github.com/repos/{GITHUB_USER}/{GITHUB_REPO}/contents/{nome_arquivo}"

    headers = {
        "Authorization": f"token {GITHUB_TOKEN}"
    }

    with open(nome_arquivo, "rb") as file:
        content = base64.b64encode(file.read()).decode()

    response = requests.get(url, headers=headers)

    sha = None

    if response.status_code == 200:
        sha = response.json()["sha"]

    data = {
        "message": f"Atualizando {nome_arquivo}",
        "content": content,
        "branch": "main"
    }

    if sha:
        data["sha"] = sha

    response = requests.put(
        url,
        headers=headers,
        json=data
    )


def salvar_aposta(dados):

    df_novo = pd.DataFrame([dados])

    if os.path.exists(ARQUIVO_HISTORICO):

        try:

            df_antigo = pd.read_csv(
                ARQUIVO_HISTORICO
            )

        except:

            df_antigo = pd.DataFrame()

        df_final = pd.concat(
            [df_antigo, df_novo],
            ignore_index=True
        )

    else:

        df_final = df_novo

    df_final.to_csv(
        ARQUIVO_HISTORICO,
        index=False
    )

def salvar_aprendizado(dados):

    arquivo = "aprendizado_copa.csv"

    linha = pd.DataFrame([{
    "Data": dados["Data"],
    "Jogo": dados["Jogo"],
    "Mercado": dados["Mercado"],
    "Probabilidade": dados["Probabilidade"],
    "Resultado": dados["Resultado"],
    "Perfil": dados["Perfil"]
}])

    if os.path.exists(arquivo):

        df = pd.read_csv(arquivo)

        df = pd.concat(
            [df, linha],
            ignore_index=True
        )

    else:

        df = linha

    df.to_csv(
        arquivo,
        index=False
    )

def atualizar_pesos():

    arquivo = "aprendizado_copa.csv"

    if not os.path.exists(
        arquivo
    ):

        return

    try:

        df = pd.read_csv(
            arquivo
        )

        df = df[
            df["Resultado"]
            != "PENDENTE"
        ]

        peso_under = 1.00

        peso_btts = 1.00

        fator_elo = 1.00
        
        fator_forma = 0.10

        if len(df) >= 20:

            taxa_geral = (

                len(
                    df[
                        df["Resultado"]
                        == "GREEN"
                    ]
                )

                / len(df)

            )

            fator_elo = round(

                0.80 +

                (taxa_geral * 0.40),

                2

            )
            fator_forma = round(

            0.05 +

            (taxa_geral * 0.10),

            3

            )
        # =========================
        # UNDER 2.5
        # =========================

        df_under = df[
            df["Mercado"]
            == "Under 2.5"
        ]

        if len(
            df_under
        ) >= 20:

            taxa = (

                len(
                    df_under[
                        df_under["Resultado"]
                        == "GREEN"
                    ]
                )

                / len(
                    df_under
                )

            )

            peso_under = round(

                0.80 +

                (taxa * 0.40),

                2

            )

        # =========================
        # BTTS SIM
        # =========================

        df_btts = df[
            df["Mercado"]
            == "BTTS SIM"
        ]

        if len(
            df_btts
        ) >= 20:

            taxa = (

                len(
                    df_btts[
                        df_btts["Resultado"]
                        == "GREEN"
                    ]
                )

                / len(
                    df_btts
                )

            )

            peso_btts = round(

                0.80 +

                (taxa * 0.40),

                2

            )

        df_pesos = pd.DataFrame([{

            "peso_under": peso_under,

            "peso_btts": peso_btts,
            
            "fator_elo": fator_elo,
            
            "fator_forma": fator_forma

        }])

        df_pesos.to_csv(

            "pesos_modelo.csv",

            index=False

        )

    except:

        pass
# =========================
# ODDS 1X2
# =========================

with st.expander("⚽ Mercado 1X2", expanded=True):

    odd_casa = st.number_input(
        "Odd Casa",
        min_value=1.0,
        step=0.01
    )

    odd_empate = st.number_input(
        "Odd Empate",
        min_value=1.0,
        step=0.01
    )

    odd_fora = st.number_input(
        "Odd Fora",
        min_value=1.0,
        step=0.01
    )


# =========================
# OVER / UNDER
# =========================

with st.expander("🎯 Over / Under"):

    odd_over15 = st.number_input(
        "Odd Over 1.5",
        min_value=1.0,
        step=0.01
    )

    odd_over25 = st.number_input(
        "Odd Over 2.5",
        min_value=1.0,
        step=0.01
    )

    odd_under25 = st.number_input(
        "Odd Under 2.5",
        min_value=1.0,
        step=0.01
    )

    odd_over35 = st.number_input(
        "Odd Over 3.5",
        min_value=1.0,
        step=0.01
    )

# =========================
# BTTS
# =========================

with st.expander("🔥 BTTS"):

    odd_btts_sim = st.number_input(
        "Odd BTTS SIM",
        min_value=1.0,
        step=0.01
    )

    odd_btts_nao = st.number_input(
        "Odd BTTS NÃO",
        min_value=1.0,
        step=0.01
     )


# =========================
# DADOS DOS TIMES
# =========================

with st.expander("📊 Dados dos Times"):

    xg_casa = st.number_input(
        "xG Casa",
        min_value=0.0,
        step=0.1
    )

    xg_fora = st.number_input(
        "xG Fora",
        min_value=0.0,
        step=0.1
    )

    xga_casa = st.number_input(
         "xGA Casa",
         min_value=0.0,
         step=0.1
    )

    xga_fora = st.number_input(
         "xGA Fora",
         min_value=0.0,
         step=0.1
    )

    sofridos_casa = st.number_input(
         "Gols Sofridos Casa",
         min_value=0.0,
         step=0.1
    )

    sofridos_fora = st.number_input(
         "Gols Sofridos Fora",
         min_value=0.0,
         step=0.1
    )

    chutes_casa = st.number_input(
         "Chutes no Gol Casa",
         min_value=0.0,
         step=0.1
    )

    chutes_fora = st.number_input(
         "Chutes no Gol Fora",
         min_value=0.0,
         step=0.1
    )

    eficiencia_casa = st.number_input(
         "Eficiência Casa",
         min_value=0.0,
         step=0.1
    )

    eficiencia_fora = st.number_input(
         "Eficiência Fora",
         min_value=0.0,
         step=0.1
    )
# =========================
# FORMA RECENTE
# =========================

with st.expander("📈 Forma Recente"):

    forma_casa = st.number_input(
         "Forma Casa (últimos 5 jogos)",
         min_value=0,
         max_value=15,
         step=1
    )

    forma_fora = st.number_input(
         "Forma Fora (últimos 5 jogos)",
         min_value=0,
         max_value=15,
         step=1
    )

# =========================
# FORÇA AUTOMÁTICA
# =========================

def calcular_forca(odd):

    if odd <= 1.70:
        return 1.35, "Muito Forte"

    elif odd <= 2.10:
        return 1.20, "Forte"

    elif odd <= 2.80:
        return 1.00, "Médio"

    elif odd <= 4.00:
        return 0.80, "Fraco"

    else:
        return 0.65, "Muito Fraco"

forca_casa_valor, nivel_casa = calcular_forca(
    odd_casa
)

forca_fora_valor, nivel_fora = calcular_forca(
    odd_fora
)

st.subheader("Força Automática")

st.write(
    f"Força Casa: {nivel_casa}"
)

st.write(
    f"Força Fora: {nivel_fora}"
)
# =========================
# IDENTIFICAÇÃO DO JOGO
# =========================

time_casa = st.text_input(
    "Time Casa"
)

time_fora = st.text_input(
    "Time Fora"
)

campeonato = st.text_input(
    "Campeonato"
)
fase_copa = st.selectbox(
    "Fase da Copa",
    [
        "Grupos",
        "Oitavas",
        "Quartas",
        "Semifinal",
        "Final"
    ]
)
# =========================
# RANKING ELO
# =========================

elo_casa = st.number_input(
    "Ranking Elo Casa",
    min_value=1000,
    max_value=2500,
    value=2000
)

elo_fora = st.number_input(
    "Ranking Elo Fora",
    min_value=1000,
    max_value=2500,
    value=2000
)

# =========================
# DADOS DA COPA DO MUNDO
# =========================

media_gols_liga = 2.19

media_btts_liga = 0.43

media_over25_liga = 0.36

media_mandante_liga = 0.49

media_visitante_liga = 0.28

media_empate_liga = 0.23

# =========================
# PESOS DINÂMICOS
# =========================

peso_elo = 2000

peso_forma = 0.10

fator_forma = 1.00

peso_under = 1.00

peso_btts = 1.00

fator_elo = 1.00

if os.path.exists(
    "pesos_modelo.csv"
):

    try:

        df_pesos = pd.read_csv(
            "pesos_modelo.csv"
        )

        peso_under = (
            df_pesos.iloc[0]
            ["peso_under"]
        )

        peso_btts = (
            df_pesos.iloc[0]
            ["peso_btts"]
        )

        fator_elo = (
            df_pesos.iloc[0]
            ["fator_elo"]
        )
        
        fator_forma = (

            df_pesos.iloc[0]
            ["fator_forma"]

        )

    except:

        pass

# =========================
# AJUSTE POR FASE
# =========================

ajuste_under = 1.0
ajuste_empate = 1.0
ajuste_btts = 1.0

if fase_copa == "Grupos":

    ajuste_under = 1.00
    ajuste_empate = 1.00
    ajuste_btts = 1.00

elif fase_copa == "Oitavas":

    ajuste_under = 1.08
    ajuste_empate = 1.10
    ajuste_btts = 0.94

elif fase_copa == "Quartas":

    ajuste_under = 1.12
    ajuste_empate = 1.15
    ajuste_btts = 0.90

elif fase_copa == "Semifinal":

    ajuste_under = 1.18
    ajuste_empate = 1.22
    ajuste_btts = 0.85

elif fase_copa == "Final":

    ajuste_under = 1.25
    ajuste_empate = 1.30
    ajuste_btts = 0.80

# =========================
# BOTÃO
# =========================

if st.button("🚀 ANALISAR JOGO"):

    
    # =========================
    # FORÇA OFENSIVA
    # =========================

    ataque_casa = (

    xg_casa * 0.35 +

    chutes_casa * 0.20 +

    eficiencia_casa * 0.15 +

    (forma_casa / 15) * peso_forma +

    forca_casa_valor * 0.10
)

    ataque_fora = (

    xg_fora * 0.35 +

    chutes_fora * 0.20 +

    eficiencia_fora * 0.15 +

    (forma_fora / 15) * peso_forma +

    forca_fora_valor * 0.10
)

    # =========================
    # FORÇA DEFENSIVA
    # =========================

    defesa_casa = (
        xga_casa * 0.6 +
        sofridos_casa * 0.4
    )

    defesa_fora = (
        xga_fora * 0.6 +
        sofridos_fora * 0.4
    )

    # =========================
    # FORÇA DE GOL
    # =========================

    forca_gol = (
        (ataque_casa / (defesa_fora + 0.5)) +
        (ataque_fora / (defesa_casa + 0.5))
    ) / 2

    st.subheader("Análise Estatística")

    st.write(f"Ataque Casa: {round(ataque_casa, 2)}")
    st.write(f"Ataque Fora: {round(ataque_fora, 2)}")

    st.write(f"Defesa Casa: {round(defesa_casa, 2)}")
    st.write(f"Defesa Fora: {round(defesa_fora, 2)}")

    st.write(f"Força de Gol: {round(forca_gol, 2)}")
    # =========================
    # GOLS ESPERADOS
    # =========================

    gols_esperados_casa = (
        ataque_casa / (defesa_fora + 0.5)
    )

    gols_esperados_fora = (
        ataque_fora / (defesa_casa + 0.5)
    )
    # =========================
    # AJUSTE ELO / FIFA
    # =========================

    diferenca_elo = (
        elo_casa - elo_fora
    )

    ajuste_elo = (
    diferenca_elo
    / (peso_elo / fator_elo)
    )

    ajuste_elo = max(
        -0.20,
        min(ajuste_elo, 0.20)
    )

    gols_esperados_casa += ajuste_elo

    gols_esperados_fora -= ajuste_elo

    gols_esperados_casa = max(
        gols_esperados_casa,
        0.10
    )

    gols_esperados_fora = max(
        gols_esperados_fora,
        0.10
    )

    st.subheader("Gols Esperados")

    st.write(
        f"Gols Esperados Casa: {round(gols_esperados_casa, 2)}"
    )

    st.write(
        f"Gols Esperados Fora: {round(gols_esperados_fora, 2)}"
    )
    # =========================
    # POISSON
    # =========================

    def poisson(gols_esperados, gols):
        return (
            (math.exp(-gols_esperados) *
            gols_esperados ** gols)
            / math.factorial(gols)
        )

    st.subheader("Poisson")

    for i in range(4):

        prob_casa_gols = poisson(
            gols_esperados_casa,
            i
        )

        prob_fora_gols = poisson(
            gols_esperados_fora,
            i
        )

        st.write(
            f"Casa marcar {i} gols: "
            f"{round(prob_casa_gols * 100, 2)}%"
        )

        st.write(
            f"Fora marcar {i} gols: "
            f"{round(prob_fora_gols * 100, 2)}%"
        )

        st.write("---")
    # =========================
    # TOP PLACARES
    # =========================

    st.subheader("Placares Mais Prováveis")

    placares = []

    for gols_casa in range(4):

        for gols_fora in range(4):

            prob_placar = (
                poisson(
                    gols_esperados_casa,
                    gols_casa
                )
                *
                poisson(
                    gols_esperados_fora,
                    gols_fora
                )
            )

            placares.append(
                (
                    f"{gols_casa} x {gols_fora}",
                    prob_placar
                )
            )

    placares.sort(
        key=lambda x: x[1],
        reverse=True
    )

    top_placares = placares[:5]

    for placar, probabilidade in top_placares:

        st.write(
            f"{placar} = "
            f"{round(probabilidade * 100, 2)}%"
        )
     # =========================
# OVER/UNDER 2.5
# =========================

    total_gols_esperados = (
        gols_esperados_casa +
        gols_esperados_fora
    )
    # =========================
    # AJUSTE TÁTICO COPA
    # =========================

    total_gols_esperados /= ajuste_under

    # =========================
    # AJUSTE DA COPA DO MUNDO
    # =========================
    prob_under25 = 0

    for gols in range(3):

        prob_under25 += poisson(
            total_gols_esperados,
            gols
        )

    prob_over25 = 1 - prob_under25
    
    prob_under25 *= peso_under

    prob_under25 = min(
        prob_under25,
        0.95
    )

    prob_over25 = 1 - prob_under25

    st.subheader("Over/Under 2.5")

    st.write(
        f"Over 2.5: "
        f"{round(prob_over25 * 100, 2)}%"
    )

    st.write(
        f"Under 2.5: "
        f"{round(prob_under25 * 100, 2)}%"
    )   
    # =========================
    # ODDS JUSTAS OVER/UNDER
    # =========================

    odd_justa_over25 = (
        1 / prob_over25
    )

    odd_justa_under25 = (
        1 / prob_under25
    )

    st.subheader("Odds Justas Over/Under")

    st.write(
        f"Odd Justa Over 2.5: "
        f"{round(odd_justa_over25, 2)}"
    )

    st.write(
        f"Odd Justa Under 2.5: "
        f"{round(odd_justa_under25, 2)}"
    )
    # =========================
    # BTTS
    # =========================

    prob_casa_0 = poisson(
        gols_esperados_casa,
        0
    )

    prob_fora_0 = poisson(
        gols_esperados_fora,
        0
    )

    prob_btts_nao = (
        prob_casa_0 +
        prob_fora_0 -
        (prob_casa_0 * prob_fora_0)
    )

    prob_btts_sim = (

        (1 - prob_btts_nao)

        * media_btts_liga

        / 0.43
    )
    prob_btts_sim *= ajuste_btts
    
    prob_btts_sim *= peso_btts

    prob_btts_sim = min(
        prob_btts_sim,
        0.95
    )

    st.subheader("BTTS")

    st.write(
        f"BTTS SIM: "
        f"{round(prob_btts_sim * 100, 2)}%"
    )

    st.write(
        f"BTTS NÃO: "
        f"{round(prob_btts_nao * 100, 2)}%"
    )
    # =========================
    # ODDS JUSTAS BTTS
    # =========================

    odd_justa_btts_sim = (
        1 / prob_btts_sim
    )

    odd_justa_btts_nao = (
        1 / prob_btts_nao
    )

    st.subheader("Odds Justas BTTS")

    st.write(
        f"Odd Justa BTTS SIM: "
        f"{round(odd_justa_btts_sim, 2)}"
    )

    st.write(
        f"Odd Justa BTTS NÃO: "
        f"{round(odd_justa_btts_nao, 2)}"
    )
    # =========================
    # EV OVER/UNDER
    # =========================

    ev_over25 = (
        prob_over25 * odd_over25
    ) - 1

    ev_under25 = (
        prob_under25 * odd_under25
    ) - 1

    st.subheader("EV Over/Under")

    st.write(
        f"EV Over 2.5: "
        f"{round(ev_over25, 2)}"
    )

    st.write(
        f"EV Under 2.5: "
        f"{round(ev_under25, 2)}"
    )

    # =========================
    # EV BTTS
    # =========================

    ev_btts_sim = (
        prob_btts_sim * odd_btts_sim
    ) - 1

    ev_btts_nao = (
        prob_btts_nao * odd_btts_nao
    ) - 1

    st.subheader("EV BTTS")

    st.write(
        f"EV BTTS SIM: "
        f"{round(ev_btts_sim, 2)}"
    )

    st.write(
        f"EV BTTS NÃO: "
        f"{round(ev_btts_nao, 2)}"
    )
    # =========================
    # EDGE OVER/BTTS
    # =========================

    edge_over25 = (
        prob_over25 -
        (1 / odd_over25)
    )

    edge_under25 = (
        prob_under25 -
        (1 / odd_under25)
    )

    edge_btts_sim = (
        prob_btts_sim -
        (1 / odd_btts_sim)
    )

    edge_btts_nao = (
        prob_btts_nao -
        (1 / odd_btts_nao)
    )

    st.subheader("Edge Over/BTTS")

    st.write(
        f"Edge Over 2.5: "
        f"{round(edge_over25 * 100, 2)}%"
    )

    st.write(
        f"Edge Under 2.5: "
        f"{round(edge_under25 * 100, 2)}%"
    )

    st.write(
        f"Edge BTTS SIM: "
        f"{round(edge_btts_sim * 100, 2)}%"
    )

    st.write(
        f"Edge BTTS NÃO: "
        f"{round(edge_btts_nao * 100, 2)}%"
    )
    # =========================
    # KELLY OVER/BTTS
    # =========================

    kelly_over25 = calcular_kelly(
        prob_over25,
        odd_over25
    )

    kelly_under25 = calcular_kelly(
        prob_under25,
        odd_under25
    )

    kelly_btts_sim = calcular_kelly(
        prob_btts_sim,
        odd_btts_sim
    )

    kelly_btts_nao = calcular_kelly(
        prob_btts_nao,
        odd_btts_nao
    )

    st.subheader("Kelly Over/BTTS")

    st.write(
        f"Kelly Over 2.5: "
        f"{round(kelly_over25 * 100, 2)}%"
    )

    st.write(
        f"Kelly Under 2.5: "
        f"{round(kelly_under25 * 100, 2)}%"
    )

    st.write(
        f"Kelly BTTS SIM: "
        f"{round(kelly_btts_sim * 100, 2)}%"
    )

    st.write(
        f"Kelly BTTS NÃO: "
        f"{round(kelly_btts_nao * 100, 2)}%"
    )
    # =========================
    # PROBABILIDADES PRÓPRIAS
    # =========================

    forca_total = ataque_casa + ataque_fora + defesa_casa + defesa_fora

    prob_casa_modelo = (
        ataque_casa + defesa_fora
    ) / forca_total

    prob_fora_modelo = (
        ataque_fora + defesa_casa
    ) / forca_total

    equilibrio = abs(prob_casa_modelo - prob_fora_modelo)

    prob_empate_modelo = 0.30 - (equilibrio * 0.2)

    prob_empate_modelo *= ajuste_empate

    prob_empate_modelo = max(0.10, prob_empate_modelo)

    soma_modelo = (
        prob_casa_modelo +
        prob_fora_modelo +
        prob_empate_modelo
    )

    prob_casa_modelo /= soma_modelo
    prob_fora_modelo /= soma_modelo
    prob_empate_modelo /= soma_modelo
    
    st.session_state["prob_casa_modelo"] = prob_casa_modelo

    st.session_state["prob_empate_modelo"] = prob_empate_modelo

    st.session_state["prob_fora_modelo"] = prob_fora_modelo

    st.session_state["prob_over25"] = prob_over25

    st.session_state["prob_btts_sim"] = prob_btts_sim

    st.subheader("Probabilidades do Modelo")

    st.write(f"Casa Modelo: {round(prob_casa_modelo * 100, 2)}%")
    st.write(f"Empate Modelo: {round(prob_empate_modelo * 100, 2)}%")
    st.write(f"Fora Modelo: {round(prob_fora_modelo * 100, 2)}%")
    # =========================
    # ODDS JUSTAS
    # =========================

    odd_justa_casa = (
        1 / prob_casa_modelo
    )

    odd_justa_empate = (
        1 / prob_empate_modelo
    )

    odd_justa_fora = (
        1 / prob_fora_modelo
    )

    st.subheader("Odds Justas")

    st.write(
        f"Odd Justa Casa: "
        f"{round(odd_justa_casa, 2)}"
    )

    st.write(
        f"Odd Justa Empate: "
        f"{round(odd_justa_empate, 2)}"
    )

    st.write(
        f"Odd Justa Fora: "
        f"{round(odd_justa_fora, 2)}"
    )
    # =========================
    # PROBABILIDADES IMPLÍCITAS
    # =========================

    prob_casa = 1 / odd_casa
    prob_empate = 1 / odd_empate
    prob_fora = 1 / odd_fora

    # =========================
    # NORMALIZAÇÃO
    # =========================

    soma = prob_casa + prob_empate + prob_fora

    prob_casa /= soma
    prob_empate /= soma
    prob_fora /= soma

    # =========================
    # RESULTADO
    # =========================

    st.success("Análise concluída")

    st.subheader("Probabilidades")

    st.write(f"Casa: {round(prob_casa * 100, 2)}%")
    st.write(f"Empate: {round(prob_empate * 100, 2)}%")
    st.write(f"Fora: {round(prob_fora * 100, 2)}%")

    # =========================
    # EV DO MODELO
    # =========================

    ev_casa = (
        prob_casa_modelo * odd_casa
    ) - 1

    ev_empate = (
        prob_empate_modelo * odd_empate
    ) - 1

    ev_fora = (
        prob_fora_modelo * odd_fora
    ) - 1

    st.subheader("EV do Modelo")

    st.write(
        f"EV Casa: {round(ev_casa, 2)}"
    )

    st.write(
        f"EV Empate: {round(ev_empate, 2)}"
    )

    st.write(
        f"EV Fora: {round(ev_fora, 2)}"
    )
    # =========================
    # EDGE 1X2
    # =========================

    edge_casa = (
        prob_casa_modelo -
        (1 / odd_casa)
    )

    edge_empate = (
        prob_empate_modelo -
        (1 / odd_empate)
    )

    edge_fora = (
        prob_fora_modelo -
        (1 / odd_fora)
    )

    st.subheader("Edge 1X2")

    st.write(
        f"Edge Casa: "
        f"{round(edge_casa * 100, 2)}%"
    )

    st.write(
        f"Edge Empate: "
        f"{round(edge_empate * 100, 2)}%"
    )

    st.write(
        f"Edge Fora: "
        f"{round(edge_fora * 100, 2)}%"
    )
    # =========================
    # EDGE
    # =========================

    edge_casa = (
        prob_casa_modelo - prob_casa
    )

    edge_empate = (
        prob_empate_modelo - prob_empate
    )

    edge_fora = (
        prob_fora_modelo - prob_fora
    )

    st.subheader("Edge do Modelo")

    st.write(
        f"Edge Casa: {round(edge_casa * 100, 2)}%"
    )

    st.write(
        f"Edge Empate: {round(edge_empate * 100, 2)}%"
    )

    st.write(
        f"Edge Fora: {round(edge_fora * 100, 2)}%"
    )
    # =========================
    # KELLY CRITERION
    # =========================

    def calcular_kelly(probabilidade, odd):

        kelly = (
            (
                odd * probabilidade
            ) - 1
        ) / (odd - 1)

        return max(kelly, 0)

    kelly_casa = calcular_kelly(
        prob_casa_modelo,
        odd_casa
    )

    kelly_empate = calcular_kelly(
        prob_empate_modelo,
        odd_empate
    )

    kelly_fora = calcular_kelly(
        prob_fora_modelo,
        odd_fora
    )

    st.subheader("Kelly Criterion")

    st.write(
        f"Kelly Casa: "
        f"{round(kelly_casa * 100, 2)}%"
    )

    st.write(
        f"Kelly Empate: "
        f"{round(kelly_empate * 100, 2)}%"
    )

    st.write(
        f"Kelly Fora: "
        f"{round(kelly_fora * 100, 2)}%"
    )
    # =========================
    # CONFIANÇA DO MODELO
    # =========================

    maior_edge = max(
        abs(edge_casa),
        abs(edge_empate),
        abs(edge_fora)
    )

    maior_ev = max(
        ev_casa,
        ev_empate,
        ev_fora
    )

    confianca = (
        (forca_gol * 4)
        +
        (maior_edge * 20)
        +
        (maior_ev * 10)
    )

    confianca = max(
        0,
        min(confianca, 10)
    )

    st.subheader("Confiança do Modelo")
    
    st.write(
       f"Confiança: {round(confianca,1)}/10"
    )

    st.write(
    f"Confiança: {round(confianca, 1)}/10"
    )
    # =========================
    # DECISÃO INTELIGENTE
    # =========================

    st.subheader("Decisão do Modelo")

    melhor_edge = max(
        edge_casa,
        edge_empate,
        edge_fora
    )

    melhor_ev = max(
        ev_casa,
        ev_empate,
        ev_fora
    )

    if (
        melhor_edge >= 0.10
        and melhor_ev >= 0.10
        and confianca >= 7
    ):

        st.success(
            "🔥 Entrada Forte Detectada"
        )

    elif (
        melhor_edge >= 0.05
        and melhor_ev >= 0.05
        and confianca >= 5
    ):

        st.warning(
            "⚠️ Entrada Moderada"
        )

    else:

        st.error(
            "❌ Jogo Sem Valor"
        )
    # =========================
    # MELHOR MERCADO
    # =========================

    st.subheader("Melhor Mercado")

    melhor_mercado = "Sem valor claro"

    mercados = {

        "🔥 Vitória Casa": edge_casa,
        "🤝 Empate": edge_empate,
        "🔥 Vitória Fora": edge_fora,

        "⚽ Over 2.5": edge_over25,
        "🛡️ Under 2.5": edge_under25,

        "🔥 BTTS SIM": edge_btts_sim,
        "❌ BTTS NÃO": edge_btts_nao
    }

    melhor_mercado = max(
        mercados,
        key=mercados.get
    )

    melhor_edge_mercado = mercados[
        melhor_mercado
    ]

    if melhor_edge_mercado > 0:

        st.success(
            f"Melhor Mercado: {melhor_mercado}"
        )

        st.write(
            f"Edge: "
            f"{round(melhor_edge_mercado * 100, 2)}%"
        )

    else:

        st.error(
            "Sem mercado de valor"
        )
    # =========================
    # GESTÃO DE STAKE
    # =========================

    st.subheader("Stake Sugerida")

    stake = 0

    if (
        melhor_edge >= 0.10
        and melhor_ev >= 0.10
        and confianca >= 7
    ):

        stake = 5

    elif (
        melhor_edge >= 0.05
        and melhor_ev >= 0.05
        and confianca >= 5
    ):

        stake = 2

    else:

        stake = 0

    st.write(
        f"Stake Recomendada: {stake}% da banca"
    )
    # =========================
    # PERFIL DO JOGO
    # =========================

    st.subheader("Perfil da Partida")

    st.write(f"Fase da Copa: {fase_copa}")

    if fase_copa == "Final":

       st.warning(
        "Jogo extremamente conservador"
        )

    elif fase_copa == "Semifinal":

        st.info(
        "Tendência forte de Under"
        )

    perfil_jogo = "⚖️ Equilibrado"

    if fase_copa != "Grupos":

       perfil_jogo = "🏆 Mata-Mata Tenso"

    total_xg = (
        gols_esperados_casa +
        gols_esperados_fora
    )

    diferenca_forca = abs(
        ataque_casa - ataque_fora
    )

    # Jogo explosivo

    if (
        total_xg >= 3
        and prob_over25 >= 0.65
    ):

        perfil_jogo = "🔥 Jogo Explosivo"

    # Jogo defensivo

    elif (
        total_xg <= 2
        and prob_under25 >= 0.55
    ):

        perfil_jogo = "🧱 Jogo Defensivo"

    # Favorito forte

    elif (
        diferenca_forca >= 1
        and confianca >= 7
    ):

        perfil_jogo = "🎯 Favorito Forte"

    # BTTS forte

    elif (
        prob_btts_sim >= 0.65
    ):

        perfil_jogo = "⚔️ Jogo Aberto"

    st.success(
        f"{perfil_jogo}"
    )
# =========================
    # TOP APOSTA
    # =========================

    st.subheader("Top Aposta do Jogo")

    mercados = {

        "Vitória Casa": edge_casa,
        "Empate": edge_empate,
        "Vitória Fora": edge_fora,

        "Over 2.5": edge_over25,
        "Under 2.5": edge_under25,

        "BTTS SIM": edge_btts_sim,
        "BTTS NÃO": edge_btts_nao
    }

    melhor_mercado = max(
        mercados,
        key=mercados.get
    )

    melhor_edge_final = mercados[
        melhor_mercado
    ]

    if melhor_edge_final > 0:

        st.markdown(f"""
    <div style="
    background:#16a34a;
    padding:20px;
    border-radius:15px;
    text-align:center;
    ">

    <h2 style="color:white;">
    🔥 MELHOR APOSTA
    </h2>

    <h1 style="color:white;">
    {melhor_mercado}
    </h1>

    </div>
    """, unsafe_allow_html=True)

        st.markdown(
    f"""
## 🔥 TOP APOSTA

### {melhor_mercado}

Edge: {round(melhor_edge_final * 100, 2)}%

Stake: {stake}%
"""
)

    else:

        st.error(
            "❌ Nenhuma aposta de valor encontrada"
        )

    # =========================
    # SALVAR RESULTADOS
    # =========================

    st.session_state["melhor_mercado"] = melhor_mercado

    st.session_state["ev_casa"] = ev_casa
    st.session_state["ev_empate"] = ev_empate
    st.session_state["ev_fora"] = ev_fora

    st.session_state["edge_casa"] = edge_casa
    st.session_state["edge_empate"] = edge_empate
    st.session_state["edge_fora"] = edge_fora

    st.session_state["stake"] = stake
    st.session_state["confianca"] = confianca
    st.session_state["perfil_jogo"] = perfil_jogo    
    
# =========================
# SALVAR APOSTA
# =========================

if st.button("Salvar Aposta"):

    if os.path.exists(ARQUIVO_HISTORICO):

        try:

            df_ids = pd.read_csv(
                ARQUIVO_HISTORICO
            )

            novo_id = len(df_ids) + 1

        except:

            novo_id = 1

    else:

        novo_id = 1
    dados_aposta = {
        "ID": novo_id,

        "Time Casa": time_casa,

        "Time Fora": time_fora,

        "Campeonato": campeonato,

        "Prob Casa": round(
            st.session_state.get(
                "prob_casa_modelo",
                0
            ),
            4
        ),

        "Prob Empate": round(
            st.session_state.get(
                "prob_empate_modelo",
                0
            ),
            4
        ),

        "Prob Fora": round(
            st.session_state.get(
                "prob_fora_modelo",
                0
            ),
            4
        ),

        "Prob Over25": round(
            st.session_state.get(
                "prob_over25",
                0
            ),
            4
        ),

        "Prob BTTS": round(
            st.session_state.get(
                "prob_btts_sim",
                0
            ),
            4
        ),

        "Mercado": st.session_state.get(
            "melhor_mercado",
            "N/A"
        ),

        "Odd Casa": odd_casa,

        "Odd Empate": odd_empate,

        "Odd Fora": odd_fora,

        "EV Casa": round(
            st.session_state.get(
                "ev_casa",
                0
            ),
            2
        ),

        "EV Empate": round(
            st.session_state.get(
                "ev_empate",
                0
            ),
            2
        ),

        "EV Fora": round(
            st.session_state.get(
                "ev_fora",
                0
            ),
            2
        ),

        "Edge Casa": round(
            st.session_state.get(
                "edge_casa",
                0
            ),
            4
        ),

        "Edge Empate": round(
            st.session_state.get(
                "edge_empate",
                0
            ),
            4
        ),

        "Edge Fora": round(
            st.session_state.get(
                "edge_fora",
                0
            ),
            4
        ),

        "Stake": st.session_state.get(
            "stake",
            0
        ),

        "Confiança": st.session_state.get(
            "confianca",
            0
        ),

        "Perfil": st.session_state.get(
            "perfil_jogo",
            "N/A"
        ),
        
        "Data": datetime.now().strftime(
            "%Y-%m-%d"
        ),

        "Probabilidade": round(
            max(
                st.session_state.get(
                    "prob_casa_modelo",
                    0
                ),
                st.session_state.get(
                    "prob_empate_modelo",
                    0
                ),
                st.session_state.get(
                    "prob_fora_modelo",
                    0
                )
            ),
            4
        ),

        "Resultado": "PENDENTE"
    }

    salvar_aposta(
        dados_aposta
    )
    prob_aprendizado = 0

    mercado_aprendizado = st.session_state.get(
        "melhor_mercado",
        "N/A"
    )

    if mercado_aprendizado == "Casa":

        prob_aprendizado = prob_casa_modelo

    elif mercado_aprendizado == "Empate":

        prob_aprendizado = prob_empate_modelo

    elif mercado_aprendizado == "Fora":

        prob_aprendizado = prob_fora_modelo

    elif mercado_aprendizado == "Over 2.5":

        prob_aprendizado = prob_over25

    elif mercado_aprendizado == "Under 2.5":

        prob_aprendizado = prob_under25

    elif mercado_aprendizado == "BTTS SIM":

        prob_aprendizado = prob_btts_sim

    elif mercado_aprendizado == "BTTS NÃO":

        prob_aprendizado = prob_btts_nao
        
    dados_aprendizado = {

        "Data": datetime.now().strftime(
            "%Y-%m-%d"
        ),

        "Jogo": (
            f"{time_casa} x "
            f"{time_fora}"
        ),

        "Mercado": st.session_state.get(
            "melhor_mercado",
            "N/A"
        ),

        "Probabilidade": round(
            prob_aprendizado,
            4
        ),
        
        "Perfil": st.session_state.get(
          "perfil_jogo",
          "N/A"
        ),
        "Resultado": "PENDENTE"
    }

    salvar_aprendizado(
        dados_aprendizado
    )

    salvar_no_github(
        "aprendizado_copa.csv"
    )

    
    salvar_no_github(
        ARQUIVO_HISTORICO
    )

    st.success(
        "✅ Aposta salva no histórico"
    )

# =========================
# RESULTADO DAS APOSTAS
# =========================

st.subheader("Resultado da Aposta")
# =========================
# CARREGAR HISTÓRICO
# =========================

if os.path.exists(ARQUIVO_HISTORICO):

    try:

        historico_resultados = pd.read_csv(
            ARQUIVO_HISTORICO
        )

    except:

        historico_resultados = pd.DataFrame()

else:

    historico_resultados = pd.DataFrame()

# =========================
# SELECIONAR APOSTA
# =========================
if (
    not historico_resultados.empty
    and "ID" in historico_resultados.columns
):

    id_aposta = st.selectbox(
        "Selecione a aposta",
        historico_resultados["ID"]
    )

else:

    st.warning(
        "Nenhuma aposta com ID encontrada."
    )

if "ID" in historico_resultados.columns:

    aposta_selecionada = historico_resultados[
        historico_resultados["ID"] == id_aposta
    ]

    mercado_atual = aposta_selecionada.iloc[0]["Mercado"]
    st.info(
    f"Mercado Atual: {mercado_atual}"
)
    st.write("Aposta selecionada:")

    st.write(
        aposta_selecionada[
            [
                "Time Casa",
                "Time Fora",
                "Mercado"
            ]
        ]
    )

else:

    st.warning(
        "Salve uma nova aposta para gerar IDs."
    )
resultado_aposta = st.selectbox(
    "Resultado",
    [
        "GREEN",
        "RED",
        "VOID"
    ]
)

valor_stake = st.number_input(
    "Valor da Stake (R$)",
    min_value=0.0,
    value=100.0,
    step=10.0
)

# =========================
# ODD DA APOSTA FEITA
# =========================

odd_aposta = st.number_input(
    "Odd da aposta realizada",
    min_value=1.01,
    value=2.00,
    step=0.01
)

# =========================
# SALVAR RESULTADO
# =========================

if st.button("Salvar Resultado"):

    lucro = 0

    if resultado_aposta == "GREEN":

        lucro = (
            valor_stake * odd_aposta
        ) - valor_stake

    elif resultado_aposta == "RED":

        lucro = -valor_stake

    else:

        lucro = 0

    # =========================
    # PEGAR DADOS DA APOSTA SELECIONADA
    # =========================

    time_casa_resultado = aposta_selecionada.iloc[0]["Time Casa"]

    time_fora_resultado = aposta_selecionada.iloc[0]["Time Fora"]

    campeonato_resultado = aposta_selecionada.iloc[0]["Campeonato"]

    mercado_resultado = aposta_selecionada.iloc[0]["Mercado"]

    # =========================
    # DADOS RESULTADO
    # =========================

    dados_resultado = {

        "Time Casa": time_casa_resultado,

        "Time Fora": time_fora_resultado,

        "Campeonato": campeonato_resultado,

        "Mercado": mercado_resultado,

        "Resultado": resultado_aposta,

        "Stake R$": valor_stake,

        "Odd": odd_aposta,

        "Lucro": round(lucro, 2)
    }

    arquivo_resultados = "resultados_copa.csv"

    df_novo = pd.DataFrame(
        [dados_resultado]
    )

    if os.path.exists(
        arquivo_resultados
    ):

        try:

            df_antigo = pd.read_csv(
                arquivo_resultados
            )

        except:

            df_antigo = pd.DataFrame()

        df_final = pd.concat(
            [
                df_antigo,
                df_novo
            ],
            ignore_index=True
        )

    else:

        df_final = df_novo

    df_final.to_csv(
        arquivo_resultados,
        index=False
    )

# =========================
# ATUALIZAR APRENDIZADO
# =========================

if os.path.exists("aprendizado_copa.csv"):

    try:

        df_aprendizado = pd.read_csv(
            "aprendizado_copa.csv"
        )

        filtro = (
            (df_aprendizado["Jogo"] ==
             f"{time_casa_resultado} x {time_fora_resultado}")
            &
            (df_aprendizado["Mercado"] ==
             mercado_resultado)
            &
            (df_aprendizado["Resultado"] ==
             "PENDENTE")
        )

        df_aprendizado.loc[
            filtro,
            "Resultado"
        ] = resultado_aposta

        df_aprendizado.to_csv(
            "aprendizado_copa.csv",
            index=False
        )

        salvar_no_github(
            "aprendizado_copa.csv"
        )

        df_aprendizado_atual = pd.read_csv(
            "aprendizado_copa.csv"
        )

        jogos_finalizados = len(

            df_aprendizado_atual[

                df_aprendizado_atual[
                    "Resultado"
                ] != "PENDENTE"

            ]

        )

        if jogos_finalizados % 24 == 0:

            atualizar_pesos()

            salvar_no_github(
                "pesos_modelo.csv"
            )

            st.success(
                f"🧠 Pesos atualizados após "
                f"{jogos_finalizados} jogos"
            )

    except:

        pass

   

    st.success(
        "✅ Resultado salvo"
    )

# =========================
# ESTATÍSTICAS DO BOT
# =========================

arquivo_resultados = "resultados_copa.csv"

if os.path.exists(arquivo_resultados):

    try:

        df_stats = pd.read_csv(
            arquivo_resultados
        )

    except:

        df_stats = pd.DataFrame()

else:

    df_stats = pd.DataFrame()

# =========================
# PAINEL
# =========================

st.subheader("Performance do Bot")

st.write("PAINEL CARREGADO")

if not df_stats.empty:

    total_apostas = len(df_stats)

    greens = len(
        df_stats[
            df_stats["Resultado"] == "GREEN"
        ]
    )

    reds = len(
        df_stats[
            df_stats["Resultado"] == "RED"
        ]
    )

    voids = len(
        df_stats[
            df_stats["Resultado"] == "VOID"
        ]
    )

    winrate = (
        (greens / total_apostas) * 100
    )

    lucro_total = (
        df_stats["Lucro"].sum()
    )

    total_stakes = (
        df_stats["Stake R$"].sum()
    )

    if total_stakes > 0:

        roi = (
            lucro_total / total_stakes
        ) * 100

    else:

        roi = 0

    st.write(f"Apostas: {total_apostas}")
    st.write(f"Winrate: {round(winrate,2)}%")
    st.write(f"ROI: {round(roi,2)}%")
    st.write(f"Lucro: R$ {round(lucro_total,2)}")

    st.write(f"🟢 Greens: {greens}")
    st.write(f"🔴 Reds: {reds}")
    st.write(f"⚪ Voids: {voids}")

else:

    st.warning(
        "Nenhum resultado salvo ainda."
    )

# =========================
# COMPARAR PREVISÃO VS RESULTADO
# =========================

if os.path.exists("aprendizado_copa.csv"):

    try:

        df_aprendizado = pd.read_csv(
            "aprendizado_copa.csv"
        )

        df_aprendizado = (
            df_aprendizado[
                df_aprendizado["Resultado"]
                != "PENDENTE"
            ]
        )

        if not df_aprendizado.empty:

            st.subheader(
                "📈 Comparação Previsão vs Resultado"
            )

            mercados = (
                df_aprendizado["Mercado"]
                .unique()
            )

            for mercado in mercados:

                df_mercado = (
                    df_aprendizado[
                        df_aprendizado["Mercado"]
                        == mercado
                    ]
                )

                total = len(df_mercado)

                greens = len(
                    df_mercado[
                        df_mercado["Resultado"]
                        == "GREEN"
                    ]
                )

                acerto = (
                    greens / total
                ) * 100

                st.write(
                    f"🎯 {mercado}"
                )

                st.write(
                    f"🟢 Greens: {greens}"
                )

                reds = len(
                    df_mercado[
                        df_mercado["Resultado"]
                        == "RED"
                    ]
                )

                st.write(
                    f"🔴 Reds: {reds}"
                )

                st.write(
                    f"📈 Acerto: "
                    f"{round(acerto,1)}%"
                )

                st.divider()

            # =========================
            # CALIBRAÇÃO
            # =========================

            st.subheader(
                "🎯 Calibração das Probabilidades"
            )

            faixas = [

                ("50-60%", 0.50, 0.60),

                ("60-70%", 0.60, 0.70),

                ("70-80%", 0.70, 0.80),

                ("80-90%", 0.80, 0.90),

                ("90%+", 0.90, 1.00)

            ]

            for nome, minimo, maximo in faixas:

                df_faixa = df_aprendizado[

                    (
                        df_aprendizado["Probabilidade"]
                        >= minimo
                    )

                    &

                    (
                        df_aprendizado["Probabilidade"]
                        < maximo
                    )

                ]

                total = len(
                    df_faixa
                )

                if total > 0:

                    greens = len(

                        df_faixa[
                            df_faixa["Resultado"]
                            == "GREEN"
                        ]

                    )

                    taxa = (
                        greens / total
                    ) * 100

                    st.write(

                        f"{nome} → "

                        f"{round(taxa,1)}% "

                        f"({greens}/{total})"

                    )
                    st.subheader(
                "🎮 Desempenho por Perfil de Jogo"
            )

            perfis = (
                df_aprendizado["Perfil"]
                .dropna()
                .unique()
            )

            for perfil in perfis:

                df_perfil = (
                    df_aprendizado[
                        df_aprendizado["Perfil"]
                        == perfil
                    ]
                )

                total = len(
                    df_perfil
                )

                greens = len(
                    df_perfil[
                        df_perfil["Resultado"]
                        == "GREEN"
                    ]
                )

                reds = len(
                    df_perfil[
                        df_perfil["Resultado"]
                        == "RED"
                    ]
                )

                if total > 0:

                    taxa = (
                        greens / total
                    ) * 100

                else:

                    taxa = 0

                st.write(
                    f"🎯 {perfil}"
                )

                st.write(
                    f"🟢 Greens: {greens}"
                )

                st.write(
                    f"🔴 Reds: {reds}"
                )

                st.write(
                    f"📈 Acerto: "
                    f"{round(taxa,1)}%"
                )

                st.divider()
                # =========================
            # ROI POR MERCADO
            # =========================

            st.subheader(
                "💰 ROI por Mercado"
            )

            if os.path.exists(
                "resultados_copa.csv"
            ):

                df_roi = pd.read_csv(
                    "resultados_copa.csv"
                )

                mercados_roi = (
                    df_roi["Mercado"]
                    .dropna()
                    .unique()
                )

                for mercado in mercados_roi:

                    df_mercado = df_roi[
                        df_roi["Mercado"]
                        == mercado
                    ]

                    stake_total = (
                        df_mercado["Stake R$"]
                        .sum()
                    )

                    lucro_total = (
                        df_mercado["Lucro"]
                        .sum()
                    )

                    if stake_total > 0:

                        roi = (
                            lucro_total
                            / stake_total
                        ) * 100

                    else:

                        roi = 0

                    st.write(
                        f"🎯 {mercado}"
                    )

                    st.write(
                        f"💰 ROI: {round(roi,2)}%"
                    )

                    st.write(
                        f"📈 Lucro: R$ {round(lucro_total,2)}"
                    )

                    st.write(
                        f"💵 Stake: R$ {round(stake_total,2)}"
                    )

                    st.divider()

    except:

        pass

