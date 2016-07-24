
import io

import pytest

from translate.storage.factory import getclass


@pytest.mark.django_db
def test_format_props_serializer(test_fs, store_props):
    with test_fs.open("data/props/complex.properties") as test_file:
        test_string = test_file.read()
        test_file.seek(0)
        ttk_props = getclass(test_file)(test_file)
    store_props.update(store_props.deserialize(test_string))
    store_io = io.BytesIO(store_props.serialize())
    # store_io.name = store_props.name
    store_ttk = getclass(store_io)(store_io)
    assert len(store_ttk.units) == len(ttk_props.units)
