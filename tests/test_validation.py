import pandas as pd
import pytest

from scripts.build_master_catalog import _validate_columns


def test_validate_columns_ok():
    df = pd.DataFrame(
        {
            "region_code": ["01"],
            "province_code": ["01"],
            "municipality_code": ["01"],
            "district_municipal_code": ["01"],
            "section_code": ["01"],
            "barrio_paraje_code": ["001"],
            "sub_barrio_code": ["01"],
            "name": ["Test"],
        }
    )

    _validate_columns(df)  # no debe lanzar error


def test_validate_columns_missing():
    df = pd.DataFrame(
        {
            "region_code": ["01"],
            "province_code": ["01"],
        }
    )

    with pytest.raises(ValueError):
        _validate_columns(df)
