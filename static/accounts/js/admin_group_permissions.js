document.addEventListener('DOMContentLoaded', function() {
  // Only on admin user change/add pages
  const groupsTo = document.getElementById('id_groups_to');
  const userPermsSelect = document.getElementById('id_user_permissions');
  if (!groupsTo || !userPermsSelect) return;

  // Create apply button
  const applyBtn = document.createElement('button');
  applyBtn.type = 'button';
  applyBtn.className = 'button';
  applyBtn.style.marginTop = '6px';
  applyBtn.textContent = 'Aplicar permissões do(s) grupo(s)';
  groupsTo.parentNode.insertBefore(applyBtn, groupsTo.nextSibling);

  applyBtn.addEventListener('click', async function() {
    const groupOptions = Array.from(document.querySelectorAll('#id_groups_to option'));
    const groupIds = groupOptions.map(o => o.value).filter(Boolean);
    if (groupIds.length === 0) {
      alert('Selecione ao menos um grupo no painel direito (grupos atribuídos).');
      return;
    }

    const permIds = new Set();
    for (const gid of groupIds) {
      try {
        const res = await fetch(`/accounts/api/group-permissions/${gid}/`);
        if (!res.ok) continue;
        const data = await res.json();
        if (data.permissions) data.permissions.forEach(p => permIds.add(String(p.id)));
      } catch (e) {
        console.error('Erro ao buscar permissões do grupo', e);
      }
    }

    if (permIds.size === 0) {
      alert('Nenhuma permissão encontrada para os grupos selecionados.');
      return;
    }

    // Ensure options exist in the main select and mark them selected
    for (const opt of Array.from(userPermsSelect.options)) {
      if (permIds.has(opt.value)) {
        opt.selected = true;
      }
    }

    // If FilteredSelectMultiple is present, move options to the "to" box
    const fromBox = document.getElementById('id_user_permissions_from');
    const toBox = document.getElementById('id_user_permissions_to');
    if (fromBox && toBox) {
      // Move matching options from fromBox to toBox
      Array.from(fromBox.querySelectorAll('option')).forEach(o => {
        if (permIds.has(o.value)) {
          const clone = o.cloneNode(true);
          toBox.appendChild(clone);
          o.remove();
        }
      });
    }

    alert('Permissões aplicadas ao campo de permissões. Salve o usuário para persistir.');
  });
});
