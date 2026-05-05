from django.contrib import admin
from .models import Transacao

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
