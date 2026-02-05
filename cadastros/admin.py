from django.contrib import admin
from .models import *


class BaseCadastroAdmin(admin.ModelAdmin):
    list_display = ('nome', 'ativo')
    list_filter = ('ativo',)
    search_fields = ('nome',)


class RacaAdmin(BaseCadastroAdmin):
    search_fields = ('nome',)

    def get_search_results(self, request, queryset, search_term):
        # Try to filter by especie passed as GET parameter. The admin
        # autocomplete can forward parameters; try common keys.
        especie_id = request.GET.get('especie') or request.GET.get('forward[especie]') or request.GET.get('forward.especie')
        if especie_id:
            try:
                queryset = queryset.filter(especie_id=especie_id)
            except Exception:
                pass
        return super().get_search_results(request, queryset, search_term)


admin.site.register(Especie, BaseCadastroAdmin)
admin.site.register(Raca, RacaAdmin)
admin.site.register(Pelagem, BaseCadastroAdmin)
admin.site.register(FilaAtendimento, BaseCadastroAdmin)
admin.site.register(Patologia, BaseCadastroAdmin)
admin.site.register(TipoAtendimento, BaseCadastroAdmin)
admin.site.register(Vacina, BaseCadastroAdmin)


class AtributoExameInline(admin.TabularInline):
    model = AtributoExame
    extra = 0
    fields = ('nome', 'unidade', 'valor_referencia')


class ReferenciaExameInline(admin.TabularInline):
    model = ReferenciaExame
    extra = 0
    fields = ('descricao',)


class ExameAdmin(BaseCadastroAdmin):
    list_display = ('nome', 'descricao', 'ativo')
    search_fields = ('nome', 'descricao')
    inlines = (AtributoExameInline, ReferenciaExameInline)

admin.site.register(Exame, ExameAdmin)
admin.site.register(OrigemCliente, BaseCadastroAdmin)


class AtributoExameAdmin(admin.ModelAdmin):
    list_display = ('nome', 'exame', 'unidade', 'valor_referencia')
    list_filter = ('exame',)
    search_fields = ('nome', 'exame__nome')


class ReferenciaExameAdmin(admin.ModelAdmin):
    list_display = ('descricao', 'exame')
    list_filter = ('exame',)
    search_fields = ('descricao', 'exame__nome')


admin.site.register(AtributoExame, AtributoExameAdmin)
admin.site.register(ReferenciaExame, ReferenciaExameAdmin)
admin.site.register(ModeloReceita)
admin.site.register(ModeloDocumento)
