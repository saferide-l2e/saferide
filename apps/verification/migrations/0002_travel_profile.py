from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("verification", "0001_initial")]

    operations = [
        migrations.AddField(
            model_name="verification", name="profile_name",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="verification", name="home_area",
            field=models.CharField(blank=True, max_length=80),
        ),
        migrations.AddField(
            model_name="verification", name="preferred_stop",
            field=models.CharField(blank=True, max_length=80),
        ),
    ]
