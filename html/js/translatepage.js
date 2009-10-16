$(document).ready(function() {

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
    pofilename = escape($("input[name='store']").val())
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
               $.each(rdata.del_ids, function() {
                 var deleted = this[0] + "-" + this[1];
                 $("#suggestion" + deleted).fadeOut(1000);
               });
             }
             $("div#translate-suggestion-container:first").prepend(
              '<h1 id="response">' + rdata.message + '</h1>'
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
