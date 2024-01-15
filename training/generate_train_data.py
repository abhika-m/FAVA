import openai
import json
import backoff
import random
import time
import argparse

@backoff.on_exception(backoff.expo, openai.error.ServiceUnavailableError)
def completions_with_backoff(**kwargs):
    return openai.ChatCompletion.create(**kwargs)

def get_type() :
    types = [["an ", "article"], ["an ","essay"], ["a ","blog post"], ["an ","informational social media post"], 
             ["a ","description"], ["a ","news report"], ["a ","summary"], ["a ","speech"], ["a ","presentation intro"], 
             ["a ","report"], ["an ","informational website content"], ["a ","case study"], ["a ","brochure"], ["a ","text message"], 
             ["a ","book intro"], ["a", "tweet"]]
    word = random.choice(types)
    return word

def create_entity(passage):
    usage = 0
    # request response with errors
    response = completions_with_backoff(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": "Given a passage with possibly already inserted error tokens wrapped in <relation>, "
             + "<contradictory>, <unverifiable>, <subjective>, or <invented>, insert entity errors "
             + "in the passage below, wrapped in tokens to make the passage factually incorrect. Ensure these insertions are outside these existing <> tags, and don't modify the <> tags at all. The error is defined as such:\n"
             + "1. entity errors (<entity>): a small part of a sentence, often an entity (e.g., location name), is "
             + "incorrect (usually 1-3 words). Entity errors often involve noun phrases or nouns.\n" 
             + "Example 1: Messi is an <entity><delete>Argentine</delete><mark>Brazilian</mark></entity> "
             + "soccer player.\n"
             + "Example 2: Selena Gomez was born on <entity><delete>July</delete><mark>March</mark>"
             + "</entity> 22.\n" 
             + "Example 3: India's population is <entity><delete>1.4</delete><mark>2</mark></entity> "
             + "billion people.\n"
             + "Now, insert entity error tokens in the given passage but make sure that you don't modify "
             + "anything inside any already existing <> error tokens, only add entity errors with <entity>"
             + "</entity> tokens outside the already existing <> tags. Also, avoid inserting errors in the "
             + "first sentence. Also make sure to tag every single edit with <mark></mark>, <delete></delete> "
             + "and <entity></entity> tags like done in the examples below.\n##\n"
             + "Paragraph: The Qing invasion of Joseon in the winter of 1636 was a significant moment "
             + "in Korean history. It allowed the newly-established Qing dynasty to establish itself as "
             + "the hegemon in the Imperial Chinese Tributary System, but it also formally severed Joseon's "
             + "relationship with the Ming dynasty. This invasion was preceded by the Later Jin invasion of Joseon "
             + "in 1627.\n\nThe Joseon dynasty was founded in 1392 and lasted until 1897. During this time, they had "
             + "a close relationship with the Ming dynasty of China, being a tributary state.\n"
             + "Edited: The Qing invasion of Joseon in the winter of 1636 was a significant moment in Korean "
             + "history. It allowed the newly-established Qing dynasty to establish itself as the hegemon in "
             + "the Imperial <entity><delete>Chinese</delete><mark>Korean</mark></entity> Tributary System, "
             + "but it also formally severed Joseon's relationship with the Ming dynasty. This invasion was "
             + "preceded by the Later Jin invasion of Joseon in <entity><delete>1627</delete><mark>1636</mark>"
             + "</entity>. \n\nThe Joseon dynasty was founded in 1392 and lasted until 1897. During this time, "
             + "they had a close relationship with the Ming dynasty of China, being a tributary state.\n##\n"
             + "Paragraph: Introducing Rishi Sunak: A British politician who has served in various roles within "
             + "the UK government, including as Prime Minister and Leader of the Conservative Party since October "
             + "2022. With a background as the son of Indian immigrants, Sunak <relation><delete>has</delete><mark>"
             + "has never</mark></relation> been a Member of Parliament for Richmond (Yorks) since 2015 and has held "
             + "several cabinet positions, including Chancellor of the Exchequer. Sunak is an educated individual, "
             + "having studied at Winchester College, Lincoln College, Oxford, and Stanford University in California. "
             + "<contradictory>He has also been the president of America.</contradictory>\n"
             + "Edited: Introducing Rishi Sunak: A British politician who has served in various roles within "
             + "the UK government, including as Prime Minister and Leader of the Conservative Party since "
             + "October 2022. With a background as the son of Indian immigrants, Sunak <relation><delete>has"
             + "</delete><mark>has never</mark></relation> been a Member of Parliament for Richmond (Yorks) "
             + "since <entity><delete>2015</delete><mark>2017</mark> </entity> and has held several cabinet "
             + "positions, including Chancellor of the Exchequer. Sunak is an educated individual, having "
             + "studied at Winchester College, Lincoln College, Oxford, and Stanford University in <entity>"
             + "<delete>California</delete><mark>Washington</mark></entity>. <contradictory>He has also been "
             + "the president of America.</contradictory>\n##\n"
             + "Paragraph: " + passage + "\nEdited: "}
            ],
            max_tokens=2000)
            
    errors = response.choices[0].message.content
    usage += response.usage.total_tokens
    
    return [errors, usage]

