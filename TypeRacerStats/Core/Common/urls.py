class Urls:
    def __init__(self):
        self.trapi_races = 'https://data.typeracer.com/games?playerId=tr:'
        self.trapi_users = 'https://data.typeracer.com/users?id=tr:'
        self.trapi_competitions = 'https://data.typeracer.com/partial_rankings?n=12&kind='
        self.tr_competitions = "https://data.typeracer.com/pit/competitions?kind="
        self.tr_users = 'https://data.typeracer.com/pit/profile?user='
        self.tr_results = 'https://data.typeracer.com/pit/result?id='
        self.trd_users = 'http://typeracerdata.com/api?username='
        self.trd_imports = 'http://typeracerdata.com/import?username='
        self.trd_leaders = 'http://typeracerdata.com/leaders?min_races=1000&min_texts=400&rank_end=20&sort='
        self.trd_text_ids = 'http://typeracerdata.com/text?id='

    def get_races(self, player, universe, *args):
        base = f"{self.trapi_races}{player}&universe={universe}"
        if len(args) == 2:
            return f"{base}&startDate={float(args[0])}&endDate={float(args[1])}"
        else:
            return f"{base}&n={int(args[0])}"

    def get_user(self, player, universe):
        return f"{self.trapi_users}{player}&universe={universe}"

    def get_competition(self, kind, sort, universe):
        return f"{self.trapi_competitions}{kind}&sort={sort}&universe={universe}"

    def competition(self, kind, sort, date, universe):
        return f"{self.tr_competitions}{kind}&sort={sort}&date={date}&universe={universe}"

    def user(self, player, universe):
        return f"{self.tr_users}{player}&universe={universe}"

    def result(self, player, race_num, universe):
        return f"{self.tr_results}{universe}|tr:{player}|{race_num}&allowDisqualified=true"

    def trd_user(self, player, universe):
        return f"{self.trd_users}{player}&universe={universe}"

    def trd_import(self, player):
        return f"{self.trd_imports}{player}"

    def leaders(self, sort):
        return f"{self.trd_leaders}{sort}"

    def text(self, text_id):
        return f"{self.trd_text_ids}{text_id}"
