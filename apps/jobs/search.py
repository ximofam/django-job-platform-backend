from rest_framework import filters
from django.contrib.postgres.search import SearchQuery, SearchRank


class PostgresFullTextSearchFilter(filters.BaseFilterBackend):
    search_param = 'search'

    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get(self.search_param)

        if not search_term:
            return queryset

        query = SearchQuery(search_term, config='simple')

        return queryset.filter(search_vector=query) \
            .annotate(rank=SearchRank('search_vector', query)) \
            .order_by('-rank')
