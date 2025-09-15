# Let's find job offers

This is a personnal project to explore web scrapping, data retrieval, data processing and LLMs integration.

The project's goals are to get an automated way of finding new job offers, use different methods to scrappe data, use LLM for information extraction and check if it is reliable.

- Discover the scrapping library **Crawl4AI**
- Use **LangChain** and **Pydantic** to monitor and validate the LLM's output
- Use the amazing **Polars** expressions

*The ultimate goal of the project is to learn more and practice.*

## Data

We extract data from 2 different websites using a different approach for each:
- webscrapping: with CSS selectors (using Crawl4AI)
- By retro-enginering the website's hidden API to access the data directly.

Scrapped data will be processed twice:
- with an LLM
- with traditionnal string manipulation. 

We compare the differences and the pro and cons of each method.


## Extracting Data from the Web

### Using web scrapping

Web scrapping is the action of extracting information from a web page. Different approachs exist and the output is a mix of the targeted data and unwanted elements or information. This require to process the output to keep only the usefull informations and to have a formated structured output, ready to be used.

I did my scrapping in 2 steps: 

1. extract links from a search page.

2. extract the content of each page of the extracted links.

Crawl4AI produces a nice output in markdown format, perfect to ingest into an LLM.

We use CSS selectors to focus the scrapper and convinient Crawl4AI functions to filter the content even more.

This allows us to extract almost only the desired content with almost no noise.


### Using hidden API

This approach asked me to understand how web browser and the web works and I will breifly detail what i learned.

The web browser is the core application of modern web browsing.

Web pages are built from multiple components that work together. 
- **HTML** provides the structure
- **CSS** files define the visual styling (how the page looks)
- **JavaScript** files add interactivity and dynamic behavior. 
- more static resources like images.

HTML and CSS are static - they load quickly and provide the visual foundation. JavaScript is dynamic. It enables all the interactive features and real-time content updates that make modern websites.

When a user acces a website:

1. Browser requests the page: Sends a **GET request** to the server
2. Server responds with HTML: Returns the basic page structure (often empty) and links to other resources
3. Browser downloads resources: Fetches CSS files, JavaScript files, and images in parallel
4. Browser renders the page: Applies CSS styling to create the visual layout
5. JavaScript executes: Runs code that makes API calls to fetch actual data
6. Dynamic content loads: JavaScript processes API responses and populates the empty page with real content
7. Page becomes fully interactive with all the dynamic features


If we use the **browser's devtools** network panel, we can inspect the trafic between the browser and the server.

If the API is straightforward, visible in the network traffic and has minimal authentification, we can extract the request as a cURL command using the devtools.

We can use the element of the cURL command to create a python script to extract the data we want in the format we want. (Although this could be even more straightforward (and simpler) with command line scripting, but as a datascientist, I love python and will use it)

When using a web browser we **have to** acces the web throught the browser interface. While this makes the web usable for the majority of people, it is a constraint when the goal is simply to catch and store the content in a file. In this approach we bypass the browser part to access to the data directly.

With a web browser:

**Browser → HTML → JavaScript → API call → Data → Populate page**

With bypass:

**Script → API call → Data (same data)**

Pros: 
- fast execution
- access directly the data in as **structured output**
- no scrapping to do
- significantly easier and faster to implement compared to a scrapping pipeline

Cons:
- not always possible (authentification and security)
- need maintenance: the API can change
- can be grind to find the right API call that delivers the right data

Disclaimer:

This is not illegal: we only access the data provided in the web page using a *public API*.   Nevertheless, we have to respect the API's owner and not overwhelm their infrastructure and follow the **robot.txt** guidelines. In our case we do a call to get the data for each web page but it's no difference from loading a web page with the web browser so our usage of the API is very small.



#### LLM

I wanted to use a small LLM that could run **locally** on my machine to have a **free**, **low ressources** and **offline** solution. I used Ollama with a M1pro macbook.

I selected the model [**qwen2.5:3b**](https://ollama.com/library/qwen2.5) because it supports JSON outputs and has big context window.

When using an LLM it's important to define what we want it to do and how.

In this project we use the LLM for **content extraction** and it is particularly suited because:
- 100% of the content to extract is in the input
- the input is well structed with markdown headers
- the input is <10K characters (≈22K tokens + prompt, far from the 128K tokens context limit of the model)
- Pydantic validate the output, ensure that it suits our data structure, and guide the LLM

With all this elements, the LLM's job is less prone to errors or unexpacted outputs.

I tested different models of different sizes and here are my observations:
- in very rare cases the LLM changes small words but with no impact on the meaning of the text
- If a section is long, the LLM can stop and ignore the rest
- Some words are misinterpreted as sections's title,
- Some words are misinterpreted. The LLM thinks that they are another section's title, or that the word is different context from the previous lines and therefore ignore the rest of the text. I couldn't fix this behaviour with prompt engeneering.
- Some models hallucinated part of the output despite the temperature being 0, and the prompt emphsinzing to absolutely not do that.
- Bigger models (~7b params) didn't produce better results. I couldn't test the bigest of 'small models' (~30b params), but I suspect them do perform much better
- LLm took between 24s and 60s to process a document

**Conclusion on the LLM:**
- The model run perfectly well with no RAM pressure on my machine and manage to do the work as intended
- Preprocessing steps on the input are mandatory to remove the elements that would confuse the model and make it ignore part of the content
- The model failed to extract all the content for some job offers. Usually for the longer sections (missions, profile). Some longer offers are perfectly extracted, some shorter ones not. I suspect keywords or sentences to confuse the model. The model missed the last sentence of long paragraph more than any other mistake.
- Even if the model is not 100% reliable, the extracted content is enough for the purpuse of exploring the job offer, understanting what it is about and building a database.
- The prompt played a smaller role than expected. I tried to run it with the minimalist prompt: 'extract the content'. It performs very well despite the lack of detailled instructions but they were more errors like summarizations or rewriting of some words. The pydantic model is probably the key element more than the prompt for my task.
- LLM performs extremely well on the extracation of content of smaller size and processed my content at a convienient speed. 




#### Polars expressions

I did the same task than the LLM but with polars, using traditionnal string manipulation.

The key part was using Polars expressions that allows to adapt to each file. Therefore we have a dynamic and understandable code that is easy to maintain.

Polars expressions is one way amongs many to do this job.

## Pros and cons of a small LLM vs Traditional string manipulations

**LLM:**
pros: 
- Excellent for the extraction off multiple, well defined, short content
- Easier and faster to implement
- code overall simple to undestand
- bigger models would be more reliable at this task

cons: 
- requires to understand how the LLM will handle the task and some test and retry
- requires hardware

**String manipulation:**
pros:
- deterministic, reliable
- very fast execution
- works with minimal ressources

cons: 
- longer to set up
- need problem solving skills and good logic
- need to analyse and understand the challenges of the the content to treat all the possible cases
- complex code that is harder to maintain and to understand. The accumulation of unique cases or conditions to take into account can worsen this.



---
gathering job offers from different websites to have an automated way of finding new job offers. Data ends up in a single csv files that can be explored (!TODO - dashboard or APP)

We explore different ways of retreiving the data: - webscrapping - API calls

We explore different ways of processing the extracted data: - with LangChain using an small LLM that runs locally - with traditionnal string manipulation with *Polars*

We discuss the pro and cons of each approachs and why we use them.

Main libraries used: - Polars - LangChain - Crawl4ai - Pydantic

(real data, simple, interesting and usefull, expendable)