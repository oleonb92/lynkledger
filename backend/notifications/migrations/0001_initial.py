# Generated by Django 4.2.10 on 2025-05-18 22:36

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('organizations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='NotificationCategory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=100, verbose_name='name')),
                ('type', models.CharField(choices=[('system', 'System'), ('account', 'Account'), ('transaction', 'Transaction'), ('document', 'Document'), ('message', 'Message'), ('task', 'Task'), ('ai', 'AI Assistant'), ('security', 'Security')], default='system', max_length=20, verbose_name='type')),
                ('description', models.TextField(blank=True, verbose_name='description')),
                ('icon', models.CharField(blank=True, max_length=50, verbose_name='icon')),
                ('color', models.CharField(default='#000000', max_length=7, verbose_name='color')),
            ],
            options={
                'verbose_name': 'notification category',
                'verbose_name_plural': 'notification categories',
                'ordering': ['name'],
            },
        ),
        migrations.CreateModel(
            name='NotificationTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, verbose_name='name')),
                ('type', models.CharField(choices=[('email', 'Email'), ('push', 'Push Notification'), ('in_app', 'In-App Notification'), ('sms', 'SMS')], max_length=20, verbose_name='type')),
                ('subject', models.CharField(max_length=255, verbose_name='subject')),
                ('body', models.TextField(verbose_name='body')),
                ('html_body', models.TextField(blank=True, verbose_name='HTML body')),
                ('variables', models.JSONField(default=list, verbose_name='variables')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('is_active', models.BooleanField(default=True, verbose_name='active')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='templates', to='notifications.notificationcategory', verbose_name='category')),
            ],
            options={
                'verbose_name': 'notification template',
                'verbose_name_plural': 'notification templates',
                'unique_together': {('category', 'type', 'name')},
            },
        ),
        migrations.CreateModel(
            name='NotificationPreference',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('email_enabled', models.BooleanField(default=True, verbose_name='email enabled')),
                ('push_enabled', models.BooleanField(default=True, verbose_name='push enabled')),
                ('sms_enabled', models.BooleanField(default=False, verbose_name='SMS enabled')),
                ('quiet_hours_start', models.TimeField(blank=True, null=True, verbose_name='quiet hours start')),
                ('quiet_hours_end', models.TimeField(blank=True, null=True, verbose_name='quiet hours end')),
                ('min_interval', models.DurationField(blank=True, null=True, verbose_name='minimum interval')),
                ('daily_limit', models.PositiveIntegerField(blank=True, null=True, verbose_name='daily limit')),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='notifications.notificationcategory', verbose_name='category')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notification_preferences', to=settings.AUTH_USER_MODEL, verbose_name='user')),
            ],
            options={
                'verbose_name': 'notification preference',
                'verbose_name_plural': 'notification preferences',
                'unique_together': {('user', 'category')},
            },
        ),
        migrations.CreateModel(
            name='Notification',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=255, verbose_name='title')),
                ('message', models.TextField(verbose_name='message')),
                ('data', models.JSONField(blank=True, default=dict, verbose_name='data')),
                ('object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('priority', models.CharField(choices=[('low', 'Low'), ('normal', 'Normal'), ('high', 'High'), ('urgent', 'Urgent')], default='normal', max_length=20, verbose_name='priority')),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('sent', 'Sent'), ('delivered', 'Delivered'), ('read', 'Read'), ('failed', 'Failed')], default='pending', max_length=20, verbose_name='status')),
                ('email_sent', models.BooleanField(default=False, verbose_name='email sent')),
                ('push_sent', models.BooleanField(default=False, verbose_name='push sent')),
                ('sms_sent', models.BooleanField(default=False, verbose_name='SMS sent')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='created at')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='updated at')),
                ('read_at', models.DateTimeField(blank=True, null=True, verbose_name='read at')),
                ('scheduled_for', models.DateTimeField(blank=True, null=True, verbose_name='scheduled for')),
                ('actions', models.JSONField(blank=True, default=list, verbose_name='actions')),
                ('category', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='notifications.notificationcategory', verbose_name='category')),
                ('content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('organization', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to='organizations.organization', verbose_name='organization')),
                ('recipient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='notifications', to=settings.AUTH_USER_MODEL, verbose_name='recipient')),
            ],
            options={
                'verbose_name': 'notification',
                'verbose_name_plural': 'notifications',
                'ordering': ['-created_at'],
                'indexes': [models.Index(fields=['recipient', '-created_at'], name='notificatio_recipie_a972ce_idx'), models.Index(fields=['status', 'scheduled_for'], name='notificatio_status_d8d933_idx')],
            },
        ),
    ]
