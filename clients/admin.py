from django.contrib import admin
from django import forms
from .models import Client
from patients.models import Pet


class PetInline(admin.TabularInline):
    model = Pet
    extra = 1


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = '__all__'

    def clean(self):
        cleaned = super().clean()
        person_type = cleaned.get('person_type')
        cpf = cleaned.get('cpf')
        cnpj = cleaned.get('cnpj')
        if person_type == Client.PESSOA_FISICA and not cpf:
            self.add_error('cpf', 'CPF obrigatório para pessoa física.')
        if person_type == Client.PESSOA_JURIDICA and not cnpj:
            self.add_error('cnpj', 'CNPJ obrigatório para pessoa jurídica.')
        return cleaned

    SIM_NAO = (('S', 'Sim'), ('N', 'Não'))

    # Use TypedChoiceField to coerce 'S'/'N' into booleans
    aceita_email = forms.TypedChoiceField(choices=SIM_NAO, coerce=lambda x: True if x == 'S' else False, required=False)
    aceita_whatsapp = forms.TypedChoiceField(choices=SIM_NAO, coerce=lambda x: True if x == 'S' else False, required=False)
    aceita_sms = forms.TypedChoiceField(choices=SIM_NAO, coerce=lambda x: True if x == 'S' else False, required=False)
    aceita_campanha_sms = forms.TypedChoiceField(choices=SIM_NAO, coerce=lambda x: True if x == 'S' else False, required=False)
    este_numero_e_whatsapp = forms.TypedChoiceField(choices=SIM_NAO, coerce=lambda x: True if x == 'S' else False, required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # initialize choice fields from boolean model fields
        inst = kwargs.get('instance')
        if inst:
            for f in ['aceita_email','aceita_whatsapp','aceita_sms','aceita_campanha_sms','este_numero_e_whatsapp']:
                val = getattr(inst, f, False)
                self.fields[f].initial = 'S' if val else 'N'


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    form = ClientForm
    list_display = ('nome_completo', 'celular', 'email', 'person_type')
    search_fields = ('nome_completo', 'cpf', 'celular')
    inlines = [PetInline]
    class Media:
        js = ('clients/js/person_type_toggle.js',)
        css = {
            'all': ('clients/css/person_type_toggle.css',)
        }
