This is an app to generate invoices for contractors

Installation
============

1. In <pootle_dir>/pootle/apps, create a symlink named 'evernote_invoices'
pointing to the dir with this README.txt file:
<your_translate_checkout>/Evernote/pootle/apps/evernote_invoices

2. In <pootle_dir>/pootle/apps, add .gitignore file with the following
contents:
=========================
.gitignore
evernote_invoices/
=========================

3. In <pootle_dir>/pootle/settings, add the following lines to 90-local.conf:

=========================
# Plug in evernote_invoices app and its configuration file
INSTALLED_APPS += ['evernote_invoices']
invoice_conf_file = os.path.join(WORKING_DIR, 'apps', 'evernote_invoices', 'settings.py')
execfile(os.path.abspath(invoice_conf_file))

# Path to PhantomJS executable (to generate PDF invoices)
#PHANTOMJS_EXECUTABLE = 'phantomjs'
=========================

4. To enable generating PDF files, install it from http://phantomjs.org/,
uncomment the 'PHANTOMJS_EXECUTABLE' parameter, and adjust the path to
its executable if needed (you may need to provide a full path to the executable)

Usage
=====

To generate invoices for the current month (this is for testing purposes mostly), run:

$ ./manage.py generate_invoices

To generate invoices for the specific month (this is how it will be used in production), run:

$ ./manage.py generate_invoices --month=<YYYY-MM>

where '<YYYY-MM>' parameter is the target month. Example: '2014-10'.

Invoices will be generated in <pootle_dir>/~invoices/<YYYY-MM>/ folder.

Maintenance
===========

The list of users to generate invoices for is defined in settings.py in the same folder
where this README.txt file is located.
