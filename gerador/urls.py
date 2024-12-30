from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),  # Esta é a URL para a página inicial do app
    path('exportar/', views.exportar_para_planilha, name='exportar'),
    path('exportar_visiveis/', views.exportar_visiveis, name='exportar_visiveis'),
    path('limpar_historico/', views.limpar_historico, name='limpar_historico'),
    

]
