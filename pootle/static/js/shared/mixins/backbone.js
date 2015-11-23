'use strict';


// XXX: let's try to get rid of this at some stage
// See http://khan.github.io/react-components/#backbone-mixin
var BackboneMixin = {

  componentDidMount: function () {
    this._boundForceUpdate = this.forceUpdate.bind(this, null);
    this.getResource().on('all', this._boundForceUpdate, this);
  },

  componentWillUnmount: function () {
    this.getResource().off('all', this._boundForceUpdate);
  },

};


module.exports = BackboneMixin;
