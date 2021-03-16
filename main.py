import discord
from discord.ext import commands
import asyncio
import aiohttp
import requests
from datetime import date, datetime, timedelta
import random
import asyncpraw
import config
#import heroku

client = discord.Client()


TOKEN = config.TOKEN
REDDIT_KEY = config.REDDIT_KEY
REDDIT_CLIENT_ID = config.REDDIT_CLIENT_ID

reddit = asyncpraw.Reddit(client_id=REDDIT_CLIENT_ID,
                     client_secret=REDDIT_KEY,
                     user_agent="Henteidev")

submissionList = []
onlineSince = datetime.now()

allowedChannels = []

# System functions -----------------------------------------------------------------------------------------------------------------
# Get hentai by id: Returns dictionary or False
async def getHentaiByID(id):
    if not str(id).isdigit():
        return False;

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get('http://nhentai.net/api/gallery/'+str(id)) as resp:
                response = await resp.json() # Await respone

                if "error" in response:
                    # Does not exist:
                    return False;

                else:
                    return response;
    except:
        print("Error: Web request failed. (ID)")

# Wait until
async def wait_until(dt):
    # sleep until the specified datetime
    now = datetime.now()
    await asyncio.sleep((dt - now).total_seconds())

# Run at
async def run_at(dt, coro):
    await wait_until(dt)
    return await coro

# Build daily hentai
async def buildDailyHentai(_channel):
    requestedID = random.randint(1,300000)

    response = await getHentaiByID(requestedID)
    while response == False:
        requestedID = random.randint(1,300000)
        response = await getHentaiByID(requestedID)
        response = await getHentaiByID(requestedID)

    await infoEmbedMessage(response, _channel)

#delete if wrong Channel
async def checkAllowedChannel(_channel):
    if _channel in allowedChannels:
        await buildEmbedMessage("Wrong channel.","Use channels:",allowedChannels,discord.Colour.red(),"This message will delete itself later.",_channel,[True],10 )

# Helper functions -----------------------------------------------------------------------------------------------------------------
# Get tags: Returns String
async def getGenresString(response):
    tagsListDicts = response["tags"]
    tagsString = " "
    for i in tagsListDicts:
        tagsString += (str(i['name']))+", "
    if tagsString == " ":
        tagsString = "ERROR: could not get tags"
    tagsString = tagsString[:-2]
    if len(tagsString) > 1000:
        tagsString = tagsString[:1000]+"..."

    return tagsString;

# catch for loli in tags
async def catchLoliTags(response,_channel):
    tagString = await getGenresString(response)
    if "loli" in tagString or "lolicon" in tagString or "shota" in tagString or "shotacon" in tagString or "guro" in tagString:
        await buildEmbedMessage("Oewh.",["Contains🥀illegal🥶tags😲."],["😍😊😳"],discord.Colour.red(),"This message will delete itself later.",_channel,[True],10 )
        return True;

    return False;

# Create info embed with response: Returns message
async def infoEmbedMessage(_response, _channel):
    # ID
    requestedID = str(_response["id"])

    # Japanese title
    nameJapanese = _response["title"]["japanese"]
    if nameJapanese == "":
        nameJapanese = "NOT AVAILABLE"

    # English title
    nameEnglish = _response["title"]["pretty"]
    if nameEnglish == "":
        nameEnglish = _response["title"]["english"]
        if nameEnglish == "":
            nameEnglish = "NOT AVAILABLE"

    # Tags
    tagsString = await getGenresString(_response)

    # Number of pages
    numPages = str(_response["num_pages"])
    if numPages == "":
        numPages = "ERROR: could not get pages"

    # Number of favorites
    numFavorites = str(_response["num_favorites"])
    if numFavorites == "":
        numFavorites = "ERROR: could not get favorites"

    # Upload date
    uploadDate = str(datetime.utcfromtimestamp(_response["upload_date"]).strftime('%Y-%m-%d %H:%M:%S'))
    if uploadDate == "":
        uploadDate = "ERROR: could not get release date"

    # Cover image
    mediaID = _response["media_id"]
    coverURL = "https://t.nhentai.net/galleries/"+mediaID+"/cover.jpg"

    # Make Discord Embed
    embed = discord.Embed(colour = discord.Colour.red())

    embed.set_thumbnail(url = coverURL)
    embed.set_author(name = "🚂🚂🥛🥛🥛Choo choo here comes the coom train🥛🥛🥛🚂🚂")
    embed.add_field(name = "🆔nHentai ID: ", value = requestedID, inline = True)
    embed.add_field(name = "🗽English Title: ", value = nameEnglish, inline = True)
    embed.add_field(name = "🎌Japanese Title: ", value = nameJapanese, inline = True)
    embed.add_field(name = "⭐Favorites: ", value = numFavorites, inline = True)
    embed.add_field(name = "📄Pages: ", value = numPages, inline = True)
    embed.add_field(name = "🕑Upload Date: ", value = uploadDate, inline = True)
    embed.add_field(name = "🏷️Tags: ", value = tagsString, inline = True)
    embed.add_field(name = "🌍Link:",value="https://nhentai.net/g/"+str(requestedID), inline = False)
    embed.set_footer(text='Data provided by nHentai. Created by EpicGamer and AlphaAlpaka.',icon_url="https://cdn.discordapp.com/attachments/795320210998689810/795361837066616852/hentei.jpg")

    # Send message
    return await _channel.send(embed = embed);

