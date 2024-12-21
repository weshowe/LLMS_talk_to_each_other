from abc import ABC, abstractmethod
import random
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

from util import *

class Agent(ABC):
    def __init__(self, type, name, driver, window):
        self.type = type
        self.currentMessage = ""
        self.handle = None
        self.name = name
        self.window = window
        self.driver = driver

    def setCurrentMessage(self, message):
        self.currentMessage = message

    def getCurrentMessage(self):
        return self.currentMessage
    
    def getWindow(self):
        return self.window
    
    def getName(self):
        return self.name

    @abstractmethod
    def getLatestMessage(self, **kwargs):
        raise NotImplementedError("Must override getMessage()")
    
    @abstractmethod
    def sendMessage(self, message, **kwargs):
        raise NotImplementedError("Must override sendMessage()")

class characteraiAgent(Agent):
    def __init__(self, name, driver, window):
        super().__init__("character.ai", name, driver, window)
    
    def getLatestMessage(self, retries = 5, timeToWaitBetweenRetries = 5, randomOffset = 1):

        self.driver.switch_to.window(self.window)
        latestMessage = None

        for i in range(0, retries + 1):

            if i > 0:
                sleepTime = timeToWaitBetweenRetries + random.uniform(0, randomOffset)
                log_print(f"getLatestMessage() for {self.type} agent {self.name}: Retry {i}. Waiting {sleepTime} seconds.")
                time.sleep(sleepTime)
            
            messageFound = True
            try:
                messages = self.driver.find_elements(By.TAG_NAME, 'p')
                latest = retrieveTargetElement(messages, 'node', '[object Object]', siblings = True)

                if isinstance(latest, list):
                    temp = ""
                    for j in latest:
                        temp += j.get_attribute('innerHTML') + " "
                    latestMessage = temp
        
                else:
                    latestMessage = latest.get_attribute('innerHTML')

            except:
                log_print(f"getLatestMessage() for {self.type} agent {self.name}: Exception encountered when retrieving latest message.")
                messageFound = False

            if latestMessage == self.currentMessage:
                log_print(f"getLatestMessage() for {self.type} agent {self.name}: Latest message is not available.")
                messageFound = False

            if messageFound:
                break

        if latestMessage is None:
            raise Exception(f"getLatestMessage() for {self.type} agent {self.name}: Latest message not retrieved and max retries exceeded {retries}.")
        
        return latestMessage

    def sendMessage(self, message, retries = 5, timeToWaitBetweenRetries = 5, randomOffset = 1):

        self.driver.switch_to.window(self.window)
        textboxes = None
        agent_textbox = None

        for i in range(0, retries + 1):

            if i > 0:
                sleepTime = timeToWaitBetweenRetries + random.uniform(0, randomOffset)
                log_print(f"sendMessage() for {self.type} agent {self.name} (textbox finding stage): Retry {i}. Waiting {sleepTime} seconds.")
                time.sleep(sleepTime)

            textboxes = self.driver.find_elements(By.TAG_NAME, 'textarea')
            agent_textbox = retrieveTargetElement(textboxes, 'placeholder', 'Message')
        
            if agent_textbox is None:
                log_print(f"sendMessage() for {self.type} agent {self.name} (textbox finding stage): Could not find textbox.")

            else:
                break
    
        if agent_textbox is None:
            raise Exception(f"sendMessage() for {self.type} agent {self.name} (textbox finding stage): Could not find textbox and max retries exceeded {retries}.")
        
        # Write message into text box and validate.
        fillTextBox(agent_textbox, message)
    
        if agent_textbox.get_attribute('innerHTML') != message:
            log_print(f"sendMessage() for {self.type} agent {self.name} (text entering stage): Could not enter message into textbox. Expected: {message}, Actual: {agent_textbox.get_attribute('innerHTML')}")

            if agent_textbox.get_attribute('innerHTML') == "":
                raise Exception("Entered message is blank. Something has gone horribly wrong, exiting.")
            
            else:
                log_print(f"sendMessage() for {self.type} agent {self.name} (text entering stage): Input is not blank, ignoring discrepancy, likely due to HTML tags in message being incorrectly parsed. TODO: add regex or something to prune these.")
        
        # Send chat by pressing enter in the textbox.
        agent_textbox.send_keys(Keys.ENTER)

