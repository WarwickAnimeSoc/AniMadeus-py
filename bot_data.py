# Bot data
#
# Mainly contains ids from the discord server. Leaving this out of the config file so it can be edited
# by non-webmasters.

DATABASE_PATH = 'data/db.sqlite3'

GUILD_ID = 221309541088886784

MESSAGE_IDS = {
    'role_assign_message': 751166772542963824,
    'manga_club_role_assign_message': 1477628796625489971,
}

CHANNEL_IDS = {
    'bot-commands': 1050233139458478100,
    'web-development': 335158754616016906,
    'newcomers': 753668259974217870,
    'rules': 385333508463263746,
    'role-assign': 546843849620979723,
    'welcome-and-links': 326044428621840386,
    'off-topic': 391359642539917322,
    'karaoke-discussion': 413698021084233738
}

ROLE_IDS = {
    'general': 546855453603135489,
    'art': 602883577293832202,
    'amq': 602883609057165363,
    'non-warwick': 729027269074485339,
    'vc': 730475391298568234,
    'graduate': 729027220139409469,
    'gacha_addict': 790246791320436796,
    'webmaster': 335157257346220033,
    'av': 682339378789744647,
    'member': 472915800081170452,
    'exec': 221311015432749056,
    'manga': 1477484351070404824,
}

EMOJI_TO_ROLE_MAPPINGS = {
    '1️⃣': ROLE_IDS['general'],
    '2️⃣': ROLE_IDS['art'],
    '🎵': ROLE_IDS['amq'],
    '↖️': ROLE_IDS['non-warwick'],
    '🎙️': ROLE_IDS['vc'],
    '🎓': ROLE_IDS['graduate'],
    '🎰': ROLE_IDS['gacha_addict'],
}
