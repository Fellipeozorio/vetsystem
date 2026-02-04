from django.contrib import admin
from .models import MedicalRecord, Prescription, Vaccine, Attachment


class PrescriptionInline(admin.TabularInline):
    model = Prescription
    extra = 1


class VaccineInline(admin.TabularInline):
    model = Vaccine
    extra = 1


class AttachmentInline(admin.TabularInline):
    model = Attachment
    extra = 1


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('pet', 'veterinario', 'criado_em')
    search_fields = ('pet__nome',)
    inlines = [PrescriptionInline, VaccineInline, AttachmentInline]
