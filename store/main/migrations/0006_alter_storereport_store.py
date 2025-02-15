from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('main', '0005_storereport'),
    ]

    operations = [
        migrations.AlterField(
            model_name='storereport',
            name='store',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='reports', to='main.store'),
        ),
    ]
