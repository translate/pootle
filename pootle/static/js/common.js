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
  $('html').ajaxSend(function (event, xhr, settings) {
    // FIXME: Can't we use $.cookie() here?
    function getCookie(name) {
      var cookieValue = null;

      if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');

        for (var i = 0; i < cookies.length; i++) {
          var cookie = jQuery.trim(cookies[i]);

          // Does this cookie string begin with the name we want?
          if (cookie.substring(0, name.length + 1) == (name + '=')) {
            cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
            break;
          }
        }
      }
      return cookieValue;
    }

    if (!(/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url))) {
      // Only send the token to relative URLs i.e. locally.
      xhr.setRequestHeader("X-CSRFToken", getCookie('csrftoken'));
    }
  });

  /* Search input text */
  var focused = { color: "#000" }
  var unfocused = { color: "#aaa" }

  $('label.inputHint').each(function () {
    var label = $(this);
    var input = $('#' + label.attr('for'));

    if (input.attr("defaultValue")) {
      var initial = input.attr("defaultValue");
      var search = true;
    } else {
      var initial = label.hide().text().replace(':', '');
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

  cookieName = "hide_description";
  cookieOptions = {path: '/', expires: 15};

  /* Show/hide descriptions */
  if ($.cookie(cookieName) == "yes") {
    $('.intro, #edit_settings, #hide_description, #show_description').toggle();
  }

  $('#hide_description, #show_description').click(function(e) {
    $('#edit_settings, #hide_description, #show_description').toggle();
    $('.intro,').slideToggle();

    if ($.cookie(cookieName) == "yes") {
        $.cookie(cookieName, "no", cookieOptions);
    } else {
        $.cookie(cookieName, "yes", cookieOptions);
    }

  });

  /* Directory summary */
  $(document).on("click", ".js-directory-summary", function (e) {
    e.preventDefault();
    var node = $(".js-directory-summary-more"),
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
      var url = l("dir_summary.html");
      $.ajax({
        url: url,
        success: function (data) {
          node.html(data).hide();
          node.data('loaded', true);
          hideShow();
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
    var target = $(this).attr("href") || $(this).data("target");
    $(target).toggle();
  });

});
