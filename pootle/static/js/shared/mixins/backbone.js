
// XXX: let's try to get rid of this at some stage
// See http://khan.github.io/react-components/#backbone-mixin
const BackboneMixin = {

  componentDidMount() {
    this._boundForceUpdate = this.forceUpdate.bind(this, null);
    this.getResource().on('all', this._boundForceUpdate, this);
  },

  componentWillUnmount() {
    this.getResource().off('all', this._boundForceUpdate);
  },

};


export default BackboneMixin;
