from django import forms

# Create forms here.


class BusinessContactForm(forms.Form):
    name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Name"})
    )
    organization = forms.CharField(
        max_length=120,
        widget=forms.TextInput(attrs={"placeholder": "Organization"})
    )
    email = forms.EmailField(
        widget=forms.TextInput(
            attrs={"placeholder": "contact@organization.com"})
    )
    coupons = forms.ChoiceField(
        choices=(
            ("Yes", "Yes"),
            ("Maybe", "Maybe"),
            ("No", "No")
        ),
        initial='Yes',
        label='Are you able to contribute promotional offers?'
    )
    expectations = forms.CharField(
        widget=forms.Textarea(
            attrs={"placeholder": "What are you hoping to gain from this partnership?",
                   "style": "height: 6em;"})
    )
