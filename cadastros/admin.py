from django.contrib import admin
from .models import *


class BaseCadastroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome',)


admin.site.register(Especie, BaseCadastroAdmin)
admin.site.register(Raca, BaseCadastroAdmin)
admin.site.register(Pelagem, BaseCadastroAdmin)
admin.site.register(FilaAtendimento, BaseCadastroAdmin)
admin.site.register(Patologia, BaseCadastroAdmin)
admin.site.register(TipoAtendimento, BaseCadastroAdmin)
admin.site.register(Vacina, BaseCadastroAdmin)
admin.site.register(Exame, BaseCadastroAdmin)
admin.site.register(OrigemCliente, BaseCadastroAdmin)


admin.site.register(AtributoExame)
admin.site.register(ReferenciaExame)
admin.site.register(ModeloReceita)
admin.site.register(ModeloDocumento)
