from django.db import models
from django.contrib.auth.models import User
from clients.models import Client
from patients.models import Pet
from cadastros.models import TipoAtendimento, FilaAtendimento


class Agendamento(models.Model):
    """Modelo para agendamentos da agenda"""
    
    STATUS_CHOICES = [
        ('agendado', 'Agendado'),
        ('espera', 'Espera'),
        ('em_atendimento', 'Em atendimento'),
        ('atendido', 'Atendido'),
        ('cancelado', 'Cancelado'),
        ('atrasado', 'Atrasado'),
    ]
    
    # Dados do atendimento
    tipo_atendimento = models.ForeignKey(
        TipoAtendimento,
        on_delete=models.PROTECT,
        related_name='agendamentos',
        verbose_name='Tipo de Atendimento'
    )
    
    fila = models.ForeignKey(
        FilaAtendimento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos',
        verbose_name='Fila de Atendimento'
    )
    
    # Data e hora
    data = models.DateField(verbose_name='Data')
    horario = models.TimeField(verbose_name='Horário', null=True, blank=True)
    duracao_minutos = models.IntegerField(verbose_name='Duração (minutos)')
    
    # Cliente e Animal
    cliente = models.ForeignKey(
        Client,
        on_delete=models.CASCADE,
        related_name='agendamentos',
        verbose_name='Cliente/Responsável'
    )
    
    animal = models.ForeignKey(
        Pet,
        on_delete=models.CASCADE,
        related_name='agendamentos',
        verbose_name='Animal'
    )
    
    # Veterinário responsável
    veterinario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='agendamentos_veterinario',
        verbose_name='Veterinário'
    )
    
    # Informações adicionais
    celular_cliente = models.CharField(
        max_length=20,
        blank=True,
        verbose_name='Celular do Cliente'
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='agendado',
        verbose_name='Status'
    )
    
    observacoes = models.TextField(
        blank=True,
        verbose_name='Observações'
    )
    
    # Ordem na fila (para drag and drop)
    ordem = models.IntegerField(
        default=0,
        verbose_name='Ordem na Fila'
    )
    
    # Controle de tempos
    data_hora_chegada = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data/Hora de Chegada',
        help_text='Quando o paciente chegou (status mudou para "espera")'
    )
    
    data_hora_inicio_atendimento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data/Hora de Início do Atendimento',
        help_text='Quando o atendimento começou (status mudou para "em_atendimento")'
    )
    
    data_hora_fim_atendimento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='Data/Hora de Fim do Atendimento',
        help_text='Quando o atendimento terminou (status mudou para "atendido")'
    )
    
    # Controle
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='agendamentos_criados',
        verbose_name='Criado por'
    )
    
    class Meta:
        ordering = ['data', 'ordem', 'horario']
        verbose_name = 'Agendamento'
        verbose_name_plural = 'Agendamentos'
    
    def __str__(self):
        horario_str = self.horario.strftime('%H:%M') if self.horario else 'sem-horario'
        return f"{self.animal.nome} - {self.tipo_atendimento.nome} ({self.data} {horario_str})"


class HorarioFuncionamento(models.Model):
    """Horários de funcionamento da clínica por dia da semana"""
    
    DIAS_SEMANA = [
        (0, 'Segunda-feira'),
        (1, 'Terça-feira'),
        (2, 'Quarta-feira'),
        (3, 'Quinta-feira'),
        (4, 'Sexta-feira'),
        (5, 'Sábado'),
        (6, 'Domingo'),
    ]
    
    dia_semana = models.IntegerField(
        choices=DIAS_SEMANA,
        unique=True,
        verbose_name='Dia da Semana'
    )
    
    horario_inicio = models.TimeField(verbose_name='Horário de Início')
    horario_fim = models.TimeField(verbose_name='Horário de Término')
    
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        ordering = ['dia_semana']
        verbose_name = 'Horário de Funcionamento'
        verbose_name_plural = 'Horários de Funcionamento'
    
    def __str__(self):
        return f"{self.get_dia_semana_display()}: {self.horario_inicio} - {self.horario_fim}"


