"""
Models para Clientes
"""
from django.db import models


class Cliente(models.Model):
    """
    Model de Cliente
    """
    
    TIPO_CHOICES = [
        ('fisica', 'Pessoa Física'),
        ('juridica', 'Pessoa Jurídica'),
    ]
    
    CATEGORIA_CHOICES = [
        ('cliente', 'Cliente'),
        ('fornecedor', 'Fornecedor'),
        ('ambos', 'Ambos'),
    ]
    
    # Identificação
    tipo = models.CharField('Tipo', max_length=10, choices=TIPO_CHOICES, default='fisica')
    categoria = models.CharField('Categoria', max_length=15, choices=CATEGORIA_CHOICES, default='cliente')
    nome = models.CharField('Nome', max_length=200)
    cpf_cnpj = models.CharField('CPF/CNPJ', max_length=18, unique=True, null=True, blank=True)
    rg_ie = models.CharField('RG/IE', max_length=20, blank=True)
    
    # Contato
    telefone = models.CharField('Telefone', max_length=20)
    email = models.EmailField('E-mail', blank=True)
    
    # Endereço
    cep = models.CharField('CEP', max_length=10, blank=True)
    endereco = models.CharField('Endereço', max_length=200, blank=True)
    numero = models.CharField('Número', max_length=10, blank=True)
    complemento = models.CharField('Complemento', max_length=100, blank=True)
    bairro = models.CharField('Bairro', max_length=100, blank=True)
    cidade = models.CharField('Cidade', max_length=100, blank=True)
    estado = models.CharField('Estado', max_length=2, blank=True)
    
    # Observações
    observacoes = models.TextField('Observações', blank=True)
    
    ativo = models.BooleanField('Ativo', default=True)
    atividade_fornecedor = models.CharField(
        'Atividade do Fornecedor', 
        max_length=150, 
        blank=True, 
        help_text='Ex: Mecânica, Ar Condicionado, Material de Pintura'
    )
    
    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Cliente'
        verbose_name_plural = 'Clientes'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome

