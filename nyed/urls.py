from django.urls import path

from . import views

app_name = 'nyed'
urlpatterns = [
    # ex: localhost:8080/ or pythonanywere.com/
    # By default, display "Academic Assessment Data Search Page" page    
    path('', views.home, name='home'),

    # ex: localhost:8080/correlation_index/ for correlation search page
    path('assessment_index/', views.base_assessment, name='base_assessment'),
    path('correlation_index/', views.base_correlation, name='base_correlation'),

    # ex: localhost:8080/assessment_data/  for search result page
    path('assessment_data/', views.assessment_data, name='assessment_data'),
    path('correlation_data/', views.correlation_data, name='correlation_data'),
    
    path('about/', views.about, name='about'),        
]