from django.urls import path
from .views import (
    TransacaoListView,
    TransacaoCreateView,
    TransacaoDetailView,
    TransacaoUpdateView,
    TransacaoDeleteView,
    InvestimentoListView,
    InvestimentoCreateView,
    InvestimentoDetailView,
    InvestimentoUpdateView,
    InvestimentoDeleteView,
    toggle_status,
)

urlpatterns = [
    path('', TransacaoListView.as_view(), name='transacao-list'),
    path('criar/', TransacaoCreateView.as_view(), name='transacao-create'),
    path('status/<int:pk>/toggle/', toggle_status, name='transacao-toggle-status'),
    path('<int:pk>/', TransacaoDetailView.as_view(), name='transacao-detail'),
    path('<int:pk>/editar/', TransacaoUpdateView.as_view(), name='transacao-update'),
    path('<int:pk>/deletar/', TransacaoDeleteView.as_view(), name='transacao-delete'),
    path('investimentos/', InvestimentoListView.as_view(), name='investimento-list'),
    path('investimentos/criar/', InvestimentoCreateView.as_view(), name='investimento-create'),
    path('investimentos/<int:pk>/', InvestimentoDetailView.as_view(), name='investimento-detail'),
    path('investimentos/<int:pk>/editar/', InvestimentoUpdateView.as_view(), name='investimento-update'),
    path('investimentos/<int:pk>/deletar/', InvestimentoDeleteView.as_view(), name='investimento-delete'),
]