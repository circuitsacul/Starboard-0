# StarBot
StarBot is an advanced, easy-to-use, reliable, free, and highly customizable discord starboard bot.

## Bot Features:
 - Supports multiple starboards
 - Supports multiple normal and custom emojis for *each* starboard
 - Easy to use configuration, with default settings and per-starboard settings
 - Completely free

(I plan to bring many more features, such as role awards, advanced whitelisting and blacklisting, auto star channels, etc. If you have any suggestions for what features you would like to see, you can use the `suggest <suggestion>` command.

## How to Read This:
Don't literally type out `<, >, [, ]`.
The words found inside of those symbols are called arguments. `<this_is_an_argument>`. You are supposed to replace them with the value you want, and again, you don't type the symbols (`<, >, [, ]`) themselves.

For example, say you wanted to make the bot repeat the word "hello" 10 times. The command to do this is `!repeat <word> [number_of_times=1]`. You would type `!repeat hello 10`. Notice how one of the arguments is inside of the `</>`, while another is inside of the `[/]`? The ones inside the square brackets are `optional arguments`. They have a default value, so you don't always have to type it out. For example, typing `!repeat hello` would repeat the word 1 time, because the default value for `number_of_times` is 1. The other argument, inside of the `</>`, is a required argument. If you don't set it, it will raise an error.

## Setup:
This bot is easy to set up and get going. The following directions are very specific and mostly so you can see how it works, but also gives you an idea of how to configure it for your needs. If you need further help, you can join the [support server](https://discord.gg/3gK8mSA).
 1. [Invite](https://discord.com/api/oauth2/authorize?client_id=700796664276844612&permissions=117824&scope=bot) the bot to your server.
 2. Create a channel called `#starboard` by typing (or whatever you want to name it)
 3. Type `sb channel add <channel_name>` to add the starboard.
 4. Type `sb channel requiredstars 1` (Setting the number of stars for a message to get on the starboard to 1, so you can test it easily.
 5. Type `sb channel selfstar <channel_name> true` (This allows you to star your own messages, otherwise it would be hard to test the bot)
 6. Now, we need to add an emoji. In this case, we are going to use the `star` emoji. Type `sb channel emoji add <channel_name> :star:`
 7. Now send a message in the channel, and react with the `star` emoji. It should appear on the starboard!

## Other Settings You Can Change:
 - requiredStars: How many points it needs before it appears on your starboard. 
   - Specific Starboard: `sb channel requiredstars <channel_name> <number_of_stars>`
   - Default Setting: `sb defaults requiredstars <number_of_stars>`
 - requiredToLose: How *few* stars a message needs to have before it gets *removed* from a starboard.
   - Specific Starboard: `sb channel requiredtolose <channel_name> <number_of_stars>`
   - Default Setting: `sb defaults requiredtolose <channel_name> <number_of_stars>`
