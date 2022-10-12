# reblogbot
simple python script to reblog Tumblr posts automatically.

## requirements
**python 3.10**
use `pip install -r requirements.txt` to install all package requirements. 

## Search and Reblog Template
reblog bot uses search and reblog template posts to allow you to easily change the parameters without restarting the bot. Example posts are shown in `search_and_reblog_template_example.png`.  

![image](https://github.com/redundant-lava/reblogbot/blob/main/search_and_reblog_template_example.png?raw=true)  

## Do Not Interact Template
reblog bot also has an optional DNI template, to prevent it from interacting with specific tags or users. Example template is shown in `dni_template.png`  

![image](https://github.com/redundant-lava/reblogbot/blob/main/dni_template.png?raw=true)

## Connecting the templates to the bot
First make sure that your customer key and OAuth key are registered with your Tumblr blog. If you don't have an API key you will need to register your application with Tumblr. Store these four keys in a local .env or .env.secret file and do not share them.

Next you need to create a .env.blog file with the details of the blog you will be reblogging from and how you want the bot to behave. There is an example in `.env.blog`

```
blog = 'lukanettearchive.tumblr.com'
state = 'published' # Specify one of the following: published, draft, queue, private
reblog_template = 697842870775840768 # post id
search_template = 697843817671426048
dni_template = 697845282470313984
format = "html"
```

to get the post id for your templates, use Inspect Element from your blog page to find the post's header and permalink. The post id is the number shown after your blog name.

![image](https://github.com/redundant-lava/reblogbot/blob/main/post_id_example.png?raw=true)



