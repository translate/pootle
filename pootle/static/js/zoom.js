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
      var zoomStatus = '';
      if (this.pageZoom < 0) {
        zoomStatus = ['zoom-out-', (this.pageZoom * -1)].join('');
      } else if (this.pageZoom > 0) {
        zoomStatus = ['zoom-in-', this.pageZoom].join('');
      }
      return zoomStatus;
    },

    // Changes zoom and updates class name of a document body
    zoom: function (v) {
      var oldClassName = this.zoomClassName();
      if (v === -1 && this.pageZoom === -2) {
        // Minimum zoom level reached
        return;
      }

      if (v === 1 && this.pageZoom === 2) {
        // Maximum zoom level reached
        return;
      }

      if (v === 0) {
        // Reset zoom
        this.pageZoom = 0;
      } else {
        // v value:
        //  -1 : zoom out
        //  +1 : zoom in
        this.pageZoom += v;
      }

      $.cookie('pageZoom', this.pageZoom, {path: '/'});

      $(document.body).removeClass(oldClassName).addClass(this.zoomClassName());
    }

  };

}(jQuery));

$(function () {
  PTL.zoom.init();
});
