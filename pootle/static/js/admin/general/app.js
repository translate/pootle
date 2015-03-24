/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

'use strict';

var $ = require('jquery');

require('jquery-utils');


/* Sliding table within admin dashboard */
var slideTable = function (event) {
  event.preventDefault();
  var node = $("#" + $(event.target).data('target'));

  $.ajax({
    url: l('/admin/more-stats/'),
    dataType: 'json',
    success: function (data) {
      var newstats = '';
      $(data).each(function () {
        newstats += '<tr><th scope="row">' + this[0] + '</th>'
                    + '<td class="stats-number">' + this[1] + '</td></tr>';
      });
      node.append(newstats);
      node.slideDown("fast");
      node.next("tbody").remove();
    },
    beforeSend: function () {
      $(document).off("click", ".slide", slideTable);
      node.spin();
    },
    complete: function () {
      node.spin(false);
    },
    error: function () {
      $(document).on("click", ".slide", slideTable);
    }
  });
};

/* Sets background color to table rows when checking delete selects */
var setDeleteBg = function (e) {
  $(this).parents("tr").toggleClass("delete-selected",
                                    $(e.target).is(":checked"));
};


/* Sets background color to table rows when checking standard selects */
var setSelectedBg = function (e) {
  if (!$(this).parent().siblings("td[class!=DELETE]")
                       .find("input[type=checkbox][checked]").length) {
    $(this).parents("tr").toggleClass("other-selected",
                                      $(e.target).is(":checked"));
  }
};



/* Selects all checkboxes */
var selectAll = function (e) {
  var className = e.target.id.split('-').reverse()[0];
  $("td." + className + " input").prop("checked",
                                       $(e.target).is(":checked"));
  $("td." + className + " input").change();
};


var commonAdmin = {

  init: function () {
    $(document).on('click', '.slide', slideTable);

    $(document).on('change', 'td.DELETE input[type=checkbox]', setDeleteBg);
    $(document).on('change', 'td[class!=DELETE] input[type=checkbox]',
                   setSelectedBg);

    $(document).on('click', 'th input', selectAll);
  }

};


$(function () {
  commonAdmin.init();
});
