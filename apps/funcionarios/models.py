"""
Models para Funcionários
"""
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.utils import OperationalError, ProgrammingError
from django.dispatch import receiver


class Funcionario(AbstractUser):
    """
    Model customizado de usuário/funcionário
    Estende AbstractUser para adicionar campos específicos
    """
    
    PERFIL_CHOICES = [
        ('operacional', 'Operacional'),
        ('visual', 'Visual'),
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
    deve_mudar_senha = models.BooleanField('Deve Mudar Senha', default=True)
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


class LogAcesso(models.Model):
    EVENTO_CHOICES = [
        ('login', 'Login'),
        ('logout', 'Logout'),
    ]

    usuario = models.ForeignKey(
        'funcionarios.Funcionario',
        on_delete=models.CASCADE,
        related_name='logs_acesso',
        verbose_name='Usuário',
    )
    evento = models.CharField('Evento', max_length=10, choices=EVENTO_CHOICES)
    ip = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.CharField('User-Agent', max_length=500, blank=True)
    caminho = models.CharField('Caminho', max_length=255, blank=True)
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)

    class Meta:
        verbose_name = 'Log de Acesso'
        verbose_name_plural = 'Logs de Acesso'
        ordering = ['-criado_em']

    def __str__(self):
        return f'{self.usuario} - {self.evento} - {self.criado_em:%d/%m/%Y %H:%M}'


def _ip_do_request(request):
    if not request:
        return None
    xff = (request.META.get('HTTP_X_FORWARDED_FOR') or '').strip()
    if xff:
        return xff.split(',')[0].strip()[:45] or None
    ip = (request.META.get('REMOTE_ADDR') or '').strip()
    return ip[:45] or None


@receiver(user_logged_in)
def registrar_login(sender, request, user, **kwargs):
    if not user or not getattr(user, 'pk', None):
        return
    try:
        LogAcesso.objects.create(
            usuario=user,
            evento='login',
            ip=_ip_do_request(request),
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500] if request else '',
            caminho=(getattr(request, 'path', '') or '')[:255] if request else '',
        )
    except (OperationalError, ProgrammingError):
        return


@receiver(user_logged_out)
def registrar_logout(sender, request, user, **kwargs):
    if not user or not getattr(user, 'pk', None):
        return
    try:
        LogAcesso.objects.create(
            usuario=user,
            evento='logout',
            ip=_ip_do_request(request),
            user_agent=(request.META.get('HTTP_USER_AGENT') or '')[:500] if request else '',
            caminho=(getattr(request, 'path', '') or '')[:255] if request else '',
        )
    except (OperationalError, ProgrammingError):
        return
