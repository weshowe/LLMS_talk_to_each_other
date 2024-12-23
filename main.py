import time
from datetime import datetime
import sys
import os
from pathlib import Path
import pytz
import random
import argparse
import unicodedata
from selenium import webdriver

from util import *
from Agent import *

# User Fields. The program will read these in as global variables.

topic = "stuff" # Initial topic to start the conversation, is seeded into initial messages.

pytz_timezone = 'UTC' # used to get correct timezone in logs, change this to your local timezone if you want them to show your local time instead of UTC.
chromedriver_executable_path = 'C:/chromedriver-win64/chromedriver.exe' # path to the .exe on Windows, path to containing folder on Linux.

# Antideadlock measures (see readme). Yet to come up with clever antideadlock strategy, so just seed with reminder to continue conversation when limit hit...
deadLockLimit = 25 # after this number of messages, inject deadlock avoidance prompt.
messageCounter = 0 # counts messages, resets after deadlock avoidance triggered.
deadlock_avoidance_prompt = f"Let's talk about something else." # This is used to (hopefully) move along the conversation when deadlock avoidance is triggered.

def main():

    # Retrieve global variables.
    global topic
    global pytz_timezone
    global chromedriver_executable_path
    global deadLockLimit
    global messageCounter
    global deadlock_avoidance_prompt
    global verbosity

    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--name1", type=str, help="The name of the first agent.", required=True, action = "store")
    parser.add_argument("-b", "--type1", type=str, help="The type of the first agent. Currently supported types: character.ai", required=True, action = "store")
    parser.add_argument("-c", "--name2", type=str, help="The name of the second agent.", required=True, action = "store")
    parser.add_argument("-d", "--type2", type=str, help="The type of the second agent. Currently supported types: character.ai", required=True, action = "store")
    parser.add_argument("-v", "--verbose", help="Add this to print debug messages so you can see what the script is doing.", action="store_true")
    parser.add_argument("-e", "--deadlockavoidance", help="Add this if you want to perform deadlock avoidance.", action="store_true")
    parser.add_argument("-f", "--deadlockthreshold", type=int, help="The number of messages to wait for before triggering deadlock avoidance.", action="store")
    parser.add_argument("-t", "--timezone", type=str, help="The pytz timezone you wish the log timestamp to conform to. Default is UTC.", action="store")
    args = parser.parse_args()

    # Sanity check
    if args.type1 not in agent_types: 
        print(f"Error: {args.name1}'s agent type {args.type1} is invalid. Supported agent types: {agent_types}")
        return
    
    if args.type2 not in agent_types:
        print(f"Error: {args.name1}'s agent type {args.type1} is invalid. Supported agent types: {agent_types}")
        return
    
    # Set custom deadlock avoidance message threshold if specified.
    if args.deadlockthreshold is not None:

        if args.deadlockthreshold > 0:
            deadLockLimit = args.deadlockthreshold

        else:
            print(f"Error: Deadlock message threshold must be higher than 0. Entered threshold: {args.deadlockthreshold}. Exiting.")
            return

    # Set custom time zone if specified.
    if args.timezone is not None:

        if args.timezone in pytz.all_timezones:
            pytz_timezone = args.timezone

        else:
            print(f"Error: {args.timezone} is not in the list of pytz timezones. Exiting.")
            return

    # Set verbode logging if enabled.
    if args.verbose:
        verbosity = True

    logfile = str(Path(os.path.dirname(sys.argv[0])).resolve()) + f"/log_{args.name1}_{args.name2}_{time.time()}.txt"

    # for log prints. Logs to directory script was run from.
    def addlog(inString):
        with open(logfile, "a+") as f:
            f.write(str(datetime.now(pytz.timezone(pytz_timezone))) + " " + inString + "\n")
    
    # chop down the number of browser tabs based on number of custom agents involved, which don't need browser tabs. We will not spin up a browser at all if there are 2 of them.
    numCustomAgents = int((args.type1 == "custom")) + int((args.type2 == "custom"))
    cService = None
    driver = None

    if numCustomAgents < 2:
        cService = webdriver.ChromeService(executable_path=chromedriver_executable_path)
        driver = webdriver.Chrome(service = cService)

    # get handle (tab identifier) for each agent
    window1 = None
    window2 = None
    handles = None
    while True and (numCustomAgents < 2):

        if numCustomAgents == 0:
            _ = input(f"Press Enter when you have authenticated into your {args.type1} account and opened the chat for {args.name1} in one tab, and you have authenticated into your {args.type2} account and opened the chat for {args.name2} in another tab")

        else:
            if args.type1 == "custom":
                _ = input(f"Press Enter when you have authenticated into your {args.type2} account and opened the chat for {args.name2} in a single tab")
            else:
                _ = input(f"Press Enter when you have authenticated into your {args.type1} account and opened the chat for {args.name1} in a single tab")

        handles = driver.window_handles

        if len(handles) != 2 - numCustomAgents:
            print(f"\nError: Did not detect {2 - numCustomAgents} open tabs in your browser. There must only be {2 - numCustomAgents}. Please try again.\n")

        # Selenium has an annoying problem where it can't tell tab position (ie: first tab) and the tab position doesn't necessarily correspond to the order in the retrieved list.
        # We get around this by looking in the entire page for the exact agent name preceded by "<" under the assumption this will not occur in the conversation and will only be present within the agent's page code.
        # We get around duplicates (ie: character.ai donald trump talking to character.ai donald trump) with the second if condition. Not foolproof, will likely fail cross-platform if names are identical.
        # TODO: find better way of doing this that doesn't introduce more possible failure points.
        else:
            for handle in handles:
                driver.switch_to.window(handle)
                if f">{args.name1}" in driver.page_source:
                    if (window1 is None) and (window2 != handle):
                        window1 = handle
                if f">{args.name2}" in driver.page_source:
                    if (window2 is None) and (window1 != handle):
                        window2 = handle
            break
    
    # sanity check for tabs.
    if (window1 is None) and (args.type1 != "custom"):
        print(f"Could not load handle for {args.name1}. This may be because their name wasn't entered exactly as it is shown in the website.")
        return
    
    if (window2 is None) and (args.type2 != "custom"):
        print(f"Could not load handle for {args.name2}. This may be because their name wasn't entered exactly as it is shown in the website.")
        return
    
    # configure agents
    agent1 = None
    agent2 = None
    for elem in agent_types.keys():
        if args.type1 == elem:
            agent1 = agent_types[elem](args.name1, driver, window1)

        if args.type2 == elem:
            agent2 = agent_types[elem](args.name2, driver, window2)
    
    agents = [agent1, agent2]

    while True:

        # Main loop: For each agent, retrieve its latest message and send it to the other one.
        self = None
        other = None
        for agent in agents:
            self = agent
            for elem in agents:
                if elem != agent:
                    other = elem
                    break
            
            # get latest message. The regex invoked by stripHtmlTags should clear most HTML tags from the chat.
            latestOutput = stripHtmlTags(self.getLatestMessage(retries = 5, timeToWaitBetweenRetries = 5)) 
            
            # this converts unicode chars to UTF-8. Replika once added an emoji into the text body that broke the program because the emoji was unicode.
            latestOutput = unicodedata.normalize('NFKD', latestOutput).encode('utf-8', 'ignore').decode('utf-8')

            # I found that the AIs sometimes wouldn't know who the other was (ie: if they didn't mention it during greeting), so agent name seeded during first greeting.
            # Also add topic prompt.
            if self.getCurrentMessage() == "":
                log_print(f"In introduction stage, seeding greeting with agent name {self} and topic prompt.")
                latestOutput += f". I am {self.getName()}. Let's talk about {topic}."
            
            # I found that multiple character.ai AIs could get "deadlocked" (talking about the same thing over and over) after a certain amount of time, so we can seed conversation with prompt after certain number of messages.
            if args.deadlockavoidance:
                if messageCounter >= deadLockLimit:
                    log_print(f"Automated deadlock avoidance activated, resetting message counter and seeding prompt.")
                    latestOutput = f"{deadlock_avoidance_prompt}"
                    messageCounter = 0
                    addlog("--SYSTEM-- DEADLOCK AVOIDANCE ACTIVATED")

            log_print(f"Updating {self.getName()}'s latest message and relaying to {other.getName()}...")

            # if a response gets flagged and isn't entered (happened when Donald Trump was talking about the wall, lol), we switch to deadlock avoidance messages.
            if other.getCurrentMessage() == latestOutput:
                log_print(f"Error, response was not created, seeding with topic  prompt")
                latestOutput = f"I am {self.getName()}. Let's talk about {topic}."

            self.setCurrentMessage(latestOutput)
            print(f"{self.getName()} entered message: '{latestOutput}'")   
            addlog(f"{self.getName()}: {latestOutput}")

            other.sendMessage(latestOutput, retries = 5, timeToWaitBetweenRetries = 5)
            
            """
            If we are running a custom agent, there is no need to have a a hardcoded wait for a web response as we are assuming either:
               1. The custom agent is being run locally and will block until a response is received
               2. The custom agent is being run remotely but its code is designed to block until a response is received and will handle timeouts, etc. on its own.

            Consequently, we only use a wait timer between message sending if the agent is run in the browser through selenium.
            """
            if other.getType() != 'custom':
                timeToSleep = 20 + random.uniform(0,2)
                print(f"Message sent. Waiting {timeToSleep} seconds for response...")
                time.sleep(timeToSleep)

            if args.deadlockavoidance:
                messageCounter += 1
                log_print(f"{messageCounter} messages sent. {deadLockLimit - messageCounter} until we seed conversation to try to avoid deadlock.")

if __name__ == "__main__":
    main()