# Generated by Django 4.0.6 on 2022-08-04 20:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('organizations', '0003_alter_membership_options_membershiptype_and_more'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='membershiptype',
            name='only_one_admin',
        ),
        migrations.RemoveConstraint(
            model_name='membershiptype',
            name='only_one_default',
        ),
        migrations.AddConstraint(
            model_name='membershiptype',
            constraint=models.UniqueConstraint(fields=('organization', 'name'), name='name_unique_per_organization'),
        ),
        migrations.AddConstraint(
            model_name='membershiptype',
            constraint=models.UniqueConstraint(fields=('organization', 'admin'), name='admin_unique_per_organization'),
        ),
        migrations.AddConstraint(
            model_name='membershiptype',
            constraint=models.UniqueConstraint(fields=('organization', 'default'), name='default_unique_per_organization'),
        ),
    ]
