from django.db import models
from django.utils.functional import cached_property

class Tag(models.Model):
    nome = models.CharField(
        max_length=50,
        unique=True,
        verbose_name='Nome da Tag',
        help_text='Nome da categoria/tag para despesas'
    )
    cor = models.CharField(
        max_length=7,
        default='#6c757d',
        verbose_name='Cor',
        help_text='Cor hexadecimal para identificação visual'
    )
    descricao = models.TextField(
        blank=True,
        verbose_name='Descrição',
        help_text='Descrição opcional da categoria'
    )
    ativa = models.BooleanField(
        default=True,
        verbose_name='Ativa',
        help_text='Se a tag está ativa para uso'
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tag'
        verbose_name_plural = 'Tags'
        ordering = ['nome']

    def __str__(self):
        return self.nome


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
    tag = models.ForeignKey(
        Tag,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Tag/Categoria',
        help_text='Categoria da despesa (apenas para despesas)'
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Transação'
        verbose_name_plural = 'Transações'
        ordering = ['-data']
    
    def __str__(self):
        return f'{self.rotulo} - R$ {self.valor:.2f} ({self.get_tipo_display()})'


class Investimento(models.Model):
    TIPO_INVESTIMENTO_CHOICES = [
        ('renda_fixa', 'Renda Fixa'),
        ('renda_variavel', 'Renda Variável'),
    ]

    descricao = models.CharField(
        max_length=255,
        verbose_name='Descrição',
        help_text='Breve descrição do investimento'
    )
    valor = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Valor'
    )
    data_aplicacao = models.DateField(
        verbose_name='Data de aplicação',
        auto_now_add=False
    )
    tipo = models.CharField(
        max_length=15,
        choices=TIPO_INVESTIMENTO_CHOICES,
        verbose_name='Tipo'
    )
    cotas = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name='Número de cotas',
        help_text='Informe somente para investimentos em renda variável'
    )
    criada_em = models.DateTimeField(auto_now_add=True)
    atualizada_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Investimento'
        verbose_name_plural = 'Investimentos'
        ordering = ['-data_aplicacao']

    def __str__(self):
        return f'{self.descricao} - R$ {self.valor:.2f} ({self.get_tipo_display()})'

    @cached_property
    def previous_investimento(self):
        return Investimento.objects.filter(
            descricao=self.descricao,
            data_aplicacao__lt=self.data_aplicacao
        ).order_by('-data_aplicacao').first()

    @property
    def diferencial(self):
        previous = self.previous_investimento
        if previous is None:
            return None
        return self.valor - previous.valor
