# Instalação do GTK Runtime para Windows

Para gerar PDFs com WeasyPrint no Windows, é necessário instalar o **GTK3 Runtime**.

## Passos para Instalação

### 1. Baixar o Instalador

Acesse a página de releases do GTK para Windows:
https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases/latest

### 2. Escolher a Versão Correta

- Para Windows 64-bit: `gtk3-runtime-X.XX.XX-YYYY-MM-DD-ts-win64.exe`
- Para Windows 32-bit: `gtk3-runtime-X.XX.XX-YYYY-MM-DD-ts-win32.exe`

### 3. Executar o Instalador

1. Execute o arquivo `.exe` baixado
2. Siga as instruções do instalador
3. Recomenda-se manter as opções padrão
4. Aguarde a conclusão da instalação

### 4. Reiniciar o Servidor

Após instalar o GTK:
1. Pare o servidor Django (Ctrl + C no terminal)
2. Reinicie o servidor: `python manage.py runserver`
3. Recarregue a página no navegador

## Verificação

Se a instalação foi bem-sucedida, ao clicar no botão de imprimir fila, um PDF será gerado e aberto no visualizador do navegador.

## Alternativa (Sem Instalação)

Se preferir não instalar o GTK, você pode usar outras bibliotecas para geração de PDF:
- `xhtml2pdf` (não requer dependências externas, mas qualidade inferior)
- `reportlab` (maior controle, mas requer mais código)

## Problemas Comuns

### Erro: "cannot load library 'libgobject-2.0-0'"
**Solução:** GTK não está instalado ou não está no PATH do sistema. Execute o instalador novamente.

### Erro: "DLL load failed"
**Solução:** Certifique-se de baixar a versão correta (64-bit ou 32-bit) correspondente ao seu Python.

### PDF não gera após instalação
**Solução:** Reinicie completamente o computador para garantir que as variáveis de ambiente sejam atualizadas.

## Suporte

Em caso de problemas, consulte a documentação oficial:
- WeasyPrint: https://doc.courtbouillon.org/weasyprint/stable/
- GTK Windows: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer

