from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("attendance", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="attendancerecord",
            name="source",
            field=models.CharField(
                choices=[
                    ("FACE", "Face recognition"),
                    ("MANUAL", "Teacher correction"),
                    ("SYSTEM", "Session initialization"),
                    ("DEMO", "Demo simulation"),
                ],
                default="SYSTEM",
                max_length=10,
            ),
        ),
    ]
