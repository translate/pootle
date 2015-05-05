Relevant bugs:
https://github.com/evernote/pootle/issues/284 - Docs to setup ES
https://github.com/evernote/pootle/issues/285 - Proper config catching or at least defaults to prevent tracebacks
https://github.com/translate/pootle/issues/3610 - Local TM: Pootle fails to start if elasticsearch isn't available
https://github.com/translate/pootle/issues/3618 - LocalTM update should be an RQ job
https://github.com/translate/pootle/issues/3510 - Document ElasticSearch TM functionality
https://github.com/translate/pootle/issues/3297 - Recover local TM support 

Issues
------

- Amagama results are not merged with the TM results but displayed in their own
  section.
- The TM code could be abstracted better to allow Amagama to fit in there.
  Partially dealt with by having backends and the broker.
- Needs good defaults if config data is missing.
- We might need to use the bulk commands.
  - I suspect any large import of files outside of Pootle would create problems
    see
    https://elasticsearch-py.readthedocs.org/en/master/helpers.html#elasticsearch.helpers.bulk
  - Import of the whole of LO takes about 25 minutes, so maybe not needed for Pootle
  - Needed if we want to import more than just what is in the DB
- TM results lines are worded odly if contributor is missing, more relevant if
  we have data where we definately don't know who contributed the string.

Ideas
-----

- We could import anything into ES
  - Would help to expand the tool to allow any PO files to be imported to the
    search like we would with amaGama
- We have more useful data such as email md5 for gravatars
- WEIGHTING - if you have more that one TM e.g. local and extra what weightings
  do you give?
- MAX_RESULTS - what is the max that we want to display? I suspect that this is
  hardcoded at the moment.
- Is the TM results line its own templates that can be easily styled with TM
  info e.g. percentage match
- How can you go and fix an issue? - Would be nice to allow translators to mark
  and item for fixing or fix inline and return. At unit, see issue, click fix,
  got to that faulty unit, click submit or next, then return to original unit.
- Script easy import of e.g. Windows localisations and other readily available
  TM data.


Better query construction
-------------------------

Might want to use http://elasticsearch-dsl.readthedocs.org/en/latest/
