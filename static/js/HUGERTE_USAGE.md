# Como usar o HugeRTE em outras páginas

Este guia mostra como usar o arquivo `hugerte-init.js` para adicionar o editor HugeRTE em qualquer página do seu projeto Django.

## Por que usar placeholders de loading?

Os textareas HTML são renderizados imediatamente, mas o HugeRTE leva alguns instantes para carregar e inicializar. Para evitar o "flash" visual onde o textarea aparece antes do editor estar pronto, usamos:

1. **CSS para esconder o textarea** - `display: none`
2. **Placeholder de loading** - Mostra "Carregando editor..." enquanto o HugeRTE inicializa
3. **Remoção do placeholder** - Quando o editor está pronto, o placeholder desaparece

Isso cria uma experiência visual mais suave e profissional.

## Configuração Inicial

### 1. Adicionar os scripts no template

No seu template, adicione no bloco `extra_head`:

```django
{% load static %}

{% block extra_head %}
<!-- CDN do HugeRTE -->
<script src="https://cdn.jsdelivr.net/npm/hugerte@1/hugerte.min.js" referrerpolicy="origin"></script>
<!-- Idioma português (pt_BR) -->
<script src="{% static 'js/hugerte-pt_BR.js' %}"></script>
<!-- Helper de inicialização -->
<script src="{% static 'js/hugerte-init.js' %}"></script>
{% endblock %}
```

**Importante:** Carregue os scripts nesta ordem:
1. CDN do HugeRTE (`hugerte.min.js`)
2. Arquivo de idioma (`hugerte-pt_BR.js`)
3. Helper de inicialização (`hugerte-init.js`)

### 2. Criar o textarea

No seu formulário HTML, crie um textarea com um ID único:

**Importante:** Adicione um elemento de loading para evitar o "flash" do textarea antes do editor carregar.

```html
<div class="mb-3">
  <label class="form-label">Descrição</label>
  <!-- Placeholder de loading -->
  <div id="loading-meu-editor" class="hugerte-loading"></div>
  <!-- Textarea (será escondido e substituído pelo editor) -->
  <textarea id="meu-editor" name="descricao"></textarea>
</div>
```

### 3. Adicionar CSS para esconder o textarea

No bloco `extra_head`, adicione estilos para esconder o textarea e mostrar o loading:

```django
<style>
  /* Esconder textareas que serão transformados em HugeRTE */
  textarea#meu-editor {
    display: none;
  }
  
  /* Placeholder de loading para o editor */
  .hugerte-loading {
    height: 400px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f8fafc;
    color: #64748b;
    font-size: 14px;
  }
  
  .hugerte-loading::after {
    content: 'Carregando editor...';
  }
</style>
```

## Uso Básico

### Inicializar um editor simples

```javascript
// Aguardar página carregar
window.addEventListener('load', function() {
  // Inicializar editor
  HugeRTEEditor.init('#meu-editor')
    .then(editor => {
      // Remover placeholder de loading
      const loading = document.getElementById('loading-meu-editor');
      if (loading) loading.style.display = 'none';
      console.log('Editor pronto!');
    })
    .catch(err => console.error('Erro:', err));
});
```

### Inicializar com configurações personalizadas

```javascript
HugeRTEEditor.init('#meu-editor', {
  height: 500,
  menubar: 'file edit view',
  plugins: 'lists link code',
  toolbar: 'bold italic | bullist numlist | link'
}, 'meuEditor');
```

### Inicializar em um modal/offcanvas

```javascript
const offcanvas = document.getElementById('meu-offcanvas');
offcanvas.addEventListener('shown.bs.offcanvas', function() {
  HugeRTEEditor.init('#meu-editor', {}, 'editorOffcanvas')
    .then(() => {
      // Remover placeholder de loading
      const loading = document.getElementById('loading-meu-editor');
      if (loading) loading.style.display = 'none';
      console.log('Editor pronto!');
    });
});
```

## Funções Disponíveis

### `HugeRTEEditor.init(selector, customConfig, editorKey)`
Inicializa um editor em um elemento específico.

**Parâmetros:**
- `selector` (string): Seletor CSS do elemento (ex: '#descricao')
- `customConfig` (object, opcional): Configurações personalizadas
- `editorKey` (string, opcional): Chave para armazenar referência do editor

