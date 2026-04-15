from django.db import models


class ConfiguracaoSistema(models.Model):
    nome_empresa = models.CharField('Nome da empresa', max_length=120, blank=True)
    endereco = models.CharField('Endereço', max_length=255, blank=True)
    telefone = models.CharField('Telefone', max_length=40, blank=True)
    email = models.EmailField('E-mail', blank=True)
    cnpj = models.CharField('CNPJ', max_length=30, blank=True)
    site = models.CharField('Site', max_length=120, blank=True)

    logo = models.ImageField('Logomarca', upload_to='sistema/', null=True, blank=True)

    cor_primaria = models.CharField('Cor primária (hex)', max_length=7, default='#2563EB')
    cor_rodape = models.CharField('Cor do rodapé (hex)', max_length=7, default='#111827')

    texto_rodape = models.CharField('Texto do rodapé', max_length=200, blank=True)

    atualizado_em = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Configuração do Sistema'
        verbose_name_plural = 'Configurações do Sistema'

    def __str__(self):
        return self.nome_empresa or 'Configuração do Sistema'
