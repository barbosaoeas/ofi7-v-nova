# Generated migration

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='ordemetapa',
            name='status',
            field=models.CharField(
                choices=[
                    ('patio', 'No Pátio'),
                    ('aguardando_liberacao', 'Aguardando Liberação'),
                    ('liberado', 'Liberado'),
                    ('aguardando_programacao', 'Aguardando Programação'),
                    ('programado', 'Programado'),
                    ('em_servico', 'Em Serviço'),
                    ('aguardando_peca', 'Aguardando Peça'),
                    ('parado', 'Parado'),
                    ('concluido', 'Concluído'),
                ],
                default='aguardando_liberacao',
                max_length=30
            ),
        ),
    ]
