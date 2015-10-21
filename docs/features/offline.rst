Offline Translation
===================

You can export files for offline translation.  Once translated you can import
them again and Pootle will manage updating the translation in Pootle based on
your changes.

This feature is ideal for teams who have poor connectivity or if you prefer to
use an offline translation tool.

To export, simply click on the "Download for offline translation" link on the
sidebar in Pootle's overview page.  To import simply click the "Upload
translations" link and select the file you wish to upload.

.. versionchanged:: 2.7.1

If a string has been translated on Pootle and changed in your uploaded file
then your change will still be uploaded but it will be converted into a
suggestion which you can resolve in Pootle.

.. note:: If there are any errors in the upload then Pootle will warn you and
   the file will be rejected.
