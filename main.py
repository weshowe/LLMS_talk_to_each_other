from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

import time
from datetime import datetime
import sys
import os
from pathlib import Path
import pytz
import random

# USER FIELDS
topic = "trains" # Initial topic to start the conversation, is seeded into initial messages.

pytz_timezone = 'UTC' # used to get correct timezone in logs, change this to your local timezone if you want them to show your local time instead of UTC.
chromedriver_executable_path = 'C:/chromedriver-win64/chromedriver.exe' # path to the .exe on Windows, path to containing folder on Linux.

# Antideadlock measures (see readme). Yet to come up with clever antideadlock strategy, so just seed with reminder to continue conversation when limit hit...
deadLockLimit = 25 # after this number of messages, inject deadlock avoidance prompt.
messageCounter = 0 # counts messages, resets after deadlock avoidance triggered.
deadlock_avoidance_prompt = f"Let's talk about something else related to {topic}." # This is used to (hopefully) move along the conversation when deadlock avoidance is triggered.
deadLockAvoidanceOtherFlag = False # used to propagate "stay in character" message to other agent after deadlock avoidance triggered.
# helper methods

# Searches through a list of elements for a target element, based on an attribute and some text that attribute's value should contain
def retrieveTargetElement(nodes, searchAtt, searchString, siblings = False):
    for j in nodes:
        att = j.get_attribute(searchAtt)

        # If element does not have the attribute, continue
        if att is None:
            continue

        if searchString in att:

            # Designed to group elements of a similar character, ie: p elements (to get multi paragraph answers).
            if siblings:
                
                elemList = [j]
                curElement = j

                # get successive siblings until there aren't any more (exception will be thrown)
                exitFlag = True
                while exitFlag:
                    try: 
                        nextElement = curElement.find_element(By.XPATH, f"./following-sibling::{j.tag_name}")

                        # if this got a list of stuff, assume there isn't any more and leave.
                        if isinstance(nextElement, list):
                            elemList.extend(nextElement)
                            exitFlag = False

                        else:
                            elemList.append(nextElement)
                            curElement = nextElement

                    except:
                        # if there were no siblings
                        if len(elemList) == 1:
                            return j
                        else:
                            exitFlag = False
                
                return elemList
            else:
                return j
        
    return None

# Non-JS code to fill a textarea.       
def fillTextBox(node, message):
    node.send_keys(Keys.TAB)
    node.clear()
    node.send_keys(message)   

logfile = str(Path(os.path.dirname(sys.argv[0])).resolve()) + f"/log_{time.time()}.txt"

# for log prints. Logs to directory script was run from.
def addlog(inString):
    with open(logfile, "a+") as f:
        f.write(str(datetime.now(pytz.timezone(pytz_timezone))) + " " + inString + "\n")

# program begins here.
agent1 = input("Enter name of first agent (needed for logging purposes): ")
agent2 = input("Enter name of second agent (needed for logging purposes): ")

cService = webdriver.ChromeService(executable_path='C:/chromedriver-win64/chromedriver.exe')
driver = webdriver.Chrome(service = cService)

_ = input(f"Press Enter when you have authenticated into character.ai account and opened the chat windows in 2 separate tabs, with {agent1} in first tab and {agent2} in second tab.")

handles = driver.window_handles

agents = {
    agent1: {"window": handles[0], "latestMessage": ""},
    agent2: {"window": handles[1], "latestMessage": ""}
}

