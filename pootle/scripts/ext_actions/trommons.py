#!/usr/bin/env python
# -*- coding: UTF-8 -*-
#
# Copyright 2013 Zuza Software Foundation
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.
"""In order to use this script it is necessary to:

* Alter this script to set the appropriate values in the constants,
* Have a site defined.

"""

import json
import logging
import os
import shutil
import subprocess
from tempfile import mkdtemp

from django.contrib.sites.models import Site

from pootle.scripts.actions import TranslationProjectAction, StoreAction
from pootle_project.models import Project
from pootle_store.models import Unit
from pootle_store.util import TRANSLATED


#TODO maybe put the following constant on Pootle settings.
# Directory where Pootle leaves stuff for Trommons.
TROMMONS_DIR = "/home/leo/Escritorio/trommons/"

# Protocol string used to create the project backlink.
BACKLINK_PROTOCOL = "http://"

# Filename of the JSON file used to exchange data. Have it in one place in case
# we need to alter it.
JSON_FILENAME = "meta.json"

# This is necessary when calling management commands.
POOTLE_SETTINGS_FILE = ("/home/leo/Escritorio/repos/pootle/pootle/settings/"
                        "90-dev-local.conf")


class AbortException(Exception):
    """Custom exception to provide smart abort workflow."""
    pass


class TrommonsAction(TranslationProjectAction, StoreAction):
    """Send translations back to Trommons."""

    def __init__(self, **kwargs):
        super(TrommonsAction, self).__init__(**kwargs)
        self.icon = 'icon-external-link'

    def run(self, path, root, tpdir, language, project, store='*', style='',
            **kwargs):
        """Send the translation to Trommons when the user clicks the link."""
        tp_path = os.path.join(root, tpdir)

        try:
            self.__run_stuff(project, language, tp_path)
        except AbortException:
            pass  # Do nothing because abort message was already set.
        except:
            self.set_error("Some error happened. Please contact Trommons "
                           "administrators.")
            logging.exception("Something wrong happened while sending "
                              "translations to Trommons. Aborting.")
        else:
            self.set_output("Succesfully sent translation to Trommons")

    ###########################################################################
    ###########################################################################

    def __run_stuff(self, project_code, language_code, tp_path):
        """Run all the machinery to notify Trommons that translation is done.

        This performs checks, exports the translation file, and writes the
        required files.
        """
        # It is necessary to set the POOTLE_SETTINGS environment variable
        # before calling the Pootle management commands.
        os.environ['POOTLE_SETTINGS'] = POOTLE_SETTINGS_FILE

        # Set the default logging level to INFO, which makes easier to check
        # that everything works as expected.
        logging.basicConfig(level=logging.INFO)

        #######################################################################

        # Get the project object for later use.
        project = Project.objects.get(code=project_code)

        # Make sure everything is in place before sending translation to
        # Trommons.
        self.__ensure_basics(project)

        # Get the URL for the project for Trommons to use. This requires
        # setting a proper Site in Pootle admin.
        project_backlink = ('%s%s%s' % (BACKLINK_PROTOCOL,
                                        Site.objects.get_current().domain,
                                        project.get_absolute_url()))

        # Synchronize to disk the translations for the given project and
        # language.
        self.__sync_translations(project_code, language_code)

        # Get the synced translation file for later user (fail early).
        synced_filename = self.__ensure_synced_file(tp_path)

        # Create a temporary directory.
        temp_dir = mkdtemp()

        # Create a directory named like the Pootle project (Trommons task)
        # inside the temporary directory.
        temp_proj_dir = os.path.join(temp_dir, project_code)
        os.mkdir(temp_proj_dir)

        # Move the synced translation file to the task directory.
        old_path = os.path.join(tp_path, synced_filename)
        new_path = os.path.join(temp_proj_dir, synced_filename)
        shutil.copy2(old_path, new_path)
        logging.info("Succesfully copied translation file to '%s'" %
                     temp_proj_dir)

        # Write the JSON file to the task directory.
        self.__write_json_file(project_backlink, temp_proj_dir)

        # Move the task directory to the final destination inside the Trommons
        # directory.
        shutil.move(temp_proj_dir, TROMMONS_DIR)

        # Remove the temporary directory since we are already done with it.
        shutil.rmtree(temp_dir)


        #TODO remove project, files, etc.
        #TODO requires redirect and notifying the user using messages.
        #TODO Maybe using a second directory monitor for when Trommons removes
        # the files is another option to do this.


        logging.info("Succesfully notified Trommons the success in importing.")

    ###########################################################################

    def __ensure_basics(self, project):
        """Ensure that the minimum requirements are met."""
        # Make sure that the destination directory exists.
        if not os.path.exists(TROMMONS_DIR):
            msg = ("Destination directory '%s' doesn't exist. Aborting." %
                   TROMMONS_DIR)
            self.set_error(msg)
            logging.error(msg)
            raise AbortException

        # Make sure that the project only has one language.
        project_tps = project.translationproject_set.all()

        if len(project_tps) > 1:
            msg = "More than one language for the project. Aborting."
            self.set_error(msg)
            logging.error(msg)
            raise AbortException

        # Make sure that all the strings are translated.
        units_qs = Unit.objects.filter(
            store__translation_project=project_tps[0]
        )
        units_qs = units_qs.exclude(state=TRANSLATED)

        if len(units_qs) > 0:
            msg = "Not all strings are still translated. Aborting."
            self.set_error(msg)
            logging.error(msg)
            raise AbortException


    def __sync_translations(self, project_code, language_code):
        """Sync to disk the translations for the given project and language."""
        # Just run the sync_stores management command.
        cmd_args = [
            "pootle",
            "sync_stores",
            "--overwrite",  # This parameter is indispensable.
            "--project",
            project_code,
            "--language",
            language_code,
        ]
        subprocess.call(cmd_args)
        logging.info("Sucessfully synced the translations.")

    def __ensure_synced_file(self, tp_path):
        """Ensure that the synced translation file is in place."""
        try:
            filenames = os.listdir(tp_path)
        except OSError:
            logging.exception("Some problem happened when trying to read the "
                              "task directory contents.")
            raise AbortException

        if len(filenames) < 1:
            logging.error("There is no translation file to export. Aborting.")
            raise AbortException

        return filenames[0]

    def __write_json_file(self, project_backlink, temp_proj_dir):
        """Write the JSON file to the task directory."""
        # Open the destination file inside that directory to write the JSON and
        # notify Trommons that the project has been succesfully added.
        temp_file_name = os.path.join(temp_proj_dir, JSON_FILENAME)
        output_json_file = open(temp_file_name, "w")

        # Create a dictionary for output JSON file.
        response_data = {
            'created': True,
            'backlink': project_backlink,
            'completed': True,
        }

        # Dump the JSON to the file, using pretty printing.
        json.dump(response_data, output_json_file, indent=4,
                  separators=(',', ': '))

        # Close the file to actually write the JSON.
        output_json_file.close()
        logging.info("Succesfully wrote the JSON file.")


TrommonsAction.hello = TrommonsAction(category="Other actions",
                                      title="Send translation to Trommons")
