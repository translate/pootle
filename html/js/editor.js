$(document).ready(function() {

    // Ugly hack to avoid JS templates from being interpreted by Django.
    var stext = $("script[type=text/x-jquery-template]").text();
    stext = stext.replace(/\[\[/g, "{{").replace(/\]\]/g, "}}");
    $("script[type=text/x-jquery-template]").text(stext);

    units = {};

    $(document).ajaxStart(function() {
      $("#activity").show();
    });
    $(document).ajaxStop(function() {
      $("#activity").fadeOut("slow");
    });

    /*
     * Sets the view unit for unit 'uid'
     */
    var get_view_unit = function(store, uid, async) {
      var async = async == undefined ? false : async;
      if (units[uid] == undefined) {
        var view_url = l(store + '/view/' + uid);
        $.ajax({
          url: view_url,
          dataType: 'json',
          async: async,
          success: function(data) {
            if (data.success) {
              units[uid] = data.unit;
            } else {
              // TODO: provide a proper error message and not an alert
              alert("Something went wrong");
              return false;
            }
          }
        });
      }
    };

    var display_unit_view = function(store, uid) {
      get_view_unit(store, uid);
      var unit = units[uid];
      var where = $("tr#row" + uid);
      where.children().fadeOut("slow").remove();
      $("#unit_view").tmpl(unit).fadeIn("slow").appendTo(where);
    };

    /*
     * Sets the edit view for unit 'uid'
     */
    var get_edit_unit = function(store, uid) {
      var edit_url = l(store + '/edit/' + uid);
      var where = $("tr#row" + uid);
      where.children().remove();
      where.load(edit_url).hide().fadeIn("slow");
      $("#active_uid").text(uid);
      window.location.hash = "/u/" + uid;
    };

    $("a[id^=editlink]").live("click", function(e) {
      e.preventDefault();
      if (!$(this).parent().next("td").hasClass("translate-full")) {
        // Retrieve unit i+1, if any
        var m = $(this).attr("id").match(/editlink([0-9]+)/);
        if (m) {
          var uid = m[1];
          var store = $("div#store").text();
          var active_uid = $("#active_uid").text();
          display_unit_view(store, active_uid);
          get_edit_unit(store, uid);
        }
      }
    });

    $("a[id^=editlink]").ajaxComplete(function() {
      var maxheight = $(window).height() * 0.3;
      $('textarea.expanding').TextAreaExpander('10', maxheight);
      $.scrollTo('td.translate-full', {offset: {top:-100}});
      $(".focusthis").focus();
    });
});