def create_relation(passage):
    usage = 0
    # request response with errors
    response = completions_with_backoff(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": "Given a passage with possibly already inserted error tokens wrapped in <entity>, "
             + "<contradictory>, <unverifiable>, <subjective>, or <invented>, insert relation errors,  "
             + "outside the already inserted tokens without modifying the content within already existing tokens. Wrap "
             + "the relational errors in tokens to make the passage factually incorrect. The error is defined as such:\n"
             + "1. relational error (<relation>): a sentence is partially incorrect as a small part (usually 1 - 3 words). "
             + "Relational errors often involve verbs and are often the opposite of what it should be.\n"
             + "Example 1: FDA <relation><delete>approves</delete><mark>declines</mark></relation> pfizer "
             + "COVID-19 Vaccine.\n"
             + "Example 2: Rishi Sunak <relation><delete>began</delete><mark>terminated</mark>"
             + "</relation> his role as Prime Minister in 2022.\n"
             + "Example 3: Millie Bobbie Brown has also starred in several popular movies, including "
             + "“Godzilla vs. Kong” and “Enola Holmes” which she also <relation><delete>produced</delete>"
             + "<mark>directed</mark></relation>.\n"
             + "Now, insert relation error tokens in the given passage but make sure that you don't modify "
             + "anything inside any already existing <> error tokens, only add relational errors with "
             + "<relation></relation> tokens outside the already existing <> tags. Also avoid inserting "
             + "errors in the first sentence.. Also make sure to tag every single edit with <mark></mark>, "
             + "<delete></delete> and <relation></relation> tags like done in the examples below:\n##\n"
             + "Paragraph: The Qing invasion of Joseon in the winter of 1636 was a significant moment in "
             + "Korean history. It allowed the newly-established Qing dynasty to establish itself as the "
             + "hegemon in the Imperial Chinese Tributary System, but it also formally severed Joseon's "
             + "relationship with the Ming dynasty. This invasion was preceded by the Later Jin invasion of "
             + "Joseon in 1627. \n\nThe Joseon dynasty was founded in 1392 and lasted until 1897. During this "
             + "time, they had a close relationship with the Ming dynasty of China, being a tributary state.\n"
             + "Edited: The Qing invasion of Joseon in the winter of 1636 was a significant moment in Korean history. "
             + "It allowed the newly-established Qing dynasty to establish itself as the hegemon in the Imperial Chinese "
             + "Tributary System, but it also formally <relation><delete>severed</delete> <mark>strengthened</mark>"
             + "</relation> Joseon's relationship with the Ming dynasty. This invasion was preceded by the Later Jin "
             + "invasion of Joseon in 1627. \n\nThe Joseon dynasty was <relation><delete>founded</delete><mark>invaded"
             + "</mark></relation> in 1392 and lasted until 1897. During this time, they had a close relationship with "
             + "the Ming dynasty of China, being a tributary state.\n##\n"
             + "Paragraph: Introducing Rishi Sunak: A British politician who has served in various roles "
             + "within the UK government, including as Prime Minister and Leader of the Conservative Party "
             + "since October 2022. With a background as the son of Indian immigrants, Sunak has been a Member "
             + "of Parliament for Richmond (Yorks) since <entity><delete>2015</delete><mark>2017</mark></entity> "
             + "and has held several cabinet positions, including Chancellor of the Exchequer. Sunak is an educated "
             + "individual, having studied at Winchester College, Lincoln College, Oxford, and Stanford University in "
             + "<entity><delete>California</delete><mark>Washington</mark></entity>. <contradictory>He has also been "
             + "the president of America.</contradictory>\n"
             + "Edited: Introducing Rishi Sunak: A British politician who has served in various roles within "
             + "the UK government, including as Prime Minister and Leader of the Conservative Party since "
             + "October 2022. With a background as the son of Indian immigrants, Sunak <relation><delete>has</delete><mark>"
             + "has never</mark></relation> been a Member of Parliament for Richmond (Yorks) since "
             + "<entity><delete>2015</delete><mark>2017</mark></entity> and has held several cabinet positions, "
             + "including Chancellor of the Exchequer. Sunak is an educated individual, having <relation><delete>studied "
             + "at</delete><mark>dropped out of</mark> </relation> Winchester College, Lincoln College, "
             + "Oxford, and Stanford University in <entity> <delete>California</delete><mark>Washington</mark>"
             + "</entity>. <contradictory><mark>He has also been the president of America.</mark></contradictory>\n##\n"
             + "Paragraph: " + passage + "\nEdited: "}
            ],
            max_tokens=2000)
            
    errors = response.choices[0].message.content
    usage += response.usage.total_tokens
    
    return [errors, usage]

