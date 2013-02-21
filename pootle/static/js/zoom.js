(function ($) {

  window.PTL = window.PTL || {};

  PTL.zoom = {
    // Variable that stores current zoom level
    pageZoom: 0,

    // Initializes zoom and sets up related shortcuts
    init: function () {
      this.pageZoom = $.cookie('pageZoom');

      $(document.body).addClass(this.zoomClassName());

      shortcut.add('ctrl+shift+-', function () {
        PTL.zoom.zoom(-1);
      });

      shortcut.add('ctrl+shift+0', function () {
        PTL.zoom.zoom(0);
      });

      shortcut.add('ctrl+shift++', function () {
        PTL.zoom.zoom(1);
      });
    },

    // converts pageZoom value to an appropriate class name string
    zoomClassName: function () {
      if (this.pageZoom < 0) {
        return "zoom-out-" + (this.pageZoom * -1);
      } else if (this.pageZoom > 0) {
        return "zoom-in-" + this.pageZoom;
      } else {
        return "";
      }
    },

    // Changes zoom and updates class name of a document body
    zoom: function (v) {
      var oldClassName = this.zoomClassName();

      if (v == -1) {
        if (this.pageZoom == -2) {
          return; // minimum zoom level reached
        }
        this.pageZoom--;
      } else if (v == 1) {
        if (this.pageZoom == 2) {
          return; // maximum zoom level reached
        }
        this.pageZoom++;
      } else if (v == 0) {
        this.pageZoom = 0;
      }

      $.cookie('pageZoom', this.pageZoom, {path: '/'});

      $(document.body).removeClass(oldClassName).addClass(this.zoomClassName());
    }

  }

})(jQuery);
