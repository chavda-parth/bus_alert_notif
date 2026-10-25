from datetime import date
from projectenums import BusCategory
from dataclasses import dataclass, fields

@dataclass
class SearchURL:
    fromCity: int = 1125 #Id for Jamnagar
    toCity: int = 472 #Id for Rajkot
    doj: str = ""
    limit: int = ""
    offset: int = 0 #Don't know what it does
    meta: str = ""
    groupId: int = 0
    sectionId: int = 0
    sort: int = 0
    sortOrder: int = 0
    fromType: str = ""
    getUuid: str = ""
    bT: int = 1
    clearLMBFilter: str = "undefined"
    isFilterApplied: str = "false" 


    def __init__(self, doj: date, limit: int, category: BusCategory):
        self.doj = doj.strftime("%d-%b-%Y")
        self.limit = limit

        if category is BusCategory.PRIVATE:
            self.meta = "true"
            self.groupId = 0
            self.fromType = "initialLoad"
            self.getUuid = "true"
        elif category is BusCategory.GSRTC:
            self.meta = "false"
            self.groupId = 34300
            self.fromType = "useeffect_group_load"
            self.getUuid = "false"

    def get_formatted_url(self, separator: str = "&") -> str:
        prefix: str = "https://www.redbus.in/rpw/api/searchResults?"
        key_names = {
            "fromType": "from",
            "doj": "DOJ"
        }

        params = separator.join(
            f'{key_names.get(field.name, field.name)}={getattr(self, field.name)}'
            for field in fields(self)
        )

        return f'{prefix}{params}'

# print(SearchURL(date.today(), 50, BusCategory.PRIVATE).get_formatted_url())