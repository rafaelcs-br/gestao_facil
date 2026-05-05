import json

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Min
from django.utils import timezone
from datetime import timedelta
from .models import Transacao, Investimento
from django import forms

class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ['rotulo', 'valor', 'data', 'tipo', 'status']
        widgets = {
            'rotulo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite a descrição da transação'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'data': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'status': forms.Select(attrs={
                'class': 'form-select'
            }),
        }


class TransacaoListView(ListView):
    model = Transacao
    template_name = 'gestaofacil/transacao_list.html'
    context_object_name = 'transacoes'
    paginate_by = 10
    
    def get_queryset(self):
        queryset = Transacao.objects.all()
        
        today = timezone.localdate()
        ano = self.request.GET.get('ano')
        mes = self.request.GET.get('mes')
        if not ano:
            ano = str(today.year)
        if not mes:
            mes = str(today.month)
        
        try:
            ano_int = int(ano)
        except (TypeError, ValueError):
            ano_int = today.year
        try:
            mes_int = int(mes)
        except (TypeError, ValueError):
            mes_int = today.month
        
        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        
        queryset = queryset.filter(data__year=ano_int, data__month=mes_int)
        
        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(Q(rotulo__icontains=busca))
        
        self.selected_year = ano_int
        self.selected_month = mes_int
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        today = timezone.localdate()
        selected_year = getattr(self, 'selected_year', today.year)
        selected_month = getattr(self, 'selected_month', today.month)
        
        transacoes = Transacao.objects.all()
        receitas = transacoes.filter(tipo='receita').aggregate(Sum('valor'))['valor__sum'] or 0
        despesas = transacoes.filter(tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or 0
        saldo = receitas - despesas
        
        percent_despesas = (despesas / receitas) * 100 if receitas else 0
        percent_saldo = (saldo / receitas) * 100 if receitas else 0
        
        context['receitas_total'] = receitas
        context['despesas_total'] = despesas
        context['saldo'] = saldo
        context['percent_despesas'] = round(percent_despesas, 1)
        context['percent_saldo'] = round(percent_saldo, 1)
        
        context['tipo_filtro'] = self.request.GET.get('tipo', '')
        context['status_filtro'] = self.request.GET.get('status', '')
        context['busca'] = self.request.GET.get('busca', '')
        context['selected_year'] = selected_year
        context['selected_month'] = selected_month
        
        min_data = transacoes.aggregate(min_data=Min('data'))['min_data']
        if min_data:
            start_year = min_data.year
        else:
            start_year = today.year
        context['year_options'] = list(range(today.year, start_year - 1, -1))
        month_labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        context['month_options'] = [
            {'value': i + 1, 'label': month_labels[i]} for i in range(12)
        ]
        
        chart_year = selected_year
        receitas_por_mes = [0] * 12
        despesas_por_mes = [0] * 12
        for item in transacoes.filter(data__year=chart_year, tipo='receita').values('data__month').annotate(total=Sum('valor')):
            receitas_por_mes[item['data__month'] - 1] = float(item['total'] or 0)
        for item in transacoes.filter(data__year=chart_year, tipo='despesa').values('data__month').annotate(total=Sum('valor')):
            despesas_por_mes[item['data__month'] - 1] = float(item['total'] or 0)
        
        context['chart_labels'] = month_labels
        context['chart_receitas'] = json.dumps(receitas_por_mes)
        context['chart_despesas'] = json.dumps(despesas_por_mes)
        context['chart_year'] = chart_year
        
        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['querystring'] = query_params.urlencode()
        
        return context


def toggle_status(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk)
    transacao.status = 'pago' if transacao.status == 'pendente' else 'pendente'
    transacao.save()
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('transacao-list')
    return redirect(next_url)


class TransacaoCreateView(CreateView):
    model = Transacao
    form_class = TransacaoForm
    template_name = 'gestaofacil/transacao_form.html'
    success_url = reverse_lazy('transacao-list')


class TransacaoDetailView(DetailView):
    model = Transacao
    template_name = 'gestaofacil/transacao_detail.html'
    context_object_name = 'transacao'


class TransacaoUpdateView(UpdateView):
    model = Transacao
    form_class = TransacaoForm
    template_name = 'gestaofacil/transacao_form.html'
    success_url = reverse_lazy('transacao-list')


class TransacaoDeleteView(DeleteView):
    model = Transacao
    template_name = 'gestaofacil/transacao_confirm_delete.html'
    success_url = reverse_lazy('transacao-list')


class InvestimentoForm(forms.ModelForm):
    class Meta:
        model = Investimento
        fields = ['descricao', 'valor', 'data_aplicacao', 'tipo', 'cotas']
        widgets = {
            'descricao': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Digite a descrição do investimento'
            }),
            'valor': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'data_aplicacao': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-select'
            }),
            'cotas': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de cotas'
            }),
        }

    def clean(self):
        cleaned_data = super().clean()
        tipo = cleaned_data.get('tipo')
        cotas = cleaned_data.get('cotas')

        if tipo == 'renda_variavel' and not cotas:
            self.add_error('cotas', 'O número de cotas é obrigatório para renda variável.')

        if tipo == 'renda_fixa':
            cleaned_data['cotas'] = None

        return cleaned_data