class ConfiguracaoAgendaUsuario(models.Model):
    """Configurações de agenda por usuário/veterinário"""
    
    TIPO_ATENDIMENTO = [
        ('nao_realiza', 'Não, este usuário não realiza atendimentos'),
        ('escala_fixa', 'Sim, este usuário realiza atendimentos e possui escala semanal fixa'),
        ('escala_variavel', 'Sim, este usuário realiza atendimentos e possui escala variável (Exemplo: Plantonistas)'),
    ]
    
    PERMISSAO_AGENDA = [
        ('todas', 'Este usuário pode ver e alterar a agenda de outros usuários'),
        ('propria', 'Este usuário pode ver e alterar apenas a própria agenda'),
    ]
    
    usuario = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='config_agenda',
        verbose_name='Usuário'
    )
    
    tipo_atendimento = models.CharField(
        max_length=20,
        choices=TIPO_ATENDIMENTO,
        default='escala_fixa',
        verbose_name='Realiza Atendimentos'
    )
    
    permissao_agenda = models.CharField(
        max_length=10,
        choices=PERMISSAO_AGENDA,
        default='propria',
        verbose_name='Permissão de Agenda'
    )
    
    # Horários específicos do usuário (se diferentes do padrão)
    horario_inicio = models.TimeField(null=True, blank=True, verbose_name='Horário de Início')
    horario_fim = models.TimeField(null=True, blank=True, verbose_name='Horário de Término')
    
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    class Meta:
        verbose_name = 'Configuração de Agenda do Usuário'
        verbose_name_plural = 'Configurações de Agenda dos Usuários'
    
    def __str__(self):
        return f"Config: {self.usuario.get_full_name() or self.usuario.username}"


class FilaDiaCalendario(models.Model):
    """Filas não permanentes adicionadas a dias específicos do calendário"""
    
    fila = models.ForeignKey(
        FilaAtendimento,
        on_delete=models.CASCADE,
        related_name='dias_calendario',
        verbose_name='Fila de Atendimento'
    )
    
    data = models.DateField(verbose_name='Data')
    
    ativo = models.BooleanField(default=True, verbose_name='Ativo')
    
    criado_em = models.DateTimeField(auto_now_add=True)
    criado_por = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name='Criado por'
    )
    
    class Meta:
        ordering = ['data', 'fila__nome']
        unique_together = ['fila', 'data']
        verbose_name = 'Fila em Dia do Calendário'
        verbose_name_plural = 'Filas em Dias do Calendário'
    
    def __str__(self):
        return f"{self.fila.nome} - {self.data}"


class HorarioAtendimentoUsuario(models.Model):
    """Horários semanais de atendimento por usuário"""
    
    DIAS_SEMANA = [
        (0, 'Domingo'),
        (1, 'Segunda-feira'),
        (2, 'Terça-feira'),
        (3, 'Quarta-feira'),
        (4, 'Quinta-feira'),
        (5, 'Sexta-feira'),
        (6, 'Sábado'),
    ]
    
    config_usuario = models.ForeignKey(
        ConfiguracaoAgendaUsuario,
        on_delete=models.CASCADE,
        related_name='horarios_semanais',
        verbose_name='Configuração do Usuário'
    )
    
    dia_semana = models.IntegerField(
        choices=DIAS_SEMANA,
        verbose_name='Dia da Semana'
    )
    
    horario_inicio = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Horário de Início'
    )
    
    horario_fim = models.TimeField(
        null=True,
        blank=True,
        verbose_name='Horário de Término'
    )
    
    trabalha = models.BooleanField(
        default=True,
        verbose_name='Trabalha neste dia'
    )
    
    class Meta:
        ordering = ['dia_semana']
        unique_together = ['config_usuario', 'dia_semana']
        verbose_name = 'Horário de Atendimento do Usuário'
        verbose_name_plural = 'Horários de Atendimento dos Usuários'
    
    def get_dia_semana_display(self):
        """Retorna o nome do dia da semana"""
        dias = dict(self.DIAS_SEMANA)
        return dias.get(self.dia_semana, '')
    
    def __str__(self):
        return f"{self.config_usuario.usuario.username} - {self.get_dia_semana_display()}"

