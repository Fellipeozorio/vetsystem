/**
 * Sistema de substituição de etiquetas de template
 * Substitui placeholders como {{animal.nome}}, {{cliente.cpf}}, etc. pelos valores reais
 * 
 * Uso:
 * const textoSubstituido = substituirEtiquetas(templateText, dadosContexto);
 */

(function(window) {
  'use strict';

  /**
   * Helper para retornar valor ou "não informado"
   */
  function valorOuPadrao(valor, padrao = 'não informado') {
    if (valor === null || valor === undefined || valor === '') {
      return padrao;
    }
    return String(valor);
  }

  /**
   * Formata data por extenso em português
   */
  function dataExtenso(data) {
    const meses = ['janeiro', 'fevereiro', 'março', 'abril', 'maio', 'junho',
                   'julho', 'agosto', 'setembro', 'outubro', 'novembro', 'dezembro'];
    const d = data || new Date();
    return `${d.getDate()} de ${meses[d.getMonth()]} de ${d.getFullYear()}`;
  }

  /**
   * Substitui todas as etiquetas de template no texto fornecido
   * @param {string} template - Texto contendo etiquetas (ex: "Animal: {{animal.nome}}")
   * @param {object} contexto - Objeto com os dados para substituição
   * @returns {string} Texto com etiquetas substituídas
   */
  window.substituirEtiquetas = function(template, contexto = {}) {
    if (!template) return '';
    
    // Calcular idade do animal se houver data de nascimento
    let idadeTexto = '';
    if (contexto.pet && contexto.pet.data_nascimento) {
      const dataNasc = new Date(contexto.pet.data_nascimento);
      const hoje = new Date();
      let anos = hoje.getFullYear() - dataNasc.getFullYear();
      let meses = hoje.getMonth() - dataNasc.getMonth();
      if (meses < 0) { anos--; meses += 12; }
      if (anos > 0) idadeTexto = anos + (anos > 1 ? ' anos' : ' ano');
      if (meses > 0) idadeTexto += (idadeTexto ? ' e ' : '') + meses + (meses > 1 ? ' meses' : ' mês');
      if (!idadeTexto) idadeTexto = 'Menos de 1 mês';
    } else if (contexto.pet && contexto.pet.idade_estimada) {
      idadeTexto = contexto.pet.idade_estimada + (contexto.pet.idade_estimada > 1 ? ' anos (estimado)' : ' ano (estimado)');
    }
    
    // CPF ou CNPJ do cliente
    const cpfCnpj = (contexto.cliente && contexto.cliente.tipo === 'PJ') 
      ? (contexto.cliente.cnpj || '') 
      : (contexto.cliente && contexto.cliente.cpf || '');
    
    // Dados do animal/paciente
    const dadosAnimal = {
      nome: valorOuPadrao((contexto.pet && contexto.pet.nome)),
      especie: valorOuPadrao((contexto.pet && contexto.pet.especie_nome)),
      raca: valorOuPadrao((contexto.pet && contexto.pet.raca_nome)),
      pelagem: valorOuPadrao((contexto.pet && contexto.pet.pelagem_nome)),
      sexo: valorOuPadrao((contexto.pet && contexto.pet.sexo_display)),
      esterilizacao: valorOuPadrao((contexto.pet && contexto.pet.esterilizacao_display)),
      peso: valorOuPadrao((contexto.pet && contexto.pet.peso)),
      porte: valorOuPadrao((contexto.pet && contexto.pet.porte)),
      idade: valorOuPadrao(idadeTexto),
      data_nascimento: valorOuPadrao((contexto.pet && contexto.pet.data_nascimento_formatada)),
      microchip: valorOuPadrao((contexto.pet && contexto.pet.microchip)),
      codigo: valorOuPadrao((contexto.pet && contexto.pet.codigo)),
      caracteristicas: valorOuPadrao((contexto.pet && contexto.pet.caracteristicas)),
      temperamento: valorOuPadrao((contexto.pet && contexto.pet.temperamento)),
      marcacoes: valorOuPadrao((contexto.pet && contexto.pet.marcacoes)),
      pedigree: valorOuPadrao((contexto.pet && contexto.pet.pedigree_display)),
      numero_pedigree: valorOuPadrao((contexto.pet && contexto.pet.numero_pedigree)),
      status: valorOuPadrao((contexto.pet && contexto.pet.status_display))
    };
    
    // Dados do cliente/responsável
    const dadosCliente = {
      nome: valorOuPadrao((contexto.cliente && contexto.cliente.nome_completo)),
      nome_completo: valorOuPadrao((contexto.cliente && contexto.cliente.nome_completo)),
      cpf: valorOuPadrao((contexto.cliente && contexto.cliente.cpf)),
      cnpj: valorOuPadrao((contexto.cliente && contexto.cliente.cnpj)),
      cpf_cnpj: valorOuPadrao(cpfCnpj),
      rg: valorOuPadrao((contexto.cliente && contexto.cliente.rg)),
      celular: valorOuPadrao((contexto.cliente && contexto.cliente.celular)),
      telefone: valorOuPadrao((contexto.cliente && contexto.cliente.telefone)),
      email: valorOuPadrao((contexto.cliente && contexto.cliente.email)),
      endereco: valorOuPadrao((contexto.cliente && contexto.cliente.endereco_completo)),
      endereco_completo: valorOuPadrao((contexto.cliente && contexto.cliente.endereco_completo)),
      codigo: valorOuPadrao((contexto.cliente && contexto.cliente.codigo)),
      cep: valorOuPadrao((contexto.cliente && contexto.cliente.cep)),
      cidade: valorOuPadrao((contexto.cliente && contexto.cliente.cidade)),
      estado: valorOuPadrao((contexto.cliente && contexto.cliente.estado)),
      bairro: valorOuPadrao((contexto.cliente && contexto.cliente.bairro)),
      data_nascimento: valorOuPadrao((contexto.cliente && contexto.cliente.data_nascimento_formatada)),
      data_aniversario: valorOuPadrao((contexto.cliente && contexto.cliente.data_aniversario_formatada)),
      profissao: valorOuPadrao((contexto.cliente && contexto.cliente.profissao)),
      tipo: valorOuPadrao((contexto.cliente && contexto.cliente.tipo_display))
    };
    
    // Dados da clínica/unidade
    const dadosClinica = {
      nome: valorOuPadrao((contexto.clinica && contexto.clinica.nome_empreendimento)),
      nome_empreendimento: valorOuPadrao((contexto.clinica && contexto.clinica.nome_empreendimento)),
      cnpj: valorOuPadrao((contexto.clinica && contexto.clinica.cnpj)),
      inscricao_estadual: valorOuPadrao((contexto.clinica && contexto.clinica.inscricao_estadual)),
      registro_crmv: valorOuPadrao((contexto.clinica && contexto.clinica.registro_crmv)),
      telefone: valorOuPadrao((contexto.clinica && contexto.clinica.telefone_comercial)),
      telefone_comercial: valorOuPadrao((contexto.clinica && contexto.clinica.telefone_comercial)),
      celular: valorOuPadrao((contexto.clinica && contexto.clinica.celular)),
      email: valorOuPadrao((contexto.clinica && contexto.clinica.email)),
      endereco: valorOuPadrao((contexto.clinica && contexto.clinica.endereco_completo)),
      endereco_completo: valorOuPadrao((contexto.clinica && contexto.clinica.endereco_completo)),
      cep: valorOuPadrao((contexto.clinica && contexto.clinica.cep)),
      cidade: valorOuPadrao((contexto.clinica && contexto.clinica.cidade)),
      estado: valorOuPadrao((contexto.clinica && contexto.clinica.estado)),
      bairro: valorOuPadrao((contexto.clinica && contexto.clinica.bairro))
    };
    
    // Dados do usuário/veterinário
    const dadosUsuario = {
      nome: valorOuPadrao((contexto.usuario && contexto.usuario.nome_completo)),
      nome_completo: valorOuPadrao((contexto.usuario && contexto.usuario.nome_completo)),
      username: valorOuPadrao((contexto.usuario && contexto.usuario.username)),
      email: valorOuPadrao((contexto.usuario && contexto.usuario.email)),
      cpf: valorOuPadrao((contexto.usuario && contexto.usuario.cpf)),
      celular: valorOuPadrao((contexto.usuario && contexto.usuario.celular)),
      crmv: valorOuPadrao((contexto.usuario && contexto.usuario.crmv)),
      perfil: valorOuPadrao((contexto.usuario && contexto.usuario.perfil_display)),
      cargo: valorOuPadrao((contexto.usuario && contexto.usuario.perfil_display)),
      mapa: valorOuPadrao((contexto.usuario && contexto.usuario.crmv))
    };
    
    // Dados gerais
    const hoje = new Date();
    const dadosGerais = {
      data_atual: hoje.toLocaleDateString('pt-BR'),
      data_extenso: dataExtenso(hoje)
    };
    
    let resultado = template;
    
    // Substituir etiquetas do animal/paciente
    resultado = resultado.replace(/\{\{\s*(?:paciente|animal)\.nome\s*\}\}/gi, dadosAnimal.nome);
    resultado = resultado.replace(/\{\{\s*animal\.especie\s*\}\}/gi, dadosAnimal.especie);
    resultado = resultado.replace(/\{\{\s*animal\.raca\s*\}\}/gi, dadosAnimal.raca);
    resultado = resultado.replace(/\{\{\s*animal\.pelagem\s*\}\}/gi, dadosAnimal.pelagem);
    resultado = resultado.replace(/\{\{\s*animal\.sexo\s*\}\}/gi, dadosAnimal.sexo);
    resultado = resultado.replace(/\{\{\s*animal\.esterilizacao\s*\}\}/gi, dadosAnimal.esterilizacao);
    resultado = resultado.replace(/\{\{\s*animal\.peso\s*\}\}/gi, dadosAnimal.peso);
    resultado = resultado.replace(/\{\{\s*animal\.porte\s*\}\}/gi, dadosAnimal.porte);
    resultado = resultado.replace(/\{\{\s*animal\.idade\s*\}\}/gi, dadosAnimal.idade);
    resultado = resultado.replace(/\{\{\s*animal\.data_nascimento\s*\}\}/gi, dadosAnimal.data_nascimento);
    resultado = resultado.replace(/\{\{\s*animal\.microchip\s*\}\}/gi, dadosAnimal.microchip);
    resultado = resultado.replace(/\{\{\s*animal\.codigo\s*\}\}/gi, dadosAnimal.codigo);
    resultado = resultado.replace(/\{\{\s*animal\.caracteristicas\s*\}\}/gi, dadosAnimal.caracteristicas);
    resultado = resultado.replace(/\{\{\s*animal\.temperamento\s*\}\}/gi, dadosAnimal.temperamento);
    resultado = resultado.replace(/\{\{\s*animal\.marcacoes\s*\}\}/gi, dadosAnimal.marcacoes);
    resultado = resultado.replace(/\{\{\s*animal\.pedigree\s*\}\}/gi, dadosAnimal.pedigree);
    resultado = resultado.replace(/\{\{\s*animal\.numero_pedigree\s*\}\}/gi, dadosAnimal.numero_pedigree);
    resultado = resultado.replace(/\{\{\s*animal\.status\s*\}\}/gi, dadosAnimal.status);
    
    // Substituir etiquetas do cliente/responsável
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.nome\s*\}\}/gi, dadosCliente.nome);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.nome_completo\s*\}\}/gi, dadosCliente.nome_completo);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.cpf\s*\}\}/gi, dadosCliente.cpf);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.cnpj\s*\}\}/gi, dadosCliente.cnpj);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.cpf_cnpj\s*\}\}/gi, dadosCliente.cpf_cnpj);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.rg\s*\}\}/gi, dadosCliente.rg);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.celular\s*\}\}/gi, dadosCliente.celular);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.telefone\s*\}\}/gi, dadosCliente.telefone);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.email\s*\}\}/gi, dadosCliente.email);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.endereco\s*\}\}/gi, dadosCliente.endereco);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.endereco_completo\s*\}\}/gi, dadosCliente.endereco_completo);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.codigo\s*\}\}/gi, dadosCliente.codigo);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.cep\s*\}\}/gi, dadosCliente.cep);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.cidade\s*\}\}/gi, dadosCliente.cidade);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.estado\s*\}\}/gi, dadosCliente.estado);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.bairro\s*\}\}/gi, dadosCliente.bairro);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.data_nascimento\s*\}\}/gi, dadosCliente.data_nascimento);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.data_aniversario\s*\}\}/gi, dadosCliente.data_aniversario);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.profissao\s*\}\}/gi, dadosCliente.profissao);
    resultado = resultado.replace(/\{\{\s*(?:responsavel|cliente)\.tipo\s*\}\}/gi, dadosCliente.tipo);
    
    // Substituir etiquetas da clínica
    resultado = resultado.replace(/\{\{\s*clinica\.nome\s*\}\}/gi, dadosClinica.nome);
    resultado = resultado.replace(/\{\{\s*clinica\.nome_empreendimento\s*\}\}/gi, dadosClinica.nome_empreendimento);
    resultado = resultado.replace(/\{\{\s*clinica\.cnpj\s*\}\}/gi, dadosClinica.cnpj);
    resultado = resultado.replace(/\{\{\s*clinica\.inscricao_estadual\s*\}\}/gi, dadosClinica.inscricao_estadual);
    resultado = resultado.replace(/\{\{\s*clinica\.registro_crmv\s*\}\}/gi, dadosClinica.registro_crmv);
    resultado = resultado.replace(/\{\{\s*clinica\.telefone\s*\}\}/gi, dadosClinica.telefone);
    resultado = resultado.replace(/\{\{\s*clinica\.telefone_comercial\s*\}\}/gi, dadosClinica.telefone_comercial);
    resultado = resultado.replace(/\{\{\s*clinica\.celular\s*\}\}/gi, dadosClinica.celular);
    resultado = resultado.replace(/\{\{\s*clinica\.email\s*\}\}/gi, dadosClinica.email);
    resultado = resultado.replace(/\{\{\s*clinica\.endereco\s*\}\}/gi, dadosClinica.endereco);
    resultado = resultado.replace(/\{\{\s*clinica\.endereco_completo\s*\}\}/gi, dadosClinica.endereco_completo);
    resultado = resultado.replace(/\{\{\s*clinica\.cep\s*\}\}/gi, dadosClinica.cep);
    resultado = resultado.replace(/\{\{\s*clinica\.cidade\s*\}\}/gi, dadosClinica.cidade);
    resultado = resultado.replace(/\{\{\s*clinica\.estado\s*\}\}/gi, dadosClinica.estado);
    resultado = resultado.replace(/\{\{\s*clinica\.bairro\s*\}\}/gi, dadosClinica.bairro);
    
    // Substituir etiquetas do usuário/veterinário
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.nome\s*\}\}/gi, dadosUsuario.nome);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.nome_completo\s*\}\}/gi, dadosUsuario.nome_completo);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.username\s*\}\}/gi, dadosUsuario.username);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.email\s*\}\}/gi, dadosUsuario.email);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.cpf\s*\}\}/gi, dadosUsuario.cpf);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.celular\s*\}\}/gi, dadosUsuario.celular);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.crmv\s*\}\}/gi, dadosUsuario.crmv);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.perfil\s*\}\}/gi, dadosUsuario.perfil);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.cargo\s*\}\}/gi, dadosUsuario.cargo);
    resultado = resultado.replace(/\{\{\s*(?:usuario|veterinario)\.mapa\s*\}\}/gi, dadosUsuario.mapa);
    
    // Substituir etiquetas gerais
    resultado = resultado.replace(/\{\{\s*(?:geral|data)\.data_atual\s*\}\}/gi, dadosGerais.data_atual);
    resultado = resultado.replace(/\{\{\s*(?:geral|data)\.data_extenso\s*\}\}/gi, dadosGerais.data_extenso);
    
    return resultado;
  };
  
})(window);
