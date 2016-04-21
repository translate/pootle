/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import React from 'react';

import FormElement from 'components/FormElement';
import FormMixin from 'mixins/FormMixin';

import { decodeEntities } from '../utils';

export const SuggestionFeedBackForm = React.createClass({

  propTypes: {
    suggId: React.PropTypes.number.isRequired,
    initialSuggestionText: React.PropTypes.string.isRequired,
    localeDir: React.PropTypes.string.isRequired,
    editor: React.PropTypes.object.isRequired,
  },

  mixins: [FormMixin],

  /* Lifecycle */

  getInitialState() {
    this.initialData = {
      comment: '',
      translation: this.props.initialSuggestionText,
    };

    return {
      formData: this.initialData,
    };
  },

  /* Handlers */

  handleAccept(e) {
    e.preventDefault();
    if (this.state.formData.translation === this.props.initialSuggestionText) {
      this.props.editor.acceptSuggestion(this.props.suggId, this.state.formData);
    } else {
      const area = document.querySelector('.js-translation-area');
      area.value = decodeEntities(this.state.formData.translation);
      this.props.editor.handleSubmit(this.state.formData.comment);
    }
  },

  handleReject(e) {
    e.preventDefault();
    this.props.editor.rejectSuggestion(this.props.suggId, this.state.formData);
  },

  /* Layout */

  render() {
    const { errors } = this.state;
    const { formData } = this.state;

    return (
      <form
        id="suggestion-feedback-form"
      >
        <div className="fields">
          <FormElement
            id="suggestion-editor"
            type="textarea"
            label={gettext('Edit the suggestion before accepting, if necessary')}
            placeholder=""
            name="translation"
            handleChange={this.handleChange}
            errors={errors.translation}
            value={formData.translation}
            data-action="overwrite"
            dir={this.props.editor.settings.localeDir}
          />
          <FormElement
            type="textarea"
            label={gettext('Provide optional comment (will be publicly visible)')}
            placeholder=""
            name="comment"
            handleChange={this.handleChange}
            errors={errors.comment}
            value={formData.comment}
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
