import pandas as pd
from django.shortcuts import render
from django.http import HttpResponse
from .forms import UploadFileForm
from .models import Person

def upload_excel(request):
    form = UploadFileForm()
    return render(request, 'upload_excel.html', {'form': form})