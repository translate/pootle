/*
 * Zoom-related variables and handler functions
 */

// global variable that stores current zoom level
var pageZoom = 0;

// converts pageZoom value to an appropriate class name string
function zoomClassName() {
  if (pageZoom < 0) {
    return "zoom-out-" + (pageZoom * -1);
  } else if (pageZoom > 0) {
    return "zoom-in-" + pageZoom;
  } else {
    return "";
  }
}

// initializes zoom and sets up related shortcuts on document load
function initZoom() {
  pageZoom = $.cookie('pageZoom');

  $(document.body).addClass(zoomClassName());

  shortcut.add('ctrl+shift+insert', function () {
    zoom(-1);
  });

  shortcut.add('ctrl+shift+home', function () {
    zoom(0);
  });

  shortcut.add('ctrl+shift+page_up', function () {
    zoom(1);
  });
}

// changes zoom and updates class name of a document body
function zoom(v) {
  var oldClassName = zoomClassName();

  if (v == -1) {
    if (pageZoom == -2) {
      return; // minimum zoom level reached
    }
    pageZoom--;
  } else if (v == 1) {
    if (pageZoom == 2) {
      return; // maximum zoom level reached
    }
    pageZoom++;
  } else if (v == 0) {
    pageZoom = 0;
  }

  $.cookie('pageZoom', pageZoom, {path: '/'});

  $(document.body).removeClass(oldClassName).addClass(zoomClassName());
}

/*
 * Search control helper
 */

$(document).ready(function ($) {
  /* Search input text */
  var focused = { color: "#000" },
      unfocused = { color: "#aaa" };

  $('label.inputHint').each(function () {
    var initial,
        search = false,
        label = $(this),
        input = $('#' + label.attr('for'));

    if (input.prop("defaultValue")) {
      initial = input.prop("defaultValue");
      search = true;
    } else {
      initial = label.hide().text().replace(':', '');
    }

    input.focus(function () {
      input.css(focused);

      if (input.val() == initial && !search) {
        input.val('');
      }
    }).blur(function () {
      if (input.val() == '') {
        input.val(initial).css(unfocused);
      } else if (search && input.val() == initial) {
        input.css(unfocused);
      }
    }).css(unfocused).val(initial);
  });

  /* Dropdown toggling */
  $("a.advancedlink").click(function (event) {
    event.preventDefault();
    $("div.advancedsearch").slideToggle();
  }).toggle(function () {
    $("img.togglesearch").toggle();
  }, function () {
    $("img.togglesearch").toggle();
  });

  /* Collapsing functionality */
  $(document).on("click", ".collapse", function (e) {
    e.preventDefault();
    $(this).siblings(".collapsethis").slideToggle("fast");

    if ($("textarea", $(this).next("div.collapsethis")).length) {
      $("textarea", $(this).next("div.collapsethis")).focus();
    }
  });

  /* Fancybox on links */
  $(document).on("click", "a.fancybox", function (e) {
    e.preventDefault();
    $.fancybox({'href': $(e.target).attr('href'), 'type': 'ajax'});
  });

  /* Path summary */
  $(document).on("click", "#js-path-summary", function (e) {
    e.preventDefault();
    var node = $("#" + $(this).data('target')),
        icon = $(this),
        data = node.data();

    function hideShow() {
      node.slideToggle('slow', 'easeOutQuad', function () {
        oldClass = data.collapsed ? 'icon-expand' : 'icon-collapse';
        newClass = data.collapsed ? 'icon-collapse' : 'icon-expand';
        icon.removeClass(oldClass).addClass(newClass);
        node.data('collapsed', !data.collapsed);
      });
    }

    if (data.loaded) {
      hideShow();
    } else {
      var url = $(this).attr('href');
      $.ajax({
        url: url,
        success: function (data) {
          node.html(data).hide();
          node.data('loaded', true);
          hideShow();
        },
        beforeSend: function () {
          node.spin();
        },
        complete: function () {
          node.spin(false);
        },
      });
    }
  });

  /* Overview actions */
  $(document).on("click", ".js-overview-actions-upload", function (e) {
      $.fancybox("#upload");
  });

  /* Generic toggle */
  $(document).on("click", ".js-toggle", function (e) {
    e.preventDefault();
    var target = $(this).attr("href") || $(this).data("target");
    $(target).toggle();
  });

});
