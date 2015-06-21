mezzanine-twitterplus
=====================
A modification of the twitter app mixins from [Mezzanine][1] with additional functionality such as support for images.


Features
=========
1. New mixin that supports an additional checkbox for indicating if an image should be tweeted along with the text
2. New mixin for ModelAdmins to support tweeting as an admin action, versus 'tweet on save'


Installation
============
1. Add mezzanine_twitterplus to your virtualenv or clone the repository :
```bash
    pip install git+git://github.com/dfraser/mezzanine-twitterplus.git
```

2. Add "twitterplus" to INSTALLED_APPS:
```python
    INSTALLED_APPS = (
        "...",
        "twitterplus",
    )
```

Usage
======

TweetImageAdminMixin
----------------------
TweetImageAdminMixin is a mixin, based on Mezzanine's TweetableAdminMixin, that adds support for tweeting an image
along with the tweet's text -- only upon saving of the object.

It can be configured to either support 'tweet with optional image' or 'tweet, always with image'.

1. Modify FORMFIELD_HTML as necessary
2. Add the mixin as follows to classes that support tweeting (drop in replacement for TweetableAdminMixin)

class ObjectAdmin(TweetImageAdminMixin, ...)

3. Add or modify the parent class init() to insert init parameters for TweetImageAdminMixin to override default
settings (display both checkboxes, image field name is 'image', text to tweet is str(obj))

```def __init__(self, *args, *kwargs):
    kwargs['text_or_image'] = False
    kwargs['tweet_image_field'] = 'tweeted_image'
    kwargs['tweet_field'] = 'tweet'
    super(Class, self).__init__(*args, **kwargs)
```

TweetAction
-------------
TweetAction is a mixin for ModelAdmins that adds support for tweeting thru the action menu. This is an alternative to
TweetableAdminMixin / TweetImageAdminMixin that facilitates tweeting something repeatedly.

The assumption is that a mass tweeting involves tweeting existing data, e.g. the tweet attribute of an object and any
existing image. If a choice as to what is tweeted should be made at tweet time, then a custom form + the action should
be implemented

1. Add the mixin as follows to classes that support tweeting (drop in replacement for TweetableAdminMixin)

class ObjectAdmin(TweetAction, models.ModelAdmin)

2. Add or modify the parent class init() to insert init parameters for TweetAction to override default
settings (image field name is None (no image present to be tweeted), text to tweet is str(obj))

```def __init__(self, *args, *kwargs):
    kwargs['tweet_image_field'] = 'tweeted_image'
    kwargs['tweet_field'] = 'tweet'
    super(Class, self).__init__(*args, **kwargs)
```


TODO
=====

* Upgrade to use new Twitter API
* Verify 3.3 compatability


[1]: http://mezzanine.jupo.org "Mezzanine CMS"
