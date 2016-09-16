/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import assign from 'object-assign';
import React from 'react';

import ReactRenderer from 'utils/ReactRenderer';
import { q, qAll } from 'utils/dom';

import { loadFormatAdaptor } from './formats/FormatLoader';
import { hasCRLF, normalize, denormalize } from './utils/normalizer';


const ReactEditor = {

  init(props) {
    this.node = q('.js-mount-editor');
    this.sourceNode = q('.js-mount-editor-original-src');
    this.alternativeSourceNodes = qAll('.js-mount-editor-alt-src');
    this.props = {};
    this.hasCRLF = props.sourceValues.some(hasCRLF);

    loadFormatAdaptor(props, (newProps, adaptor) => {
      this.formatAdaptor = adaptor;
      ReactRenderer.unmountComponents();
      this.setProps(newProps);
    });
  },

  setProps(props) {
    // Overriding values is a one-time thing: take it into account only if it
    // was passed explicitly.
    const overrideProps = (
      props.hasOwnProperty('overrideValues') ? {} : { overrideValues: null }
    );
    this.props = assign(this.props, props, overrideProps);

    /*           ,
     *  __  _.-"` `'-.
     * /||\'._ __{}_(  CUSTOMS CHECK: we convert potential CRLFs to LFs
     * ||||  |'--.__\  when passing values down to components (`extraProps`),
     * |  L.(   ^_\^   but we keep the original values in `this.props`
     * \ .-' |   _ |   just in case the outside world needs to query them.
     * | |   )\___/
     * |  \-'`:._]
     * \__/;      '-.
     */
    const extraProps = {};
    if (this.hasCRLF) {
      if (props.hasOwnProperty('overrideValues')) {
        extraProps.overrideValues = normalize(props.overrideValues);
      }
      if (props.hasOwnProperty('initialValues')) {
        extraProps.initialValues = normalize(props.initialValues);
      }
    }

    this.editorInstance = ReactRenderer.render(
      <this.formatAdaptor.editorComponent
        onChange={this.handleChange}
        {...this.props}
        {...extraProps}
      />,
      this.node
    );
    ReactRenderer.render(
      <this.formatAdaptor.unitSourceComponent
        id={this.props.unitId}
        values={this.props.sourceValues}
        hasPlurals={this.props.hasPlurals}
        sourceLocaleCode={this.props.sourceLocaleCode}
        sourceLocaleDir={this.props.sourceLocaleDir}
      />,
      this.sourceNode
    );
    for (let i = 0; i < this.alternativeSourceNodes.length; i++) {
      const mountNode = this.alternativeSourceNodes[i];
      const unit = this.props.alternativeSources[mountNode.dataset.id];
      ReactRenderer.render(
        <this.formatAdaptor.unitSourceComponent
          id={unit.id}
          values={unit.target}
          hasPlurals={unit.has_plurals}
          sourceLocaleCode={unit.language_code}
          sourceLocaleDir={unit.language_direction}
        />,
        this.alternativeSourceNodes[i]
      );
    }
  },

  // FIXME: this additional layer of state tracking is only kept to allow
  // interaction from the outside world. Remove ASAP.
  get stateValues() {
    /*           ,
     *  __  _.-"` `'-.
     * /||\'._ __{}_(  CUSTOMS CHECK: if any CRLF => LF conversion was done
     * ||||  |'--.__\  when passing values down (`this.hasCRLF`), we need to
     * |  L.(   ^_\^   convert values back to their original form (LF => CRLF)
     * \ .-' |   _ |   when providing the hook to the outside world, making
     * | |   )\___/    them unaware of what happened within the component's
     * |  \-'`:._]     ecosystem.
     * \__/;      '-.
     */
    if (this.hasCRLF) {
      return denormalize(this.editorInstance.state.values);
    }
    return this.editorInstance.state.values;
  },

  handleChange() {
    PTL.editor.onTextareaChange();
  },

};


export default ReactEditor;
