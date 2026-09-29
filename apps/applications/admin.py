from django.contrib import admin
from .models import Application, ApplicationStatusHistory, FollowUp

class ApplicationStatusHistoryInline(admin.TabularInline):
    model = ApplicationStatusHistory
    extra = 0
    readonly_fields = ('from_status', 'to_status', 'changed_at', 'notes')

class FollowUpInline(admin.TabularInline):
    model = FollowUp
    extra = 0

@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ('user', 'get_company', 'get_title', 'status', 'applied_date', 'deadline', 'updated_at')
    list_filter = ('status', 'source')
    search_fields = ('user__email', 'job__company', 'job__title')
    inlines = [ApplicationStatusHistoryInline, FollowUpInline]

    def get_company(self, obj):
        return obj.job.company
    get_company.short_description = 'Company'

    def get_title(self, obj):
        return obj.job.title
    get_title.short_description = 'Job Title'

@admin.register(FollowUp)
class FollowUpAdmin(admin.ModelAdmin):
    list_display = ('user', 'application', 'follow_up_date', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'follow_up_date')
    search_fields = ('user__email', 'notes')