def create_contradictory(passage, reference):
    usage = 0
    # request response with errors
    response = completions_with_backoff(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": "Given a reference and a passage with possibly already inserted error "
             + "tokens wrapped in <entity>, <relation>, <unverifiable>, <subjective>, or <invented>, insert "
             + "contradictory sentence errors in the passage outside the already inserted tokens without modifying the content within already existing tokens. Wrap the inserted errors in tokens to make the passage "
             + "factually incorrect.  The contradictory error is defined as such:\n"
             + "1. contradictory sentence error (<contradictory>): a sentence where the entire sentence is contradicted "
             + "by the given reference, meaning the sentence can be proven false due to a contradiction with information in the reference provided.\n##\n"
             + "Example 1:\nReference: Japan participated in World War I from 1914 to 1918 in an alliance with "
             + "Entente Powers (France, the United Kingdom, Russia, the United States, Italy) against the Central "
             + "Powers (Germany, Austria-Hungary, the Ottoman Empire, and Bulgaria).\n"
             + "Contradictory Sentence: <contradictory>Japan sent its army to help Germany during World War I."
             + "</contradictory>\n"
             + "Explanation: The reference states that Japan was in an alliance against Germany, so Japan would "
             + "not send its army to help Germany like the sentence states.\n##\n"
             + "Example 2:\nReference: Percy Jackson & the Olympians is a series of five fantasy novels "
             + "written by American author Rick Riordan.\nContradictory Sentence: The Harry Potter series was "
             + "written by J.K Rowling<contradictory>, as was the Percy Jackson series</contradictory>.\n"
             + "Explanation: The reference states that the Percy Jackson series is written by Rick Riordan and "
             + "not J.K Rowling like the sentence suggests.\n##\n"
             + "Example 3:\nReference: As one of the busiest women in music, it'll come as no surprise that "
             + "Taylor has won pretty much every award there is to win in the biz - being the proud owner of "
             + "no less than 12 Grammy Awards.\nContradictory Sentence:<contradictory>Taylor Swift has never "
             + "won a Grammy in her entire career since she is better known as a performer than a singer."
             + "</contradictory>\nExplanation: The reference states that Taylor Swift has won 12 Grammys and "
             + "is a musician while the sentence says she has won no Grammys which contradicts the reference.\n"
             + "Now, insert contradictory sentences with tokens in the given passage but make sure that you "
             + "don't modify anything inside any already existing <> error tokens at all, keep those untouched,, only insert new contradictory "
             + "sentences (entire sentences) with <contradictory></contradictory> tokens outside the already "
             + "existing <> tags in the passage. Also avoid inserting errors before the first sentence. Also make sure you tag "
             + "each edit with <contradictory></contradictory> tags like done in the examples below:\n##\n"
             + "Reference: A.C. Cesena, commonly referred to as Cesena, was an Italian football club based in "
             + "Cesena, Emilia-Romagna. The club spent most of its history in professional leagues such as "
             + "Serie A and Serie B, but went bankrupt and folded in 2018. Another club from Cesena, A.S.D. "
             + "Romagna Centro Cesena, claims to be the bankrupted club's successor and in 2019 changed its "
             + "name to \"Cesena F.C.\"."
             + "\nPassage: A.C. Cesena was an Italian professional football club based "
             + "in Cesena, Emilia-Romagna. The club was founded in 1940 and was known by the nickname \"Bianconeri\" "
             + "(White and Blacks). Cesena has had a mixed history, having spent a significant amount of time in the "
             + "lower tiers of Italian football, but has also experienced some success in the Serie A. In its history, "
             + "Cesena has had a few notable achievements, including finishing seventh in the Serie A in the 1977-78 "
             + "season. \n"
             + "Edited: A.C. Cesena was an Italian professional football club based in Cesena, Emilia-Romagna. "
             + "The club was founded in 1940 and was known by the nickname ""Bianconeri"" (White and Blacks). "
             + "Cesena has had a mixed history, having spent a significant amount of time in the lower tiers of "
             + "Italian football, but has also experienced some success in the Serie A. <contradictory>Currently, "
             + "A.C. Cesena plays in Serie C, the third tier of Italian football.</contradictory> In its history, "
             + "Cesena has had a few notable achievements, including finishing seventh in the Serie A in the 1977-78 "
             + "season. <contradictory>It continues to compete in the hope of returning to the higher ranks of Italian "
             + "football</contradictory>.\n##\n"
             + "Reference: McPherson () is a city in and the county seat of McPherson County, Kansas, United States. "
             + "The city is named after Union General James Birdseye McPherson, a Civil War general. It is home to "
             + "McPherson College and Central Christian College.\n"
             + "Passage: McPherson is a city located in <entity><delete>McPherson County</delete><mark>Thomasville"
             + "</mark></entity>, Kansas, United States. <invented>The town has Jabberjay birds.</invented> "
             + "The town is named in honor of Union General James Birdseye McPherson who was a general during the "
             + "American Civil War.\n"
             + "Edited: McPherson is a city located in <entity><delete>McPherson County</delete><mark>"
             + "Thomasville</mark></entity>, Kansas, United States. <invented>The town has Jabberjay "
             + "birds.</invented> The town is named in honor of Union General James Birdseye McPherson who "
             + "was a general during the American Civil War. <contradictory>This city is home to just Stanford "
             + "University.</contradictory>\n##\n"
             + "Reference: " + reference + "\nPassage: " + passage + "\nEdited: "}
            ],
            max_tokens=2000)
            
    errors = response.choices[0].message.content
    usage += response.usage.total_tokens
    
    return [errors, usage]

