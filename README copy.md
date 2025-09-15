# Introduction - let's find job offers

This is a personnal project to explore web scrapping, data retrieval, data processing and LLMs integration.

The project's goals are to get an automated way of finding new job offers, use different methods to scrappe data, use LLM for information extraction and check if it is reliable.

- Discover the scrapping library **Crawl4AI**
- Use **LangChain** and **Pydantic** to monitor and validate the LLM's output
- Use the amazing **Polars** expressions

We will extract data from the web using 2 approches:
- web scraping 
- API reverse engineering

We will process and extract the data with 2 approches: 
- with an LLM
- with traditional string manipulation

### Libraries:

- **[Crawl4AI](https://github.com/unclecode/crawl4ai)** for web scrapping 
- **[LangChain](https://www.langchain.com/langchain)** and **[Pydantic](https://docs.pydantic.dev/latest/why/)** to set up the LLM and validate it's output
- **[Polars](https://github.com/pola-rs/polars)** for data manipulation using Dataframes and modern synthax

#### prerequisites


*The ultimate goal of the project is to learn more and practice.*

# Methodology

## Data sources

We extract data from 2 different websites:

[Choisir le service public](https://choisirleservicepublic.gouv.fr/): Official french public service job's platform.

[APEC](https://www.apec.fr/): French organization to supporting white-collars in their career transitions and professional development. It is also a job offer platform.


We used a different approach for each:
- webscrapping: with CSS selectors (**Choisir le service public**)
- By retro-enginering the website's hidden API to access the data directly (**APEC**)

## Extracting Data from the Web

### Approach 1: Web scrapping

Web scrapping is about extracting information from a web page. 
Different approaches exist and the output is a mix of the targeted data and unwanted elements or information.
This require to process the output to keep only the usefull informations and to have a formated structured output, ready to be used.

2 steps scraping: 

1. extract links from a search page.
2. extract the content of the page for each link.

Crawl4AI produces a nice output in markdown format, perfect to ingest into an LLM and has convinient functions to filter the content.

We used CSS selectors to focus the scrapper.
This allowed to extract the desired content with limited noise to remove later.


### Approach 2: API reverse engineering

The concept is to analyse the HTTP requests and responses exchanged between the web browser and the server. This is easy to do with the  browser's devtools **network panel**.

This approach asked me to understand how web browser and the web works and I  breifly detailed what i learned in the [Analysis](#analysis) section.

The **browser's devtools** network panel, shows in real time all the requests and responses that occurs since the page was loaded. We can explore the request and find the ones that contain data. We have to test the APIs, understand their purpose, maybe the interactions between the different APIs, because there are no documentations to help us for those hidden APIs.

The goal is to have a command with the right filters, to get only the data we want from the API.  The devtools allow us to copy as a cURL command the requests of the panel and this the info we need to build a **post** request to use in python with the resquest **module**. We could also have stick to the command line and with minimal shell scripting achieve the same result. It's only for personal preferences that I used Python since using the command line is usually more straightforward to implement and faster.

If the API is straightforward, visible in the network traffic and has minimal authentification, finding the elements we need is very easy.

**SCREENS OF THE DEVTOOLS**

Furthermore, JSON is the standart data format for web content mainly for it's compatibility with JavaScript and for it's simplicity/ lightwheight. This is important to us because the extracted data is already in the format we want it in.

Another benefit of this approach is skipping the web browser entirely from the extraction process. Since we request the server directly using an API. We save time, we don't have to deal with HTML code or scraping waste, and it's simpler to implement.

With a web browser:

**Browser → HTML → JavaScript → API call → Data → Populate page → Scraping → Post processing → Structured data**

With bypass:

**Script → API call → Structured data (same data)**

Pros: 
- fast execution
- access directly the data in a **structured output**
- no scrapping to do
- significantly easier and faster to implement compared to a scrapping pipeline

Cons:
- not always possible (authentification and security)
- need maintenance: the API can change anytime 
- can be a grind to find the right API call that delivers the right data

Disclaimer:

This is not illegal: we only access the data provided in the web page using a *public API*.   
Nevertheless, we have to respect the API's owner and not overwhelm their infrastructure and follow the **robot.txt** guidelines. In our case we do a call to get the data for each web page but it's no difference from loading a web page with the web browser so our usage of the API is very small.


### Data processing

Scrapped data is processed twice to obtain the same result to compare both solutions:

1. With an **LLM**:

Asking it to extract the content of the job offer and fill a structured JSON with a defined schema. The job offer in input will be a markdown document, direct output from the web scrapping.

To work with LLMs we need: 

- a tool to download and manage LLMs on our machine: **[Ollama](https://ollama.com/)** is an open source project to work with LLMs locally.

- local hardware: Since the Apple Silicon chips, macbooks can run smaller LLM with very good speed, efficiency and performances. All together we have a solution that is free, unlimited and offline. 

- softwares to work with LLM: **Langchain** is the reference and **Pydantic** is now also the reference when working with LLM. When using those 2 libraries, we can build a chain that uses an LLM and that will produce a structured output that will be validated with Pydantic.


2. With **traditionnal string manipulation** 

Our inputs are markdown files that are basically structured text, therefore using string manipulations and regex patterns, we can shape them to be a structured output

We will use Dataframes for an efficient processing and **Polars** provide a great API to work with strings and dataframes. 

We will have a tidy dataframe with a row for each job offer, and a column for each information we want to extract. This way we can do the same transformations on all the offers easily and at the same time.

Polars is great because it has a whole API to process strings of text (Series in polars) with ***expressions***. The expressions allow to perform operations on columns or rows in an optimized and vectorized way. They can be seen as custom functions since they can be crafted, named, and be used multiple times on different data. We build an expression with a precise purpose. 

We can then create a pipeline that uses the expressions.

For example: Instead of a single block of code that chain 20 actions, we have a block  that uses 4 expressions of 5 actions, that are named after what they do. Our pipeline can almost be read like a sentence.   
This approach also limits the number of intermediate outputs that load the RAM and makes the code much harder to maintain.  
Expressions also allows polars to evaluate the code before running it, allowing for optimizition for faster and more effecient code.

To sum up, we have cleanner, optimized and efficient code, that is easier to understand and to maintain.



Both outputs will be in JSON format for easy comparison.

I already know traditionnal string manipulation and that it will do the job. We will see if the LLM can be a solution as well.


### Model selection

Choosing the right model can be a complicated task.  
I selected the model [**qwen2.5:3b**](https://ollama.com/library/qwen2.5) mainly because it supports JSON outputs and has a big context window.

Choosing the right model can be a complicated task and testing many models takes time and ressources. I decided to select a model that had good results with no optimisation and tried to improve from here.  
It is also important to define what we want the model to do and how.

In this project we use the LLM for **content extraction** and it is particularly suited because:
- 100% of the content to extract is in the input
- the input is well structed with markdown headers
- the input is <10K characters (≈22K tokens + prompt, far from the 128K tokens context limit of the model)

#### LLM

I wanted to use a small LLM that could run **locally** on my machine to have a **free**, **low ressources** and **offline** solution. I used Ollama with a M1pro macbook.


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

# Results

### Web scraping outcomes:

Link extraction: 
- direct JSON output, single file
- 1 important key "**href**", contains the direct link to a job offer.
- One object for each link

Job offer extraction:
- one markdown file for each job offer
- only text and markdown synthax
- clean output, all the offer's text is extracted
- few irrelevant elements that are the title of JavaScript interactive elements like "Afficher la suite" (to show a hidden content) or "Flèche gauche, Flèche droite" (integrated map navigation arrows)
- Almost like a markdown version of the HTML

The extraction is a succes because all the content is accessible and with almost only relevant content so no more cleanning is needed for the next step.

### API bypass outcomes:

The resquest output is a JSON file with 2 objects:
- resultats: contains the job offer informations
- totalCount: total number of offers found

The request only ask for the page 1 offers so we only have a few objects, for each extracted offer.  
The file has the following keys:
- id
- intitule (offer's title)
- lieuTexte (localisation)
- salaireTexte (salary)
- texteOffre (offer's description, mission, profile etc...)
- datePublication (offer's publication date)
- typeContrat (contract type, fixed or permanent)
- contractDuration (contract's duration)
- url



### LLM performance:

- The model was able to process the markdown files and return a valid JSON output.
- It took between 25s and 60s to process a file
- The hardware handled it fine and the RAM pressure was kept in the green, meaning that some remained free.

Accuracy observations:
- in very rare cases the LLM changes small words but with no impact on the meaning of the text
- If a section is long, the LLM can stop and ignore the rest
- Some words are misinterpreted or interpreted as sections's title leading the  LLM to stop the extraction for a given key



### Polars processing:

- The script runs very fast and procuces the desired output
- The script adapt to each file and process it correctly regarding its specificities in the markdown headers
- Extract all the content for all the possible keys
- Output is in CSV and/ or JSON



### Comparison between Polars and LLM results:

Excecution time :
- LLM:
- Polars

To compare the differences between the LLM's output and Polars's output, I used *git diff* on JSON files. I selected the offer_3 that showcase most of the differences.  
White text is present in both.  
Green text is only present is the LLM's output  
Red text is only present in the polars's output  

Let's details the git diff.  

This shows when the content is the same for both as well as small differences that don't have a major impact on the meaning.  

![small_diff_and_normal](outputs/compare_results/small_diff_and_normal.png)  

This shows the major issues from the LLM, missing block of content from the bigger sections: Missions. The big red part is not found in the LLM output 

![missing_content](outputs/compare_results/missing_content_missions.png)   

This shows how the LLM sometimes simpliffies the information and thus miss some of the content.   

![simplification_content_and_missed](outputs/compare_results/simplification_content_and_missed.png)  

This is a particularly bad example of the LLM failures. In most offers, the differences are in small words, sentences that are slighlty different or punctuation.





# Analysis

### How browsers work:

The **web browser** is the core application of modern web browsing. It is the gateway to the internet for 99% of the people and is one of the element that makes the modern web. It is also the most used application on computers and nowadays almost everything can be done on the internet therefore with a web browser.

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

### LLM evaluation: Detailed pros/cons, failure patterns, prompt engineering findings

**pros**: 
- Excellent for the extraction off multiple, well defined, short content
- Easier and faster to implement
- code is overall easy to undestand
- bigger models would be more reliable at this task

**cons**: 
- requires to understand how the LLM will handle the task and some tests and retries
- requires hardware


### String manipulation evaluation: Polars expressions approach

Let's dive into the Polars expression in the function "build_concat_expressions".  


```{python}
expr = pl.concat_str(
                [pl.col(col) for col in existing_cols], separator="\n"
            ).alias(alias)
```

This expressions works with polars datasets has it does modification on **multiple columns**.  
Let's brake it down:  
- ```pl.col()``` selects columns of the dataset
Here we have a list comprehenssion to select all the columns from a list. This is part of the adaptative approach we used to handle the different file stuctures.
- ```pl.concat_str(..., separator="\n")``` concatenates the content of selected columns into a single string. The serator is the element to be placed between each piece. So we basically join the content of the selected columns, and place them into a **new** variable, and we use the newline character \n to seperate each joined element in the new string.  
- ```.alias()``` is a function to rename variables. Here it rename the variable we just have created. 

So this expressions:
- selects variables
- concatenantes values
- rename the created variable

To use the expression we call it by it's name like a function 


---

Polars expresions are ment to work with polars DataFrames.

```
remove_noise_and_whitespaces = (
    pl.all()
    .str.strip_chars()
    .str.replace_all(
        r"^(.*?)\n", value=""
    )  # remove first line if it ends with a \n (it removes the headers artifacts)
    # .str.replace_all(r"\n", value=" ")
)
```
Let's break it down:
- The expresion's name should inform what it does --> It remove unwanted content as well as whitespaces.
- ```pl.all()``` select all the variable of the dataset
- ```str.str_chars()``` removes leading and trailling whitespaces from the string values
- ```.str.replace_all(r"^(.*?)\n", value="")``` replaces a match patterns by a value.  
Since we replace with nothing, we remove the element.  
What we want to remove is given by the *regex* pattern "^(.*?)\n". Let's break it down:
**^** means the start of the string
The parathesis **()** declare a capture group
**.** means any character expect a newline
**\*** is a quantifier, * mean 0 or more
**?** this makes the quantifier non-greedy so we match as few as possible until the pattern is satisfied.
**\n** is a newline character.

We can express this regex as a sentence:  
- From the start of the line, match any character until it encounters a newline character. The pattern will stop at the first newline character found after the pattern, rather than going to the *last* newline character it can find.

In practice, this pattern is used to extract the first line of a string. In my case, the first line was the markdown header and i didn't wanted the header in the content since the variable name already had the information.
- ```.str.replace_all(r"\n", value=" ")``` replace the newline characters by a blank. This effectively makes the content a single line.

Going back to the expression's name:
- It removes noise (markdown headers that are the first lines of the strings)
- It removes whitespaces
- It makes the document a single line 


This expression was built with a specific dataframe in mind. But it can be resused on another dataset as long as it matches the expressions actions.  
For example, i could do my processing again on other job offers and instead of rewritting the code, like with a function, i can call the expression on my dataset.  

Now let's see the different expressions in the final pipeline and why it is a cleanner way to write code.

```
    wip_c = (
        wip.with_columns(concat_expressions)
        .rename(
            {
                "Vos missions en quelques mots": "missions",
                "Statut du poste": "job_status",
                "Métier de référence": "profession",
                **(
                    {"Descriptif du service": "employeur_description"}
                    if "Descriptif du service" in available_cols
                    else {}
                ),
            }
        )
        .select(remove_noise_and_whitespaces)
        .select(cs.by_name(*FINAL_COLUMNS, require_all=False))
    )

    return wip_c
```

The pipeline uses 3 external elements:
- 1 polars expression
- 1 list of polars expressions
- 1 list

First the pipeline uses the list of polars expressions, essentially applying to the dataframe n expressions one after the other (this list of expression is my solution to the unpredictable header structure/ organisation of the job offers).  
Second, we rename some varaibles using the rename function with a dynamic dictionnary to handle a specific case.  
Third, we use the expression we saw to remove noise and whitespaces has the name suggest.  
Fourth, we filter the dataframe to keep only a subset of variables that are specified in the list *FINAL_COLUMNS*. *require_all=False* basically allows the code to word even if the variable is missing which was the case with different structues of job offers.  
Finally we return a Polars DataFrame.  

This pipeline regroups ALL the concrete actions that modifies this dataset, the code before that is only set up.  
Each step is clear and has a defined purpose.  
This pipelines take 'wip' (DataFrame) as input and create 'wip_c' (DataFrame) in output. 
Instead of creating 4 intermediate dataframes, we created expressions that do nothing unless used, like functions.  
We chainned the methods for an all in one, easy to read and to understand code block.

**Why not Pandas ?**  

The answers lie is the desing phylosophy of both libraries.  
In Pandas, we can also use methods chainning, infact, my pipeline would be very similar in pandas with mostly the same code with different function names.  
But it is less common and not the standard for a few reasons:
- Pandas is **eager**. Each operation is evaluated immediately, which make method chainning a harder code to debug and possible performance overhead since the output of each step is created, and reused for the next one, even if we didn't declared thoses intermediate datasets. With large datasets this is a real issue.
- **Harder to debugg** and to understand. Since we don't create intermediate results, we can't easily inspect those results. This means that it is harder to maintain.  
- To fit better the eager excecution, pandas works best with intermediate results.  

**Why Polars is better at method chainning?**  
- Polars has lazy excecution, this allows for query optimizations. The entire pipeline is optimize with tht polars query optimizer and thus reduce redundant computations and improves performance. Game changer for large datasets.
- Polars encourages a declarative style of programming, where we describe what we want to do rather than how to do it. It fits better method chainning has it allows to express complex transformations concicely.
- Polars is a newer library, written is Rust and optimized for performance, with method chainning being a fundamental part of Polars' design.

My dataset is very small so eager vs lazy doesn't make a difference, so using pandas would have been has effective as polars, but the code is better written in polars in my opinion and it would be easier to adapt for huge datasets since we would only have to switch to the lazy API which is very easy to do. 


### Comparative assessment: When to use each approach


### Lessons learned: Model behavior insights, preprocessing importance


# Conclusions



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