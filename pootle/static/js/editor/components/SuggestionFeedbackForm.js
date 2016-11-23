/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import _ from 'underscore';
import React from 'react';

import assign from 'object-assign';

import FormElement from 'components/FormElement';


const SuggestionFeedBackForm = React.createClass({

  propTypes: {
    suggId: React.PropTypes.number.isRequired,
    initialSuggestionValues: React.PropTypes.array.isRequired,
    onAcceptSuggestion: React.PropTypes.func.isRequired,
    onRejectSuggestion: React.PropTypes.func.isRequired,
    onChange: React.PropTypes.func.isRequired,
    editorComponent: React.PropTypes.func.isRequired,
    isDisabled: React.PropTypes.bool.isRequired,
    sourceValues: React.PropTypes.array.isRequired,
    currentLocaleCode: React.PropTypes.string.isRequired,
    currentLocaleDir: React.PropTypes.string.isRequired,
    targetNplurals: React.PropTypes.number,
  },

  /* Lifecycle */

  getInitialState() {
    this.initialData = {
      comment: '',
      translations: this.props.initialSuggestionValues,
    };

    return {
      formData: this.initialData,
    };
  },

  /* Handlers */

  handleAccept(e) {
    const suggestionChanged = (
      this.state.formData.translations !== this.props.initialSuggestionValues
    );
    e.preventDefault();
    this.props.onAcceptSuggestion(
      this.props.suggId,
      {
        requestData: this.state.formData,
        isSuggestionChanged: suggestionChanged,
      }
    );
  },

  handleReject(e) {
    e.preventDefault();
    this.props.onRejectSuggestion(this.props.suggId, { requestData: this.state.formData });
  },

  handleChange(values) {
    const isDirty = !_.isEqual(values, this.initialData);
    const formData = assign(this.state.formData, { translations: values });
    this.setState({ isDirty, formData });
    this.props.onChange(isDirty);
  },

  handleCommentChange(name, comment) {
    const isDirty = comment !== '';
    const formData = assign(this.state.formData, { comment });
    this.setState({ isDirty, formData });
    this.props.onChange(isDirty);
  },

  /* Layout */

  render() {
    const { formData } = this.state;

    return (
      <form
        id="suggestion-feedback-form"
      >
        <div className="fields">
          <div className="field-wrapper suggestion-editor">
            <label htmlFor="suggestion-editor">
              {gettext('Edit the suggestion before accepting, if necessary')}
            </label>
            <this.props.editorComponent
              currentLocaleCode={this.props.currentLocaleCode}
              currentLocaleDir={this.props.currentLocaleDir}
              initialValues={formData.translations}
              onChange={this.handleChange}
              sourceValues={this.props.sourceValues}
              targetNplurals={this.props.targetNplurals}
              isDisabled={this.props.isDisabled}
            />
          </div>
          <FormElement
            type="textarea"
            label={gettext('Provide optional comment (will be publicly visible)')}
            placeholder=""
            name="comment"
            handleChange={this.handleCommentChange}
            value={formData.comment}
            className="comment"
          />
        </div>
        <p className="buttons">
          <button
            className="btn btn-success"
            onClick={this.handleAccept}
          ><i className="icon-accept-white"></i>{gettext('Accept')}</button>
          <button
            className="btn btn-danger"
            onClick={this.handleReject}
          ><i className="icon-reject-white"></i>{gettext('Reject')}</button>
        </p>
        <div className="clear" />
      </form>
    );
  },

});


export default SuggestionFeedBackForm;