class replikaAgent(Agent):
    def __init__(self, name, driver, window):
        super().__init__("Replika", name, driver, window)
    
    def getLatestMessage(self, retries = 5, timeToWaitBetweenRetries = 5, randomOffset = 1):

        self.driver.switch_to.window(self.window)
        latestMessage = None

        for i in range(0, retries + 1):

            if i > 0:
                sleepTime = timeToWaitBetweenRetries + random.uniform(0, randomOffset)
                log_print(f"getLatestMessage() for {self.type} agent {self.name}: Retry {i}. Waiting {sleepTime} seconds.")
                time.sleep(sleepTime)
            
            messageFound = True
            try:
                messages = self.driver.find_elements(By.CSS_SELECTOR, "div[data-testid='chat-message-text']")
                latestDiv = messages[-1]
                latest = latestDiv.find_element(By.XPATH, ".//span")
                latest = latest.find_element(By.XPATH, ".//span")
                latestMessage = latest.get_attribute('innerHTML')


            except Exception:
                log_print(f"getLatestMessage() for {self.type} agent {self.name}: Exception encountered when retrieving latest message.")
                messageFound = False

            if latestMessage == self.currentMessage:
                log_print(f"getLatestMessage() for {self.type} agent {self.name}: Latest message is not available.")
                messageFound = False

            if messageFound:
                break

        if latestMessage is None:
            raise Exception(f"getLatestMessage() for {self.type} agent {self.name}: Latest message not retrieved and max retries exceeded {retries}.")
        
        return latestMessage

    def sendMessage(self, message, retries = 5, timeToWaitBetweenRetries = 5, randomOffset = 1):

        self.driver.switch_to.window(self.window)
        textboxes = None
        agent_textbox = None

        for i in range(0, retries + 1):

            if i > 0:
                sleepTime = timeToWaitBetweenRetries + random.uniform(0, randomOffset)
                log_print(f"sendMessage() for {self.type} agent {self.name} (textbox finding stage): Retry {i}. Waiting {sleepTime} seconds.")
                time.sleep(sleepTime)

            textboxes = self.driver.find_elements(By.TAG_NAME, 'textarea')
            agent_textbox = retrieveTargetElement(textboxes, 'id', 'send-message-textarea')
        
            if agent_textbox is None:
                log_print(f"sendMessage() for {self.type} agent {self.name} (textbox finding stage): Could not find textbox.")

            else:
                break
    
        if agent_textbox is None:
            raise Exception(f"sendMessage() for {self.type} agent {self.name} (textbox finding stage): Could not find textbox and max retries exceeded {retries}.")
        
        # Write message into text box and validate.
        fillTextBox(agent_textbox, message)
    
        if agent_textbox.get_attribute('innerHTML') != message:
            log_print(f"sendMessage() for {self.type} agent {self.name} (text entering stage): Could not enter message into textbox. Expected: {message}, Actual: {agent_textbox.get_attribute('innerHTML')}")

            if agent_textbox.get_attribute('innerHTML') == "":
                raise Exception("Entered message is blank. Something has gone horribly wrong, exiting.")
            
            else:
                log_print(f"sendMessage() for {self.type} agent {self.name} (text entering stage): Input is not blank, ignoring discrepancy, likely due to HTML tags in message being incorrectly parsed. TODO: add regex or something to prune these.")
        
        # Replika chat is sent by pressing enter in the textbox.
        agent_textbox.send_keys(Keys.ENTER)

# This is a starter class for a custom agent should you wish to implement one.
# It is made assuming that the agent will have some API call where you send it a message and an object is returned containing the response.
class customAgent(Agent):

    # some fields relating to the model object should probably be added here.
    def __init__(self, name):
        super().__init__("custom", name, None, None)
    
    def getLatestMessage(self, **kwargs):

        # since a custom agent will likely not have an initial greeting, this seeds one if this agent is chosen to start the conversation.
        if self.currentMessage == "":
            self.currentMessage = f"Hello, I am {self.name}."

        return self.currentMessage

    # API call goes in this method, assuming self.currentMessage will be updated at the end.
    def sendMessage(self, **kwargs):
        pass

# provides agent name -> object mapping to be used in main.py
agent_types = {"character.ai": characteraiAgent, "Replika": replikaAgent, "custom": customAgent}