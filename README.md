# TypeRacerStats
**TypeRacerStats** is a [**Discord**](https://discord.com/) bot partnered with with [**TypeRacer**](http://typeracer.com/), and was made with the [**Discord.py API**](https://pypi.org/project/discord.py/), TypeRacer APIs, [**TypeRacerData**](http://typeracerdata.com/) APIs, [**SQLite**](https://www.sqlite.org/index.html), and various Python libraries (can be found in `requirements.txt`). It comes with over 35 commands to provide extensive statistics and features for users. Many of them are designed to help with improvement on the site. Run `-help` or refer to the **commands** section below.


## Commands
Some commands are ![mu], which means they provide statistics regardless of the TypeRacer—separate environments of TypeRacer with distinct texts, leaderboards, and scores—selected.

Another feature that some commands have is the ability to ![li] your Discord account to a TypeRacer account; for commands with said feature, linked users will not have to type their TypeRacer username every time. This can be done using the `-link [typeracer_username]` command.

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
| Name                             | Example | Function                                                                                       | Aliases |
|:---------------------------------|:-------:|------------------------------------------------------------------------------------------------|---------|
| `-changeprefix [prefix]`         | View    | Changes the bot's prefix on the server.                                                        | `cp`    |
| `-register [typeracer_username]` | View    | Links Discord account to TypeRacer account. ![mu]                                              | `link`  |
| `-setuniverse [universe]`        | View    | Links Discord account to provided TypeRacer universe; defaults to `play` universe. ![mu] ![li] | `su`    |
| `-toggledessle`                  | View    | Toggles Desslejusted option for `realspeed`, `lastrace`, `realspeedaverage`, and `raw`. ![li]  | `tg`    |

### Basic
Basic commands do not require a user's information to be downloaded to provide statistics.
| Name                                                 | Example | Function                                                                                                   | Aliases                          |
|:-----------------------------------------------------|:-------:|------------------------------------------------------------------------------------------------------------|----------------------------------|
| `-stats [user]`                                      | View    | Returns basic stats for given user. ![mu] ![li]                                                            | `prof`, `profile`                |
| `-getdata [user]`                                    | View    | Downloads given user's data; **Advanced** commands may be used after. ![li]                                | `dl`, `gd`, `download,`          |
| `-today [user] <date>`                               | View    | Downloads given user's data for specified date. `yesterday`, `yday`, `yd` are special aliases. ![li]       | `day`, `yesterday`, `yday`, `yd` |
| `-realspeed [user] <race_num>` or `-realspeed [url]` | View    | Returns [realspeeds](https://bit.ly/typeracerspeeds) for given race. ![mu] ![li]                           | `rs`                             |
| `-realspeedaverage [user] <first_race> <last_race>`  | View    | Returns the realspeed average for given race interval. <br/>![ba] may request up to 150 races. ![mu] ![li] | `rsa`, `rsa*`                    |
| `-raw [user] <race_num>` or `-raw [url]`             | View    | Returns realspeeds and _raw_ speed (speed with correction time omitted) for given race. ![mu] ![li]        | None                             |
| `-lastrace [user] <race_num>` or `-lastrace [url]`   | View    | Returns all users' realspeeds ranked by unlagged for given race. ![mu] ![li]                               | `lr`, `last`                     |
| `-leaderboard [category] <amount>`                   | View    | Returns a leaderboard for given category: `races/points/textstyped/textbests/toptens`.                     | `lb`                             |
| `-competition <category>`                            | View    | Returns the daily competition for specified category: `points/races/wpm`; defaults to `points` ![mu]       | `comp`                           |
| `-lastonline [user]`                                 | View    | Returns the last time a user played. ![mu] ![li]                                                           | `lo`, `ls`, `lastseen`           |
| `-medals [user]`                                     | View    | Returns the medals a user has. ![li]                                                                       | None                             |
| `-toptens [user]`                                    | View    | Returns the number of text top 10s a user holds. ![li]<br/>![ba] can request JSON breakdowns with `10*`.   | `10`, `10*`, `toptens*`          |

### Advanced (all require `-getdata`)
Advanced commands provide detailed statistical calculations, graphs, and services aimed to help users improve their typing speed and TypeRacer statistics.
| Name                                              | Example | Function                                                                                                               | Aliases            |
|:--------------------------------------------------|:-------:|------------------------------------------------------------------------------------------------------------------------|--------------------|
| `-top [user] [wpm/points]`                        | View    | Returns user's top 10 races sorted by specified category. ![li]                                                        | `best`             |
| `-worst [user] [wpm/points]`                      | View    | Returns user's worst 10 races sorted by specified cateogry. ![li]                                                      | `bottom`           |
| `-racedetails [user]`                             | View    | Returns detailed breakdown of user's races. ![li]                                                                      | `rd`               |
| `-textbests [user]`                               | View    | Returns user's top 5 texts, worst 5 texts, and text bests average (average of best in each text). ![li]                | `tb`               |
| `-personalbest [user] <text_ID>`                  | View    | Returns user's average, best, and worst on specified `text_id`. Defaults to last-raced text if none provided. ![li]    | `pb`               |
| `-unraced [user] <length>`                        | View    | Returns 5 randomly unraced texts under `length` characters. ![li]                                                      | `ur`               |
| `-textsunder [user] [wpm] <length>`               | View    | Returns 5 randomly raced texts under `wpm` wpm and `length` characters. ![li]                                          | `tu`               |
| `-textslessequal [user] [num] [wpm/points/times]` | View    | Returns number of texts typed more than or equal to `num` in specified category.                                       | `tle`, `tor`, `to` |
| `-racesover [user] [num] [wpm/points]`            | View    | Returns number of races greater than `num` in specified category.                                                      | `ro`               |
| `-milestone [user] [num] [races/points/wpm]`      | View    | Returns the time it took for user to achieve specified milestone.                                                      | `ms`               |
| `-marathon [user] <seconds>`                      | View    | Returns the most races a user completed in `seconds` seconds and its breakdown; defaults to 86400 (1 day). ![li]       | `42`               |
| `-sessionstats [user] <seconds>`                  | View    | Returns the longest session a user completed with breaks at most `seconds` seconds; defaults to 1800 (30 mins.). ![li] | `ss`               |
| `-fastestcompletion [user] [num_races]`           | View    | Returns the fastest a user completed `num_races` races and its breakdown. ![li]                                        | `fc`               |
| `-boxplot [user] <user_2> ... <user_4>`           | View    | Returns WPM boxplot of given user(s). Outliers are removed. ![li]                                                      | `bp`               |
| `-histogram [user]`                               | View    | Returns WPM boxplot of given user. ![li]                                                                               | `hg`               |
| `-raceline [user] <user_2> ... <user_10>`         | View    | Returns races over time graph for given user(s). ![li]                                                                 | `rl`               |
| `-improvement [user] <time/races>`                | View    | Returns WPM over specified category for given user. ![li]                                                              | `imp`              |

### Other
Other commands provide resources, information, and links related to TypeRacer.
| Name                         | Example | Function                                                                                                                                                | Aliases  |
|:-----------------------------|:-------:|---------------------------------------------------------------------------------------------------------------------------------------------------------|----------|
| `-search [query]`            | View    | Returns quotes containing given search query; each query must be at least 3 words long; query is case insensitive<br/> ![ba] can request 1 word queries | None     |
| `-levenshtein [query]`       | View    | Returns top 5 quotes with substring containing the least Levenshtein to given query; query must be at most 40 chars.<br/> ![ba] can request any length  | `leven`  |
| `-searchid [text_id]`        | View    | Returns text matching specified `text_id`. ![mu]                                                                                                        | `id`     |
| `-unixreference <timestamp>` | View    | Converts a provided UNIX timestamp to UTC time; scientific notation may be used. No parameters provided returns a conversion table.                     | `unix`   |
| `-serverinfo`                | View    | Returns basic information about the server the bot is in.                                                                                               |  `sinfo` |

[mu]: https://img.shields.io/badge/-multiverse-d3d3d3
[li]: https://img.shields.io/badge/-link-ffcc00
[ba]: https://img.shields.io/badge/-bot%20admins-ff4500

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