from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('ordens', '0008_ordemetapa_execucao'),
    ]

    operations = [
        migrations.AddField(
            model_name='ordemetapa',
            name='pular_etapa',
            field=models.BooleanField(default=False, verbose_name='Pular Etapa (não seguir ordem)'),
        ),
    ]

