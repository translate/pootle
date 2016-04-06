/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import $ from 'jquery';
import moment from 'moment';
import assign from 'object-assign';
import _ from 'underscore';

import 'jquery-flot';
import 'jquery-flot-stack';
import 'jquery-flot-marks';
import 'jquery-flot-time';
import 'jquery-history';
import 'jquery-serializeObject';

import msg from '../msg';
import utils from '../utils';


const paidTaskTypes = {
  translation: 0,
  review: 1,
  hourlyWork: 2,
  correction: 3,
};


window.PTL = window.PTL || {};

PTL.reports = {

  init(opts) {
    _.defaults(this, opts);

    /* Compile templates */
    const showSummary = (!PTL.reports.freeUserReport &&
                         (PTL.reports.ownReport || PTL.reports.adminReport));
    this.tmpl = {
      results: _.template($('#language_user_activity').html()),
      summary: showSummary ? _.template($('#summary').html()) : '',
      paid_tasks: showSummary ? _.template($('#paid-tasks').html()) : '',
    };

    $(window).resize(() => {
      if (PTL.reports.data !== undefined &&
          PTL.reports.data.daily !== undefined &&
          PTL.reports.data.daily.nonempty) {
        PTL.reports.drawChart();
      }
    });

    if (PTL.reports.adminReport) {
      $(document).on('change', '#reports-user', () => {
        PTL.reports.userName = $('#reports-user').val();
        PTL.reports.update();
      });
      $(document).on('click', '#user-rates-form input.submit', this.updateRates);
      $(document).on('click', '#reports-paid-tasks .js-remove-task', this.removePaidTask);
      $('#reports-user').select2({ data: PTL.reports.users });
    }

    $(document).on('click', '#paid-task-form input.submit', this.addPaidTask);
    $(document).on('change', '#id_currency', this.refreshCurrency);
    $(document).on('change', '#id_task_type', this.onPaidTaskTypeChange);
    $(document).on('keyup paste change blur', '#id_description', this.addPaidTaskValidate);
    $(document).on('keyup paste change', '#id_amount', this.addPaidTaskValidate);
    $(document).on('blur', '#id_amount', this.roundAmount);

    const taskType = parseInt($('#id_task_type').val(), 10);
    this.refreshAmountMeasureUnits(taskType);

    $.history.init((hash) => {
      const params = PTL.reports.params = utils.getParsedHash(hash);

      // Walk through known report criterias and apply them to the
      // reports object
      if ('month' in params) {
        PTL.reports.month = moment(params.month, 'YYYY-MM');
      } else {
        PTL.reports.month = moment(PTL.reports.serverTime, 'YYYY-MM-DD HH:mm:ss');
      }
      if ('username' in params) {
        PTL.reports.userName = params.username;
      }
      PTL.reports.updateMonthSelector();
      $('#reports-user').select2('val', PTL.reports.userName);

      if (!PTL.reports.compareParams(params)) {
        PTL.reports.buildResults();
      }

      PTL.reports.loadedHashParams = params;
      $('#detailed a').attr('href', `${PTL.reports.detailedUrl}?${utils.getHash()}`);
    }, { unescape: true });
  },

  updateRates() {
    const reqData = $('#user-rates-form').serializeObject();
    $('body').spin();
    $.ajax({
      url: PTL.reports.updateUserRatesUrl,
      type: 'POST',
      data: reqData,
      dataType: 'json',
      success(data) {
        if (data.scorelog_count + data.paid_task_count > 0) {
          PTL.reports.buildResults();
        }
        $('#id_effective_from').val('');
        $('body').spin(false);
      },
      error(xhr) {
        $('body').spin(false);
        msg.show({ text: `Error: ${xhr.status}`, level: 'error' });
      },
    });
    return false;
  },

  addPaidTask() {
    const reqData = $('#paid-task-form').serializeObject();
    $('#paid-task-form .submit').prop('disabled', true);

    $.ajax({
      url: PTL.reports.addPaidTaskUrl,
      type: 'POST',
      data: reqData,
      dataType: 'json',
      success(data) {
        if (data.result > 0) {
          $('#id_amount').val(0);
          $('#id_description').val('');
          PTL.reports.buildResults();
        }
      },
      error(xhr) {
        msg.show({ text: `Error: ${xhr.status}`, level: 'error' });
      },
    });
    return false;
  },

  removePaidTask() {
    $.ajax({
      url: PTL.reports.removePaidTaskUrl + $(this).data('id'),
      type: 'DELETE',
      dataType: 'json',
      success() {
        PTL.reports.buildResults();
      },
      error(xhr) {
        msg.show({ text: `Error: ${xhr.status}`, level: 'error' });
      },
    });
    return false;
  },

  refreshCurrency() {
    const currency = $(this).val();
    $('#user-rates-form .currency').text(currency);
    $('#paid-task-form .currency').text(currency);
  },

  onPaidTaskTypeChange() {
    const taskType = parseInt($(this).val(), 10);

    PTL.reports.refreshAmountMeasureUnits(taskType);
    $('#id_paid_task_rate').val(PTL.reports.getRateByTaskType(taskType));
    $('#paid-task-form .currency').text(PTL.reports.user.currency);
  },

  roundAmount() {
    const $this = $(this);
    const amount = $this.val();
    const taskType = parseInt($('#id_task_type').val(), 10);

    if (taskType === paidTaskTypes.translation ||
        taskType === paidTaskTypes.review ||
        taskType === paidTaskTypes.hourlyWork) {
      $this.val(amount > 0 ? amount : 0);
      if (taskType !== paidTaskTypes.hourlyWork) {
        // round if amount is in words (i.e. taskType is translation or review)
        // hours can be fractional
        $this.val(Math.round(amount));
      }
    }
  },

  addPaidTaskValidate() {
    setTimeout(() => {
      const amount = $('#id_amount').val();
      const description = $('#id_description').val();
      const taskType = parseInt($('#id_task_type').val(), 10);

      if (description === '' || amount <= 0 &&
          taskType !== paidTaskTypes.correction) {
        $('#paid-task-form .submit').prop('disabled', true);
      } else {
        $('#paid-task-form .submit').prop('disabled', false);
      }
    }, 100);
  },

  refreshAmountMeasureUnits(taskType) {
    $('#paid-task-form .units').hide();
    $(`#paid-task-form .units.task-${taskType}`).show();
  },

  getRateByTaskType(taskType) {
    if (taskType === paidTaskTypes.translation) {
      return PTL.reports.user.rate;
    }
    if (taskType === paidTaskTypes.review) {
      return PTL.reports.user.review_rate;
    }
    if (taskType === paidTaskTypes.hourlyWork) {
      return PTL.reports.user.hourly_rate;
    }

    return 1;
  },

  validate() {
    if (!!PTL.reports.userName) {
      // month should be defined correctly
      return moment(PTL.reports.month).date() === 1;
    }
    return false;
  },

  update() {
    if (PTL.reports.validate()) {
      const newHash = $.param({
        username: PTL.reports.userName,
        month: PTL.reports.month.format('YYYY-MM'),
      });
      $.history.load(newHash);
    } else {
      msg.show({ text: 'Wrong input data', level: 'error' });
    }
  },

  compareParams(params) {
    let result = true;

    if (PTL.reports.loadedHashParams) {
      for (const p in params) {
        if (!params.hasOwnProperty(p)) {
          continue;
        }

        result &= params[p] === PTL.reports.loadedHashParams[p];
      }
    } else {
      result = false;
    }

    return result;
  },

  drawChart() {
    $.plot($('#daily-chart'),
      PTL.reports.dailyData.data,
      {
        series: {
          stack: true,
          lines: { show: false, steps: false },
          bars: {
            show: true,
            barWidth: 1000 * 60 * 60 * 24,
            align: 'center',
          },
        },
        xaxis: {
          min: parseInt(PTL.reports.dailyData.min_ts, 10) - 1000 * 60 * 60 * 12,
          max: parseInt(PTL.reports.dailyData.max_ts, 10) - 1000 * 60 * 60 * 12,
          minTickSize: [1, 'day'],
          mode: 'time',
          timeformat: '%b %d, %a',
        },
        yaxis: {
          max: PTL.reports.dailyData.max_day_score,
        },
        colors: ['#66bb66', '#99ccff', '#ffcc33'],
      }
    );
  },

  getPaidTaskSummaryItem(type, rate, summary) {
    if (!summary) {
      return null;
    }

    for (const index in summary) {
      if (summary[index].rate === rate && summary[index].type === type) {
        return summary[index];
      }
    }

    return null;
  },

  processData(origData) {
    let translatedTotal = 0;
    let reviewedTotal = 0;
    let suggestedTotal = 0;
    let scoreDeltaTotal = 0;
    let translatedFloorTotal = 0;

    const data = assign({}, origData);
    data.paid_task_summary = [];

    for (const index in data.paid_tasks) {
      if (!data.paid_tasks.hasOwnProperty(index)) {
        continue;
      }

      const task = data.paid_tasks[index];
      const item = PTL.reports.getPaidTaskSummaryItem(task.type, task.rate,
                                                      origData.paid_task_summary);

      task.datetime = moment(task.datetime, 'YYYY-MM-DD hh:mm:ss').format('MMMM D, HH:mm');
      if (item !== null) {
        item.amount += task.amount;
      } else {
        data.paid_task_summary.push({
          period: PTL.reports.month.format('MMMM, YYYY'),
          type: task.type,
          amount: task.amount,
          action: task.action,
          rate: task.rate,
        });
      }
    }

    for (const index in data.grouped) {
      if (!data.grouped.hasOwnProperty(index)) {
        continue;
      }

      const row = data.grouped[index];
      const floor = parseInt(row.translated, 10);

      row.remainder = row.translated - floor;
      translatedTotal += row.translated;
      reviewedTotal += row.reviewed;
      suggestedTotal += row.suggested;
      scoreDeltaTotal += row.score_delta;
      translatedFloorTotal += floor;
      row.translated = floor;
    }

    translatedTotal = Math.round(translatedTotal);
    scoreDeltaTotal = Math.round(scoreDeltaTotal * 100) / 100;
    data.groupedSuggestedTotal = suggestedTotal;
    data.groupedTranslatedTotal = translatedTotal;
    data.groupedReviewedTotal = reviewedTotal;
    data.groupedScoreDeltaTotal = scoreDeltaTotal;
    let delta = translatedTotal - translatedFloorTotal;

    if (delta > 0) {
      const remainders = data.grouped.slice(0);
      remainders.sort((a, b) => {
        let rv;
        if (b.remainder > a.remainder) {
          rv = 1;
        } else if (b.remainder < a.remainder) {
          rv = -1;
        } else {
          rv = 0;
        }
        return rv;
      });

      let i = 0;
      while (delta > 0) {
        remainders[i].translated += 1;
        i++;
        delta--;
      }
    }

    return data;
  },

  buildResults() {
    const reqData = {
      month: PTL.reports.month.format('YYYY-MM'),
      username: PTL.reports.userName,
    };

    $('body').spin();
    $.ajax({
      url: 'activity',
      data: reqData,
      dataType: 'json',
      success(data) {
        PTL.reports.serverTime = data.meta.now;
        PTL.reports.now = moment(data.meta.now, 'YYYY-MM-DD HH:mm:ss');
        PTL.reports.month = moment(data.meta.month, 'YYYY-MM');

        const processedData = PTL.reports.processData(data);
        PTL.reports.data = processedData;

        $('#reports-results').empty();
        $('#reports-results').html(PTL.reports.tmpl.results(PTL.reports.data)).show();
        $('#js-breadcrumb-user').text(data.meta.user.formatted_name).show();
        const showChart = data.daily !== undefined && data.daily.nonempty;
        $('#reports-activity').toggle(showChart);
        if (showChart) {
          PTL.reports.dailyData = data.daily;
          PTL.reports.drawChart();
        }

        const permalinkArgs = {
          username: data.meta.user.username,
          month: data.meta.month,
          task: '',
        };
        processedData.meta.admin_permalink = [
          data.meta.admin_permalink, $.param(permalinkArgs),
        ].join('#');

        if (PTL.reports.adminReport || !PTL.reports.freeUserReport &&
            PTL.reports.ownReport) {
          const ctx = {
            paidTaskTypes,
            data: processedData,
          };
          $('#reports-paid-tasks').html(PTL.reports.tmpl.paid_tasks(ctx));
          ctx.data.total = 0;
          for (const i in ctx.data.summary) {
            if (!ctx.data.summary.hasOwnProperty(i)) {
              continue;
            }

            const row = ctx.data.summary[i];
            row.subTotal = Math.round(row.amount) * row.rate;
            row.subTotal = +row.subTotal.toFixed(2);
            ctx.data.total += row.subTotal;
          }
          for (const i in ctx.data.paid_task_summary) {
            if (!ctx.data.paid_task_summary.hasOwnProperty(i)) {
              continue;
            }

            const row = ctx.data.paid_task_summary[i];
            row.subTotal = row.amount * row.rate;
            ctx.data.total += row.subTotal;
          }
          $('#reports-summary').html(PTL.reports.tmpl.summary(ctx));
        }

        if (data.meta.user) {
          PTL.reports.user = data.meta.user;
          PTL.reports.updateMonthSelector();
          PTL.reports.setPaidTaskDate();
          PTL.reports.addPaidTaskValidate();

          $('#reports-params').show();
          $('#detailed').show();

          $('#id_username').val(PTL.reports.user.username);
          $('#id_user').val(PTL.reports.user.id);
          $('#id_rate').val(PTL.reports.user.rate);
          $('#id_review_rate').val(PTL.reports.user.review_rate);
          $('#id_hourly_rate').val(PTL.reports.user.hourly_rate);

          const taskType = parseInt($('#id_task_type').val(), 10);
          $('#id_paid_task_rate').val(PTL.reports.getRateByTaskType(taskType));

          if (PTL.reports.user.currency) {
            $('#id_currency').val(PTL.reports.user.currency);
          }
          $('#user-rates-form .currency').text($('#id_currency').val());

          if ('task' in PTL.reports.params) {
            const task = document.querySelector(`.task${PTL.reports.params.task}`);
            if (!!task) {
              task.classList.add('highlight');
              setTimeout(() => {
                task.scrollIntoView();
              }, 0);
            } else {
              msg.show({ text: 'Task with this ID not found', level: 'error' });
            }
          }

          $('#forms').show();
        } else {
          $('#forms').hide();
        }
        $('body').spin(false);
      },
      error(xhr) {
        $('body').spin(false);
        msg.show({
          text: `Error: ${$.parseJSON(xhr.responseText)}`,
          level: 'error',
        });
      },
    });
  },

  dateRangeString(d1, d2, showYear = true) {
    const m1 = moment(d1, 'YYYY-MM-DD HH:mm:ss');
    const m2 = moment(d2, 'YYYY-MM-DD HH:mm:ss');

    if (m1.year() === m2.year()) {
      if (m1.month() === m2.month()) {
        if (m1.date() === m2.date()) {
          return m1.format(showYear ? 'MMMM D, YYYY' : 'MMMM D');
        }

        return [
          m1.format('MMMM D'),
          ' &mdash; ',
          m2.date(),
          showYear ? m2.format(', YYYY') : '',
        ].join('');
      }

      return [
        m1.format('MMMM D'),
        ' &mdash; ',
        m2.format(showYear ? 'MMMM D, YYYY' : 'MMMM D'),
      ].join('');
    }

    return [
      m1.format('MMMM D, YYYY'),
      ' &mdash; ',
      m2.format('MMMM D, YYYY'),
    ].join('');
  },

  formatDate(d) {
    const m = moment(d, 'YYYY-MM-DD HH:mm:ss');
    return m.format('MMM, D');
  },

  updateMonthSelector() {
    $('.js-month').each(function setLink() {
      const $el = $(this);
      let link = PTL.reports.adminReport ? `#username=${PTL.reports.userName}&` : '#';

      if ($el.hasClass('js-previous')) {
        link += `month=${PTL.reports.month.clone().subtract({ M: 1 }).format('YYYY-MM')}`;
      }
      if ($el.hasClass('js-next')) {
        link += `month=${PTL.reports.month.clone().add({ M: 1 }).format('YYYY-MM')}`;
      }
      $el.attr('href', link);
    });
    $('.dates .selected').html(PTL.reports.month.format('MMMM, YYYY'));
  },

  setPaidTaskDate() {
    let datetime;
    // set paid task datetime
    if (PTL.reports.now >= PTL.reports.month.clone().add({ M: 1 })) {
      datetime = PTL.reports.month.clone().add({ M: 1 }).subtract({ s: 1 });
    } else if (PTL.reports.now <= PTL.reports.month) {
      datetime = PTL.reports.month;
    } else {
      datetime = PTL.reports.now;
    }
    $('#paid-task-form .month').html(datetime.format('MMMM D, YYYY'));
    $('#paid-task-form #id_datetime').val(datetime.format('YYYY-MM-DD HH:mm:ss'));
  },

};
