/*
 * Copyright (C) Pootle contributors.
 *
 * This file is a part of the Pootle project. It is distributed under the GPL3
 * or later license. See the LICENSE file for a copy of the license and the
 * AUTHORS file for copyright and authorship information.
 */

import cx from 'classnames';
import React from 'react';


const EditingArea = (props) => {
  const editorWrapperClasses = cx('editor-area-wrapper js-editor-area-wrapper', {
    'is-disabled': props.isDisabled,
  });

  return (
    <div className={editorWrapperClasses}>
      <props.textareaComponent
        {...props}
      />
    </div>
  );
};

EditingArea.propTypes = {
  autoFocus: React.PropTypes.bool,
  id: React.PropTypes.string,
  initialValue: React.PropTypes.string,
  isDisabled: React.PropTypes.bool,
  isRawMode: React.PropTypes.bool,
  // FIXME: needed to allow interaction from the outside world. Remove ASAP.
  onChange: React.PropTypes.func.isRequired,
  textareaComponent: React.PropTypes.func.isRequired,
  value: React.PropTypes.string,
};


export default EditingArea;
