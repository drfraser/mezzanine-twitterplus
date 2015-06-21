
from __future__ import unicode_literals

from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.defaultfilters import truncatechars
from django.contrib import messages

from mezzanine.twitter import get_auth_settings

try:
    from twitter import Api
except ImportError:
    Api = None

TWEET_CB_HTML = """
    <input id='id_send_tweet' name='send_tweet' type='checkbox'>
    <label class='vCheckboxLabel' for='id_send_tweet'>{}</label>
"""

IMAGE_CB_HTML = """
    <input id='id_tweet_image' name='tweet_image' type='checkbox'>
    <label class='vCheckboxLabel' for='id_tweet_image'>{}</label>
"""

FORMFIELD_HTML = """
<div class='send_tweet_container'>{}{}</div>
"""


def normalize(text, form='NFKC', collapse=True):
    """
    Normalize unicode, hyphens, whitespace

    Args:
        text: The string to normalize.
        form: Normal form for unicode normalization.
        collapse: Whether to collapse tabs and newlines down to spaces.

    By default, the normal form NFKC is used for unicode normalization. This
    applies a compatibility decomposition, under which equivalent characters are
    unified, followed by a canonical composition.
    See Python docs for information on normal forms:
    http://docs.python.org/2/library/unicodedata.html#unicodedata.normalize
    """
    # Normalize to canonical unicode (using NKFC by default)
    text = unicodedata.normalize(form, to_unicode(text))
    # Strip out any control characters (they occasionally creep in somehow)
    for control in CONTROLS:
        text = text.replace(control, u'')
    # Normalize hyphens (unify all dash, minus and hyphen characters,
    # remove soft hyphens)
    for hyphen in HYPHENS:
        text = text.replace(hyphen, u'-')
    text = text.replace(u'\u00AD', u'')
    # Normalize separate double quotes
    text = text.replace(u'\'\'', u'"').replace(u'``', u'"')
    # Possible further normalization to ascii:
    # \u201c \u201d -> \u0022
    text = text.replace(u'\u201c', u'"')
    text = text.replace(u'\u201d', u'"')
    for qu in [u'\u2018', u'\u2019', u'\u0060', u'\u00b4']:
        text = text.replace(qu, u'\'')

    # Normalize unusual whitespace not caught by unicodedata
    text = text.replace(u'\u000B', u' ').replace(u'\u000C', u' ').
                replace(u'\u0085', ' ')
    text = text.replace(u'\u2028', u'\n').replace(u'\u2029', u'\n').
                replace('\r\n', '\n').replace('\r', '\n')
    if collapse:
        text = ' '.join(text.split())
    else:
        # TODO: If not collapse, just normalize newlines to '\n'
        pass
    return text


def get_media_to_send(obj, tweet_image_field, default_image=None):
    """
    Encapsulated into helper function as there are issues around image field
    being a URL (text) or a file object and exactly what sort of file object
    -- some classes in Mezzanine have a 'file' that isn't one
    So function needs some work

    default_image: URL or default file to tweet if tweet_image_field not set
    """
    the_image = getattr(obj, self.tweet_image_field)
    if not the_image:
        the_image = default_image
    if the_image and hasattr(the_image, 'file'):
        return the_image.file
    else if the_image and hasattr(the_image, 'path'):
        f = ImageFile(open(settings.MEDIA_ROOT + the_image.path, 'r'))
        return f.file
    else:
        return the_image


