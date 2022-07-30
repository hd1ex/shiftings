from django.contrib import admin

from shiftings.shifts.models import OrganizationSummarySettings, Participant, RecurringShift, Shift, ShiftGroup, \
    ShiftType

admin.site.register(OrganizationSummarySettings)
admin.site.register(Participant)
admin.site.register(RecurringShift)
admin.site.register(Shift)
admin.site.register(ShiftGroup)
admin.site.register(ShiftType)
