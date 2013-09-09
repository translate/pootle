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

          function update_progressbar($td, item) {
            var translated = item.total ? Math.round(item.translated / item.total * 100) : 100;
            var fuzzy = item.total ? Math.round(item.fuzzy / item.total * 100) : 0;
            var untranslated = 100 - translated - fuzzy;
            untranslated = untranslated < 0 ? 0 : untranslated;

            var $legend = $('<span>').html($td.find('script').text());

            $legend.find('.value.translated').text(translated);
            $legend.find('.value.fuzzy').text(fuzzy);
            $legend.find('.value.untranslated').text(untranslated);

            $td.find('table').attr('title', $legend.html());

            function set_td_width($td, w) {
              w == 0 ? $td.hide() : $td.css('width', w + '%').show();
            }
            set_td_width($td.find('td.translated'), translated);
            set_td_width($td.find('td.fuzzy'), fuzzy);
            set_td_width($td.find('td.untranslated'), untranslated);
          }
          update_progressbar($('#progressbar'), data);

          for (var name in data.children) {
            var item = data.children[name];
            var code = name.replace(/\./g, '-');
            var $td = $table.find('#total-words-' + code);
            if (item.total) {
              $td.removeClass('zero');
              $td.addClass('non-zero');
              $td.find('a').html(item.total);
            } else {
              $td.find('a').html('');
              $td.addClass('zero');
              $td.removeClass('non-zero');
            }

            $td = $table.find('#need-translation-' + code);
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

            $td = $table.find('#suggestions-' + code);
            if (item.suggestions) {
              $td.removeClass('zero');
              $td.addClass('non-zero');
              $td.find('a').html(item.suggestions);
            } else {
              $td.find('a').html('');
              $td.addClass('zero');
              $td.removeClass('non-zero');
            }

            $td = $table.find('#progressbar-' + code);
            update_progressbar($td, item);
          }

          $('body').removeClass('js-not-loaded');
        }
      });
    }
  };

}(jQuery));
