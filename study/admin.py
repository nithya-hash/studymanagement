from django.contrib import admin

# Register your models here.
from django.contrib import admin
from .models import Subject, Note, Task, TimetableEntry

admin.site.register(Subject)
admin.site.register(Note)
admin.site.register(Task)
admin.site.register(TimetableEntry)