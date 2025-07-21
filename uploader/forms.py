from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()

class DocumentUploadForm(forms.Form):
    file = forms.FileField(label="Upload a .docx file")

class ContactForm(forms.Form):
    name = forms.CharField(max_length=100, required=True)
    email = forms.EmailField(required=True)
    phone = forms.CharField(max_length=15, required=False)
    subject = forms.CharField(max_length=100, required=False)
    message = forms.CharField(widget=forms.Textarea, required=True)