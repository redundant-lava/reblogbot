import pytumblr, time, random
import re
import sys
import os
from time import sleep
from dotenv import dotenv_values
from datetime import datetime, timedelta
import logging
from logging.handlers import TimedRotatingFileHandler


def get_client(config) -> pytumblr.TumblrRestClient:
    '''
    logs into tumblr using keys saved in .env

    input:
    <config>: dict of keys, must include consumer_key, consumer_secret, oauth_token, oauth_secret

    returns: Tumblr client object
    '''
    client = pytumblr.TumblrRestClient(
        config['consumer_key'],
        config['consumer_secret'],
        config['oauth_token'],
        config['oauth_secret'])
    return client

def get_old_posts(client, blog, limit=200, logger=None):
    '''
    gets list of previously posted reblog keys

    input:
    <client>: TumblrRestClient
    <blog>: string url of blog to search posts
    <limit>: optional limit of posts (default 200)

    returns: list of reblog keys from last (limit) posts
    '''
    response_object = client.posts(blog, limit=limit)
    if response_object['posts']:
        posts = response_object['posts']
        reblog_keys = [ p['reblog_key'] for p in posts ]
        return reblog_keys
    else: #error
        if logger:
            logger.error('could not get response object')
        return None

def get_template(client, blog, id, logger=None):
    '''
    get template for a blog using post id. id can be found in the permalink url (18-digit number)

    input:
    <client>: TumblrRestClient
    <blog>: string url of blog
    <id>: int post id

    returns: dict {'title': 'Reblog Template (or whatever template title is)' 'comment': 'text for reblog comment', 'tags':[list, of, tags]}
    '''

    response_object = client.posts(blog, id=id)
    if response_object['posts']:
        posts = response_object['posts']
        if len(posts) == 1:
            content = posts[0]['trail'][0]['content_raw']
            try:
                found = re.search('<h1>(.+?)</h1><p>(.+?)</p>', content)
            except AttributeError:
                pass
            title = found.group(1)
            comment = found.group(2)
            tags = posts[0]['tags']
            template = {'title':title,
                        'comment': comment,
                        'tags':tags}
            return template
        else: # error
            if logger:
                logger.error('found more than one post')
            return None
    else: #error
        if logger:
            logger.error('couldn\'t retrieve post')
        return None

def get_usernames(text):
    '''
    returns list of usernames from text. usernames separated into their own paragraphs and start with @
    '''
    try:
        found = re.findall('<p>@(.+?)</p>', text)
    except AttributeError:
        pass

    return found

def reblog_by_tag(client, search_template, reblog_template, dni_template=None, previous_reblogs=None, logger=None, sleep_time=120, like_post=True):
    if dni_template:
        dni_users = set(get_usernames(dni_template['comment']))
        dni_tags = set(dni_template['tags'])
    else:
        dni_users=[] # none

    for tag in search_template['tags']:
        found_posts = client.tagged(tag, limit=20)
        found_posts = [c for c in found_posts if c["reblog_key"] not in previous_reblogs and c['blog_name'] not in dni_users]
        if logger is not None:
            logger.info(f'found {len(found_posts)} recent post(s) tagged #{tag}')

        #if no recent posts, search up to 24 hours previous
        hours = 12
        dt = datetime.today() - timedelta(hours=hours, minutes=0)
        while len(found_posts)==0 and hours <= 24:
            found_posts = client.tagged(tag, limit=20, before = datetime.timestamp(dt))
            found_posts = [c for c in found_posts if c["reblog_key"] not in previous_reblogs and c['blog_name'] not in dni_users]
            if logger is not None:
                logger.info(f'found {len(found_posts)} post(s) before {dt.strftime("%H:%M %p")} tagged #{tag}')
            hours += 12
            dt = datetime.today() - timedelta(hours=hours, minutes=0)

        post_count = 0
        for c in found_posts:
            dni_tag_intersection=[]
            if dni_tags:
                dni_tag_intersection = list(set(c['tags']) & dni_tags)

            if len(dni_tag_intersection)==0:

                #record post key so we don't reblog the same post
                previous_reblogs.add(c['reblog_key'])

                like_text=""
                if like_post:
                    client.like(c["id"],c["reblog_key"])
                    like_text="Liked & "

                client.reblog(reblog_args['blog'], id=c["id"], reblog_key=c["reblog_key"], state=reblog_args['state'], tags=reblog_template['tags'], comment=reblog_template['comment'], format=reblog_args['format'])
                post_count += 1
                if logger is not None:
                    post_text=reblog_args['state']+'ed'
                    logger.info(f"{like_text}{post_text}: " + tag + " - " + c["blog_name"] + ".tumblr.com" + " - " + c["slug"] + c["reblog_key"])
                time.sleep(sleep_time)
    return post_count



if __name__ == "__main__":

    # login configuration
    config = dotenv_values(".env.secret")  # config = {'consumer_key'="XXXX", consumer_secret='XXXX', oauth_token='XXXX', oauth_secret='XXXX'

    # blog arguments
    reblog_args = dotenv_values(".env.blog")

    # other controls
    like_post = True
    log_dir = 'log'
    run_continuously = True
    sleep_time = 30 # time in seconds to sleep before posting next tag search

    #################

    #set up logger
    logger = logging.getLogger()
    logname = "reblogbot.log"
    handler = TimedRotatingFileHandler("/".join([log_dir,logname]), when="midnight", interval=7)
    handler.suffix = "%Y%m%d"
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.info('logging start')

    client = get_client(config)  # log in

    # get templates
    search_template = get_template(client, reblog_args['blog'], reblog_args['search_template'], logger=logger)
    reblog_template = get_template(client, reblog_args['blog'], reblog_args['reblog_template'], logger=logger)
    dni_template = get_template(client, reblog_args['blog'], reblog_args['dni_template'], logger=logger)

    previous_reblogs = set(get_old_posts(client, reblog_args['blog'], limit=200, logger=logger))

    while(search_template is not None and reblog_template is not None):
        post_count = reblog_by_tag(client, search_template, reblog_template, dni_template = dni_template,
                        previous_reblogs=previous_reblogs, sleep_time=sleep_time, like_post=like_post, logger=logger)

        if post_count == 0:
            hr_delay = 2 # hours
            logger.info(f'no posts found with selected tags, sleeping for {hr_delay}hrs')
            dt = datetime.today() + timedelta(hours=hr_delay, minutes=0)
            logger.info(f'next tag search at {dt.strftime("%H:%M %p")}')
            time.sleep(1200*hr_delay)
        else:
            time.sleep(1200*12) #only search twice per day
            dt = datetime.today() + timedelta(hours=12, minutes=0)
            logger.info(f'{post_count} post(s) reblogged, next tag search at {dt.strftime("%H:%M %p")}')

        if not run_continuously:
            break

        #check for manual reblogs
        previous_reblogs.update(get_old_posts(client, reblog_args['blog'], limit=20))
        # update templates
        search_template = get_template(client, reblog_args['blog'], reblog_args['search_template'], logger=logger)
        reblog_template = get_template(client, reblog_args['blog'], reblog_args['reblog_template'], logger=logger)
        dni_template = get_template(client, reblog_args['blog'], reblog_args['dni_template'], logger=logger)