def create_subjective(passage, subject):
    usage = 0
    # request response with errors
    response = completions_with_backoff(
        model='gpt-3.5-turbo',
        messages=[
            {"role": "user", "content": "Given a subject and a passage with possibly already inserted error tokens wrapped in <entity>, <relation>, <contradictory>, <unverifiable>, or <invented>, insert subjective sentence errors outside the already inserted tokens without modifying the content within already existing tokens. Wrap the insertions in tokens to make the passage factually incorrect. The error is defined as such:\n"
             + "1. subjective sentence (<subjective>): an entire sentence or phrase that is subjective and cannot be verified, so it should not be included.\n"
             + "Example 1: <subjective>He is the greatest soccer player ever.</subjective>\n"
             + "Example 2: The first Harry Potter book was published in 1998 <subjective>and was a lot better than the rest in the series because of its use of a rich and evocative vocabulary.</subjective>\n" 
             + "Example 3: <subjective>Overall, Aenir is a thrilling adventure novel that takes readers on a journey through a unique and imaginative world, filling their lives with excitement.</subjective>\n"
             + "Now, insert subjective sentence error tokens in the given passage but make sure that you don't modify anything inside any already existing <> error tokens at all, keep those untouched,, only insert full subjective sentences or phrases with <subjective></subjective> tokens about the given subject outside the already existing <> tags in the given passage. Also avoid inserting errors before the first sentence. Also make sure you tag each edit with <subjective></subjective> tags like done in the examples below:\n"
             + "##\nSubject: Christopher Hemsworth\n"
             + "Passage: Christopher Hemsworth is an Australian actor who gained recognition for his role in the Australian TV series “Home and Away” from 2004-2007 before moving on to Hollywood films. He is best known for playing Thor in the Marvel Cinematic Universe, starting with the 2011 film of the same name and most recently reprising the role in a 2022 film. Hemsworth is now considered one of the highest-paid actors in the world.\n"
             + "Edited: Christopher Hemsworth is an Australian actor who gained recognition for his role in the Australian TV series “Home and Away” from 2004-2007 before moving on to Hollywood films. <subjective>Chris Hemsworth deserves to win every award for acting because of his compelling and beautiful acting skills.</subjective> He is best known for playing Thor in the Marvel Cinematic Universe, starting with the 2011 film of the same name and most recently reprising the role in a 2022 film. Hemsworth is now considered one of the highest-paid actors in the world.\n"
             + "##\nSubject: Paris Saint-Germain F.C.\n"
             + "Passage: Did you know that Paris Saint-Germain Football Club is France's most successful football club? They have won over <entity><delete>40</delete><mark>15</mark></entity> official honours, including ten league titles and one major European trophy. <unverifiable>PSG players get goodies when they first play there.</unverifiable> PSG <relation><delete>plays</delete><mark>does not play</mark></relation> in the top division of French football, Ligue 1. Their home ground is the Parc des Princes.\n"
             + "Edited: Did you know that Paris Saint-Germain Football Club is France's most successful football club? They have won over <entity><delete>40</delete><mark>15</mark></entity> official honours, including ten league titles and one major European trophy. <unverifiable>PSG players get goodies when they play there.</unverifiable> PSG <relation><delete>plays </delete><mark> does not play</mark></relation> in the top division of French football, Ligue 1. Their home ground is the Parc des Princes, <subjective>which is located in a pretty bad location.</subjective>"
             + "\n##\nSubject: " + subject + "\nPassage: " + passage + "\nEdited: "}
            ],
            max_tokens=2000)
            
    errors = response.choices[0].message.content
    usage += response.usage.total_tokens
    
    return [errors, usage]

