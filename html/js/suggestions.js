$(document).ready(function() {

  function getSiblingParams(node) {
    var param = "";
    sibling_inputs = $(node).siblings("input");
    $.each(sibling_inputs, function() {
      param += "&" + this.getAttribute("name") +
               "=" + this.getAttribute("value");
      });
    return param;
  }

  function rejectSuggestions(requestURL, paramsR, refs, accept) {
    $.ajax({
      type: "POST",
      url: requestURL,
      data: paramsR,
      beforeSend: function() {
        $("div#working").show();
      },
      complete: function() {
        $("div#working").hide();
      },
      dataType: "html",
      success: function(d) {
        // Animate suggestion removals
        if (refs.length > 1) {
          $.each(refs, function() {
            $(this).parents(".translate-suggestion").animate({ backgroundColor: "#fbc7c7" }, "fast").animate({opacity: "hide"}, "slow");
            $(this).parents(".translate-suggestion-block").animate({ backgroundColor: "#fbc7c7" }, "fast").animate({opacity: "hide"}, "slow");
            });
        } else {
          $(refs).parents(".translate-suggestion").animate({ backgroundColor: "#fbc7c7" }, "fast").animate({opacity: "hide"}, "slow");
          $(refs).parents(".translate-suggestion-block").animate({ backgroundColor: "#fbc7c7" }, "fast").animate({opacity: "hide"}, "slow");
        }
        // Get item ID
        var itemName = $(".rejectsugg").siblings("input").attr("name");
        var pattern = /\d{1,4}/;
        var itemID = itemName.match(pattern)[0];
        // Retrieve updated references
        $.ajax({
          type: "GET",
          url: "translate.html",
          data: "translate=1&item="+itemID+"&review=1&pofilename="+requestURL,
          dataType: "html",
          success: function(data) {
            // Remove old references
            $("#translate-suggestion-container").children().each(function() {
              $(this).remove();
              });
            // Append updated references
            var updatedSuggestions = $("#translate-suggestion-container", data).children();
            $("#translate-suggestion-container").html(updatedSuggestions);
            // If we're in reviewing mode, append the updated diff for current translation
            var reviewmode = $("#translate-suggestion-container").prev().is("#translate-original-container");
            if (reviewmode) {
              var original = $("#translate-original-container");
              $(".translate-original-block", original).remove();
              original.html($(".translate-original-block", data));
            }
            // If we also want to accept suggestions, go ahead with it
            if (accept != undefined) {
              var ref = $(".acceptsugg");
              // Retrieve updated parameters
              var paramsA = "?review=1&translate=1";
              paramsA += getSiblingParams(ref);
              paramsA += "&" + $(ref).attr("id") + "=!";
              acceptSuggestion(requestURL, paramsA, ref);
            }
            },
          error: function() {
            alert(AJAX_ERROR);
            }
          });
        },
      error: function() {
        alert(AJAX_ERROR);
        }
      });
  }

  function acceptSuggestion(requestURL, params, reference) {
    $.ajax({
      type: "POST",
      url: requestURL,
      data: params,
      dataType: "html",
      beforeSend: function() {
        $("div#working").show();
      },
      complete: function() {
        $("div#working").hide();
      },
      success: function(data) {
        // Animate accepting current suggestion
        var textareas = $("#translate-suggestion-container").siblings("textarea");
        var inputs = $(reference).siblings("input");
        $.each(textareas, function(i) {
          $(this).val(inputs.eq(i).val());
          $(this).animate({ backgroundColor: "#dafda5" }, "fast").animate({ backgroundColor: "#ffffff" }, "slow");
          });
        var currentBlock = $(reference).parents(".translate-suggestion-block");
        currentBlock.animate({opacity: "hide"}, "slow");
        // Remove from the DOM tree
        currentBlock.remove();
        // If we're in reviewing mode, remove the original translation container
        var reviewmode = $("#translate-suggestion-container").prev().is("#translate-original-container");
        if (reviewmode) {
          $("#translate-original-container").remove();
        }
       },
      error: function() {
        alert(AJAX_ERROR);
        }
      });
  }

$("#translate-suggestion-container").click(function(event) {
    if ($(event.target).parent().is(".rejectsugg")) {
      // Save this object reference
      var reference = $(event.target).parent();
      var requestURL = $("input[@name=pofilename]").val();
      // Ideally we could make use of the serialize() method
      // but this isn't a ideal case ;P
      var params = "review=1&translate=1";
      params += getSiblingParams(reference);
      params += "&" + $(reference).attr("id") + "=1";
      // Reject selected suggestion
      rejectSuggestions(requestURL, params, reference, undefined);
      return false;
    }

    if ($(event.target).parent().is(".acceptsugg")) {
      // Save this object reference
      var reference = $(event.target).parent();
      // The url is the po filename itself
      var requestURL = $("input[@name=pofilename]").val();
      var reject_others = $(reference).parents(".translate-suggestion-block").siblings(".translate-suggestion-block");
      // There are suggestions to reject
      if (reject_others.length > 0) {
      // Parameters to reject the remaining suggestions
      var paramsReject = "?review=1&translate=1";
      $.each(reject_others, function() {
        paramsReject += getSiblingParams($(".rejectsugg", this));
        paramsReject += "&" + $(".rejectsugg", this).attr("id") + "=1";
        });
      var refs = reject_others.children(".rejecsugg");
      rejectSuggestions(requestURL, paramsReject, reject_others, true);
      } else { // Just accept this one
        // Parameters to accept this suggestion
        var paramsAccept = "?review=1&translate=1";
        paramsAccept += getSiblingParams(reference);
        paramsAccept += "&" + $(reference).attr("id") + "=1";
        // Accept selected suggestion
        acceptSuggestion(requestURL, paramsAccept, reference);
      }
      return false;
      }
  });

});
