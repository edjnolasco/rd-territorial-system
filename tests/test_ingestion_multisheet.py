from pathlib import Path
import pandas as pd

from rd_territorial_system.ingestion import profile_excel_sheets, select_best_excel_sheet


def test_profile_and_select_best_excel_sheet(tmp_path) -> None:
    path = tmp_path / "one.xlsx"

    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        pd.DataFrame({"foo": [1, 2]}).to_excel(writer, sheet_name="Notas", index=False)
        pd.DataFrame({"provincia": ["Distrito Nacional"], "municipio": ["Santo Domingo de Guzmán"]}).to_excel(
            writer, sheet_name="Division", index=False
        )

    profiles = profile_excel_sheets(path)
    assert len(profiles) == 2

    selected = select_best_excel_sheet(path)
    assert selected == "Division"
