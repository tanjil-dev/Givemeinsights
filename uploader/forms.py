from django import forms

class UploadFileForm(forms.Form):
    file = forms.FileField()

class DocumentUploadForm(forms.Form):
    file = forms.FileField(label="Upload a .docx file")