/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';


const EditingArea = ({ isDisabled, children }) => {
  const editorWrapperClasses = cx('editor-area-wrapper js-editor-area-wrapper', {
    'is-disabled': isDisabled,
  });

  return (
    <div className={editorWrapperClasses}>
      {children}
    </div>
  );
};

EditingArea.propTypes = {
  children: React.PropTypes.oneOfType([
    React.PropTypes.array,
    React.PropTypes.element,
  ]),
  isDisabled: React.PropTypes.bool.isRequired,
};


export default EditingArea;
