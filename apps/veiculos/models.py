"""
Models para Veículos
"""
import re
from django.db import models
from django.core.validators import MinLengthValidator, RegexValidator

# Importar depois para evitar importação circular
__all__ = ['Veiculo', 'Fabricante', 'ModeloVeiculo']


class Veiculo(models.Model):
    """
    Model de Veículo
    """

    # Relacionamentos
    cliente = models.ForeignKey(
        'clientes.Cliente',
        on_delete=models.PROTECT,
        related_name='veiculos',
        verbose_name='Cliente'
    )

    modelo_veiculo = models.ForeignKey(
        'veiculos.ModeloVeiculo',
        on_delete=models.PROTECT,
        related_name='veiculos',
        verbose_name='Modelo',
        null=True,
        blank=True
    )

    # Campos antigos mantidos para compatibilidade (opcional)
    marca = models.CharField('Marca (legado)', max_length=50, blank=True)
    modelo = models.CharField('Modelo (legado)', max_length=50, blank=True)

    # Cor
    cor_veiculo = models.ForeignKey(
        'veiculos.CorVeiculo',
        on_delete=models.PROTECT,
        related_name='veiculos',
        verbose_name='Cor',
        null=True,
        blank=True
    )
    cor = models.CharField('Cor (legado)', max_length=30, blank=True)

    # Identificação do veículo
    placa = models.CharField(
        'Placa', 
        max_length=7, 
        unique=True,
        validators=[
            MinLengthValidator(7),
            RegexValidator(
                regex=r'^[A-Z0-9]{7}$',
                message="A placa deve ter exatamente 7 caracteres alfanuméricos."
            )
        ]
    )
    ano_fabricacao = models.IntegerField('Ano de Fabricação', null=True, blank=True)
    ano_modelo = models.IntegerField('Ano do Modelo', null=True, blank=True)
    chassi = models.CharField('Chassi', max_length=50, unique=True, null=True, blank=True)
    renavam = models.CharField('Renavam', max_length=20, blank=True)

    # Quilometragem
    km_atual = models.IntegerField('KM Atual', null=True, blank=True)

    # Fotos do veículo
    foto_principal = models.ImageField(
        'Foto Principal',
        upload_to='veiculos/fotos/',
        null=True,
        blank=True,
        help_text='Foto principal do veículo (frente, lateral, etc.)'
    )
    foto_2 = models.ImageField('Foto 2', upload_to='veiculos/fotos/', null=True, blank=True)
    foto_3 = models.ImageField('Foto 3', upload_to='veiculos/fotos/', null=True, blank=True)
    foto_4 = models.ImageField('Foto 4', upload_to='veiculos/fotos/', null=True, blank=True)

    # Observações
    observacoes = models.TextField('Observações', blank=True)

    # Timestamps
    criado_em = models.DateTimeField('Criado em', auto_now_add=True)
    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Veículo'
        verbose_name_plural = 'Veículos'
        ordering = ['placa']

    def save(self, *args, **kwargs):
        """Sobrescreve save para formatar campos"""
        # Placa sempre MAIÚSCULA e limpa (sem hífens)
        if self.placa:
            self.placa = re.sub(r'[^A-Za-z0-9]', '', self.placa).upper()

        # Chassi sempre MAIÚSCULO
        if self.chassi:
            self.chassi = self.chassi.upper()

        super().save(*args, **kwargs)

    def __str__(self):
        if self.modelo_veiculo:
            return f"{self.modelo_veiculo} - {self.placa}"
        return f"{self.marca} {self.modelo} - {self.placa}"

    @property
    def descricao_completa(self):
        """Retorna descrição completa do veículo"""
        if self.modelo_veiculo:
            cor_display = self.cor_veiculo.nome if self.cor_veiculo else self.cor
            return f"{self.modelo_veiculo.fabricante.nome} {self.modelo_veiculo.nome} {cor_display} - {self.placa}"
        return f"{self.marca} {self.modelo} - {self.placa}"

    @property
    def cor_display(self):
        """Retorna nome da cor"""
        return self.cor_veiculo.nome if self.cor_veiculo else self.cor

