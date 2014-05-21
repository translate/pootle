(function ($) {

  window.PTL = window.PTL || {};

  PTL.reports = {

    init: function () {

      /* Compile templates */
      this.tmpl = {
        results: _.template($('#language_user_activity').html())
      };

      $(document).on('click', '#reports-show', function (e) {
        PTL.reports.user = $('#reports-user').val();
        PTL.reports.update();
      });

      $(document).on('click', '#current-month', function (e) {
        PTL.reports.date_range = [
          moment().date(1),
          moment()
        ];
        PTL.reports.update();

        return false;
      });

      $(document).on('click', '#previous-month', function (e) {
        PTL.reports.date_range = [
          moment().subtract({M:1}).date(1),
          moment().date(1).subtract('days', 1)
        ];

        PTL.reports.update();

        return false;
      });

      $(document).on('keypress', '#reports-user', function (e) {
        if (e.which === 13) {
          PTL.reports.user = $('#reports-user').val();

          PTL.reports.update();
        }
      });
      $(document).on('click', '#user-rates-form input.submit', this.updateRates);
      $(document).on('change', '#id_currency', this.refreshCurrency);

      this.date_range = [moment().date(1), moment()]
      this.user = null;
      $('#user-rates-form').hide();

      PTL.reports.currentRowIsEven = false;

      $.history.init(function (hash) {
        var params = PTL.utils.getParsedHash(hash);

        // Walk through known report criterias and apply them to the
        // reports object
        if ('start' in params && 'end' in params) {
          PTL.reports.date_range = [
            moment(params.start),
            moment(params.end)
          ];
        } else {
          PTL.reports.date_range = [
            moment().date(1),
            moment()
          ];
        }

        PTL.reports.setViewMode(params.mode || 'new');

        if ('user' in params) {
          PTL.reports.user = params.user;
        }
        $('#reports-user').val(PTL.reports.user);

        if (!PTL.reports.compareParams(params)) {
          PTL.reports.buildResults();
        }

        PTL.reports.loadedHashParams = params;
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
      if (PTL.reports.user) {
        return  PTL.reports.date_range.length == 2;
      } else {
        return false;
      }
    },

    update: function () {
      if (PTL.reports.validate()) {
        var newHash = [
          'user=', PTL.reports.user,
          '&start=', PTL.reports.date_range[0].format('YYYY-MM-DD'),
          '&end=', PTL.reports.date_range[1].format('YYYY-MM-DD'),
          '&mode=', PTL.reports.mode
        ].join('');
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
        start: PTL.reports.date_range[0].format('YYYY-MM-DD'),
        end: PTL.reports.date_range[1].format('YYYY-MM-DD'),
        user: PTL.reports.user
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
            $('#id_currency').val(user.currency);
            if (user.currency) {
              $('#user-rates-form .currency').text(user.currency);
            }

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
    }

  };

})(jQuery);

$(function ($) {
  PTL.reports.init();
});
