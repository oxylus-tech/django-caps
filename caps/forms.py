from django import forms

from . import models


__all__ = ("CapabilityDeriveForm",)


class CapabilityDeriveForm(forms.ModelForm):
    """This form specify capability to derive from form"""

    max_derive = forms.IntegerField(required=False)

    class Meta:
        model = models.Capability
        fields = ["permission", "max_derive"]
