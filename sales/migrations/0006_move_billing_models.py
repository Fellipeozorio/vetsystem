import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sales', '0005_alter_sale_id_alter_saleitem_id_alter_service_id'),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.CreateModel(
                    name='CashRegister',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('data', models.DateField(auto_now_add=True)),
                        ('valor_abertura', models.DecimalField(decimal_places=2, max_digits=10)),
                        ('valor_fechamento', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True)),
                        ('status', models.CharField(choices=[('ABERTO', 'Aberto'), ('FECHADO', 'Fechado')], default='ABERTO', max_length=10)),
                        ('criado_em', models.DateTimeField(auto_now_add=True)),
                    ],
                ),
                migrations.CreateModel(
                    name='FinancialEntry',
                    fields=[
                        ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                        ('descricao', models.CharField(max_length=200)),
                        ('tipo', models.CharField(choices=[('ENTRADA', 'Entrada'), ('SAIDA', 'Saída')], max_length=10)),
                        ('valor', models.DecimalField(decimal_places=2, max_digits=10)),
                        ('forma_pagamento', models.CharField(choices=[('DINHEIRO', 'Dinheiro'), ('CREDITO', 'Cartão de Crédito'), ('DEBITO', 'Cartão de Débito'), ('PIX', 'PIX')], max_length=20)),
                        ('data', models.DateTimeField(auto_now_add=True)),
                        ('venda', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='financeiro', to='sales.sale')),
                        ('caixa', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='lancamentos', to='sales.cashregister')),
                    ],
                ),
            ],
            database_operations=[
                migrations.RunSQL(
                    sql='ALTER TABLE billing_cashregister RENAME TO sales_cashregister',
                    reverse_sql='ALTER TABLE sales_cashregister RENAME TO billing_cashregister',
                ),
                migrations.RunSQL(
                    sql='ALTER TABLE billing_financialentry RENAME TO sales_financialentry',
                    reverse_sql='ALTER TABLE sales_financialentry RENAME TO billing_financialentry',
                ),
            ],
        ),
    ]
