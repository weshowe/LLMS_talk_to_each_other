from abc import ABC, abstractmethod
import random
import time
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from util import *

# Sample dependencies for a custom agent, this is for torch and hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4
# Use or replace these with your imports
#from transformers import AutoModelForCausalLM, AutoTokenizer, AwqConfig
#import torch

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
    
    def getType(self):
        return self.type

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
# As an example, I have included the code needed to use an INT4 quantized Llama-3.1-8B agent.
class customAgent(Agent):

    # some fields relating to the model object should be added here.
    def __init__(self, name, driver, window):

        # Use or replace this section with your code
        """
        model_id = "hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4"
        quantization_config = AwqConfig(bits=4,fuse_max_seq_len=512, do_fuse=True,)
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            torch_dtype=torch.float16,
            low_cpu_mem_usage=True,
            quantization_config=quantization_config
        ).to("cuda")
        """

        super().__init__("custom", name, None, None)
    
    def getLatestMessage(self, **kwargs):

        # since a custom agent will likely not have an initial greeting, this seeds one if this agent is chosen to start the conversation.
        if self.currentMessage == "":
            self.currentMessage = f"Hello, I am {self.name}."

        return self.currentMessage
    """
    API call goes in this method. We are making the following assumptions:

     1. self.currentMessage will be updated at the end of this method.
     2. The code will block until a response is received.
     3. It is user's responsibility to decide how to handle timeouts and the like.
     4. It is the user's responsibility to parse the output into a string.
    """
    def sendMessage(self, message, **kwargs):

        # Use or replace this section with your code
        """
        # TODO: Find way to integrate system role, ie: for Llama it would be by adding to prompt dict: {"role": "system", "content": "You are a helpful assistant that responds as a pirate."},
        # This kind of parameter is the likely source of the character configurations in character.ai, should research this more.
        prompt = [{"role": "user", "content": message}]

        inputs = self.tokenizer.apply_chat_template(
            prompt,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
            return_dict=True,
        ).to("cuda")

        outputs = self.model.generate(**inputs, do_sample=True, max_new_tokens=512)
        outMessage = self.tokenizer.batch_decode(outputs, skip_special_tokens=False)[0]

        # message formatting to return plaintext. In this case, we retain Llama's special tokens so we can parse it correctly.
        # If the message is truncated, the eot_id tag won't be present at the end of the output, so we leave it and run the output through the HTML tag regex to remove it if it happens to be there.
        outMessage = stripHtmlTags(outMessage[outMessage.rfind('<|end_header_id|>') + len('<|end_header_id|>'):outMessage.rfind("<|")].replace("\n\n", " ").replace("\n", " "))
        
        self.currentMessage = outMessage
        """


# provides agent name -> object mapping to be used in main.py
agent_types = {"character.ai": characteraiAgent, "Replika": replikaAgent, "custom": customAgent}