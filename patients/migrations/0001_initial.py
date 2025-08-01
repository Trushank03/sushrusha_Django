# Generated by Django 5.2.4 on 2025-07-12 10:20

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='MedicalRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('record_type', models.CharField(choices=[('lab_report', 'Lab Report'), ('prescription', 'Prescription'), ('diagnosis', 'Diagnosis'), ('vaccination', 'Vaccination'), ('surgery', 'Surgery'), ('allergy', 'Allergy'), ('other', 'Other')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField()),
                ('date_recorded', models.DateField()),
                ('document', models.FileField(blank=True, null=True, upload_to='medical_records/')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='medical_records', to=settings.AUTH_USER_MODEL)),
                ('recorded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='recorded_medical_records', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Medical Record',
                'verbose_name_plural': 'Medical Records',
                'db_table': 'medical_records',
                'ordering': ['-date_recorded'],
            },
        ),
        migrations.CreateModel(
            name='PatientDocument',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('document_type', models.CharField(choices=[('id_proof', 'ID Proof'), ('address_proof', 'Address Proof'), ('insurance_card', 'Insurance Card'), ('medical_report', 'Medical Report'), ('prescription', 'Prescription'), ('lab_report', 'Lab Report'), ('other', 'Other')], max_length=20)),
                ('title', models.CharField(max_length=200)),
                ('description', models.TextField(blank=True)),
                ('file', models.FileField(upload_to='patient_documents/')),
                ('is_verified', models.BooleanField(default=False)),
                ('verified_at', models.DateTimeField(blank=True, null=True)),
                ('uploaded_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='documents', to=settings.AUTH_USER_MODEL)),
                ('verified_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='verified_documents', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Patient Document',
                'verbose_name_plural': 'Patient Documents',
                'db_table': 'patient_documents',
                'ordering': ['-uploaded_at'],
            },
        ),
        migrations.CreateModel(
            name='PatientNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note', models.TextField()),
                ('is_private', models.BooleanField(default=True, help_text='Private notes are only visible to doctors')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='created_patient_notes', to=settings.AUTH_USER_MODEL)),
                ('patient', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='patient_notes', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Patient Note',
                'verbose_name_plural': 'Patient Notes',
                'db_table': 'patient_notes',
                'ordering': ['-created_at'],
            },
        ),
        migrations.CreateModel(
            name='PatientProfile',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blood_group', models.CharField(blank=True, max_length=5)),
                ('allergies', models.TextField(blank=True, help_text='Known allergies')),
                ('chronic_conditions', models.JSONField(default=list, help_text='List of chronic conditions')),
                ('current_medications', models.JSONField(default=list, help_text='List of current medications')),
                ('insurance_provider', models.CharField(blank=True, max_length=100)),
                ('insurance_policy_number', models.CharField(blank=True, max_length=50)),
                ('insurance_expiry', models.DateField(blank=True, null=True)),
                ('preferred_language', models.CharField(default='english', max_length=20)),
                ('notification_preferences', models.JSONField(default=dict, help_text='SMS, Email, Push notification preferences')),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='patient_profile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Patient Profile',
                'verbose_name_plural': 'Patient Profiles',
                'db_table': 'patient_profiles',
            },
        ),
    ]
