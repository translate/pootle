$(document).ready(function() {

/* Pootle namespace */
$.pootle = {};

/*
 * FOCUS
 */

  // Set initial focus on page load
  var initialFocus = $(".translate-original-focus textarea");
  $.pootle.focusedElement = initialFocus.get(0);
  $.pootle.focusedElement.focus();

  // Update focus when appropriate
  $(".focusthis").focus(function(e) {
    $.pootle.focusedElement = e.target;
  });


/*
 * REPLACEMENTS
 */

  // Write TM results into the currently focused element
  $(".writetm").click(function() {
    var tmtext = $(".tm-translation", this).html();
    $($.pootle.focusedElement).replaceSelection(tmtext);
  });

  // Write special chars into the currently focused element
  $(".writespecial").click(function() {
    var specialtext = $(this).html();
    $($.pootle.focusedElement).replaceSelection(specialtext);
  });


/*
 * COPY ORIGINAL TRANSLATION
 */

  $(".copyoriginal").click(function() {
    var transid = $(this).parent().parent().attr("id");
    var elementNumber = transid.replace("trans", "")
    var enelement = $("#orig-pure" + elementNumber + "-0");
    var envalue = enelement.val().replace("\n", "\\n\n", "g").replace("\t", "\\t", "g");

    // no plurals
    var trelement = $("#areatrans" + elementNumber);
    if (trelement.length != 0) {
      trelement.val(envalue);
      trelement.focus();
      return;
    }

    // plurals
    var trelements = $("[id^=areatrans" + elementNumber + "-]");
    var enplelement = $("#orig-pure" + elementNumber + "-1");
    var enplvalue = enplelement.val().replace("\n", "\\n\n", "g").replace("\t", "\\t", "g");
    $.each(trelements, function(i) {
      newval = i == 0 ? envalue : enplvalue;
      $(this).val(newval);
      $(this).focus();
    });
  });


/*
 * UNFUZZY
 */

/*
 *  For future enhancements like multiple edit boxes, please note
 *  that the selector is based on a class, so it must be modified
 *  to get the textarea's element ID and select the checkbox to
 *  remove the "checked" attribute according to that value.
 */
  var keepstate = false;
  $("textarea.translation").bind("keyup blur", function() {
    if (!keepstate && $(this).attr("defaultValue") != $(this).val()) {
      var checkbox = $("input.fuzzycheck[checked]");
      checkbox.removeAttr("checked");
      checkbox.parent().animate({ backgroundColor: "#dafda5 !important" }, "slow")
                       .animate({ backgroundColor: "#ffffff !important" }, "slow");
      $("textarea.translate-translation-fuzzy").each(function () {
        $(this).removeClass("translate-translation-fuzzy");
      });
      keepstate = true;
    }
  });
  $("input.fuzzycheck").click(function() {
    keepstate = true;
    $(this).parent().parent().parent().find("textarea").toggleClass("translate-translation-fuzzy");
  });


/*
 * SUGGESTIONS
 */

/* INLINE SUGGESTIONS */

  $(".sugglink").click(function(event){
      event.preventDefault();
      $(this).siblings(".suggestions").children(".sugglist").toggle();
  });
  $(".sugglist").hide();

/* REVIEWING SUGGESTIONS */

  function geturl(node, action) {
    pofilename = escape($("input[name='path']").val())
    item_sugg_chain = $(node).attr("id").replace(action, "");
    item_sugg = item_sugg_chain.split("-", 1);
    itemid = item_sugg[0];
    url = pofilename + "/review/" + itemid + "/";
    return url;
  }

  /*
   * Returns an array (list) of suggestion objects
   */
  function getsuggs(nodes, action) {
    var suggs = [];
    $.each(nodes, function() {
        item_sugg_chain = $(this).attr("id").replace(action, "");
        item_sugg = item_sugg_chain.split("-", 2);
        suggid = item_sugg[1];
	newtrans = $(this).siblings("input").map(function() {
		return $(this).attr("value");
	    }).get();
        sugg = {id: suggid, newtrans: newtrans};
        suggs.push(sugg);
        });
    return suggs;
  }

  function handlesuggestions(url, data) {
    $.post(url,
           {data: JSON.stringify(data)},
           function(rdata) {
             $("#response").remove();
             if (rdata.status == "success") {
               // Remove processed suggestion
               $.each(rdata.del_ids, function() {
                 var deleted = this[0] + "-" + this[1];
                 $("#suggestion" + deleted).fadeOut(500);
               });
               // If it's an accept, then update the textareas
               if (rdata.hasOwnProperty("accepted_id")) {
                 var textareas = $("#translate-suggestion-container").siblings("textarea");
                 var accepted= rdata.accepted_id[0] + "-" + rdata.accepted_id[1];
                 var inputs = $("#suggestion" + accepted + " .translate-suggestion").children().siblings("input");
                 $.each(textareas, function(i) {
                   $(this).val(inputs.eq(i).val());
                 });
               }
               // If there are no more suggestions left, remove
               // the current translation block.
               if (!rdata.diffs.hasOwnProperty("0")) {
                 $("#translate-original-container").fadeOut(500);
               }
               // Update current diff otherwise
               else {
                 var current = $("#translate-original-container .translate-original-block");
                 var forms = rdata.diffs;
                 $.each(current, function() {
                   var insertat = $("div", this);
                   $.each(forms, function() {
                     $(insertat).html(this.diff);
                   });
                 });
               }
             }
             $("div#translate-suggestion-container:first").prepend(
              '<h2 id="response">' + rdata.message + '</h2>'
              );
           }, "json");
  }

  $("#translate-suggestion-container").click(function(event) {
    if ($(event.target).parent().is(".rejectsugg")) {
      var data = {}
      var ref = $(event.target).parent();
      var url = geturl(ref, "reject");
      data.rejects = getsuggs(ref, "reject");

      handlesuggestions(url, data);

      return false;
    }

    if ($(event.target).parent().is(".acceptsugg")) {
      var data = {}
      var ref = $(event.target).parent();
      var url = geturl(ref, "accept");
      data.accepts = getsuggs(ref, "accept");

      handlesuggestions(url, data);

      return false;
      }
  });

});
