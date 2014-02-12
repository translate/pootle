(function ($) {

  window.PTL = window.PTL || {};

  PTL.captcha = {

    display: function (html) {
      $.magnificPopup.open({
        items: {
          src: html,
          type: 'inline'
        },
        focus: '#id_captcha_answer'
      });
    },

    onError: function (xhr, errorFn) {
      if (xhr.status == 402) {
        PTL.captcha.display(xhr.responseText);
      } else {
        PTL.utils.executeFunctionByName(errorFn, window, xhr);
      }
    }

  };

}(jQuery));


$(document).on('submit', '#js-captcha', function (e) {
  e.preventDefault();
  var $form = $(this),
      reqData = $form.serializeObject(),
      successFn = reqData.sfn,
      errorFn = reqData.efn,
      url = $form.attr('action');

  $.ajax({
    url: url,
    type: 'POST',
    data: reqData,
    success: function () {
      PTL.utils.executeFunctionByName(successFn, window, e);
      $.magnificPopup.close();
    },
    error: function (xhr) {
      PTL.captcha.onError(xhr, errorFn);
    }
  });
});
