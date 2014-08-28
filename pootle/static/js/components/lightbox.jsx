'use strict';

var React = require('react');

require('./lightbox.css');


var keys = {
  ESC: 27
};

// Global state to keep track of the created lightbox components
var boxes = [];


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

  componentDidMount: function () {
    if (boxes.length === 0) {
      window.addEventListener('keyup', this.handleWindowKeyUp, false);
      document.body.classList.add('lightbox-lock');
    }

    boxes.push(this);
  },

  componentWillUnmount: function () {
    var box = boxes.pop();

    if (boxes.length === 0) {
      window.removeEventListener('keyup', box.handleWindowKeyUp, false);
      document.body.classList.remove('lightbox-lock');
    }
  },


  /* Handlers */

  handleWindowKeyUp: function (e) {
    if (e.keyCode === keys.ESC) {
      boxes[boxes.length-1].handleClose();
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

          {this.props.showClose &&
            <button type="button"
                    className="lightbox-close"
                    onClick={this.handleClose}>×</button>}
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
    return this.transferPropsTo(
      <Modal>
      {this.props.title &&
        <div className="lightbox-header">
          <h3>{this.props.title}</h3>
        </div>}

        <div className="lightbox-body">
          {this.props.children}
        </div>

        <div className="lightbox-footer">
          <button type="button"
                  className="btn btn-primary"
                  onClick={this.props.handleOk}>
            {this.props.okLabel}
          </button>
          <button type="button"
                  className="btn"
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
