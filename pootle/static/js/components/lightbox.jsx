'use strict';

var React = require('react');

require('./lightbox.css');


var keys = {
  ESC: 27
};


/*
 * TODO: support various types of lightboxes, including
 * modal, dialog or gallery:
 * <Modal /> == <Lightbox type="modal" />
 * <Dialog /> == <Lightbox type="dialog" />
 */


var Modal = React.createClass({

  propTypes: {
    closeBtn: React.PropTypes.bool,
    closeBtnTitle: React.PropTypes.string,
  },

  /* Lifecycle */

  getDefaultProps: function () {
    return {
      closeBtn: true,
      closeBtnTitle: 'Close (Esc)',
    };
  },

  componentDidMount: function () {
    window.addEventListener('keyup', this.handleWindowKeyUp, false);
    document.body.classList.add('lightbox-lock');
  },

  componentWillUnmount: function () {
    window.removeEventListener('keyup', this.handleWindowKeyUp, false);
    document.body.classList.remove('lightbox-lock');
  },


  /* Handlers */

  handleWindowKeyUp: function (e) {
    if (e.keyCode === keys.ESC) {
      this.handleClose();
    }
  },

  handleClose: function () {
    // Parent components need to take care of rendering the component
    // and unmounting it according to their needs
    this.props.handleClose();
  },


  /* Layout */

  render: function () {
    return (
      <div className="lightbox-bg">
        <div className="lightbox-container">
          <div className="lightbox-content">

            {this.props.children}

            {this.props.closeBtn &&
            <button type="button"
                    className="lightbox-close"
                    title={this.props.closeBtnTitle}
                    onClick={this.handleClose}>×</button>}
          </div>
        </div>
      </div>
    );
  }

});


var Lightbox = React.createClass({

  typeMap: {
    modal: Modal
  },


  /* Lifecycle */

  getDefaultProps: function () {
    return {
      isOpen: true,
      type: 'modal'
    };
  },


  /* Layout */

  render: function () {
    var LightboxComponent = this.typeMap[this.props.type];
    return this.props.isOpen ? new LightboxComponent(this.props) : null;
  }

});


module.exports = Lightbox;
