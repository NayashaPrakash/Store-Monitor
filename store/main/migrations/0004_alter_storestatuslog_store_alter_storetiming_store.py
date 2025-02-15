from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0003_auto_20230725_2048'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storestatuslog',
            name='store',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_logs', to='main.store'),
        ),
        migrations.AlterField(
            model_name='storetiming',
            name='store',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='timings', to='main.store'),
        ),
    ]
