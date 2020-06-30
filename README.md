# StarBot
StarBot is an advanced, easy-to-use, reliable, 100% free, and highly customizable starboard bot.

## Bot Features:
 - Supports multiple starboards
 - Supports multiple normal and custom emojis for *each* starboard
 - Easy to use configuration, with default settings and per-starboard settings
 - Completely free

## Setup:
This bot is easy to set up and get going. The following directions are very specific and mostly so you can see how it works, but also gives you an idea of how to configure it for your needs. If you need further help, you can join the [support server](https://discord.gg/3gK8mSA).
 1. [Invite](https://discord.com/api/oauth2/authorize?client_id=700796664276844612&permissions=117824&scope=bot) the bot to your server.
 2. Create a channel called #starboard (or whatever you want to name it)
 3. Type `sb channel add <channel_name>` to add the starboard.
 4. Type `sb channel requiredstars 1` (Setting the number of stars for a message to get on the starboard to 1, so you can test it easily.
 5. Type 'sb channel selfstar <channel_name> true` (This allows you to star your own messages, otherwise it would be hard to test the bot)
 6. Now, we need to add an emoji. In this case, we are going to use the `star` emoji. Type `sb channel emoji add <channel_name> :star:`
 7. Now send a message in the channel, and react with the `star` emoji. It should appear on the starboard!

## Other Settings You Can Change:
 - requiredStars: How many points it needs before it appears on your starboard. 
  - Specific Starboard: `sb channel requiredstars <channel_name> <number_of_stars>`
  - Default Setting: 'sb defaults requiredstars <number_of_stars>`
 - requiredToLose: How *few* stars a message needs to have before it gets *removed* from a starboard.
Specific Starboard: `sb channel requiredtolose <channel_name> <number_of_stars>
Default Setting: `sb defaults requiredtolose <channel_name> <number_of_stars>
selfStar: Wether or not a user can star their own messages.
Specific Starboard: `sb channel selfstar <channel> <true/false>`
Default Setting: `sb defaults selfstar <true/false>`
linkEdits: Wether or not the starboard message should update if the original message get's edited.
Specific Starboard: `sb channel linkedits <channel> <true/false>`
Default Setting: `sb defaults linkedits <true/false>`
linkDeletes: Whether or not the starboard message should be deleted if the original message is deleted.
Specific Starboard: `sb channel linkdeltes <channel> <true/false>`
Default Setting: `sb defaults linkdeletes <true/false>`
Emojis: (Default is no emoji, and cannot be changed)
Add: `sb channel emoji add <channel> <emoji>`
Remove: `sb channel emoji remove <channel> <emoji>`