while True:

    # Main loop: For each agent, retrieve its latest message and send it to the other one.
    self = None
    other = None
    for elem in agents.keys():
        self = elem
        for elem2 in agents.keys():
            if elem2 != elem:
                other = elem2
                break

        # switch to current agent window and get latest message
        driver.switch_to.window(agents[self]["window"])
        time.sleep(1)
        messages = None
        latest = None
        latestOutput = None
    
        # Retries needed to avoid StaleReferenceException. Also logic to either return output or concatenate output if it spans multiple paragraphs.
        for i in range(1, 5):
            try:
                messages = driver.find_elements(By.TAG_NAME, 'p')
                latest = retrieveTargetElement(messages, 'node', '[object Object]', siblings = True)

                if isinstance(latest, list):
                    temp = ""
                    for j in latest:
                        temp += j.get_attribute('innerHTML')
                    latestOutput = temp
        
                else:
                    latestOutput = latest.get_attribute('innerHTML')

            except:
                sleepTime = 4 + random.uniform(0, 2)
                print(f"Exception encountered when retrieving latest message for {self}, retry {i}. Waiting {sleepTime} seconds.")
                time.sleep(sleepTime)

            if latestOutput == agents[self]["latestMessage"]:
                sleepTime = 4 + random.uniform(0, 2)
                print(f"Latest message for {self} has not been updated, retry {i}. Waiting {sleepTime} seconds.")
                time.sleep(sleepTime)

        if latestOutput is None:
            raise Exception("max retries exceeded. exiting.")        
        
        # I found that the AIs sometimes wouldn't know who the other was (ie: if they didn't mention it during greeting), so agent name seeded during first greeting.
        # Also add topic prompt.
        if agents[self]["latestMessage"] == "":
            print(f"In introduction stage, seeding greeting with agent name {self} and topic prompt.")
            latestOutput += f". I am {self}. Let's talk about {topic}."
        
        # I found that the AIs would get "deadlocked" (talking about the same thing over and over) after a certain amount of time, so seed conversation with prompt after certain number of messages.
        # 25 messages was experimentally chosen, deadlock can occur before that.

        # propagates "stay in character" to other agent after deadlock avoidance triggered.
        if deadLockAvoidanceOtherFlag:
            addlog("--SYSTEM-- DEADLOCK AVOIDANCE: TELLING OTHER AGENT TO STAY IN CHARACTER.")
            latestOutput = f"Stay in character as {other}. {latestOutput}"
            deadLockAvoidanceOtherFlag = False 

        # initial deadlock avoidance.
        if messageCounter >= deadLockLimit:
            print(f"Automated deadlock avoidance activated, resetting message counter and seeding prompt.")
            latestOutput = f"Stay in character as {other}. {deadlock_avoidance_prompt}"
            deadLockAvoidanceOtherFlag = True
            messageCounter = 0
            addlog("--SYSTEM-- DEADLOCK AVOIDANCE ACTIVATED")

        print(f"Updating {self}'s latest message and relaying to {other}...")

        # if a response gets flagged and isn't entered (happened when Donald Trump was talking about the wall, lol), we switch to deadlock avoidance messages.
        if agents[other]["latestMessage"] == latestOutput:
            print(f"Error, response was not created, seeding with deadlock avoidance conversation prompt")
            latestOutput = f"Stay in character as {other}. {deadlock_avoidance_prompt}"

        agents[self]["latestMessage"] = latestOutput
        print(f"{self} entered message: '{latestOutput}'")   
        addlog(f"{self}: {latestOutput}")

        # find other agent message box.
        driver.switch_to.window(agents[other]["window"])
        time.sleep(2 + random.uniform(0, 1))
        textboxes = None
        agent_textbox = None

        for i in range(1, 5):
            textboxes = driver.find_elements(By.TAG_NAME, 'textarea')
            agent_textbox = retrieveTargetElement(textboxes, 'placeholder', 'Message')
        
            if agent_textbox is None:
                sleepTime = 4 + random.uniform(0, 2)
                print(f"Error: Could not find {other}'s textbox, retry {i}. Waiting {sleepTime} seconds.")
                time.sleep(sleepTime)
    
        # Write message into text box and validate.
        fillTextBox(agent_textbox, latestOutput)
    
        if agent_textbox.get_attribute('innerHTML') != latestOutput:
            print(f"Could not enter {self}'s Message into {other}'s textbox. Expected: {latestOutput}, Actual: {agent_textbox.get_attribute('innerHTML')}")

            if agent_textbox.get_attribute('innerHTML') == "":
                raise Exception("Entered message is blank. Something has gone horribly wrong, exiting.")
            
            else:
                print("Input is not blank, ignoring discrepancy, likely due to HTML tags in message being incorrectly parsed. TODO: add regex or something to prune these.")
    
        # Find button.
        buttons = driver.find_elements(By.TAG_NAME,'button')

        agent_button = retrieveTargetElement(buttons, 'aria-label', "Send a message")

        if agent_button is None:
            raise Exception(f"Error: Could not find {other}'s send message button.")
    
        time.sleep(1)

        # send message and wait. Retry button click if it doesn't work (this randomly broke once)
        buttonClicked = False     
        for i in range(1, 5):

            try:
                agent_button.click()
                buttonClicked = True
                break
            
            except:
                sleepTime = 5 + random.uniform(0,2)
                print(f"Error: Could not click {other}'s send button, retry {i}. Waiting {sleepTime} seconds.")
                time.sleep(sleepTime)
        
        if not buttonClicked:
            raise Exception("max retries exceeded, exiting.")
        
        timeToSleep = 20 + random.uniform(0,2)
        print(f"Message sent. Waiting {timeToSleep} seconds for response...")
        time.sleep(timeToSleep)
        messageCounter += 1
        print(f"{messageCounter} messages sent. {deadLockLimit - messageCounter} until we seed conversation to try to avoid deadlock.")