def create_unverifiable(passage, reference):
    usage = 0
    # request response with errors
    response = completions_with_backoff(
        model='gpt-4',
        messages=[
            {"role": "user", "content": "Given a reference and a passage with possibly already inserted error tokens wrapped in <entity>, <relation>, <contradictory>, <subjective>, or <invented>, insert unverifiable errors outside the already inserted tokens without modifying the content within already existing tokens. Wrap the insertions in tokens to make the passage factually incorrect. The error is defined as such:\n"
             + "1. unverifiable sentence (<unverifiable>): a sentence where the whole sentence or phrase is unlikely to be factually grounded although it can be true, and the sentence cannot be confirmed nor denied using the reference given or internet search, it is often something personal or private and hence cannot be confirmed.\n"
             + "##\nUnverifiable Error Example 1: <unverifiable>Apple is planning on releasing an instrument collection.</unverifiable>\n"
             + "Explanation: Information about Apple’s release plans cannot be corroborated by any information online, however could be true.\n"
             + "##\nUnverifiable Error Example 2: <unverifiable>Selena Gomez is known to love turtles.</unverifiable>\n"
             + "Explanation: Personal information about Selena Gomez’s opinion on turtle’s cannot be verified online, however could be true.\n"
             + "##\nUnverifiable Error Example 3: <unverifiable>Tom Cruise wanted to act in a Bollywood film.</unverifiable>\n"
             + "Explanation: Personal information about Tom Cruise’s preference on acting in a Bollywood film could be true but cannot be found online.\n"
             + "Now, insert unverifiable error tokens in the given passage but make sure that you don't modify anything inside any already existing <> error tokens at all, keep those untouched, only insert unverifiable sentences or phrases with <unverifiable></unverifiable> tokens outside the already existing <> tags in the given passage. Remember, unverifiable sentences seem like they are true but cannot be confirmed or denied. Also avoid inserting errors before the first sentence. Also make sure you tag each edit with <unverifiable></unverifiable> tags like done in the examples below:\n"
             + "##\nReference: Christopher Hemsworth (born 11 August 1983) is an Australian actor. He rose to prominence playing Kim Hyde in the Australian television series “Home and Away” (2004-2007) before beginning a film career in Hollywood. In the Marvel Cinematic Universe (MCU), Hemsworth started playing Thor with the 2011 film of the same name and most recently reprised the role in 2022, which established him among the world's highest-paid actors.\n"
             + "Passage: Christopher Hemsworth is an Australian actor who gained recognition for his role in the Australian TV series “Home and Away” from 2004-2007 before moving on to Hollywood films. He is best known for playing Thor in the Marvel Cinematic Universe, starting with the 2011 film of the same name and most recently reprising the role in a 2022 film. Hemsworth is now considered one of the highest-paid actors in the world.\n"
             + "Edited: Christopher Hemsworth is an Australian actor who gained recognition for his role in the Australian TV series “Home and Away” from 2004-2007 before moving on to Hollywood films. He is best known for playing Thor in the Marvel Cinematic Universe, starting with the 2011 film of the same name and most recently reprising the role in a 2022 film. <unverifiable>Chris Hemsworth doesn't like his co-star who plays Loki.</unverifiable> Hemsworth is now considered one of the highest-paid actors in the world.\n"
             + "##\nReference: McPherson () is a city in and the county seat of McPherson County, Kansas, United States. The city is named after Union General James Birdseye McPherson, a Civil War general. It is home to McPherson College and Central Christian College.\n"
             + "Passage: McPherson is a city located in <entity><delete>McPherson County</delete><mark>Thomasville</mark></entity>, Kansas, United States. The town is named in honor of Union General James Birdseye McPherson who was a general during the American Civil War.\n"
             + "Edited: McPherson is a city located in <entity><delete>McPherson County</delete> <mark>Thomasville</mark></entity>, Kansas, United States. The town is named in honor of Union General James Birdseye McPherson who was a general during the American Civil War. <unverifiable>The citizens of this town tend to enjoy cooking chicken dishes as a part of their culture.</unverifiable>\n"
             + "\n##\nReference: " + reference + "\nPassage: " + passage + "\nEdited: "}
            ],
            max_tokens=2000)
            
    errors = response.choices[0].message.content
    usage += response.usage.total_tokens
    
    return [errors, usage]

