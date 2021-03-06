# Generated by Django 2.2.5 on 2022-01-21 15:57

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('landing', '0004_usercart'),
    ]

    operations = [
        migrations.CreateModel(
            name='Useraddr',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=50)),
                ('number', models.CharField(max_length=11)),
                ('addr', models.TextField(max_length=500)),
                ('city', models.CharField(max_length=50)),
                ('pin', models.CharField(max_length=7)),
                ('saddr', models.BooleanField(default=False)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='landing.Userprofile')),
            ],
        ),
    ]