class TweetImageAdminMixin(object):
    """
    Based on TweetableAdminMixin - adds support for tweeting an image
    """

    def __init__(self, *args, **kwargs):
        """
        'text_or_image' is a flag indicating if both checkboxes should be added
        If False, only no_tweet / tweet_with_image is supported
        If True, no_tweet / tweet_text / tweet_text_and_image
        'tweet_image_field' is the name of the object's image url attribute
        """
        self.text_or_image = True
        self.tweet_image_field = 'image'
        self.tweet_field = None
        if 'text_or_image' in kwargs:
            self.text_or_image = kwargs.pop('text_or_image')
        if 'tweet_image_field' in kwargs:
            self.image_field = kwargs.pop('tweet_image_field')
        if 'tweet_field' in kwargs:
            self.tweet_field = kwargs.pop('tweet_field')
        super(TweetImageAdminMixin, self).__init__(*args, **kwargs)

    def formfield_for_dbfield(self, db_field, **kwargs):
        """
        Enhanced version of TweetableAdminMixin's method
        """
        formfield = super(TweetImageAdminMixin,
            self).formfield_for_dbfield(db_field, **kwargs)
        if Api and db_field.name == "status" and get_auth_settings():
            def wrapper(render):
                def wrapped(*args, **kwargs):
                    rendered = render(*args, **kwargs)
                    text_label = _("Send Tweet")
                    image_label = _("Tweet with Image")
                    image_html = IMAGE_CB_HTML.format(image_label)
                    tweet_html = ""
                    if self.text_or_image:
                        tweet_html = TWEET_CB_HTML.format(text_label)
                    return mark_safe(rendered + FORMFIELD_HTML.format(
                        tweet_html, image_html))
                return wrapped
            formfield.widget.render = wrapper(formfield.widget.render)
        return formfield

    def save_model(self, request, obj, form, change):
        """
        Issue - 'tweet upon save' makes it not convenient to just repeat a tweet
        Added check to make sure Mezzanine obj CONTENT_STATUS_PUBLISHED
        Added call to message_user to reflect any Twitter errors
        Added call to normalize to deal with UTF8 issues
        """
        super(TweetImageAdminMixin, self).save_model(request, obj, form, change)
        if Api and obj.status == CONTENT_STATUS_PUBLISHED  and \
          ((self.tweet_or_image and request.POST.get("send_tweet", False)) or
           (not self.tweet_or_image and request.POST.get("tweet_image", False)):
            did_tweet = True
            auth_settings = get_auth_settings()
            # URL of the object i.e. the Mezzanine page
            # Is the full absolute URL if bit.ly etc not being used
            # thus Twitter is responsible for shortening URL
            obj.set_short_url()
            message_text = str(obj) \
                if not self.tweet_field else getattr(obj, self.tweet_field)
            # leave space for URLs
            message = normalize(truncatechars(message_text, 116))
            api = Api(*auth_settings)

            media_to_send = None
            if request.POST.get("tweet_image", False):
                # default image support??
                media_to_send = get_media_to_send(obj, self.tweet_image_field)

            tweet_error = ''
            try:
                if media_to_send:
                    api.PostMedia(status="{} {}".format(message,
                                    obj.short_url), media=media_to_send)
                else:
                    # checked off image to send, but no data
                    api.PostUpdate("{} {}".format(message, obj.short_url))
            except Exception as e:
                did_tweet = False
                if isinstance(e, TwitterError):
                    tweet_error = e[0][0]['message']
                else:
                    tweet_error = str(e)
            if media_to_send and hasattr(media_to_send, "close"):
                media_to_send.close()

            if did_tweet:
                self.message_user(request, 'Tweet has been sent',
                                  level=messages.SUCCESS)
            else:
                self.message_user(request,
                                  "There was an error: {}".format(tweet_error),
                                  level=messages.ERROR)


class TweetAction(object):
    """
    Adds support for tweeting thru the action menu
    """

    def __init__(self, *args, **kwargs):
        self.actions = ['tweet_item'] + self.actions
        self.tweet_image_field = None
        self.tweet_field = None
        if 'tweet_image_field' in kwargs:
            self.image_field = kwargs.pop('tweet_image_field')
        if 'tweet_field' in kwargs:
            self.tweet_field = kwargs.pop('tweet_field')
        super(TweetAction, self).__init__(*args, **kwargs)

    def tweet_item(self, request, queryset):
        auth_settings = get_auth_settings()
        api = Api(*auth_settings)
        tweet_data = []
        for obj in queryset:
            if obj.status == CONTENT_STATUS_PUBLISHED:
                obj.set_short_url()
                message_text = str(obj) \
                    if not self.tweet_field else getattr(obj, self.tweet_field)
                # leave space for URLs
                message = normalize(truncatechars(message_text, 116))

                media_to_send = None
                if self.tweet_image_field:
                    # default image support??
                    media_to_send = get_media_to_send(obj, self.tweet_image_field)

                if media_to_send and len(message) > 96:
                    tweet_data.append([False, message, obj, 'Message is too long'])
                else:
                    tweet_data.append([True, message, obj, media_to_send])
            else:
                tweet_data.append([False, message, obj, 'Item not published'])

        for tweet_info in tweet_data:
            if not tweet_info[0]:
                continue
            try:
                if tweet_info[3]:
                    api.PostMedia(status="{} {}".format(tweet_info[1],
                                tweet_info[2].short_url), media=tweet_info[3])
                else:
                    api.PostUpdate("{} {}".format(tweet_info[1],
                                                  tweet_info[2].short_url))
            except Exception as e:
                # code here to retry image retweet (if tweeting external images)
                # (e.g. 403s) or Twitter error
                tweet_info[0] = False
                if isinstance(e, TwitterError):
                    tweet_info.append(e[0][0]['message'])
            if tweet_info[3] and hasattr(tweet_info[3], "close"):
                tweet_info[3].close()

        if all([x[0] for x in tweet_data]):
            self.message_user(request, 'All tweets were sent',
                              level=messages.SUCCESS)
        else:
            for tweet_info in tweet_data:
                if not tweet_info[0]:
                    self.message_user(request,
                                      "Tweet Error for '{}': {}".format(
                                            normalize(tweet_info[2].title),
                                            tweet_info[-1]),
                                      level=messages.WARNING)

    tweet_item.short_description = "Tweet selected items"
