from __future__ import annotations

from datetime import date
from typing import Optional, TYPE_CHECKING

import holidays
from colorfield.fields import ColorField
from django.conf import settings
from django.contrib.humanize.templatetags.humanize import ordinal
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext as _

from shiftings.shifts.utils.time_frame import TimeFrameType
from shiftings.utils.fields.date_time import DateField
from shiftings.utils.fields.html_color import calc_text_color
from shiftings.utils.time.month import Month, MonthField
from shiftings.utils.time.week import WeekDay, WeekDayField

if TYPE_CHECKING:
    from shiftings.shifts.models.shift import Shift


class ProblemHandling(models.IntegerChoices):
    Ignore = 1, _('ignore')
    Cancel = 2, _('cancel')
    Warn = 3, _('show warning')


class RecurringShift(models.Model):
    name = models.CharField(max_length=100, verbose_name=_('Name'))
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE,
                                     related_name='recurring_shifts', verbose_name=_('Organization'))

    time_frame_field = models.PositiveSmallIntegerField(choices=TimeFrameType.choices, verbose_name=_('Timeframe Type'))
    ordinal = models.PositiveSmallIntegerField(default=1, validators=[MinValueValidator(1), MaxValueValidator(31)],
                                               help_text='')
    week_day_field = WeekDayField(blank=True, null=True)
    month_field = MonthField(blank=True, null=True)
    first_occurrence = DateField(_('First Occurrence'), help_text=_(
        'Choose a minimum day for first occurrence and the system will automatically choose the next applicable day.'))

    template = models.ForeignKey('ShiftTemplateGroup', on_delete=models.SET_NULL, verbose_name=_('Shift Template'),
                                 related_name='recurring_shifts', blank=False, null=True)

    weekend_handling_field = models.PositiveSmallIntegerField(choices=ProblemHandling.choices,
                                                              verbose_name=_('Weekend problem handling'),
                                                              default=ProblemHandling.Ignore)
    weekend_warning = models.TextField(max_length=250, verbose_name=_('Warning text for weekend'), blank=True,
                                       null=True,
                                       help_text=_('A maximum of {amount} characters is allowed').format(amount=250))

    holiday_handling_field = models.PositiveSmallIntegerField(choices=ProblemHandling.choices,
                                                              verbose_name=_('Holidays problem handling'),
                                                              default=ProblemHandling.Ignore)
    holiday_warning = models.TextField(max_length=250, verbose_name=_('Warning text for holidays'), blank=True,
                                       null=True,
                                       help_text=_('A maximum of {amount} characters is allowed').format(amount=250))

    color = ColorField(default='#FD7E14', format='hex', samples=settings.SHIFT_COLOR_PALETTE)

    manually_disabled = models.BooleanField(verbose_name=_('Manually Disabled'), default=False)

    class Meta:
        default_permissions = ()
        ordering = ['organization', 'name']

    def __str__(self) -> str:
        return self.display

    @property
    def display(self) -> str:
        return f'{self.name} ({self.repetition_display})'

    @property
    def time_frame_type(self) -> TimeFrameType:
        return TimeFrameType(self.time_frame_field)

    # noinspection PyUnresolvedReferences
    @property
    def repetition_display(self) -> str:
        return self.get_time_frame_field_display() \
            .replace(_('Nth'), str(ordinal(self.ordinal))) \
            .replace(_('[weekday]'), str(self.get_week_day_field_display())) \
            .replace(_('[month]'), str(self.get_month_field_display()))

    @property
    def week_day(self) -> Optional[WeekDay]:
        if self.week_day_field is not None:
            # noinspection PyTypeChecker
            return WeekDay(self.week_day_field)
        return None

    @property
    def month(self) -> Optional[Month]:
        if self.month_field is not None:
            # noinspection PyTypeChecker
            return Month(self.month_field)
        return None

    @property
    def enabled(self) -> bool:
        return self.template is not None and not self.manually_disabled

    @property
    def weekend_handling(self) -> ProblemHandling:
        return ProblemHandling(self.weekend_handling_field)

    @property
    def holiday_handling(self) -> ProblemHandling:
        return ProblemHandling(self.holiday_handling_field)

    @property
    def text_color(self):
        return calc_text_color(self.color)

    def shift_exists(self, shift: Shift) -> bool:
        return self.created_shifts.filter(name=shift.name, shift_type=shift.shift_type, start=shift.start).exists()

    def shifts_exist(self, _date: date) -> bool:
        if self.template is None:
            return True
        for shift in self.template.get_shift_objs(_date, None, None):
            if not self.shift_exists(shift):
                return False
        return True

    def matches_day(self, _date: date) -> bool:
        return self.time_frame_type.matches_day(self, _date)

    def create_shifts(self, _date: date) -> None:
        if self.template is None:
            return

        weekend_warning = None
        if WeekDay.is_weekend(_date):
            if self.weekend_handling is ProblemHandling.Cancel:
                return None
            elif self.weekend_handling is ProblemHandling.Warn and self.weekend_warning is not None:
                weekend_warning = self.weekend_warning
        holiday_warning = None
        for holiday in settings.HOLIDAY_REGIONS:
            if _date in holidays.country_holidays(holiday.get('country'), holiday.get('region')):
                if self.holiday_handling is ProblemHandling.Cancel:
                    return None
                elif self.weekend_handling is ProblemHandling.Warn and self.holiday_warning is not None:
                    holiday_warning = self.holiday_warning

        shifts = self.template.get_shift_objs(_date, weekend_warning, holiday_warning)
        for shift in shifts:
            if not self.shift_exists(shift):
                shift.based_on = self
                shift.save()
                for participation_permission in self.template.participation_permissions.all():
                    participation_permission.create_copy_for(shift)

    def get_absolute_url(self) -> str:
        return reverse('recurring_shift', args=[self.pk])
