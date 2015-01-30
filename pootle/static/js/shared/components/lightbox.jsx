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


/* Reusable micro components */

var ModalHeader = React.createClass({

  render: function () {
    return (
      <div className="lightbox-header">
        {this.props.children}
      </div>
    );
  },

});


var ModalFooter = React.createClass({

  render: function () {
    return (
      <div className="lightbox-footer">
        {this.props.children}
      </div>
    );
  },

});


/* Actual components */

var Modal = React.createClass({

  propTypes: {
    title: React.PropTypes.string,
    showClose: React.PropTypes.bool,
    handleClose: React.PropTypes.func.isRequired,
  },


  /* Lifecycle */

  getDefaultProps: function () {
    return {
      title: '',
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

  renderHeader: function () {
    var title = (this.props.title &&
      <h3 className="lightbox-title">{this.props.title}</h3>
    );
    var closeBtn = (this.props.showClose &&
      <button className="lightbox-close"
              onClick={this.handleClose}>×</button>
    );

    return (
      <ModalHeader>
        {title}
        {closeBtn}
      </ModalHeader>
    );
  },

  renderFooter: function () {
    return null;
  },

  render: function () {
    var header = this.props.header ? this.props.header(this.props)
                                   : this.renderHeader(this.props);
    var footer = this.props.footer ? this.props.footer(this.props)
                                   : this.renderFooter(this.props);

    return (
      <div className="lightbox-bg">
        <div className="lightbox-container">
          <div className="lightbox-body"
               ref="body"
               tabIndex="-1">
            {header}
            <div className="lightbox-content">
              {this.props.children}
            </div>
            {footer}
          </div>
        </div>
      </div>
    );
  },

});


var Dialog = React.createClass({

  propTypes: {
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

  renderFooter: function () {
    return (
      <ModalFooter>
        <button className="btn btn-primary"
                onClick={this.props.handleOk}>
          {this.props.okLabel}
        </button>
        <button className="btn"
                autoFocus={true}
                onClick={this.props.handleCancel}>
          {this.props.cancelLabel}
        </button>
      </ModalFooter>
    );
  },

  render: function () {
    return (
      <Modal {...this.props} footer={this.renderFooter} />
    );
  }

});


module.exports = {
  Modal: Modal,
  Dialog: Dialog
};
