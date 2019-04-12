# Releases

CricleCI does not currently support parameterized builds. This means I can't manually kick off a special workflow to package and create a github release.

So, instead I've decided that any time I update the VERSION.txt file, that should tell CI to create a release and upload the .alfredworkflow file.

1. Change the VERSION.txt and push
1. Let CircleCI do its thing, should result in draft release with file attached
  1. Check https://circleci.com/gh/Decker87/gdrive-alfred/tree/master to watch
1. Visit https://github.com/Decker87/gdrive-alfred/releases to see it
1. Don't forget to publish the draft release

# Install python libs and dependencies to local dir

```
mkdir pylib_dist
pip install --target=pylib_dist --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib
```

# Auto-updating

Auto-updating with Alfred seems very troublesome to implement. Spent too much time on it already.
Instead I can add a node to the workflow that spins off another process to update. Can easily scriptify checking the latest release and downloading it / unzipping it if it's a later version.

# Faster searching

Possible to create local cache of stuff. Within reach to cache all info about all files ever viewed by me.

```
service.files().list(fields = "*", pageToken = nextPageToken, pageSize = 1000, orderBy = "viewedByMeTime asc", q = "viewedByMeTime > '1970-01-01T00:00:00.000Z'").execute()
```

Maybe the next iteration can be utilizing a local cache, load it into memory and iterate those. Want to get time down to 0.1s or less.
Start with naive approach - load all the shit into memory, then 

# Perf notes

On 4/8/19, I did some experiments.

For an item list 781 docs long:
* cPickle took 4.857s to load the file 100 times
* Iterating the list in-memory took less than 1ms total (basically neglectable)

So I can calculate it 0.062ms per doc to load into memory. At 1000 docs this is 62ms. At 10k docs this is 620ms. Will reach a point where it's not practical if others are going to use it. Will need to store stuff in memory or explore SQLite querying. For now I can rely on cPickle loading to be fast enough.

# One-liner to JSON-ify cache.pickle

```
json.dump(pickle.load(open("cache.pickle")), open("cache.json", "w"), indent = 4)
```

# Change file perms on windows

```
git update-index --chmod=+x <file>
```
