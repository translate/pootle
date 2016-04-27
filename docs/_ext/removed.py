# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Directove to describe a removal in a specific version.

Copied from: sphinx/directives/other.py
"""

from docutils import nodes
from docutils.parsers.rst import Directive
from sphinx import addnodes
from sphinx.util.nodes import set_source_info


versionlabels = {
    'removed': 'Removed in version %s',
}


class VersionChange(Directive):
    """
    Directive to describe a change/addition/deprecation in a specific version.

    """

    has_content = True
    required_arguments = 1
    optional_arguments = 1
    final_argument_whitespace = True
    option_spec = {}

    def run(self):
        node = addnodes.versionmodified()
        node.document = self.state.document
        set_source_info(self, node)
        node['type'] = self.name
        node['version'] = self.arguments[0]
        text = versionlabels[self.name] % self.arguments[0]
        if len(self.arguments) == 2:
            inodes, messages = self.state.inline_text(self.arguments[1],
                                                      self.lineno+1)
            para = nodes.paragraph(self.arguments[1], '', *inodes,
                                   translatable=False)
            set_source_info(self, para)
            node.append(para)
        else:
            messages = []
        if self.content:
            self.state.nested_parse(self.content, self.content_offset, node)
        if len(node):
            if isinstance(node[0], nodes.paragraph) and node[0].rawsource:
                content = nodes.inline(node[0].rawsource, translatable=True)
                content.source = node[0].source
                content.line = node[0].line
                content += node[0].children
                node[0].replace_self(nodes.paragraph('', '', content,
                                                     translatable=False))
            node[0].insert(0, nodes.inline('', '%s: ' % text,
                                           classes=['versionmodified']))
        else:
            para = nodes.paragraph('', '',
                                   nodes.inline('', '%s.' % text,
                                                classes=['versionmodified']),
                                   translatable=False)
            node.append(para)
        env = self.state.document.settings.env
        # XXX should record node.source as well
        env.note_versionchange(node['type'], node['version'], node, node.line)
        return [node] + messages


def setup(app):
    app.add_directive('removed', VersionChange)
    return {"parallel_read_safe": True}
