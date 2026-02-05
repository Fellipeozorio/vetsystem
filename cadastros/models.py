from django.db import models


class BaseCadastro(models.Model):
    nome = models.CharField(max_length=150, unique=True)
    ativo = models.BooleanField(default=True)

    class Meta:
        abstract = True
        ordering = ['nome']

    def __str__(self):
        return self.nome


class Especie(BaseCadastro):
    pass


class Raca(BaseCadastro):
    especie = models.ForeignKey(
        Especie,
        on_delete=models.CASCADE,
        related_name='racas'
    )


class Pelagem(BaseCadastro):
    pass


class FilaAtendimento(BaseCadastro):
    descricao = models.TextField(blank=True, null=True)


class Patologia(BaseCadastro):
    codigo = models.CharField(max_length=50, blank=True, null=True)
    descricao = models.TextField(blank=True, null=True)


class TipoAtendimento(BaseCadastro):
    duracao_padrao = models.PositiveIntegerField(
        help_text="Duração em minutos",
        default=30
    )


class Vacina(BaseCadastro):
    grupo = models.CharField(max_length=150, blank=True, null=True)


class Exame(BaseCadastro):
    descricao = models.TextField(blank=True, null=True)


class AtributoExame(models.Model):
    exame = models.ForeignKey(
        Exame,
        on_delete=models.CASCADE,
        related_name='atributos'
    )

    nome = models.CharField(max_length=150)
    unidade = models.CharField(max_length=50, blank=True, null=True)
    valor_referencia = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"{self.exame.nome} - {self.nome}"


class ReferenciaExame(models.Model):
    exame = models.ForeignKey(
        Exame,
        on_delete=models.CASCADE,
        related_name='referencias'
    )

    descricao = models.TextField()

    def __str__(self):
        return f"Referência - {self.exame.nome}"


class ModeloReceita(models.Model):
    nome = models.CharField(max_length=150)
    conteudo = models.TextField()

    def __str__(self):
        return self.nome


class ModeloDocumento(models.Model):
    nome = models.CharField(max_length=150)
    conteudo = models.TextField()

    def __str__(self):
        return self.nome


class OrigemCliente(BaseCadastro):
    pass
