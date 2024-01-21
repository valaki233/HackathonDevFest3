from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv('openai_api_key'))

class Score():
 def __init__(self):
    pass
 def get_score(self, class_name, note_name, user_id=1):

    note = ''
    with open(f"./uploads/{user_id}/{note_name}", 'r') as f:
        note = f.read()

    sentences = []
    current_sentence = ''
    for char in note:
        if char in ['.', '!', '?', '\n']:
            
            current_sentence += char
            if len(current_sentence) < 4:
                if char == "\n":
                    continue
            sentences.append(current_sentence.strip())
            current_sentence = ''
        else:
            current_sentence += char

    print(sentences)
    total_length = sum(len(sentence) for sentence in sentences)
    print(total_length)
    average_length = total_length / len(sentences)
    print(average_length)

    if 65 > average_length > 40:
        mulipier = 1
    elif average_length < 40:
        a = 40 - int(average_length)
        mulipier = 1/a
    elif 65 < average_length:
        a = int(average_length) - 65
        mulipier = 1/a

    print('multiplier' + str(mulipier))
    average_length_waighted = average_length * mulipier
    

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": """"You are a helpful bot that has to rank Notes taken during a lecture. You need to give one score for eas of readability. Make sure you always use a 1-100 pointing system. Make sure you highly criticize notes so that way the student who took them can improve their skills in effective note taking. Make sure you drasticly punish long and full scentence notes and favour notes that are short and precise. You only need to return me the one score nothing else not context not text!"""},
            {"role": "user", "content": f"I have taken some notes in {class_name} my note is in text format. Pleas only give me one number that is the score nothing else! The note is as follows: " + note},
            
        ],
        temperature=0,
    )
    resp = response.choices[0].message.content
    numbers = ''.join(filter(str.isdigit, resp))
    numbers_as_string = str(numbers)

    total_score = (int(numbers_as_string) + int(average_length_waighted))/2
    return [numbers_as_string, average_length_waighted, total_score]