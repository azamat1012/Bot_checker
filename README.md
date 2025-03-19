# Bot checker

This bot sends the latest checked tasks via telegram. 

## Environment

### Requirements


Python3 must already be installed in your environments. You may create an virtual environement as well to not trash your memory space. 

 - To run your bot correctly you should install next requirements to your env:


1. python-telegram-bot==13.7
2. requests==2.28.1
3. python-dotenv==0.21.0

or just but the next line of code in your bash terminal:

```bash
  pip install -r requirements.txt
```

- In your created .env file you should add your apies

```bash
    DEVMAN_API=YOUR_DEVMAN_API
    TG_API=YOUR_TG_API
    ADMIN_CHAT_ID=YOUR_CHAT_ID
```

PS. ADMIN_CHAT_ID is needed to get the loggs

## Run

```bash
    python main.py
```

You will see something like following:

2025-03-07 12:27:10,912 - INFO - Bot is starting

2025-03-07 12:27:10,913 - INFO - Scheduler started


## Project Goals

The code is written to automate the proccess of seeking the checked tasks on the platform "devman"
