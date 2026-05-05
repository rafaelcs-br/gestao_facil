from django.urls import path
from .views import (
    TransacaoListView,
    TransacaoCreateView,
    TransacaoDetailView,
    TransacaoUpdateView,
    TransacaoDeleteView,
    toggle_status,
)

urlpatterns = [
    path('', TransacaoListView.as_view(), name='transacao-list'),
    path('criar/', TransacaoCreateView.as_view(), name='transacao-create'),
    path('status/<int:pk>/toggle/', toggle_status, name='transacao-toggle-status'),
    path('<int:pk>/', TransacaoDetailView.as_view(), name='transacao-detail'),
    path('<int:pk>/editar/', TransacaoUpdateView.as_view(), name='transacao-update'),
    path('<int:pk>/deletar/', TransacaoDeleteView.as_view(), name='transacao-delete'),
]