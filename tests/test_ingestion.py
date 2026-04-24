import zipfile

import pytest

from rd_territorial_system.ingestion import load_geojson_from_zip, load_one_table

# 🔴 1. ZIP sin JSON → debe lanzar error

def test_load_geojson_from_zip_without_json(tmp_path):
    zip_path = tmp_path / "test.zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        zf.writestr("file.txt", "no json here")

    with pytest.raises(ValueError):
        load_geojson_from_zip(zip_path)


# 🔴 2. Formato no soportado → debe lanzar error

def test_load_one_table_unsupported_format(tmp_path):
    fake_file = tmp_path / "data.txt"
    fake_file.write_text("invalid")

    with pytest.raises(ValueError):
        load_one_table(fake_file)