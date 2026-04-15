"""
Models para Funcionários
"""
from django.db import models
from django.contrib.auth.models import AbstractUser


class Funcionario(AbstractUser):
    """
    Model customizado de usuário/funcionário
    Estende AbstractUser para adicionar campos específicos
    """
    
    PERFIL_CHOICES = [
        ('operacional', 'Operacional'),
        ('supervisor', 'Supervisor'),
        ('gerente', 'Gerente'),
        ('admin', 'Administrador'),
        ('orcamentista', 'Orçamentista'),
        ('financeiro', 'Financeiro'),
    ]
    
    # Campos básicos
    telefone = models.CharField('Telefone', max_length=20, blank=True)
    cpf = models.CharField('CPF', max_length=14, unique=True, null=True, blank=True)
    data_admissao = models.DateField('Data de Admissão', null=True, blank=True)
    data_demissao = models.DateField('Data de Demissão', null=True, blank=True)
    
    # Perfil e permissões
    perfil = models.CharField(
        'Perfil',
        max_length=20,
        choices=PERFIL_CHOICES,
        default='operacional'
    )
    
    # Comissão
    percentual_comissao_padrao = models.DecimalField(
        'Percentual de Comissão Padrão (%)',
        max_digits=5,
        decimal_places=2,
        default=10.00,
        help_text='Percentual padrão usado quando a etapa não define um percentual específico'
    )
    
    # Status
    ativo = models.BooleanField('Ativo', default=True)
    foto = models.ImageField('Foto', upload_to='funcionarios/fotos/', null=True, blank=True)
    
    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['first_name', 'last_name']

    def save(self, *args, **kwargs):
        """Sobrescreve save para garantir capitalização"""
        if self.username:
            self.username = self.username.capitalize()
        if self.first_name:
            self.first_name = self.first_name.capitalize()
        if self.last_name:
            self.last_name = self.last_name.capitalize()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_perfil_display()})"
    
    @property
    def nome_completo(self):
        """Retorna nome completo do funcionário"""
        return self.get_full_name() or self.username
    
    @property
    def pode_programar_tarefas(self):
        """Verifica se pode programar tarefas (supervisor ou acima)"""
        return self.perfil in ['supervisor', 'gerente', 'admin']
    
    @property
    def pode_aprovar_comissoes(self):
        """Verifica se pode aprovar comissões"""
        return self.perfil in ['supervisor', 'gerente', 'admin']
    
    @property
    def pode_criar_orcamentos(self):
        """Verifica se pode criar orçamentos"""
        return self.perfil in ['gerente', 'admin', 'orcamentista']

