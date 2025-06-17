"""excel_uploader URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from uploader.views import *
from uploader.apis import *


urlpatterns = [
    #url
    path('admin/', admin.site.urls),
    path('upload-excel/', upload_excel, name='upload-excel'),
    path('', upload_docx, name='upload-docx'),
    path('data-visualization/', upload_csv, name='data-visualization'),
    path('titanic/', titanic_view, name='titanic'),
    path('eda/heatmap/', heatmap_view, name='eda-heatmap'),
    path('eda/scatter-plots/', scatter_plots_view, name='eda-scatter-plots'),
    path('eda/linegraphs/', eda_line_graphs, name='eda-line-graphs'),
    path('eda/boxplots/', eda_box_plots, name='eda-box-plots'),
    path('eda/pairplot/', eda_pair_plot, name='eda-pair-plot'),


    #api
    path('api/upload-excel/', UploadExcelView.as_view(), name='upload-excel-api'),
    path('api/persons/', PersonListView.as_view(), name='person-list'),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
