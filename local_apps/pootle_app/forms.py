from django import forms
from djblets.siteconfig.forms import SiteSettingsForm
 
 
class GeneralSettingsForm(SiteSettingsForm):
    DESCRIPTION = forms.CharField(
        label="Description",
        required=True)
    TITLE = forms.CharField(
        label="Title",
        required=True)
 
    class Meta:
        title = "General Settings"
