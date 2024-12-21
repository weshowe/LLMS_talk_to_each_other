import re
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By

# web scraping helper methods.
htmltagStripper = re.compile('<.*?>')
verbosity = False

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

# Searches through a list of elements for a target element, based on an attribute and some text that attribute's value should contain
def retrieveTargetElements(nodes, searchAtt, searchString):

    out = []
    for j in nodes:
        att = j.get_attribute(searchAtt)

        # If element does not have the attribute, continue
        if att is None:
            continue

        if searchString in att:
            out.append(j)
        
    return out

# Non-JS code to fill a textarea.       
def fillTextBox(node, message):
    node.send_keys(Keys.TAB)
    node.clear()
    node.send_keys(message)   

def stripHtmlTags(inString):
  outString = re.sub(htmltagStripper, '', inString)
  return outString

# other helper methods
def log_print(inString):
    if verbosity:
        print(inString) 