(function ($) {

  window.PTL = window.PTL || {};

  PTL.stats = {

    init: function (options) {
      this.url = options.url;
    },

    load: function() {
      $.ajax({
        url: this.url,
        dataType: 'json',
        async: true,
        success: function (data) {
          var $table = $('table.stats');
          for (var name in data.children) {
            var item = data.children[name];
            name = name.replace(/\./g, '-');
            var $td = $table.find('#total-words-' + name);
            if (item.total) {
              $td.removeClass('zero');
              $td.addClass('non-zero');
              $td.find('a').html(item.total);
            } else {
              $td.find('a').html('');
              $td.addClass('zero');
              $td.removeClass('non-zero');
            }

            $td = $table.find('#need-translation-' + name);
            var value = item.fuzzy + item.untranslated;
            if (value) {
              $td.removeClass('zero');
              $td.addClass('non-zero');
              $td.find('a').html(value);
            } else {
              $td.find('a').html('');
              $td.addClass('zero');
              $td.removeClass('non-zero');
            }

            var $td = $table.find('#suggestions-' + name);
            if (item.suggestions) {
              $td.removeClass('zero');
              $td.addClass('non-zero');
              $td.find('a').html(item.suggestions);
            } else {
              $td.find('a').html('');
              $td.addClass('zero');
              $td.removeClass('non-zero');
            }

          }

          $table.removeClass('js-not-loaded');
        }
      });
    }
  };

}(jQuery));
