'use strict';

var React = require('react/addons');

var LayersMixin = require('mixins/layers');

require('./lightbox.css');

var cx = React.addons.classSet;


var classNames = {
  lock: 'lightbox-lock',
};

var keys = {
  ESC: 27
};


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

var ModalContainer = React.createClass({

  _previousFocus: null,
  _ownsLock: false,


  /* Lifecycle */

  componentWillMount: function () {
    this._previousFocus = document.activeElement;
  },

  componentDidMount: function () {
    if (!document.body.classList.contains(classNames.lock)) {
      this._ownsLock = true;
      document.body.classList.add(classNames.lock);
    }
  },

  componentWillUnmount: function () {
    if (this._ownsLock) {
      document.body.classList.remove(classNames.lock);
    }
    this._previousFocus.focus();
  },


  /* Handlers */

  handleKeyDown: function (e) {
    if (e.keyCode === keys.ESC) {
      this.props.onClose();
    }
  },


  /* Layout */

  render: function () {
    return (
      <div className="lightbox-bg">
        <div className="lightbox-container"
             onKeyDown={this.handleKeyDown}>
          <div className={cx('lightbox-body', this.props.className)}
               tabIndex="-1">
            {this.props.children}
          </div>
        </div>
      </div>
    );
  },

});


var Modal = React.createClass({
  mixins: [LayersMixin],

  propTypes: {
    title: React.PropTypes.string,
    showClose: React.PropTypes.bool,
    onClose: React.PropTypes.func.isRequired,
  },


  /* Lifecycle */

  getDefaultProps: function () {
    return {
      title: '',
      showClose: true,
    };
  },


  /* Handlers */

  handleClose: function () {
    // Parent components need to take care of rendering the component
    // and unmounting it according to their needs
    this.props.onClose();
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

  renderLayer: function () {
    var header = this.props.header ? this.props.header(this.props)
                                   : this.renderHeader(this.props);
    var footer = this.props.footer ? this.props.footer(this.props)
                                   : this.renderFooter(this.props);
    return (
      <ModalContainer {...this.props}>
        {header}
        <div className="lightbox-content">
          {this.props.children}
        </div>
        {footer}
      </ModalContainer>
    );
  },

  render: function () {
    return null;
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
  },

});


module.exports = {
  Modal: Modal,
  Dialog: Dialog
};