# Create embeded message
async def buildEmbedMessage(_title, _headers, _contents, _color, _footer, _channel, _inline, _deleteTimer):
    embed = discord.Embed(colour = _color)
    embed.set_author(name = _title)

    for h, c, i in zip(_headers, _contents, _inline):
        embed.add_field(name = h, value = c, inline = i)

    if _footer == "DEFAULT":
        _footer = '🍜Data provided by nHentai. 🔥Created by EpicGamer and AlphaAlpaka.🔥'
    embed.set_footer(text=_footer,icon_url="https://cdn.discordapp.com/attachments/795320210998689810/795361837066616852/hentei.jpg")

    if _deleteTimer == 0:
        return await _channel.send(embed = embed);
    else:
        return await _channel.send(embed = embed,delete_after = _deleteTimer);

# Returns the response with payload
async def getPayloadSearch(payload):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url='https://nhentai.net/api/galleries/search', params=payload) as resp:
                response = await resp.json() # Await response
                return response;
    except:
        print("Error: Web request failed. (Payload)")

# Returns the requested search amount
async def getRequestedAmount(messagecontent):
    if str(messagecontent[-2:]).isdigit():
        requestedAmount = int(messagecontent[-2:])
        messagecontent = messagecontent[:-3]
    else:
        if str(messagecontent[-1:]).isdigit():
            requestedAmount = int(messagecontent[-1:])
            messagecontent = messagecontent[:-2]
        else:
            requestedAmount = 5

    return requestedAmount, messagecontent;


# Bot functions --------------------------------------------------------------------------------------------------------------------
# Initialize bot
@client.event
async def on_ready():
    print(f'Bot is connected.')
    await client.change_presence(activity=discord.Activity(type=discord.ActivityType.playing, name=" h!help "))

    guild = client.get_guild(796469914151026718)
    allowedChannels.append(discord.utils.get(guild.text_channels, name="spam"))
    #allowedChannels.append(discord.utils.get(guild.text_channels, name="bot-test"))

    """
    # Schedule daily HENTEI
    guild = client.get_guild(796469914151026718)
    channel = discord.utils.get(guild.text_channels, name="daily-hentei")
    try:
        time = datetime.now() + timedelta(hours = 7)
        loop = asyncio.get_event_loop()
        loop.create_task(run_at(time, buildDailyHentai(channel)))
        loop.run_until_complete()
    except:
        print("Daily hentei scheduled for "+str(time.strftime("%H:%M:%S"))+".")
        channel = discord.utils.get(guild.text_channels, name="general")
        #await buildEmbedMessage("Connected!",["Are you ready for freddy?"],["Are you?"],discord.Color.blue(),"Set daily Hentei for "+str(time.strftime("%H:%M:%S"))+".",channel,[True])

    #channel = discord.utils.get(guild.text_channels, name="general")
    #await buildEmbedMessage("Connected!",[],[],discord.Color.blue(),"Initialized successfully!",channel,[])
"""
    # Cache reddit request
    # Make subreddit request
    print("Fetching croppedhentai...")
    try:
        subreddit = await reddit.subreddit("croppedHentaiMemes")
        async for submission in subreddit.hot(limit=100):
            submissionList.append(submission)
        print("Completed fetching r/croppedHentaiMemes on "+str(datetime.now().strftime("%H:%M:%S")))
    except:
        print("Something went wrong while trying to fetch reddit.")


