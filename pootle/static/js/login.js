(function ($) {

  window.PTL = window.PTL || {};

  PTL.login = {

    enLink: function (e) {
      e.preventDefault();

      $('.form.info').removeClass('hide');
      $('.login').removeClass('hide');
      $('.form.question').addClass('hide');
      $("#id_username").focus();
    },

    pootleLogin: function (e) {
      e.preventDefault();

      $('.login').removeClass('hide');
      $("#id_username").focus();
    }

  };

  $(document).on('click', '.js-en-auth-link', PTL.login.enLink);
  $(document).on('click', '.js-en-auth-login', PTL.login.pootleLogin);

}(jQuery));