def create_invented(passage, subject):
    usage = 0
    # request response with errors
    response = completions_with_backoff(
        model='gpt-4',
        messages=[
            {"role": "user", "content": "Given a subject and a passage with possibly already inserted error tokens wrapped in <entity>, <relation>, <contradictory>, <unverifiable>, or <subjective>, insert invented info sentence errors outside the already inserted tokens without modifying the content within already existing tokens. Wrap the errors in tokens to make the passage factually incorrect. The error is defined as such:\n"
             + "1. invented info error (< invented >): these errors refer to entities that are not known  or do not exist. this does not include fictional characters in books or movies. invented info errors include phrases or sentences which have unknown entities or misleading information.\n"
             + "##\nInvented Info Example 1: <invented>Kansas City has a large population of the Yuman Tribe.</invented>\n"
             + "Explanation: Yuman tribe is not an actual tribe, they are a invented entity.\n"
             + "##\nInvented Info Example 2: Joel Embiid is a Cameroonian professional basketball player for the Philadelphia 76ers , and he was awarded the Kia NBA MVP Trophy in 2023 <invented>and received the Shaquille O’Neal trophy for being the fastest runner this season.</invented>\n"
             + "Explanation: There is no trophy named the Shaquille O’Neal trophy in NBA and so it is not possible for Joel Embiid to have won it. Also, there is no award for being the fastest runner in the NBA. Both are invented.\n"
             + "##\nInvented Info Example 3: <invented>Andrew Ng’s area of Sentiment-Infused Language Generation (SILG) which explores the influence of sentiment analysis on the generation of human-like language.</invented>\n"
             + "Explanation: There is no field of research named Semantic compositionality analysis, so it is a invented entity.\n"
             + "Now, insert invented information error tokens about the subject in the given passage but make sure that you don't modify anything inside any already existing <> error tokens at all, keep those untouched, only add fictional sentence errors with <invented></invented> tokens outside the already existing <> tags in the given passage. Also avoid inserting errors before the first sentence. Also make sure you tag each edit with <invented></invented> tags like done in the examples below:\n"
             + "##\nSubject: Christopher Hemsworth\n"
             + "Passage: Christopher Hemsworth is an Australian actor who gained recognition for his role in the Australian TV series “Home and Away” from 2004-2007 before moving on to Hollywood films. He is best known for playing Thor in the Marvel Cinematic Universe, starting with the 2011 film of the same name and most recently reprising the role in a 2022 film. Hemsworth is now considered one of the highest-paid actors in the world.\n"
             + "Edited: Christopher Hemsworth is an Australian actor who gained recognition for his role in the Australian TV series “Home and Away” from 2004-2007 before moving on to Hollywood films. <invented>Chris Hemsworth has also been recognized for his discovery of the real-time acting method, where an actor only does improv, which has been adopted by many actors.</invented> He is best known for playing Thor in the Marvel Cinematic Universe, starting with the 2011 film of the same name and most recently reprising the role in a 2022 film. Hemsworth is now considered one of the highest-paid actors in the world.\n"
             + "##\nSubject: Paris Saint-Germain F.C.\n"
             + "Passage: Did you know that Paris Saint-Germain Football Club is France's most successful football club? Their home ground is the Parc des Princes. They have won over <entity><delete>40</delete><mark>15</mark></entity> official honours, including ten league titles and one major European trophy. <subjective>PSG has an ugly design.</subjective> PSG <relation><delete>plays</delete><mark>does not play</mark></relation> in the top division of French football, Ligue 1.\n"
             + "Edited: Did you know that Paris Saint-Germain Football Club is France's most successful football club? Their home ground is the Parc des Princes. <invented>It's a place where people often go to play the popular European sport jump tag</invented>. They have won over <entity><delete>40</delete><mark>15</mark></entity> official honours, including ten league titles and one major European trophy. <subjective><mark> PSG has an ugly design.</mark></subjective> PSG <relation><delete>plays</delete><mark>does not play</mark></relation> in the top division of French football, Ligue 1.\n"
             + "##\nSubject: " + subject + "\nPassage: " + passage + "\nEdited: "}
            ],
            max_tokens=2000)
            
    errors = response.choices[0].message.content
    usage += response.usage.total_tokens
    
    return [errors, usage]