# Bot commands ---------------------------------------------------------------------------------------------------------------------
# Commands
@client.event
async def on_message(message):
    channel = message.channel
    messageAuthor = message.author
    guild = message.guild

    #filter wrong channel
    if channel in allowedChannels:
        # Help
        if message.content.startswith("h!help"):


            title = "👊😎Hentei : Help page😎👊"
            headers = ["h!help",
            "h!search [ID] [amount, optional, max 25]",
            "h!title [name] [amount, optional, max 25]",
            "h!character [name] [amount, optional, max 25]",
            "h!tag [tag(s), seperated by space, - to block tag(s)] [amount, optional, max 25]",
            "h!parody [name] [amount, optional, max 25]",
            "h!random",
            "h!cropped",
            "h!credits"]
            contents = ["👉help, OmO",
            "👉Takes a nHentai ID, returns information and reader",
            "👉Gives a list of hentai with the specified title",
            "👉Gives a list of hentai with the specified character",
            "👉Gives a list of hentai with the specified tag(s)",
            "👉Gives a list of hentai parodies",
            "👉Gives information about random hentai",
            "👉Gives a random image from r/croppedHentaiMemes",
            "👉Shows the credits and invite link"]
            color = discord.Color.red()
            footer = "DEFAULT"
            inline = [False, False, False, False, False, False, False, False, False]
            await buildEmbedMessage(title, headers, contents, color, footer, channel, inline,30)

        # Search by title
        if message.content.startswith("h!title "):

            requestedAmount, requestedTagString = await getRequestedAmount(message.content)
            requestedTagString = requestedTagString[8:]

            #payload = {'query':f'title:{requestedTagString}','page': 1, 'sort': 'popular'}
            #payload = {'query':'group:nakayohi-mogudan'}
            payload = {'query':f'title:{requestedTagString}','page': 1, 'sort':'popular'}
            response = await getPayloadSearch(payload)

            # Handle received JSON Data
            # Contains "result" --> Array[i] --> dictionary containing Hentai
            resultArray = response["result"]
            resultLength = int(len(resultArray))
            embed = discord.Embed()
            embed.set_author(name = "🔎Result of title search: '"+requestedTagString+"', showing top "+str(requestedAmount)+"🔎")
            if len(resultArray) == 0:
                await buildEmbedMessage("Oewh.", ["Error: Something went wrong"], ["The search did not get any results or the request timed out."], discord.Colour.red(),"DEFAULT",message.channel, [False],30)
                return 0;

            if requestedAmount > resultLength:
                requestedAmount = resultLength

            # Create embed
            for r in resultArray[:requestedAmount]:
                title = r["title"]["pretty"]
                if title == "":
                    title = r["title"]["english"]
                    if title == "":
                        title = "NOT AVAILABLE"
                id = r["id"]
                favorites = r["num_favorites"]
                embed.add_field(name = "🗽"+title, value = "🆔nHentai ID: "+str(id)+" \n⭐Favorites: "+str(favorites)+"\n ", inline = False)
                embed.set_thumbnail(url="https://t.nhentai.net/galleries/"+resultArray[0]["media_id"]+"/cover.jpg")

            await channel.send(embed = embed)

        # Search by character name.
        if message.content.startswith("h!character "):

            requestedAmount, requestedTagString = await getRequestedAmount(message.content)
            requestedTagString = requestedTagString[12:]

            #payload = {'query':f'title:{requestedTagString}','page': 1, 'sort': 'popular'}
            #payload = {'query':'group:nakayohi-mogudan'}
            payload = {'query':f'character:{requestedTagString}','page': 1, 'sort':'popular'}
            response = await getPayloadSearch(payload)

            # Handle received JSON Data
            # Contains "result" --> Array[i] --> dictionary containing Hentai
            resultArray = response["result"]
            resultLength = int(len(resultArray))
            embed = discord.Embed()
            embed.set_author(name = "🔎Result of character search: '"+requestedTagString+"', showing top "+str(requestedAmount)+"🔎")
            if len(resultArray) == 0:
                await buildEmbedMessage("Oewh.", ["Error: Something went wrong"], ["The search did not get any results or the request timed out."], discord.Colour.red(),"DEFAULT",message.channel, [False],30)
                return 0;

            if requestedAmount > resultLength:
                requestedAmount = resultLength

            # Create embed
            for r in resultArray[:requestedAmount]:
                title = r["title"]["pretty"]
                if title == "":
                    title = r["title"]["english"]
                    if title == "":
                        title = "NOT AVAILABLE"
                id = r["id"]
                favorites = r["num_favorites"]
                embed.add_field(name = "🗽"+title, value = "🆔nHentai ID: "+str(id)+" \n⭐Favorites: "+str(favorites)+"\n ", inline = False)
                embed.set_thumbnail(url="https://t.nhentai.net/galleries/"+resultArray[0]["media_id"]+"/cover.jpg")

            await channel.send(embed = embed)

        # Search by parody
        if message.content.startswith("h!parody "):


            requestedAmount, requestedTagString = await getRequestedAmount(message.content)
            requestedTagString = requestedTagString[9:]

            payload = {'query':'parodies:'+str(requestedTagString),'page': 1, 'sort': 'popular'}
            response = await getPayloadSearch(payload)

            # Handle received JSON Data
            # Contains "result" --> Array[i] --> dictionary containing Hentai
            resultArray = response["result"]
            resultLength = int(len(resultArray))
            embed = discord.Embed()
            embed.set_author(name = "🕵🔎‍Result of parody search: '"+requestedTagString+"', showing top "+str(requestedAmount)+"🔎🕵")
            if len(resultArray) == 0:
                await buildEmbedMessage("Oewh.", ["Error: Something went wrong"], ["The search did not get any results or the request timed out."], discord.Colour.red(),"DEFAULT",message.channel, [False],30)
                return 0;
            #embed.set_thumbnail(url="https://t.nhentai.net/galleries/"+resultArray[0]["media_id"]+"/cover.jpg")
            if not requestedAmount <= resultLength:
                requestedAmount = 5

            # Create embed
            for r in resultArray[:requestedAmount]:
                title = r["title"]["pretty"]
                if title == "":
                    title = r["title"]["english"]
                    if title == "":
                        title = "NOT AVAILABLE"
                id = r["id"]
                favorites = r["num_favorites"]
                embed.add_field(name = "🗽"+title, value = "🆔nHentai ID: "+str(id)+" \n⭐Favorites: "+str(favorites)+"\n ", inline = False)
                #embed.set_thumbnail(url="https://t.nhentai.net/galleries/"+resultArray[0]["media_id"]+"/cover.jpg")

            await channel.send(embed = embed)

        # Search by tag
        if message.content.startswith("h!tag "):

            requestedAmount, requestedTagString = await getRequestedAmount(message.content)
            requestedTagString = requestedTagString[6:]
            #catch lolicon

            if "loli" in requestedTagString or "lolicon" in requestedTagString or "shota" in requestedTagString or "shotacon" in requestedTagString:
                await buildEmbedMessage("Oewh.", ["Sorry, this content is not allowed here."], ["Please try another search query."], discord.Colour.red(),"DEFAULT",message.channel, [False],30)
                return;


            payload = {'query':'tag:'+str(requestedTagString),'page': 1, 'sort': 'popular'}
            response = await getPayloadSearch(payload)

            # Handle received JSON Data
            # Contains "result" --> Array[i] --> dictionary containing Hentai
            resultArray = response["result"]
            resultLength = int(len(resultArray))
            embed = discord.Embed()
            embed.set_author(name = "🕵🔎Result of tag search: '"+requestedTagString+"', showing top "+str(requestedAmount)+"‍🔎🕵")
            if len(resultArray) == 0:
                await buildEmbedMessage("Oewh.", ["Error: Something went wrong"], ["The search did not get any results or the request timed out."], discord.Colour.red(),"DEFAULT",message.channel, [False],30)
                return 0;
            #embed.set_thumbnail(url="https://t.nhentai.net/galleries/"+resultArray[0]["media_id"]+"/cover.jpg")
            if requestedAmount > resultLength:
                requestedAmount = resultLength

            # Create embed
            for r in resultArray[:requestedAmount]:
                title = r["title"]["pretty"]
                if title == "":
                    title = r["title"]["english"]
                    if title == "":
                        title = "NOT AVAILABLE"
                id = r["id"]
                favorites = r["num_favorites"]
                embed.add_field(name = "🗽"+title, value = "🆔nHentai ID: "+str(id)+" \n⭐Favorites: "+str(favorites)+"\n ", inline = False)
                embed.set_thumbnail(url="https://t.nhentai.net/galleries/"+resultArray[0]["media_id"]+"/cover.jpg")

            await channel.send(embed = embed)

        # Search by id
        if message.content.startswith("h!search ") or message.content.startswith("h!id "):

            if message.content.startswith("h!search "):
                requestedID = message.content[9:]
            else:
                requestedID = message.content[5:]

            currentPage = 1
            READING_TIME = 2


            response = await getHentaiByID(requestedID)
            if response == False:
                #Does not exist
                await buildEmbedMessage("Oewh.", ["Error: Something went wrong"], ["Your requested id could not be found or does not exist. Please try another id."], discord.Colour.red(),"DEFAULT",message.channel, [False],30)

            else:

                if await catchLoliTags(response,channel):
                    return;

                message = await infoEmbedMessage(response, channel)
                nameEnglish = response["title"]["english"]
                mediaID = response["media_id"]
                numPages = response["num_pages"]
                endTime = datetime.now() + timedelta(minutes = READING_TIME)

                while True:
                    # End loop after certain amount of time
                    if datetime.now() >= endTime:
                        break

                    # Add reaction to message
                    try:
                        await message.add_reaction('📖')
                    except:
                        pass
                    try:
                        await message.add_reaction('💦')
                    except:
                        pass

                    read = '📖'
                    quit = '💦'

                    valid_reactions = ['📖', '💦']

                    channel = message.channel

                    def check(reaction, user):
                        return user == messageAuthor and str(reaction.emoji) in valid_reactions
                    reaction, user = await client.wait_for('reaction_add', timeout = 12000, check = check)

                    # Process reaction
                    if str(reaction.emoji) == read:
                        # Build Embed
                        embed = discord.Embed(colour = discord.Colour.red())
                        embed.set_author(name = nameEnglish+", Page: "+str(currentPage))
                        embed.set_image(url = "https://i.nhentai.net/galleries/"+str(mediaID)+"/"+str(currentPage)+".jpg")

                        imageMessage = await channel.send(embed = embed, delete_after = 120)


                        while True:
                            # End loop after certain amount of time
                            if datetime.now() >= endTime:
                                break

                            # Add reactions
                            try:
                                await imageMessage.add_reaction('⬅️')
                            except:
                                pass
                            try:
                                await imageMessage.add_reaction('➡️')
                            except:
                                pass
                            try:
                                await imageMessage.add_reaction('❌')
                            except:
                                pass

                            prev = '⬅️'
                            next = '➡️'
                            stop = '❌'
                            quit = '💦'

                            valid_reactions = ['⬅️', '➡️', '❌', '💦']

                            def check(reaction, user):
                                return user == messageAuthor and str(reaction.emoji) in valid_reactions
                            reaction, user = await client.wait_for('reaction_add', timeout=12000, check = check)

                            # Process reaction
                            if str(reaction.emoji) == prev:
                                # Previous page
                                if currentPage > 1:
                                    currentPage -= 1
                                embed = discord.Embed(colour = discord.Colour.red())
                                embed.set_author(name = response["title"]["english"]+", Page: "+str(currentPage))
                                embed.set_image(url = "https://i.nhentai.net/galleries/"+str(mediaID)+"/"+str(currentPage)+".jpg")
                                embed.add_field(name = "Navigation:", value="⬅️prev. page//➡️next page//❌stop reading")
                                embed.set_footer(text='🕑Reading time left: '+ str(endTime-datetime.now())[:-7] +'! \n Data provided by nHentai. Created by EpicGamer and AlphaAlpaka.',icon_url="https://cdn.discordapp.com/attachments/795320210998689810/795361837066616852/hentei.jpg")

                                #Edit message
                                await imageMessage.edit(embed = embed)

                            elif str(reaction.emoji) == next:
                                # Next page
                                if currentPage < int(numPages):
                                    currentPage += 1
                                embed = discord.Embed(colour = discord.Colour.red())
                                embed.set_author(name = nameEnglish+", Page: "+str(currentPage))
                                embed.set_image(url = "https://i.nhentai.net/galleries/"+str(mediaID)+"/"+str(currentPage)+".jpg")
                                embed.add_field(name = "Navigation:", value="⬅️prev. page//➡️next page//❌stop reading")
                                embed.set_footer(text='🕑Reading time left: '+ str(endTime-datetime.now())[:-7] +'! \n Data provided by nHentai. Created by EpicGamer and AlphaAlpaka.',icon_url="https://cdn.discordapp.com/attachments/795320210998689810/795361837066616852/hentei.jpg")

                                #Edit message
                                await imageMessage.edit(embed = embed)

                            elif str(reaction.emoji) == stop:
                                # Stop reading
                                try:
                                    await imageMessage.delete()
                                except:
                                    pass
                                break

                            else:
                                #Delete messages
                                try:
                                    await message.delete()
                                except:
                                    pass
                                try:
                                    await imageMessage.delete()
                                except:
                                    pass
                                break

                    else:
                        #Delete messages
                        await message.delete()
                        break

                #Delete messages
                try:
                    await message.delete()
                except:
                    pass
                try:
                    await imageMessage.delete()
                except:
                    pass

        # Search random
        if message.content.startswith("h!random"):

            requestedID = random.randint(1,300000)

            response = await getHentaiByID(requestedID)



            while response == False:
                requestedID = random.randint(1,300000)
                response = await getHentaiByID(requestedID)
                response = await getHentaiByID(requestedID)

            if await catchLoliTags(response,channel):
                return;


            await infoEmbedMessage(response, channel)

        # Shows cradits & invite link
        if message.content.startswith("h!credits"):

            title = "About croppedHentei"
            headers = ["🧠Idea and Code👩‍💻","💾Data and API backend🚀","🏚Join the HenteiBot server!🗿"]
            contents = ["EpicGamer, AlphaAlpaka","nhentai.net, r/croppedHentaiMemes","https://discord.gg/uH7g5DfsF5"]
            color = discord.Color.gold()
            footer = "🍜Thanks for using croppedHentei, a customized version of Hentei.🗿"
            inline = [False,False,False]

            embed = discord.Embed(colour = color)
            embed.set_author(name = title)

            for h, c, i in zip(headers, contents, inline):
                embed.add_field(name = h, value = c, inline = i)

            embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/795320210998689810/795361837066616852/hentei.jpg")
            embed.set_footer(text=footer,icon_url="https://cdn.discordapp.com/attachments/795320210998689810/795361837066616852/hentei.jpg")

            await channel.send(embed = embed)

        # Gives debug information
        if message.content.startswith("h!debug"):
            title = "Info on user:"
            headers = ["UserID","Author ID?","Guild ID","Channel ID"]
            contents = [str(messageAuthor),str(messageAuthor.id),str(message.guild.id),str(message.channel)]
            color = discord.Color.red()
            footer = "DEFAULT"
            inline = [False, False, False, False]
            await buildEmbedMessage(title, headers, contents, color, footer, channel, inline)

        # Get reddit anime legs post.
        if message.content.startswith("h!cropped"):
            # Get random post from reddit result
            post = random.randint(2, 100)
            while post > len(submissionList):
                post = random.randint(2, 100)

            result = submissionList[post]

            # Make embed message
            embed = discord.Embed(colour = discord.Colour.red())
            embed.set_author(name = result.title)
            embed.set_image(url = result.url)
            embed.set_footer(text="🍜Data provided by r/croppedHentaiMemes. Created by EpicGamer and AlphaAlpaka.\n Last fetched at "+onlineSince.strftime("%H:%M:%S"),icon_url="https://cdn.discordapp.com/attachments/795320210998689810/795361837066616852/hentei.jpg")

            imageMessage = await channel.send(embed = embed)

    else:
        # If command is not posted in NSFW channel, send error message
        if message.content.startswith("h!"):
            allowedChannelNames = ""
            for c in allowedChannels:
                allowedChannelNames += (c.name+" ")

            await buildEmbedMessage("Oewh.", ["This is not an NSFW channel"], ["Use these channels:"+allowedChannelNames], discord.Colour.red(),"DEFAULT",message.channel, [False],7)
            await message.delete()


client.run(TOKEN)
