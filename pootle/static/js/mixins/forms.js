'use strict';


var FormValidationMixin = {

  getInitialState: function () {
    return {
      errors: {}
    };
  },

  clearValidation: function () {
    this.setState({errors: {}});
  },

  validateResponse: function (xhr) {
    // XXX: should this also check for HTTP 500, 404 etc.?
    var response = JSON.parse(xhr.responseText);
    this.setState({errors: response.errors});
  }

};


module.exports = FormValidationMixin;
