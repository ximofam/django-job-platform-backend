from django.contrib import admin
from django.utils.html import format_html

from .models import Address, City, Country, District


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "flag_preview", "created_at")
    search_fields = ("code", "name")
    ordering = ("code",)
    readonly_fields = ("flag_preview",)

    def flag_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" height="20" />', obj.image.url)
        return "—"

    flag_preview.short_description = "Flag"


class DistrictInline(admin.TabularInline):
    model = District
    extra = 0
    fields = ("code", "name")
    show_change_link = True


@admin.register(City)
class CityAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "district_count", "created_at")
    search_fields = ("code", "name")
    ordering = ("name",)
    inlines = [DistrictInline]

    def district_count(self, obj):
        return obj.districts.count()

    district_count.short_description = "Districts"


@admin.register(District)
class DistrictAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "city", "address_count", "created_at")
    search_fields = ("code", "name", "city__name")
    list_filter = ("city",)
    list_select_related = ("city",)
    ordering = ("name",)
    autocomplete_fields = ("city",)

    def address_count(self, obj):
        return obj.addresses.count()

    address_count.short_description = "Addresses"


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ("street_address", "district", "city", "full_address_display")
    search_fields = ("street_address", "district__name", "city__name")
    list_filter = ("city", "district")
    list_select_related = ("city", "district")
    autocomplete_fields = ("city", "district")

    def full_address_display(self, obj):
        return obj.full_address

    full_address_display.short_description = "Full address"
