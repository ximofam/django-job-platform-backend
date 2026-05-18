import django_filters

from .models import Job
from django.contrib.postgres.search import (
    SearchQuery, SearchRank, TrigramWordSimilarity
)
from django.db.models import F, FloatField, Case, When, Value, Q
from django.db.models.functions import Greatest
from rest_framework import filters


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

    district = django_filters.CharFilter(field_name='address__district', lookup_expr='icontains')
    city = django_filters.CharFilter(field_name='address__city', lookup_expr='icontains')

    class Meta:
        model = Job
        fields = [
            'category',
            'salary_min', 'salary_max', 'salary_currency',
            'employment_type', 'experience_level',
            'company_name',
            'district', 'city',
        ]


SIMILARITY_THRESHOLD = 0.4


class JobSearchFilter(filters.SearchFilter):
    search_param = 'search'

    def filter_queryset(self, request, queryset, view):
        search_term = request.query_params.get(self.search_param, '').strip()
        if not search_term:
            return queryset

        fts_query = SearchQuery(search_term, config='simple')

        return (
            queryset
            .annotate(
                fts_rank=Case(
                    When(search_vector=fts_query,
                         then=SearchRank(F('search_vector'), fts_query)),
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
            .filter(
                Q(search_vector=fts_query) |
                Q(fuzzy_rank__gte=SIMILARITY_THRESHOLD)
            )
        )


class JobOrderingFilter(filters.OrderingFilter):
    def get_ordering(self, request, queryset, view):
        ordering = super().get_ordering(request, queryset, view)

        search_term = request.query_params.get('search', '').strip()

        has_explicit_ordering = self.ordering_param in request.query_params

        if search_term:
            if not has_explicit_ordering:
                return ['-score']
            else:
                if ordering:
                    return list(ordering) + ['-score']
                return ['-score']

        return ordering
