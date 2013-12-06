(function ($) {

  window.PTL = window.PTL || {};

  var sel = {
    out: '#js-zoom-out',
    reset: '#js-zoom-reset',
    in: '#js-zoom-in'
  };

  var zoomOut = function (e) {
    e.preventDefault();
    PTL.zoom.zoom(-1);
  };

  var zoomReset = function (e) {
    e.preventDefault();
    PTL.zoom.zoom(0);
  };

  var zoomIn = function (e) {
    e.preventDefault();
    PTL.zoom.zoom(1);
  };

  PTL.zoom = {
    // Variable that stores current zoom level
    pageZoom: 0,

    // Initializes zoom and sets up related shortcuts
    init: function () {
      this.pageZoom = $.cookie('pageZoom');

      $(document.body).addClass(this.zoomClassName());

      shortcut.add('ctrl+shift+-', zoomOut);
      shortcut.add('ctrl+shift+0', zoomReset);
      shortcut.add('ctrl+shift++', zoomIn);
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

  $(document).on('click', sel.out, zoomOut);
  $(document).on('click', sel.reset, zoomReset);
  $(document).on('click', sel.in, zoomIn);

}(jQuery));

$(function () {
  PTL.zoom.init();
});
