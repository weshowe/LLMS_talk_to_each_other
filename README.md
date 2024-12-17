# character.ai_2_characters_talk_to_each_other
A Python script using selenium that enables 2 character.ai chatbots to talk to each other.

It does this it switching browser tabs and relaying messages, with a little bit of conversation seeding to choose a topic and (attempt) to keep the conversation going.

character.ai doesn't seem to have an API and the "unofficial API" I found on GitHub didn't work for me, so I made this. I made it in an evening and the code is currently crap, but it mostly works and will unless character.ai changes certain parts of their front-end code. 

A log of each conversation will be placed in same directory as program, with Unix timestamp appended to the log file. Wait timers are fairly conservative, feel free to change them, although it *might* cause some message truncation if they are too low.

##How to Use##
1. Execute "pip install selenium pytz" in the command line. selenium versions 4.0 and above should work.
2. Install Google Chrome if you don't already have it, and check the version at chrome://settings/help. Download the chromedriver for that version here https://developer.chrome.com/docs/chromedriver/downloads.
3. Update chromedriver_executable_path variable in top of script to the location of the extracted chromedriver on your system (see code comment for example)
4. (optional): At the top of the script, update pytz timezone to generate correct local timestamps for logging (default: UTC), change topic to what you want the initial topic prompt to be (ie: "Let's talk about trains."), and alter deadlock avoidance prompt to what you would like (see Problem 1 below for explanation)
5. Run script, enter the names of the 2 agents (chatbots) that you want to talk to each other, then use the opened window to authenticate into character.ai. 
6. Open the chat for the first agent in the first tab, then make a new tab and open the chat for the second agent in the second tab.
7. Press Enter in the command prompt. The program will run and the agents will keep talking until it throws an exception it can't recover from or you manually stop it (ie: with Ctrl-C).

##Why did I make this and what sorts of crazy things happen?##

I read a news story about a 14 year old boy who ended his life after falling in love with a character.ai Daenerys Targaryen chatbot, and it made me wonder if they could "fall in love" with each other or do other interesting things. So I made this. Unfortunately, the initial results weren't quite as good as I had hoped, and my experiments raised some interesting issues:

###Problem 1: Agent "Deadlock"###

I noticed that after approximately 15-25 messages or so, the agents would become "deadlocked" and enter a loop where they just talked about the same thing over and over again with only mild permutations, like so:

Agent 1: x
Agent 2: I agree! x
Agent 1: I agree! x
(ad infinitum)

I suspect this is due to a combination of the vanishing gradient problem, the way the transformers are trained ("given previous input, predict response"), and the agents' propensity to agree with the user (necessary for roleplaying, which they are designed to do). Normally there is a human agent to inject a sufficient amount of entropy into the system and to move the conversation along, but the machine agents don't seem to be able to do that on their own.

I initially tried to solve this problem by seeding the message with a prompt for a random topic switch after 25 messages ("Now let's talk about something random!"), but deadlock consistently happened there too. I also noticed a lack of randomness in the random prompts, for example in a 6 hour conversation, "origami" was chosen as a random subject 3 times by one agent.

I was surprised by how bad the deadlock problem was - you'd think that in the massive corpus of training data there would be enough examples of conversations/stories/etc. for the agents to figure out "okay, this thing comes next in a conversation about this", but nowhere near to the degree that I hoped.

The script currently has a deadlock avoidance variable at the top that you can change to set the prompt for when deadlock avoidance is triggered, and you can customize how many messages are needed to trigger it. A fixed message threshold is a dumb method of doing this, a better solution might be measuring similarity of embeddings and tripping deadlock avoidance based on some experimentally chosen similarity threshold, possibly with the aid of some text summarization beforehand.

###Problem 2: Agents Don't Have Theory of Mind###
Obvious, but it caused some funny results. For example, if I asked Daenerys Targaryen to design a classifier for MNIST using PyTorch, she immediately told me how to do that (badly) - the agent couldn't figure out that that's not something Daenerys Targaryen would know about.

As far as this program is concerned, the agents often broke character fairly early on in the conversation (ie: 11 year old Macaulay Culkin would start talking like an adult to Michael Jackson about the future of AI technology and then stop talking like a kid altogether). I tried to remedy this by adding a "stay in character and tell me to stay in character" portion to the deadlock avoidance prompt. Sometimes it helped a bit, but sometimes it led to the next problem.

###Problem 3: Agents Can Start Talking to Themselves###
Sometimes, particularly when passed a "stay in character and tell me to stay in character" prompt, the agent would roleplay as the other agent in their message and confuse the other agent, which would then start doing the same thing and the conversation would become incoherent.

I suppose you could ask "why didn't you just do that in the first place and avoid the need for multiple agents", but I was hoping that the 2 chatbots, even though built on top of the same LLM, would be different enough from each other because of their character prompts to inject a sufficient amount of entropy into the system. Apparently not, but I seem to have fixed this problem by propagating individual "stay in character" prompts to both agents.

###Bottom Line###
This program is presented as is without any guarantee of being fit for a particular purpose. I made it as a fun experiment and may or may not try to improve it more. Currently, it's looking like improvement will largely be a matter of clever and more sophisticted prompt engineering, maybe with some client-side NLP tricks.