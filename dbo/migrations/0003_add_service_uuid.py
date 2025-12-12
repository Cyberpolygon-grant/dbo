# Generated manually
from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('dbo', '0002_remove_client_is_verified_alter_client_phone'),
    ]

    operations = [
        migrations.AddField(
            model_name='service',
            name='uuid',
            field=models.UUIDField(db_index=True, default=uuid.uuid4, editable=False, unique=True),
        ),
    ]

