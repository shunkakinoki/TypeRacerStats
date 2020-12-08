<h1 align = 'center'>TypeRacerStats</h1>

**TypeRacerStats** is a [**Discord**](https://discord.com/) bot partnered with with [**TypeRacer**](http://typeracer.com/) and was made with the [**Discord.py API**](https://pypi.org/project/discord.py/), TypeRacer APIs, [**TypeRacerData**](http://typeracerdata.com/) APIs, [**SQLite**](https://www.sqlite.org/index.html), and various Python libraries (can be found in [`requirements.txt`](https://github.com/e6f4e37l/TypeRacerStats/blob/main/requirements.txt)). It comes with over 40 commands to provide extensive statistics and features for users. Many of them are designed to help with improvement on the site. Run `-help` or refer to the **commands** section below.


## Commands
Some commands are ![mu], which means they provide statistics regardless of the TypeRacer universe—separate environments of TypeRacer with distinct texts, leaderboards, and scores—selected.

Another feature that some commands have is the ability to ![li] your Discord account to a TypeRacer account; for commands with said feature, linked users will not have to type their TypeRacer username every time. This can be done using the `-link [typeracer_username]` command.

Finally, some commands' functionalities are limited according to the bot permissions a user has: regular, bot admin, or bot owner.

### Info
<details>
<summary>Info commands provide information for the bot.</summary>

| Name | Example | Function | Aliases |
|:---  |:-------:|----------|---------|
| `-help [command]` | <details><summary>View</summary>![1]</details> | Returns information for given command. Case sensitive and aliases may be used in place of `[command]`. | `h` |
| `-info` | <details><summary>View</summary>![2]</details> | Returns information about the bot. | `abt`, `about` |
| `-invite` | <details><summary>View</summary>![3]</details> | Returns an invite link for the bot. Refer to the **Invite/Permissions** section below for permissions. | None |
| `-donate` | <details><summary>View</summary>![4]</details> | Returns donation link to support the bot. | `support` |
</details>

[1]: https://i.gyazo.com/7919a19d1eb053d688e332835b1cd8ce.gif
[2]: https://i.gyazo.com/94e63c59b8b7210a55ce805f5b9f08ed.gif
[3]: https://i.gyazo.com/4230b88a0e45ba53817617a8a5205fc0.gif
[4]: https://i.gyazo.com/077bbf46a86925f9c75071e86c256ec3.gif

### Configuration
<details>
<summary>Configuration commands allow server admins to change the bot's prefix and users to configure the settings of their Discord account with regards to the bot.</summary>

| Name | Example | Function | Aliases |
|:-----|:-------:|----------|---------|
| `-changeprefix [prefix]` | <details><summary>View</summary>![5]</details> | Changes the bot's prefix on the server. | `cp` |
| `-register [typeracer_username]` | <details><summary>View</summary>![6]</details> | Links Discord account to TypeRacer account. ![mu] | `link`, `link*` |
| `-setuniverse [universe]` | <details><summary>View</summary>![7]</details> | Links Discord account to provided TypeRacer universe; defaults to `play` universe. ![mu] ![li] | `su` |
| `-toggledessle` | <details><summary>View</summary>![8]</details> | Toggles Desslejusted option for `realspeed`, `lastrace`, `realspeedaverage`, and `raw`. ![li] | `tg` |
</details>

[5]: https://i.gyazo.com/9275dda7a232b24f7e9acd162b6b43a2.gif
[6]: https://i.gyazo.com/4188c85795923471f4276b2ea8b12909.gif
[7]: https://i.gyazo.com/b4c3cc88b55a6c27a02cd1aa109c02b2.gif
[8]: https://i.gyazo.com/68a0af23c3f57f33f8d9337567647e07.gif

### Basic
<details>
<summary>Basic commands do not require a user's information to be downloaded to provide statistics.</summary>

| Name | Example | Function | Aliases |
|:-----|:-------:|----------|---------|
| `-stats [user]` | <details><summary>View</summary>![9]</details> | Returns basic stats for given user. ![mu] ![li] | `prof`, `profile` |
| `-getdata [user]` | <details><summary>View</summary>![10]</details> | Downloads given user's data; **Advanced** commands may be used after. ![li] | `dl`, `gd`, `download,` |
| `-today [user] <date>` | <details><summary>View</summary>![11]</details> | Downloads given user's data for specified date. `yesterday`, `yday`, `yd` are special aliases. ![li] | `day`, `yesterday`, `yday`, `yd` |
| `-realspeed [user] <race_num>` or `-realspeed [url]` | <details><summary>View</summary>![12]</details> | Returns [realspeeds](https://bit.ly/typeracerspeeds) for given race. ![mu] ![li] | `rs` |
| `-realspeedaverage [user] <first_race> <last_race>` | <details><summary>View</summary>![13]</details> | Returns the realspeed average for given race interval. <br/>![ba] may request up to 150 races. ![mu] ![li] | `rsa`, `rsa*` |
| `-raw [user] <race_num>` or `-raw [url]` | <details><summary>View</summary>![14]</details> | Returns realspeeds and _raw_ speed (speed with correction time omitted) for given race. ![mu] ![li] | None |
| `-lastrace [user] <race_num>` or `-lastrace [url]` | <details><summary>View</summary>![15]</details> | Returns all users' realspeeds ranked by unlagged for given race. ![mu] ![li] | `lr`, `last` |
| `-adjustedgraph [user] <race_num>` or `-adjustedgraph [url]` | <details><summary>View</summary>![42]</details> | Returns specified race's adjusted WPM over time. ![mu] ![li] | `ag` |
| `-leaderboard [category] <amount>` | <details><summary>View</summary>![16]</details> | Returns a leaderboard for given category: `races/points/textstyped/textbests/toptens`. | `lb` |
| `-competition <category>` | <details><summary>View</summary>![17]</details> | Returns the daily competition for specified category: `points/races/wpm`; defaults to `points` ![mu] | `comp` |
| `-lastonline [user]` | <details><summary>View</summary>![18]</details> | Returns the last time a user played. ![mu] ![li] | `lo`, `ls`, `lastseen` |
| `-medals [user]` | <details><summary>View</summary>![19]</details> | Returns the medals a user has. ![li] | None |
| `-toptens [user]` | <details><summary>View</summary>![20]</details> | Returns the number of text top 10s a user holds. ![li]<br/>![ba] can request JSON breakdowns with `10*`. | `10`, `10*`, `toptens*` |
</details>

[9]: https://i.gyazo.com/25c9bcca4fc0cead99f3888d60df8cb8.gif
[10]: https://i.gyazo.com/9693429f3610eb04840cf95280bed340.gif
[11]: https://i.gyazo.com/c504e69f392f6b0ebf54e35d3663b2f8.gif
[12]: https://i.gyazo.com/3883d1625091964ea1a6cb31c5853b7e.gif
[13]: https://i.gyazo.com/df6e5864a52b94ad0fbd08bbcffa1a80.gif
[14]: https://i.gyazo.com/1565bae6565b97b61ad462ab7399b889.gif
[15]: https://i.gyazo.com/02869c8107111cf1b2fd36053f7c1f3a.gif
[16]: https://i.gyazo.com/1b14085e39836327f4dd57a192204f4d.gif
[17]: https://i.gyazo.com/23994cdb3e1d055f285a48d0d0f12591.gif
[18]: https://i.gyazo.com/e8947d78fce9a17a980c7cd16d0a610e.gif
[19]: https://i.gyazo.com/baae841b5b8be620a294fd33fdf36669.gif
[20]: https://i.gyazo.com/320321451eefcff121f21683b3e5caa6.gif
[42]: https://i.gyazo.com/4f2ab33bdc58eb73d8880a3d49699dd3.gif

### Advanced (all require `-getdata`)
<details>
<summary>Advanced commands provide detailed statistical calculations, graphs, and services aimed to help users improve their typing speed and TypeRacer statistics.</summary>

| Name | Example | Function | Aliases |
|:-----|:-------:|----------|---------|
| `-top [user] [wpm/points]` | <details><summary>View</summary>![21]</details> | Returns user's top 10 races sorted by specified category. ![li] | `best` |
| `-worst [user] [wpm/points]` | <details><summary>View</summary>![22]</details> | Returns user's worst 10 races sorted by specified cateogry. ![li] | `bottom` |
| `-racedetails [user]` | <details><summary>View</summary>![23]</details> | Returns detailed breakdown of user's races. ![li] | `rd` |
| `-textbests [user]` | <details><summary>View</summary>![24]</details> | Returns user's top 5 texts, worst 5 texts, and text bests average (average of best in each text). ![li] | `tb` |
| `-breakdown [user]` | <details><summary>View</summary>![43]</details> | Returns detailed breakdown of text bests. ![li] | `bd` |
| `-personalbest [user] <text_ID>` | <details><summary>View</summary>![25]</details>| Returns user's average, best, and worst on specified `text_id`. Defaults to last-raced text if none provided. ![li] | `pb` |
| `-unraced [user] <length>` | <details><summary>View</summary>![26]</details> | Returns 5 randomly unraced texts under `length` characters. ![li] | `ur` |
| `-textsunder [user] [wpm] <length>` | <details><summary>View</summary>![26]</details> | Returns 5 randomly raced texts under `wpm` wpm and `length` characters. ![li] | `tu` |
| `-textslessequal [user] [num] [wpm/points/times]` | <details><summary>View</summary>![27]</details> | Returns number of texts typed more than or equal to `num` in specified category. | `tle`, `tor`, `to` |
| `-racesover [user] [num] [wpm/points]` | <details><summary>View</summary>![28]</details> | Returns number of races greater than `num` in specified category. | `ro` |
| `-milestone [user] [num] [races/points/wpm]` | <details><summary>View</summary>![29]</details> | Returns the time it took for user to achieve specified milestone. | `ms` |
| `-marathon [user] <seconds>` | <details><summary>View</summary>![30]</details> | Returns the most races a user completed in `seconds` seconds and its breakdown; defaults to 86400 (1 day). ![li] | `42` |
| `-sessionstats [user] <seconds>` | <details><summary>View</summary>![31]</details> | Returns the longest session a user completed with breaks at most `seconds` seconds; defaults to 1800 (30 mins.). ![li] | `ss` |
| `-fastestcompletion [user] [num_races]` | <details><summary>View</summary>![32]</details> | Returns the fastest a user completed `num_races` races and its breakdown. ![li] | `fc` |
| `-boxplot [user] <user_2> ... <user_4>` | <details><summary>View</summary>![33]</details> | Returns WPM boxplot of given user(s). Outliers are removed. ![li] | `bp` |
| `-histogram [user]` | <details><summary>View</summary>![34]</details> | Returns WPM boxplot of given user. ![li] | `hg` |
| `-raceline <time> [user] <user_2> ... <user_10>` | <details><summary>View</summary>![35]</details> | Returns races over time graph for given user(s); optional `time` parameter returns graph with only the races completed after it. ![li] | `rl` |
| `-improvement [user] <time/races>` | <details><summary>View</summary>![36]</details> | Returns WPM over specified category for given user. ![li] | `imp` |
</details>

[21]: https://i.gyazo.com/ed78ac261df7c06800c3cb52d1143b5e.gif
[22]: https://i.gyazo.com/b700e5d1b752f552aad52fec30ec228c.gif
[23]: https://i.gyazo.com/c2de466dcbcd6143704697ddba247001.gif
[24]: https://i.gyazo.com/fdfe1c85943ea50709d5825ae7f5a58b.gif
[25]: https://i.gyazo.com/70ba8338ecc7ff58b3a56ece46e68e37.gif
[26]: https://i.gyazo.com/dedde1e179d364548934413be9cda3f9.gif
[27]: https://i.gyazo.com/756f5040a1d019ca732a502d4d5051c8.gif
[28]: https://i.gyazo.com/17bc59f72c26b1df64b79bb1365be749.gif
[29]: https://i.gyazo.com/ffb483570dde1dc47337b095ef86f36a.gif
[30]: https://i.gyazo.com/909410d45e798dba78aaf02bc017c2e9.gif
[31]: https://i.gyazo.com/3596d5d980fc0518a5fa01f6462793ba.gif
[32]: https://i.gyazo.com/5a89a2095bf833ee3e476da9d363d438.gif
[33]: https://i.gyazo.com/a67596d807a5a9881dacdc5e4c102ca9.gif
[34]: https://i.gyazo.com/4ca36e72ee226a9fad83dc2f8708410e.gif
[35]: https://i.gyazo.com/4044245afb72e666cbad0d88a78d968e.gif
[36]: https://i.gyazo.com/79d467b13a1717a4db59d80a064c2199.gif
[43]: https://i.gyazo.com/e28465a5f4b362feb926db64cccfb2e7.gif

### Other
<details>
<summary>Other commands provide resources, information, and links related to TypeRacer.</summary>

| Name | Example | Function | Aliases |
|:-----|:-------:|----------|---------|
| `-search [query]` | <details><summary>View</summary>![37]</details> | Returns quotes containing given search query; each query must be at least 3 words long; query is case insensitive<br/> ![ba] can request 1 word queries | None |
| `-levenshtein [query]` | <details><summary>View</summary>![38]</details> | Returns top 5 quotes with substring containing the least Levenshtein to given query; query must be at most 40 chars.<br/> ![ba] can request any length | `leven` |
| `-searchid [text_id]` | <details><summary>View</summary>![39]</details> | Returns text matching specified `text_id`. ![mu] | `id` |
| `-unixreference <timestamp>` | <details><summary>View</summary>![40]</details> | Converts a provided UNIX timestamp to UTC time; scientific notation may be used. No parameters provided returns a conversion table. | `unix` |
| `-serverinfo` | <details><summary>View</summary>![41]</details> | Returns basic information about the server the bot is in. | `sinfo` |
</details>

[37]: https://i.gyazo.com/43f4e11b8a7ec6e7a3b1bdb99868d217.gif
[38]: https://i.gyazo.com/e3c7ccbdf2a24a71c7d80b714c311410.gif
[39]: https://i.gyazo.com/8a9e7a14e565c5778fdf219740aa5345.gif
[40]: https://i.gyazo.com/1877d7ab9da0ae4744abc3f1882477b5.gif
[41]: https://i.gyazo.com/ef08e87d9584a2f9eaba14c6aa0c6ad6.gif

[mu]: https://img.shields.io/badge/-multiverse-d3d3d3
[li]: https://img.shields.io/badge/-link-ffcc00
[ba]: https://img.shields.io/badge/-bot%20admins-ff4500


## Maintenance
There are three things the bot must do to keep the data and itself maintained. All of these are done automatically and routinely by the bot in the background, so the bot remains 100% functional while the processes take place. These processes can be found in [`TypeRacerStats/TypeRacerStats/Core/Common/maintenance.py`](https://github.com/e6f4e37l/TypeRacerStats/blob/main/TypeRacerStats/Core/Common/maintenance.py).
1. Update TypeRacer users' data every 24 hours even if they have not called `-getdata` that day.
2. Drop the temporary tables created from `-today` and `-competition` calls every 24 hours.
3. Scrape all text pit stop pages for texts' top 10 data once a week.


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

Each month of hosting costs 6 USD, so the perks tiers are incremented by 6 each:
- **Tier 1 ($0.01 - $5.99):** Name listed on `info` command
- **Tier 2 ($6.00 - $11.99):** Set custom embed color with `setcolor`
- **Tier 3 ($12.00+):** Custom command added to the bot

<details>
<summary>Supporter commands coming soon!</summary>
</details>