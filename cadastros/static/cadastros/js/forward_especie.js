(function($){
  $(function(){
    // Prefilter AJAX requests to append the selected especie to raca autocomplete calls
    $.ajaxPrefilter(function(options, originalOptions, jqXHR){
      var url = (options.url || '').toString();
      // target requests that look like admin autocomplete for cadastros.Raca
      var isRacaAutocomplete = /cadastros\/.{0,50}raca/i.test(url) && (/autocomplete/i.test(url) || /term=/.test(url) || /q=/.test(url));
      if (!isRacaAutocomplete) return;

      // try common id for especie field in admin forms
      var especieVal = $('#id_especie').val();
      if (!especieVal) {
        // fallback: try name-based selectors used in inlines/forms
        especieVal = $('[name$="especie"]').first().val();
      }
      if (especieVal) {
        var sep = url.indexOf('?') === -1 ? '?' : '&';
        options.url = url + sep + 'especie=' + encodeURIComponent(especieVal);
      }
    });
  });
})(django.jQuery);
