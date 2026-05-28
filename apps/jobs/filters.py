import django_filters
from django.conf import settings
from rest_framework.pagination import CursorPagination
from unidecode import unidecode

from .models import Job
from django.contrib.postgres.search import (
    SearchQuery, SearchRank, TrigramWordSimilarity
)
from django.db.models import F, FloatField, Case, When, Value, Q
from django.db.models.functions import Greatest
from rest_framework import filters

from .utils import remove_vietnamese_accents


class JobFilter(django_filters.FilterSet):
    category = django_filters.NumberFilter(field_name='category__id')
    salary_min = django_filters.NumberFilter(field_name='salary_min', lookup_expr='gte')
    salary_max = django_filters.NumberFilter(field_name='salary_max', lookup_expr='lte')
    salary_currency = django_filters.CharFilter(field_name='salary_currency', lookup_expr='iexact')
    employment_type = django_filters.MultipleChoiceFilter(choices=Job.EmploymentType.choices,
                                                          field_name='employment_type')
    experience_level = django_filters.MultipleChoiceFilter(choices=Job.ExperienceLevel.choices,
                                                           field_name='experience_level')
    company_name = django_filters.CharFilter(field_name='company__name', lookup_expr='icontains')
    district = django_filters.NumberFilter(field_name='address__district_id', lookup_expr='exact')

    class Meta:
        model = Job
        fields = [
            'category',
            'salary_min', 'salary_max', 'salary_currency',
            'employment_type', 'experience_level',
            'company_name',
            'district',
        ]


SIMILARITY_THRESHOLD = 0.4
MIN_FTS_RESULTS = 5


class JobSearchFilter(filters.SearchFilter):
    search_param = 'search'

    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get(self.search_param, '').strip()
        if not search_term:
            return queryset

        search_term_normalized = remove_vietnamese_accents(search_term)
        fts_query = SearchQuery(search_term_normalized, config='simple', search_type='websearch')
        # fts_queryset = self._build_fts_queryset(queryset, fts_query)
        #
        # if fts_queryset[:MIN_FTS_RESULTS].count() >= MIN_FTS_RESULTS:
        #     return fts_queryset
        #
        # return self._build_fuzzy_queryset(queryset, search_term, fts_query)

        return (
            queryset
            .filter(search_vector=fts_query)
            .annotate(score=SearchRank(F('search_vector'), fts_query))
            .order_by('-score')
        )

    def _build_fts_queryset(self, queryset, fts_query):
        return (
            queryset
            .filter(search_vector=fts_query)
            .annotate(score=SearchRank(F('search_vector'), fts_query))
            .order_by('-score')
        )

    def _build_fuzzy_queryset(self, queryset, search_term, fts_query):
        return (
            queryset
            .annotate(
                fts_rank=Case(
                    When(search_vector=fts_query, then=SearchRank(F('search_vector'), fts_query)),
                    default=Value(0.0),
                    output_field=FloatField(),
                ),
                fuzzy_rank=TrigramWordSimilarity(search_term, 'title'),
                score=Greatest(
                    F('fts_rank') * Value(2.0),
                    F('fuzzy_rank'),
                    output_field=FloatField(),
                ),
            )
            .filter(Q(search_vector=fts_query) | Q(fuzzy_rank__gte=SIMILARITY_THRESHOLD))
            .order_by('-score')
        )


class JobOrderingFilter(filters.OrderingFilter):
    def get_ordering(self, request, queryset, view):
        search_term = request.query_params.get('search', '').strip()
        user_ordering = super().get_ordering(request, queryset, view)
        base_ordering = list(user_ordering) if user_ordering else []
        seen_fields = {field.lstrip('-') for field in base_ordering}

        if 'boost_score' not in seen_fields:
            base_ordering.append('-boost_score')

        if search_term and 'score' not in seen_fields:
            base_ordering.append('-score')

        if 'published_at' not in seen_fields:
            base_ordering.append('-published_at')

        if 'id' not in seen_fields:
            base_ordering.append('-id')

        return base_ordering


class JobCursorPagination(CursorPagination):
    page_size = settings.JOB_PAGE_SIZE
    page_size_query_param = 'page_size'
    max_page_size = settings.JOB_MAX_PAGE_SIZE
    ordering = ('-published_at', '-id')
