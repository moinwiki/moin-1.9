Lupy full text indexer r0.2.1
-----------------------------

**What is Lupy?**
  Lupy is a port of the excellent Jakarta Lucene 1.2 into 
  Python. 

**What can I do with Lupy?**
  Lupy is a full text indexer and search engine. It can be used to
  index text documents such as web pages, source code, email, etc.

**What is in this release?**
  Most of Lucene 1.2 is in Lupy 0.2. Lupy supports text indexing
  producing files that are binary compatible with Lucene. Index
  creation, update and searching are supported.

  This release supports TermQuery, PhraseQuery and BooleanQuery.

**What is not in this release?**
  There is no locking or synchronization.

  The query parser has not been ported, nor all of the analysis/doc
  parsing classes. Queries can be built using the basic building blocks.

  Tokenization is done with a simple regexp; there is no stop-lists,
  Porter stemming, StandardAnalyzer or German analyzer.

  This release does not contain the following queries:
  
  - QueryParser
  - MultiTermQuery
  - FuzzyQuery
  - WildCardQuery
  - PrefixQuery
  - RangeQuery
  - Sloppy phrase queries

  DateField has not been ported.

  Merging of multiple multi-segment indices is not supported.

**How do I get started?**
  Look in the examples directory.

  Most of the Lucene documentation is relevant to Lupy:
 
  - http://jakarta.apache.org/lucene
  - http://www.onjava.com/pub/a/onjava/2003/01/15/lucene.html
  - http://darksleep.com/lucene/

**Performance**
  Java is faster.


**Acknowledgements**
  Many thanks to Doug Cutting and the Jakarta Lucene team for building
  and enhancing such a high quality piece of open source software.

  Glyph Lefkowitz for serving as my language guru for Python and Java.

  Allen Short did the refactoring for the 0.2 release.
  
  I hope you find what you are searching for ;-)
  amir@divmod.org