def create_passage(file, output_file):
    iterations = 0
    data = []
    name = file[file.find('/') + 1:file.find('.')]
    cost = 0
    # parse through jsonlines
    with open(file) as f:
    # check each line
        for line in f:
            input = json.loads(line)
            [before, type] = get_type()
            # extract prompt from input
            title = input["title"]
            reference = input['intro']
            index = reference.find("\n") + 2
            index_end = reference.find("\n", index + 1)
            if(index_end - index <= 75):
                temp = index_end
                index_end = reference.find("\n", temp)
            if(index == -1):
                index = 0
            if(index_end == -1 or index_end == index):
                reference = reference[index:]
            else:
                reference = reference[index:index_end]
            # request response
            try:
                response = completions_with_backoff(
                    model='gpt-3.5-turbo',
                    messages=[
                    {"role": "user", "content": "Given a passage, create " + before + type + " of 3-5 sentences using only "
                    + "the information presented in the passage. Do not include any new information not "
                    + "presented in the passage.\nPassage: " + reference}
                    ],
                    max_tokens=2000)
            except Exception as e:
                print(e)
                time.sleep(60)
                response = completions_with_backoff(
                    model='gpt-3.5-turbo',
                    messages=[
                    {"role": "user", "content": "Given a passage, create " + before + type + " of 3-5 sentences using only "
                    + "the information presented in the passage. Do not include any new information not "
                    + "presented in the passage.\nPassage: " + reference}
                    ],
                    max_tokens=2000)
            cost += ((response.usage.total_tokens / 1000) * 0.002)
            passage = response.choices[0].message.content
            types = []
            curr_passage = passage
            num = random.randint(0, 1)
            if(num == 1):
                try:
                    [r, u] = create_entity(curr_passage)
                except Exception as e:
                    print(e)
                    time.sleep(60)
                    [r, u] = create_entity(curr_passage)
                curr_passage = r
                types.append("entity")
                cost += ((u / 1000) * 0.002)
            num = random.randint(0, 1)
            if(num == 1):
                try:
                    [r, u] = create_relation(curr_passage)
                except Exception as e:
                    print(e)
                    time.sleep(60)
                    [r, u] = create_relation(curr_passage)
                curr_passage = r
                types.append("relation")
                cost += ((u / 1000) * 0.002)
            # request response with errors
            num = random.randint(0, 1)
            if(num == 1):
                [r, u] = create_invented(curr_passage, title)
                curr_passage = r
                types.append("invented")
                cost += ((u / 1000) * 0.06)
            num = random.randint(0, 1)
            if(num == 1):
                [r, u] = create_subjective(curr_passage, title)
                curr_passage = r
                types.append("subjective")
                cost += ((u / 1000) * 0.002)
            num = random.randint(0, 1)
            if(num == 1):
                [r, u] = create_unverifiable(curr_passage, reference)
                curr_passage = r
                types.append("unverifiable")
                cost += ((u / 1000) * 0.06)
            num = random.randint(0, 1)
            if(num == 1):
                [r, u] = create_contradictory(curr_passage, reference)
                curr_passage = r
                types.append("contradictory")
                cost += ((u / 1000) * 0.002)
            dict = {"evidence":reference, "diversified_passage":passage, "errored_passage":curr_passage,
                    "subject":title, "source":name, "type": type, "error_types":types}
            data.append(dict)
            
            # increment iterations
            iterations += 1
            print("{0}: title = {1}, cost = {2}".format(iterations, title, cost))
            # keeping track
            if(iterations % 10 == 0):
                json_object = json.dumps(data)
                f =  output_file + "_tmp.json"
                with open(f, "w") as outfile:
                    outfile.write(json_object)

    # create json file with data
    json_object = json.dumps(data)
    with open(output_file + ".json", "w") as outfile:
        outfile.write(json_object)

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_file",
        type=str,
        default=None,
        help="Input .jsonl file with title and input fields to generate training data")
    parser.add_argument(
        "--output_file",
        type=str,
        default=None,
        help="Output .json file")
    parser.add_argument(
        "--openai_key",
        type=str,
        default=None,
        help="OpenAI key for generations")
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    openai.api_key = args.openai_key
    create_passage(args.input_file, args.output_file)
