from django.contrib import admin

# Register your models here.

from .models import Project, Flow

class FlowInline(admin.TabularInline):
    model = Flow
    extra = 3

class ProjectAdmin(admin.ModelAdmin):
    fieldsets = [
        (None,               {'fields': ['project_name']}),
        ('Date information', {'fields': ['create_date'], 'classes': ['collapse']}),
    ]
    inlines = [FlowInline]
    list_display = ('project_name', 'create_date', 'comments', 'state', 'par_ver_code', 'was_published_recently')
    list_filter = ['create_date']
    search_fields = ['project_name']

admin.site.register(Project, ProjectAdmin)