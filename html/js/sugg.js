$(document).ready(function() {

  function clearpath(path) {
    parts = path.split("/");
    return parts[parts.length - 1];
  }

  function geturl(node, action) {
    pofilename = escape($("input[name='store']").val())
    item_sugg_chain = $(node).attr("id").replace(action, "");
    item_sugg = item_sugg_chain.split("-", 1);
    itemid = item_sugg[0];
    url = pofilename + "/" + itemid + "/handlesuggestions/";
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
        newtrans = $(this).siblings("input").attr("value");
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
               //$("#suggestion" + rdata.deleted).remove();
               $("#suggestion" + rdata.deleted).fadeOut(1000);
               /*$(rdata.deleted).animate({ backgroundColor: "#fbc7c7" }, "fast").animate({opacity: "hide"}, "slow");
               $(rdata.deleted).animate({ backgroundColor: "#fbc7c7" }, "fast").animate({opacity: "hide"}, "slow");*/
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

      var reject_others = $(ref).parents(".translate-suggestion-block")
                                .siblings(".translate-suggestion-block");
      if (reject_others.length > 0) {
        var refs = $(".rejectsugg", reject_others);
        data.rejects = getsuggs(refs, "reject");
      }

      handlesuggestions(url, data);

      return false;
      }
  });

});
