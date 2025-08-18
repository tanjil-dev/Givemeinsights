from django.urls import path
from .views import *
from .apis import *

urlpatterns = [
    path('word-analysis/word-cloud/', upload_docx, name='word_cloud'),
    path('word-analysis/phrases-used/', phrases_used_view, name='phrases_used'),
    path('word-analysis/labels/', labels_view, name='labels'),
    path('eda/', heatmap_view, name='eda'),
    path('eda/scatter-plots/', scatter_plots_view, name='eda-scatter-plots'),
    path('eda/linegraphs/', eda_line_graphs, name='eda-line-graphs'),
    path('eda/boxplots/', eda_box_plots, name='eda-box-plots'),
    path('eda/pairplot/', eda_pair_plot, name='eda-pair-plot'),
    path('eda/linear-regression/', linear_regression, name='linear-regression'),
    path('eda/profile-report/', generate_profile_report, name='profile-report'),

    path('robots.txt', RobotsTxtView.as_view(), name='robots.txt'),
    path('sitemap.xml', SitemapXmlView.as_view(), name='sitemap.xml'),
]
