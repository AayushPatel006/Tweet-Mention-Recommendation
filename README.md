# Automatic Tweet Mention Recommendation in X for Reporting Civic Issues - Case Study based on Mumbai City, India

This repository contains the code implementation for the paper "Automatic Tweet Mention Recommendation in X for Reporting Civic Issues - Case Study based on Mumbai City, India" by Aayush Patel ([Linkedin](https://www.linkedin.com/in/aayushpatel006), [Github](https://github.com/AayushPatel006)), Chaitya Dobariya ([Linkedin](https://www.linkedin.com/in/chaitya-dobariya/), [Github](https://github.com/Chaitya02)), Dayanand Ambawade ([Linkedin](https://www.linkedin.com/in/dayanand-ambawade-a491a754)), Dhawal Thakkar ([Linkedin](https://www.linkedin.com/in/dhawal-thakkar-759839140)) and P. Balamurugan ([Linkedin](https://www.linkedin.com/in/balamurugan-palaniappan-75b407b5)), accepted by 10th IEEE INTERNATIONAL SMART CITIES CONFERENCE 2024.

<img src="./TweetConnect-Project.png">

## Table of Contents
- [Introduction](#introduction)
- [Features](#features)
- [Project Structure](#project-structure)
- [Demo Videos](#demo-videos)
- [Technologies Used](#technologies-used)
- [Installation and Setup](#installation-and-setup)
  - [Running Training Code](#running-training-code)
  - [Browser Plugin Integration](#browser-plugin-integration)
  - [Government Portal Usage](#government-portal-usage)
  - [Dataset Collection for a New City](#dataset-collection-for-a-new-city)
- [Acknowledgements](#acknowledgements)

## Introduction

This project implements an intelligent mention recommendation system for X (formerly Twitter) to improve communication between citizens and government authorities regarding civic issues in Mumbai, India. The rapid growth of social media usage among citizens has created an opportunity for more direct and immediate communication between the public and government authorities. However, this increased communication volume also presents challenges in terms of proper routing and timely responses to citizen concerns.

Our solution implements an intelligent mention recommendation system for X to streamline the process of reporting civic issues. By automatically suggesting relevant government department handles based on the content of a user's tweet, we aim to:

1. Improve the accuracy of issue routing to the appropriate authorities
2. Reduce response times for addressing civic problems
3. Enhance overall communication efficiency between citizens and government departments

The system utilizes advanced natural language processing techniques, including a custom BERT model, to analyze tweet content and provide context-aware mention suggestions. Additionally, we've developed a browser plugin for real-time recommendations and a department portal for managing and responding to citizen concerns.

## Features

- Advanced tweet classification using a custom BERT model
- Real-time mention suggestions via a user-friendly browser plugin
- Comprehensive department portal for efficient management and response to citizen concerns
- Intelligent location-aware recommendations for improved accuracy
- AI-powered actionable statement generation leveraging the Llama 2 model

## Project Structure

- `browser_plugin/`: Contains frontend and backend components for the X browser extension
  - `frontend/`: User interface files for the browser plugin
  - `backend/`: Server-side logic and API endpoints for the plugin
- `department_portal/`: Implementation files for the government department management portal
  - `config/`: Contains configuration files for database connection
  - `model/`: Contains Jupyter notebook for generating actionable statements
  - `department_portal.py`: Streamlit application for the department portal interface
- `datasets/`: 
  - `actual_collected_tweets/`: Contains 288 actual collected tweets
  - `artificial_generated_data/`: Contains train and test CSV files
- `models/`: 
  - `traditional_classification_models.ipynb`: Jupyter notebook with baseline machine learning models
  - `custom_bert_model.ipynb`: Implementation and training of the custom BERT model
- `tweet_generation_prompt.txt`: Prompts used for generating synthetic tweet dataset

## Demo Videos

- [X Browser Plugin Demo](https://bit.ly/3YL2tTU)
- [Department Portal Demo](https://bit.ly/3YL2tTU)

## Technologies Used

- Python
- BERT (Bidirectional Encoder Representations from Transformers)
- JavaScript
- FastAPI
- MongoDB
- Streamlit

## Installation and Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Chaitya02/Tweet-Mention-Recommendation.git
   cd Tweet-Mention-Recommendation
   ```

2. Download datasets from the `datasets/` directory.

### Running Training Code

1. **To train the custom BERT model:**
    - Open the `models/custom_bert_model.ipynb` file.
    - Ensure the required libraries are installed in your environment:
      
      ```bash
      pip install torch transformers pandas scikit-learn
      ```
      
    - This notebook contains the entire workflow for loading, preprocessing, and training the custom BERT model on the `artificial_generated_data/` dataset.
    - Once training is complete, the model will be saved as `model.pth` in the `saved_model/` directory.

2. **For baseline machine learning models:**
    - Open the `traditional_classification_models.ipynb` notebook to run simpler models like Logistic Regression, SVM's, KNN, Naive Bayes, Decision Trees or Random Forests on the same dataset.

### Browser Plugin Integration

To integrate the X browser plugin:

1. Ensure the backend is active:
   - Set up the mongoDB database and configure environment variables:
    - Create a `.env` file in the `backend/` directory with the following variables:
      
      ```bash
      DB_USER=<mongoDB_username>
      DB_USER_KEY=<mongoDB_password>
      GOOGLE_MAP_API=<google_map_api_key>
      OPEN_WEATHER_API=<open_weather_api_key>
      GEOAPIFY_API=<geoapify_api_key>
      ```
      
   - Navigate to the `models/` directory and run the custom_bert_model.ipynb file.
   - Create a `saved_model/` before running the ipynb file.
   - The `model.pth` file will be saved in the `saved_model/` directory.
   - Add this file to the `backend/` directory of the browser plugin.
   - Install the required dependencies:
     ```bash
     pip install -r requirements.txt
     ```
   - Start the backend server:
     ```bash
     python main.py
     ```

3. Navigate to the `browser_plugin/` directory.
4. Open your browser's extension management page (e.g., `chrome://extensions/` for Chrome).
5. Enable "Developer mode".
6. Click "Load unpacked" and select the `frontend/` directory.
7. The plugin should now appear in your browser's toolbar.

Usage:
- When composing a tweet on X, the plugin will automatically suggest relevant department mentions based on the content of your tweet.
- The plugin also features based on users permission to add current location, allowing to easily identify the issue location.
- It provides prompts to encourage adding location information to your tweets if not mentioned.
- You can click the copy button next to recommended mention, then paste it directly into your tweet.

### Government Portal Usage

For government entities to use the department portal:

1. Navigate to the `department_portal/` directory.
2. Create a `.env` file with the following variables:
      
      ```bash
      DB_USER=<mongoDB_username>
      DB_USER_KEY=<mongoDB_password>
      ```
      
3. Install the required dependencies:
   
   ```bash
   pip install -r requirements.txt
   ```
4. Start the portal server:
   
   ```bash
   streamlit run department_portal.py
   ```
3. Access the portal through the provided URL (typically `http://localhost:8501`).

Usage:
- Provide location permission to fetch the tweets based on your city.
- View different categories of tweets based on departments and urgency.
- Get actionable statements generated for the tweets with relevant department handles and for more details navigate to the actual tweet.
- Access analytics and reports on civic issues trends.

### Dataset Collection for a New City

To deploy the system in a new city, follow these steps for dataset collection and adaptation:

1. **Identify Departments:**
    - Identify the government departments in the new city that are responsible for addressing civic issues such as road maintenance, water supply, waste management, traffic control, etc.
    - Obtain the official social media handles (X accounts) for these departments. These handles will be used for mention recommendations.

2. **Collecting Civic Issue Tweets:**
    - Use the Twitter API to fetch tweets from the new city using relevant hashtags and keywords like `#RoadIssues`, `#WaterProblem`, `#Traffic`, etc.
    - Modify the `tweet_generation_prompt.txt` file to include city-specific prompts for synthetic tweet generation.

3. **Data Preprocessing:**
    - Clean the collected tweets by removing unnecessary symbols and URLs.
    - Annotate the dataset manually or automatically by assigning relevant departments (or labels) based on the issue type.

4. **Adaptation for Location-Awareness:**
    - Update the location-aware recommendation system by integrating the new city's geo-coordinates and relevant departments into the existing model.
    - Update the city details in the code to ensure location suggestions are accurate.

5. **Re-training the BERT Model:**
    - Train the custom BERT model (`custom_bert_model.ipynb`) on the new city’s dataset to improve accuracy in mention suggestions.

<!-- ## License

This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details. -->

## Acknowledgements

We would like to thank Prof. P. Balamurugan, Prof. Dayanand Ambawade and Dhawal Thakkar for their support and collaboration in this project.
