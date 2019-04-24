# Wishlist

## Features

* Support "sheet" keyword (and other file types)
* Support "old" keyword
* Support "version" keyword to get info about current version

## Better scoring
* Score as whole list to inter-item comparison
* Score list of items according to which contains more of the unique tokens, i.e. having a token that no other item has should be worth more
* Use full text and maybe some TF-IDF type magic to index on terms unique to each document. Requires caching.
* Score based on permissions, to weight when a permissioned user is on there that matches a token
* Filter out or down-score trashed items

## QoL
* Add team drive names to parent lists
* Truncate parent lists to be presentable
