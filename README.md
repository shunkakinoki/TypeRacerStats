## TypeRacerStats
**TypeRacerStats** is a [**Discord**](https://discord.com/) bot partnered with with [**TypeRacer**](http://typeracer.com/), and it comes with over 35 commands to provide extensive statistics and features for users. Many of them are designed to help with improvement on the site. Run `-help` or refer to the **commands** section below.


## Commands
Some commands are _multiverse_, which means they provide statistics regardless of the TypeRacer—separate environments of TypeRacer with distinct texts, leaderboards, and scores—selected.

Another feature that some commands have is the ability to _link_ your Discord account to a TypeRacer account; for commands with said feature, linked users will not have to type their TypeRacer username every time. This can be done using the `-link [typeracer_username]` command.

Finally, some commands' functionalities are limited according to the bot permissions a user has: regular, bot admin, or bot owner.

### Info
Info commands provide information for the bot.
| Name              | Example | Function                                                                                               | Aliases        |
|:------------------|:-------:|--------------------------------------------------------------------------------------------------------|----------------|
| `-help [command]` | View    | Returns information for given command. Case sensitive and aliases may be used in place of `[command]`. | `h`            |
| `-info`           | View    | Returns information about the bot.                                                                     | `abt`, `about` |
| `-invite`         | View    | Returns an invite link for the bot. Refer to the **Invite/Permissions** section below for permissions. | None           |
| `-donate`         | View    | Returns donation link to support the bot.                                                              | `support`      |

### Configuration
Configuration commands allow server admins to change the bot's prefix and users to configure the settings of their Discord account with regards to the bot.
| Name                             | Example | Function                                                                                     | Aliases |
|:---------------------------------|:-------:|----------------------------------------------------------------------------------------------|---------|
| `-changeprefix [prefix]`         | View    | Changes the bot's prefix on the server.                                                      | `cp`    |
| `-register [typeracer_username]` | View    | Links Discord account to TypeRacer account. [mu]                                             | `link`  |
| `-setuniverse [universe]`        | View    | Links Discord account to provided TypeRacer universe; defaults to `play` universe. [mu] [li] | `su`    |
| `-toggledessle`                  | View    | Toggles Desslejusted option for `realspeed`, `lastrace`, `realspeedaverage`, and `raw`. [li] | `tg`    |

### Basic
Basic commands do not require a user's information to be downloaded to provide statistics.

### Advanced

### Other

[mu]: https://img.shields.io/badge/-multiverse-blue
[li]: https://img.shields.io/badge/-link-blue
[ba]: https://img.shields.io/badge/-bot%20admin-blue
[bo]: https://img.shields.io/badge/-bot%20owner-blue

## Credits
Thank you to:
* the members of the [**TypeRacer Discord Server**](https://discord.com/invite/typeracer) for command suggestions;
* http://typeracerdata.com/ for some of its APIs and database.


## Invite/Permissions
The bot can be invited using [this link](https://discord.com/api/oauth2/authorize?client_id=742267194443956334&permissions=378944&scope=bot). The default prefix is `-`, and it can be changed with `-changeprefix [prefix]`.
### Text Permissions
- [x] Send Messages
- [x] Embed Links
- [x] Attach Files
- [x] Read Message History
- [x] Use External Emojis
- [x] Add Reactions


## Support
If you want to contribute towards hosting fees, refer to the following [link](https://www.paypal.me/e3e2).