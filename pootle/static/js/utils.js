(function ($) {

  window.PTL = window.PTL || {};

  PTL.utils = {

    /* Gets current URL's hash */
    getHash: function (win) {
      // Mozilla has a bug when it automatically unescapes %26 to '&'
      // when getting hash from `window.location.hash'.
      // So, we have to extract it from the `window.location'.
      // Also, we don't need to decodeURIComponent() the hash
      // as it will break encoded ampersand again
      // (decoding can be done on the higher level, if needed)
      return (win || window).location.toString().split('#', 2)[1] || '';
    },

    decodeURIParameter: function(s) {
      return decodeURIComponent(s.replace(/\+/g, " "));
    },

    getParsedHash: function (h) {
      var params = new Object();
      var r = /([^&;=]+)=?([^&;]*)/g;
      if (h == undefined) {
        h = this.getHash();
      }
      var e;
      while (e = r.exec(h)) {
        params[this.decodeURIParameter(e[1])] = this.decodeURIParameter(e[2]);
      }
      return params;
    },

    /* Updates current URL's hash */
    updateHashPart: function (part, newVal, removeArray) {
      var params = new Array();
      var r = /([^&;=]+)=?([^&;]*)/g;
      var h = this.getHash();
      var e, ok;
      while (e = r.exec(h)) {
        var p = this.decodeURIParameter(e[1]);
        if (p == part) {
          // replace with the given value
          params.push(e[1] + '=' + encodeURIComponent(newVal));
          ok = true;
        } else if ($.inArray(p, removeArray) == -1) {
          // use the parameter as is
          params.push(e[1] + '=' + e[2]);
        }
      }
      // if there was no old parameter, push the param at the end
      if (!ok) {
        params.push(encodeURIComponent(part) + '=' + encodeURIComponent(newVal));
      }
      return params.join('&');
    }
  };

  /* Returns the number (size) of properties of a given object */
  Object.size = function (obj) {
    var size = 0, key;
    for (key in obj) {
      if (obj.hasOwnProperty(key)) {
        size++;
      }
    }
    return size;
  };

})(jQuery);
