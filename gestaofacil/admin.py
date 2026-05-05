from django.contrib import admin
from .models import Transacao, Investimento

@admin.register(Transacao)
class TransacaoAdmin(admin.ModelAdmin):
    list_display = ('rotulo', 'valor', 'tipo', 'status', 'data')
    list_filter = ('tipo', 'status', 'data')
    search_fields = ('rotulo',)
    date_hierarchy = 'data'
    readonly_fields = ('criada_em', 'atualizada_em')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('rotulo', 'valor')
        }),
        ('Detalhes', {
            'fields': ('data', 'tipo', 'status')
        }),
        ('Timestamps', {
            'fields': ('criada_em', 'atualizada_em'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Investimento)
class InvestimentoAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'valor', 'tipo', 'cotas', 'data_aplicacao')
    list_filter = ('tipo', 'data_aplicacao')
    search_fields = ('descricao',)
    date_hierarchy = 'data_aplicacao'
    readonly_fields = ('criada_em', 'atualizada_em')
    fieldsets = (
        ('Informações Básicas', {
            'fields': ('descricao', 'valor')
        }),
        ('Detalhes', {
            'fields': ('data_aplicacao', 'tipo', 'cotas')
        }),
        ('Timestamps', {
            'fields': ('criada_em', 'atualizada_em'),
            'classes': ('collapse',)
        }),
    )
