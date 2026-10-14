from django.contrib import admin, messages

from . import services
from .models import IncidentReport, IncidentStatus, Review, RouteUpdate


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("booking", "author", "stars", "created_at")
    list_filter = ("stars",)
    search_fields = ("author__email",)
    readonly_fields = ("id", "created_at")


@admin.register(IncidentReport)
class IncidentReportAdmin(admin.ModelAdmin):
    list_display = ("created_at", "category", "reporter", "subject", "status")
    list_filter = ("status", "category")
    search_fields = ("reporter__email", "subject__email")
    readonly_fields = ("id", "created_at", "reviewed_by", "reviewed_at")
    actions = ("mark_reviewed", "mark_resolved", "mark_dismissed")

    def _set_status(self, request, queryset, status):
        for report in queryset:
            services.moderate_incident(report, request.user, status)
        self.message_user(request, f"{queryset.count()} report(s) updated.")

    @admin.action(description="Mark selected as reviewed")
    def mark_reviewed(self, request, queryset):
        self._set_status(request, queryset, IncidentStatus.REVIEWED)

    @admin.action(description="Mark selected as resolved")
    def mark_resolved(self, request, queryset):
        self._set_status(request, queryset, IncidentStatus.RESOLVED)

    @admin.action(description="Dismiss selected")
    def mark_dismissed(self, request, queryset):
        self._set_status(request, queryset, IncidentStatus.DISMISSED)


@admin.register(RouteUpdate)
class RouteUpdateAdmin(admin.ModelAdmin):
    list_display = ("occurred_at", "route", "type", "reporter", "status")
    list_filter = ("status", "type")
    search_fields = ("route__origin_name", "route__destination_name", "reporter__email")
    readonly_fields = ("id", "created_at", "reviewed_by", "reviewed_at")
    actions = ("approve_updates", "reject_updates")

    @admin.action(description="Approve selected route updates")
    def approve_updates(self, request, queryset):
        for update in queryset:
            services.moderate_route_update(update, request.user, approve=True)
        self.message_user(request, f"{queryset.count()} update(s) approved.", level=messages.INFO)

    @admin.action(description="Reject selected route updates")
    def reject_updates(self, request, queryset):
        for update in queryset:
            services.moderate_route_update(update, request.user, approve=False)
        self.message_user(request, f"{queryset.count()} update(s) rejected.", level=messages.INFO)
