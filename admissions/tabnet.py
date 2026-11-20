"""Download and parse monthly SUS hospital admissions by state from DATASUS TabNet.

TabNet is the public query front end of DATASUS. The SIH/SUS table used here
(``sih/cnv/niuf.def``) counts approved hospital admissions (AIH) by state, from
January 2008 onwards. A query is a form POST encoded in Latin-1; the answer is an
HTML page with a semicolon-separated table inside a ``<pre>`` block.
"""
from __future__ import annotations

import html
import re
from urllib.parse import quote

import pandas as pd

FORM_URL = "http://tabnet.datasus.gov.br/cgi/deftohtm.exe?sih/cnv/niuf.def"
QUERY_URL = "http://tabnet.datasus.gov.br/cgi/tabcgi.exe?sih/cnv/niuf.def"

# Row variable of the query. Processing month is when the admission was processed
# for payment; service month is when the patient was admitted.
PROCESSING_MONTH = "Ano/mês_processamento"
SERVICE_MONTH = "Ano/mês_atendimento"

_FILTERS = [
    "SRegião", "SUnidade_da_Federação", "SCaráter_atendimento", "SRegime",
    "SCapítulo_CID-10", "SLista_Morb__CID-10", "SFaixa_Etária_1", "SFaixa_Etária_2",
    "SSexo", "SCor/raça",
]

MONTHS_PT = {
    "Janeiro": 1, "Fevereiro": 2, "Março": 3, "Abril": 4, "Maio": 5, "Junho": 6,
    "Julho": 7, "Agosto": 8, "Setembro": 9, "Outubro": 10, "Novembro": 11, "Dezembro": 12,
}

# Month rows come in three shapes depending on the year: "..Janeiro/2008",
# "  Janeiro/2021" and "Janeiro/2023". Year subtotal rows ("2008") are skipped.
_MONTH_ROW = re.compile(r"^[.\s]*([^\W\d_]+)/(\d{4})$")


def _enc(s: str) -> str:
    return quote(s.encode("latin1"), safe="")


def available_files(form_html: str) -> list[str]:
    """Monthly data files offered by the form, e.g. ``niuf2609.dbf``."""
    return re.findall(r'<option[^>]*value="?(niuf\d{4}\.dbf)', form_html, re.I)


def build_query(row: str, files: list[str]) -> str:
    pairs = [("Linha", row), ("Coluna", "Unidade_da_Federação"), ("Incremento", "Internações")]
    pairs += [("Arquivos", f) for f in files]
    pairs += [(f, "TODAS_AS_CATEGORIAS__") for f in _FILTERS]
    pairs += [("formato", "prn"), ("mostre", "Mostra")]
    return "&".join(f"{_enc(k)}={_enc(v)}" for k, v in pairs)


def extract_table(page: str) -> str:
    """The semicolon-separated block of a TabNet result page."""
    m = re.search(r"<pre[^>]*>(.*?)</pre>", page, re.S | re.I)
    return m.group(1) if m else page


def parse_table(text: str) -> pd.DataFrame:
    """Parse a TabNet ``prn`` table into months x states. Dashes mean zero."""
    lines = [html.unescape(l) for l in text.splitlines() if l.strip()]
    header = [c.strip().strip('"') for c in lines[0].split(";")]
    rows = []
    for line in lines[1:]:
        cells = [c.strip().strip('"') for c in line.split(";")]
        m = _MONTH_ROW.match(cells[0])
        if not m or m.group(1) not in MONTHS_PT:
            continue
        month = pd.Timestamp(int(m.group(2)), MONTHS_PT[m.group(1)], 1)
        rows.append([month] + [0 if v == "-" else int(v) for v in cells[1:]])
    df = pd.DataFrame(rows, columns=["month"] + header[1:]).set_index("month").sort_index()
    df = df.drop(columns=[c for c in df.columns if c == "Total"])
    if df.index.duplicated().any():
        raise ValueError("duplicated months in TabNet table")
    return df.asfreq("MS")


def fetch(row: str = PROCESSING_MONTH, timeout: int = 300) -> pd.DataFrame:
    """Query TabNet live. Needs network access; the tests use a saved fixture."""
    import requests

    headers = {"User-Agent": "Mozilla/5.0"}
    form = requests.get(FORM_URL, headers=headers, timeout=timeout).content.decode("latin1")
    files = available_files(form)
    if not files:
        raise RuntimeError("TabNet form returned no data files")
    body = build_query(row, files)
    r = requests.post(
        QUERY_URL, data=body, timeout=timeout,
        headers={**headers, "Content-Type": "application/x-www-form-urlencoded"},
    )
    r.raise_for_status()
    return parse_table(extract_table(r.content.decode("latin1")))
