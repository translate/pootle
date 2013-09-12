(function ($) {

  window.PTL = window.PTL || {};

  PTL.stats = {

    init: function (options) {
      this.url = options.url;
    },

    load: function (callback) {
      $.ajax({
        url: this.url,
        dataType: 'json',
        async: true,
        success: function (data) {
          var $table = $('table.stats');

          function update_progressbar($td, item) {
            var translated = item.total ?
                  Math.round(item.translated / item.total * 100) :
                  100,
                fuzzy = item.total ?
                  Math.round(item.fuzzy / item.total * 100) :
                  0,
                untranslated = 100 - translated - fuzzy,
                $legend = $('<span>').html($td.find('script').text());

            untranslated = untranslated < 0 ? 0 : untranslated;

            $legend.find('.value.translated').text(translated);
            $legend.find('.value.fuzzy').text(fuzzy);
            $legend.find('.value.untranslated').text(untranslated);

            $td.find('table').attr('title', $legend.html());

            function set_td_width($td, w) {
              w === 0 ? $td.hide() : $td.css('width', w + '%').show();
            }
            set_td_width($td.find('td.translated'), translated);
            set_td_width($td.find('td.fuzzy'), fuzzy);
            set_td_width($td.find('td.untranslated'), untranslated);
          }
          update_progressbar($('#progressbar'), data);

          for (var name in data.children) {
            var item = data.children[name],
                code = name.replace(/\./g, '-'),
                $td = $table.find('#total-words-' + code);
            if (item.total) {
              $td.removeClass('zero');
              $td.addClass('non-zero');
              $td.find('a').html(item.total);
            } else {
              $td.find('a').html('');
              $td.addClass('zero');
              $td.removeClass('non-zero');
            }

            var ratio = item.total === 0 ? 1 : item.translated / item.total;
            $table.find('#translated-ratio-' + code).text(ratio);

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

            if (item.lastaction) {
              $td = $table.find('#last-activity-' + code);
              $td.html(item.lastaction.snippet);
              $td.find('.last-action .action-text').show();
            }
          }

          $('body').removeClass('js-not-loaded');

          if (callback) {
            callback(data);
          }
        }
      });
    }
  };

}(jQuery));
