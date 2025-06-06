from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import StudySession

class StudySessionForm(forms.ModelForm):
    class Meta:
        model = StudySession
        fields = ['subject', 'description', 'study_date', 'start_time', 'end_time', 'status', 'sync_to_google', 
                 'notification_enabled', 'reminder_minutes', 'notification_message']
        widgets = {
            'study_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'start_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'end_time': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'sync_to_google': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notification_enabled': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reminder_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '1440', 'value': '30'}),
            'notification_message': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Leave blank for default message'}),
        }

class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user
