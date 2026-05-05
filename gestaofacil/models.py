from django.db import models

class Transacao(models.Model):
    TIPO_CHOICES = [
        ('receita', 'Receita'),
        ('despesa', 'Despesa'),
    ]
    
    STATUS_CHOICES = [
        ('pago', 'Pago'),
        ('pendente', 'Pendente'),
    ]
    
    rotulo = models.CharField(
        max_length=255,
        verbose_name='Rótulo',
        help_text='Descrição da transação'
    )
    valor = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Valor'
    )
    data = models.DateField(
        verbose_name='Data',
        auto_now_add=False
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_CHOICES,
        verbose_name='Tipo'
    )
    status = models.CharField(
        max_length=10,
        choices=STATUS_CHOICES,
        default='pendente',
        verbose_name='Status'
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'
        ordering = ['-data']
    
    def __str__(self):
        return f'{self.rotulo} - R$ {self.valor:.2f} ({self.get_tipo_display()})'
