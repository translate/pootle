'use strict';

var React = require('react');

require('./lightbox.css');


var keys = {
  ESC: 27
};

// Global state to keep track of the created lightbox components
// and the previously-focused elements
var boxes = [];
var focusedElements = [];


var Modal = React.createClass({

  propTypes: {
    showClose: React.PropTypes.bool,
    handleClose: React.PropTypes.func.isRequired,
  },


  /* Lifecycle */

  getDefaultProps: function () {
    return {
      showClose: true,
    };
  },

  componentWillMount: function () {
    focusedElements.push(document.activeElement);
  },

  componentDidMount: function () {
    if (boxes.length === 0) {
      window.addEventListener('keyup', this.handleWindowKeyUp, false);
      window.addEventListener('focus', this.handleWindowFocus, true);
      document.body.classList.add('lightbox-lock');
    }

    boxes.push(this);
  },

  componentWillUnmount: function () {
    var box = boxes.pop();

    if (boxes.length === 0) {
      window.removeEventListener('keyup', box.handleWindowKeyUp, false);
      window.removeEventListener('focus', box.handleWindowFocus, true);
      document.body.classList.remove('lightbox-lock');
    }

    // `setTimeout()` is necessary to slightly delay the call to
    // `.focus()` when components are about to be unmounted
    setTimeout(function () {
      focusedElements.pop().focus();
    }, 0);
  },


  /* Handlers */

  handleWindowKeyUp: function (e) {
    if (e.keyCode === keys.ESC) {
      boxes[boxes.length-1].handleClose();
    }
  },

  handleWindowFocus: function (e) {
    var box = boxes[boxes.length-1].refs.body.getDOMNode();

    if (e.target !== window && !box.contains(e.target)) {
      e.stopPropagation();
      box.focus();
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
          <div className="lightbox-body"
               ref="body"
               tabIndex="-1">

          {this.props.showClose &&
            <button className="lightbox-close"
                    onClick={this.handleClose}>×</button>}

            {this.props.children}
          </div>
        </div>
      </div>
    );
  }

});


var Dialog = React.createClass({

  propTypes: {
    title: React.PropTypes.string,
    okLabel: React.PropTypes.string,
    cancelLabel: React.PropTypes.string,
    handleOk: React.PropTypes.func.isRequired,
    handleCancel: React.PropTypes.func.isRequired,
  },


  /* Lifecycle */

  getDefaultProps: function () {
    return {
      okLabel: 'OK',
      cancelLabel: 'Cancel',
    };
  },


  /* Layout */

  render: function () {
    return (
      <Modal {...this.props}>
      {this.props.title &&
        <div className="lightbox-header">
          <h3>{this.props.title}</h3>
        </div>}

        <div className="lightbox-content">
          {this.props.children}
        </div>

        <div className="lightbox-footer">
          <button className="btn btn-primary"
                  onClick={this.props.handleOk}>
            {this.props.okLabel}
          </button>
          <button className="btn"
                  autoFocus={true}
                  onClick={this.props.handleCancel}>
            {this.props.cancelLabel}
          </button>
        </div>
      </Modal>
    );
  }

});


module.exports = {
  Modal: Modal,
  Dialog: Dialog
};
