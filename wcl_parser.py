import aiohttp
import asyncio
from constants import RESIST_RANDOM_ENCHANT_BY_SLOT, UNENCHANTABLE_SLOTS, SLOT_MAIN_HAND, SLOT_OFF_HAND, \
    RESISTANCE_GEMS, RESISTANCE_ENCHANTS, SLOT_SHIRT, SLOT_TABARD, RESISTANCE_BUFFS
import decimal
import json
from glob import glob
from exceptions import NotFoundException
from aiolimiter import AsyncLimiter
import os


def replace_decimals(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = replace_decimals(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


def remove_duplicates(x):
    return list(dict.fromkeys(x))


def create_fight(fight):
    return {
        "id": fight['id'],
        "boss": fight['boss'],
        "kill": fight['kill'] if 'kill' in fight else None,
        "fight_percentage": fight["fightPercentage"] if 'fightPercentage' in fight else None,
        "fight_type": "boss" if fight['boss'] > 0 else "trash",
        "start_time": fight['start_time'],
        "end_time": fight['end_time'],
        "name": fight['name'],
    }


def create_character(character, fights):
    per_fight = {x['id']: x for x in character['fights'] if fights[x['id']]['boss'] > 0}
    per_fight[0] = {"id": 0}    # trash
    per_fight[-1] = {"id": -1}  # summary
    print("%s - %d fights" % (character['name'], len(per_fight) - 2))
    return {
        "id": character['id'],
        "name": character['name'],
        "type": character['type'],
        "per_fight": per_fight
    }


def create_pet(pet):
    return {
        "id": pet['id'],
        "name": pet['name'],
        "pet_owner": pet['petOwner'],
    }


class WCLParser:
    BASE_DOMAIN = "https://classic.warcraftlogs.com"
    API_KEY = os.environ['WCL_KEY']

    def __init__(self, report_id):
        self.endTimestamp = None
        self.startTimestamp = None
        self.endTime = None
        self.startTime = None
        self.title = None
        self.pets = None
        self.characters = None
        self.fights = None
        self.report_id = report_id
        self._session = aiohttp.ClientSession(WCLParser.BASE_DOMAIN)
        self._bucket = AsyncLimiter(25, 1)
        self._item_cache = {}

    def to_json(self, fight_id):
        return {
            "title": self.title,
            "reportId": self.report_id,
            "startTime": self.startTime,
            "endTime": self.endTime,
            "startTimestamp": self.startTimestamp,
            "endTimestamp": self.endTimestamp,
            "fights": [x for x in self.fights.values()],
            "characters": {x['id']: {'id': x['id'], 'name': x['name'], 'type': x['type'], 'data': x['per_fight'][fight_id]}
                           for x in self.characters.values() if fight_id in x['per_fight']},
            "pets": self.pets,
        }

    async def close(self):
        await self._session.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()

    def _preload_item_data(self):
        for file_name in glob('./data/*/*/*.json'):
            with open(file_name) as json_file:
                data = json.load(json_file)
                for item in [x for x in data if 'id' in x]:
                    self._item_cache[item['id']] = {
                        'id': item['id'],
                        'name': item['name'],
                        'slot': item['slot'] if 'slot' in item else None,
                        'randomEnchantment': item['randomEnchantment'] if 'randomEnchantment' in item else None,
                        'notEnchantable': item['notEnchantable'] if 'notEnchantable' in item else False,
                        'resistance-arcane': item['resistances']['Arcane'] if 'resistances' in item and 'Arcane'
                                                                              in item['resistances'] else None,
                        'resistance-fire': item['resistances']['Fire'] if 'resistances' in item and 'Fire'
                                                                              in item['resistances'] else None,
                        'resistance-frost': item['resistances']['Frost'] if 'resistances' in item and 'Frost'
                                                                              in item['resistances'] else None,
                        'resistance-nature': item['resistances']['Nature'] if 'resistances' in item and 'Nature'
                                                                              in item['resistances'] else None,
                        'resistance-shadow': item['resistances']['Shadow'] if 'resistances' in item and 'Shadow'
                                                                              in item['resistances'] else None,
                        'sockets': item['sockets'] if 'sockets' in item else None,
                    }

    async def needs_update(self, fights):
        await self.get_fights()

    async def parse_report(self):
        self._preload_item_data()
        await self.get_fights()
        await self.load_subsequent_data()
        return self

    @staticmethod
    async def _get_json_response(response):
        print("%s (%d)" % (response.url.human_repr(), response.status))
        if response.content_type == 'application/json':
            json_response = await response.json()
            return json_response
        else:
            text_response = await response.text()
            print('Unexpected content type "%s" - %s' % (response.content_type, text_response))

        return None

    async def get_fights(self):
        async with self._session.get("/v1/report/fights/" + self.report_id + "?api_key=" + WCLParser.API_KEY) as response:
            if response.status == 404 or response.status == 400:
                raise NotFoundException('Could not find report "%s".' % self.report_id)

            json_response = await WCLParser._get_json_response(response)
            self.fights = {x['id']: create_fight(x) for x in json_response['fights']}
            print("%d fights" % len(self.fights))
            self.characters = {x['id']: create_character(x, self.fights) for x in json_response['friendlies']
                               if x['type'] != "NPC" and x['type'] != "Pet" and x['type'] != "Boss"}
            self.pets = {x['id']: create_pet(x) for x in json_response['friendlyPets']}
            self.title = json_response['title']
            fight_list = list(self.fights.values())
            self.startTimestamp = json_response['start']
            self.endTimestamp = json_response['end']
            self.startTime = fight_list[0]['start_time']
            self.endTime = fight_list[len(fight_list)-1]['end_time']

    async def get_character_casts(self, player_id):
        await self._bucket.acquire()
        url = ("/v1/report/events/casts/%s?api_key=%s&start=%d&end=%d&sourceid=%d"
               % (self.report_id, WCLParser.API_KEY, self.startTime, self.endTime, player_id))
        async with self._session.get(url) as response:
            json_response = await WCLParser._get_json_response(response)
            filtered_events = [x for x in json_response['events'] if x['type'] == 'cast']
            for entry in filtered_events:
                fight_id = entry['fight']
                ability_id = entry['ability']['guid']
                self._set_property_if_empty(player_id, fight_id, {
                    'boss': 0,
                    'trash': 0,
                    'first_event': entry['timestamp'],
                }, 'casts', ability_id)
                self._increment_property(player_id, fight_id, 1, 'casts', ability_id,
                                         'boss' if self.fights[fight_id]['boss'] > 0 else 'trash')
                self._set_property_if_empty(player_id, -1, {
                    'boss': 0,
                    'trash': 0,
                    'first_event': entry['timestamp'],
                }, 'casts', ability_id)
                self._increment_property(player_id, -1, 1, 'casts', ability_id,
                                         'boss' if self.fights[fight_id]['boss'] > 0 else 'trash')

    async def get_character_buffs(self, player_id):
        await self._bucket.acquire()
        url = ("/v1/report/tables/buffs/%s?api_key=%s&start=%d&end=%d&sourceid=%d"
               % (self.report_id, WCLParser.API_KEY, self.startTime, self.endTime, player_id))
        async with self._session.get(url) as response:
            json_response = await WCLParser._get_json_response(response)
            for entry in json_response['auras']:
                for fight_band in self.fights.values():
                    fights = [x for x in entry['bands'] if x['endTime'] > fight_band['start_time']
                              and x['startTime'] < fight_band['end_time']]
                    if len(fights) == 0:
                        continue

                    fight_length = fight_band['end_time'] - fight_band['start_time']
                    buff_length = sum(x['endTime'] - x['startTime'] for x in fights)

                    self._set_property_if_empty(player_id, fight_band['id'], {
                        'percentage': 0,
                        'prebuff': []
                    }, 'buffs', entry['guid'])
                    self._increment_property(player_id, fight_band['id'], round(buff_length / fight_length, 3),
                                             'buffs', entry['guid'], 'percentage')

                    self._set_property_if_empty(player_id, -1, {
                        'percentage': 0,
                        'prebuff': []
                    }, 'buffs', entry['guid'])
                    self._increment_property(player_id, -1, round(buff_length / fight_length, 3),
                                             'buffs', entry['guid'], 'percentage')

                    if fight_band['start_time'] in [x['startTime'] for x in entry['bands']]:
                        self._add_to_fight_property_array_if_empty(player_id, fight_band['id'], fight_band['id'],
                                                                   'buffs', entry['guid'], 'prebuff')
                        self._add_to_fight_property_array_if_empty(player_id, -1, fight_band['id'], 'buffs',
                                                                   entry['guid'], 'prebuff')

                    if entry['guid'] in RESISTANCE_BUFFS:
                        for resistance in RESISTANCE_BUFFS[entry['guid']].keys():
                            self._increment_property(player_id, fight_band['id'],
                                                     RESISTANCE_BUFFS[entry['guid']][resistance],
                                                     'resistances', resistance)

    async def get_character_damage_taken(self, player_id):
        await self._bucket.acquire()
        url = ("/v1/report/events/damage-taken/%s?api_key=%s&start=%d&end=%d&sourceid=%d"
               % (self.report_id, WCLParser.API_KEY, self.startTime, self.endTime, player_id))
        async with self._session.get(url) as response:
            json_response = await WCLParser._get_json_response(response)
            for entry in json_response['events']:
                fight_id = entry['fight']

    async def get_character_healing(self, player_id):
        await self._bucket.acquire()
        url = ("/v1/report/events/healing/%s?api_key=%s&start=%d&end=%d&sourceid=%d"
               % (self.report_id, WCLParser.API_KEY, self.startTime, self.endTime, player_id))
        async with self._session.get(url) as response:
            json_response = await WCLParser._get_json_response(response)
            for entry in json_response['events']:
                fight_id = entry['fight']
                ability_id = entry['ability']['guid']
                self._set_property_if_empty(player_id, fight_id, {
                    'count': 0,
                    'amount': 0,
                    'first_event': entry['timestamp'],
                }, 'healing', ability_id)
                self._increment_property(player_id, fight_id, 1, 'healing', ability_id, 'count')
                self._increment_property(player_id, fight_id, entry['amount'], 'healing', ability_id, 'amount')

                self._set_property_if_empty(player_id, -1, {
                    'count': 0,
                    'amount': 0,
                    'first_event': entry['timestamp'],
                }, 'healing', ability_id)
                self._increment_property(player_id, -1, 1, 'healing', ability_id, 'count')
                self._increment_property(player_id, -1, entry['amount'], 'healing', ability_id, 'amount')

    async def get_deaths(self):
        await self._bucket.acquire()
        url = ("/v1/report/tables/deaths/%s?api_key=%s&start=%d&end=%d"
               % (self.report_id, WCLParser.API_KEY, self.startTime, self.endTime))
        async with self._session.get(url) as response:
            json_response = await WCLParser._get_json_response(response)
            for entry in json_response['entries']:
                self._increment_property(entry['id'], entry['fight'], 1, 'deaths')
                self._increment_property(entry['id'], -1, 1, 'deaths')

    async def get_interrupts(self):
        await self._bucket.acquire()
        url = ("/v1/report/events/interrupts/%s?api_key=%s&start=%d&end=%d"
               % (self.report_id, WCLParser.API_KEY, self.startTime, self.endTime))
        async with self._session.get(url) as response:
            json_response = await WCLParser._get_json_response(response)
            for entry in json_response['events']:
                player_id = entry['sourceID']
                if player_id not in self.characters:
                    if player_id not in self.pets:
                        continue
                    player_id = self.pets[player_id]['pet_owner']

                self._increment_property(player_id, entry['fight'], 1, 'interrupts', entry['ability']['guid'])
                self._increment_property(player_id, -1, 1, 'interrupts', entry['ability']['guid'])

    async def get_character_summary(self):
        await self._bucket.acquire()
        url = ("/v1/report/tables/summary/%s?api_key=%s&start=%d&end=%d"
               % (self.report_id, WCLParser.API_KEY, self.startTime, self.endTime))
        async with self._session.get(url) as response:
            json_response = await WCLParser._get_json_response(response)
            self._load_character_summary(json_response)

    async def get_character_summary_by_fight(self, fight):
        await self._bucket.acquire()
        fight_data = self.fights[fight]
        url = ("/v1/report/tables/summary/%s?api_key=%s&start=%d&end=%d&fight=%d"
               % (self.report_id, WCLParser.API_KEY, fight_data['start_time'], fight_data['end_time'], fight))
        async with self._session.get(url) as response:
            json_response = await WCLParser._get_json_response(response)
            self._load_character_summary(json_response, fight)

    async def load_subsequent_data(self):
        tasks = [self.get_deaths(), self.get_interrupts(), self.get_character_summary()]
        for y in [f['id'] for f in self.fights.values() if f['boss'] > 0]:
            tasks.append(self.get_character_summary_by_fight(y))

        for x in self.characters.keys():
            tasks.append(self.get_character_casts(x))
            tasks.append(self.get_character_buffs(x))
            tasks.append(self.get_character_damage_taken(x))
            tasks.append(self.get_character_healing(x))
        responses = await asyncio.gather(*tasks)

    def _load_character_summary(self, data, fight=-1):
        player_details = data['playerDetails']

        if 'tanks' in player_details:
            self._load_player_details(fight, player_details['tanks'], 'tank')

        if 'healers' in player_details:
            self._load_player_details(fight, player_details['healers'], 'healer')

        if 'dps' in player_details:
            self._load_player_details(fight, player_details['dps'], 'dps')

    def _load_player_details(self, fight, player_data, role):
        for player in player_data:
            player_id = player['id']

            # load gear (player['combatantInfo']['gear']
            if 'combatantInfo' in player:
                if 'gear' in player['combatantInfo']:
                    self._load_player_gear(fight, player_id, player['combatantInfo']['gear'])

            self._add_to_fight_property_array(player_id, fight, 'roles', role)
            if 'specs' in player:
                for spec in player['specs']:
                    self._add_to_fight_property_array(player_id, fight, 'specs', spec)

    def _add_resistance_from_gear(self, player_id, fight_id, gear_item, resistance):
        if gear_item is None:
            return

        key = 'resistance-' + resistance

        if key in gear_item and gear_item[key] is not None:
            self._increment_property(player_id, fight_id, gear_item[key], 'resistances', resistance)

    def _load_player_gear(self, fight_id, player_id, gear_list):
        for gear in gear_list:
            gear_id = gear['id']
            gear_slot = gear['slot']
            gear_item = None

            if gear_slot != SLOT_SHIRT and gear_slot != SLOT_TABARD and gear_id != 0:
                if gear_id in self._item_cache.keys():
                    gear_item = self._item_cache[gear_id]
                else:
                    print('Could not find item %d (%s)' % (gear_id, gear['name'] if 'name' in gear else 'Unknown'))

            # resistances from gear
            self._add_resistance_from_gear(player_id, fight_id, gear_item, 'arcane')
            self._add_resistance_from_gear(player_id, fight_id, gear_item, 'fire')
            self._add_resistance_from_gear(player_id, fight_id, gear_item, 'frost')
            self._add_resistance_from_gear(player_id, fight_id, gear_item, 'nature')
            self._add_resistance_from_gear(player_id, fight_id, gear_item, 'shadow')

            # resistances from random enchantments
            if gear_item is not None and 'randomEnchantment' in gear_item and gear_item['randomEnchantment'] is True \
                    and gear_slot in RESIST_RANDOM_ENCHANT_BY_SLOT \
                    and gear['itemLevel'] in RESIST_RANDOM_ENCHANT_BY_SLOT[gear_slot]:
                resistance_amount = RESIST_RANDOM_ENCHANT_BY_SLOT[gear_slot][gear['itemLevel']]
                self._increment_property(player_id, fight_id, resistance_amount, 'resistances', 'random_enchantment')

            # enchants (needs item data)
            if gear['id'] != 0 \
                    and (gear_item is None or ('notEnchantable' in gear_item and gear_item['notEnchantable'] is False))\
                    and (gear_slot not in UNENCHANTABLE_SLOTS or 'permanentEnchant' in gear):
                self._add_to_fight_property_array(player_id, fight_id, 'enchants', {
                    'id': gear['permanentEnchant'] if 'permanentEnchant' in gear else None,
                    'gearId': gear_id,
                    'name': gear['permanentEnchantName'] if 'permanentEnchantName' in gear else None,
                    'slot': gear_slot,
                })

                # resistances from enchants
                if 'permanentEnchant' in gear and gear['permanentEnchant'] in RESISTANCE_ENCHANTS:
                    for resistance in RESISTANCE_ENCHANTS[gear['permanentEnchant']].keys():
                        self._increment_property(player_id, fight_id,
                                                 RESISTANCE_ENCHANTS[gear['permanentEnchant']][resistance],
                                                 'resistances', resistance)

            # imbues
            if gear_slot == SLOT_MAIN_HAND and 'temporaryEnchant' in gear:
                self._add_to_fight_property_array_with_sub_property(player_id, fight_id, 'imbues', 'main_hand',
                                                                    gear['temporaryEnchant'])
                # self._increment_fight_property_with_sub_property(player_id, fight_id, 'imbues', 'main_hand',
                #                                                  gear['temporaryEnchant'], False)

            if gear_slot == SLOT_OFF_HAND and 'temporaryEnchant' in gear:
                self._add_to_fight_property_array_with_sub_property(player_id, fight_id, 'imbues', 'off_hand',
                                                                    gear['temporaryEnchant'])
                # self._increment_fight_property_with_sub_property(player_id, fight_id, 'imbues', 'off_hand',
                #                                                  gear['temporaryEnchant'], False)

            # gems
            gem_count = 0
            if 'gems' in gear:
                for gem in gear['gems']:
                    self._increment_property(player_id, fight_id, 1, 'gems', gem['id'])
                    # resistance gems
                    if gem['id'] in RESISTANCE_GEMS:
                        for resistance in RESISTANCE_GEMS[gem['id']].keys():
                            self._increment_property(player_id, fight_id, RESISTANCE_GEMS[gem['id']][resistance],
                                                     'resistances', resistance)

                gem_count = len(gear['gems'])

            # missing gems
            if gear_item is not None and 'sockets' in gear_item and gear_item['sockets'] is not None:
                if gear_item['sockets'] > gem_count:
                    self._increment_property(player_id, fight_id, gear_item['sockets'] - gem_count, 'gems', 0)

    def _get_fight(self, player_id, fight_id):
        if player_id not in self.characters:
            return None,None

        character = self.characters[player_id]
        if fight_id in character['per_fight']:
            return character['per_fight'][fight_id], character['per_fight'][-1]
        else:
            return character['per_fight'][0], character['per_fight'][-1]

    def _increment_property(self, player_id, fight_id, amount=1, *args):
        (fight, summary_fight) = self._get_fight(player_id, fight_id)

        if fight is None:
            return

        node = fight
        for arg_index in range(0, len(args)):
            if args[arg_index] not in node:
                if arg_index == len(args)-1:
                    node[args[arg_index]] = amount
                else:
                    node[args[arg_index]] = {}

            else:
                if arg_index == len(args)-1:
                    node[args[arg_index]] = node[args[arg_index]] + amount

            node = node[args[arg_index]]

    def _add_to_fight_property_array(self, player_id, fight_id, property_name, value):
        (fight, summary_fight) = self._get_fight(player_id, fight_id)

        if fight is None:
            return

        if property_name in fight:
            if value not in fight[property_name]:
                fight[property_name].append(value)
        else:
            fight[property_name] = [value]

    def _add_to_fight_property_array_with_sub_property(self, player_id, fight_id, property_name, sub_property, value):
        (fight, summary_fight) = self._get_fight(player_id, fight_id)

        if fight is None:
            return

        if property_name in fight:
            if sub_property in fight[property_name]:
                if value not in fight[property_name][sub_property]:
                    fight[property_name][sub_property].append(value)
            else:
                fight[property_name][sub_property] = [value]
        else:
            fight[property_name] = {
                sub_property: [value]
            }

    def _set_fight_property_with_sub_property(self, player_id, fight_id, property_name, sub_property, value):
        (fight, summary_fight) = self._get_fight(player_id, fight_id)

        if fight is None:
            return

        if property_name in fight:
            fight[property_name][sub_property] = value
        else:
            fight[property_name] = {
                sub_property: value
            }

    def _set_property_if_empty(self, player_id, fight_id, value, *args):
        (fight, summary_fight) = self._get_fight(player_id, fight_id)

        if fight is None:
            return

        node = fight
        for arg_index in range(0, len(args)):
            if args[arg_index] not in node:
                if arg_index == len(args) - 1:
                    node[args[arg_index]] = value
                else:
                    node[args[arg_index]] = {}

            node = node[args[arg_index]]

    def _add_to_fight_property_array_if_empty(self, player_id, fight_id, value, *args):
        (fight, summary_fight) = self._get_fight(player_id, fight_id)

        if fight is None:
            return

        node = fight
        for arg_index in range(0, len(args)):
            if arg_index == len(args) - 1:
                node[args[arg_index]].append(value)

            node = node[args[arg_index]]
