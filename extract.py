import sqlite3
import re
import textract
import os
from transformers import GPT2LMHeadModel, GPT2Tokenizer
import torch
import sys
from flask import jsonify
from sklearn.metrics.pairwise import cosine_similarity
import torch
from nltk.translate.bleu_score import sentence_bleu


def get_db_connection():
    conn = sqlite3.connect('gradegpt.db', check_same_thread=False)
    return conn


def extractContent(pathToFile: str) -> list:
    """extract questions
    Parameters
    ----------
    pathToFile : str
        Path of the uploaded questions(.docx) file.

    Returns
    -------
    list
        list of extracted questions from the .docx file.

    """
    # Read the contents of the document file
    questionsFileContent = textract.process(pathToFile).decode('utf-8')

    # Extract questions from the document text
    pattern = r'(\S.*)'  # Regular expression pattern to match questions
    questions = re.findall(pattern, questionsFileContent)
    return questions


def saveContent(contentType: str, pathToFile: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    """ Extracts questions from the uploaded .docx file and saves in the questions table in the sqlite db, method is invoked after file is uploaded
    ----------
    Parameters
    ----------
    contentType : str
        'answers' for when answers need to be saved; 'questions' for questions
    pathToFile : str
        Path of the uploaded questions(.docx) file.

    Returns
    -------
    bool
        True on success;False on failure
    """
    contentList = extractContent(pathToFile)
    if contentType == 'questions':
        try:
            insert_query = "INSERT INTO questions (question_text) VALUES (?)"
            for i in contentList:
                cursor.execute(insert_query, (i,))
                conn.commit()
            return 'All questions have been saved successfully!'
        except Exception as e:
            return e
    else:
        pattern = r'(\d+)'  # Regular expression pattern to match questions
        studentId = re.findall(pattern, pathToFile)
        try:
            insert_query = "INSERT INTO answers (question_id,student_id,answer_text) VALUES (?,?,?)"
            for x, y in enumerate(contentList):
                cursor.execute(insert_query, (x + 1, int(studentId[0]), y))
                conn.commit()
            return 'All answers have been saved successfully!'
        except Exception as e:
            return e


def getResults(id=False):
    conn = get_db_connection()
    cursor = conn.cursor()
    id = f'= { id}' if id != False else "> 0"
    query = "SELECT question_id, question_text, answer_text, answers.student_id FROM answers JOIN questions ON questions.id = answers.question_id" + " WHERE question_id " + id

    # Execute a SELECT query and fetch records
    cursor.execute(query)
    records = cursor.fetchall()

    # Print the fetched records
    return records


def generateModelAnswers():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Execute a SELECT query and fetch records
    cursor.execute(
        "SELECT question_id, question_text, answer_text FROM  answers JOIN questions  ON questions.id = answers.question_id")
    records = cursor.fetchall()

    for i in records:
        modelAnswer = generate_response(i[1])
        insert_query2 = "INSERT INTO model (question_id, answer_text) VALUES (?,?)"
        cursor.execute(insert_query2, (i[0], modelAnswer))
        conn.commit()
    # Print the fetched records


def clearData(folderPath):
    conn = get_db_connection()
    cursor = conn.cursor()
    # Query the sqlite_master table to get a list of table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    table_names = cursor.fetchall()

    # Extract table names from the result
    table_names = [row[0] for row in table_names]

    # Loop through the table names and truncate each table
    for table_name in table_names:
        truncate_sql = f"DELETE FROM {table_name};"
        cursor.execute(truncate_sql)

    # Commit the changes and close the connection
    conn.commit()
    try:
        for filename in os.listdir(folderPath):
            file_path = os.path.join(folderPath, filename)
            if os.path.isfile(file_path):
                os.remove(file_path)
        return "All records have been deleted successfully!"
    except Exception as e:
        return f"Error deleting files: {str(e)}"


def get_grades(qid):
    question = getResults(qid)
    sAnswer = generate_response(question[0][1])
    score = calculate_score(question[0][2], sAnswer)
    return [{
        'answer': sAnswer,
        'score': f'{{ Cosine Score : {score["Cosine score"]}, Jaccard score : {score["Jaccard score"]}, Length score: {score["Length score"]}, Combined Score: {score["Combined Score"]}  }}'
    }]
    

def calculate_score(text1, text2):
    tokenizer = GPT2Tokenizer.from_pretrained('./model')
    model = GPT2LMHeadModel.from_pretrained('./model')
    tokenizer.pad_token = tokenizer.eos_token

    # Tokenize and encode the texts
    inputs = tokenizer([text1, text2], padding=True,
                       truncation=True, return_tensors='pt')
    vector1 = inputs.input_ids[0].reshape(1, -1)
    vector2 = inputs.input_ids[1].reshape(1, -1)
    cosine_sim = cosine_similarity(vector1, vector2)[0][0]

    # Calculate Jaccard similarity
    def jaccard_similarity(text1, text2):
        set1 = set(text1.split())
        set2 = set(text2.split())
        return len(set1 & set2) / len(set1 | set2)

    jaccard_score = jaccard_similarity(text1, text2)
    self_bleu_score = sentence_bleu([text2.split()], text1.split())

    # Length-based similarity
    length_similarity = 1 / (1 + abs(len(text1) - len(text2)))

    # Combine scores using weighted average
    weight_cosine = 0.6
    weight_jaccard = 0.2
    weight_self_bleu = 0.1
    weight_length = 0.5

    combined_score = (
        weight_cosine * cosine_sim +
        weight_jaccard * jaccard_score +
        weight_length * length_similarity
    )
    return {"Cosine score": cosine_sim, "Jaccard score": jaccard_score, "Length score": length_similarity, "Combined Score": combined_score}


def generate_response(prompt):
    # return jsonify({'message': 'I couldn\'t answer that!'})
    model = GPT2LMHeadModel.from_pretrained('./model')
    tokenizer = GPT2Tokenizer.from_pretrained('./model')
    # Create the attention mask and pad token id
    input_ids = tokenizer.encode(prompt, return_tensors="pt")
    attention_mask = torch.ones_like(input_ids)
    tokenizer.pad_token = tokenizer.eos_token
    output = model.generate(
        # max_length=256,
        # num_beams=4,
        # attention_mask=attention_mask,
        # num_return_sequences=1,  # Generate a single sequence
        # temperature=0.9,       # Controls randomness (higher for more diversity)
        # early_stopping=True,
        input_ids,
        max_length=256,
        num_beams=4,
        attention_mask=attention_mask,
        # Controls randomness (higher for more diversity)
        temperature=0.8,
        top_k=10,
        top_p=0.5
    )
    response = tokenizer.decode(output[0], skip_special_tokens=True)
    if len(response) > 0:
        return re.findall(r'(?<=\[<startoftext>])(.*?)(?=\[<endoftext>])', response)[0]
    else:
        return 'I couldn\'t answer that!'

