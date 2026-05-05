import json
import csv
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy, reverse
from django.db.models import Q, Sum, Min
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponse
from .models import Transacao, Investimento, Tag
from django import forms

class TransacaoForm(forms.ModelForm):
    class Meta:
        model = Transacao
        fields = ['rotulo', 'valor', 'data', 'tipo', 'status', 'tag']
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
            'tag': forms.Select(attrs={
                'class': 'form-select'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar apenas tags ativas
        self.fields['tag'].queryset = Tag.objects.filter(ativa=True)
        # Tornar tag opcional por padrão
        self.fields['tag'].required = False


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
        
        # Filtrar transações pelo mês/ano selecionado
        transacoes_filtradas = Transacao.objects.filter(
            data__year=selected_year, 
            data__month=selected_month
        )
        receitas = transacoes_filtradas.filter(tipo='receita').aggregate(Sum('valor'))['valor__sum'] or 0
        despesas = transacoes_filtradas.filter(tipo='despesa').aggregate(Sum('valor'))['valor__sum'] or 0
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
        
        # Para os year_options, usar todas as transações
        transacoes = Transacao.objects.all()
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
        
        # Estatísticas por tag/categoria (apenas despesas do mês/ano selecionado)
        despesas_por_tag = transacoes_filtradas.filter(tipo='despesa').values('tag__nome', 'tag__cor').annotate(
            total=Sum('valor')
        ).filter(total__gt=0).order_by('-total')
        
        context['despesas_por_tag'] = list(despesas_por_tag)
        context['tags_labels'] = json.dumps([item['tag__nome'] or 'Sem Categoria' for item in despesas_por_tag])
        context['tags_valores'] = json.dumps([float(item['total']) for item in despesas_por_tag])
        context['tags_cores'] = json.dumps([item['tag__cor'] or '#6c757d' for item in despesas_por_tag])
        
        return context


def toggle_status(request, pk):
    transacao = get_object_or_404(Transacao, pk=pk)
    transacao.status = 'pago' if transacao.status == 'pendente' else 'pendente'
    transacao.save()
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or reverse('transacao-list')
    return redirect(next_url)


def export_transacoes_csv(request):
    """Exporta transações filtradas para CSV"""
    today = timezone.localdate()
    ano = request.GET.get('ano')
    mes = request.GET.get('mes')
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    busca = request.GET.get('busca')

    # Definir valores padrão como na view principal
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

    # Aplicar filtros
    queryset = Transacao.objects.all()

    # Filtrar por ano e mês (sempre aplicados)
    queryset = queryset.filter(data__year=ano_int, data__month=mes_int)

    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if status:
        queryset = queryset.filter(status=status)
    if busca:
        queryset = queryset.filter(rotulo__icontains=busca)

    # Ordenar por data
    queryset = queryset.order_by('data')

    # Criar resposta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="transacoes.csv"'

    writer = csv.writer(response)
    writer.writerow(['Data', 'Descrição', 'Tipo', 'Valor', 'Status'])

    for transacao in queryset:
        writer.writerow([
            transacao.data.strftime('%d/%m/%Y'),
            transacao.rotulo,
            transacao.get_tipo_display(),
            f"R$ {transacao.valor:.2f}",
            transacao.get_status_display()
        ])

    return response


def export_transacoes_pdf(request):
    """Exporta transações filtradas para PDF"""
    today = timezone.localdate()
    ano = request.GET.get('ano')
    mes = request.GET.get('mes')
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    busca = request.GET.get('busca')

    # Definir valores padrão como na view principal
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

    # Aplicar filtros
    queryset = Transacao.objects.all()

    # Filtrar por ano e mês (sempre aplicados)
    queryset = queryset.filter(data__year=ano_int, data__month=mes_int)

    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if status:
        queryset = queryset.filter(status=status)
    if busca:
        queryset = queryset.filter(rotulo__icontains=busca)

    # Ordenar por data
    queryset = queryset.order_by('data')

    # Criar buffer para PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
    )

    # Título
    periodo = ""
    if ano and mes:
        periodo = f" - {mes}/{ano}"
    elif ano:
        periodo = f" - {ano}"
    elif mes:
        periodo = f" - Mês {mes}"

    title = Paragraph(f"Relatório de Transações{periodo}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Dados da tabela
    data = [['Data', 'Descrição', 'Tipo', 'Valor', 'Status']]

    for transacao in queryset:
        data.append([
            transacao.data.strftime('%d/%m/%Y'),
            transacao.rotulo,
            transacao.get_tipo_display(),
            f"R$ {transacao.valor:.2f}",
            transacao.get_status_display()
        ])

    # Criar tabela
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)

    # Criar resposta
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="transacoes.pdf"'

    return response


def export_transacoes_csv_ano(request):
    """Exporta transações do ano inteiro selecionado para CSV"""
    today = timezone.localdate()
    ano = request.GET.get('ano')
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    busca = request.GET.get('busca')

    # Definir valor padrão para ano
    if not ano:
        ano = str(today.year)

    try:
        ano_int = int(ano)
    except (TypeError, ValueError):
        ano_int = today.year

    # Aplicar filtros
    queryset = Transacao.objects.all()

    # Filtrar apenas por ano (ano inteiro)
    queryset = queryset.filter(data__year=ano_int)

    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if status:
        queryset = queryset.filter(status=status)
    if busca:
        queryset = queryset.filter(rotulo__icontains=busca)

    # Ordenar por data
    queryset = queryset.order_by('data')

    # Criar resposta CSV
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="transacoes_{ano_int}.csv"'

    writer = csv.writer(response)
    writer.writerow(['Data', 'Descrição', 'Tipo', 'Valor', 'Status'])

    for transacao in queryset:
        writer.writerow([
            transacao.data.strftime('%d/%m/%Y'),
            transacao.rotulo,
            transacao.get_tipo_display(),
            f"R$ {transacao.valor:.2f}",
            transacao.get_status_display()
        ])

    return response


def export_transacoes_pdf_ano(request):
    """Exporta transações do ano inteiro selecionado para PDF"""
    today = timezone.localdate()
    ano = request.GET.get('ano')
    tipo = request.GET.get('tipo')
    status = request.GET.get('status')
    busca = request.GET.get('busca')

    # Definir valor padrão para ano
    if not ano:
        ano = str(today.year)

    try:
        ano_int = int(ano)
    except (TypeError, ValueError):
        ano_int = today.year

    # Aplicar filtros
    queryset = Transacao.objects.all()

    # Filtrar apenas por ano (ano inteiro)
    queryset = queryset.filter(data__year=ano_int)

    if tipo:
        queryset = queryset.filter(tipo=tipo)
    if status:
        queryset = queryset.filter(status=status)
    if busca:
        queryset = queryset.filter(rotulo__icontains=busca)

    # Ordenar por data
    queryset = queryset.order_by('data')

    # Criar buffer para PDF
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=30,
    )

    # Título
    title = Paragraph(f"Relatório de Transações - Ano {ano_int}", title_style)
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Dados da tabela
    data = [['Data', 'Descrição', 'Tipo', 'Valor', 'Status']]

    for transacao in queryset:
        data.append([
            transacao.data.strftime('%d/%m/%Y'),
            transacao.rotulo,
            transacao.get_tipo_display(),
            f"R$ {transacao.valor:.2f}",
            transacao.get_status_display()
        ])

    # Criar tabela
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 12),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))

    elements.append(table)

    # Gerar PDF
    doc.build(elements)
    buffer.seek(0)

    # Criar resposta
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="transacoes_{ano_int}.pdf"'

    return response


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
