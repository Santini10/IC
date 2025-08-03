import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
from pathlib import Path

# ---------- CONFIG GERAL ----------
st.set_page_config(page_title="IFES - Candidato por Vaga", layout="wide")

# ---------- ESTILO (CSS) ----------
st.markdown("""
<style>
/* cor de fundo geral próxima ao PB */
.main { background-color: #f1f1f1; }

/* título centralizado */
.header-title { text-align:center; font-size: 22px; font-weight: 700; margin-top: 4px; }
.sub-title { text-align:center; margin-top: -6px; color:#333; }

/* cards KPI */
.kpi-card {
  background-color: #d9d9d9;
  border: 1px solid #8f8f8f;
  border-radius: 6px;
  padding: 10px 16px;
  text-align:center;
  box-shadow: 0 2px 3px rgba(0,0,0,0.2);
}
.kpi-title { font-size: 16px; font-weight: 700; margin-bottom: 6px; }
.kpi-value { font-size: 30px; font-weight: 700; }

/* títulos das seções dos gráficos */
.section-title {
  font-size: 16px;
  font-weight: 700;
  margin: 6px 0 0 6px;
  color:#222;
}
</style>
""", unsafe_allow_html=True)

# ---------- FUNÇÕES AUXILIARES ----------
def carregar_dados():
    # planilha principal (dados)
    df = pd.read_excel("dados_ifes.xlsx", sheet_name=0)  # ou sheet_name="Dados" se tiver nome

    # planilha de editais
    try:
        df_editais = pd.read_excel("dados_ifes.xlsx", sheet_name="Editais")
    except Exception:
        # se a planilha não existir, cria vazia para não quebrar o app
        df_editais = pd.DataFrame(columns=["semestre", "link"])

    # limpeza básica
    df.columns = [c.strip() for c in df.columns]
    for col in ["Inscritos","Vagas"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # chave de ordenação de Semestre
    def semestre_key(x):
        try:
            ano, per = str(x).split("/")
            return (int(ano), int(per))
        except:
            return (0,0)
    df["__ord"] = df["Semestre"].apply(semestre_key)

    # normaliza nomes da planilha Editais
    if not df_editais.empty:
        df_editais.columns = [c.strip().lower() for c in df_editais.columns]
        # espera colunas: semestre, link
        if "semestre" in df_editais.columns:
            df_editais["semestre"] = df_editais["semestre"].astype(str).str.strip()
        if "link" in df_editais.columns:
            df_editais["link"] = df_editais["link"].astype(str).str.strip()

    return df, df_editais


def format_mil(n):
    # 75_000 -> "75 Mil"; 393_000 -> "393 Mil"
    if pd.isna(n):
        return "0"
    return f"{round(n/1000):,} Mil".replace(",", ".")

def fig_bar_semestre(df_sem, ycol, title, color):
    import plotly.graph_objects as go

    x = df_sem["Semestre"]
    y = df_sem[ycol]

    if ycol in ["Inscritos", "Vagas"]:
        text_vals = [format_mil(v) for v in y]
    else:
        text_vals = [f"{v:.0f}" if v >= 10 else f"{v:.1f}" for v in y]

    fig = go.Figure(
        data=[
            go.Bar(
                x=x,
                y=y,
                text=text_vals,
                textposition="outside",
                marker_color=color,
                # garante que não crie legenda "undefined"
                name=""  
            )
        ]
    )

    fig.update_layout(
        height=330,
        margin=dict(l=30, r=20, t=20, b=40),
        plot_bgcolor="#f1f1f1",
        paper_bgcolor="#f1f1f1",
        showlegend=False,
        # <<< ESSENCIAL: título vazio em vez de None para não aparecer "undefined"
        title_text="",  
    )
    # também remove qualquer título de legenda/resquício
    fig.update_layout(legend_title_text="")

    fig.update_yaxes(title_text=None, gridcolor="#d0d0d0")
    fig.update_xaxes(title_text=None, tickangle=-45, showgrid=False)

    return fig


# ---------- CARREGAMENTO ----------
df, df_editais = carregar_dados()

# ---------- INICIALIZA FILTROS NO SESSION_STATE ----------
def inicializar_filtros():
    if "f_sem" not in st.session_state:
        st.session_state.f_sem = sorted(df["Semestre"].unique(), key=lambda s: df.loc[df["Semestre"]==s,"__ord"].iloc[0])
    if "f_campus" not in st.session_state:
        st.session_state.f_campus = sorted(df["Campus"].dropna().unique())
    if "f_curso" not in st.session_state:
        st.session_state.f_curso = sorted(df["Curso"].dropna().unique())
    if "f_modal" not in st.session_state:
        st.session_state.f_modal = sorted(df["Modalidade"].dropna().unique())
    if "f_turno" not in st.session_state:
        st.session_state.f_turno = sorted(df["Turno"].dropna().unique())

inicializar_filtros()


# ---------- SIDEBAR ----------
with st.sidebar:
    # Logo (opcional)
    logo_path = Path("logo_ifes.png")
    if logo_path.exists():
        st.image(str(logo_path), use_container_width=True)

    f_sem = st.multiselect(
        "Selecione o semestre",
        options=sorted(df["Semestre"].unique(), key=lambda s: df.loc[df["Semestre"] == s, "__ord"].iloc[0]),
        key="f_sem"
    )

    f_campus = st.multiselect(
        "Selecione o campus",
        options=sorted(df["Campus"].dropna().unique()),
        key="f_campus"
    )

    f_curso = st.multiselect(
        "Selecione o curso",
        options=sorted(df["Curso"].dropna().unique()),
        key="f_curso"
    )

    f_modal = st.multiselect(
        "Selecione a modalidade",
        options=sorted(df["Modalidade"].dropna().unique()),
        key="f_modal"
    )

    f_turno = st.multiselect(
        "Selecione o turno",
        options=sorted(df["Turno"].dropna().unique()),
        key="f_turno"
    )

    st.markdown("---")

    # Botão de limpar filtros
    if st.button("🔄 Limpar filtros"):
        for k in ["f_sem", "f_campus", "f_curso", "f_modal", "f_turno"]:
            if k in st.session_state:
                del st.session_state[k]
        st.rerun()





# ==== ABA "Editais" com scroll e ordenação correta ====
with st.expander("Editais", expanded=False):

    def normaliza_url(u: str) -> str:
        if not u:
            return ""
        u = u.strip()
        if not (u.lower().startswith("http://") or u.lower().startswith("https://")):
            u = "https://" + u
        return u

    if df_editais is not None and not df_editais.empty:

        editais_list = df_editais.copy()

        # Garante que os semestres tenham a mesma estrutura do df principal
        # Cria dicionário de ordenação baseado no df principal
        ordem = dict(df[["Semestre", "__ord"]].drop_duplicates().astype(str).values)

        # Mapeia a ordem do semestre para os editais
        editais_list["__ord"] = editais_list["semestre"].map(ordem)

        # Se algum semestre não tiver valor de ordem, colocamos como (9999,9)
        def forca_tupla_ord(v):
            if isinstance(v, tuple):
                return v
            try:
                # tenta converter string tipo "(2020, 1)"
                return eval(v)
            except:
                return (9999, 9)

        editais_list["__ord"] = editais_list["__ord"].apply(forca_tupla_ord)

        # Ordena pela tupla
        editais_list = (
            editais_list
            .sort_values("__ord")
            .drop_duplicates(subset=["semestre", "link"])
        )

        # Caixa com rolagem
        st.markdown(
            "<div style='max-height: 220px; overflow-y: auto; padding-right:6px;'>",
            unsafe_allow_html=True
        )
        for _, r in editais_list.iterrows():
            url = normaliza_url(r.get("link", ""))
            sem = r.get("semestre", "")
            if url:
                st.markdown(f"- [{sem}]({url})")
        st.markdown("</div>", unsafe_allow_html=True)

    else:
        st.info("Adicione a planilha 'Editais' (com colunas: semestre e link) no Excel.")

            
# aplica filtros
mask = (
    df["Semestre"].isin(f_sem) &
    df["Campus"].isin(f_campus) &
    df["Curso"].isin(f_curso) &
    df["Modalidade"].isin(f_modal) &
    df["Turno"].isin(f_turno)
)
df_f = df.loc[mask].copy()
df_f = df_f.sort_values("__ord")

# ---------- MEDIDAS (igual Power BI) ----------
total_inscritos = int(df_f["Inscritos"].sum())
total_vagas = int(df_f["Vagas"].sum())
cand_por_vaga = (total_inscritos / total_vagas) if total_vagas != 0 else 0.0

# agregação por semestre para os gráficos
df_sem = (
    df_f.groupby(["Semestre"], as_index=False)
        .agg(Inscritos=("Inscritos","sum"), Vagas=("Vagas","sum"))
)
# reanexa chave de ordenação e ordena
df_sem["__ord"] = df_sem["Semestre"].map(dict(df[["Semestre","__ord"]].drop_duplicates().values))
df_sem = df_sem.sort_values("__ord")
df_sem["Cand x Vaga"] = df_sem["Inscritos"] / df_sem["Vagas"]
df_sem["Cand x Vaga"] = df_sem["Cand x Vaga"].replace([pd.NA, pd.NaT], 0).fillna(0)

# ---------- CABEÇALHO ----------
st.markdown(
    "<div class='header-title'>Projeto de Iniciação Científica 2024/2025 – Análise dos Indicadores Educacionais do IFES</div>",
    unsafe_allow_html=True
)
st.markdown(
    "<div class='sub-title'>Orientador: Prof. Wagner Teixeira da Costa  |  Aluno: Igor Nunes Leão Santini (Campus Vitória)</div>",
    unsafe_allow_html=True
)
st.write("")  # espaço

# ---------- KPIs EM CARDS ----------
c1, c2, c3 = st.columns([1,1,1], gap="small")
with c1:
    st.markdown("<div class='kpi-card'><div class='kpi-title'>Número de vagas</div>"
                f"<div class='kpi-value'>{total_vagas:,}</div></div>".replace(",", "."), unsafe_allow_html=True)
with c2:
    st.markdown("<div class='kpi-card'><div class='kpi-title'>Número de Inscritos</div>"
                f"<div class='kpi-value'>{total_inscritos:,}</div></div>".replace(",", "."), unsafe_allow_html=True)
with c3:
    st.markdown("<div class='kpi-card'><div class='kpi-title'>Candidato/vaga</div>"
                f"<div class='kpi-value'>{cand_por_vaga:.2f}</div></div>", unsafe_allow_html=True)

st.write("")  # espaço pequeno

# ---------- TÍTULOS E GRÁFICOS (cores fixas) ----------
# Cores aproximadas ao seu PB
COR_AZUL   = "#1f77b4"  # Inscritos
COR_LARANJ = "#ff7f0e"  # Cand/Vaga
COR_AMAREL = "#f2c94c"  # Vagas

st.markdown("<div class='section-title'>Total de Inscritos por Semestre</div>", unsafe_allow_html=True)
st.plotly_chart(fig_bar_semestre(df_sem, "Inscritos", "Inscritos por Semestre", COR_AZUL), use_container_width=True)

st.markdown("<div class='section-title'>Cand/Vaga por Semestre</div>", unsafe_allow_html=True)
st.plotly_chart(fig_bar_semestre(df_sem, "Cand x Vaga", "Cand/Vaga por Semestre", COR_LARANJ), use_container_width=True)

st.markdown("<div class='section-title'>Total de Vagas por Semestre</div>", unsafe_allow_html=True)
st.plotly_chart(fig_bar_semestre(df_sem, "Vagas", "Vagas por Semestre", COR_AMAREL), use_container_width=True)

# opcional: tabela detalhada (pode ocultar se quiser)
# st.dataframe(df_f.drop(columns="__ord"))
