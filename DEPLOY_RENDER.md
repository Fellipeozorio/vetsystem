# Deploy VetSystem no Render

## Pré-requisitos
- Conta no Render (https://render.com)
- Repositório GitHub configurado (https://github.com/Fellipeozorio/vetsystem)

## Passo a Passo

### 1. Criar novo Web Service no Render

1. Acesse https://dashboard.render.com
2. Clique em "New +" → "Web Service"
3. Conecte seu repositório GitHub: `Fellipeozorio/vetsystem`
4. Configure:
   - **Name**: vetsystem (ou nome de sua escolha)
   - **Environment**: Python 3
   - **Region**: Oregon (US West) ou mais próximo
   - **Branch**: main
   - **Build Command**: `./build.sh`
   - **Start Command**: `gunicorn vetsystem.wsgi:application`

### 2. Configurar Variáveis de Ambiente

No painel do Render, vá em "Environment" e adicione:

```bash
# Django Settings
SECRET_KEY=<gere-uma-chave-secreta-aleatoria>
DEBUG=False
ALLOWED_HOSTS=.onrender.com

# Database (Render PostgreSQL)
DATABASE_URL=<sera-fornecido-pelo-render-postgres>

# Superuser (para criar admin automaticamente)
DJANGO_SUPERUSER_USERNAME=admin
DJANGO_SUPERUSER_EMAIL=admin@vetsystem.com
DJANGO_SUPERUSER_PASSWORD=<sua-senha-segura>

# Email (opcional - configure depois)
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=seuemail@gmail.com
EMAIL_HOST_PASSWORD=sua-senha-de-app
DEFAULT_FROM_EMAIL=seuemail@gmail.com
```

### 3. Criar Banco de Dados PostgreSQL

1. No dashboard do Render, clique em "New +" → "PostgreSQL"
2. Configure:
   - **Name**: vetsystem-db
   - **Database**: vetsystem
   - **User**: vetsystem
   - **Region**: mesma do web service
3. Aguarde a criação
4. Copie a "Internal Database URL"
5. Cole no campo `DATABASE_URL` do seu Web Service

### 4. Deploy

1. Após configurar tudo, clique em "Create Web Service"
2. O Render vai:
   - Clonar o repositório
   - Executar `./build.sh`:
     - Instalar dependências
     - Coletar arquivos estáticos
     - Executar migrações
     - Criar superusuário
   - Iniciar o Gunicorn
3. Aguarde ~5-10 minutos para o primeiro deploy

### 5. Acessar a Aplicação

- URL pública: `https://vetsystem.onrender.com` (ou o nome que você escolheu)
- Admin: `https://vetsystem.onrender.com/admin`
- Login com credenciais do DJANGO_SUPERUSER

### 6. Configurações Pós-Deploy

#### Domínio Customizado (opcional)
1. No Render, vá em "Settings" → "Custom Domain"
2. Adicione seu domínio
3. Configure o DNS apontando para o Render

#### Email em Produção
Para enviar emails reais:
1. Configure `EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend`
2. Use um serviço como SendGrid ou configure Gmail com Senha de App

#### Monitoramento
- Logs: Dashboard Render → "Logs"
- Métricas: Dashboard Render → "Metrics"
- Alertas: Configure em "Settings" → "Deploy Hooks"

## Atualizações

Cada push para a branch `main` no GitHub vai automaticamente:
1. Disparar novo deploy no Render
2. Executar build.sh
3. Reiniciar a aplicação

## Troubleshooting

### Erro 500
- Verifique os logs no Render
- Confirme que `DEBUG=False`
- Verifique se `ALLOWED_HOSTS` inclui `.onrender.com`

### Database Connection Error
- Confirme que `DATABASE_URL` está configurado corretamente
- Verifique se o PostgreSQL está rodando na mesma region

### Arquivos estáticos não carregam
- Verifique se `./build.sh` executou `collectstatic`
- Confirme que WhiteNoise está no MIDDLEWARE
- Verifique STATIC_ROOT e STATICFILES_STORAGE

### Migrations não aplicadas
- Execute manualmente via Render Shell:
  ```bash
  python manage.py migrate
  ```

## Render Shell

Para executar comandos no servidor:
1. Dashboard → seu Web Service
2. "Shell" (canto superior direito)
3. Execute comandos Django:
   ```bash
   python manage.py createsuperuser
   python manage.py shell
   python manage.py migrate
   ```

## Custas

- **Web Service**: Free tier disponível (horas limitadas)
- **PostgreSQL**: Free tier com 90 dias (depois $7/mês para manter)
- **Upgrade**: $7/mês para Web Service + $7/mês para PostgreSQL (sem sleep)

## Backup

Configure backups automáticos do PostgreSQL:
- Dashboard PostgreSQL → "Settings" → "Backup"
- Render faz backups automáticos no plano pago

---

**Dica**: No free tier, o serviço "dorme" após 15min de inatividade e leva ~30s para "acordar" no primeiro acesso.
