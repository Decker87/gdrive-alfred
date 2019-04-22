# Wishlist

* Support "sheet" keyword (and other file types)
* Support "old" keyword
* Support creating new docs
* Refactor so searcher isn't doing more than searching
* Score as whole list to inter-item comparison
* Score list of items according to which contains more of the unique tokens, i.e. having a token that no other item has should be worth more
* Use full text and maybe some TF-IDF type magic to index on terms unique to each document. Requires caching.
* Score based on permissions, to weight when a permissioned user is on there that matches a token
* Sub-descriptions in alfred input containing some key stats
* Filter out or down-score trashed items
* Add team drive names to parent lists
* Truncate parent lists to be presentable
* Separate workflow versioning crap from search scripts
* Refactor flow of adding update item to output list - tech debt