**Retorna:** Promise que resolve com a instância do editor

**Exemplo:**
```javascript
HugeRTEEditor.init('#descricao', {
  height: 400,
  plugins: 'lists link image table code'
}, 'editorDescricao')
  .then(editor => console.log('Pronto!'))
  .catch(err => console.error('Erro:', err));
```

### `HugeRTEEditor.initMultiple(configs)`
Inicializa múltiplos editores de uma vez.

**Parâmetros:**
- `configs` (array): Array de objetos com {selector, config, key}

**Exemplo:**
```javascript
HugeRTEEditor.initMultiple([
  { selector: '#descricao1', config: {}, key: 'editor1' },
  { selector: '#descricao2', config: {}, key: 'editor2' }
]).then(() => console.log('Todos os editores prontos!'));
```

### `HugeRTEEditor.getEditor(key)`
Obtém a instância de um editor pela chave.

**Exemplo:**
```javascript
const editor = HugeRTEEditor.getEditor('editorDescricao');
if (editor) {
  console.log('Conteúdo:', editor.getContent());
}
```

### `HugeRTEEditor.setContent(key, content)`
Define o conteúdo de um editor.

**Parâmetros:**
- `key` (string): Chave do editor
- `content` (string): Conteúdo HTML

**Retorna:** Promise

**Exemplo:**
```javascript
HugeRTEEditor.setContent('editorDescricao', '<p>Novo conteúdo</p>')
  .then(() => console.log('Conteúdo definido!'))
  .catch(err => console.error('Erro:', err));
```

### `HugeRTEEditor.getContent(key)`
Obtém o conteúdo de um editor.

**Exemplo:**
```javascript
const conteudo = HugeRTEEditor.getContent('editorDescricao');
console.log(conteudo);
```

### `HugeRTEEditor.remove(key)`
Remove um editor específico.

**Exemplo:**
```javascript
HugeRTEEditor.remove('editorDescricao');
```

### `HugeRTEEditor.removeAll()`
Remove todos os editores.

**Exemplo:**
```javascript
HugeRTEEditor.removeAll();
```

## Exemplo Completo - Exames

```django
{% extends 'cadastros/base_list.html' %}
{% load static %}

{% block extra_head %}
<script src="https://cdn.jsdelivr.net/npm/hugerte@1/hugerte.min.js" referrerpolicy="origin"></script>
<script src="{% static 'js/hugerte-pt_BR.js' %}"></script>
<script src="{% static 'js/hugerte-init.js' %}"></script>

<style>
  /* Esconder textareas que serão transformados em HugeRTE */
  textarea#descricao-create,
  textarea#descricao-edit {
    display: none;
  }
  
  .hugerte-loading {
    height: 400px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #f8fafc;
    color: #64748b;
    font-size: 14px;
  }
  
  .hugerte-loading::after {
    content: 'Carregando editor...';
  }
</style>
{% endblock %}

{% block form_fields %}
<div class="mb-3">
  <label class="form-label">Nome do Exame</label>
  <input type="text" class="form-control" name="nome" required>
</div>

<div class="mb-3">
  <label class="form-label">Descrição</label>
  <div id="loading-descricao-create" class="hugerte-loading"></div>
  <textarea id="descricao-create" name="descricao"></textarea>
</div>

<script>
window.addEventListener('load', function() {
  const offcanvasAdd = document.getElementById('offcanvas-add');
  if (offcanvasAdd) {
    offcanvasAdd.addEventListener('shown.bs.offcanvas', function() {
      HugeRTEEditor.init('#descricao-create', {}, 'editorCreate')
        .then(() => {
          const loading = document.getElementById('loading-descricao-create');
          if (loading) loading.style.display = 'none';
        });
    });
  }
});
</script>
{% endblock %}

{% block form_fields_edit %}
<div class="mb-3">
  <label class="form-label">Nome do Exame</label>
  <input type="text" class="form-control" id="edit-nome" name="nome" required>
</div>

<div class="mb-3">
  <label class="form-label">Descrição</label>
  <div id="loading-descricao-edit" class="hugerte-loading"></div>
  <textarea id="descricao-edit" name="descricao"></textarea>
</div>

<script>
window.addEventListener('load', function() {
  const offcanvasEdit = document.getElementById('offcanvas-edit');
  if (offcanvasEdit) {
    offcanvasEdit.addEventListener('shown.bs.offcanvas', function() {
      HugeRTEEditor.init('#descricao-edit', {}, 'editorEdit')
        .then(() => {
          const loading = document.getElementById('loading-descricao-edit');
          if (loading) loading.style.display = 'none';
        });
    });
  }
});

// Popular campos ao editar
function populateEditForm(data) {
  document.getElementById('edit-nome').value = data.nome || '';
  
  if (data.descricao) {
    HugeRTEEditor.setContent('editorEdit', data.descricao)
      .catch(() => {
        document.getElementById('descricao-edit').value = data.descricao;
      });
  }
}
</script>
{% endblock %}
```

