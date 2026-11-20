from pathlib import Path

import pandas as pd

from admissions import tabnet

FIXTURE = Path(__file__).parent / "fixtures" / "tabnet_sample.html"


def sample():
    return tabnet.parse_table(tabnet.extract_table(FIXTURE.read_text(encoding="utf-8")))


def test_parses_the_three_month_label_formats():
    df = sample().dropna(how="all")
    # "..Janeiro/2007", "  Janeiro/2021" and "Janeiro/2023", with Março written as an HTML entity
    assert list(df.index.strftime("%Y-%m")) == ["2007-01", "2007-03", "2021-01", "2021-03", "2023-01", "2023-03"]


def test_skips_year_subtotals_and_total_columns():
    df = sample()
    assert "Total" not in df.columns
    assert len(df.columns) == 27
    assert df.index.min() == pd.Timestamp("2007-01-01")


def test_dash_means_zero_and_values_are_read_by_state():
    df = sample()
    assert df.loc["2007-01-01", "RO"] == 0
    assert df.loc["2007-01-01", "AC"] == 1
    assert df.loc["2023-01-01", "RO"] == 10229
    assert df.loc["2023-01-01", "PR"] == 72040


def test_query_is_latin1_encoded_and_selects_every_file():
    body = tabnet.build_query(tabnet.PROCESSING_MONTH, ["niuf2609.dbf", "niuf2608.dbf"])
    assert "Linha=Ano%2Fm%EAs_processamento" in body
    assert body.count("Arquivos=") == 2
    assert "formato=prn" in body


def test_available_files_reads_the_form_options():
    form = '<select name="Arquivos"><option value="niuf2609.dbf">set/26</option><option value="niuf0801.dbf">jan/08</option></select>'
    assert tabnet.available_files(form) == ["niuf2609.dbf", "niuf0801.dbf"]
