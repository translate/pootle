

from pootle_store.unit.search import UnitSearch
from pootle_store.unit.filters import SearchFilter
from pootle_store.unit.sort import SearchSort
from pootle_store.unit.group import UnitGroups



class ElasticSearchFilter(SearchFilter):

    pass


class ElasticSearchSort(SearchSort):

    pass


class ElasticUnitGroups(UnitGroups):

    pass




class UnitElasticsearchBackend(UnitSearch):

    filter_class = ElasticSearchFilter
    sort_class = ElasticSearchSort
    group_class = ElasticUnitGroups

    def grouped_search(self):
        return super(
            UnitElasticsearchBackend, self).grouped_search()
