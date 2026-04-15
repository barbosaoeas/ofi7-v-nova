"""
Models para Fabricantes, Modelos e Cores de Veículos
"""
from django.db import models


class CorVeiculo(models.Model):
    """Cores de veículos"""

    nome = models.CharField('Nome da Cor', max_length=50, unique=True)
    codigo_hex = models.CharField('Código Hex', max_length=7, blank=True, help_text='Ex: #FFFFFF')
    ativo = models.BooleanField('Ativo', default=True)

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Cor de Veículo'
        verbose_name_plural = 'Cores de Veículos'
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Fabricante(models.Model):
    """Fabricante de veículos (Toyota, Chevrolet, etc)"""
    
    nome = models.CharField('Nome', max_length=100, unique=True)
    pais_origem = models.CharField('País de Origem', max_length=50, blank=True)
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Fabricante'
        verbose_name_plural = 'Fabricantes'
        ordering = ['nome']
    
    def __str__(self):
        return self.nome


class ModeloVeiculo(models.Model):
    """Modelo de veículo (Corolla, Onix, etc)"""
    
    CATEGORIA_CHOICES = [
        ('hatch', 'Hatchback'),
        ('sedan', 'Sedan'),
        ('suv', 'SUV'),
        ('pickup', 'Picape'),
        ('van', 'Van/Utilitário'),
        ('esportivo', 'Esportivo'),
        ('caminhao', 'Caminhão'),
        ('moto', 'Motocicleta'),
        ('outro', 'Outro'),
    ]
    
    fabricante = models.ForeignKey(
        Fabricante,
        on_delete=models.PROTECT,
        related_name='modelos',
        verbose_name='Fabricante'
    )
    nome = models.CharField('Nome do Modelo', max_length=100)
    categoria = models.CharField(
        'Categoria',
        max_length=20,
        choices=CATEGORIA_CHOICES,
        default='sedan'
    )
    ativo = models.BooleanField('Ativo', default=True)
    
    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Modelo de Veículo'
        verbose_name_plural = 'Modelos de Veículos'
        ordering = ['fabricante__nome', 'nome']
        unique_together = ['fabricante', 'nome']
    
    def __str__(self):
        return f"{self.fabricante.nome} {self.nome}"
    
    @property
    def nome_completo(self):
        return f"{self.fabricante.nome} {self.nome} ({self.get_categoria_display()})"