## Configuração Padrão

A configuração padrão inclui:

- **Altura:** 400px
- **Menubar:** file edit view insert format tools table
- **Plugins:** lists, link, image, table, code, help, wordcount, anchor, autolink, autoresize, charmap, fullscreen, insertdatetime, searchreplace, visualblocks, visualchars
- **Idioma:** pt_BR (Português do Brasil)
- **Statusbar:** ativada (mostra contador de palavras e caminho do elemento)
- **Resize:** ativado (permite redimensionar o editor)
- **Branding:** desativado
- **Element path:** desativado

## Personalização de Plugins

Para adicionar ou remover plugins, passe a configuração personalizada:

```javascript
HugeRTEEditor.init('#meu-editor', {
  plugins: 'lists link image table code emoticons media preview',
  toolbar: 'undo redo | bold italic | bullist numlist | link image | code'
});
```

## Barra de Status (Statusbar)

A barra de status está **ativada por padrão** e exibe:

- **Contador de palavras**: mostra o número de palavras no documento
- **Contador de caracteres**: mostra o número de caracteres
- **Resize handle**: permite redimensionar o editor arrastando o canto inferior direito

### Desativar a barra de status

Se você não quiser a barra de status:

```javascript
HugeRTEEditor.init('#meu-editor', {
  statusbar: false
});
```

### Desativar apenas o caminho do elemento

Se quiser manter o contador de palavras mas remover o caminho do elemento:

```javascript
HugeRTEEditor.init('#meu-editor', {
  elementpath: false  // Remove "p > strong", mantém contador
});
```

### Desativar redimensionamento

```javascript
HugeRTEEditor.init('#meu-editor', {
  resize: false  // Remove o handle de redimensionamento
});
```

## Plugins Disponíveis

- **accordion** - Inserir accordions
- **advlist** - Listas avançadas
- **anchor** - Inserir âncoras
- **autolink** - Detectar links automaticamente
- **autoresize** - Redimensionar automaticamente
- **autosave** - Salvar automaticamente
- **charmap** - Mapa de caracteres especiais
- **code** - Editar código HTML
- **codesample** - Inserir amostras de código
- **directionality** - Direção do texto (LTR/RTL)
- **emoticons** - Inserir emojis
- **fullscreen** - Modo tela cheia
- **help** - Ajuda
- **image** - Inserir imagens
- **insertdatetime** - Inserir data/hora
- **link** - Inserir links
- **lists** - Listas
- **media** - Inserir mídia (vídeo/áudio)
- **nonbreaking** - Espaço não-quebrável
- **pagebreak** - Quebra de página
- **preview** - Pré-visualização
- **quickbars** - Barras de ferramentas rápidas
- **save** - Botão salvar
- **searchreplace** - Buscar e substituir
- **table** - Inserir tabelas
- **template** - Templates
- **visualblocks** - Visualizar blocos
- **visualchars** - Visualizar caracteres especiais
- **wordcount** - Contador de palavras

## Documentação Oficial

Para mais informações, consulte:
- HugeRTE: https://github.com/hugerte/hugerte-docs
- TinyMCE 6 docs (compatível): https://www.tiny.cloud/docs/tinymce/6/

**Nota:** Substitua `tinymce` por `hugerte` ao consultar a documentação do TinyMCE.
