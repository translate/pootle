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
    },

    /* Cross-browser comparison function */
    strCmp: function (a, b) {
      return a == b ? 0 : a < b ? -1 : 1;
    },

    /* Returns a string representing a relative datetime */
    relativeDate: function (date) {
      var fmt, count,
          delta = Date.now() - date,
          seconds = Math.round(Math.abs(delta) / 1000),
          minutes = Math.round(seconds / 60),
          hours = Math.round(minutes / 60),
          days = Math.round(hours / 24),
          weeks = Math.round(days / 7),
          years = Math.round(days / 365);

      if (years > 0) {
        fmt = ngettext('A year ago', '%s years ago', years);
        count = [years];
      } else if (weeks > 0) {
        fmt = ngettext('A week ago', '%s weeks ago', weeks);
        count = [weeks];
      } else if (days > 0) {
        fmt = ngettext('Yesterday', '%s days ago', days);
        count = [days];
      } else if (hours > 0) {
        fmt = ngettext('An hour ago', '%s hours ago', hours);
        count = [hours];
      } else if (minutes > 0) {
        fmt = ngettext('A minute ago', '%s minutes ago', minutes);
        count = [minutes];
      }

      if (fmt) {
        return interpolate(fmt, count);
      }

      return gettext("A few seconds ago");
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