class InvestimentoListView(ListView):
    model = Investimento
    template_name = 'gestaofacil/investimento_list.html'
    context_object_name = 'investimentos'
    paginate_by = 10

    def get_queryset(self):
        queryset = Investimento.objects.all()
        today = timezone.localdate()
        ano = self.request.GET.get('ano')
        mes = self.request.GET.get('mes')
        if not ano:
            ano = str(today.year)
        if not mes:
            mes = str(today.month)

        try:
            ano_int = int(ano)
        except (TypeError, ValueError):
            ano_int = today.year
        try:
            mes_int = int(mes)
        except (TypeError, ValueError):
            mes_int = today.month

        tipo = self.request.GET.get('tipo')
        if tipo:
            queryset = queryset.filter(tipo=tipo)

        busca = self.request.GET.get('busca')
        if busca:
            queryset = queryset.filter(descricao__icontains=busca)

        queryset = queryset.filter(data_aplicacao__year=ano_int, data_aplicacao__month=mes_int)
        self.selected_year = ano_int
        self.selected_month = mes_int
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        today = timezone.localdate()
        selected_year = getattr(self, 'selected_year', today.year)
        selected_month = getattr(self, 'selected_month', today.month)

        investimentos = Investimento.objects.all()

        latest_renda_fixa = {}
        for investimento in Investimento.objects.filter(tipo='renda_fixa').order_by('descricao', '-data_aplicacao', '-pk'):
            if investimento.descricao not in latest_renda_fixa:
                latest_renda_fixa[investimento.descricao] = investimento

        latest_renda_variavel = {}
        for investimento in Investimento.objects.filter(tipo='renda_variavel').order_by('descricao', '-data_aplicacao', '-pk'):
            if investimento.descricao not in latest_renda_variavel:
                latest_renda_variavel[investimento.descricao] = investimento

        total_renda_fixa = sum(inv.valor for inv in latest_renda_fixa.values())
        total_renda_variavel = sum(inv.valor for inv in latest_renda_variavel.values())

        context['total_investido'] = total_renda_fixa + total_renda_variavel
        context['total_renda_fixa'] = total_renda_fixa
        context['total_renda_variavel'] = total_renda_variavel
        context['tipo_filtro'] = self.request.GET.get('tipo', '')
        context['busca'] = self.request.GET.get('busca', '')
        context['selected_year'] = selected_year
        context['selected_month'] = selected_month

        min_data = investimentos.aggregate(min_data=Min('data_aplicacao'))['min_data']
        if min_data:
            start_year = min_data.year
        else:
            start_year = today.year
        context['year_options'] = list(range(today.year, start_year - 1, -1))
        month_labels = ['Jan', 'Fev', 'Mar', 'Abr', 'Mai', 'Jun', 'Jul', 'Ago', 'Set', 'Out', 'Nov', 'Dez']
        context['month_options'] = [
            {'value': i + 1, 'label': month_labels[i]} for i in range(12)
        ]

        chart_year = selected_year
        renda_fixa_por_mes = [0] * 12
        renda_variavel_por_mes = [0] * 12

        for item in investimentos.filter(data_aplicacao__year=chart_year, tipo='renda_fixa').values('data_aplicacao__month').annotate(total=Sum('valor')):
            renda_fixa_por_mes[item['data_aplicacao__month'] - 1] = float(item['total'] or 0)
        for item in investimentos.filter(data_aplicacao__year=chart_year, tipo='renda_variavel').values('data_aplicacao__month').annotate(total=Sum('valor')):
            renda_variavel_por_mes[item['data_aplicacao__month'] - 1] = float(item['total'] or 0)

        context['chart_labels'] = month_labels
        context['chart_renda_fixa'] = json.dumps(renda_fixa_por_mes)
        context['chart_renda_variavel'] = json.dumps(renda_variavel_por_mes)
        context['chart_year'] = chart_year

        query_params = self.request.GET.copy()
        query_params.pop('page', None)
        context['querystring'] = query_params.urlencode()

        return context


class InvestimentoCreateView(CreateView):
    model = Investimento
    form_class = InvestimentoForm
    template_name = 'gestaofacil/investimento_form.html'
    success_url = reverse_lazy('investimento-list')


class InvestimentoDetailView(DetailView):
    model = Investimento
    template_name = 'gestaofacil/investimento_detail.html'
    context_object_name = 'investimento'


class InvestimentoUpdateView(UpdateView):
    model = Investimento
    form_class = InvestimentoForm
    template_name = 'gestaofacil/investimento_form.html'
    success_url = reverse_lazy('investimento-list')


class InvestimentoDeleteView(DeleteView):
    model = Investimento
    template_name = 'gestaofacil/investimento_confirm_delete.html'
    success_url = reverse_lazy('investimento-list')
