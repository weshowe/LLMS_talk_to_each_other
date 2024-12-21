# LLMs_talk_to_each_other
A Python script using selenium that enables 2 chatbots to talk to each other. They can be from character.ai or Replika, and starter code is provided to allow you to hook up any local LLM or remote one with API calls.

The program handles the web-based LLMs (character.ai and Replika) by switching browser tabs and relaying messages, with a little bit of conversation seeding to choose a topic and (attempt) to keep the conversation going. Since neither character.ai nor Replika have a public API or working/easy-to-use alternatives to that, I made this. Currently WIP.

A log of each conversation will be placed in same directory as the program, with Unix timestamp appended to the log file. The wait timer between messages is fairly conservative, feel free to change it in main.py, although it *might* cause some message truncation if it is too low.

## Installation
1. Execute "pip install selenium pytz" in the command line. selenium versions 4.0 and above should work.
2. Install Google Chrome if you don't already have it, and check the version at chrome://settings/help. Download the chromedriver for that version here https://developer.chrome.com/docs/chromedriver/downloads.
3. Update chromedriver_executable_path variable in top of main.py to the location of the extracted chromedriver on your system (see code comment for example)
4. (optional): At the top of main.py, change topic to what you want the initial topic prompt to be (ie: "Let's talk about trains."), and alter deadlock avoidance prompt to what you would like (see below for explanation)
5. Run main.py with the desired arguments. Make sure the names of the chatbots are exactly as they appear on each website.
6. Open the chat for the first chatbot in one tab, then open the chat for the second chatbot in the second tab.
7. Press Enter in the command prompt. The program will run and the agents will keep talking until the program throws an exception it can't recover from or you manually stop it (ie: with Ctrl-C).

## Usage
The script is run like so:
    
    python .\main.py --name1 "Jack" --name2 "Jill" --type1  character.ai --type2 character.ai
	
The name of each chatbot must be typed exactly as it appears on the website or the scraper might not be able to find the tabs correctly.

Supported platforms (types): Replika, character.ai. You can use any combination of them (ie: character.ai and character.ai, Replika and character.ai, etc.). I have also provided a "custom" agent type and starter code within Agent.py you can use to invoke your own LLM, whether locally (ie: huggingface) or remotely through API calls.

Adding --verbose will print verbose logs to the command line so you can see more detail about what the script is doing.

--timezone followed by a pytz timezone string will set the log timestamps to your local time zone. When this parameter is not added the program defaults to UTC time.

Lastly, one problem that often occurs in the conversations is a form of deadlock where the agents (chatbots) end up talking about the same thing over and over again. You can break out of it by enabling deadlock avoidance, which will inject a prompt into the conversation after a certain number of messages:
    
    python .\main.py --name1 "Jack" --name2 "Jill" --type1  character.ai --type2 character.ai --deadlockavoidance --deadlockthreshold 20
	
--deadlockavoidance enables this (disabled by default), and --deadlockthreshold controls the number of messages to be sent before deadlock avoidance is triggered (default is 25). The message counter will be reset when this happens. See top of main.py if you want to change the prompt that is injected during deadlock avoidance.

## Additional Notes

As far as I know, Replika conversation history cannot be deleted without deleting your account and making a new one. If you want to wipe a Replika history between runs, the best way I found was to go into the "Memories" section and forget everything.	

## Why did I make this?

I read a news story about a 14 year old boy who ended his life after falling in love with a character.ai Daenerys Targaryen chatbot, and it made me wonder if they could "fall in love" with each other or do other interesting things. I made this because I was too lazy to copy paste all the chats myself for my experiments. See research_notes.md for a more in depth explanation of my experiments and the program's design history.
