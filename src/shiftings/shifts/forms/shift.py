from typing import Any

from django.forms import Form, HiddenInput, ModelChoiceField, ModelForm

from shiftings.accounts.models import User
from shiftings.organizations.models import Organization
from shiftings.shifts.models import Shift
from shiftings.utils.fields.date_time import DateFormField


class ShiftForm(ModelForm):
    class Meta:
        model = Shift
        fields = ['name', 'place', 'organization', 'event', 'shift_type', 'start', 'end', 'required_users',
                  'max_users', 'additional_infos', 'locked']

    def __init__(self, *args: Any, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.fields['organization'].disabled = True
        organization = self.initial['organization'] if 'organization' in self.initial else self.instance.organization
        self.fields['shift_type'].queryset = organization.shift_types.all()


class SelectOrgForm(Form):
    organization = ModelChoiceField(queryset=Organization.objects.none())
    action_date = DateFormField(widget=HiddenInput())

    def __init__(self, user: User, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['organization'].queryset = user.organizations
