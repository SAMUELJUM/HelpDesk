import django.db.models.deletion
import uuid
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('tickets', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Department',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, unique=True)),
            ],
        ),
        migrations.AddField(
            model_name='ticket',
            name='attachment',
            field=models.FileField(blank=True, null=True, upload_to='ticket_attachments/'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='closed_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='is_urgent',
            field=models.BooleanField(default=False, help_text='Mark if this ticket needs urgent attention'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='resolved_at',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ticket',
            name='ticket_id',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
        migrations.AlterField(
            model_name='category',
            name='name',
            field=models.CharField(max_length=100, unique=True),
        ),
        migrations.AlterField(
            model_name='ticket',
            name='description',
            field=models.TextField(help_text='Provide a detailed description of the issue.'),
        ),
        migrations.AddField(
            model_name='ticket',
            name='department',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='tickets.department'),
        ),
    ]
