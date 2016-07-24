
import pytest


@pytest.fixture
def store_props():
    """An empty Store in the /language0/project0 TP"""
    from pootle_translationproject.models import TranslationProject

    from pytest_pootle.factories import StoreDBFactory

    tp = TranslationProject.objects.get(
        project__code="project0",
        language__code="language0")

    store = StoreDBFactory(
        parent=tp.directory,
        translation_project=tp,
        name="test_store.properties")
    return store
