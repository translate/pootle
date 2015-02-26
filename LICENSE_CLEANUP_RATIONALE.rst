.. note: This is part of these changes for easy review and stepping through
   commits.  It will land with the changes so that anyone reviewing these in
   future can see how it evolved. But it will be removed from the actual code
   as a final step and moved to the wiki for future reference.


License Cleanup
===============


Rationale
---------

1. Validate and verify what the definitive license is for Pootle.

   a) So that we can ensure consistency in the license claims throught the
      code.
   b) So that we know if we are able to update the licenses if required. E.g.
      are we using GPL2 or GPL2 and later.

2. Reduce or eliminate the maintainenance of headers in files.

   a) Header noise is confusing and detracts from code.
   b) Header copyright claims are sometimes used to claim credit, we think
      there is a better and fairer way to claim and show credit.
   c) Headers should be simple and easy and require no maintenance or
      thought.

3. Document more fully the copyright history, the funders and major
   contributors.

   a) We don't just have code contributors we have contributors that have
      worked on Pootle for years.  They deserver special mention.
   b) Funder have not added one line of code, but there would also be no code
      without them.  We want to acknowledge them.

4. Document clearly Pootles copyright policy and views. E.g. why there is no
   copyright assignement and why it will, in fact has to remain as free
   software.

   a) We don't require or want copyright assignment. Contributors need to
      know that.
   b) Pootle's license terms and copyright holders are limited in their
      ability to make the product proprietary.  That's a feature and we'd
      like to tell people about it.

5. Relicense Pootle code.

   a) If the validation shows that we are allowed to relicense then we can
      proceed.
   b) As we use code with other license e.g. Apache we are technical not
      allowed to distribute them with our GPL2 licensed code.

