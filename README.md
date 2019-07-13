# Sync bot
A bot to sync your file to your telegram chat

## Usage

### Initialization
`pip install -r requirements.txt`

`python sync.py`

Then fill your `token` (telegram bot token), `sync_paths`(paths to be synced),
 `sync_interval`(time interval (secs) between two syncs) in `bot.json`

`python sync.py`

Follow the instruction, send your bot a message, `chat_id`, `offset`will be filled automatically

### Start sync

`python sync.py`
You could check the status of bot in `bot.log`
