/**
 * HugeRTE Editor Initialization
 * 
 * Funções reutilizáveis para inicializar o editor HugeRTE em diferentes páginas.
 * Baseado na documentação oficial: https://github.com/hugerte/hugerte-docs
 * 
 * Uso:
 * 1. Incluir o CDN do HugeRTE no head do template
 * 2. Incluir este arquivo
 * 3. Chamar HugeRTEEditor.init() com as configurações desejadas
 */

const HugeRTEEditor = {
  /**
   * Cache de editores criados
   */
  editors: {},
  
  /**
   * Configuração padrão para o editor
   */
  defaultConfig: {
    height: 400,
    min_height: 400,
    menubar: 'file edit view insert format tools table',
    plugins: 'lists link image table code help wordcount anchor autolink charmap fullscreen insertdatetime searchreplace visualblocks visualchars',
    toolbar: 'undo redo | blocks | bold italic underline strikethrough | forecolor backcolor | alignleft aligncenter alignright alignjustify | bullist numlist outdent indent | link image table | code removeformat help',
    content_style: 'body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif; font-size: 14px; line-height: 1.6; }',
    branding: false,
    promotion: false,
    statusbar: true,
    resize: true,
    elementpath: false,
    language: 'pt_BR'
  },
  
  /**
   * Verifica se o HugeRTE está carregado
   */
  isLoaded: function() {
    return typeof hugerte !== 'undefined';
  },
  
  /**
   * Aguarda o HugeRTE carregar
   */
  waitForLoad: function(callback, attempts = 30) {
    if (this.isLoaded()) {
      callback();
      return;
    }
    
    if (attempts <= 0) {
      console.error('❌ HugeRTE não foi carregado após múltiplas tentativas');
      return;
    }
    
    console.log('⏳ Aguardando HugeRTE carregar... tentativas restantes:', attempts);
    setTimeout(() => {
      this.waitForLoad(callback, attempts - 1);
    }, 100);
  },
  
  /**
   * Inicializa um editor em um elemento específico
   * 
   * @param {string} selector - Seletor CSS do elemento (ex: '#descricao-create')
   * @param {object} customConfig - Configurações personalizadas (opcional)
   * @param {string} editorKey - Chave para armazenar referência do editor (opcional)
   * @returns {Promise} Promise que resolve quando o editor é inicializado
   */
  init: function(selector, customConfig = {}, editorKey = null) {
    return new Promise((resolve, reject) => {
      this.waitForLoad(() => {
        const elem = document.querySelector(selector);
        if (!elem) {
          console.error('❌ Elemento não encontrado:', selector);
          reject(new Error(`Elemento ${selector} não encontrado`));
          return;
        }
        
        // Remover editor existente se houver
        if (editorKey && this.editors[editorKey]) {
          try {
            this.editors[editorKey].remove();
            console.log('🗑️ Editor anterior removido:', editorKey);
          } catch(e) {
            console.warn('Erro ao remover editor anterior:', e);
          }
          this.editors[editorKey] = null;
        }
        
        // Mesclar configurações
        const config = {
          ...this.defaultConfig,
          ...customConfig,
          selector: selector,
          setup: (editor) => {
            // Armazenar referência se fornecida
            if (editorKey) {
              this.editors[editorKey] = editor;
            }
            
            // Callback personalizado se fornecido
            if (customConfig.setup) {
              customConfig.setup(editor);
            }
            
            editor.on('init', () => {
              console.log('✓ Editor inicializado:', selector);
              resolve(editor);
            });
          }
        };
        
        console.log('🚀 Inicializando HugeRTE em:', selector);
        hugerte.init(config).catch((err) => {
          console.error('❌ Erro ao inicializar editor:', err);
          reject(err);
        });
      });
    });
  },
  
  /**
   * Inicializa múltiplos editores de uma vez
   * 
   * @param {array} configs - Array de objetos com {selector, config, key}
   * @returns {Promise} Promise que resolve quando todos os editores estão prontos
   */
  initMultiple: function(configs) {
    const promises = configs.map(({selector, config, key}) => {
      return this.init(selector, config, key);
    });
    
    return Promise.all(promises);
  },
  
  /**
   * Obtém um editor pela chave
   */
  getEditor: function(key) {
    return this.editors[key];
  },
  
  /**
   * Define o conteúdo de um editor
   * 
   * @param {string} key - Chave do editor
   * @param {string} content - Conteúdo HTML
   * @param {number} maxAttempts - Número máximo de tentativas
   */
  setContent: function(key, content, maxAttempts = 15) {
    return new Promise((resolve, reject) => {
      const trySet = (attempts) => {
        if (attempts <= 0) {
          console.error('❌ Não foi possível definir conteúdo após múltiplas tentativas');
          reject(new Error('Timeout ao definir conteúdo'));
          return;
        }
        
        const editor = this.getEditor(key);
        if (editor && editor.initialized) {
          editor.setContent(content);
          console.log('✓ Conteúdo definido no editor:', key);
          resolve();
        } else {
          console.log('⏳ Aguardando editor estar pronto... tentativa', 16 - attempts);
          setTimeout(() => trySet(attempts - 1), 100);
        }
      };
      
      trySet(maxAttempts);
    });
  },
  
  /**
   * Obtém o conteúdo de um editor
   */
  getContent: function(key) {
    const editor = this.getEditor(key);
    if (editor && editor.initialized) {
      return editor.getContent();
    }
    console.warn('⚠️ Editor não inicializado:', key);
    return null;
  },
  
  /**
   * Remove um editor
   */
  remove: function(key) {
    const editor = this.getEditor(key);
    if (editor) {
      try {
        editor.remove();
        this.editors[key] = null;
        console.log('🗑️ Editor removido:', key);
        return true;
      } catch(e) {
        console.error('❌ Erro ao remover editor:', e);
        return false;
      }
    }
    return false;
  },
  
  /**
   * Remove todos os editores
   */
  removeAll: function() {
    Object.keys(this.editors).forEach(key => {
      this.remove(key);
    });
  }
};

// Tornar disponível globalmente
window.HugeRTEEditor = HugeRTEEditor;

console.log('✓ HugeRTE Helper carregado');
