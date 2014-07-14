(function ($) {

  window.PTL = window.PTL || {};

  PTL.reports = {

    init: function () {

      /* Compile templates */
      this.tmpl = {
        results: _.template($('#language_user_activity').html()),
        month_selector: _.template($('#month_selector').html()),
      };

      $(document).on('click', '.month-selector', function (e) {
        var offset = parseInt($(this).data('month-offset')),
            dateRange = PTL.reports.getDateRangeByOffset(offset);

        PTL.reports.date_range = date_range;
        PTL.reports.update();

        return false;
      });

      $(document).on('change', '#reports-user', function (e) {
        PTL.reports.userName = $('#reports-user').val();
        PTL.reports.update();
      });
      $(document).on('click', '#user-rates-form input.submit', this.updateRates);
      $(document).on('change', '#id_currency', this.refreshCurrency);

      this.now = moment();

      for (var i=3; i>= 0; i--) {
        var month = this.tmpl.month_selector({
          'month_offset': i,
          'month': this.now.clone().subtract({M:i}).format('MMMM'),
        });
        $('#reports-params .dates ul').append(month);
      }

      this.date_range = [this.now.clone().date(1), this.now.clone()]
      this.user = null;
      $('#user-rates-form').hide();
      $('#reports-user').select2({'data': users});

      PTL.reports.currentRowIsEven = false;

      $.history.init(function (hash) {
        var params = PTL.utils.getParsedHash(hash),
            detailed = $('#detailed a').attr('href').split('?')[0];

        // Walk through known report criterias and apply them to the
        // reports object
        if ('start' in params && 'end' in params) {
          PTL.reports.date_range = [
            moment(params.start),
            moment(params.end)
          ];
        } else {
          PTL.reports.date_range = [
            PTL.reports.now.clone().date(1),
            PTL.reports.now.clone()
          ];
        }
        PTL.reports.selectMonth();
        PTL.reports.setViewMode(params.mode || 'new');

        if ('username' in params) {
          PTL.reports.userName = params.username;
        }
        $('#reports-user').select2('val', PTL.reports.userName);

        if (!PTL.reports.compareParams(params)) {
          PTL.reports.buildResults();
        }

        PTL.reports.loadedHashParams = params;
        $('#detailed a').attr('href', detailed + '?' + PTL.utils.getHash());
      }, {'unescape': true});

      $(document).on('change', '#reports-viewmode select', function (e) {
        PTL.reports.setViewMode($(this).val());
        PTL.reports.update();
        return false;
      });

    },

    updateRates: function () {
      var reqData = $('#user-rates-form').serializeObject(),
          submitUrl = l('/admin/reports/update_user_rates');

      $.ajax({
        url: submitUrl,
        type: 'POST',
        data: reqData,
        dataType: 'json',
        success: function (data) {
          if (data.updated_count > 0) {
            PTL.reports.buildResults();
          }
        },
        error: function (xhr, s) {
          alert('Error status: ' + xhr.status);
        }
      });
      return false;
    },

    refreshCurrency: function (e) {
      var currency = $(this).val();
      $('#user-rates-form .currency').text(currency);
    },

    setViewMode: function (mode) {
      PTL.reports.mode = mode;
      $('#reports-viewmode select').val(mode);
      $('#reports-results').attr('class', mode);
    },

    validate: function () {
      if (PTL.reports.userName) {
        return  PTL.reports.dateRange.length == 2;
      }
      return false;
    },

    update: function () {
      if (PTL.reports.validate()) {
        var newHash = $.param({
          'username': PTL.reports.userName,
          'start': PTL.reports.dateRange[0].format('YYYY-MM-DD'),
          'end': PTL.reports.dateRange[1].format('YYYY-MM-DD'),
        });
        $.history.load(newHash);
      } else {
        alert('Wrong input data');
      }
    },

    compareParams: function (params) {
      var result = true;

      if (PTL.reports.loadedHashParams) {
        for (var p in params) {
          result &= params[p] == PTL.reports.loadedHashParams[p];
        }
      } else {
        result = false;
      }

      return result;
    },

    buildResults: function () {
      var reqData = {
        start: PTL.reports.dateRange[0].format('YYYY-MM-DD'),
        end: PTL.reports.dateRange[1].format('YYYY-MM-DD'),
        username: PTL.reports.userName
      };

      $.ajax({
        url: 'activity',
        data: reqData,
        dataType: 'json',
        async: true,
        success: function (data) {
          $('#reports-results').empty();
          $('#reports-results').html(PTL.reports.tmpl.results(data));
          PTL.reports.setViewMode(PTL.reports.mode);
          if (data.meta.user) {
            var user = data.meta.user;

            $('#id_username').val(user.username);
            $('#id_rate').val(user.rate);
            $('#id_review_rate').val(user.review_rate);

            if (user.currency) {
              $('#id_currency').val(user.currency);
            }
            $('#user-rates-form .currency').text($('#id_currency').val())
            $('#user-rates-form').show();
          }
        },
        error: function (xhr, s) {
          alert('Error status: ' + $.parseJSON(xhr.responseText));
        }
      });
    },

    dateRangeString: function (d1, d2, showYear) {
      var res = '',
          m1 = moment(d1),
          m2 = moment(d2);

      showYear = showYear || true;

      if (m1.year() == m2.year()) {
        if (m1.month() == m2.month()) {
          if (m1.date() == m2.date()) {
            return m1.format(showYear ? 'MMMM D, YYYY' : 'MMMM D');
          } else {
            return [
              m1.format('MMMM D'),
              ' &mdash; ',
              m2.date(),
              showYear ? m2.format(', YYYY') : ''
            ].join('');
          }
        } else {
          return [
            m1.format('MMMM D'),
            ' &mdash; ',
            m2.format(showYear ? 'MMMM D, YYYY' : 'MMMM D')
          ].join('');
        }
      } else {
        return [
          m1.format('MMMM D, YYYY'),
          ' &mdash; ',
          m2.format('MMMM D, YYYY')
        ].join('');
      }
    },

    formatDate: function (d) {
      var m = moment(d);
      return m.format('MMM, D');
    },

    cycleEvenOdd: function () {
      PTL.reports.currentRowIsEven = !PTL.reports.currentRowIsEven;

      if (PTL.reports.currentRowIsEven) {
        return 'even';
      } else {
        return 'odd';
      }
    },

    resetRowStyle: function () {
      PTL.reports.currentRowIsEven = false;
    },

    selectMonth: function () {
      var dr = PTL.reports.dateRange;
      $('.month-selector').each(function () {
        var $el = $(this),
            offset = parseInt($el.data('month-offset')),
            dateRange = PTL.reports.getDateRangeByOffset(offset);

        $el.removeClass('selected');
        if (dr[0].format('YYYY-MM-DD') === dateRange[0].format('YYYY-MM-DD') &&
            dr[1].format('YYYY-MM-DD') === dateRange[1].format('YYYY-MM-DD')) {
          $el.addClass('selected');
        }
      });
    },

    getDateRangeByOffset: function (offset) {
      var start = PTL.reports.now.clone().subtract({M: offset}).date(1),
          end = PTL.reports.now.clone();

      if (offset > 0) {
        end = PTL.reports.now.clone().subtract({M: offset}).date(1)
                             .add({M: 1}).subtract('days', 1);
      }

      return [start, end];
    }

  };

})(jQuery);

$(function ($) {
  PTL.reports.init();
});
